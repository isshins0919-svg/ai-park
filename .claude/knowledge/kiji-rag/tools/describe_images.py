#!/usr/bin/env python3
"""
describe_images.py — kiji-rag chunks.json の画像チャンクを Gemini Vision で説明文化する。

目的:
  画像チャンクは embed_chunks.py で「ほぼ空文字」をembedしてしまう問題を解決。
  Gemini Vision (gemini-2.5-flash) で画像を1〜3文に説明 → chunks.json の
  各imageチャンクに `image_description` フィールドを追加。
  embed_chunks.py 側はこのフィールドを embed_text に含める。

使い方:
  python3 describe_images.py <path/to/chunks.json> [--blocks-raw <path>] [--force]

入力:
  chunks.json + blocks_raw.json（実画像URLを引くため）

出力:
  chunks.json の各imageチャンクに `image_description` 追加
  + image_descriptions.json: 画像URL→説明文のキャッシュ
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

# 親プロジェクトのvector_store経由でGEMINI_API_KEYをロード
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from vector_store import _load_env  # type: ignore

VISION_MODEL = "gemini-2.5-flash"
VISION_DELAY = 0.4  # seconds between API calls

PROMPT = """この画像は記事LP（ランディングページ）内のビジュアル要素です。
広告マーケター視点で、以下を1〜3文（日本語）で簡潔に記述してください。

1. 画像の主題（誰／何が写っているか）
2. 視覚的な訴求要素（ビフォーアフター比較／実績バッジ／商品写真／グラフ／ビジュアル装飾 等）
3. テキストが写り込んでいれば、そのキーワードのみ抜粋

書かないこと：
- 主観的評価（「良い」「効果的」等の意見）
- 推測（「〜と思われる」等）
- 装飾的修飾語

例: 「40代女性の手のビフォーアフター比較画像。左は乾燥して血管が浮き出た手、右はみずみずしくシワが少ない手。中央に『たった10秒』のテロップ。」"""


_client = None
def _get_client():
    global _client
    if _client is None:
        _load_env("GEMINI_API_KEY_1")
        key = os.environ.get("GEMINI_API_KEY_1")
        if not key:
            print("ERROR: GEMINI_API_KEY_1 not found", file=sys.stderr)
            sys.exit(1)
        from google import genai
        _client = genai.Client(api_key=key)
    return _client


def _mime_from_url(url):
    url_lower = url.lower().split("?")[0]
    if url_lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if url_lower.endswith(".png"):
        return "image/png"
    if url_lower.endswith(".webp"):
        return "image/webp"
    if url_lower.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"  # default


def describe_image(url, max_retries=2):
    """画像URLをVision APIで説明文化。失敗時はNone。"""
    if not url or "lazy.png" in url or url.endswith("pixel.gif") or "id.mysquadbeyond.com/pixel" in url:
        return None
    try:
        # Download image
        with httpx.Client(timeout=20, follow_redirects=True) as c:
            r = c.get(url)
            r.raise_for_status()
            img_bytes = r.content
            if len(img_bytes) < 200:
                return None  # too small, likely placeholder
            mime = r.headers.get("content-type", _mime_from_url(url)).split(";")[0].strip()
            if not mime.startswith("image/"):
                mime = _mime_from_url(url)
    except Exception as e:
        print(f"    download failed: {e}", file=sys.stderr)
        return None

    client = _get_client()
    from google.genai import types as gtypes
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.models.generate_content(
                model=VISION_MODEL,
                contents=[
                    gtypes.Part.from_bytes(data=img_bytes, mime_type=mime),
                    PROMPT,
                ],
            )
            text = (resp.text or "").strip()
            # Squash newlines, limit length
            text = re.sub(r"\s+", " ", text)
            return text[:600] if text else None
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(1.5)
            else:
                print(f"    vision failed: {e}", file=sys.stderr)
    return None


def get_block_url_map(blocks_raw_path):
    """block.order → media_url の辞書"""
    if not blocks_raw_path.exists():
        return {}
    data = json.loads(blocks_raw_path.read_text(encoding="utf-8"))
    out = {}
    for b in data.get("blocks", []):
        if b.get("block_type") == "image":
            url = b.get("media_url")
            if url:
                out[b["order"]] = url
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chunks_path", type=Path)
    ap.add_argument("--blocks-raw", type=Path, default=None,
                    help="blocks_raw.json path. Defaults to <art_dir>/blocks_raw.json")
    ap.add_argument("--force", action="store_true",
                    help="Re-describe even if image_description already set")
    args = ap.parse_args()

    chunks_path = args.chunks_path.resolve()
    art_dir = chunks_path.parent
    blocks_raw_path = (args.blocks_raw or (art_dir / "blocks_raw.json")).resolve()

    data = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = data["chunks"]

    # source_block_orders → media_url
    block_url_map = get_block_url_map(blocks_raw_path)
    if not block_url_map:
        print(f"WARN: no image URLs found in {blocks_raw_path}", file=sys.stderr)

    # Cache file
    cache_path = art_dir / "image_descriptions.json"
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    img_chunks = [c for c in chunks if c.get("block_type") == "image"]
    print(f"Found {len(img_chunks)} image chunks. Describing with {VISION_MODEL}...")
    success = 0
    skipped = 0
    failed = 0

    for i, c in enumerate(img_chunks):
        if not args.force and c.get("image_description"):
            skipped += 1
            continue

        # Pick first non-empty media URL among source blocks
        urls = []
        for ord_ in c.get("source_block_orders", []):
            u = block_url_map.get(ord_)
            if u and "lazy.png" not in u:
                urls.append(u)

        # Fallback: use content_media_urls from chunk if present
        if not urls:
            for u in c.get("content_media_urls", []) or []:
                if u and "lazy.png" not in u:
                    urls.append(u)

        if not urls:
            failed += 1
            print(f"  [{i+1:>3}/{len(img_chunks)}] chunk{c['chunk_order']:>3} NO URL (all lazy.png)")
            continue

        # Describe each, then merge
        descriptions = []
        for url in urls:
            if url in cache:
                desc = cache[url]
            else:
                desc = describe_image(url)
                cache[url] = desc or ""
                # Save cache after each call (interruption-safe)
                cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
                time.sleep(VISION_DELAY)
            if desc:
                descriptions.append(desc)

        if descriptions:
            joined = " / ".join(descriptions)
            c["image_description"] = joined
            success += 1
            print(f"  [{i+1:>3}/{len(img_chunks)}] chunk{c['chunk_order']:>3} ok ({len(joined)}文字)")
        else:
            failed += 1
            print(f"  [{i+1:>3}/{len(img_chunks)}] chunk{c['chunk_order']:>3} FAILED")

    # Persist
    chunks_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✓ Described {success} chunks (skipped {skipped} cached, failed {failed})")
    print(f"  cache : {cache_path}")
    print(f"  output: {chunks_path}")


if __name__ == "__main__":
    main()
