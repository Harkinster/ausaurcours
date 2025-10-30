from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
import re
from app.database import get_db
from app.models import Article

router = APIRouter(prefix="/api", tags=["search"])

@router.get("/search")
def search(q: str, db: Session = Depends(get_db)):
    q = (q or "").strip()
    if not q:
        return {"hits": []}
    tokens = [t for t in re.split(r"\s+", q) if t]
    # Mode OR: au moins un mot présent dans title ou content
    ors = [or_(Article.title.ilike(f"%{t}%"), Article.content.ilike(f"%{t}%")) for t in tokens]
    query = db.query(Article)
    if ors:
        query = query.filter(or_(*ors))
    # Récupérer un peu plus d'articles puis scorer côté Python
    cand = query.order_by(Article.updated_at.desc()).limit(100).all()
    def score_article(a):
        title = (a.title or "").lower()
        content = (a.content or "").lower()
        s = 0
        for t in tokens:
            tl = t.lower()
            if tl in title: s += 2
            if tl in content: s += 1
        return s
    ranked = sorted(cand, key=lambda a: (score_article(a), a.updated_at or 0), reverse=True)[:20]
    return {
        "hits": [
            {
                "id": a.id,
                "slug": a.slug,
                "title": a.title,
                "snippet": (a.content or "")[:240],
                "category": a.category.name if a.category else "",
                "tags": [t.name for t in a.tags],
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in ranked
        ]
    }
