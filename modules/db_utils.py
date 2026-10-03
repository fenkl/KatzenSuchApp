"""DB utilities for KatzenSuchApp - SQLite gezien.db schema and CRUD."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

from classes.Cconfig import Config


def _get_db_path():
    """Dynamically get DB path from Config."""
    config = Config()
    return Path(config.db_path).resolve()


def get_connection():
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if not exists."""
    conn = get_connection()
    cur = conn.cursor()
    
    # platforms
    cur.execute("""
        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            base_url TEXT,
            enabled INTEGER DEFAULT 1
        )
    """)
    
    # seen_urls
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            platform TEXT NOT NULL,
            url_hash TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed INTEGER DEFAULT 0,
            UNIQUE(url, platform)
        )
    """)
    
    # configs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # scraper_configs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scraper_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_name TEXT NOT NULL,
            base_url TEXT,
            listing_selector TEXT,
            detail_selector TEXT,
            pagination_param TEXT,
            city_param TEXT,
            enabled INTEGER DEFAULT 1,
            handler_class TEXT,
            login_required INTEGER DEFAULT 0
        )
    """)
    
    # feature_requests
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feature_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_name TEXT NOT NULL,
            start_url TEXT,
            example_listing_url TEXT,
            description TEXT,
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'open'
        )
    """)
    
    # scraped_listings - NEW: Store raw scraping results
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scraped_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            platform TEXT NOT NULL,
            city TEXT,
            title TEXT,
            description TEXT,
            age INTEGER,
            extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            url_hash TEXT UNIQUE,
            processed INTEGER DEFAULT 0,
            UNIQUE(url, platform)
        )
    """)
    
    # llm_classification
    cur.execute("""
        CREATE TABLE IF NOT EXISTS llm_classification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash TEXT UNIQUE NOT NULL,
            url TEXT,
            platform TEXT,
            alter_ok INTEGER,
            alter_jahre INTEGER,
            alter_unsicher INTEGER,
            einzelgaenger INTEGER,
            einzelgaenger_unsicher INTEGER,
            freigang_noetig INTEGER,
            freigang_unsicher INTEGER,
            kein_freigang_gewuenscht INTEGER,
            confidence REAL,
            reason TEXT,
            classified_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ratings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            platform TEXT,
            rating INTEGER,
            comment TEXT,
            rated_by TEXT,
            rated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def is_known(url: str, platform: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM seen_urls WHERE url = ? AND platform = ?", (url, platform))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def save_url(url: str, platform: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    cur.execute("""
        INSERT OR IGNORE INTO seen_urls (url, platform, url_hash) VALUES (?, ?, ?)
    """, (url, platform, url_hash))
    conn.commit()
    conn.close()


def get_scraper_configs() -> List[Tuple]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, platform_name, base_url, listing_selector, detail_selector,
               pagination_param, city_param, enabled, handler_class, login_required,
               '' as created_at, '' as updated_at
        FROM scraper_configs
    """)
    rows = cur.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def add_scraper_config(platform_name: str, base_url: str = None, listing_selector: str = None,
                       detail_selector: str = None, pagination_param: str = None,
                       city_param: str = None, enabled: int = 1,
                       handler_class: str = None, login_required: int = 0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO scraper_configs
        (platform_name, base_url, listing_selector, detail_selector,
         pagination_param, city_param, enabled, handler_class, login_required)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (platform_name, base_url, listing_selector, detail_selector,
          pagination_param, city_param, enabled, handler_class, login_required))
    conn.commit()
    conn.close()


def get_platforms() -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, base_url, enabled FROM platforms")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_feature_request(platform_name: str, start_url: str, example_listing_url: str,
                        description: str, created_by: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO feature_requests (platform_name, start_url, example_listing_url, description, created_by)
        VALUES (?, ?, ?, ?, ?)
    """, (platform_name, start_url, example_listing_url, description, created_by))
    conn.commit()
    conn.close()


def get_feature_requests(status: Optional[str] = None) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM feature_requests WHERE status = ?", (status,))
    else:
        cur.execute("SELECT * FROM feature_requests")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_scraped_listing(url: str, platform: str, city: str, title: str, description: str, age: Optional[int] = None):
    """Save scraped listing details to DB."""
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO scraped_listings
        (url, platform, city, title, description, age, url_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (url, platform, city, title, description, age, url_hash))
    conn.commit()
    conn.close()


def mark_processed(url: str, platform: str, processed: bool = True):
    """Mark URL as processed."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE seen_urls SET processed = ?, last_seen = CURRENT_TIMESTAMP 
        WHERE url = ? AND platform = ?
    """, (1 if processed else 0, url, platform))
    conn.commit()
    conn.close()


def get_scraped_listings(limit: int = 100, offset: int = 0, processed: Optional[int] = None) -> List[Dict]:
    """Get scraped listings with optional processed filter."""
    conn = get_connection()
    cur = conn.cursor()
    
    if processed is not None:
        cur.execute("""
            SELECT sl.*, lc.confidence, lc.alter_ok, lc.einzelgaenger, lc.freigang_noetig
            FROM scraped_listings sl
            LEFT JOIN llm_classification lc ON sl.url_hash = lc.url_hash
            WHERE sl.processed = ?
            ORDER BY sl.extracted_at DESC
            LIMIT ? OFFSET ?
        """, (processed, limit, offset))
    else:
        cur.execute("""
            SELECT sl.*, lc.confidence, lc.alter_ok, lc.einzelgaenger, lc.freigang_noetig
            FROM scraped_listings sl
            LEFT JOIN llm_classification lc ON sl.url_hash = lc.url_hash
            ORDER BY sl.extracted_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
    
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def cache_llm_classification(url: str, platform: str, result: Dict):
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO llm_classification
        (url_hash, url, platform, alter_ok, alter_jahre, alter_unsicher,
         einzelgaenger, einzelgaenger_unsicher, freigang_noetig, freigang_unsicher,
         kein_freigang_gewuenscht, confidence, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url_hash, url, platform,
        int(result.get("alter_ok", 0)),
        result.get("alter_jahre"),
        int(result.get("alter_unsicher", False)),
        int(result.get("einzelgaenger", 0)),
        int(result.get("einzelgaenger_unsicher", False)),
        int(result.get("freigang_noetig", 0)),
        int(result.get("freigang_unsicher", False)),
        int(result.get("kein_freigang_gewuenscht", 0)),
        result.get("confidence", 0.0),
        result.get("reason", "")
    ))
    conn.commit()
    conn.close()


def get_llm_classification(url: str) -> Optional[Dict]:
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM llm_classification WHERE url_hash = ?", (url_hash,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


if __name__ == "__main__":
    init_db()
    print("DB initialized at", _get_db_path())
