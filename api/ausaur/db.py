import pymysql
from pymysql.cursors import DictCursor
from .config import DB_HOST, DB_USER, DB_PASS, DB_NAME

def conn():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME,
        charset="utf8mb4", cursorclass=DictCursor, autocommit=True
    )

def ensure_schema():
    with conn() as c, c.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
          id INT AUTO_INCREMENT PRIMARY KEY,
          slug VARCHAR(191) NOT NULL UNIQUE,
          title VARCHAR(255) NOT NULL,
          content MEDIUMTEXT NOT NULL,
          category VARCHAR(64) NOT NULL,
          type VARCHAR(32) NOT NULL DEFAULT 'process',
          tags JSON NULL,
          links JSON NULL,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
