from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File

router = APIRouter()

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    file_path = AUDIO_DIR / file.filename

    async with aiofiles.open(file_path, "wb") as audio_file:
        await audio_file.write(await file.read())

    return {
        "filename": file.filename,
        "saved_to": str(file_path),
        "message": "Audio saved successfully"
    }