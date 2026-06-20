"""util/feed.py::fetch_page_title のテスト（requests を monkeypatch、実ネットワーク不使用）。"""

import pytest

import util.feed as feed
from util.feed import fetch_page_title


class _FakeResp:
  def __init__(self, text):
    self.text = text

  def raise_for_status(self):
    pass


def test_fetch_page_title_success(monkeypatch):
  """<title> が取得できればその文字列を返す。"""
  def fake_get(url, **kwargs):
    return _FakeResp("<html><head><title>  ページ名  </title></head></html>")
  monkeypatch.setattr(feed.requests, "get", fake_get)
  assert fetch_page_title("https://example.com/a") == "ページ名"


def test_fetch_page_title_empty_falls_back_to_url(monkeypatch):
  """<title> が空文字ならフォールバックで URL を返す。"""
  def fake_get(url, **kwargs):
    return _FakeResp("<html><head><title>   </title></head></html>")
  monkeypatch.setattr(feed.requests, "get", fake_get)
  assert fetch_page_title("https://example.com/a") == "https://example.com/a"


def test_fetch_page_title_no_title_falls_back_to_url(monkeypatch):
  """<title> 要素自体が無ければフォールバックで URL を返す。"""
  def fake_get(url, **kwargs):
    return _FakeResp("<html><head></head><body>x</body></html>")
  monkeypatch.setattr(feed.requests, "get", fake_get)
  assert fetch_page_title("https://example.com/a") == "https://example.com/a"


def test_fetch_page_title_exception_falls_back_to_url(monkeypatch):
  """取得時に例外が出てもフォールバックで URL を返す（例外は送出しない）。"""
  def fake_get(url, **kwargs):
    raise RuntimeError("network down")
  monkeypatch.setattr(feed.requests, "get", fake_get)
  assert fetch_page_title("https://example.com/a") == "https://example.com/a"
