from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Comment
from app.auth import get_current_user
from app.audit import log_action

router = APIRouter(prefix="/api/articles", tags=["comments"])

class CommentIn(BaseModel):
    content: str

@router.post("/{article_id}/comments")
def add_comment(article_id: int, data: CommentIn, db: Session = Depends(get_db), user = Depends(get_current_user)):
    comment = Comment(article_id=article_id, author_id=user.id, content=data.content)
    db.add(comment); db.commit()
    log_action(db, user_id=user.id, action="add_comment", entity_type="article", entity_id=str(article_id))
    return {"id": comment.id, "status": "pending"}
