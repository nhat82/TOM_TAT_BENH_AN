# Reference

Complete descriptions of every API endpoint, configuration option, and data field in the system.

---

## API Endpoints

All endpoints are served at `http://localhost:8000` (or your server's address).

---

### `GET /`

Health check.

**Response:**
```json
{ "message": "OK" }
```

---

### `GET /api/patients`

Returns a list of all patients in the database.

**Response:**
```json
{
  "patients": [
    { "ma_bn_an": "BN0052", "ho_ten": "Nguyen Van A", ... },
    ...
  ]
}
```

---

### `GET /api/patient/{id}`

Returns the full medical record for one patient.

**URL parameter:** `id` — patient code, e.g. `BN0052`

**Response:**
```json
{
  "patient_id": "BN0052",
  "data": {
    "ho_ten": "Nguyen Van A",
    "birthdayyear": "1975",
    "chandoan_in": "...",
    ...
  }
}
```

---

### `POST /api/summary`

Generates an AI summary for a patient.

**Request body:**
```json
{ "ma_bn_an": "BN0052" }
```

**Response:**
```json
{
  "patient_id": "BN0052",
  "summary": {
    "chandoan_in_icd10": "J18.9",
    "chandoan_out_main_icd10": "J18.1",
    "chandoan_in": "Viêm phổi",
    "chandoan_out_main": "Viêm phổi thùy",
    "lydodenkham": "Sốt, ho khan 3 ngày",
    "tom_tat_qua_trinh_dien_bien": "...",
    "tien_su_benh": "...",
    "dau_hieu_chinh": "...",
    "tom_tat_ket_qua": "...",
    "pttt": "...",
    "tinh_trang_ra_vien": "Đỡ",
    "huongdieutri_out": "..."
  }
}
```

---

### `POST /api/refine`

Refines an existing summary based on an instruction.

**Request body:**
```json
{
  "ma_bn_an": "BN0052",
  "summary": { ... },
  "prompt": "Thêm thông tin về thuốc đã dùng"
}
```

**Response:** Same format as `/api/summary`.

---

### `POST /api/preview-html`

Returns an HTML document of the summary for browser preview.

**Request body:** Same as `/api/refine` (without `prompt`)

**Response:** HTML text (`text/html`)

---

### `POST /api/export-docx`

Downloads the summary as a `.docx` file.

**Request body:** Same as `/api/preview-html`

**Response:** Binary file download (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`)

---

### `POST /api/chat`

Streams an answer to a question about a patient. Uses Server-Sent Events (SSE).

**Request body:**
```json
{
  "patient_id": "BN0052",
  "query": "Bệnh nhân có tiền sử bệnh gì?",
  "chat_history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response:** `text/event-stream` — one JSON object per line:

| Event type | Meaning |
|------------|---------|
| `{"type": "token", "content": "..."}` | A chunk of the answer text |
| `{"type": "done"}` | The answer is complete |
| `{"type": "error", "detail": "..."}` | Something went wrong |

---

## Summary Fields

These are the fields the AI fills in when generating a summary.

| Field | Description |
|-------|-------------|
| `chandoan_in_icd10` | ICD-10 code for admission diagnosis |
| `chandoan_out_main_icd10` | ICD-10 code for discharge diagnosis |
| `chandoan_in` | Admission diagnosis (full text) |
| `chandoan_out_main` | Main discharge diagnosis (full text) |
| `lydodenkham` | Reason for admission |
| `tom_tat_qua_trinh_dien_bien` | Disease course narrative |
| `tien_su_benh` | Past medical history |
| `dau_hieu_chinh` | Key clinical signs and findings |
| `tom_tat_ket_qua` | Summary of lab and imaging results |
| `pttt` | Surgical or procedural interventions |
| `tinh_trang_ra_vien` | Discharge status (see values below) |
| `huongdieutri_out` | Follow-up treatment directions |

**Valid discharge status values (`tinh_trang_ra_vien`):**
- `Khỏi` — Recovered
- `Đỡ` — Improved
- `Không thay đổi` — No change
- `Nặng hơn` — Deteriorated
- `Tử vong` — Deceased
- `Xin về` — Discharged by request
- `Chuyển viện` — Transferred

---

## Environment Variables

Set these in `backend/.env`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Generative AI API key |
| `PG_URL` | Yes | — | PostgreSQL connection string |
| `GEMINI_MODEL` | No | `gemini-3.1-flash-lite` | Model name for both agents |
| `VM_EXTERNAL_IP` | No | `localhost` | Server IP for CORS in production |
| `LANGSMITH_API_KEY` | No | — | LangSmith tracing key |
| `LANGSMITH_TRACING` | No | `false` | Set to `true` to enable tracing |
| `LANGSMITH_PROJECT` | No | `medical-app` | LangSmith project name |

---

## Database

**Table:** `medical_records`

**Primary identifier:** `ma_bn_an` (patient code, e.g. `BN0052`)

Key columns used by the system:

| Column | Description |
|--------|-------------|
| `ma_bn_an` | Patient ID |
| `ho_ten` | Patient name |
| `birthdayyear` | Birth year |
| `cccd` | National ID number |
| `gender` | Gender |
| `dm_tinhcode` | Province/address code |
| `departmentid` | Department ID |
| `medicalrecorddate_in` | Admission date |
| `medicalrecorddate_out` | Discharge date |
| `chandoan_in` | Admission diagnosis |
| `chandoan_in_icd10` | Admission diagnosis ICD-10 |
| `chandoan_out_main` | Discharge diagnosis |
| `chandoan_out_main_icd10` | Discharge diagnosis ICD-10 |
| `lydodenkham` | Reason for visit |
| `ds_cdha` | Imaging study results |
| `ds_xet_nghiem` | Lab test results |
| `ds_dich_vu` | Services provided |
| `tinh_trang_ra_vien` | Discharge status |
| `huongdieutri_out` | Follow-up treatment plan |

The table has approximately 49 columns total. The AI agents can query any of them.

---

## Agent SQL Tools

The AI agents have access to three tools for querying the database:

| Tool | Description |
|------|-------------|
| `list_tables()` | Returns the names of all available tables |
| `get_table_schema(table_names)` | Returns column definitions and sample rows |
| `run_sql_query(query, parameters)` | Executes a SQL query with named placeholders |

All queries are **parameterized** — the patient ID is always passed as a variable, not embedded in the SQL string. This prevents SQL injection.

---

## Frontend Routes

| URL | Page | Description |
|-----|------|-------------|
| `/` | Home | Patient search and list |
| `/patient/:patientId` | Patient | Full record, summary, and chat |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Uvicorn |
| AI Agents | LangGraph, LangChain, Google Gemini |
| Database | PostgreSQL, SQLAlchemy |
| Export | python-docx |
| Deployment | Docker Compose |
