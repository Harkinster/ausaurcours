from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import ensure_schema
from .meili import ensure_index
from .routes import search, articles, admin

app = FastAPI(title="Au SAURcours API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

@app.get("/health")
@app.get("/api/health")
def health():
    return {"ok": True}

@app.on_event("startup")
def startup():
    ensure_schema()
    ensure_index()

app.include_router(search.router)
app.include_router(articles.router)
app.include_router(admin.router)
