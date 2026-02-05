import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.core.logger import logger


class LanguageSpec(BaseModel):
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)

    image: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    command_template: str = Field(..., min_length=1)

    ace_mode: str = Field(..., min_length=1)


class LanguagesConfig(BaseModel):
    languages: list[LanguageSpec] = Field(default_factory=list)


def load_languages() -> dict[str, LanguageSpec]:
    path = settings.LANGUAGES_CONFIG
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Languages config file not found: {path}. "
            f"Put languages.yaml next to .env or set LANGUAGES_CONFIG."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to read languages config {path}: {e}") from e

    try:
        cfg = LanguagesConfig.model_validate(raw)
    except ValidationError as e:
        raise RuntimeError(f"Invalid languages config schema in {path}: {e}") from e

    langs: dict[str, LanguageSpec] = {}
    for spec in cfg.languages:
        if spec.key in langs:
            raise RuntimeError(f"Duplicate language key in {path}: '{spec.key}'")
        langs[spec.key] = spec

    if not langs:
        logger.warning(f"No languages found in {path}")

    return langs


LANGUAGES: dict[str, LanguageSpec] = load_languages()


def get_language(key: str) -> LanguageSpec | None:
    return LANGUAGES.get((key or "").strip())


def required_images() -> list[str]:
    images: set[str] = {spec.image for spec in LANGUAGES.values()}
    return sorted(images)


def list_languages_public() -> list[dict]:
    """
    Отдает ключ, лейбл и ace_mode для фронта
    """
    return [
        {"key": spec.key, "label": spec.label, "ace_mode": spec.ace_mode}
        for spec in LANGUAGES.values()
    ]
