# AI Research Roadmap Agent (HAI Term Project 2026)

An explainable, web-based AI research assistant designed for **Computer Science (CS)**, **Scientific Computing (SC)**, **Artificial Intelligence (AI)**, and **Information Systems (IS)** students and researchers.

- **Active HAI Principle:** **Explainability** — Every recommendation is ranked deterministically by the backend over a curated paper corpus before the language model phrases the guidance.
- **Course:** Human, Computer, and AI Interaction (HAI / HCAI) — Term Project 2026.

---

## System Architecture & Pipeline

1. **Accessible Web Interface (`frontend/`):** Semantic HTML/CSS/JS workspace with a 5-stage step indicator, persistent profile strip, quick-reply chips, full-profile paste shortcut, a dedicated **"Why this?"** explainability panel, and built-in accessibility controls (100%–200% text scaling, High Contrast mode, Plain Language toggle, and full keyboard navigation).
2. **Scope & Safety Gate (`backend/reason_builder.py`):** Detects out-of-scope topics (outside CS, SC, AI, IS) and high-risk requests (guaranteed novelty, guaranteed acceptance, exact APC fees/deadlines, or fabricating citations) and routes them to safe fallback or human-handover messages.
3. **Grounded Retrieval & Reason Builder (`backend/init_db.py`, `backend/reason_builder.py`):** Queries a local **SQLite + FTS5** database of **12 verified CC BY 4.0 papers (2025–2026)** (3 per department, planned expansion to 32) and **3 publication venues**, computing explicit match scores, skill overlaps, hardware compatibility, and documented paper limitations.
4. **Constrained Language Generation & Citation Verification (`backend/app.py`):** Calls **`gemini-3.1-flash-lite`** via the official `google-genai` SDK with a strict evidence-only system prompt (`temperature=0.2`), verifies all cited paper IDs against the retrieved set, and falls back gracefully to backend-computed reasons on API timeout or error.

---

## Repository Structure

```text
repo/
├── backend/
│   ├── data/
│   │   ├── corpus.json        # 12 curated CC BY 4.0 papers + 3 venues
│   │   └── research.db        # Generated SQLite + FTS5 database
│   ├── app.py                 # Flask server & grounded /recommend pipeline
│   ├── reason_builder.py      # Scope check, FTS5 retrieval, reason builder & citation check
│   ├── init_db.py             # Builds research.db from corpus.json
│   ├── first_call.py          # Initial Gemini API verification script
│   ├── list_models.py         # Lists models accessible to the API key
│   ├── speed_test.py          # Latency benchmark across Gemini models
│   ├── test_chat.py           # Local endpoint test client
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variable template (no real keys)
├── frontend/
│   ├── index.html             # Accessible chat & "Why this?" UI
│   ├── style.css              # High-contrast & scalable styling
│   └── app.js                 # State management, Undo, onboarding & API client
├── docs/
│   └── Week 5.pptx            # Flow, architecture, Shneiderman checklist & prompt log
├── .gitignore
└── README.md
```

---

## Setup & How to Run Locally (Windows)

### 1. Clone and create virtual environment
```cmd
git clone https://github.com/AbdallahEmad111/HCAI-Project.git
cd HCAI-Project\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key
Copy `.env.example` to `.env` inside `backend/` and add your Google AI Studio key:
```env
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

### 3. Build the SQLite FTS5 Database
```cmd
python init_db.py
```

### 4. Start the Server and Open the Web App
```cmd
python app.py
```
Open `[http://127.0.0.1:5000](http://127.0.0.1:5000)` in your browser.

---

## Current Scope & Planned Work
- **Implemented:** End-to-end grounded chat, deterministic "Why this?" explainability engine, scope/handover safeguards, citation validator, 5-stage progress bar, persistent profile strip, full-profile paste shortcut, Undo/Start Over controls, and accessibility modes.
- **Planned:** Expanding the curated paper corpus from 12 verified papers to 32 papers and running the 30+ prompt automated evaluation harness.