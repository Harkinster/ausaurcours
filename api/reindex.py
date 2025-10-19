import os, json, sys
import pymysql
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DB_NAME = os.getenv("DB_NAME","ausaurcours")
DB_USER = os.getenv("DB_USER","ausaur")
DB_PASS = os.getenv("DB_PASS","change_me")
DB_HOST = os.getenv("DB_HOST","localhost")

MEILI_URL = os.getenv("MEILI_URL","http://127.0.0.1:7700")
MEILI_KEY = os.getenv("MEILI_MASTER_KEY","change_this_master_key_really")
INDEX     = os.getenv("MEILI_INDEX","articles")

def http(method, path, data=None, auth=True):
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = Request(MEILI_URL + path, data=body, method=method)
    if auth:
        req.add_header("Authorization", f"Bearer {MEILI_KEY}")
    req.add_header("Content-Type","application/json")
    with urlopen(req) as r:
        raw = r.read()
        if not raw: return None
        try: return json.loads(raw.decode("utf-8"))
        except Exception: return raw.decode("utf-8")

def ensure_index(uid):
    try:
        http("GET", f"/indexes/{uid}")
    except HTTPError as e:
        if e.code == 404:
            http("POST", "/indexes", {"uid": uid, "primaryKey": "id"})
        else:
            raise

def main():
    # 1) DB → lecture
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                           database=DB_NAME, charset="utf8mb4",
                           cursorclass=pymysql.cursors.DictCursor)
    with conn, conn.cursor() as cur:
        cur.execute("SELECT id, slug, title, content, category, type, updated_at FROM articles")
        articles = cur.fetchall()
        id2slug = {a["id"]: a["slug"] for a in articles}

        cur.execute("""SELECT at.article_id, t.name AS tag
                       FROM article_tags at JOIN tags t ON t.id = at.tag_id""")
        tag_rows = cur.fetchall()
        tags_map = {}
        for r in tag_rows:
            tags_map.setdefault(r["article_id"], []).append(r["tag"])

        cur.execute("SELECT src_article_id, dst_article_id FROM article_links")
        link_rows = cur.fetchall()
        links_map = {}
        for r in link_rows:
            links_map.setdefault(r["src_article_id"], []).append(id2slug.get(r["dst_article_id"]))

    # 2) Docs pour Meili
    docs = []
    for a in articles:
        docs.append({
            "id": a["id"],
            "slug": a["slug"],
            "title": a["title"],
            "content": a["content"],
            "category": a["category"],
            "type": a["type"],
            "tags": sorted(list(set(tags_map.get(a["id"], [])))),
            "links": [s for s in (links_map.get(a["id"], []) or []) if s],
            "updated_at": a["updated_at"].isoformat() if a.get("updated_at") else None
        })

    # 3) Index → création si besoin, puis push
    try:
        ensure_index(INDEX)
    except Exception as e:
        print("ensure_index failed:", e, file=sys.stderr)
        sys.exit(2)

    out = http("POST", f"/indexes/{INDEX}/documents", docs)
    print(json.dumps({"indexed": len(docs), "task": out}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except HTTPError as e:
        print("HTTPError:", e.code, e.reason, file=sys.stderr); sys.exit(3)
    except URLError as e:
        print("URLError:", e.reason, file=sys.stderr); sys.exit(4)
    except Exception as e:
        print("Error:", repr(e), file=sys.stderr); sys.exit(5)
