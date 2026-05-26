"""
Core prep session logic: generate questions, score answers, track weak topics.
"""
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session as SQLSession, select
from app.models.kb import Session, Question, Answer, Section, WeakTopic
from app.services.llm import generate_mcqs, generate_clarification
from app.services.kb import engine
from app.core.config import DEFAULT_QUESTIONS_PER_SECTION


def get_weak_topics_for_sections(section_ids: List[int], limit: int = 3) -> List[str]:
    """
    Retrieve topics user has struggled with in given sections.

    Args:
        section_ids: List of section IDs to check
        limit: Max number of weak topics to return

    Returns:
        List of topic names (strings)
    """
    with SQLSession(engine) as session:
        stmt = (
            select(WeakTopic.topic_name)
            .where(WeakTopic.section_id.in_(section_ids))
            .order_by(WeakTopic.times_wrong.desc())
            .limit(limit)
        )
        topics = session.exec(stmt).all()
    return topics


def create_session(user_id: str, section_ids: List[int]) -> Session:
    """
    Create a new prep session.

    Args:
        user_id: User identifier
        section_ids: List of section IDs to study

    Returns:
        Session object
    """
    session = Session(
        user_id=user_id,
        started_at=datetime.utcnow(),
        section_ids_csv=",".join(map(str, section_ids))
    )

    with SQLSession(engine) as db_session:
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

    return session


def generate_questions_for_session(
        session_id: int,
        section_ids: List[int],
        num_questions_per_section: int = DEFAULT_QUESTIONS_PER_SECTION
) -> List[Question]:
    """
    Generate MCQs for a session, considering weak topics for adaptation.

    Args:
        session_id: ID of the session
        section_ids: List of section IDs
        num_questions_per_section: Questions per section

    Returns:
        List of Question objects (saved to DB)
    """
    questions_list = []

    with SQLSession(engine) as db_session:
        for section_id in section_ids:
            # Get section text
            section = db_session.get(Section, section_id)
            if not section:
                print(f"⚠️ Section {section_id} not found")
                continue

            # Get weak topics for this section
            weak_topics = get_weak_topics_for_sections([section_id], limit=2)

            # Generate MCQs with adaptation
            mcq_list = generate_mcqs(
                section_text=section.raw_text,
                section_title=section.title,
                num_questions=num_questions_per_section,
                weak_topics=weak_topics if weak_topics else None
            )

            # Save questions to DB
            for mcq in mcq_list:
                question = Question(
                    session_id=session_id,
                    section_id=section_id,
                    question=mcq["question"],
                    choice_a=mcq["choice_a"],
                    choice_b=mcq["choice_b"],
                    choice_c=mcq["choice_c"],
                    choice_d=mcq["choice_d"],
                    correct_answer=mcq["correct_answer"],
                    explanation=mcq["explanation"]
                )
                db_session.add(question)
                questions_list.append(question)

        db_session.commit()

    return questions_list


def submit_answers(
        session_id: int,
        answers_dict: dict
) -> dict:
    """
    Score user answers and update weak topics.

    Args:
        session_id: Session ID
        answers_dict: {question_id: user_answer_letter}
        Example: {1: "A", 2: "B", 3: "C"}

    Returns:
        {
            "session_id": int,
            "total_questions": int,
            "correct": int,
            "score_percentage": float,
            "results": [
                {
                    "question_id": int,
                    "question": str,
                    "user_answer": str,
                    "correct_answer": str,
                    "is_correct": bool,
                    "explanation": str,
                    "clarification": str (optional)
                }
            ]
        }
    """
    results = []
    correct_count = 0
    weak_topics_to_add = []

    with SQLSession(engine) as db_session:
        # Get all questions for this session
        stmt = select(Question).where(Question.session_id == session_id)
        questions = db_session.exec(stmt).all()

        for question in questions:
            user_answer = answers_dict.get(question.id, "")
            is_correct = user_answer.upper() == question.correct_answer.upper()

            if is_correct:
                correct_count += 1

            # Generate clarification for wrong answers
            clarification = None
            if not is_correct and user_answer:
                section = db_session.get(Section, question.section_id)
                clarification = generate_clarification(
                    question=question.question,
                    user_answer=user_answer,
                    correct_answer=question.correct_answer,
                    section_text=section.raw_text if section else ""
                )

                # Track weak topic
                weak_topics_to_add.append({
                    "section_id": question.section_id,
                    "topic": question.question[:50],  # Use question start as topic
                    "session_id": session_id
                })

            # Save answer
            answer = Answer(
                question_id=question.id,
                user_answer=user_answer,
                is_correct=is_correct,
                clarification=clarification
            )
            db_session.add(answer)

            results.append({
                "question_id": question.id,
                "question": question.question,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
                "clarification": clarification
            })

        # Update session score
        total_questions = len(questions)
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0

        session = db_session.get(Session, session_id)
        session.completed_at = datetime.utcnow()
        session.score = score_percentage

        # Add weak topics
        for weak_topic_info in weak_topics_to_add:
            # Check if topic exists
            stmt = select(WeakTopic).where(
                (WeakTopic.section_id == weak_topic_info["section_id"]) &
                (WeakTopic.topic_name == weak_topic_info["topic"])
            )
            existing = db_session.exec(stmt).first()

            if existing:
                existing.times_wrong += 1
                existing.last_session_id = weak_topic_info["session_id"]
                existing.last_seen = datetime.utcnow()
            else:
                new_weak_topic = WeakTopic(
                    section_id=weak_topic_info["section_id"],
                    topic_name=weak_topic_info["topic"],
                    times_wrong=1,
                    last_session_id=weak_topic_info["session_id"]
                )
                db_session.add(new_weak_topic)

        db_session.commit()

    return {
        "session_id": session_id,
        "total_questions": total_questions,
        "correct": correct_count,
        "score_percentage": score_percentage,
        "results": results
    }


def get_session_details(session_id: int) -> Optional[dict]:
    """
    Retrieve full session details with all questions and answers.
    """
    with SQLSession(engine) as db_session:
        session = db_session.get(Session, session_id)
        if not session:
            return None

        stmt = select(Question).where(Question.session_id == session_id)
        questions = db_session.exec(stmt).all()

        questions_data = []
        for q in questions:
            stmt_answers = select(Answer).where(Answer.question_id == q.id)
            answer = db_session.exec(stmt_answers).first()

            questions_data.append({
                "question_id": q.id,
                "section_id": q.section_id,
                "question": q.question,
                "choices": {
                    "A": q.choice_a,
                    "B": q.choice_b,
                    "C": q.choice_c,
                    "D": q.choice_d
                },
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "user_answer": answer.user_answer if answer else None,
                "is_correct": answer.is_correct if answer else None,
                "clarification": answer.clarification if answer else None
            })

        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "score_percentage": session.score,
            "section_ids": [int(x) for x in session.section_ids_csv.split(",")],
            "questions": questions_data
        }