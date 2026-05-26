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

    # Truncate section text if too long (Groq has token limits)
    max_chars = 3000
    if len(section_text) > max_chars:
        section_text = section_text[:max_chars] + "\n[... text truncated ...]"

    prompt = f"""You are an expert educational assessment designer. 

Based on the following section from a document, generate exactly {num_questions} multiple-choice questions.

SECTION TITLE: {section_title}

SECTION TEXT:
{section_text}
{weak_context}

REQUIREMENTS:
- Generate exactly {num_questions} questions
- Each question should test understanding of key concepts
- Provide 4 choices (A, B, C, D) for each question
- Clearly mark the correct answer
- Include a brief explanation (1-2 sentences) for why the answer is correct
- Format your response as a JSON array with objects containing:
  {{"question": "...", "choice_a": "...", "choice_b": "...", "choice_c": "...", "choice_d": "...", "correct_answer": "A", "explanation": "..."}}

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
            required_keys = {"question", "choice_a", "choice_b", "choice_c", "choice_d", "correct_answer",
                             "explanation"}
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
    prompt = f"""A user answered a question incorrectly. Provide a brief, clear explanation of why their answer was wrong and why the correct answer is right.

Question: {question}
User's Answer: {user_answer}
Correct Answer: {correct_answer}

Context from document:
{section_text[:1000]}

Provide a concise explanation (2-3 sentences max) that helps them understand."""

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