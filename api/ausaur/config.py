import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DB_NAME = os.getenv("DB_NAME", "ausaurcours")
DB_USER = os.getenv("DB_USER", "ausaur")
DB_PASS = os.getenv("DB_PASS", "change_me")
DB_HOST = os.getenv("DB_HOST", "localhost")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

MEILI_URL = os.getenv("MEILI_URL", "http://127.0.0.1:7700")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY", "change_this_master_key_really")
MEILI_INDEX = os.getenv("MEILI_INDEX", "articles")
