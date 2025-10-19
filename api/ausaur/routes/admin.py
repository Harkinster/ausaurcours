from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from ..config import ADMIN_TOKEN
from ..crud import list_articles, create_article, update_article, delete_article
from ..meili import upsert as meili_upsert, delete_ids as meili_delete

router = APIRouter(prefix="/api/admin")

def check_token(auth: Optional[str], x_admin_token: Optional[str]):
    tok = ""
    if auth and auth.lower().startswith("bearer "):
        tok = auth.split(" ",1)[1]
    elif x_admin_token:
        tok = x_admin_token
    if not ADMIN_TOKEN or tok != ADMIN_TOKEN:
        raise HTTPException(401, "Admin token invalide")

@router.get("/articles")
def admin_list(auth: Optional[str]=Header(None), x_admin_token: Optional[str]=Header(None), q: Optional[str]=None):
    check_token(auth, x_admin_token)
    return list_articles(q=q)

@router.post("/articles")
def admin_create(payload: dict, auth: Optional[str]=Header(None), x_admin_token: Optional[str]=Header(None)):
    check_token(auth, x_admin_token)
    row = create_article(payload)
    try: meili_upsert([row])
    except: pass
    return {"ok": True, "id": row["id"], "slug": row["slug"]}

@router.put("/articles/{id}")
def admin_update(id: int, payload: dict, auth: Optional[str]=Header(None), x_admin_token: Optional[str]=Header(None)):
    check_token(auth, x_admin_token)
    row = update_article(id, payload)
    try: meili_upsert([row])
    except: pass
    return {"ok": True}

@router.delete("/articles/{id}")
def admin_delete(id: int, auth: Optional[str]=Header(None), x_admin_token: Optional[str]=Header(None)):
    check_token(auth, x_admin_token)
    delete_article(id)
    try: meili_delete([id])
    except: pass
    return {"ok": True}
