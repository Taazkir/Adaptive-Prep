"""
LLM service for generating adaptive MCQs using Groq.
"""
from typing import Optional, List
import json
from groq import Groq
from app.core.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


def generate_mcqs(
    section_text: str,
    section_title: str,
    num_questions: int = 5,
    weak_topics: Optional[List[str]] = None,
    previous_questions: Optional[List[str]] = None,
) -> List[dict]:
    """
    Generate MCQs from section text using Groq.

    Args:
        section_text: Raw text from the PDF section
        section_title: Title of the section (for context)
        num_questions: Number of questions to generate (default 5)
        weak_topics: List of topics user struggled with (for adaptation)

    Returns:
        List of dicts with keys: question, choice_a, choice_b, choice_c, choice_d,
                                 correct_answer, explanation
    """

    # Build adaptive context
    weak_context = ""
    if weak_topics:
        weak_context = f"\n\nIMPORTANT: The user has struggled with these topics before: {', '.join(weak_topics)}. Focus at least 2-3 questions on these areas to help them improve."

    previous_questions_context = ""
    if previous_questions:
        joined_questions = "\n".join(
            [f"- {q}" for q in previous_questions[:10]]
        )

        previous_questions_context = f"""

    AVOID REPEATING THESE PREVIOUS QUESTIONS:
    {joined_questions}

    Generate NEW questions that test similar concepts differently.
    Do NOT repeat wording verbatim.
    """

    # Truncate section text if too long (Groq has token limits)
    max_chars = 3000
    if len(section_text) > max_chars:
        section_text = section_text[:max_chars] + "\n[... text truncated ...]"

    prompt = f"""
    You are an expert educational assessment designer.

    Generate exactly {num_questions} high-quality multiple choice questions.

    SECTION TITLE:
    {section_title}

    SECTION TEXT:
    {section_text}

    {weak_context}

    {previous_questions_context}

    IMPORTANT RULES:
    - Only generate questions directly supported by the provided text
    - Do NOT hallucinate facts
    - Avoid repeating previous questions verbatim
    - Focus more heavily on weak topics if provided
    - Questions should test comprehension, not trivial memorization
    - Each question must have exactly 4 choices
    - Exactly one correct answer
    - Explanations should be concise and grounded in the text
    - Create a short topic_tag for each question

    Return ONLY valid JSON.

    Required JSON format:

    [
      {{
        "question": "...",
        "choice_a": "...",
        "choice_b": "...",
        "choice_c": "...",
        "choice_d": "...",
        "correct_answer": "A",
        "explanation": "...",
        "topic_tag": "short topic label"
      }}
    ]
Return ONLY valid JSON, no other text."""

    try:
        message = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.choices[0].message.content

        # Parse JSON response
        questions = json.loads(response_text)

        # Validate structure
        for q in questions:
            required_keys = {
                "question",
                "choice_a",
                "choice_b",
                "choice_c",
                "choice_d",
                "correct_answer",
                "explanation",
                "topic_tag"
            }
            if not all(k in q for k in required_keys):
                raise ValueError(f"Question missing required keys: {q}")
            if q["correct_answer"] not in ["A", "B", "C", "D"]:
                raise ValueError(f"Invalid correct_answer: {q['correct_answer']}")

        return questions

    except Exception as e:
        print(f"Error generating MCQs: {e}")
        raise


def generate_clarification(
        question: str,
        user_answer: str,
        correct_answer: str,
        section_text: str,
) -> str:
    """
    Generate a detailed clarification for why the user's answer was wrong.

    Args:
        question: The MCQ question
        user_answer: What the user answered (A/B/C/D)
        correct_answer: Correct answer (A/B/C/D)
        section_text: Section context

    Returns:
        Clarification string
    """
    prompt = f"""
    You are explaining why an answer was incorrect.

    Use ONLY the provided context.
    Do not speculate.
    Do not mention missing context if the answer exists in context.

    Question:
    {question}

    User Answer:
    {user_answer}

    Correct Answer:
    {correct_answer}

    Context:
    {section_text[:1500]}

    Return:
    1-3 concise sentences.
    """

    try:
        message = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.choices[0].message.content
    except Exception as e:
        print(f"Error generating clarification: {e}")
        return "Unable to generate clarification at this time."