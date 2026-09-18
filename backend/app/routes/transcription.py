from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.parakeet import transcribe
from app.services.runtime_detector import detect_runtimes
from app.services.settings import load_settings, save_settings


router = APIRouter()

AUDIO_DIR = Path(__file__).resolve().parents[2] / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

@router.get("/runtimes")
def get_runtimes():
    return {
        "runtimes": detect_runtimes()
    }

@router.get("/settings/runtime")
def get_runtime_setting():
    settings = load_settings()

    return {
        "runtime": settings.get("runtime")
    }

@router.post("/settings/runtime")
def set_runtime_setting(runtime: str = Form(...)):
    if runtime not in ("cuda", "vulkan", "cpu"):
        raise HTTPException(
           status_code=400,
           detail="Invalid runtime. Choose cuda, vulkan, or cpu."
        )

    settings = load_settings()
    settings["runtime"] = runtime
    save_settings(settings)

    return {
        "runtime": runtime
    }

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    runtime: str = Form("cuda"),
):
    file_path = AUDIO_DIR / file.filename

    async with aiofiles.open(file_path, "wb") as audio_file:
        await audio_file.write(await file.read())

    try:
        result = transcribe(file_path, runtime)

        return {
           "filename": file.filename,
           "runtime": runtime,
           "transcription": result,
        }

    except Exception as error:
      return {
        "error": str(error),
        "runtime": runtime,
      }