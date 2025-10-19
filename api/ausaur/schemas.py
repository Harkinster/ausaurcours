from typing import List, Optional
from pydantic import BaseModel, Field

class ArticleOut(BaseModel):
    id: Optional[int] = None
    slug: str
    title: str
    content: str
    category: str
    type: str = "process"
    tags: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)

class ArticleIn(BaseModel):
    title: str
    slug: Optional[str] = None
    content: str
    category: str = "Processus"
    type: str = "process"
    tags: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)

class ArticleUpdate(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    links: Optional[List[str]] = None
