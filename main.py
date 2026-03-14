#!/usr/bin/env python3

import feedparser
import hashlib
import argparse
from util.url import get_domain
from util.feed import discover_feed
from db.db import StartsDB


def cmd_add(db, args):
  try:
    feed = discover_feed(args.url)
  except ValueError as e:
    print(f"エラー: {e}")
    return
  domain = get_domain(feed["url"])
  name = feed["name"] or domain
  db.add_source(feed["url"], domain, name)
  print(f"追加しました: {feed['url']} ({name})")


def cmd_list(db, args):
  sources = db.get_sources()
  if not sources:
    print("登録されているフィードはありません")
    return
  for s in sources:
    print(f"{s['name']}\t{s['url']}\t(登録日: {s['created_at']})")


def cmd_delete(db, args):
  if db.delete_source(args.url):
    print(f"削除しました: {args.url}")
  else:
    print(f"見つかりません: {args.url}")


def cmd_run(db, args):
  sources = db.get_sources()
  if not sources:
    print("フィードが登録されていません。`python main.py add <URL>` で追加してください。")
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

  p_add = subparsers.add_parser("add", help="フィードを追加")
  p_add.add_argument("url", help="RSS フィードのURL")

  subparsers.add_parser("list", help="登録済みフィード一覧")

  p_del = subparsers.add_parser("delete", help="フィードを削除")
  p_del.add_argument("url", help="削除するフィードのURL")

  subparsers.add_parser("run", help="フィードを取得して新着を記録")

  args = parser.parse_args()

  match args.command:
    case "add":    cmd_add(db, args)
    case "list":   cmd_list(db, args)
    case "delete": cmd_delete(db, args)
    case "run":    cmd_run(db, args)
    case _:        parser.print_help()


if __name__ == "__main__":
  main()
