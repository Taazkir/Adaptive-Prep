from pathlib import Path
from typing import List
from sqlmodel import SQLModel, create_engine, Session, select


# Engine
DB_PATH = "adaptive.db"
_db_file = Path(DB_PATH).resolve()
engine = create_engine(f"sqlite:///{_db_file}", echo=False, future=True)

# Table Creation
def create_db_and_tables():
    from app.models import kb as _
    SQLModel.metadata.create_all(engine)
    print(f"✓ DB ready at {_db_file}")

# Query Helpers
from models.kb import Section, Session as PrepSession, Question, Answer

def get_section(section_id: int) -> Optional[Section]:
    with Session(engine) as s:
        return s.get(Section, section_id)


def get_last_sections(limit: int = 5) -> List[Section]:
    with Session(engine) as s:
        stmt = select(Section).order_by(Section.id.desc()).limit(limit)
        return list(s.exec(stmt))