import re, unicodedata

_slug_rx = re.compile(r"[^a-z0-9\-]+")

def normalize(s: str) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower()

def slugify(title: str) -> str:
    s = normalize(title).replace(" ", "-")
    s = _slug_rx.sub("", s)
    s = re.sub("-+", "-", s).strip("-")
    return s or "article"
