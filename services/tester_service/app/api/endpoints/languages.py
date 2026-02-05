from fastapi import APIRouter

from app.core.languages import list_languages_public

router = APIRouter(prefix="/languages", tags=["languages"])

@router.get("/")
def get_languages():
    return list_languages_public()
