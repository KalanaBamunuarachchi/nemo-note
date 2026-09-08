import json
import subprocess
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

PARAKEET = (
    BASE_DIR
    / "engines"
    / "parakeet"
    / "parakeet-v0.5.0-bin-win-cuda-x64"
    / "parakeet-cli.exe"
)

MODEL = (
    BASE_DIR
    / "engines"
    / "parakeet"
    / "parakeet-v0.5.0-bin-win-cuda-x64"
    / ".cache"
    / "parakeet.cpp"
    / "models"
    / "tdt-0.6b-v3-f16.gguf"
)


def create_segments(words):
    segments = []
    current_words = []

    for word in words:
        current_words.append(word)

        if word["w"].endswith((".", "?", "!")):
            segments.append({
                "start": current_words[0]["start"],
                "end": current_words[-1]["end"],
                "text": " ".join(w["w"] for w in current_words)
            })

            current_words = []

    if current_words:
        segments.append({
            "start": current_words[0]["start"],
            "end": current_words[-1]["end"],
            "text": " ".join(w["w"] for w in current_words)
        })

    return segments


def transcribe(audio_path: Path):
    command = [
        str(PARAKEET),
        "transcribe",
        "--model",
        str(MODEL),
        "--input",
        str(audio_path),
        "--timestamps",
        "--json",
    ]

    start_time = time.perf_counter()

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    elapsed_time = time.perf_counter() - start_time

    print(f"Parakeet processing time: {elapsed_time:.2f} seconds")

    if result.returncode != 0:
        raise RuntimeError(
            f"Parakeet failed:\n{result.stderr}"
        )

    data = json.loads(result.stdout)

    return {
        "text": data["text"],
        "segments": create_segments(data["words"]),
    }