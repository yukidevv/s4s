#!/usr/bin/env python3

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from util.url import get_domain
from util.feed import discover_feed
from db.db import StartsDB

app = FastAPI()

def verify_token(token: str = Query(default="")):
  expected = os.environ.get("STARTS_TOKEN", "")
  if not expected or token != expected:
    raise HTTPException(status_code=403, detail="Forbidden")

class SourceRequest(BaseModel):
  url: str


@app.get("/api/entries")
def list_entries(token: str = Query(default="")):
  verify_token(token)
  db = StartsDB()
  return db.fetch_entries()


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: str, token: str = Query(default="")):
  verify_token(token)
  db = StartsDB()
  if not db.delete_entry(entry_id):
    raise HTTPException(status_code=404, detail="見つかりません")
  return {"deleted": entry_id}


@app.get("/api/sources")
def list_sources(token: str = Query(default="")):
  verify_token(token)
  db = StartsDB()
  return db.get_sources()


@app.post("/api/sources", status_code=201)
def add_source(body: SourceRequest, token: str = Query(default="")):
  verify_token(token)
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
  return {"url": feed["url"], "domain": domain, "name": name}


@app.delete("/api/sources")
def delete_source(body: SourceRequest, token: str = Query(default="")):
  verify_token(token)
  db = StartsDB()
  if not db.delete_source(body.url):
    raise HTTPException(status_code=404, detail="見つかりません")
  return {"deleted": body.url}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
