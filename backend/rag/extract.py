"""
backend/rag/extract.py

LLM-based extraction of structured HR policy data from a document's chunks.

Given a document_id, reads all stored chunks and asks the LLM to return:
  {vacation_days, sick_days, pto_days, notes}

The caller owns DB commit — this function only flushes the DocumentExtraction row.
"""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Document, DocumentChunk, DocumentExtraction
from settings import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an HR policy analyst. You will be given text extracted from an HR document.
Extract the following information and return it as valid JSON with these exact keys:
  - vacation_days: annual vacation days (number, null if not found)
  - sick_days: annual sick/illness leave days (number, null if not found)
  - pto_days: annual PTO or personal days (number, null if not found)
  - notes: a plain-text summary of other relevant HR policies (string, max 300 chars)

Return ONLY the JSON object, no other text.
Example: {"vacation_days": 15, "sick_days": 10, "pto_days": 5, "notes": "..."}
"""


async def extract_document_policy(
    document_id: int,
    session: AsyncSession,
) -> DocumentExtraction:
    """
    Extract HR policy data from the given document's chunks using an LLM.

    Creates or updates the DocumentExtraction row for `document_id`.
    Sets status to 'extracting' during processing, then 'extracted' on success
    or 'failed' on error. Caller must commit.
    """
    extraction = await session.scalar(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
    )
    if extraction is None:
        extraction = DocumentExtraction(document_id=document_id, status="extracting")
        session.add(extraction)
    else:
        extraction.status = "extracting"
        extraction.error_message = None  # type: ignore[assignment]

    await session.flush()

    try:
        doc = await session.scalar(select(Document).where(Document.id == document_id))
        if doc is None:
            raise ValueError(f"Document {document_id} not found")

        chunks = (
            (
                await session.execute(
                    select(DocumentChunk)
                    .where(DocumentChunk.document_id == document_id)
                    .order_by(DocumentChunk.chunk_index)
                )
            )
            .scalars()
            .all()
        )

        if not chunks:
            raise ValueError("Document has no chunks to extract from")

        combined_text = "\n\n".join(c.content for c in chunks)[:8000]

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=2,
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"HR Document: {doc.filename}\n\n{combined_text}",
            },
        ]

        response = await llm.ainvoke(messages)
        raw = str(response.content).strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw[start:end])
            else:
                raise ValueError(f"LLM returned non-JSON: {raw[:200]}") from None

        def _float_or_none(v: object) -> float | None:
            try:
                return float(v) if v is not None else None  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return None

        extracted: dict[str, object] = {
            "vacation_days": _float_or_none(parsed.get("vacation_days")),
            "sick_days": _float_or_none(parsed.get("sick_days")),
            "pto_days": _float_or_none(parsed.get("pto_days")),
            "notes": str(parsed.get("notes", ""))[:300],
        }

        extraction.extracted_data = json.dumps(extracted)  # type: ignore[assignment]
        extraction.status = "extracted"
        logger.info("Extraction complete document_id=%d", document_id)

    except Exception as exc:
        logger.exception("Extraction failed for document_id=%d: %s", document_id, exc)
        extraction.status = "failed"
        extraction.error_message = str(exc)[:500]  # type: ignore[assignment]

    await session.flush()
    return extraction
