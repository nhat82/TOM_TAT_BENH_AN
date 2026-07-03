# Explanation: How the System Works

This document explains the thinking behind the design — why certain choices were made, and how the different parts fit together.

---

## Core Problems Before Moving On With This Project 
This project is designed and build on being able to use cloud services (Compute Engine, Gemini API). But per latest meeting with the hospital, they want everything local (MCP server model, choose a good local model, better design for database connections if they allow it). 

---

## Why Two Separate AI Agents?

The system has two distinct AI agents: one for summaries, one for chat. They serve different purposes.

**The summary agent** is given one job: read the patient's record and fill in 12 specific fields. It uses a fixed, detailed Vietnamese prompt with rules for edge cases like infertility records or miscarriage care. The output is always the same structure, which makes it suitable for regulatory documentation.

**The chat agent** is more flexible. It answers freeform questions by writing and running SQL queries against the database on the fly. A doctor might ask about medications, lab trends, or specific dates — questions that don't fit any pre-defined template. The chat agent figures out the right SQL to answer the question, runs it, and summarizes the result.

Keeping them separate means each agent can have a prompt and behavior optimized for its specific task.

---

## Why SQL Instead of Embeddings?

An alternative design would store the medical records as text embeddings (vector search), and retrieve relevant chunks before generating a response. This is common for document Q&A systems.

This system uses direct SQL queries instead. The reasons:

- Medical records are **highly structured** — each piece of information lives in a named column. SQL is the natural fit.
- The records are already in **PostgreSQL**, so no second storage system is needed.
- SQL results are **exact**, not approximate. A doctor asking "what was the patient's discharge date?" should get a precise answer, not a nearest-match.
- The data volume per patient is small enough that reading all relevant columns in a single query is fast.

---

## Why Parameterized SQL?

The AI agents generate SQL queries based on the user's question. This creates a risk: a malicious or confused AI could generate a query that reads data it shouldn't, or worse, modifies the database.

The system handles this in two ways:

1. **Parameterized queries.** The AI writes SQL with named placeholders (e.g. `:patient_id`), not literal values. The actual patient ID is injected by the application, not the AI. This is the same protection used against SQL injection in all web applications.

2. **Patient scoping.** The `patient_id` is always injected from the application state — the AI can't access a different patient's record just by writing a different WHERE clause.


---

## How Chat Memory Works

Each patient has a separate conversation history. When a doctor asks a follow-up question, the AI has access to everything said earlier in that session — but nothing from a different patient's session.

This is implemented using LangGraph's `MemorySaver`, keyed by `thread_id = patient_id`. Every new conversation about a patient resumes from where it left off (within the same server session). If the server restarts, conversation history is cleared.

---

## How Streaming Works

The chat panel shows the AI's answer appearing word by word. This is handled using **Server-Sent Events (SSE)**.

When the frontend calls `/api/chat`, the backend opens a persistent HTTP connection and sends small JSON chunks as the AI generates them. Each chunk is either:
- A token (`{"type": "token", "content": "..."}`) — a small piece of the answer
- A done signal (`{"type": "done"}`) — the answer is complete
- An error (`{"type": "error", "detail": "..."}`) — something went wrong

The frontend listens on this connection and appends each token to the current message bubble. This feels faster than waiting for the full response and makes long answers easier to read as they arrive.


---

## Frontend Architecture

The patient page is divided into four panels. Each panel is a self-contained React component:

- **PatientData** — raw data table, read-only
- **PatientHealthData** — vitals and lab results, structured view
- **PatientSummaryPanel** — generate, refine, and export the summary
- **ClinicalInsightsPanel** — the streaming chat interface

The two right-side panels (summary and chat) are sticky — they stay visible as the doctor scrolls through the raw data on the left. This layout is intentional: the doctor can reference the raw data on the left while reading the AI summary or asking questions on the right.

---

## Deployment Model

The system runs as two Docker containers:

- **backend** — FastAPI server, exposes port 8000
- **frontend** — Vite dev server, exposes port 5173

In production, Nginx (in the `nginx/` folder) acts as a reverse proxy — it sits in front of both services and routes requests appropriately. The `VM_EXTERNAL_IP` environment variable is used to configure CORS so the frontend and backend can communicate across different origins when deployed to a remote server.
