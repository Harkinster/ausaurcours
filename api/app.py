from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from sqlalchemy import create_engine, text
import os

DB_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@localhost/{os.getenv('DB_NAME')}?charset=utf8mb4"
engine = create_engine(DB_URL, pool_pre_ping=True)

app = FastAPI(title="Au SAURcours API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

@app.get("/health")
def health(): return {"ok": True}

@app.get("/articles")
def list_articles(q: Optional[str] = None):
    sql = "SELECT id,slug,title,content,category,type FROM articles"
    params = {}
    if q:
        sql += " WHERE title LIKE :q OR content LIKE :q"
        params["q"] = f"%{q}%"
    with engine.begin() as cx:
        rows = cx.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]

@app.get("/articles/{slug}")
def get_article(slug: str):
    with engine.begin() as cx:
        r = cx.execute(text("SELECT id,slug,title,content,category,type FROM articles WHERE slug=:s"), {"s": slug}).mappings().first()
    if not r: raise HTTPException(404, "Not found")
    return dict(r)

@app.post("/articles")
def create_article(item: dict):
    required = ["slug","title","content"]
    if not all(k in item and item[k] for k in required):
        raise HTTPException(400, "slug, title, content requis")
    with engine.begin() as cx:
        cx.execute(text("""
          INSERT INTO articles (slug,title,content,category,type)
          VALUES (:slug,:title,:content,:category,:type)
        """), {
            "slug": item["slug"], "title": item["title"],
            "content": item["content"],
            "category": item.get("category","Abonnement"),
            "type": item.get("type","process")
        })
    return {"ok": True}

# --- SEARCH BACKEND (Meili wrapper, union + ranking) ---
import os, re, unicodedata, httpx
from fastapi import Query
from typing import List, Optional

MEILI_URL = os.getenv("MEILI_URL", "http://127.0.0.1:7700")
MEILI_KEY = os.getenv("MEILI_MASTER_KEY", "")

def _norm(s:str)->str:
    if not s: return ""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s

def _toks(q:str)->List[str]:
    return list({t for t in re.split(r"\W+", _norm(q)) if len(t)>=2})

def _intent_boost(q:str)->dict:
    t = _norm(q); plus = {}
    def has(*w): return all(wi in t for wi in w)
    if has('res','abo') or has('resi','abo') or has('resil','abo'): plus['resiliation'] = 50
    if has('souscrire','abo') or has('ouvrir','abo') or has('nouveau','abo') or has('creer','abo') or has('créer','abo'): plus['creer-abonnement'] = 30
    return plus

