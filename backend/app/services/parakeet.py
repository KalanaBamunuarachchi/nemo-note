import json
import os
import subprocess
import time
from pathlib import Path
import sys


def get_engines_dir() -> Path:
    env_dir = os.environ.get("NEMO_ENGINES_DIR")
    if env_dir:
        return Path(env_dir)

    if getattr(sys, "frozen", False):
        raise RuntimeError(
            "NEMO_ENGINES_DIR not set — packaged sidecar must receive "
            "the resource path from Tauri (check lib.rs sidecar setup)."
        )

    # Dev-mode fallback only
    return Path(__file__).resolve().parents[3] / "engines"


ENGINES_DIR = get_engines_dir()

PARAKEET_DIR = ENGINES_DIR / "parakeet"

RUNTIMES_DIR = PARAKEET_DIR / "runtimes"
MODEL = PARAKEET_DIR / "models" / "tdt-0.6b-v3-f16.gguf"


RUNTIMES = {
    "cuda": RUNTIMES_DIR / "cuda" / "parakeet-cli.exe",
    "vulkan": RUNTIMES_DIR / "vulkan" / "parakeet-cli.exe",
    "cpu": RUNTIMES_DIR / "cpu" / "parakeet-cli.exe",
}


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


def transcribe(audio_path: Path, runtime: str = "cuda"):

    parakeet = RUNTIMES.get(runtime)

    if parakeet is None:
         raise ValueError(f"Unknown runtime: {runtime}")

    if not parakeet.exists():
         raise FileNotFoundError(
        f"Parakeet runtime not found at {parakeet}"
    )

    if not MODEL.exists():
          raise FileNotFoundError(f"model not found at {MODEL}")

    if not parakeet.exists():
        raise FileNotFoundError(f"parakeet-cli.exe not found at {parakeet}")
    if not MODEL.exists():
        raise FileNotFoundError(f"model not found at {MODEL}")

    command = [
        str(parakeet),
        "transcribe",
        "--model",
        str(MODEL),
        "--input",
        str(audio_path.resolve()),
        "--timestamps",
        "--json",
    ]

    start_time = time.perf_counter()

    print("ENGINES_DIR:", ENGINES_DIR)
    print("RUNTIME:", runtime)
    print("PARAKEET:", parakeet)
    print("PARAKEET EXISTS:", parakeet.exists())
    print("MODEL:", MODEL)
    print("MODEL EXISTS:", MODEL.exists())
    print("AUDIO:", audio_path.resolve())
    print("AUDIO EXISTS:", audio_path.resolve().exists())

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=parakeet.parent,
    )

    elapsed_time = time.perf_counter() - start_time
    print(f"Parakeet processing time: {elapsed_time:.2f} seconds")

    if result.returncode != 0:
        raise RuntimeError(f"Parakeet failed:\n{result.stderr}")

    data = json.loads(result.stdout)

    return {
        "text": data["text"],
        "segments": create_segments(data["words"]),
    }