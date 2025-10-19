from fastapi import APIRouter, HTTPException
from ..crud import get_by_slug

router = APIRouter(prefix="/api")

@router.get("/articles/{slug}")
def get_article(slug: str):
    doc = get_by_slug(slug)
    if not doc: raise HTTPException(404, "Not found")
    return doc
