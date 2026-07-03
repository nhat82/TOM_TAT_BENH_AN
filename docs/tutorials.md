# Tutorial: Getting Started

---

## What You'll Need

- **Docker** installed on your machine ([download here](https://www.docker.com/products/docker-desktop/)). For local development, you can skip this. 
- A **Google Gemini API key** (get one at [aistudio.google.com](https://aistudio.google.com))
- A **PostgreSQL database** with a `medical_records` table already loaded
    + Create a blank database: `createdb -U local_username local_database_name`
    + Restore the dump file: `pg_restore -U local_username -d local_database_name -v /path/to/your/local/project/folder/my_database.dump`
        * Make sure you're using a database user with only read/select permissions, don't use postgres user directly

---

## Step 1: Get the Code

```bash
git clone <repository-url>
cd tom_tat_benh_an
```

---

## Step 2: Set Up Environment Variables

Create a file at `backend/.env` based on `backend/.env.example`


---

## Step 3: Start the App

```
cd backend
fastapi dev
```
In another terminal 
```
cd frontend
npm run dev
```

Wait about 30–60 seconds for both services to start. You'll see log lines from both `backend` and `frontend`.

Once ready, open your browser at **http://localhost:5173**.

---

## Step 4: Find a Patient

You'll see a search page listing all patients in the database.

- Type a patient code (e.g. `BN0052`) or a name in the search box
- Click a patient row to open their record

---

## Step 5: Generate a Summary

On the patient page, you'll see a panel called **"Tóm tắt bệnh án"** (Patient Summary).

1. Click the **"Tạo tóm tắt"** (Generate) button
2. Wait 10–30 seconds — the AI reads the patient's full record and writes a structured summary
3. The summary appears as labeled sections: diagnosis, reason for visit, clinical findings, treatment, etc.

---

## Step 6: Ask a Question

In the **"Thông tin lâm sàng"** (Clinical Insights) panel on the right:

1. Type a question in Vietnamese, e.g. *"Bệnh nhân có tiền sử bệnh gì?"* (What is the patient's medical history?)
2. Press **Send**
3. The answer streams back in real time, based on the actual database record

---

## Step 7: Refine or Export

If the summary needs adjustment:

- Click **"Tinh chỉnh"** (Refine) and type an instruction, e.g. *"Thêm thông tin về thuốc đã dùng"* (Add information about medications used)
- Click **"Xuất DOCX"** (Export DOCX) to download a Word document

---

## What Just Happened?

- The backend pulled the patient's raw record from PostgreSQL
- A Gemini-powered AI agent read that record and filled in a structured Vietnamese medical template
- The chat panel used a second AI agent that can write and run SQL queries to answer your specific questions

You're now ready to use the system. For more specific tasks, see the [How-to Guides](how-to-guides.md).
