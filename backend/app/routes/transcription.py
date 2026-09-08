from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File

from app.services.parakeet import transcribe


router = APIRouter()

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    file_path = AUDIO_DIR / file.filename

    async with aiofiles.open(file_path, "wb") as audio_file:
        await audio_file.write(await file.read())

    result = transcribe(file_path)

    return {
        "filename": file.filename,
        "transcription": result,
    }