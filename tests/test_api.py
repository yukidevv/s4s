"""api.py の HTTP エンドポイントのテスト（TestClient 使用、実ネットワーク不使用）。

STARTS_TOKEN を未設定にすることで認証 middleware は素通りする（expected が空文字のため）。
api.py は各エンドポイント内で StartsDB() を引数なしで生成するため、
テストでは api.StartsDB を一時ファイル DB を使うファクトリに差し替えて本番 DB を汚さない。
"""

import pytest
from fastapi.testclient import TestClient

import api
from db.db import StartsDB


@pytest.fixture
def app_client(tmp_path, monkeypatch):
  monkeypatch.delenv("STARTS_TOKEN", raising=False)
  db_path = str(tmp_path / "api.db")
  monkeypatch.setattr(api, "StartsDB", lambda: StartsDB(db_path=db_path))
  return TestClient(api.app)


def test_post_saved_invalid_url_returns_400(app_client, monkeypatch):
  # ドメインが取れない無効 URL → 400。fetch_page_title は呼ばれない想定だが念のためモック。
  monkeypatch.setattr(api, "fetch_page_title", lambda url: "should-not-be-used")
  resp = app_client.post("/api/saved", json={"url": "not a url"})
  assert resp.status_code == 400


def test_post_saved_valid_url_succeeds(app_client, monkeypatch):
  monkeypatch.setattr(api, "fetch_page_title", lambda url: "モックタイトル")
  resp = app_client.post("/api/saved", json={"url": "https://example.com/article"})
  assert resp.status_code == 201
  body = resp.json()
  assert body["link"] == "https://example.com/article"
  assert body["title"] == "モックタイトル"
  assert body["domain"] == "example.com"
  # 後で読む一覧に追加されている
  saved = app_client.get("/api/saved").json()
  assert any(s["link"] == "https://example.com/article" for s in saved)


# --- PATCH /api/sources（フィード名変更） ---

def _seed_source(db_path):
  """テスト用に source と feeds を1件ずつ登録する。"""
  db = StartsDB(db_path=db_path)
  db.add_source("https://example.com/feed", "example.com", "旧名")
  db.register_feed("記事", "https://example.com/a", "example.com", "旧名")
  db.conn.close()


def test_patch_source_renames(app_client, tmp_path):
  db_path = str(tmp_path / "api.db")
  _seed_source(db_path)
  resp = app_client.patch(
    "/api/sources", json={"url": "https://example.com/feed", "name": "新名"}
  )
  assert resp.status_code == 200
  assert resp.json()["name"] == "新名"

  # sources 一覧に反映
  sources = app_client.get("/api/sources").json()
  assert any(s["url"] == "https://example.com/feed" and s["name"] == "新名" for s in sources)

  # 既存記事の source_name も更新される
  db = StartsDB(db_path=db_path)
  name = db.conn.execute(
    "SELECT source_name FROM feeds WHERE domain = ?", ("example.com",)
  ).fetchone()[0]
  db.conn.close()
  assert name == "新名"


def test_patch_source_strips_and_rejects_blank(app_client, tmp_path):
  db_path = str(tmp_path / "api.db")
  _seed_source(db_path)
  resp = app_client.patch(
    "/api/sources", json={"url": "https://example.com/feed", "name": "   "}
  )
  assert resp.status_code == 400


def test_patch_source_missing_returns_404(app_client):
  resp = app_client.patch(
    "/api/sources", json={"url": "https://notexist.com/feed", "name": "新名"}
  )
  assert resp.status_code == 404


# --- POST /api/entries/read-all（新着の一括既読化） ---

def test_read_all_marks_entries_and_keeps_saved(app_client, tmp_path):
  db = StartsDB(db_path=str(tmp_path / "api.db"))
  db.register_feed("a", "https://example.com/a", "example.com", "ソース")
  db.register_feed("b", "https://example.com/b", "example.com", "ソース")
  db.register_feed("既読", "https://example.com/c", "example.com", "ソース")
  db.delete_entry(StartsDB._hash("https://example.com/c"))
  db.add_saved_link("保存", "https://example.com/d", "example.com", "example.com")
  db.conn.close()

  resp = app_client.post("/api/entries/read-all")
  assert resp.status_code == 200
  assert resp.json() == {"updated": 2}

  assert app_client.get("/api/entries").json() == []
  saved = app_client.get("/api/saved").json()
  assert [s["link"] for s in saved] == ["https://example.com/d"]


def test_read_all_no_targets_returns_zero(app_client):
  resp = app_client.post("/api/entries/read-all")
  assert resp.status_code == 200
  assert resp.json() == {"updated": 0}
