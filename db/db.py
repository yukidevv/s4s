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
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          url TEXT UNIQUE,
          keywords TEXT
        )
      """)
      self.conn.execute("""
        CREATE TABLE IF NOT EXISTS history 
        (
          link TEXT PRIMARY KEY,
          title TEXT,
          created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
        )
      """)
      self.conn.commit()
  def register_feed(self, title, link):
    self.conn.execute("INSERT INTO feeds (url) VALUES (?)", (link, ))
    self.conn.execute("INSERT INTO history (link) VALUES (?)", (link, ))
    self.conn.commit()

