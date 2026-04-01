#!/usr/bin/env python3
"""
Fish Audio 日本語ボイス一覧取得スクリプト
→ voice_catalog.json の reference_id を埋めるために使う

使い方:
  python3 video-ai/fetch_fish_voices.py

出力: 日本語ボイス一覧（ID・名前・説明）をターミナルに表示
"""
import os
import json
import subprocess
import requests

def get_fish_key() -> str:
    result = subprocess.run(
        ["zsh", "-i", "-c", "echo $FISH_AUDIO_API_KEY"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def fetch_japanese_voices(fish_key: str, page_size: int = 20) -> list:
    """Fish Audio API から日本語ボイスを検索して返す"""
    try:
        resp = requests.get(
            "https://api.fish.audio/model",
            headers={"Authorization": f"Bearer {fish_key}"},
            params={
                "language": "ja",
                "page_size": page_size,
                "sort_by": "score",  # 人気順
            },
            timeout=15
        )
        if resp.status_code != 200:
            print(f"❌ Fish Audio API エラー: {resp.status_code}")
            print(resp.text[:200])
            return []
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        print(f"❌ 接続失敗: {e}")
        return []

def main():
    fish_key = get_fish_key()
    if not fish_key:
        print("❌ FISH_AUDIO_API_KEY が設定されていません（~/.zshrc を確認）")
        return

    print("🔍 Fish Audio 日本語ボイスを検索中...\n")
    voices = fetch_japanese_voices(fish_key)

    if not voices:
        print("ボイスが見つかりませんでした。")
        return

    print(f"{'ID':<36}  {'名前':<20}  {'説明'}")
    print("─" * 90)
    for v in voices:
        vid = v.get("_id", "")
        name = v.get("title", "")[:20]
        desc = v.get("description", "")[:40]
        tags = ", ".join(v.get("tags", []))
        print(f"{vid}  {name:<20}  {desc}")
        if tags:
            print(f"{'':36}  {'':20}  タグ: {tags}")

    print(f"\n合計 {len(voices)} 件")
    print("\n📝 voice_catalog.json の reference_id を上記のIDで更新してください。")
    print("   cat video-ai/voice_catalog.json でカタログを確認できます。")

if __name__ == "__main__":
    main()
