import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.chat import router as chat_router
from app.routers.patient import router as patient_router
# from app.routers.summary import router as summary_router
import os

logging.basicConfig(
    level=logging.INFO,
    format="LOG: %(asctime)s %(levelname)s %(name)s — %(message)s",
)

vm_ip = os.getenv("VM_EXTERNAL_IP", "localhost")

app = FastAPI(title="Tóm tắt bệnh án API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{vm_ip}:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(summary_router)
app.include_router(chat_router)
app.include_router(patient_router)


@app.get("/")
def root():
    return {"message": "OK"}
