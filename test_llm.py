"""Quick test of Groq LLM integration"""
from app.services.llm import generate_mcqs

# Sample section text (use real text from your PDF)
sample_text = """
SLATEFALL is an asset designated PAMC-A2-014. The codename was assigned 
by the PAMC Naming Subcommittee on 7 May 2019, derived from the asset's 
powers-emergence event on the eastern slate face of Cerro Castillo, Aysén 
Region, Chile. Her registry threat-to-handler rating is 0.7 / 5, the 
lowest among PAMC Class A-2 operatives.
"""

try:
    questions = generate_mcqs(
        section_text=sample_text,
        section_title="Identity, Background, and Public Status",
        num_questions=3,
        weak_topics=None
    )

    print("✅ MCQ Generation successful!")
    print(f"Generated {len(questions)} questions:\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q['question']}")
        print(f"   A) {q['choice_a']}")
        print(f"   B) {q['choice_b']}")
        print(f"   C) {q['choice_c']}")
        print(f"   D) {q['choice_d']}")
        print(f"   ✓ Correct: {q['correct_answer']}")
        print(f"   Why: {q['explanation']}\n")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()