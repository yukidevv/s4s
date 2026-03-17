# starts (Strategic Tracking & RSS System)

自分専用RSSリーダー。登録したフィードの新着記事をWeb UIで閲覧できます。

## 技術スタック

- Python 3.14
- SQLite
- FastAPI / uvicorn
- feedparser / BeautifulSoup4

## セットアップ

### Docker（推奨）

```bash
docker compose up -d --build
```

Web UI: http://localhost:8000

### ローカル

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --host 0.0.0.0
```

## 認証

クエリパラメータにトークンを付与することでアクセスを制限できます。

`docker-compose.override.yml` をプロジェクトルートに作成します（gitignore済み）：

```yaml
services:
  app:
    environment:
      - STARTS_TOKEN=<your-token>
```

トークンの生成：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`docker compose up` 時に自動で読み込まれます。

アクセスURL：
```
https://example.com/starts/?token=<token>
```

このURLをスマホにブックマークしてください。トークンなしのアクセスは403になります。

## Web UI

`http://localhost:8000` にアクセスすると以下が利用できます。

- **新着タブ** — 取得済みの未読エントリ一覧。フィード（ソース）ごとにグルーピングして表示し、新着が各グループの先頭に並ぶ。既読ボタンで消化、後で読むボタンで保存
- **後で読むタブ** — 保存した記事の一覧。削除ボタンで消化
- **フィード管理タブ** — フィードの登録・削除

RSSフィードのURLだけでなく、サイトのトップURLを入力してもフィードを自動検出します。サイト名も自動で取得します。

## CLI

```bash
python main.py run  # 新着を取得してDBに記録
```

フィードの追加・削除は Web UI から行います。

## サーバーへのデプロイ (systemd)

```bash
git clone <repo> /srv/www/htdocs/starts
cd /srv/www/htdocs/starts
python -m venv .venv
.venv/bin/pip install -r requirements.txt

sudo cp systemd/starts.service /etc/systemd/system/
sudo cp systemd/starts.timer  /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now starts.timer
```

07:00 / 12:00 / 17:00 (JST) に自動で新着取得します。

```bash
sudo systemctl list-timers starts.timer  # 次回実行時刻の確認
journalctl -u starts.service             # ログ確認
```

## DB

```bash
docker compose exec app sqlite3 data/stars.db
sqlite> .headers on
sqlite> .mode column
sqlite> SELECT * FROM feeds;    -- 取得済みエントリ
sqlite> SELECT * FROM sources;  -- 登録フィード一覧
sqlite> .quit
```
