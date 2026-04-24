"""
routers/ingest.py — Document upload and ingestion endpoints
"""

import os
import uuid
import aiosqlite
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List

from config import get_settings
from services.parser import parse_document
from services.vector_store import ingest_document, get_session_stats, delete_session
from database import DB_PATH

settings = get_settings()
router = APIRouter()

os.makedirs(settings.upload_dir, exist_ok=True)


# ─── Create Session ───────────────────────────────────────────────────────────

@router.post("/session")
async def create_session(label: str = Form(default="My Exam Session")):
    """
    Create a new study session. Returns session_id.
    All documents and Q&A are scoped to a session.
    """
    session_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO sessions (id, label) VALUES (?, ?)",
            (session_id, label)
        )
        await db.commit()
    return {"session_id": session_id, "label": label}


# ─── Upload Documents ─────────────────────────────────────────────────────────

@router.post("/upload/{session_id}")
async def upload_documents(
    session_id: str,
    files: List[UploadFile] = File(...),
):
    """
    Upload one or more documents (PDF, DOCX, images, TXT).
    Each file is parsed and chunked into the session's vector store.
    """
    # Validate session exists
    async with aiosqlite.connect(DB_PATH) as db:
        row = await db.execute_fetchall(
            "SELECT id FROM sessions WHERE id = ?", (session_id,)
        )
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")

    results = []

    for file in files:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in settings.allowed_extensions:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": f"File type .{ext} not supported",
            })
            continue

        file_bytes = await file.read()
        if len(file_bytes) > settings.max_file_size_mb * 1024 * 1024:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": f"File exceeds {settings.max_file_size_mb}MB limit",
            })
            continue

        try:
            # Parse document
            parsed = parse_document(file_bytes, file.filename)

            if parsed.page_count == 0:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "Could not extract text from this file",
                })
                continue

            # Ingest into vector store
            chunk_count = ingest_document(session_id, parsed)

            # Save metadata to DB
            doc_id = str(uuid.uuid4())
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    """INSERT INTO documents 
                       (id, session_id, filename, file_type, page_count, chunk_count)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (doc_id, session_id, file.filename, ext,
                     parsed.page_count, chunk_count),
                )
                await db.commit()

            results.append({
                "filename": file.filename,
                "status": "success",
                "doc_id": doc_id,
                "pages": parsed.page_count,
                "chunks": chunk_count,
                "file_type": ext,
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e),
            })

    success = [r for r in results if r["status"] == "success"]
    return {
        "session_id": session_id,
        "uploaded": len(success),
        "failed": len(results) - len(success),
        "documents": results,
        "vector_stats": get_session_stats(session_id),
    }


# ─── List Documents ───────────────────────────────────────────────────────────

@router.get("/documents/{session_id}")
async def list_documents(session_id: str):
    """List all documents uploaded to a session."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT * FROM documents WHERE session_id = ? ORDER BY uploaded_at DESC",
            (session_id,)
        )
    return {
        "session_id": session_id,
        "documents": [dict(r) for r in rows],
        "vector_stats": get_session_stats(session_id),
    }


# ─── Delete / Reset Session ───────────────────────────────────────────────────

@router.delete("/session/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete a session and all its documents and vectors."""
    delete_session(session_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM documents WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM qa_history WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM practice_results WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await db.commit()
    return {"status": "deleted", "session_id": session_id}
