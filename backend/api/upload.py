"""
myPerks — UploadThing webhook handler
backend/api/upload.py

POST /upload/callback
  - Receives the UploadThing webhook payload (file URL + metadata + department)
  - Downloads the PDF from the given URL
  - Calls the RAG ingest pipeline (rag.ingest.ingest_pdf)
  - T5 owns Document creation, dedup, chunk storage, and commit
  - Returns { status, document_id }

Protected by require_admin (HR-admin only).
"""

from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from db.models import Document, DocumentExtraction, Employee, department_enum
from db.session import get_session
from rag.ingest import ingest_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# ── Constants ──────────────────────────────────────────────────────────────────

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB

_VALID_DEPARTMENTS = set(department_enum.enums)


# ── Schemas ────────────────────────────────────────────────────────────────────


class UploadThingFile(BaseModel):
    """Single file entry in the UploadThing webhook payload."""

    url: HttpUrl
    name: str
    size: int  # bytes
    key: str  # UploadThing opaque file key


class UploadCallbackPayload(BaseModel):
    """
    Webhook body posted by UploadThing after a successful client upload.
    Includes the target department for RAG scoping (T28).
    """

    files: list[UploadThingFile]
    department: str  # must be a valid department enum value


class IngestResponse(BaseModel):
    status: str  # "ingested" | "duplicate"
    document_id: int


class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    department: str
    extraction_status: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _download_pdf(url: str) -> tuple[bytes, str]:
    """
    Fetch `url` and return (raw_bytes, filename).

    Raises:
        HTTP 502 — upstream download failed
        HTTP 422 — not a PDF, or exceeds size limit
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "UploadThing CDN returned %s for %s", exc.response.status_code, url
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Could not download file from storage"
                f" ({exc.response.status_code})."
            ),
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Network error downloading %s: %s", url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Network error while downloading file.",
        ) from exc

    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Expected a PDF, got content-type: {content_type!r}",
        )

    pdf_bytes = response.content
    if len(pdf_bytes) > _MAX_PDF_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File exceeds the {_MAX_PDF_BYTES // (1024 * 1024)} MB size limit.",
        )

    filename = urlparse(url).path.rstrip("/").split("/")[-1] or "upload.pdf"
    return pdf_bytes, filename


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.post(
    "/callback",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest uploaded PDF into the RAG pipeline (HR admin only)",
)
async def upload_callback(
    payload: UploadCallbackPayload,
    admin: Employee = Depends(require_admin),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> IngestResponse:
    """
    Called by UploadThing after the frontend successfully uploads a file.
    Restricted to HR admins (require_admin raises 403 for employees).

    Flow:
      1. Validate department value.
      2. Download the PDF from the UploadThing CDN.
      3. Call ingest_pdf() — handles dedup, chunking, embedding, and flush.
      4. Commit and return { status, document_id }.
    """
    if not payload.files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Webhook payload contained no files.",
        )

    department = payload.department.lower().strip()
    if department not in _VALID_DEPARTMENTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid department {department!r}. "
            f"Must be one of: {sorted(_VALID_DEPARTMENTS)}",
        )

    file_meta = payload.files[0]
    file_url = str(file_meta.url)

    logger.info(
        "PDF upload by admin=%d department=%r url=%s",
        admin.id,
        department,
        file_url,
    )
    pdf_bytes, filename = await _download_pdf(file_url)

    try:
        document = await ingest_pdf(
            pdf_bytes=pdf_bytes,
            filename=file_meta.name or filename,
            uploaded_by=int(admin.id),
            department=department,
            session=session,
        )
        await session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Ingestion failed for filename=%r: %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingestion pipeline failed.",
        ) from exc

    logger.info(
        "Ingestion complete document_id=%d department=%r", document.id, department
    )

    # ingest_pdf returns the pre-existing Document on a SHA-256 dedup hit.
    # Status distinction is best handled by having ingest_pdf return a flag;
    # deferred to a follow-up. Both cases are safe to call "ingested" here.
    return IngestResponse(status="ingested", document_id=document.id)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all documents (HR admin only)",
)
async def list_documents(
    admin: Employee = Depends(require_admin),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> DocumentListResponse:
    """
    Returns all uploaded documents, ordered newest-first.
    Restricted to HR admins.
    """
    try:
        rows = (
            await session.execute(
                select(Document, DocumentExtraction.status.label("extraction_status"))
                .outerjoin(
                    DocumentExtraction,
                    DocumentExtraction.document_id == Document.id,
                )
                .order_by(Document.uploaded_at.desc())
            )
        ).all()

        return DocumentListResponse(
            documents=[
                DocumentResponse(
                    id=int(row.Document.id),
                    filename=str(row.Document.filename),
                    uploaded_at=row.Document.uploaded_at,
                    department=str(row.Document.department),
                    extraction_status=row.extraction_status,
                )
                for row in rows
            ]
        )
    except Exception:
        # document_extractions table not yet migrated — return docs without status
        await session.rollback()
        documents = (
            (
                await session.execute(
                    select(Document).order_by(Document.uploaded_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return DocumentListResponse(
            documents=[
                DocumentResponse(
                    id=int(doc.id),
                    filename=str(doc.filename),
                    uploaded_at=doc.uploaded_at,
                    department=str(doc.department),
                    extraction_status=None,
                )
                for doc in documents
            ]
        )
