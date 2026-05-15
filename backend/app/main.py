from fastapi import FastAPI
from app.routers.summary import router as summary_router

app = FastAPI(title="Tóm tắt bệnh án API")

app.include_router(summary_router)


@app.get("/")
def root():
    return {"message": "OK"}
