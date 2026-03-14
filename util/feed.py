import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def discover_feed_url(url: str) -> str:
  """
  URLがフィードであればそのまま返す。
  HTMLページであれば <link rel="alternate"> からフィードURLを探して返す。
  見つからなければ ValueError を送出する。
  """
  d = feedparser.parse(url)
  if d.entries or d.feed.get("title"):
    return url

  try:
    resp = requests.get(url, timeout=10, headers={"User-Agent": "starts/1.0"})
    resp.raise_for_status()
  except requests.RequestException as e:
    raise ValueError(f"URLへのアクセスに失敗しました: {e}")

  soup = BeautifulSoup(resp.text, "html.parser")
  for link in soup.find_all("link", rel="alternate"):
    t = link.get("type", "")
    if t in ("application/rss+xml", "application/atom+xml"):
      href = link.get("href", "")
      if href:
        return urljoin(url, href)

  raise ValueError("フィードが見つかりませんでした")
