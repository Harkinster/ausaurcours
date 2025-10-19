"""Reindex the knowledge base in Meilisearch.

This script synchronises the ``articles`` table with the configured
Meilisearch index. It reads data using the helpers from the ``ausaur``
package so the behaviour stays consistent with the API itself.
"""
from __future__ import annotations

import json
from typing import Iterable, Dict, Any

from ausaur.db import conn
from ausaur.crud import row_to_doc
from ausaur.meili import ensure_index, upsert


def fetch_documents() -> Iterable[Dict[str, Any]]:
    """Return the documents to index in Meilisearch."""
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM articles")
        for row in cur.fetchall():
            yield row_to_doc(row)


def main() -> None:
    ensure_index()
    docs = list(fetch_documents())
    upsert(docs)
    print(json.dumps({"indexed": len(docs)}, ensure_ascii=False))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
