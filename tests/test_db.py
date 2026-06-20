"""StartsDB の DB 操作に関するテスト。"""

from db.db import StartsDB


def _hash(link):
  # 本体のハッシュ方式に追従させるため StartsDB._hash に委譲する
  return StartsDB._hash(link)


# --- add_saved_link の UPSERT セマンティクス ---

def test_add_saved_link_new(db):
  """新規追加は saved=1 / read=0 で記録される。"""
  db.add_saved_link("タイトル", "https://example.com/a", "example.com", "example.com")
  saved = db.fetch_saved()
  assert len(saved) == 1
  assert saved[0]["title"] == "タイトル"
  assert saved[0]["link"] == "https://example.com/a"
  # fetch_saved は saved=1 のみ返すので、ここに出る時点で saved=1
  # read=0 であることも確認（read=1 なら fetch_entries には出ないが saved には出る）
  h = _hash("https://example.com/a")
  row = db.conn.execute("SELECT read, saved FROM feeds WHERE url_2_hash = ?", (h,)).fetchone()
  assert row == (0, 1)


def test_add_saved_link_conflict_resaves(db):
  """既存エントリ（既読化済み）に同一URLを add_saved_link すると saved=1 / read=0 に戻る。"""
  link = "https://example.com/a"
  # 通常エントリとして登録し、既読化する
  db.register_feed("元タイトル", link, "example.com", "元ソース")
  db.delete_entry(_hash(link))  # read=1
  # 同一URLを後で読むに直接追加
  db.add_saved_link("新タイトル", link, "example.com", "example.com")
  row = db.conn.execute(
    "SELECT read, saved, title FROM feeds WHERE url_2_hash = ?", (_hash(link),)
  ).fetchone()
  assert row[0] == 0  # read=0 に戻る
  assert row[1] == 1  # saved=1
  assert row[2] == "元タイトル"  # タイトルは上書きされない


def test_add_saved_link_conflict_keeps_existing_title(db):
  """URL衝突時、既存タイトルは上書きされない。"""
  link = "https://example.com/a"
  db.register_feed("元タイトル", link, "example.com", "元ソース")
  db.add_saved_link("新タイトル", link, "example.com", "example.com")
  row = db.conn.execute(
    "SELECT title FROM feeds WHERE url_2_hash = ?", (_hash(link),)
  ).fetchone()
  assert row[0] == "元タイトル"


# --- ソフト削除セマンティクス ---

def test_delete_entry_soft(db):
  """delete_entry は read=1 を立てるソフト削除。"""
  link = "https://example.com/a"
  db.register_feed("t", link, "example.com", "s")
  assert db.delete_entry(_hash(link)) is True
  row = db.conn.execute(
    "SELECT read FROM feeds WHERE url_2_hash = ?", (_hash(link),)
  ).fetchone()
  assert row[0] == 1


def test_delete_entry_missing_returns_false(db):
  assert db.delete_entry("notexist") is False


def test_save_entry(db):
  link = "https://example.com/a"
  db.register_feed("t", link, "example.com", "s")
  assert db.save_entry(_hash(link)) is True
  row = db.conn.execute(
    "SELECT saved FROM feeds WHERE url_2_hash = ?", (_hash(link),)
  ).fetchone()
  assert row[0] == 1


def test_save_entry_missing_returns_false(db):
  assert db.save_entry("notexist") is False


def test_delete_saved_soft(db):
  """delete_saved は saved=0 / read=1 にする。"""
  link = "https://example.com/a"
  db.add_saved_link("t", link, "example.com", "example.com")
  assert db.delete_saved(_hash(link)) is True
  row = db.conn.execute(
    "SELECT read, saved FROM feeds WHERE url_2_hash = ?", (_hash(link),)
  ).fetchone()
  assert row == (1, 0)


def test_delete_saved_missing_returns_false(db):
  assert db.delete_saved("notexist") is False


# --- fetch_entries / fetch_saved のフィルタ ---

def test_fetch_entries_filters_read_and_saved(db):
  """fetch_entries は read=0 AND saved=0 のみ返す。"""
  db.register_feed("unread", "https://example.com/1", "example.com", "s")
  db.register_feed("toread", "https://example.com/2", "example.com", "s")
  db.register_feed("done", "https://example.com/3", "example.com", "s")
  db.save_entry(_hash("https://example.com/2"))   # saved=1 → 除外
  db.delete_entry(_hash("https://example.com/3"))  # read=1 → 除外
  entries = db.fetch_entries()
  titles = {e["title"] for e in entries}
  assert titles == {"unread"}


def test_fetch_saved_filters_saved(db):
  """fetch_saved は saved=1 のみ返す。"""
  db.register_feed("unread", "https://example.com/1", "example.com", "s")
  db.register_feed("toread", "https://example.com/2", "example.com", "s")
  db.save_entry(_hash("https://example.com/2"))
  saved = db.fetch_saved()
  titles = {e["title"] for e in saved}
  assert titles == {"toread"}


# --- delete_source の domain カスケード削除 ---

def test_delete_source_cascades_by_domain(db):
  """delete_source は同一 domain の feeds を全削除し、別 domain は残す。"""
  db.add_source("https://example.com/feed", "example.com", "Example")
  db.register_feed("a", "https://example.com/a", "example.com", "Example")
  db.register_feed("b", "https://example.com/b", "example.com", "Example")
  db.register_feed("other", "https://other.com/x", "other.com", "Other")
  assert db.delete_source("https://example.com/feed") is True
  remaining = db.conn.execute("SELECT domain FROM feeds").fetchall()
  domains = {r[0] for r in remaining}
  assert domains == {"other.com"}
  # source も消える
  assert db.get_sources() == []


def test_delete_source_missing_returns_false(db):
  assert db.delete_source("https://notexist.com/feed") is False
