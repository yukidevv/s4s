#!/usr/bin/env python3

import os
import hashlib
import feedparser
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from util.url import get_domain
from util.feed import discover_feed
from db.db import StartsDB

app = FastAPI()

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
  expected = os.environ.get("STARTS_TOKEN", "")
  if expected and request.url.path not in ("/sw.js",) and request.query_params.get("token") != expected:
    return Response("Forbidden", status_code=403)
  return await call_next(request)

class SourceRequest(BaseModel):
  url: str

class PushSubscriptionRequest(BaseModel):
  endpoint: str
  p256dh: str
  auth: str


@app.get("/api/entries")
def list_entries():
  db = StartsDB()
  return db.fetch_entries()


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: str):
  db = StartsDB()
  if not db.delete_entry(entry_id):
    raise HTTPException(status_code=404, detail="見つかりません")
  return {"deleted": entry_id}


@app.get("/api/sources")
def list_sources():
  db = StartsDB()
  return db.get_sources()


@app.post("/api/sources", status_code=201)
def add_source(body: SourceRequest):
  db = StartsDB()
  if not get_domain(body.url):
    raise HTTPException(status_code=400, detail="無効なURLです")
  try:
    feed = discover_feed(body.url)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  domain = get_domain(feed["url"])
  name = feed["name"] or domain
  db.add_source(feed["url"], domain, name)

  existing_hashes = db.fetch_all()
  d = feedparser.parse(feed["url"])
  for entry in d.entries:
    content_hash = hashlib.md5(entry.link.encode()).hexdigest()
    if content_hash in existing_hashes:
      break
    db.register_feed(entry.title, entry.link, domain, name)
    existing_hashes.add(content_hash)

  return {"url": feed["url"], "domain": domain, "name": name}


@app.delete("/api/sources")
def delete_source(body: SourceRequest):
  db = StartsDB()
  if not db.delete_source(body.url):
    raise HTTPException(status_code=404, detail="見つかりません")
  return {"deleted": body.url}


@app.get("/sw.js")
def service_worker():
  return FileResponse("static/sw.js", media_type="text/javascript")


@app.get("/api/vapid-public-key")
def get_vapid_public_key():
  key = os.environ.get("VAPID_PUBLIC_KEY", "")
  if not key:
    raise HTTPException(status_code=503, detail="VAPID keys not configured")
  return {"publicKey": key}


@app.post("/api/push/subscribe", status_code=201)
def subscribe_push(body: PushSubscriptionRequest):
  db = StartsDB()
  db.add_push_subscription(body.endpoint, body.p256dh, body.auth)
  return {"subscribed": True}


@app.delete("/api/push/subscribe")
def unsubscribe_push(body: PushSubscriptionRequest):
  db = StartsDB()
  db.delete_push_subscription(body.endpoint)
  return {"unsubscribed": True}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
