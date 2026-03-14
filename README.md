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

## Web UI

`http://localhost:8000` にアクセスすると以下が利用できます。

- **新着タブ** — 取得済みの未読エントリ一覧。既読ボタンで消化
- **フィード管理タブ** — フィードの登録・削除

RSSフィードのURLだけでなく、サイトのトップURLを入力してもフィードを自動検出します。サイト名も自動で取得します。

## CLI

```bash
python main.py add <URL>     # フィードを追加
python main.py list          # 登録済みフィード一覧
python main.py delete <URL>  # フィードを削除
python main.py run           # 新着を取得してDBに記録
```

## サーバーへのデプロイ (systemd)

```bash
git clone <repo> /opt/starts
cd /opt/starts
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
