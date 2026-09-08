import subprocess
import json

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

    # Handle any words left over
    if current_words:
        segments.append({
            "start": current_words[0]["start"],
            "end": current_words[-1]["end"],
            "text": " ".join(w["w"] for w in current_words)
        })

    return segments

parakeet = r"..\engines\parakeet\parakeet-v0.5.0-bin-win-cuda-x64\parakeet-cli.exe"

model = r"..\engines\parakeet\parakeet-v0.5.0-bin-win-cuda-x64\.cache\parakeet.cpp\models\tdt-0.6b-v3-f16.gguf"

audio = r"audio\harvard.wav"

command = [
    parakeet,
    "transcribe",
    "--model",
    model,
    "--input",
    audio,
    "--timestamps",
    "--json",
]

result = subprocess.run(
    command,
    capture_output=True,
    text=True,
)

print("RETURN CODE:")
print(result.returncode)

if result.returncode != 0:
    print("\nPARAKEET ERROR:")
    print(result.stderr)
    raise SystemExit(1)

# Convert JSON text into a Python dictionary
data = json.loads(result.stdout)

print("\nFULL RESULT:")
print(data)

print("\nTRANSCRIPT:")
print(data["text"])

print("\nWORDS:")
for word in data["words"]:
    print(
        word["w"],
        word["start"],
        "→",
        word["end"]
    )

print("\nSEGMENTS:")

segments = create_segments(data["words"])

for segment in segments:
    print(
        f'{segment["start"]:.2f} → '
        f'{segment["end"]:.2f} | '
        f'{segment["text"]}'
    )