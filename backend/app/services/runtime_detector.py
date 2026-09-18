import json
import subprocess
import time
from pathlib import Path
import sys

from app.services.parakeet import MODEL, RUNTIMES


if getattr(sys, "frozen", False):
    TEST_AUDIO = Path(sys._MEIPASS) / "audio" / "harvard.wav"
else:
    TEST_AUDIO = Path(__file__).resolve().parents[2] / "audio" / "harvard.wav"


def test_runtime(runtime: str) -> dict:
    parakeet = RUNTIMES[runtime]

    if not parakeet.exists():
        return {
            "runtime": runtime,
            "available": False,
            "time": None,
            "error": "Runtime executable not found",
        }

    command = [
        str(parakeet),
        "transcribe",
        "--model",
        str(MODEL),
        "--input",
        str(TEST_AUDIO.resolve()),
        "--timestamps",
        "--json",
    ]

    try:
        # First run: initialize the runtime and load the model.
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=parakeet.parent,
        )

        # Second run: measure the actual transcription time.
        start_time = time.perf_counter()

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=parakeet.parent,
        )

        elapsed = time.perf_counter() - start_time

        if result.returncode != 0:
            return {
                "runtime": runtime,
                "available": False,
                "time": None,
                "error": result.stderr.strip(),
            }

        # Make sure the output is actually valid Parakeet JSON.
        json.loads(result.stdout)

        return {
            "runtime": runtime,
            "available": True,
            "time": round(elapsed, 2),
            "error": None,
        }

    except Exception as error:
        return {
            "runtime": runtime,
            "available": False,
            "time": None,
            "error": str(error),
        }

def detect_runtimes() -> list[dict]:
    results = []

    for runtime in ("cuda", "vulkan", "cpu"):
        result = test_runtime(runtime)
        results.append(result)

    return results