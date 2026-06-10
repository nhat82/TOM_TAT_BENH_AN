# Change Logs 
## Jun 4, 2026
New Design: ReAct agent doing RAG over PostgreSQL + ChromaDB.
User query → agent reason on what to do (tools: create query, do semantic search in database)
→ combine and reason whether has enough information. if yes, return response, if not, loop

Expected areas of failure
- infinite loops, over retrieval => hard cap at some number of tool calls per query. after cap, force synthesis with whatever is available. add a loop detection check if the same tool is called twice with the same params, break. 
- token budget overflow with patients with long history. => cap retrieval at N records or date bounded
- semantic search returning irrelevant results => switch to bkai vietnamese and test gemini-embedding001 
- slow latency when multi hop: stream partial results to the frontend as each hop completes, Parallelize independent hops where possible.

Schema of the sample postgresql data: 
```
sample_medical_records=# \d medical_records
                            Table "public.medical_records"
        Column         |            Type             | Collation | Nullable | Default 
-----------------------+-----------------------------+-----------+----------+---------
 ma_bn_an              | character varying(50)       |           | not null | 
 birthdayyear          | integer                     |           |          | 
 dm_tinhcode           | integer                     |           |          | 
 dm_hinhthucvaovienid  | integer                     |           |          | 
 medicalrecorddate_in  | timestamp without time zone |           |          | 
 medicalrecorddate_out | timestamp without time zone |           |          | 
 so_ngay_dieu_tri      | numeric(5,1)                |           |          | 
 departmentid          | integer                     |           |          | 
 roomid                | integer                     |           |          | 
 bedid                 | integer                     |           |          | 
 lydodenkham           | text                        |           |          | 
 medicalrecorddate_kb  | timestamp without time zone |           |          | 
 chandoantuyenduoi     | text                        |           |          | 
 chandoan_in           | text                        |           |          | 
 chandoan_kb_main      | text                        |           |          | 
 chandoan_out_main     | text                        |           |          | 
 chandoan_out_ex       | text                        |           |          | 
 lydobnvaonoitru       | text                        |           |          | 
 huongdieutri_out      | text                        |           |          | 
 chieucao              | numeric(5,1)                |           |          | 
 cannang               | numeric(5,1)                |           |          | 
 nhiptim               | numeric(5,1)                |           |          | 
 nhietdo               | numeric(3,1)                |           |          | 
 huyetap_low           | numeric(5,1)                |           |          | 
 huyetap_high          | numeric(5,1)                |           |          | 
 nhiptho               | numeric(5,1)                |           |          | 
 ds_dich_vu            | text                        |           |          | 
 ds_thuoc              | text                        |           |          | 
 ds_xet_nghiem         | text                        |           |          | 
 ds_cdha               | text                        |           |          | 
```

## Jun 5, 2026 
✅ Connection to local postgresql db
✅ Create a user only has SELECT permissions: lead_agent 
✅ Create query tools (get tables, view table schema, call generated query)
✅ Prompt: Get full query returns. Only get the records from the given patient
✅ Langsmith monitoring

## Jun 6, 2026
Replaced native rag to ReAct Agent for /chat, /patient pulls directly from db. set string output for langchain sql tool to a large number. Removed ingestion step

## Jun 8, 2026 
fixed routing for backend, frontend. added streaming chunks from gemini. 

## Jun 10, 2026
added summary agent: calls database to get information once, create summary based on template (template doesn't call for personal information to prevent PII leak). can refine but cannot call database anymore. 