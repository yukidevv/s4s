#!/usr/bin/env python3

import feedparser
import hashlib
import argparse
import json
import os
from db.db import StartsDB


def send_push_notifications(db, new_count):
  vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY", "")
  vapid_email = os.environ.get("VAPID_EMAIL", "")
  if not vapid_private_key or not vapid_email:
    return

  try:
    from pywebpush import webpush, WebPushException
  except ImportError:
    return

  subscriptions = db.get_push_subscriptions()
  if not subscriptions:
    return

  body = f"新着 {new_count} 件" if new_count > 0 else "新着エントリはありませんでした"
  payload = json.dumps({"title": "starts", "body": body})

  for sub in subscriptions:
    try:
      webpush(
        subscription_info={
          "endpoint": sub["endpoint"],
          "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
        },
        data=payload,
        vapid_private_key=vapid_private_key,
        vapid_claims={"sub": f"mailto:{vapid_email}"},
      )
    except WebPushException as e:
      status = e.response.status_code if e.response is not None else None
      if status in (404, 410) or "410" in str(e) or "404" in str(e):
        db.delete_push_subscription(sub["endpoint"])
      else:
        print(f"push送信失敗: {e}")


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
  send_push_notifications(db, len(new_entries))


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
