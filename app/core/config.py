import os
from dotenv import load_dotenv

load_dotenv()

# LLM Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast, free tier friendly


# DB Config
DB_PATH = os.getenv("DB_PATH", "adaptive.db")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_store")

# Prep Config
DEFAULT_QUESTIONS_PER_SECTION = 5
