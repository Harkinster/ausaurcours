from fastapi import APIRouter, Query
from typing import List, Optional
from ..meili import search as meili_search

router = APIRouter(prefix="/api")

@router.get("/search")
def search(q: str, categories: Optional[List[str]] = Query(None)):
    try:
        res = meili_search(q, categories)
        return {"hits": res.get("hits", [])}
    except Exception:
        # fallback simple si Meili down
        return {"hits": []}
