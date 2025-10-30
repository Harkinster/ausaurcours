from typing import List, Optional
from pydantic import BaseModel

class CategoryIn(BaseModel):
    name: str
    slug: str

class CategoryOut(CategoryIn):
    id: int
    class Config:
        from_attributes = True

class TagIn(BaseModel):
    name: str

class TagOut(TagIn):
    id: int
    class Config:
        from_attributes = True

class UserIn(BaseModel):
    username: str
    email: str
    role: str = "editor"

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    class Config:
        from_attributes = True

class ArticleIn(BaseModel):
    slug: str
    title: str
    content: Optional[str] = ""
    category_slug: Optional[str] = None
    tags: List[str] = []
    author_username: Optional[str] = None
    links: Optional[List[str]] = []

class ArticlePatch(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    category_slug: Optional[str] = None
    tags: Optional[List[str]] = None
    author_username: Optional[str] = None
    links: Optional[List[str]] = None

class ArticleOut(BaseModel):
    id: int
    slug: str
    title: str
    content: Optional[str]
    category: Optional[str]
    tags: List[str]
    author: Optional[str]
    created_at: str
    updated_at: str
    class Config:
        from_attributes = True
