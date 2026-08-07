import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.medrecords.route.patient_route import router as patient_router
from app.modules.patient_chat.route.chat_route import router as chat_router
from app.modules.medrecord_export.route.export_route import router as export_router
from app.modules.medrecord_summary.route.summary_route import router as summary_router

logging.basicConfig(
    level=logging.INFO,
    format="LOG: %(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Tóm tắt bệnh án API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summary_router)
app.include_router(chat_router)
app.include_router(patient_router)
app.include_router(export_router)


@app.get("/")
def root():
    return {"message": "OK"}
