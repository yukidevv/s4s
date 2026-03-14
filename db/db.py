import sqlite3
import os

class StartsDB:
  def __init__(self):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(base_dir, "..", "data", "stars.db")
    self.db_path = DB_PATH
    self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
    self._init_db()

  def _init_db(self):
      self.conn.execute("PRAGMA journal_mode=WAL;")
      self.conn.execute("""
        CREATE TABLE IF NOT EXISTS feeds
        (
          url_2_hash  TEXT PRIMARY KEY,
          title       TEXT,
          link        TEXT,
          domain      TEXT,
          source_name TEXT,
          read        INTEGER NOT NULL DEFAULT 0,
          created_at  TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
        )
      """)
      self.conn.execute("""
        CREATE TABLE IF NOT EXISTS sources
        (
          url        TEXT PRIMARY KEY,
          domain     TEXT,
          name       TEXT,
          created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
        )
      """)
      self.conn.commit()

  def register_feed(self, title, link, domain, source_name):
    content_hash = __import__("hashlib").md5(link.encode()).hexdigest()
    self.conn.execute("INSERT INTO feeds (url_2_hash, title, link, domain, source_name) VALUES (?, ?, ?, ?, ?)", (content_hash, title, link, domain, source_name))
    self.conn.commit()

  def fetch_all(self):
    res = self.conn.execute("SELECT url_2_hash from feeds").fetchall()
    return {r[0] for r in res}

  def fetch_entries(self):
    res = self.conn.execute(
      "SELECT url_2_hash, title, link, source_name, domain, created_at FROM feeds WHERE read = 0 ORDER BY created_at DESC"
    ).fetchall()
    return [{"id": r[0], "title": r[1], "link": r[2], "source_name": r[3], "domain": r[4], "created_at": r[5]} for r in res]

  def delete_entry(self, url_2_hash: str) -> bool:
    cur = self.conn.execute("UPDATE feeds SET read = 1 WHERE url_2_hash = ?", (url_2_hash,))
    self.conn.commit()
    return cur.rowcount > 0

  def add_source(self, url, domain, name):
    self.conn.execute("INSERT OR IGNORE INTO sources (url, domain, name) VALUES (?, ?, ?)", (url, domain, name))
    self.conn.commit()

  def get_sources(self):
    res = self.conn.execute("SELECT url, domain, name, created_at FROM sources ORDER BY created_at").fetchall()
    return [{"url": r[0], "domain": r[1], "name": r[2], "created_at": r[3]} for r in res]

  def delete_source(self, url):
    self.conn.execute("DELETE FROM feeds WHERE domain = (SELECT domain FROM sources WHERE url = ?)", (url,))
    cur = self.conn.execute("DELETE FROM sources WHERE url = ?", (url,))
    self.conn.commit()
    return cur.rowcount > 0