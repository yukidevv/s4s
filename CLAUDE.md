# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 実行方法

```bash
# 仮想環境のセットアップ
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Web UI 起動 (http://localhost:8000)
uvicorn api:app --reload

# フィード管理 (CLI)
python main.py add <URL>     # フィードを追加
python main.py list          # 登録済みフィード一覧
python main.py delete <URL>  # フィードを削除
python main.py run           # フィードを取得して新着を記録

# Dockerで実行
docker compose up -d         # Web UI が :8000 で起動
docker compose exec app python main.py run
```

## アーキテクチャ

RSSフィードを取得し、未読エントリをSQLiteに記録するCLIツール。

**データフロー:**
1. `main.py` — RSS_URLリストからfeedparserでフィード取得
2. エントリのURLをMD5ハッシュ化して重複チェック（`StartsDB.fetch_all()`）
3. 未取得エントリを`StartsDB.register_feed()`でDBに保存
4. 通知処理（未実装・TODO）

**モジュール構成:**
- `db/db.py` — `StartsDB`クラス。SQLite接続・テーブル初期化・CRUD操作
- `util/url.py` — `get_domain(url)` でURLからドメイン名を抽出
- `data/` — SQLiteのDBファイル置き場（`stars.db`）、gitignore済み

**DBスキーマ:**
```sql
-- 取得済みエントリの記録（重複チェック用）
CREATE TABLE feeds (
  url_2_hash TEXT PRIMARY KEY,  -- エントリURLのMD5ハッシュ
  domain     TEXT,
  created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))  -- JST
)

-- 購読するRSSフィードの管理
CREATE TABLE sources (
  url        TEXT PRIMARY KEY,
  domain     TEXT,
  created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
)
```

## サーバへのデプロイ (systemd)

```bash
# アプリを /opt/starts に配置し仮想環境を作成
git clone <repo> /opt/starts
cd /opt/starts
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# 環境変数ファイルを設置
sudo mkdir /etc/starts
sudo cp systemd/env.example /etc/starts/env
sudo vim /etc/starts/env  # DISCORD_WEBHOOK_URL を設定

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
- SQLiteのDBファイルは `data/stars.db`（環境変数 `DATABASE_URL` で上書き可）
