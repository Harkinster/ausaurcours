from sqlalchemy.orm import Session
from sqlalchemy import select
from . import models

def get_category_by_slug(db: Session, slug: str):
    return db.execute(select(models.Category).where(models.Category.slug == slug)).scalar_one_or_none()

def get_user_by_username(db: Session, username: str):
    return db.execute(select(models.User).where(models.User.username == username)).scalar_one_or_none()

def get_tag_by_name(db: Session, name: str):
    return db.execute(select(models.Tag).where(models.Tag.name == name)).scalar_one_or_none()
