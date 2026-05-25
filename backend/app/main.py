from fastapi import FastAPI
from app.routers.chat import router as chat_router
from app.routers.ingest import router as ingest_router
from app.routers.patient import router as patient_router
from app.routers.summary import router as summary_router

app = FastAPI(title="Tóm tắt bệnh án API")

app.include_router(ingest_router)
app.include_router(summary_router)
app.include_router(chat_router)
app.include_router(patient_router)


@app.get("/")
def root():
    return {"message": "OK"}
