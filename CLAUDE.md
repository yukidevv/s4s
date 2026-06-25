# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 応答言語

- ユーザーへの応答は必ず日本語で行うこと。

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
- `static/index.html` — 新着一覧・後で読む・フィード管理・プッシュ通知のSPA
- `static/sw.js` — Service Worker（プッシュ通知受信・Cache API）
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
  saved       INTEGER NOT NULL DEFAULT 0,  -- 1=後で読む（ALTER TABLEで追加）
  created_at  TIMESTAMP DEFAULT (datetime('now', '+9 hours'))  -- JST
)

-- 購読するRSSフィードの管理
CREATE TABLE sources (
  url        TEXT PRIMARY KEY,
  domain     TEXT,
  name       TEXT,
  created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
)

-- Web Pushプッシュ通知の購読情報
CREATE TABLE push_subscriptions (
  endpoint   TEXT PRIMARY KEY,
  p256dh     TEXT NOT NULL,
  auth       TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT (datetime('now', '+9 hours'))
)
```

## 実装上の注意（非自明な挙動）

- **重複検知の前提**: `cmd_run()` / `add_source()` はフィードを先頭から走査し、既知ハッシュに当たった時点で `break` する。フィードのエントリが新着順に並んでいることを前提としており、既知エントリより後ろにある未取得エントリは取りこぼす。
- **ハッシュ生成は1箇所に集約**: エントリの一意キー（URLのMD5）生成は `StartsDB._hash` に集約済み。新たにハッシュ突き合わせ（`fetch_all()` との比較など）を書くときは必ず `StartsDB._hash` を使い、`hashlib.md5(...)` を直書きしないこと。方式変更時に重複検知がサイレントに壊れるのを防ぐため。
- **「削除」はソフト削除**: `DELETE /api/entries/{id}` は実際にはレコードを消さず `read=1` を立てるだけ（＝既読化）。同様に `DELETE /api/saved/{id}` は `saved=0, read=1`。物理削除されるのはフィード購読解除時のみ。
- **フィード購読解除はカスケード**: `delete_source()` は同一 `domain` の `feeds` レコードを全削除する。URL ではなく domain でひも付くため、同一ドメインの別フィードを登録していると巻き添えで消える。
- **認証**: `STARTS_TOKEN` 設定時、クエリパラメータ `?token=` が一致しないと 403。例外パスは `/sw.js` `/manifest.json` `/icon.png`（PWA がトークンなしで取得する必要があるため）。未設定時は全リクエスト拒否。
- **テスト**: `pytest` を導入済み。`pip install -r requirements-dev.txt` 後に `pytest` で実行する（テストは `tests/` 配下）。`StartsDB(db_path=...)` で一時ファイル DB を渡してテスト間を隔離する（引数なしなら従来どおり `data/stars.db`）。API テストは `STARTS_TOKEN` 未設定で認証 middleware を素通りさせ、`api.StartsDB` を一時 DB ファクトリに、`fetch_page_title` をモックに差し替える。実ネットワークは叩かない（`requests.get` を monkeypatch）。`util/url.py` の `python util/url.py` によるインライン assert も従来どおり残してある。`static/` の HTML/JS（`index.html` `sw.js` 等）は pytest の対象外なので、変更時は PR 本文に手動確認の観点を列挙する。
- **コード規約**: Python はインデント2スペース（PEP8 の4スペースではない）。既存ファイルに合わせること。

## 開発ワークフロー（developer / reviewer）

`.claude/agents/` に2つのサブエージェント定義がある。実装作業はこのフローで進める。

- `developer.md` — 実装担当。着手前に**日本語で設計方針を提示して合意**を取り、その後 **GitHub issue を作成**（`gh issue create`）し、**作業ブランチを切って**（`main` では作業しない。`feature/<概要>` または `fix/<概要>`、可能なら issue 番号を含める）実装する。**ブランチは必ず最新の `main` を起点に切る**（例: `git switch -c feature/42-tag-filter main`）。他の feature/fix ブランチの上に重ねて切らない（差分が混ざりレビュー・マージが煩雑になるため）。
- `reviewer.md` — レビュー担当。自分では修正せず、重要度・`file:line`・理由・修正方針を添えて日本語で指摘する。

標準フロー: 設計方針提示 → **合意（唯一の確認ポイント）** → issue 作成 → ブランチ作成 → 実装 → reviewer レビュー（2〜3往復で収束）→ コミット → push → **PR 作成まで自動**。

**自走の原則**: 着手前の設計方針の合意だけ確認を取り、それ以降は途中で操作確認を求めずに最後まで進める（issue 作成・コミット・push・PR 作成も含めて確認不要）。開発ループの途中で逐一ユーザーに確認しないこと。

**気づきの報告**: CLAUDE.md / メモリに残すべき規約・前提・落とし穴に気づいたら、作業を止めずに進め、**完了後にまとめて提案・報告する**（ループの途中で止めない）。

**実装はサブエージェントに委譲**: 実装作業はメインで直接編集せず developer サブエージェントに任せる。サブエージェントの編集が承認プロンプトで止まらないよう、`.claude/settings.local.json` の `permissions.allow` に `Edit(./**)` / `Write(./**)` を許可済み（プロジェクト配下にスコープ。`Edit`/`Write` の bare 許可はリポジトリ外まで書けてしまうためセキュリティ上避ける）。

## サーバへのデプロイ (systemd + Docker)

```bash
# アプリを /srv/docker/s4s に配置
git clone <repo> /srv/docker/s4s
cd /srv/docker/s4s

# Dockerコンテナを起動（Web UIが :8000 で起動）
docker compose up -d --build

# systemd ユニットをインストール（定期フィード取得）
sudo systemctl link $(pwd)/systemd/s4s.service
sudo systemctl link $(pwd)/systemd/s4s.timer
sudo systemctl daemon-reload
sudo systemctl enable --now s4s.timer

# 確認
sudo systemctl status s4s.timer
sudo systemctl list-timers s4s.timer
journalctl -u s4s.service
```

## 環境

- Python 3.14（Docker: `python:3.14.2-slim-trixie`）、ローカル仮想環境は `.venv/`
- SQLiteのDBファイルは `data/stars.db`
- 環境変数:
  - `STARTS_TOKEN` — トークン認証（未設定時は全リクエストを拒否）
  - `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_EMAIL` — Web Pushプッシュ通知用（未設定時は通知機能無効）
  ```bash
  export STARTS_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
  docker compose up -d --build
  # アクセス: http://localhost:8000/?token=<token>
  ```
- ローカル開発では `docker-compose.override.yml`（gitignore済み）で `STARTS_TOKEN` と VAPID 鍵を上書きできる。秘密情報を含むためコミットしないこと。
