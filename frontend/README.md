# Frontend — React Medical Record UI

React + TypeScript + Vite single-page application for browsing patient records, generating AI summaries, and chatting with a RAG assistant about individual patients.

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| React | 19.2.6 | UI framework |
| TypeScript | 6.0.2 | Type safety |
| Vite | 8.0.12 | Build tool + HMR dev server |
| React Router DOM | 7.15.1 | Client-side routing |
| Tailwind CSS | 3.4.19 | Utility-first styling |

## Setup

```bash
cd frontend
npm install
```

No environment variables are required. API calls are proxied through Vite's dev server to `http://localhost:8000` (see [vite.config.ts](vite.config.ts)).

## Running

**Development (hot module replacement):**
```bash
npm run dev
# App: http://localhost:5173
```

**Production build:**
```bash
npm run build       # TypeScript compile + Vite bundle → dist/
npm run preview     # Serve dist/ locally to verify
```

**Lint:**
```bash
npm run lint
```

**Docker (via docker-compose):**
```bash
docker-compose up frontend
# Runs: npm install && npm run dev -- --host
```

## Project Structure

```
src/
├── main.tsx                     # React root + BrowserRouter
├── App.tsx                      # Route definitions
├── pages/
│   ├── HomePage.tsx             # Patient ID search form
│   └── PatientPage.tsx          # Full patient view (data + summary + chat)
├── components/
│   ├── Header.tsx               # Navigation bar
│   ├── Footer.tsx               # Footer
│   ├── PatientData.tsx          # Raw CSV data table (312 lines)
│   ├── PatientHealthData.tsx    # Vitals & metrics display (203 lines)
│   ├── PatientSummaryPanel.tsx  # Summary generation UI (147 lines)
│   └── ClinicalInsightsPanel.tsx # Streaming chat interface (169 lines)
├── types/
│   └── index.ts                 # Shared TypeScript interfaces
├── App.css
└── index.css
```

## Pages

### `/` — HomePage

Patient search. Enter a patient ID (e.g. `BN0052`) to navigate to their full record.

### `/patient/:patientId` — PatientPage

Full patient view composed of four sections:

| Section | Component | Description |
|---------|-----------|-------------|
| Raw data | `PatientData` | All CSV columns with Vietnamese labels, scrollable table |
| Health metrics | `PatientHealthData` | Vitals, lab results, medications |
| AI summary | `PatientSummaryPanel` | Generate / refine a comprehensive medical summary via RAG |
| Chat | `ClinicalInsightsPanel` | Free-form Q&A with real-time streaming responses |

## Components

### `PatientSummaryPanel`

- Calls `POST /api/summary` with the patient ID.
- Displays the generated summary and a chronological event timeline.
- Supports a "refine" prompt to regenerate with additional instructions.

### `ClinicalInsightsPanel`

- Calls `POST /api/chat` and reads the response as Server-Sent Events (SSE).
- Streams tokens into the chat bubble in real time using `ReadableStream`.
- Maintains chat history in local state and sends it with each request.
- Parses three SSE event types:

```
data: {"type": "token",  "content": "..."}   → append to current bubble
data: {"type": "done",   "sources": [...]}   → finalize bubble, show sources
data: {"type": "error",  "detail": "..."}    → show error message
```

## TypeScript Types (`src/types/index.ts`)

```typescript
interface Vitals       { bloodPressure: string; heartRate: string; temp: string }
interface LabResult    { id: string; testName: string; value: string; date: string; isAbnormal?: boolean }
interface Medication   { id: string; name: string; frequency: string }
interface ChatMessage  { id: string; sender: 'doctor' | 'assistant'; senderName: string; content: string }
```

## API Integration

All requests go to `/api/*` which Vite proxies to `http://localhost:8000` in development. In Docker, Nginx handles the proxy.

| Method | Endpoint | Used by |
|--------|----------|---------|
| `GET` | `/api/patient/{id}` | PatientPage (on mount) |
| `POST` | `/api/summary` | PatientSummaryPanel |
| `POST` | `/api/chat` | ClinicalInsightsPanel (SSE) |

## Styling

Styling uses Tailwind CSS with Material Design 3 design tokens defined in [tailwind.config.js](tailwind.config.js):

**Custom colors:**
- `primary`: `#2563eb` (blue)
- `error`: `#ef4444` (red)
- `surface`, `on-surface`, `outline`, etc.

**Custom spacing:**
- `md` (16px), `lg` (24px), `xl` (48px), `2xl` (64px)

**Custom typography utilities:**
- `display-lg`, `headline-md`, `body-md`, `label-caps`

## Troubleshooting

**"Cannot GET /api/..."**
Ensure the backend is running on port 8000 before starting the dev server.

**Streaming chat stops mid-response**
Check the browser console for `ReadableStream` errors. The parser expects each SSE line to start with `data: `. Verify the backend is returning `Content-Type: text/event-stream`.

**Build fails with TypeScript errors**
```bash
npm run lint            # check ESLint
npx tsc --noEmit       # check types without building
rm -rf dist && npm run build
```

**Blank page after navigation**
React Router uses `BrowserRouter`. If deployed behind Nginx, ensure all routes fall back to `index.html`.
