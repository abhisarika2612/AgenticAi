# LastMinute AI — Backend API

AI-powered last-minute doubt resolver for students. Built with FastAPI + Claude + ChromaDB.

---

## Quick Start

### 1. Install system dependency (Tesseract OCR)
```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Windows — download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 4. Run the server
```bash
uvicorn main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

---

## Project Structure

```
lastminute-ai/
├── main.py                  # FastAPI app entry point
├── config.py                # Settings from .env
├── database.py              # SQLite metadata store
├── requirements.txt
├── .env.example
├── routers/
│   ├── ingest.py            # Document upload & ingestion
│   ├── qa.py                # RAG-powered Q&A
│   ├── practice.py          # Past paper practice engine
│   └── mindmap.py           # Mind map generation
└── services/
    ├── parser.py            # PDF/DOCX/Image/OCR parser
    ├── vector_store.py      # ChromaDB embeddings & search
    └── claude.py            # All Claude API calls
```

---

## API Endpoints

### Session Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingest/session` | Create a new study session |
| DELETE | `/api/ingest/session/{session_id}` | Delete session + all data |

### Document Ingestion
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingest/upload/{session_id}` | Upload notes (PDF/DOCX/PNG/TXT) |
| GET | `/api/ingest/documents/{session_id}` | List uploaded documents |

### Q&A (Core Feature)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/qa/ask` | Ask a doubt, get grounded answer |
| POST | `/api/qa/suggest` | Get auto-suggested questions |
| GET | `/api/qa/history/{session_id}` | View Q&A history |

### Practice Engine
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/practice/upload-paper/{session_id}` | Upload past exam paper |
| GET | `/api/practice/questions/{session_id}` | Get practice questions |
| POST | `/api/practice/submit` | Submit answer, get evaluated |
| GET | `/api/practice/readiness/{session_id}` | Get readiness score % |
| GET | `/api/practice/priority-topics/{session_id}` | High-frequency exam topics |

### Mind Map
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mindmap/generate` | Generate topic mind map |

---

## Frontend Integration Examples

### 1. Create session + upload notes
```javascript
// Create session
const { session_id } = await fetch('/api/ingest/session', {
  method: 'POST',
  body: new URLSearchParams({ label: 'Physics Exam' })
}).then(r => r.json());

// Upload PDF notes
const form = new FormData();
form.append('files', pdfFile);
const upload = await fetch(`/api/ingest/upload/${session_id}`, {
  method: 'POST', body: form
}).then(r => r.json());
```

### 2. Ask a doubt
```javascript
const result = await fetch('/api/qa/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id, question: "What is photosynthesis?" })
}).then(r => r.json());

// result.answer  → grounded answer text
// result.sources → ["Physics Notes — Page 3", ...]
// result.confidence → "high" | "medium" | "low"
```

### 3. Practice with past papers
```javascript
// Upload past paper
const form = new FormData();
form.append('file', pastPaperFile);
await fetch(`/api/practice/upload-paper/${session_id}`, {
  method: 'POST', body: form
});

// Get questions
const { questions } = await fetch(
  `/api/practice/questions/${session_id}`
).then(r => r.json());

// Submit answer
const eval = await fetch('/api/practice/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id, 
    question: questions[0].question,
    student_answer: "My answer here",
    marks: questions[0].marks
  })
}).then(r => r.json());

// eval.score, eval.feedback, eval.model_answer, eval.weak_area
```

### 4. Get readiness score
```javascript
const { overall_readiness, topic_scores, weak_areas } = 
  await fetch(`/api/practice/readiness/${session_id}`).then(r => r.json());
// overall_readiness → 72 (percentage)
```

### 5. Generate mind map
```javascript
const { mind_map } = await fetch('/api/mindmap/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id })
}).then(r => r.json());
// mind_map.root → "Chemistry"
// mind_map.nodes → [{id, label, parent, level, description}, ...]
```

---

## Deployment

### Free tier (recommended for hackathon)

**Frontend → Vercel**
```bash
# In your React frontend directory
vercel deploy
```

**Backend → Railway**
```bash
# Add a Procfile:
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
railway up
```

Set these environment variables in Railway dashboard:
- `ANTHROPIC_API_KEY` — your key
- `OPENAI_API_KEY` — optional, for better embeddings

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI |
| LLM | Claude Sonnet (Anthropic) |
| Embeddings | OpenAI text-embedding-3-small (or fallback) |
| Vector Store | ChromaDB (local persistent) |
| PDF Parsing | PyMuPDF (fitz) |
| OCR | Tesseract via pytesseract |
| Database | SQLite via aiosqlite |
| Deployment | Vercel (frontend) + Railway (backend) |
