import requests

DISCORD_MAX_LENGTH = 2000

def notify(webhook_url: str, entries: list[dict]):
  if not entries:
    return

  chunks = []
  current = []
  current_len = 0

  for e in entries:
    line = f"**[{e['domain']}]** [{e['title']}]({e['link']})"
    # +1 は改行分
    if current and current_len + len(line) + 1 > DISCORD_MAX_LENGTH:
      chunks.append("\n".join(current))
      current = []
      current_len = 0
    current.append(line)
    current_len += len(line) + 1

  if current:
    chunks.append("\n".join(current))

  for chunk in chunks:
    resp = requests.post(webhook_url, json={"content": chunk})
    resp.raise_for_status()
