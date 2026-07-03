# How-to Guides

Practical steps for common tasks. Each section solves one specific problem.

---

## Run Without Docker (Local Development)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create backend/.env with GEMINI_API_KEY and PG_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (in a separate terminal):**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The frontend automatically proxies `/api` requests to the backend at port 8000.

---

## Change the AI Model

Open `backend/app/config.py` and change the model in chatbot_agent_model or summary_agent_model

Valid model names are any Gemini model available on your API key. The default is `gemini-3.1-flash-lite`.

To change temperature or set a fallback model, edit `backend/app/config.py` — look for the `ModelConfig` class.

---

## Update the Summary Prompt

The summary agent uses a detailed Vietnamese prompt that tells the AI what fields to extract and how.

File: `backend/app/services/agent_package/prompts.py` → `summary_system_prompt`

Edit the string directly. The prompt includes domain-specific rules for:
- Infertility treatment records
- Miscarriage and obstetric care
- Discharge status coding
- And more

After editing, restart the backend for changes to take effect.

---

## Update the Chat Prompt

The chat agent's behavior is controlled by `chatbot_system_prompt` in the same file:

`backend/app/services/agent_package/prompts.py`

This controls how the AI interprets questions and what context it uses from the database.

---

## Add a New API Endpoint

1. Create or open a router file in `backend/app/routers/`
2. Define your endpoint function:

```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/api/my-endpoint")
async def my_endpoint():
    return {"result": "..."}
```

3. Register it in `backend/app/main.py`:

```python
from app.routers import my_router
app.include_router(my_router.router)
```

---

## Deploy to a Remote Server

1. SSH into your server
2. Clone the repository on the main branch
    - There are 3 git branches: dev, stage, main
3. `npm run build` to serve newest frontend code 
4. `sudo systemctl restart tomtat` to restart the backend systemd service after code change
5. `journalctl -u tomtat -n 50 --no-pager ` to check the full error log after service restart

Firewall rules: frontend 5173 port is open externally but backend 8000 port is open internally 

---

## Enable LangSmith Tracing

LangSmith lets you inspect every AI call — what was sent, what came back, how long it took.

Add to `backend/.env`:

```env
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=medical-app
```

Restart the backend. Traces will appear in your LangSmith dashboard.

---

## Export a Summary to DOCX

From the patient summary panel:

1. Generate or load a summary
2. Click **"Xuất DOCX"**
3. A `.docx` file downloads to your browser's default download folder

The DOCX is generated server-side using python-docx. To modify the document layout or add fields, edit `backend/app/services/docx_export.py`.

---

## Preview the Summary as HTML

Click **"Xem trước"** (Preview) in the summary panel. A modal opens with a styled HTML version of the summary — useful for checking formatting before exporting.

The HTML template lives in `backend/app/services/html_preview.py`.
