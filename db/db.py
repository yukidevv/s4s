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
          url_2_hash TEXT PRIMARY KEY,
          domain TEXT,
          created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
        )
      """)
      self.conn.execute("""
        CREATE TABLE IF NOT EXISTS sources
        (
          url TEXT PRIMARY KEY,
          domain TEXT,
          created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
        )
      """)
      self.conn.commit()

  def register_feed(self, title, link, domain):
    self.conn.execute("INSERT INTO feeds (url_2_hash, domain) VALUES (?, ?)", (link, domain))
    self.conn.commit()

  def fetch_all(self):
    res = self.conn.execute("SELECT url_2_hash from feeds").fetchall()
    return {r[0] for r in res}

  def add_source(self, url, domain):
    self.conn.execute("INSERT OR IGNORE INTO sources (url, domain) VALUES (?, ?)", (url, domain))
    self.conn.commit()

  def get_sources(self):
    res = self.conn.execute("SELECT url, domain, created_at FROM sources ORDER BY created_at").fetchall()
    return [{"url": r[0], "domain": r[1], "created_at": r[2]} for r in res]

  def delete_source(self, url):
    cur = self.conn.execute("DELETE FROM sources WHERE url = ?", (url,))
    self.conn.commit()
    return cur.rowcount > 0