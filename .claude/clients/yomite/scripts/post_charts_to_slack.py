#!/usr/bin/env python3
"""
ヨミテデイリーニュース 画像自動投稿スクリプト
.claude/clients/yomite/charts/{今日}_voyage_{slug}.png を Slack にアップロード。

【使い方】
  # 環境変数 SLACK_BOT_TOKEN が必要（~/.zshrc に設定済み）
  python3 post_charts_to_slack.py                    # チャンネルに新規投稿
  python3 post_charts_to_slack.py --thread_ts <TS>   # 既存スレッドに添付

【仕組み】
  Slack Files API (files.upload_v2) を使用:
    1) files.getUploadURLExternal でアップロードURL取得
    2) そのURLにPOSTでファイル実体送信
    3) files.completeUploadExternal でSlackに登録
  チャンネルに直接添付したい場合は channels 引数または thread_ts を渡す。

【備考】
  - 必要権限: chat:write, files:write （Bot Token Scopes）
  - Bot を対象チャンネルに /invite で招待してから実行すること
"""

import os
import sys
import json
import glob
from datetime import datetime
from pathlib import Path
import argparse

import requests

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
CHANNEL_ID = "C0AMYLU2W5D"  # #yomite_ai-agents

CHARTS_DIR = Path("/Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite/charts")

# 6画像の表示順（投稿する順、先頭にサマリ）
PRODUCT_ORDER = [
    ("00summary", "📊 ヨミテ デイリー総覧（5商品の今の立ち位置）"),
    ("onmyskin", "🧖‍♀️ on:myskin ハーブピーリング"),
    ("proust", "💧 プルーストクリーム2"),
    ("gungun", "🌱 伸長ぐんぐん習慣"),
    ("rkl", "🦵 RKL"),
    ("apobusterf", "🧴 アポバスターF"),
]


def die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def slack_api(method, endpoint, **kwargs):
    """Slack API呼び出しラッパー。エラー時は詳細を出す。"""
    url = f"https://slack.com/api/{endpoint}"
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {SLACK_TOKEN}"
    r = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    try:
        data = r.json()
    except Exception:
        die(f"{endpoint} returned non-JSON: {r.text[:300]}")
    if not data.get("ok"):
        die(f"{endpoint} failed: {data.get('error')} / {data}")
    return data


def upload_file(path: Path, title: str):
    """
    files.upload_v2 の3段階フロー
    1) getUploadURLExternal で upload_url + file_id 取得
    2) upload_url にファイル実体POST
    3) completeUploadExternal で確定（channelにまだ添付しない）
    """
    size = path.stat().st_size
    # Step 1: upload URL 取得
    d = slack_api(
        "GET",
        "files.getUploadURLExternal",
        params={
            "filename": path.name,
            "length": size,
        },
    )
    upload_url = d["upload_url"]
    file_id = d["file_id"]

    # Step 2: ファイル実体POST (Bearer不要)
    with open(path, "rb") as f:
        r = requests.post(upload_url, files={"file": (path.name, f)}, timeout=60)
    if r.status_code != 200:
        die(f"upload POST failed: {r.status_code} {r.text[:200]}")

    return {"id": file_id, "title": title}


def complete_and_post(files, channel_id, initial_comment, thread_ts=None):
    """
    files.completeUploadExternal でSlackに登録＆指定チャンネルに投稿。
    files: [{"id": "F...", "title": "..."}]
    """
    payload = {
        "files": [{"id": f["id"], "title": f["title"]} for f in files],
        "channel_id": channel_id,
        "initial_comment": initial_comment,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    d = slack_api(
        "POST",
        "files.completeUploadExternal",
        headers={"Content-Type": "application/json; charset=utf-8"},
        data=json.dumps(payload),
    )
    return d


def main():
    if not SLACK_TOKEN:
        die("SLACK_BOT_TOKEN が設定されてない。~/.zshrc を確認して source ~/.zshrc しろ")

    parser = argparse.ArgumentParser()
    parser.add_argument("--thread_ts", help="投稿するスレッドの親メッセージts。無ければ新規投稿", default=None)
    parser.add_argument("--date", help="対象日 (YYYY-MM-DD)。デフォルトは最新", default=None)
    parser.add_argument("--channel", help="Slack channel ID", default=CHANNEL_ID)
    parser.add_argument("--dry_run", action="store_true", help="ファイル検出だけ行う")
    parser.add_argument("--single", help="特定slugだけアップ（テスト用）", default=None)
    args = parser.parse_args()

    # 対象日を決める
    if args.date:
        target_date = args.date
    else:
        files = sorted(CHARTS_DIR.glob("*_voyage_*.png"))
        if not files:
            die("charts/ に画像が無い。先に generate_charts.py を実行")
        # 最新ファイルのプレフィクス
        target_date = files[-1].name.split("_voyage_")[0]

    print(f"📅 対象日: {target_date}")

    # 画像パス解決
    targets = []
    for slug, title in PRODUCT_ORDER:
        if args.single and args.single != slug:
            continue
        path = CHARTS_DIR / f"{target_date}_voyage_{slug}.png"
        if not path.exists():
            print(f"⚠️  {path} 無し、スキップ")
            continue
        targets.append((path, title))

    if not targets:
        die("アップロード対象画像なし")

    print(f"📎 アップロード対象: {len(targets)} 枚")
    for p, t in targets:
        print(f"   - {p.name}  ({t})")

    if args.dry_run:
        print("🏁 dry_run 終了")
        return

    # アップロード
    print("\n🚀 Slackにアップロード開始...")
    uploaded = []
    for path, title in targets:
        r = upload_file(path, title)
        uploaded.append(r)
        print(f"   ✅ {path.name} → file_id={r['id']}")

    # チャンネル or スレッドに投稿
    comment = f"📊 ヨミテデイリー航路図 {target_date} ({len(uploaded)}枚)"
    print(f"\n📣 channel={args.channel} thread_ts={args.thread_ts}")
    d = complete_and_post(uploaded, args.channel, comment, args.thread_ts)
    print(f"✅ 投稿完了！")
    print(json.dumps(d, ensure_ascii=False, indent=2)[:500])


if __name__ == "__main__":
    main()
