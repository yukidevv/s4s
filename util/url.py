from urllib.parse import urlparse

def get_domain(url) -> str:
  parsed_url = urlparse(url)
  return parsed_url.netloc

if __name__ == "__main__":
    assert get_domain("https://google.com/path") == "google.com"
    assert get_domain("http://localhost:8080") == "localhost:8080"
    assert get_domain("http://yahoo.co.jp") == "yahoo.co.jp"
    print("passed!")