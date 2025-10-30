from fastapi import FastAPI

app = FastAPI(
    title="Au SAURcours API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

from app import auth, users, articles
from app import search_api
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(articles.router)
app.include_router(search_api.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
