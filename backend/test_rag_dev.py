"""T
HIS FILE IS FOR TESTING RAG DURING DEVELOPMENT. NOT A REAL BACKEND ENDPOINT.
IT SHOULD BE DELETED ONCE RAG IS WORKING AND INTEGRATED INTO THE CHAT FLOW.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from agent.graph import run_agent
from db.session import AsyncSessionLocal
from rag.ingest import ingest_pdf


def _load_pdf(path: str) -> tuple[bytes, str]:
    p = Path(path)
    return p.read_bytes(), p.name


_TEST_QUESTIONS = [
    "How many vacation days do I have left this year?",
    "What is the sick leave policy? Do I need a doctor's note?",
    "How does vacation rollover work?",
    "Can I take 15 vacation days ?",
    "How can I change my Name or Address in the system?",
]


async def main(pdf_path: str, employee_id: int) -> None:
    pdf_bytes, filename = _load_pdf(pdf_path)

    # ── Step 1: Ingest ────────────────────────────────────────────────────────
    print(f"[1/3] Ingesting '{filename}' ...")
    async with AsyncSessionLocal() as session:
        doc = await ingest_pdf(
            source=pdf_bytes,
            filename=filename,
            uploaded_by=None,
            session=session,
        )
    print(f"      doc.id={doc.id}  chunks={len(doc.chunks)}")
    if not doc.chunks:
        print(
            "      WARNING: 0 chunks — PDF may be image-only or text extraction failed."
        )
        return

    # ── Step 2: Run agent for each test question ───────────────────────────────
    print(f"\n[2/3] Running agent as employee_id={employee_id} ...\n")
    separator = "─" * 60

    for question in _TEST_QUESTIONS:
        print(separator)
        print(f"Q: {question}")
        print("A: ", end="", flush=True)
        async for token in run_agent(employee_id=employee_id, question=question):
            print(token, end="", flush=True)
        print()

    print(separator)
    print("\n[3/3] Done. If the answers reference your PDF content, RAG is working.")


def _parse_args() -> tuple[str | None, int]:
    args = sys.argv[1:]
    pdf_path: str | None = None
    employee_id = 1

    i = 0
    while i < len(args):
        if args[i] == "--employee-id" and i + 1 < len(args):
            employee_id = int(args[i + 1])
            i += 2
        elif not args[i].startswith("--"):
            pdf_path = args[i]
            i += 1
        else:
            i += 1

    return pdf_path, employee_id


if __name__ == "__main__":
    pdf_path, employee_id = _parse_args()
    if pdf_path is None:
        print("Usage: python test_rag_dev.py <path/to/file.pdf> [--employee-id N]")
        sys.exit(1)
    asyncio.run(main(pdf_path, employee_id))
