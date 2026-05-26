from app.services.prep import create_session, generate_questions_for_session
from app.models.kb import Section
from app.services.kb import engine
from sqlmodel import Session, select

# Create a test session
print("1️⃣ Creating session...")
session = create_session(user_id="test_user", section_ids=[1, 2])
print(f"✅ Session created: ID={session.id}")

# Try to generate questions
print("\n2️⃣ Generating questions for sections [1, 2]...")
try:
    questions = generate_questions_for_session(
        session_id=session.id,
        section_ids=[1, 2],
        num_questions_per_section=2
    )
    print(f"✅ Questions generated: {len(questions)}")
    for q in questions:
        print(f"   - Q{q.id}: {q.question[:60]}...")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Verify they were saved to DB
print("\n3️⃣ Verifying DB has questions...")
with Session(engine) as s:
    from app.models.kb import Question
    stmt = select(Question).where(Question.session_id == session.id)
    saved_questions = list(s.exec(stmt))
    print(f"✅ Questions in DB: {len(saved_questions)}")
    for q in saved_questions:
        print(f"   - Q{q.id}: {q.question[:60]}...")