def _meili_search(q:str, limit:int=24, filt:Optional[str]=None)->List[dict]:
    headers = {"Authorization": f"Bearer {MEILI_KEY}"}
    payload = {"q": q, "limit": limit, "matchingStrategy": "all"}
    if filt: payload["filter"] = filt
    r = httpx.post(f"{MEILI_URL}/indexes/articles/search", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json().get("hits", [])

@app.get("/search")
def search(q: str, limit: int = 20,
           categories: Optional[List[str]] = Query(default=None),
           types: Optional[List[str]] = Query(default=None)):
    toks = _toks(q)
    if not toks:
        return {"hits": []}

    # Filtre Meili (facultatif)
    parts = []
    if categories: parts.append(" OR ".join([f'category = "{c}"' for c in categories]))
    if types:      parts.append(" OR ".join([f'type = "{t}"' for t in types]))
    filt = " AND ".join(f"({p})" for p in parts) if parts else None

    # UNION: 1 requête par token
    by_slug = {}  # slug -> {hit, matches:set, titleN, tagsN, contentN}
    for t in toks:
        for h in _meili_search(t, limit=max(limit, 24), filt=filt):
            slug = h.get("slug") or str(h.get("id"))
            v = by_slug.get(slug)
            if not v:
                v = {
                    "hit": h,
                    "matches": set(),
                    "titleN": _norm(h.get("title","")),
                    "tagsN": _norm(" ".join(h.get("tags",[]) or [])),
                    "contentN": _norm(h.get("content",""))
                }
                by_slug[slug] = v
            v["matches"].add(t)

    # SCORING
    boost = _intent_boost(q)
    scored = []
    for v in by_slug.values():
        h, matches = v["hit"], v["matches"]
        s = 10*len(matches)  # +10 par mot couvert
        for t in toks:
            if t in v["titleN"]:   s += 6
            if t in v["tagsN"]:    s += 3
            if t in v["contentN"]: s += 1
        s += boost.get(h.get("slug",""), 0)
        scored.append((s, h))

    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [h for _,h in scored][:limit]
    return {"hits": hits}
# --- CRUD ARTICLES + synchro Meili ---
import json, re, unicodedata, pymysql, httpx
from fastapi import HTTPException, Request

DB_NAME=os.getenv("DB_NAME","ausaurcours")
DB_USER=os.getenv("DB_USER","ausaur")
DB_PASS=os.getenv("DB_PASS","change_me")
DB_HOST=os.getenv("DB_HOST","localhost")
ADMIN_TOKEN=os.getenv("ADMIN_TOKEN","")

def db():
    return pymysql.connect(
        host=DB_HOST,user=DB_USER,password=DB_PASS,database=DB_NAME,
        charset="utf8mb4",cursorclass=pymysql.cursors.DictCursor,autocommit=True
    )

def _norm(s:str)->str:
    if not s: return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower()

slug_rx = re.compile(r"[^a-z0-9\-]+")
def slugify(title:str)->str:
    s = _norm(title).replace(" ", "-")
    s = slug_rx.sub("", s)
    s = re.sub("-+", "-", s).strip("-")
    return s or "article"

def require_admin(request: Request):
    # Autorise soit "Authorization: Bearer XXX", soit "X-Admin-Token: XXX"
    auth = request.headers.get("authorization","")
    token = request.headers.get("x-admin-token","")
    if auth.startswith("Bearer "):
        token = auth.split(" ",1)[1]
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Admin token invalide")

def meili_upsert(doc:dict):
    headers={"Authorization": f"Bearer {MEILI_KEY}"}
    r=httpx.post(f"{MEILI_URL}/indexes/articles/documents", headers=headers, json=[doc], timeout=10)
    r.raise_for_status()

def meili_delete(doc_id:int):
    headers={"Authorization": f"Bearer {MEILI_KEY}"}
    r=httpx.post(f"{MEILI_URL}/indexes/articles/documents/delete-batch", headers=headers, json=[doc_id], timeout=10)
    r.raise_for_status()

def row_to_doc(row:dict)->dict:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "content": row["content"],
        "category": row["category"],
        "type": row["type"],
        "tags": json.loads(row["tags"]) if row.get("tags") else [],
        "links": json.loads(row["links"]) if row.get("links") else []
    }

@app.get("/articles/{slug}")
def get_article(slug:str):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM articles WHERE slug=%s", (slug,))
        row = cur.fetchone()
        if not row: raise HTTPException(404, "not found")
        return row_to_doc(row)

@app.get("/admin/articles")
def list_articles(request: Request, q:str|None=None, limit:int=200, offset:int=0):
    require_admin(request)
    sql="SELECT * FROM articles "
    args=[]
    if q:
        like = f"%{q}%"
        sql+="WHERE title LIKE %s OR content LIKE %s OR category LIKE %s "
        args+=[like,like,like]
    sql+="ORDER BY updated_at DESC LIMIT %s OFFSET %s"
    args+=[limit,offset]
    with db() as conn, conn.cursor() as cur:
        cur.execute(sql, args)
        rows=cur.fetchall()
    return [row_to_doc(r) for r in rows]

