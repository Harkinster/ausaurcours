import json, httpx
from typing import List, Dict, Any, Optional, Iterable
from .config import MEILI_URL, MEILI_MASTER_KEY, MEILI_INDEX

HEAD = {"Authorization": f"Bearer {MEILI_MASTER_KEY}"}

def ensure_index():
    with httpx.Client(timeout=10) as x:
        r = x.get(f"{MEILI_URL}/indexes/{MEILI_INDEX}", headers=HEAD)
        if r.status_code == 404:
            x.put(f"{MEILI_URL}/indexes/{MEILI_INDEX}", headers=HEAD, json={"uid": MEILI_INDEX, "primaryKey": "id"})
        # settings minimales
        x.patch(f"{MEILI_URL}/indexes/{MEILI_INDEX}/settings", headers=HEAD, json={
            "displayedAttributes":["id","slug","title","content","category","type","tags","links"],
            "searchableAttributes":["title","tags","content"],
            "filterableAttributes":["category","tags"],
        })

def search(q:str, categories: Optional[List[str]]=None) -> Dict[str, Any]:
    payload = {"q": q, "limit": 24}
    if categories:
        # ex: category IN ["Abonnement","Résiliation"]
        vals = ",".join([json.dumps(c) for c in categories])
        payload["filter"] = f'category IN [{vals}]'
    with httpx.Client(timeout=10) as x:
        r = x.post(f"{MEILI_URL}/indexes/{MEILI_INDEX}/search", headers=HEAD, json=payload)
        r.raise_for_status()
        return r.json()

def upsert(docs: Iterable[Dict[str, Any]]):
    docs = list(docs)
    if not docs: return
    with httpx.Client(timeout=10) as x:
        x.post(f"{MEILI_URL}/indexes/{MEILI_INDEX}/documents", headers=HEAD, json=docs)

def delete_ids(ids: List[int]):
    if not ids: return
    with httpx.Client(timeout=10) as x:
        x.post(f"{MEILI_URL}/indexes/{MEILI_INDEX}/documents/delete-batch", headers=HEAD, json=ids)
