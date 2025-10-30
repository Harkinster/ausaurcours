from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, JSON, Table
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# --- Table d’association articles <-> tags ---
article_tags_table = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# --- Modèles ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255))
    role = Column(String(20), default="editor")
    created_at = Column(DateTime, server_default=func.current_timestamp())

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(150), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    links_json = Column(JSON)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    category = relationship("Category")
    author = relationship("User")
    tags = relationship("Tag", secondary=article_tags_table, lazy="joined")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.current_timestamp())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))
    entity_type = Column(String(50))
    entity_id = Column(String(50))
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Crée les tables si besoin
from app.database import engine
Base.metadata.create_all(bind=engine)
