from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Article, Category, Tag
from app.auth import get_current_user
from app.models import AuditLog, User
from app.search import upsert_document, ensure_collection
from app.audit import log_action
from typing import List, Optional

router = APIRouter(prefix="/api/articles", tags=["articles"])

try:
    ensure_collection()
except:
    pass  # Typesense désactivé

class ArticleIn(BaseModel):
    slug: str
    title: str
    content: Optional[str] = ""
    category_slug: Optional[str] = None
    tags: List[str] = []
    links: Optional[List[str]] = []

@router.get("/")
def list_articles(db: Session = Depends(get_db)):
    articles = db.query(Article).all()
    return [{
        "id": a.id,
        "slug": a.slug,
        "title": a.title,
        "content": a.content or "",
        "category": a.category.name if a.category else "",
        "category_slug": a.category.slug if a.category else "",
        "tags": [t.name for t in a.tags],
        "author": a.author.username if a.author else "Inconnu",
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat()
    } for a in articles]

@router.get("/recent")
def recent_articles(db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.updated_at.desc()).limit(20).all()
    return [{
        "id": a.id,
        "slug": a.slug,
        "title": a.title,
        "content": a.content or "",
        "category": a.category.name if a.category else "",
        "tags": [t.name for t in a.tags],
        "author": a.author.username if a.author else "Inconnu",
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat()
    } for a in articles]

@router.get("/slug/{slug}")
def get_by_slug(slug: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(404, "Article non trouvé")
    return {
        "id": article.id,
        "slug": article.slug,
        "title": article.title,
        "content": article.content or "",
        "category": article.category.name if article.category else "",
        "category_slug": article.category.slug if article.category else "",
        "tags": [t.name for t in article.tags],
        "author": article.author.username if article.author else "Inconnu",
        "created_at": article.created_at.isoformat(),
        "updated_at": article.updated_at.isoformat()
    }

@router.get("/slug/{slug}/history")
def history_by_slug(slug: str, db: Session = Depends(get_db)):
    # récupère l'historique d'audit pour cet article (par slug)
    logs = (
        db.query(AuditLog, User)
        .outerjoin(User, User.id == AuditLog.user_id)
        .filter(AuditLog.entity_type == "article", AuditLog.entity_id == slug)
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "action": a.action,
            "user": (u.username if u else None),
            "created_at": (a.created_at.isoformat() if a.created_at else None),
            "meta": a.meta or {},
        }
        for (a, u) in logs
    ]

@router.post("/")
def create_article(data: ArticleIn, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if db.query(Article).filter(Article.slug == data.slug).first():
        raise HTTPException(409, "Slug déjà utilisé")

    category = None
    if data.category_slug:
        category = db.query(Category).filter(Category.slug == data.category_slug).first()
        if not category:
            # créer automatiquement la catégorie si absente
            category = Category(name=data.category_slug.replace('-', ' ').title(), slug=data.category_slug)
            db.add(category)
            db.flush()

    tags = []
    for name in data.tags:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)

    article = Article(
        slug=data.slug,
        title=data.title,
        content=data.content,
        category=category,
        author=user,
        links_json=data.links
    )
    article.tags = tags
    db.add(article); db.commit(); db.refresh(article)

    upsert_document({
        "id": str(article.id),
        "slug": article.slug,
        "title": article.title,
        "content": article.content or "",
        "category": article.category.name if article.category else "",
        "tags": [t.name for t in article.tags],
        "created_at": int(article.created_at.timestamp()),
        "updated_at": int(article.updated_at.timestamp())
    })

    log_action(db, user_id=user.id, action="create", entity_type="article", entity_id=article.slug)
    return {"id": article.id}

@router.put("/{article_id}")
def update_article(article_id: int, data: ArticleIn, db: Session = Depends(get_db), user = Depends(get_current_user)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "Article non trouvé")

    if data.slug != article.slug and db.query(Article).filter(Article.slug == data.slug).first():
        raise HTTPException(409, "Slug déjà utilisé")

    category = None
    if data.category_slug:
        category = db.query(Category).filter(Category.slug == data.category_slug).first()
        if not category:
            # créer automatiquement la catégorie si absente
            category = Category(name=data.category_slug.replace('-', ' ').title(), slug=data.category_slug)
            db.add(category)
            db.flush()

    tags = []
    for name in data.tags:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)

    article.slug = data.slug
    article.title = data.title
    article.content = data.content
    article.category = category
    article.links_json = data.links
    article.tags = tags

    db.commit()

    upsert_document({
        "id": str(article.id),
        "slug": article.slug,
        "title": article.title,
        "content": article.content or "",
        "category": article.category.name if article.category else "",
        "tags": [t.name for t in article.tags],
        "created_at": int(article.created_at.timestamp()),
        "updated_at": int(article.updated_at.timestamp())
    })

    log_action(db, user_id=user.id, action="update", entity_type="article", entity_id=article.slug)
    return article

@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Supprime un article et son historique d'audit."""
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "Article non trouvé")
    
    # Journaliser l'action avant de supprimer
    log_action(db, user_id=user.id, action="delete", entity_type="article", entity_id=article.slug)
    
    # Supprimer d'abord les entrées liées dans audit_logs
    db.query(AuditLog).filter(
        AuditLog.entity_type == "article", 
        AuditLog.entity_id == article.slug
    ).delete()
    
    # Puis supprimer l'article
    db.delete(article)
    db.commit()
    
    return {"status": "success", "message": "Article supprimé"}
