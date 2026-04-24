"""
services/claude.py — All Claude API interactions
Handles: RAG Q&A, practice evaluation, mind map generation, topic suggestions
"""

import anthropic
import json
from typing import List, Dict, Any

from config import get_settings

settings = get_settings()
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _call_claude(system: str, user_message: str, max_tokens: int = None) -> str:
    """Base wrapper for all Claude API calls."""
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens or settings.claude_max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


# ─── RAG Q&A ──────────────────────────────────────────────────────────────────

def answer_doubt(
    question: str,
    context_chunks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Answer a student's doubt using only the retrieved context chunks.
    Returns answer text + cited sources.
    """
    if not context_chunks:
        return {
            "answer": "No relevant notes found for this question. Please upload your notes first.",
            "sources": [],
            "confidence": "none",
        }

    # Build context block
    context_block = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_block += f"\n[{i}] SOURCE: {chunk['source_label']}\n{chunk['text']}\n"

    system_prompt = """You are a precise exam assistant. Your ONLY job is to answer the student's doubt using the provided notes excerpts.

STRICT RULES:
1. Answer ONLY using information from the provided [SOURCE] excerpts. No outside knowledge.
2. Be concise — 2-5 sentences max for simple doubts. Up to 8 for complex concepts.
3. At the end of your answer, add a JSON block on a new line in this exact format:
   SOURCES_JSON: {"sources": ["Source label 1", "Source label 2"], "confidence": "high|medium|low"}
4. If the answer is NOT in the notes, respond: "This topic isn't covered in your uploaded notes. Try checking your textbook or add more notes."
5. Never make up facts. If unsure, say so."""

    user_message = f"""Student's Notes (retrieved excerpts):
{context_block}

Student's Doubt: {question}"""

    raw = _call_claude(system_prompt, user_message)

    # Parse out the JSON sources block
    answer = raw
    sources = [c["source_label"] for c in context_chunks[:3]]
    confidence = "medium"

    if "SOURCES_JSON:" in raw:
        parts = raw.split("SOURCES_JSON:", 1)
        answer = parts[0].strip()
        try:
            meta = json.loads(parts[1].strip())
            sources = meta.get("sources", sources)
            confidence = meta.get("confidence", "medium")
        except Exception:
            pass

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "context_chunks_used": len(context_chunks),
    }


# ─── PAST PAPER PRACTICE ──────────────────────────────────────────────────────

def extract_questions_from_paper(paper_text: str) -> List[Dict[str, Any]]:
    """
    Extract and categorize questions from a past exam paper.
    Returns list of questions with topic tags.
    """
    system = """You are an expert exam question parser.
Extract all exam questions from the text and return ONLY valid JSON (no markdown, no preamble).
Format: {"questions": [{"question": "...", "topic": "...", "marks": 5, "type": "short/long/mcq"}]}
- topic: the subject topic this question covers
- marks: estimated marks (1-20), guess from context if not explicit
- type: short (1-3 marks), long (4+ marks), mcq (multiple choice)"""

    raw = _call_claude(system, f"Past exam paper:\n\n{paper_text}", max_tokens=2000)

    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean).get("questions", [])
    except Exception:
        return []


def evaluate_student_answer(
    question: str,
    student_answer: str,
    context_chunks: List[Dict[str, Any]],
    marks: int = 5,
) -> Dict[str, Any]:
    """
    Evaluate a student's answer against their uploaded notes.
    Returns score, feedback, and weak areas.
    """
    context_block = "\n".join(
        f"[SOURCE: {c['source_label']}]\n{c['text']}" for c in context_chunks
    )

    system = """You are a strict but encouraging exam evaluator.
Evaluate the student's answer against the notes provided. Return ONLY valid JSON:
{"score": 3, "max_score": 5, "percentage": 60, "grade": "C", 
 "feedback": "...", "correct_points": ["..."], "missing_points": ["..."],
 "model_answer": "...", "weak_area": "..."}
- Be specific in feedback. Quote what the student got right.
- model_answer: what a full-marks answer would look like (from notes only)
- weak_area: the topic/concept the student needs to review"""

    user_msg = f"""Question: {question}
Maximum Marks: {marks}

Reference Notes:
{context_block}

Student's Answer: {student_answer or "(no answer provided)"}"""

    raw = _call_claude(system, user_msg, max_tokens=1000)
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
        result["max_score"] = marks
        return result
    except Exception:
        return {
            "score": 0,
            "max_score": marks,
            "percentage": 0,
            "grade": "F",
            "feedback": "Could not evaluate answer. Please try again.",
            "correct_points": [],
            "missing_points": [],
            "model_answer": "",
            "weak_area": "unknown",
        }


def detect_high_priority_topics(paper_texts: List[str]) -> List[Dict[str, Any]]:
    """
    Analyse multiple past papers and identify frequently tested topics.
    Returns ranked list of topics with frequency and likelihood.
    """
    combined = "\n\n---PAPER BREAK---\n\n".join(paper_texts[:5])

    system = """You are an expert exam strategist. Analyse these past exam papers and identify the most frequently tested topics.
Return ONLY valid JSON:
{"topics": [{"topic": "...", "frequency": 3, "likelihood": "very likely|likely|possible", "subtopics": ["...", "..."]}]}
Sort by frequency descending. Maximum 10 topics."""

    raw = _call_claude(system, f"Past papers:\n\n{combined}", max_tokens=1500)
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean).get("topics", [])
    except Exception:
        return []


# ─── MIND MAP ─────────────────────────────────────────────────────────────────

def generate_mind_map(notes_text: str) -> Dict[str, Any]:
    """
    Generate a hierarchical topic mind map from notes.
    Returns a tree structure for frontend visualization.
    """
    system = """You are an expert at extracting and organizing knowledge.
Analyse the notes and generate a topic mind map. Return ONLY valid JSON:
{
  "root": "Subject Name",
  "nodes": [
    {
      "id": "1",
      "label": "Main Topic",
      "parent": null,
      "level": 1,
      "description": "brief summary"
    },
    {
      "id": "2", 
      "label": "Subtopic",
      "parent": "1",
      "level": 2,
      "description": "brief summary"
    }
  ]
}
- Maximum 3 levels deep
- Maximum 20 nodes total
- Focus on the most important concepts"""

    raw = _call_claude(system, f"Notes:\n\n{notes_text[:4000]}", max_tokens=2000)
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        return {"root": "Your Notes", "nodes": []}


# ─── SMART SUGGESTIONS ────────────────────────────────────────────────────────

def suggest_questions(notes_text: str, count: int = 5) -> List[str]:
    """
    Generate sample doubt questions a student might ask about their notes.
    """
    system = """Generate exam-prep questions a student would ask about these notes.
Return ONLY valid JSON: {"questions": ["...", "...", "..."]}
Questions should be short, conversational, and cover key concepts."""

    raw = _call_claude(system, f"Notes:\n\n{notes_text[:2000]}", max_tokens=500)
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean).get("questions", [])[:count]
    except Exception:
        return []
