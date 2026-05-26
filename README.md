# 📘 Adaptive Document Preparation System
An AI-powered backend system that ingests structured PDF documents, generates MCQs using an LLM, evaluates user responses, and builds an adaptive knowledge base that improves future question generation based on user weaknesses.

# 🚀 Features
## 📄 PDF ingestion into structured sections
## 🤖 LLM-powered MCQ generation (Groq / OpenAI-compatible / local LLM supported)
## 🧠 Adaptive learning via persistent Knowledge Base (KB)
## 📊 Auto-scoring and explanations for answers
## 🔁 Weak-topic tracking across sessions
## 📦 Session snapshot export for evaluation
## ⚡ REST API-first architecture (FastAPI)
## 🏗️ Tech Stack
## Backend: FastAPI (Python)
## Database: SQLite (SQLModel)
## LLM: Groq / OpenAI-compatible / local LLM (configurable)
## PDF Parsing: PyMuPDF
## Orchestration: Custom service layer (app/services)
## Testing: curl-based workflow + optional scripts

# 📂 Project Structure

```
adaptive-prep/
│── app/
│   ├── main.py
│   ├── routers/
│   │   └── prep.py
│   ├── services/
│   │   ├── prep.py
│   │   ├── kb.py
│   │   └── llm.py
│   ├── models/
│   │   └── kb.py
│   └── core/
│       └── config.py
│
│── scripts/
│   ├── init_db.py
│   └── ingest_pdf.py
│
│── adaptive.db
│── SLATEFALL_DOSSIER.pdf
│── requirements.txt

```

# ⚙️ Setup Instructions

1. Clone repo
```
git clone <your-repo-url>
cd adaptive-prep
```
3. Create virtual environment
```
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
```
5. Install dependencies
```
pip install -r requirements.txt

```
7. Setup environment variables

```
Create .env:
GROQ_API_KEY=your_key_here

```
9. Initialize database
```
python -m scripts.init_db
Expected:
DB created at adaptive.db
```
11. Ingest PDF into sections
```
python -m scripts.ingest_pdf
Expected:
Found 10 sections
Sections inserted
```
13. Run API server
```
uvicorn app.main:app --reload
Server:
http://127.0.0.1:8000
```

# 🔁 Core API Workflow

1. Start Prep Session
```
curl -X POST "http://127.0.0.1:8000/prep/start" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "test_user",
  "section_ids": [5,8]
}'
Response:
session_id
generated MCQs
section mapping
```
3. Submit Answers
```
curl -X POST "http://127.0.0.1:8000/prep/submit-answers" \
-H "Content-Type: application/json" \
-d '{
  "session_id": 1,
  "answers": {
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "D",
    "5": "A"
  }
}'
Response includes:
score
per-question feedback
explanations
corrections for wrong answers
```
4. Get Knowledge Base Snapshot
```
curl -X GET "http://127.0.0.1:8000/prep/kb-snapshot"
```

Output:
recent sessions
weak topics across sessions
historical performance tracking

# 🧪 Evaluation Scenarios

✅ Scenario A — Cold Start
Step 1
```
curl -X POST "http://127.0.0.1:8000/prep/start" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "user_a",
  "section_ids": [5,8]
}'
```
Step 2

Submit answers (simulate any mix)
```
curl -X POST "http://127.0.0.1:8000/prep/submit-answers" \
-H "Content-Type: application/json" \
-d '{
  "session_id": 1,
  "answers": {
    "1": "A",
    "2": "C",
    "3": "B",
    "4": "D",
    "5": "A"
  }
}'

```
Step 3
```
curl -X GET "http://127.0.0.1:8000/prep/kb-snapshot"

```
🔁 Scenario B — Adaptive Learning (IMPORTANT)

This demonstrates the core evaluation requirement: history-aware adaptation
Iteration 1 (baseline learning)
```
curl -X POST "http://127.0.0.1:8000/prep/start" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "adaptive_user",
  "section_ids": [5,8]
}'

```

Submit answers:
```
curl -X POST "http://127.0.0.1:8000/prep/submit-answers" \
-H "Content-Type: application/json" \
-d '{
  "session_id": 1,
  "answers": {
    "1": "A",
    "2": "B",
    "3": "D",
    "4": "A",
    "5": "C"
  }
}'
```

Save snapshot:
```
curl -X GET "http://127.0.0.1:8000/prep/kb-snapshot" > outputs/scenario_b_iter1.json
Iteration 2 (repeat + observe adaptation)
curl -X POST "http://127.0.0.1:8000/prep/start" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "adaptive_user",
  "section_ids": [6,8,9]
}'
```

Submit answers:
```
curl -X POST "http://127.0.0.1:8000/prep/submit-answers" \
-H "Content-Type: application/json" \
-d '{
  "session_id": 2,
  "answers": {
    "6": "A",
    "7": "C",
    "8": "D",
    "9": "B",
    "10": "A"
  }
}'
```

Save snapshot:

```
curl -X GET "http://127.0.0.1:8000/prep/kb-snapshot" > outputs/scenario_b_iter2.json

```
Iteration 3 (weak-topic reinforcement)
```
curl -X POST "http://127.0.0.1:8000/prep/start" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "adaptive_user",
  "section_ids": [8]
}'
```

Submit answers:

```
curl -X POST "http://127.0.0.1:8000/prep/submit-answers" \
-H "Content-Type: application/json" \
-d '{
  "session_id": 3,
  "answers": {
    "11": "A",
    "12": "B",
    "13": "C",
    "14": "D",
    "15": "A"
  }
}'
```

Save snapshot:
```
curl -X GET "http://127.0.0.1:8000/prep/kb-snapshot" > outputs/scenario_b_iter3.json
```

# 📦 Expected Output Structure
```
outputs/
└── scenario_b/
    ├── iter1_kb.json
    ├── iter2_kb.json
    └── iter3_kb.json
```

# 🧠 What Reviewers Should Observe

After Iteration 1:
- baseline weak topics created

After Iteration 2:
- overlapping weak topics tracked
- repeated mistakes aggregated

After Iteration 3:
- MCQs should shift toward weak topics
- repeated concepts reduced
- stronger personalization signal

# 📌 Key Design Highlights

1. Adaptive KB

Tracks:
- question-level correctness
- topic-level aggregation
- repeated mistakes weighting 

2. Session Persistence

Each session stores:
- questions asked
- user answers
- correctness
- explanations

4. Adaptive Prompting (core requirement)

- LLM receives:
- weak topics
- prior mistakes
- section context


# ⚠️ Assumptions

- PDF is clean text (non-scanned)
- Section IDs are stable post-ingestion
- LLM returns structured MCQs
- User input simulated or manual via curl

# 🧪 Quick Test Command (Full Flow)
```
python -m scripts.init_db && \
python -m scripts.ingest_pdf && \
uvicorn app.main:app --reload
```

Then run Scenario B curl commands above.

# 🏁 Final Notes

This system is designed to demonstrate:
- real-world LLM orchestration
- memory + adaptation layer
- production-style backend architecture
- evaluation-driven design
