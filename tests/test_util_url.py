"""util/url.py::get_domain のテスト（inline assert を pytest に移植）。"""

from util.url import get_domain


def test_get_domain_https_with_path():
  assert get_domain("https://google.com/path") == "google.com"


def test_get_domain_with_port():
  assert get_domain("http://localhost:8080") == "localhost:8080"


def test_get_domain_cojp():
  assert get_domain("http://yahoo.co.jp") == "yahoo.co.jp"


def test_get_domain_invalid_returns_empty():
  # スキームが無いと netloc が空になる（api.py の 400 バリデーションが依存する挙動）
  assert get_domain("not a url") == ""


def test_get_domain_path_only_returns_empty():
  # パスのみ（スキーム無し）も netloc は空
  assert get_domain("foo/bar") == ""


def test_get_domain_scheme_relative():
  # スキームレス authority（//host/path）は netloc が取れる
  assert get_domain("//example.com/x") == "example.com"
