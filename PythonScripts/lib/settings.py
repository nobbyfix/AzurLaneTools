import tomllib
import shutil
from pathlib import Path
from dataclasses import dataclass


SETTINGS_FILEPATH = Path("data", "settings.toml")
SETTINGS_FILEPATH_DEFAULT = Path("data", "static", "settings_default.toml")

@dataclass
class APISettings:
    json_source_path: Path
    jsonloader_variant: str


def read_settings(path: Path = SETTINGS_FILEPATH):
    if not path.exists():
        if SETTINGS_FILEPATH_DEFAULT.exists():
            shutil.copyfile(SETTINGS_FILEPATH_DEFAULT, path)
        else:
            raise RuntimeError(f"Default settings backup file at '{SETTINGS_FILEPATH_DEFAULT}' does not exist!")
    
    with open(path, "rb") as f:
        return tomllib.load(f)

def read_and_parse_settings(path: Path | None = None) -> APISettings:
    settings_data = read_settings(path) if path else read_settings()

    return APISettings(
        json_source_path = Path(settings_data["source_json_path"]).resolve(),
        jsonloader_variant = settings_data["jsonloader_variant"]
    )
