"""
routers/mindmap.py — Smart Topic Mind Map generation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.vector_store import search
from services.claude import generate_mind_map

router = APIRouter()


class MindMapRequest(BaseModel):
    session_id: str


@router.post("/generate")
async def generate(req: MindMapRequest):
    """
    Generate a hierarchical topic mind map from the session's uploaded notes.
    Returns a tree structure ready for frontend visualization (e.g. D3, vis.js).
    """
    # Grab a broad representative sample of notes
    chunks = search(req.session_id, "main topics concepts definitions", top_k=12)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No notes found for this session. Please upload your notes first."
        )

    notes_text = "\n\n".join(c["text"] for c in chunks)
    mind_map = generate_mind_map(notes_text)

    return {
        "session_id": req.session_id,
        "mind_map": mind_map,
        "sources_used": list({c["filename"] for c in chunks}),
    }
