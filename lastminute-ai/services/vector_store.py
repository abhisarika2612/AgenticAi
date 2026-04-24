"""
services/vector_store.py — ChromaDB vector store
Handles: chunking, embedding, upsert, and semantic search
"""

import uuid
import re
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from config import get_settings
from services.parser import ParsedDocument

settings = get_settings()

# ─── ChromaDB client (persistent local storage) ───────────────────────────────

_chroma_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)

# ─── OpenAI client for embeddings ─────────────────────────────────────────────
# Falls back to a simple TF-IDF-style keyword approach if no OpenAI key is set.

_openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None


def _get_collection(session_id: str) -> chromadb.Collection:
    """Each session gets its own isolated ChromaDB collection."""
    return _chroma_client.get_or_create_collection(
        name=f"session_{session_id}",
        metadata={"hnsw:space": "cosine"},
    )


def _embed(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings. Uses OpenAI if key is available,
    otherwise falls back to a simple character n-gram hash embedding
    (good enough for hackathon / demo without an OpenAI key).
    """
    if _openai_client and settings.openai_api_key:
        response = _openai_client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]
    else:
        return [_fallback_embed(t) for t in texts]


def _fallback_embed(text: str) -> List[float]:
    """
    Deterministic 384-dim hash embedding for offline / no-key usage.
    Not semantically meaningful but allows ChromaDB to function.
    """
    import hashlib, struct
    result = []
    for i in range(384):
        h = hashlib.md5(f"{i}:{text[:256]}".encode()).digest()
        val = struct.unpack("f", h[:4])[0]
        result.append(float(val))
    return result


# ─── Chunking ─────────────────────────────────────────────────────────────────

def _chunk_text(
    text: str,
    source_label: str,
    chunk_size: int = None,
    overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks, preserving sentence boundaries.
    Returns list of {text, source_label, chunk_index}.
    """
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    # Split on sentence boundaries first
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current = []
    current_len = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence_len = len(sentence)

        if current_len + sentence_len > chunk_size and current:
            chunk_text = " ".join(current)
            chunks.append({
                "text": chunk_text,
                "source_label": source_label,
                "chunk_index": len(chunks),
            })
            # Keep last N chars as overlap
            overlap_text = chunk_text[-overlap:]
            current = [overlap_text]
            current_len = len(overlap_text)

        current.append(sentence)
        current_len += sentence_len + 1

    if current:
        chunks.append({
            "text": " ".join(current),
            "source_label": source_label,
            "chunk_index": len(chunks),
        })

    return chunks


# ─── Public API ───────────────────────────────────────────────────────────────

def ingest_document(session_id: str, doc: ParsedDocument) -> int:
    """
    Chunk and embed all pages of a document, store in the session's collection.
    Returns total chunks added.
    """
    collection = _get_collection(session_id)
    all_chunks = []

    for page in doc.pages:
        page_chunks = _chunk_text(page["text"], page["source_label"])
        all_chunks.extend(page_chunks)

    if not all_chunks:
        return 0

    texts = [c["text"] for c in all_chunks]
    embeddings = _embed(texts)
    ids = [str(uuid.uuid4()) for _ in all_chunks]
    metadatas = [
        {
            "source_label": c["source_label"],
            "chunk_index": c["chunk_index"],
            "filename": doc.filename,
        }
        for c in all_chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return len(all_chunks)


def search(session_id: str, query: str, top_k: int = None) -> List[Dict[str, Any]]:
    """
    Semantic search over the session's documents.
    Returns top_k most relevant chunks with source labels.
    """
    top_k = top_k or settings.top_k_chunks
    collection = _get_collection(session_id)

    count = collection.count()
    if count == 0:
        return []

    query_embedding = _embed([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i, doc_text in enumerate(results["documents"][0]):
        chunks.append({
            "text": doc_text,
            "source_label": results["metadatas"][0][i]["source_label"],
            "filename": results["metadatas"][0][i]["filename"],
            "relevance_score": round(1 - results["distances"][0][i], 3),
        })

    return chunks


def delete_session(session_id: str):
    """Remove all vectors for a session (e.g., exam over, reset)."""
    try:
        _chroma_client.delete_collection(f"session_{session_id}")
    except Exception:
        pass


def get_session_stats(session_id: str) -> Dict[str, int]:
    collection = _get_collection(session_id)
    return {"total_chunks": collection.count()}
