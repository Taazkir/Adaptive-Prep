"""
REST API endpoints for the prep system.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List
from pydantic import BaseModel

from app.services.prep import (
    create_session,
    generate_questions_for_session,
    submit_answers,
    get_session_details
)
from app.services.kb import export_kb_snapshot

router = APIRouter(prefix="/prep", tags=["prep"])


# Request/Response Models
class StartPrepRequest(BaseModel):
    user_id: str
    section_ids: List[int]


class StartPrepResponse(BaseModel):
    session_id: int
    user_id: str
    section_ids: List[int]
    questions: list


class SubmitAnswersRequest(BaseModel):
    session_id: int
    answers: dict  # {question_id: "A"/"B"/"C"/"D"}


class SubmitAnswersResponse(BaseModel):
    session_id: int
    total_questions: int
    correct: int
    score_percentage: float
    results: list


# Endpoints

@router.post("/start", response_model=StartPrepResponse)
def start_prep(request: StartPrepRequest):
    """
    Start a new prep session and generate MCQs.

    Args:
        user_id: User identifier
        section_ids: List of section IDs to study (e.g., [1, 3, 5])

    Returns:
        Session details with generated questions
    """
    try:
        # Create session
        session = create_session(
            user_id=request.user_id,
            section_ids=request.section_ids
        )

        # Generate questions (considers weak topics for adaptation)
        questions = generate_questions_for_session(
            session_id=session.id,
            section_ids=request.section_ids
        )

        # Format questions for response
        questions_data = [
            {
                "question_id": q.id,
                "section_id": q.section_id,
                "question": q.question,
                "choices": {
                    "A": q.choice_a,
                    "B": q.choice_b,
                    "C": q.choice_c,
                    "D": q.choice_d
                }
            }
            for q in questions
        ]

        return StartPrepResponse(
            session_id=session.id,
            user_id=session.user_id,
            section_ids=request.section_ids,
            questions=questions_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting prep: {str(e)}")


@router.post("/submit-answers", response_model=SubmitAnswersResponse)
def submit_prep_answers(request: SubmitAnswersRequest):
    """
    Submit answers for a prep session and receive scoring.

    Args:
        session_id: ID of the session
        answers: Dict mapping question_id to answer letter (A/B/C/D)
                Example: {"1": "A", "2": "C", "3": "B"}

    Returns:
        Session score, results with clarifications for wrong answers
    """
    try:
        # Convert string keys to integers if needed
        answers_dict = {int(k) if isinstance(k, str) else k: v for k, v in request.answers.items()}

        result = submit_answers(
            session_id=request.session_id,
            answers_dict=answers_dict
        )

        return SubmitAnswersResponse(
            session_id=result["session_id"],
            total_questions=result["total_questions"],
            correct=result["correct"],
            score_percentage=result["score_percentage"],
            results=result["results"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting answers: {str(e)}")


@router.get("/session/{session_id}")
def get_session(session_id: int):
    """
    Retrieve full details of a completed session.
    """
    try:
        session_data = get_session_details(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")


@router.get("/kb-snapshot")
def kb_snapshot():
    """
    Export a snapshot of the knowledge base (top 5 recent sessions + weak topics).
    Used for evaluation and verification of adaptive behavior.
    """
    try:
        snapshot = export_kb_snapshot(limit=5)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting KB snapshot: {str(e)}")