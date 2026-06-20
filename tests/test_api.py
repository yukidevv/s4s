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
