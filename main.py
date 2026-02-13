#!/usr/bin/env python3

import feedparser
import json
import sqlite3
from db.db import StartsDB

# sample
RSS_URL = [
  "https://yukidev.net/blog/index.xml",
  "https://zenn.dev/feed"
]

def main():
  db = StartsDB()
  for site in RSS_URL:
    d = feedparser.parse(site)
    i = 0
    for entry in d.entries:
      db.register_feed(entry.title, entry.link)
      print(f"タイトル: {entry.title}")
      print(f"リンク  : {entry.link}")
      print(f"公開日  : {entry.published}")
      print("-" * 30)

if __name__ == "__main__":
  main()
