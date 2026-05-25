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