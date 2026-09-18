import json
import os
from pathlib import Path


def get_settings_file() -> Path:
    app_data = os.environ.get("NEMO_SETTINGS_DIR")

    if not app_data:
        raise RuntimeError(
            "NEMO_SETTINGS_DIR is not set."
        )

    settings_dir = Path(app_data)
    settings_dir.mkdir(parents=True, exist_ok=True)

    return settings_dir / "settings.json"


def load_settings() -> dict:
    settings_file = get_settings_file()

    if not settings_file.exists():
        return {}

    with open(settings_file, "r", encoding="utf-8") as file:
        return json.load(file)


def save_settings(settings: dict):
    settings_file = get_settings_file()

    with open(settings_file, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2)