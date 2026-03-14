#!/usr/bin/env python3

import feedparser
import hashlib
import argparse
from db.db import StartsDB


def cmd_run(db, args):
  sources = db.get_sources()
  if not sources:
    print("フィードが登録されていません。Web UIからフィードを追加してください。")
    return

  existing_hashes = db.fetch_all()
  new_entries = []

  for source in sources:
    d = feedparser.parse(source["url"])
    for entry in d.entries:
      content_hash = hashlib.md5(entry.link.encode()).hexdigest()
      if content_hash in existing_hashes:
        break
      db.register_feed(entry.title, entry.link, source["domain"], source["name"])
      existing_hashes.add(content_hash)
      new_entries.append({"title": entry.title, "link": entry.link, "domain": source["domain"]})

  print(f"{len(new_entries)} 件の新着エントリを取得しました")


def main():
  db = StartsDB()

  parser = argparse.ArgumentParser(description="starts - RSSリーダー")
  subparsers = parser.add_subparsers(dest="command")
  subparsers.add_parser("run", help="フィードを取得して新着を記録")

  args = parser.parse_args()

  match args.command:
    case "run": cmd_run(db, args)
    case _:     parser.print_help()


if __name__ == "__main__":
  main()