@app.post("/admin/articles")
def create_article(payload: dict, request: Request):
    require_admin(request)
    title = payload.get("title","").strip()
    if not title: raise HTTPException(400,"title requis")
    slug = payload.get("slug") or slugify(title)
    content = payload.get("content","")
    category = payload.get("category","Processus")
    type_ = payload.get("type","process")
    tags = payload.get("tags") or []
    links = payload.get("links") or []
    with db() as conn, conn.cursor() as cur:
        cur.execute("""INSERT INTO articles(slug,title,content,category,type,tags,links)
                       VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                    (slug,title,content,category,type_,json.dumps(tags,ensure_ascii=False),json.dumps(links,ensure_ascii=False)))
        cur.execute("SELECT * FROM articles WHERE id=LAST_INSERT_ID()")
        row=cur.fetchone()
    doc=row_to_doc(row)
    meili_upsert(doc)
    return {"ok":True,"id":row["id"],"slug":row["slug"]}

@app.put("/admin/articles/{id}")
def update_article(id:int, payload: dict, request: Request):
    require_admin(request)
    fields=[]
    args=[]
    for k in ("slug","title","content","category","type"):
        if k in payload and payload[k] is not None:
            fields.append(f"{k}=%s"); args.append(payload[k])
    if "tags" in payload:
        fields.append("tags=%s"); args.append(json.dumps(payload["tags"] or [],ensure_ascii=False))
    if "links" in payload:
        fields.append("links=%s"); args.append(json.dumps(payload["links"] or [],ensure_ascii=False))
    if not fields: return {"ok":True}
    args.append(id)
    with db() as conn, conn.cursor() as cur:
        cur.execute(f"UPDATE articles SET {', '.join(fields)} WHERE id=%s", args)
        cur.execute("SELECT * FROM articles WHERE id=%s",(id,))
        row=cur.fetchone()
        if not row: raise HTTPException(404,"not found")
    meili_upsert(row_to_doc(row))
    return {"ok":True}

@app.delete("/admin/articles/{id}")
def delete_article(id:int, request: Request):
    require_admin(request)
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM articles WHERE id=%s",(id,))
    meili_delete(id)
    return {"ok":True}

# --- Alias simple /search (pour tolérer /api retiré par le proxy) ---
from typing import Optional, List
from fastapi import Query
import os, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

MEILI_URL = os.getenv("MEILI_URL", "http://127.0.0.1:7700")
MEILI_INDEX = os.getenv("MEILI_INDEX", "articles")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY", "")

@app.get("/search")
def search_alias(q: str, categories: Optional[List[str]] = Query(None)):
    payload = {"q": q, "limit": 20}
    if categories:
        payload["filter"] = " OR ".join([f'category = "{c}"' for c in categories])
    req = Request(
        f"{MEILI_URL}/indexes/{MEILI_INDEX}/search",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
    )
    if MEILI_MASTER_KEY:
        req.add_header("Authorization", f"Bearer {MEILI_MASTER_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req) as r:
            data = json.loads(r.read().decode("utf-8"))
            return {"hits": data.get("hits", [])}
    except HTTPError as e:
        return {"hits": [], "error": f"meili {e.code}"}

# --- SEARCH endpoints (ajout) ---
from fastapi import Query
from typing import Optional, List
import os, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

MEILI_URL = os.getenv("MEILI_URL","http://127.0.0.1:7700")
MEILI_INDEX = os.getenv("MEILI_INDEX","articles")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY","")

def _do_search(q: str, categories: Optional[List[str]]):
    payload = {"q": q, "limit": 20}
    if categories:
        payload["filter"] = " OR ".join([f'category = "{c}"' for c in categories])
    req = Request(
        f"{MEILI_URL}/indexes/{MEILI_INDEX}/search",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
    )
    if MEILI_MASTER_KEY:
        req.add_header("Authorization", f"Bearer {MEILI_MASTER_KEY}")
    req.add_header("Content-Type", "application/json")
    with urlopen(req) as r:
        data = json.loads(r.read().decode("utf-8"))
        return {"hits": data.get("hits", [])}

@app.get("/api/search")
def search_api(q: str, categories: Optional[List[str]] = Query(None)):
    try:
        return _do_search(q, categories)
    except (HTTPError, URLError) as e:
        return {"hits": [], "error": f"{e}"}

@app.get("/search")  # alias de secours
def search_alias(q: str, categories: Optional[List[str]] = Query(None)):
    try:
        return _do_search(q, categories)
    except (HTTPError, URLError) as e:
        return {"hits": [], "error": f"{e}"}

# --- ALIAS pour compat simplicité derrière Apache ---
from fastapi import Query
from typing import Optional, List

# Si la fonction search officielle est /api/search :
# On lui colle un alias public /search qui délègue dessus.

@app.get("/search")
def _search_alias(q: str, categories: Optional[List[str]] = Query(None)):
    # Délègue à l'endpoint officiel si tu l’as appelé différemment, adapte :
    return search(q=q, categories=categories)

# Idem santé, pour que /api/health puisse cibler /health si besoin
@app.get("/health")
def _health_alias():
    return {"ok": True}

@app.get("/api/health")
def api_health():
    return {"ok": True}
