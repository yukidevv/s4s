#!/usr/bin/env python3

import feedparser
import json

#対象サイトをリストに追加する
RSS_URL = ["https://yukidev.net/blog/index.xml"]

def main() -> int:
  d = feedparser.parse(RSS_URL[0])
  
  for entry in d.entries[:3]:
      print(f"タイトル: {entry.title}")
      print(f"リンク  : {entry.link}")
      print(f"公開日  : {entry.published}")
      print("-" * 30)

if __name__ == "__main__":
  main()