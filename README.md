# Tóm Tắt Bệnh Án — Medical Record Summarization System

A Vietnamese healthcare AI system that ingests patient medical records (CSV), stores them in a vector database, and provides RAG-powered summarization and conversational Q&A via a web interface.

## Overview

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS |
| Backend API | FastAPI + Uvicorn (async) |
| LLM Orchestration | LangGraph (stateful graphs) |
| Vector Database | ChromaDB (persistent, cosine similarity) |
| Embeddings | Vietnamese bi-encoder (`bkai-foundation-models/vietnamese-bi-encoder`) |
| LLM Provider | Google Generative AI (Gemini 2.5-flash-lite) |
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
│  /ingest  /patient  /summary     │
│  /chat (SSE streaming)           │
│                                  │
│  LangGraph Graphs                │
│  ┌─────────────┐ ┌─────────────┐│
│  │ Summary     │ │ Chat        ││
│  │ retrieve →  │ │ embed →     ││
│  │ timeline →  │ │ retrieve →  ││
│  │ draft       │ │ answer      ││
│  └─────────────┘ └─────────────┘│
│                                  │
│  ChromaDB  ←  Vietnamese Embeds  │
└──────────────────────────────────┘
```

## Repository Structure

```
tom_tat_benh_an/
├── backend/              # FastAPI server, LangGraph graphs, ChromaDB
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/      # chat, summary, ingest, patient
│   │   ├── services/     # llm, chroma, ingest
│   │   └── graphs/       # summary_graph, chat_graph
│   ├── evaluation/       # Evaluation suite (LLM-judged metrics)
│   ├── data/             # CSV files + ChromaDB persistent store
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # React + TypeScript SPA
│   ├── src/
│   │   ├── pages/        # HomePage, PatientPage
│   │   └── components/   # PatientData, Summary, Chat panels
│   ├── vite.config.ts
│   └── package.json
├── nginx/                # Nginx reverse-proxy config (placeholder)
└── docker-compose.yml
```

## Prerequisites

- Docker + Docker Compose, **or** Python 3.11+ and Node 20+
- A Google Cloud API key with Generative AI access ([get one here](https://aistudio.google.com/app/apikey))
- Patient data CSV file

## Quick Start (Docker Compose)

```bash
# 1. Clone the repo
git clone <repo-url>
cd tom_tat_benh_an

# 2. Set your API key
echo "GOOGLE_API_KEY=your_key_here" > backend/.env

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
cp .env.example .env          # add GOOGLE_API_KEY
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

## Workflow

1. **Ingest** — `POST /api/ingest` reads the CSV, embeds each patient record with the Vietnamese bi-encoder, and upserts into ChromaDB (hash-gated to skip unchanged records).
2. **View** — `GET /api/patient/{id}` returns raw CSV data for a patient.
3. **Summarize** — `POST /api/summary` runs the LangGraph summary graph: retrieve chunks → extract timeline → draft full Vietnamese summary.
4. **Chat** — `POST /api/chat` streams answers via SSE. The chat graph maintains per-patient conversation history using LangGraph's MemorySaver.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Google Generative AI API key |
| `GEMINI_API_KEY` | Alt. | — | Alias for `GOOGLE_API_KEY` |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | LLM model for summarization/chat |
| `CHROMA_PATH` | No | `./data/chromadb` | ChromaDB persistent storage path |

## Sub-project READMEs

- [backend/README.md](backend/README.md) — FastAPI server setup, API reference, graph architecture
- [backend/evaluation/README.md](backend/evaluation/README.md) — Evaluation suite, metrics, configuration
- [frontend/README.md](frontend/README.md) — React app setup, component guide, styling
