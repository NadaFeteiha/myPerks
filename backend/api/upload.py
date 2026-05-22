"""
myPerks — UploadThing webhook handler
backend/api/upload.py

POST /upload/callback
  - Receives the UploadThing webhook payload (file URL + metadata)
  - Downloads the PDF from the given URL
  - Calls the RAG ingest pipeline (T5: rag.ingest.ingest_pdf)
  - T5 owns Document creation, dedup, chunk storage, and commit
  - Returns { status, document_id }

Protected by Clerk JWT via get_current_user (T3).
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.models import Employee
from db.session import get_session
from rag.ingest import ingest_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# ── Constants ──────────────────────────────────────────────────────────────────

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB

# ── Schemas ────────────────────────────────────────────────────────────────────


class UploadThingFile(BaseModel):
    """Single file entry in the UploadThing webhook payload."""

    url: HttpUrl
    name: str
    size: int  # bytes
    key: str   # UploadThing opaque file key


class UploadCallbackPayload(BaseModel):
    """
    Webhook body posted by UploadThing after a successful client upload.
    UploadThing sends one file per callback in the default router config.
    """

    files: list[UploadThingFile]


class IngestResponse(BaseModel):
    status: str       # "ingested" | "duplicate"
    document_id: int


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
            "UploadThing CDN returned %s for %s",
            exc.response.status_code, url
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


async def _resolve_employee(
    clerk_user_id: str, session: AsyncSession
) -> Employee | None:
    result = await session.execute(
        select(Employee).where(Employee.clerk_user_id == clerk_user_id)
    )
    return result.scalar_one_or_none()


# ── Route ──────────────────────────────────────────────────────────────────────


@router.post(
    "/callback",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="UploadThing webhook — ingest uploaded PDF into the RAG pipeline",
)
async def upload_callback(
    payload: UploadCallbackPayload,
    clerk_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session), # noqa: B008
) -> IngestResponse:
    """
    Called by UploadThing after the frontend successfully uploads a file.

    Flow:
      1. Validate payload has at least one file.
      2. Resolve the Clerk user to an Employee row.
      3. Download the PDF from the UploadThing CDN.
      4. Call ingest_pdf() — T5 handles dedup, chunking, embedding, and commit.
      5. Return { status, document_id }.
    """
    if not payload.files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Webhook payload contained no files.",
        )

    file_meta = payload.files[0]
    file_url = str(file_meta.url)

    # ── 1. Resolve employee ────────────────────────────────────────────────────
    employee = await _resolve_employee(clerk_user_id, session)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user has no employee record.",
        )

    # ── 2. Download PDF ────────────────────────────────────────────────────────
    logger.info("Downloading PDF for employee=%d url=%s", employee.id, file_url)
    pdf_bytes, filename = await _download_pdf(file_url)

    # ── 3. Ingest ──────────────────────────────────────────────────────────────
    # ingest_pdf handles dedup via SHA-256 — returns existing Document if already
    # ingested, or a new one. It owns the commit.
    logger.info("Starting ingestion: filename=%r employee=%d", filename, employee.id)
    try:
        document = await ingest_pdf(
            source=pdf_bytes,
            filename=file_meta.name or filename,
            uploaded_by=employee.id,
            session=session,
        )
    except Exception as exc:
        logger.exception("Ingestion failed for filename=%r: %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingestion pipeline failed.",
        ) from exc

    logger.info("Ingestion complete document_id=%d", document.id)
    return IngestResponse(status="ingested", document_id=document.id)
