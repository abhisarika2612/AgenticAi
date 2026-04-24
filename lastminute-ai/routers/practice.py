"""
routers/practice.py — Past Paper Practice Engine
Upload past papers → extract questions → quiz student → evaluate against notes
"""

import aiosqlite
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from services.parser import parse_document
from services.vector_store import search
from services.claude import (
    extract_questions_from_paper,
    evaluate_student_answer,
    detect_high_priority_topics,
)
from database import DB_PATH

router = APIRouter()

# In-memory cache of extracted questions per session (fast for hackathon)
_question_cache: dict = {}


# ─── Upload Past Paper ────────────────────────────────────────────────────────

@router.post("/upload-paper/{session_id}")
async def upload_past_paper(session_id: str, file: UploadFile = File(...)):
    """
    Upload a past exam paper (PDF or image).
    Extracts all questions and caches them for practice.
    """
    file_bytes = await file.read()
    parsed = parse_document(file_bytes, file.filename)

    if parsed.page_count == 0:
        raise HTTPException(status_code=400, detail="Could not extract text from paper")

    paper_text = parsed.full_text
    questions = extract_questions_from_paper(paper_text)

    if not questions:
        raise HTTPException(
            status_code=422,
            detail="No exam questions could be identified in this file"
        )

    if session_id not in _question_cache:
        _question_cache[session_id] = []
    _question_cache[session_id].extend(questions)

    return {
        "filename": file.filename,
        "questions_found": len(questions),
        "total_questions": len(_question_cache[session_id]),
        "questions": questions,
    }


# ─── Get Practice Questions ───────────────────────────────────────────────────

@router.get("/questions/{session_id}")
async def get_questions(
    session_id: str,
    topic: Optional[str] = None,
    question_type: Optional[str] = None,
    limit: int = 10,
):
    """
    Return practice questions for the session.
    Optionally filter by topic or type (short/long/mcq).
    """
    questions = _question_cache.get(session_id, [])

    if topic:
        questions = [q for q in questions if topic.lower() in q.get("topic", "").lower()]
    if question_type:
        questions = [q for q in questions if q.get("type") == question_type]

    return {
        "session_id": session_id,
        "total": len(questions),
        "questions": questions[:limit],
    }


# ─── Submit Answer ────────────────────────────────────────────────────────────

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question: str
    student_answer: str
    marks: Optional[int] = 5
    topic: Optional[str] = ""


@router.post("/submit")
async def submit_answer(req: SubmitAnswerRequest):
    """
    Evaluate a student's answer against their uploaded notes.
    Returns score, feedback, model answer, and weak areas.
    """
    # Find relevant notes chunks for this question
    chunks = search(req.session_id, req.question, top_k=5)

    result = evaluate_student_answer(
        question=req.question,
        student_answer=req.student_answer,
        context_chunks=chunks,
        marks=req.marks,
    )

    # Persist result
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO practice_results
               (session_id, question, student_ans, score, feedback, topic)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (req.session_id, req.question, req.student_answer,
             result.get("score", 0), result.get("feedback", ""), req.topic or "")
        )
        await db.commit()

    return result


# ─── Readiness Score ──────────────────────────────────────────────────────────

@router.get("/readiness/{session_id}")
async def get_readiness(session_id: str):
    """
    Calculate overall exam readiness score based on practice history.
    Returns percentage, per-topic breakdown, and weak areas.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """SELECT topic, score, 
                      (SELECT MAX(marks) FROM (SELECT 5 as marks)) as max_score
               FROM practice_results WHERE session_id = ?""",
            (session_id,)
        )

    if not rows:
        return {
            "overall_readiness": 0,
            "questions_attempted": 0,
            "topic_scores": {},
            "weak_areas": [],
            "message": "No practice attempts yet. Start practicing to see your readiness!",
        }

    topic_data: dict = {}
    for r in rows:
        t = r["topic"] or "General"
        if t not in topic_data:
            topic_data[t] = {"scores": [], "max": 5}
        topic_data[t]["scores"].append(r["score"] or 0)

    topic_scores = {}
    weak_areas = []
    for topic, data in topic_data.items():
        avg = sum(data["scores"]) / len(data["scores"])
        pct = round((avg / data["max"]) * 100)
        topic_scores[topic] = pct
        if pct < 60:
            weak_areas.append(topic)

    all_scores = [s for d in topic_data.values() for s in d["scores"]]
    overall = round(sum(all_scores) / len(all_scores) / 5 * 100) if all_scores else 0

    return {
        "overall_readiness": overall,
        "questions_attempted": len(all_scores),
        "topic_scores": topic_scores,
        "weak_areas": weak_areas,
        "message": _readiness_message(overall),
    }


def _readiness_message(pct: int) -> str:
    if pct >= 85: return "Excellent! You're well-prepared for this exam."
    if pct >= 70: return "Good progress! Focus on your weak areas."
    if pct >= 50: return "Getting there. Keep practicing consistently."
    return "Lots of room to improve. Review your notes and try again."


# ─── High Priority Topics ────────────────────────────────────────────────────

@router.get("/priority-topics/{session_id}")
async def get_priority_topics(session_id: str):
    """
    Analyse uploaded past papers to identify likely exam topics.
    """
    questions = _question_cache.get(session_id, [])
    if not questions:
        return {"topics": [], "message": "Upload past papers to detect high-priority topics."}

    paper_texts = [q["question"] for q in questions]
    topics = detect_high_priority_topics(paper_texts)
    return {"topics": topics, "total_questions_analysed": len(questions)}
