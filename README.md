# Tóm Tắt Bệnh Án — Medical Record Summarization System

A Vietnamese healthcare AI system that reads patient records from PostgreSQL and provides structured summarization and conversational Q&A via a web interface.

## Overview

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS |
| Backend API | FastAPI + Uvicorn (async) |
| LLM Orchestration | LangGraph (stateful graphs) |
| Database | PostgreSQL (`medical_records` table) |
| LLM Provider | Google Generative AI (Gemini) |
| Deployment | Docker Compose |

## Architecture

```
┌──────────────────────────────────┐
│           Frontend (Vite:5173)   │
│  Search → View → Summary → Chat  │
└────────────┬─────────────────────┘
             │ /api (proxy)
┌────────────▼─────────────────────┐
│         Backend (FastAPI:8000)   │
│  /patient  /summary  /refine     │
│  /chat (SSE streaming)           │
│  /preview-html  /export-docx     │
│                                  │
│  LangGraph Agents                │
│  ┌─────────────────┐             │
│  │  Summary Agent  │             │
│  │  query DB →     │             │
│  │  fill template  │             │
│  └─────────────────┘             │
│  ┌─────────────────┐             │
│  │  ReAct Chat     │             │
│  │  Agent (Text-   │             │
│  │  to-SQL)        │             │
│  └─────────────────┘             │
└──────────────┬───────────────────┘
               │
         PostgreSQL
```

## Two LangGraph Agents

### Summary Agent (`services/summary_agent/`)
- Queries PostgreSQL directly for the patient's record
- Fills a fixed Vietnamese medical template (34 domain-specific instructions)
- Handles special cases: infertility treatment, miscarriage care, outpatient follow-up
- `run_summary()` — initial generation; `run_refine()` — refine per user instruction

### ReAct Chat Agent (`services/agent_package/`)
- Text-to-SQL: the LLM generates parameterized SQL queries at runtime
- Tools: `list_tables`, `get_table_schema`, `execute_sql_query`
- SQL parameters are bound at execution time to prevent injection
- Per-patient conversation history via LangGraph `MemorySaver` (`thread_id = patient_id`)

## Repository Structure

```
tom_tat_benh_an/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/          # chat, summary, patient
│   │   └── services/
│   │       ├── agent_package/    # ReAct chat agent + SQL tools
│   │       │   └── agents/chatbot_agent.py
│   │       ├── summary_agent/    # Summary + refine graphs
│   │       │   └── summary_graph.py
│   │       ├── database.py       # PostgreSQL connection
│   │       ├── docx_export.py
│   │       └── html_preview.py
│   ├── evaluation/           # Evaluation suite (LLM-judged metrics)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # HomePage, PatientPage
│   │   └── components/       # PatientData, PatientHealthData,
│   │                         # PatientSummaryPanel, ClinicalInsightsPanel
│   ├── vite.config.ts
│   └── package.json
└── docker-compose.yml
```

## Prerequisites

- Docker + Docker Compose, **or** Python 3.11+ and Node 20+
- A Google API key with Generative AI access ([get one here](https://aistudio.google.com/app/apikey))
- PostgreSQL instance with the `medical_records` table

## Quick Start (Docker Compose)

```bash
# 1. Clone the repo
git clone <repo-url>
cd tom_tat_benh_an

# 2. Create backend/.env
cat > backend/.env <<EOF
GOOGLE_API_KEY=your_key_here
PG_URI=postgresql://user:pass@host:5432/dbname
EOF

# 3. Start all services
docker-compose up

# Frontend → http://localhost:5173
# Backend  → http://localhost:8000
```

## Local Development

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev    # http://localhost:5173
```

## Workflow

1. **View** — `GET /api/patient/{id}` returns raw data for a patient from PostgreSQL.
2. **Summarize** — `POST /api/summary` runs the Summary Agent: query DB → fill Vietnamese template.
3. **Refine** — `POST /api/refine` re-runs the template fill with an additional user instruction.
4. **Chat** — `POST /api/chat` streams answers via SSE. The ReAct agent generates SQL on the fly to answer questions about the patient record.
5. **Export** — `GET /api/export-docx` downloads the summary as a DOCX file; `POST /api/preview-html` renders an HTML preview.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Google Generative AI API key |
| `PG_URI` | Yes | — | PostgreSQL connection URI |
| `GEMINI_MODEL` | No | `gemini-3.1-flash-lite` | Gemini model for both agents |
| `VM_EXTERNAL_IP` | No | — | External IP added to CORS allowlist |

## Evaluation (Depreciated)

```bash
cd backend
python -m evaluation.run_eval [--patient-ids BN0003 BN0064]
# Output: evaluation/eval_report.json
```
