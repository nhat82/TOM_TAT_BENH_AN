# Backend — FastAPI Medical Record RAG Server

FastAPI server providing patient data access, CSV ingestion into ChromaDB, and LLM-powered summarization and streaming Q&A via LangGraph graphs.

## Architecture

```
app/
├── main.py               # FastAPI app + router registration
├── routers/
│   ├── ingest.py         # POST /api/ingest
│   ├── patient.py        # GET  /api/patient/{id}
│   ├── summary.py        # POST /api/summary
│   └── chat.py           # POST /api/chat  (SSE streaming)
├── services/
│   ├── llm.py            # Google Gemini singleton (lazy init)
│   ├── chroma.py         # ChromaDB client + collection factory
│   └── ingest.py         # CSV → embed → upsert pipeline
└── graphs/
    ├── summary_graph.py  # LangGraph: retrieve → timeline → draft
    └── chat_graph.py     # LangGraph: embed → retrieve → answer (MemorySaver)
```

## Setup

### 1. Python environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
# Edit .env — at minimum set GOOGLE_API_KEY
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Google Generative AI API key |
| `GEMINI_API_KEY` | Alt. | — | Alias for `GOOGLE_API_KEY` |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | Model for generation |
| `GEMINI_JUDGE_MODEL` | No | `gemini-2.0-flash-lite` | Model for evaluation |
| `CHROMA_PATH` | No | `./data/chromadb` | ChromaDB storage path |
| `JUDGE_MAX_WAIT` | No | `900` | Max seconds to wait on rate limits |

### 3. Data directory

```bash
mkdir -p data/chromadb
# Place your CSV in data/ (default: data/Sample_20BN.csv)
```

## Running

**Development (with auto-reload):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Docker:**
```bash
docker build -t tom-tat-backend .
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  tom-tat-backend
```

## API Reference

### `POST /api/ingest`

Reads the CSV, embeds patient records with the Vietnamese bi-encoder, and upserts into ChromaDB. Skips records whose content hash has not changed (use `force: true` to re-embed everything).

**Request:**
```json
{ "force": false }
```

**Response:**
```json
{ "added": 18, "skipped": 2 }
```

---

### `GET /api/patient/{patient_id}`

Returns all CSV columns for a single patient as a flat JSON object.

**Response:**
```json
{
  "patient_id": "BN0052",
  "data": {
    "ma_bn_an": "BN0052",
    "ho_ten": "Nguyễn Văn A",
    ...
  }
}
```

---

### `POST /api/summary`

Runs the LangGraph summary graph for the given patient and returns a structured medical summary with a chronological event timeline.

**Request:**
```json
{ "ma_bn_an": "BN0052" }
```

**Response:**
```json
{
  "patient_id": "BN0052",
  "summary": "Bệnh nhân ...",
  "timeline": [
    { "date": "2024-01-15", "event": "Nhập viện", "detail": "..." }
  ],
  "chunks_used": 6
}
```

---

### `POST /api/chat` (Server-Sent Events)

Streams an LLM answer for a patient-scoped question. Chat history is passed in the request; state is also persisted per patient via LangGraph MemorySaver (keyed by `id_benh_nhan`).

**Request:**
```json
{
  "id_benh_nhan": "BN0052",
  "query": "Chẩn đoán chính của bệnh nhân là gì?",
  "chat_history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response** — `text/event-stream`:
```
data: {"type": "token",  "content": "Bệnh nhân "}
data: {"type": "token",  "content": "được chẩn đoán "}
...
data: {"type": "done",   "sources": ["BN0052"]}
```

On error:
```
data: {"type": "error", "detail": "Patient not found in ChromaDB"}
```

---

### `GET /`

Health check. Returns `{ "message": "OK" }`.

## LangGraph Graphs

### Summary Graph (`graphs/summary_graph.py`)

```
[retrieve]
  ChromaDB similarity search → split into chunks → rerank by score

[build_timeline]
  LLM prompt → extract chronological events as JSON array

[draft_summary]
  LLM prompt → write comprehensive Vietnamese medical summary
```

### Chat Graph (`graphs/chat_graph.py`)

```
[embed_question]
  Encode user question with Vietnamese bi-encoder

[retrieve_chunks]
  Fetch patient document from ChromaDB → rank chunks by cosine similarity

[generate_answer]
  LLM prompt with context + full chat history → streaming tokens
```

Conversation state is persisted using LangGraph's `MemorySaver`. Each patient has its own thread (`thread_id = patient_id`).

## CLI Utilities

```bash
# Ingest CSV into ChromaDB
python -m app.services.ingest ingest
python -m app.services.ingest ingest --csv data/Sample_BN_2026.csv --force

# Show ChromaDB record count
python -m app.services.ingest stats
```

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `langgraph` | Graph orchestration + MemorySaver |
| `langchain-google-genai` | Gemini integration |
| `chromadb` | Vector database |
| `sentence-transformers` | Vietnamese bi-encoder embeddings |
| `pandas` | CSV processing |
| `pydantic` | Request/response validation |

## Troubleshooting

**"Patient not found in ChromaDB"**
Call `POST /api/ingest` first to populate the vector database.

**Rate limit errors (429)**
Google Free Tier limits: 15 RPM / 1000 RPD / 250K TPM. Reduce concurrent requests or wait for quota reset.

**Slow first request**
The Vietnamese bi-encoder model is downloaded and loaded on first use (~400MB). Subsequent requests are fast.

**Missing API key**
Ensure `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) is exported before starting the server.
