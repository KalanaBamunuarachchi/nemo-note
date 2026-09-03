from fastapi import FastAPI

from app.routes.transcription import router as transcription_router


app = FastAPI(title="nemonote API")

app.include_router(transcription_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}