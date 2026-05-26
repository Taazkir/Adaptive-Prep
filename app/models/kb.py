from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# Get text by section from PDF
class Section(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    page_start: int
    page_end: int
    raw_text: str

# A prep session
class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    started_at: datetime
    section_ids_csv: str

    questions: List["Question"] = Relationship(back_populates="session")


# Generate MCQ
class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    section_id: int = Field(foreign_key="section.id")

    question: str
    choice_a: str
    choice_b: str
    choice_c: str
    choice_d: str
    correct_answer: str
    explanation: str

    session: Session = Relationship(back_populates="questions")
    answers: List["Answer"] = Relationship(back_populates="questions")

# User Answers
class Answer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    user_answer_id: str
    is_correct: bool

    questions: Question = Relationship(back_populates="answers")

# Track weak topics for adaptation
class WeakTopic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    section_id: int = Field(foreign_key="section.id")
    topic_name: str
    times_wrong: int = 1
    last_session_id: int = Field(foreign_key="session.id")
    last_seen: datetime = Field(default_factory=datetime.utcnow)



