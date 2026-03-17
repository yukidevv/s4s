# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 実行方法

```bash
# 仮想環境のセットアップ
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Web UI 起動 (http://localhost:8000)
uvicorn api:app --reload --host 0.0.0.0

python main.py run  # フィードを取得して新着を記録

# Dockerで実行
docker compose up -d --build  # Web UI が :8000 で起動
docker compose exec app python main.py run
```

## アーキテクチャ

RSSフィードを取得し、未読エントリをSQLiteに記録してWeb UIで閲覧するツール。

**データフロー:**
1. `main.py run` — `sources` テーブルのフィードURLをfeedparserで取得
2. エントリのURLをMD5ハッシュ化して重複チェック（`StartsDB.fetch_all()`）
3. 未取得エントリを `StartsDB.register_feed()` でDBに保存
4. Web UI (`http://localhost:8000`) で新着一覧を閲覧・既読処理

**モジュール構成:**
- `api.py` — FastAPI。REST APIの提供と `static/` の配信
- `db/db.py` — `StartsDB` クラス。SQLite接続・テーブル初期化・CRUD操作
- `util/feed.py` — `discover_feed(url)` でフィードURLとサイト名を自動検出
- `util/url.py` — `get_domain(url)` でURLからドメイン名を抽出
- `static/index.html` — 新着一覧・後で読む・フィード管理のSPA
- `data/` — SQLiteのDBファイル置き場（`stars.db`）、gitignore済み

**DBスキーマ:**
```sql
-- 取得済みエントリの記録
CREATE TABLE feeds (
  url_2_hash  TEXT PRIMARY KEY,  -- エントリURLのMD5ハッシュ
  title       TEXT,
  link        TEXT,
  domain      TEXT,
  source_name TEXT,
  read        INTEGER NOT NULL DEFAULT 0,  -- 1=既読
  saved       INTEGER NOT NULL DEFAULT 0,  -- 1=後で読む
  created_at  TIMESTAMP DEFAULT (datetime('now', '+9 hours'))  -- JST
)

-- 購読するRSSフィードの管理
CREATE TABLE sources (
  url        TEXT PRIMARY KEY,
  domain     TEXT,
  name       TEXT,
  created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
)
```

## サーバへのデプロイ (systemd)

```bash
# アプリを /srv/www/htdocs/starts に配置し仮想環境を作成
git clone <repo> /srv/www/htdocs/starts
cd /srv/www/htdocs/starts
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# systemd ユニットをインストール
sudo cp systemd/starts.service /etc/systemd/system/
sudo cp systemd/starts.timer  /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now starts.timer

# 確認
sudo systemctl status starts.timer
sudo systemctl list-timers starts.timer
journalctl -u starts.service
```

## 環境

- Python 3.14（Docker: `python:3.14.2-slim-trixie`）、ローカル仮想環境は `.venv/`
- SQLiteのDBファイルは `data/stars.db`
- `STARTS_TOKEN` 環境変数でトークン認証を設定（未設定時は全リクエストを拒否）
  ```bash
  export STARTS_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
  docker compose up -d --build
  # アクセス: http://localhost:8000/?token=<token>
  ```
