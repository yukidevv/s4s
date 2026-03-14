# starts (Strategic Tracking & RSS System)

自分専用RSSリーダー。登録したフィードの新着記事をDiscordに通知します。

## 技術スタック

- Python 3.14
- SQLite
- FastAPI / uvicorn
- feedparser / BeautifulSoup4

## セットアップ

### Docker（推奨）

`.env` をプロジェクトルートに作成：

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy
```

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

`http://localhost:8000` にアクセスするとフィードの登録・削除ができます。
RSSフィードのURLだけでなく、サイトのトップURLを入力してもフィードを自動検出します。

## CLI

```bash
python main.py add <URL>     # フィードを追加
python main.py list          # 登録済みフィード一覧
python main.py delete <URL>  # フィードを削除
python main.py run           # 新着を取得してDiscordに通知
```

## Discord通知

1. Discordで通知先チャンネルを右クリック →「チャンネルの編集」
2. 「連携サービス」→「ウェブフック」→「新しいウェブフック」
3. 「ウェブフックURLをコピー」して `.env` に設定

通知は `python main.py run` 実行時に新着があった場合のみ送信されます。

## サーバーへのデプロイ (systemd)

```bash
git clone <repo> /opt/starts
cd /opt/starts
python -m venv .venv
.venv/bin/pip install -r requirements.txt

sudo mkdir /etc/starts
sudo cp systemd/env.example /etc/starts/env
sudo vim /etc/starts/env  # DISCORD_WEBHOOK_URL を設定

sudo cp systemd/starts.service /etc/systemd/system/
sudo cp systemd/starts.timer  /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now starts.timer
```

07:00 / 12:00 / 17:00 (JST) に自動で新着取得・通知します。

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
