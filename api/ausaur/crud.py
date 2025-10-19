import json
from typing import List, Optional, Dict, Any
from pymysql.err import IntegrityError
from .db import conn
from .utils import slugify

def _parse_json(v):
    if v is None: return []
    if isinstance(v, (list, dict)): return v
    try: return json.loads(v)
    except: return []

def row_to_doc(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "content": row["content"],
        "category": row["category"],
        "type": row.get("type","process"),
        "tags": _parse_json(row.get("tags")),
        "links": _parse_json(row.get("links")),
    }

def unique_slug(cur, wanted: str, exclude_id: Optional[int] = None) -> str:
    base = wanted or "article"; slug = base; n = 2
    while True:
        if exclude_id is None:
            cur.execute("SELECT 1 FROM articles WHERE slug=%s", (slug,))
        else:
            cur.execute("SELECT 1 FROM articles WHERE slug=%s AND id<>%s", (slug, exclude_id))
        if not cur.fetchone(): return slug
        slug = f"{base}-{n}"; n += 1

def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM articles WHERE slug=%s", (slug,))
        row = cur.fetchone()
        return row_to_doc(row) if row else None

def list_articles(q: Optional[str]=None, limit:int=200, offset:int=0) -> List[Dict[str, Any]]:
    with conn() as c, c.cursor() as cur:
        sql="SELECT * FROM articles "; args=[]
        if q:
            like=f"%{q}%"
            sql+="WHERE title LIKE %s OR content LIKE %s OR category LIKE %s "
            args+=[like,like,like]
        sql+="ORDER BY updated_at DESC LIMIT %s OFFSET %s"; args+=[limit,offset]
        cur.execute(sql, args)
        return [row_to_doc(r) for r in cur.fetchall()]

def create_article(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = (payload.get("title") or "").strip()
    if not title: raise ValueError("title requis")
    raw_slug = (payload.get("slug") or slugify(title)).strip()
    content = payload.get("content","")
    category = payload.get("category","Processus")
    type_ = payload.get("type","process")
    tags = payload.get("tags") or []
    links = payload.get("links") or []
    with conn() as c, c.cursor() as cur:
        slug = unique_slug(cur, raw_slug)
        try:
            cur.execute("""INSERT INTO articles(slug,title,content,category,type,tags,links)
                           VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                        (slug,title,content,category,type_,json.dumps(tags,ensure_ascii=False),
                         json.dumps(links,ensure_ascii=False)))
            cur.execute("SELECT * FROM articles WHERE id=LAST_INSERT_ID()")
            row=cur.fetchone()
        except IntegrityError as e:
            raise RuntimeError("slug déjà utilisé") from e
    return row_to_doc(row)

def update_article(id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    fields=[]; args=[]
    with conn() as c, c.cursor() as cur:
        if "slug" in payload and payload["slug"] is not None:
            new_slug = unique_slug(cur, (payload["slug"] or "").strip(), exclude_id=id)
            fields.append("slug=%s"); args.append(new_slug)
        for k in ("title","content","category","type"):
            if k in payload and payload[k] is not None:
                fields.append(f"{k}=%s"); args.append(payload[k])
        if "tags" in payload:
            fields.append("tags=%s"); args.append(json.dumps(payload["tags"] or [], ensure_ascii=False))
        if "links" in payload:
            fields.append("links=%s"); args.append(json.dumps(payload["links"] or [], ensure_ascii=False))
        if not fields:
            cur.execute("SELECT * FROM articles WHERE id=%s",(id,))
            row=cur.fetchone()
            if not row: raise LookupError("not found")
            return row_to_doc(row)
        args.append(id)
        cur.execute(f"UPDATE articles SET {', '.join(fields)} WHERE id=%s", args)
        cur.execute("SELECT * FROM articles WHERE id=%s",(id,))
        row=cur.fetchone()
        if not row: raise LookupError("not found")
    return row_to_doc(row)

def delete_article(id:int)->None:
    with conn() as c, c.cursor() as cur:
        cur.execute("DELETE FROM articles WHERE id=%s",(id,))
