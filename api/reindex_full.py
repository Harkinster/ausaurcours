import json
from ausaur.db import conn
from ausaur.crud import row_to_doc
from ausaur.meili import ensure_index, upsert, delete_ids
def main():
    ensure_index()
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM articles")
        rows = cur.fetchall()
    docs=[row_to_doc(r) for r in rows]
    upsert(docs)
    # pas d'effacement ici (optionnel: lire les ids Meili et supprimer orphelins)
    print(json.dumps({"upserted": len(docs)}, ensure_ascii=False))
if __name__ == "__main__":
    main()
