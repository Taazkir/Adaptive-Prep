from pathlib import Path
from typing import List
from sqlmodel import SQLModel, create_engine, Session, select
from ..core.config import DB_PATH

# Engine
_path = Path(DB_PATH).expanduser().resolve()
_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{_path}", echo=False, future=True)

# Table Creation
def create_db_and_tables():
    from app.models import kb
    SQLModel.metadata.create_all(engine)
    print(f"DB created at {_path}")

# Query Helpers
from app.models.kb import Section, Session as PrepSession, Question, Answer

def get_session(session_id: int) -> PrepSession | None:
    with Session(engine) as session:
        stmt = select(PrepSession).where(PrepSession.id == session_id)
        return session.exec(stmt).first()


def get_last_sections(limit: int = 5) -> List[Section]:
    with Session(engine) as sess:
        stmt = select(Section).order_by(Section.id.desc()).limit(limit)
        return list(sess.exec(stmt))


# Additional query helpers for weak topics and KB snapshots

def get_recent_sessions(limit: int = 5) -> List[PrepSession]:
    """Get the most recent prep sessions."""
    with Session(engine) as sess:
        stmt = select(PrepSession).order_by(PrepSession.started_at.desc()).limit(limit)
        return list(sess.exec(stmt))


def get_sessions_for_sections(section_ids: List[int], limit: int = 10) -> List[PrepSession]:
    """Get all sessions that involved any of the given section IDs."""
    with Session(engine) as sess:
        # This is a simple contains check - you may want a more sophisticated approach
        results = []
        stmt = select(PrepSession).order_by(PrepSession.started_at.desc()).limit(limit * 2)
        all_sessions = list(sess.exec(stmt))

        for s in all_sessions:
            session_sections = [int(x) for x in s.section_ids_csv.split(",")]
            if any(sec in section_ids for sec in session_sections):
                results.append(s)
            if len(results) >= limit:
                break

        return results


def export_kb_snapshot(limit: int = 5) -> dict:
    """
    Export a human-readable snapshot of the top N recent sessions.
    Useful for evaluation and debugging.
    """
    import json
    from app.models.kb import WeakTopic

    sessions = get_recent_sessions(limit=limit)

    snapshot = {
        "exported_at": datetime.utcnow().isoformat(),
        "recent_sessions": []
    }

    with Session(engine) as sess:
        for s in sessions:
            # Get all questions for session
            stmt = select(Question).where(Question.session_id == s.id)
            questions = list(sess.exec(stmt))

            session_data = {
                "session_id": s.id,
                "user_id": s.user_id,
                "started_at": s.started_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "score_percentage": s.score,
                "section_ids": [int(x) for x in s.section_ids_csv.split(",")],
                "total_questions": len(questions),
                "correct_answers": sum(1 for q in questions for a in q.answers if a.is_correct)
            }

            snapshot["recent_sessions"].append(session_data)

        # Get weak topics
        stmt = select(WeakTopic).order_by(WeakTopic.times_wrong.desc()).limit(10)
        weak_topics = list(sess.exec(stmt))

        snapshot["weak_topics"] = [
            {
                "section_id": wt.section_id,
                "topic": wt.topic_name,
                "times_wrong": wt.times_wrong,
                "last_seen": wt.last_seen.isoformat()
            }
            for wt in weak_topics
        ]

    return snapshot