#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from util.url import get_domain
from util.feed import discover_feed_url
from db.db import StartsDB

app = FastAPI()

class SourceRequest(BaseModel):
  url: str


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
    feed_url = discover_feed_url(body.url)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  domain = get_domain(feed_url)
  db.add_source(feed_url, domain)
  return {"url": feed_url, "domain": domain}


@app.delete("/api/sources")
def delete_source(body: SourceRequest):
  db = StartsDB()
  if not db.delete_source(body.url):
    raise HTTPException(status_code=404, detail="見つかりません")
  return {"deleted": body.url}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
