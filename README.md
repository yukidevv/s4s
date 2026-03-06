# starts(Strategic Tracking & RSS System)
自分専用RSSリーダー、欲しい情報を欲しい間隔で

# ツール
- python3(3.14.2)
- sqlite

# 依存関係
~~~bash
pip freeze > requirements.txt
pip install -r requirements.txt
~~~

# DB
~~~bash
docker compose up -d
docker compose exec app sqlite3 data/stars.db
sqlite> .headers on # お好み
sqlite> .mode column # お好み
sqlite> SELECT * FROM feeds;
sqlite> .quit
~~~