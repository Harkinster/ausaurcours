import typesense
from app.config import get_settings

def _client():
    s = get_settings()
    if not s.TYPESENSE_API_KEY:
        return None
    return typesense.Client({
        'nodes': [{'host': s.TYPESENSE_HOST, 'port': s.TYPESENSE_PORT, 'protocol': s.TYPESENSE_PROTOCOL}],
        'api_key': s.TYPESENSE_API_KEY,
        'connection_timeout_seconds': 2
    })

def ensure_collection():
    s = get_settings()
    if not s.TYPESENSE_API_KEY:
        print("Typesense désactivé (API key manquant)")
        return
    c = _client()
    if c is None:
        return
    schema = {
        'name': s.TYPESENSE_COLLECTION,
        'fields': [
            {'name':'id','type':'string'},
            {'name':'slug','type':'string'},
            {'name':'title','type':'string'},
            {'name':'content','type':'string'},
            {'name':'category','type':'string','facet':True},
            {'name':'tags','type':'string[]','facet':True},
            {'name':'created_at','type':'int64'},
            {'name':'updated_at','type':'int64'},
        ],
        'default_sorting_field': 'updated_at'
    }
    try:
        c.collections[s.TYPESENSE_COLLECTION].retrieve()
    except:
        try:
            c.collections.create(schema)
        except Exception as e:
            print(f"Typesense: création collection échouée → {e}")

def upsert_document(doc):
    s = get_settings()
    if not s.TYPESENSE_API_KEY:
        return
    c = _client()
    if c is None:
        return
    try:
        c.collections[s.TYPESENSE_COLLECTION].documents.upsert(doc)
    except Exception as e:
        print(f"Typesense: upsert échoué → {e}")
