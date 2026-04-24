"""
routers/qa.py — RAG-powered Q&A endpoints
"""

import aiosqlite
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.vector_store import search
from services.claude import answer_doubt, suggest_questions
from database import DB_PATH

router = APIRouter()


class AskRequest(BaseModel):
    session_id: str
    question: str
    top_k: Optional[int] = 5


class SuggestRequest(BaseModel):
    session_id: str
    count: Optional[int] = 5


# ─── Ask a Doubt ──────────────────────────────────────────────────────────────

@router.post("/ask")
async def ask_doubt(req: AskRequest):
    """
    Core RAG endpoint. Retrieves relevant chunks from the session's notes
    and generates a grounded answer with source citations.
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Retrieve relevant chunks
    chunks = search(req.session_id, req.question, top_k=req.top_k)

    # Generate answer with Claude
    result = answer_doubt(req.question, chunks)

    # Save to history
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO qa_history (session_id, question, answer, sources)
               VALUES (?, ?, ?, ?)""",
            (req.session_id, req.question, result["answer"],
             json.dumps(result["sources"]))
        )
        await db.commit()

    return {
        "question": req.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "chunks_searched": len(chunks),
        "context_chunks_used": result.get("context_chunks_used", 0),
    }


# ─── Suggest Questions ────────────────────────────────────────────────────────

@router.post("/suggest")
async def get_suggestions(req: SuggestRequest):
    """
    Auto-generate sample doubts based on uploaded notes.
    Used for the 'Try asking' quick-fill buttons in the UI.
    """
    # Grab a broad sample of chunks from the session
    chunks = search(req.session_id, "overview summary main topics", top_k=8)
    if not chunks:
        return {"questions": []}

    notes_sample = "\n\n".join(c["text"] for c in chunks[:5])
    questions = suggest_questions(notes_sample, count=req.count)
    return {"questions": questions}


# ─── Q&A History ─────────────────────────────────────────────────────────────

@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 20):
    """Return recent Q&A history for a session."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """SELECT question, answer, sources, created_at
               FROM qa_history WHERE session_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, limit)
        )
    history = []
    for r in rows:
        item = dict(r)
        try:
            item["sources"] = json.loads(item["sources"] or "[]")
        except Exception:
            item["sources"] = []
        history.append(item)

    return {"session_id": session_id, "history": history}
