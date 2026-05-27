# Evaluation Suite

LLM-judged evaluation of the RAG system's summarization and Q&A quality. Uses Google Gemini as the judge — no external evaluation frameworks required.

## Overview

The suite runs a set of Vietnamese test queries against the live chat endpoint, then asks a Gemini judge model to score each answer on faithfulness and answer relevancy. Results are saved to `eval_report.json`.

## Setup

The evaluation shares the same dependencies as the main backend:

```bash
cd backend                        # run from backend/, not evaluation/
pip install -r requirements.txt
export GOOGLE_API_KEY=your_key
```

The backend server does **not** need to be running separately — the evaluation invokes the LangGraph chat graph directly.

## Running

**Evaluate all patients in `sample_queries.py`:**
```bash
cd backend
python -m evaluation.run_eval
```

**Evaluate specific patients:**
```bash
python -m evaluation.run_eval --patient-ids BN0003 BN0064 BN0052
```

Output is written to `evaluation/eval_report.json` and a summary is printed to stdout.

## Output Format

`eval_report.json`:
```json
{
  "summary": {
    "total_queries": 20,
    "ok": 18,
    "error": 2,
    "faithfulness":     { "mean": 0.85, "std": 0.12 },
    "answer_relevancy": { "mean": 0.82, "std": 0.15 }
  },
  "queries": [
    {
      "patient_id":       "BN0052",
      "query":            "Chẩn đoán chính của bệnh nhân là gì?",
      "answer":           "Bệnh nhân được chẩn đoán ...",
      "status":           "ok",
      "faithfulness":     0.9,
      "answer_relevancy": 0.88,
      "wait_seconds":     4.2
    }
  ]
}
```

## Metrics

| Metric | Description |
|--------|-------------|
| **Faithfulness** | Does the answer stay grounded in the retrieved context? Scored 0–1 by the judge. |
| **Answer Relevancy** | Is the answer relevant and responsive to the question? Scored 0–1 by the judge. |

The judge model is prompted with the original question, the retrieved context, and the generated answer, then asked to return a JSON score object.

## Configuration

Tuneable constants at the top of `run_eval.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `_JUDGE_WORKERS` | `2` | Parallel judge threads. Keep low to stay within Google Free Tier (15 RPM). |
| `_COLLECT_SEM` | `2` | Max concurrent chat invocations. |
| `_COLLECT_RETRIES` | `3` | Retries per query on non-rate-limit errors. |
| `_MAX_RATE_LIMIT_WAIT` | `900` | Seconds to wait before giving up on a rate-limited request. |

Environment variables (set in `backend/.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_JUDGE_MODEL` | `gemini-2.0-flash-lite` | Gemini model used as the judge. |
| `JUDGE_MAX_WAIT` | `900` | Overrides `_MAX_RATE_LIMIT_WAIT` at runtime. |

## Files

| File | Purpose |
|------|---------|
| `run_eval.py` | Main runner — collects answers, calls judge, aggregates stats |
| `sample_queries.py` | Vietnamese test queries and expected ground-truth answers |
| `acronym_detector.py` | Validates that medical acronyms in answers are recognized |
| `eval_report.json` | Most recent evaluation results (committed for reference) |

## Troubleshooting

**Evaluation takes a long time**
Expected — at 2 judge workers and 15 RPM, 20 queries takes ~10–15 minutes. Do not increase `_JUDGE_WORKERS` beyond 4 on the free tier.

**Rate limit errors (429)**
The runner backs off and retries automatically up to `_MAX_RATE_LIMIT_WAIT` seconds. If you hit the daily quota (1000 RPD), wait until midnight Pacific time.

**`Patient not found in ChromaDB`**
Run `POST /api/ingest` (or `python -m app.services.ingest ingest`) before running the evaluation.

**Judge returns malformed JSON**
The judge prompt asks for a strict JSON object. If the model returns prose, the score for that query is recorded as `null`. This is logged as a warning, not an error — the query still appears in results with `status: "judge_parse_error"`.
