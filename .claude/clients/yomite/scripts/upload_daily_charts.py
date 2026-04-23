#!/usr/bin/env python3
"""
ヨミテデイリー 6商品チャート バッチアップロード
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【使い方】
1) thread_map を /tmp/yomite_thread_map.json に書く:
   {
     "date": "2026-04-22",
     "channel": "C0AMYLU2W5D",
     "targets": [
       {"slug": "00summary",   "thread_ts": "1776819130.866869", "title": "..."},
       {"slug": "proust",      "thread_ts": "1776819160.562279", "title": "..."},
       ...
     ]
   }

2) スクリプト実行:
   python3 upload_daily_charts.py [--map /tmp/yomite_thread_map.json]

【allowlist エントリ】
  Bash(python3 /Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite/scripts/*.py *)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

CHARTS_DIR = Path("/Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite/charts")
DEFAULT_MAP = "/tmp/yomite_thread_map.json"


def get_token():
    """~/.zshrc から SLACK_BOT_TOKEN を読む（interactive zshをロードせずに）"""
    zshrc = os.path.expanduser("~/.zshrc")
    with open(zshrc) as f:
        for line in f:
            line = line.strip()
            if line.startswith("export SLACK_BOT_TOKEN="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                return val
    return ""


def api(token, method, endpoint, *, params=None, data=None, headers=None):
    url = f"https://slack.com/api/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    hdr = {"Authorization": f"Bearer {token}"}
    if headers:
        hdr.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdr, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def upload_one(token, channel, slug, thread_ts, title, date):
    path = CHARTS_DIR / f"{date}_voyage_{slug}.png"
    if not path.exists():
        return {"ok": False, "error": f"file_not_found: {path}"}
    size = path.stat().st_size

    # Step 1: get upload URL
    d = api(token, "GET", "files.getUploadURLExternal",
            params={"filename": path.name, "length": size})
    if not d.get("ok"):
        return d
    upload_url = d["upload_url"]
    file_id = d["file_id"]

    # Step 2: upload file body
    with open(path, "rb") as f:
        boundary = "----UploadBoundaryXY"
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f'Content-Type: image/png\r\n\r\n'
        ).encode() + f.read() + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            upload_url, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        urllib.request.urlopen(req, timeout=60)

    # Step 3: complete and attach to thread
    payload = {
        "files": [{"id": file_id, "title": title}],
        "channel_id": channel,
        "thread_ts": thread_ts,
    }
    return api(token, "POST", "files.completeUploadExternal",
               data=json.dumps(payload).encode(),
               headers={"Content-Type": "application/json"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default=DEFAULT_MAP,
                        help="thread_mapのJSONファイルパス")
    parser.add_argument("--date", default=None,
                        help="対象日 (YYYY-MM-DD)。未指定ならmap側のdate or最新を使う")
    args = parser.parse_args()

    token = get_token()
    if not token:
        print("❌ SLACK_BOT_TOKEN not found in ~/.zshrc", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.map):
        print(f"❌ thread_map not found: {args.map}", file=sys.stderr)
        sys.exit(1)

    with open(args.map) as f:
        config = json.load(f)

    date = args.date or config.get("date")
    if not date:
        # Auto-detect from latest chart
        files = sorted(CHARTS_DIR.glob("*_voyage_00summary.png"))
        if not files:
            print("❌ date未指定、チャート画像なし", file=sys.stderr)
            sys.exit(1)
        date = files[-1].name.split("_voyage_")[0]

    channel = config.get("channel", "C0AMYLU2W5D")
    targets = config.get("targets", [])

    if not targets:
        print("❌ targetsが空", file=sys.stderr)
        sys.exit(1)

    print(f"📅 対象日: {date}")
    print(f"📣 channel: {channel}")
    print(f"📎 アップロード対象: {len(targets)}枚\n")

    ok_count = 0
    for t in targets:
        slug = t["slug"]
        thread_ts = t["thread_ts"]
        title = t.get("title", f"ヨミテデイリー {slug}")
        r = upload_one(token, channel, slug, thread_ts, title, date)
        if r.get("ok"):
            print(f"  ✅ {slug:<12} → thread {thread_ts}")
            ok_count += 1
        else:
            print(f"  ❌ {slug:<12} → {r.get('error', r)}")

    print(f"\n🏁 {ok_count}/{len(targets)} 成功")
    if ok_count < len(targets):
        sys.exit(1)


if __name__ == "__main__":
    main()
