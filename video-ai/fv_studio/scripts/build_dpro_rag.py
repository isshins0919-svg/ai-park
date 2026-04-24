#!/usr/bin/env python3
"""DPro勝ちFVパターンRAG 構築スクリプト.

- 5ジャンル（成長期サプリ/体臭ケア/スキンケア/美容液/ヘルスケア用品）の
  DPro TOP動画広告を集約し、Gemini embedding-2 でベクトル化して
  `data/dpro_fv_patterns.json` に保存する。

使い方:
    # 事前にMCP get_items_by_rds を叩いた結果ファイル群を
    # tool-results/ から指定して本スクリプトを実行
    GEMINI_API_KEY_1=xxx python3 scripts/build_dpro_rag.py

ソース入力: tool-results/mcp-df...-<timestamp>.txt （複数）
出力: data/dpro_fv_patterns.json
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
assert API_KEY, "GEMINI_API_KEY_1 not set"

MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_PATH = DATA_DIR / "dpro_fv_patterns.json"

SOURCE_FILES = {
    54: "/Users/ca01224/.claude/projects/-Users-ca01224-Desktop---VOYAGE-/60e6c77d-236e-4d13-bec8-0ea865b9d87f/tool-results/mcp-df6842ef-0c99-4102-8c8a-84b879dd8520-get_items_by_rds_api_v1_items_get-1777054104719.txt",
    76: "/Users/ca01224/.claude/projects/-Users-ca01224-Desktop---VOYAGE-/60e6c77d-236e-4d13-bec8-0ea865b9d87f/tool-results/mcp-df6842ef-0c99-4102-8c8a-84b879dd8520-get_items_by_rds_api_v1_items_get-1777054110247.txt",
    80: "/Users/ca01224/.claude/projects/-Users-ca01224-Desktop---VOYAGE-/60e6c77d-236e-4d13-bec8-0ea865b9d87f/tool-results/mcp-df6842ef-0c99-4102-8c8a-84b879dd8520-get_items_by_rds_api_v1_items_get-1777054115777.txt",
    7: "/Users/ca01224/.claude/projects/-Users-ca01224-Desktop---VOYAGE-/60e6c77d-236e-4d13-bec8-0ea865b9d87f/tool-results/mcp-df6842ef-0c99-4102-8c8a-84b879dd8520-get_items_by_rds_api_v1_items_get-1777054154410.txt",
    1467: "/Users/ca01224/.claude/projects/-Users-ca01224-Desktop---VOYAGE-/60e6c77d-236e-4d13-bec8-0ea865b9d87f/tool-results/mcp-df6842ef-0c99-4102-8c8a-84b879dd8520-get_items_by_rds_api_v1_items_get-1777054126223.txt",
}

# embedding入力用: ペルソナ/N1と意味照合しやすいよう
#   冒頭セリフ + ナレーション要約（先頭300字） を結合する
def build_embed_text(item: dict[str, Any]) -> str:
    parts: list[str] = []
    if s := item.get("ad_start_sentence"):
        parts.append(f"冒頭: {s}")
    if s := item.get("ad_sentence"):
        parts.append(f"ヘッドコピー: {s[:160]}")
    if s := item.get("ad_all_sentence"):
        parts.append(f"ナレーション: {s[:400]}")
    parts.append(f"ジャンル: {item.get('genre_name', '')}")
    parts.append(f"商品: {item.get('product_name', '')}")
    return " / ".join(parts)


def extract_pattern(item: dict[str, Any]) -> dict[str, Any]:
    """1広告のFVパターン要約を抽出."""
    return {
        "item_id": item.get("id"),
        "product_id": item.get("product_id"),
        "product_name": item.get("product_name"),
        "genre_id": item.get("genre_id"),
        "genre_name": item.get("genre_name"),
        "app_name": item.get("app_name"),
        "duration": item.get("duration"),
        "video_shape": item.get("video_shape"),
        "media_type": item.get("media_type"),
        "transition_type": item.get("transition_type"),
        "ad_start_sentence": item.get("ad_start_sentence"),
        "ad_sentence": item.get("ad_sentence"),
        # ナレーションは長文なので先頭600字で丸める
        "ad_all_sentence": (item.get("ad_all_sentence") or "")[:600],
        "thumbnail_url": item.get("thumbnail_url"),
        "production_url": item.get("production_url"),
        "video_url": item.get("production_share_url"),
        "cost_difference": int(item.get("cost_difference") or 0),
        "play_count_difference": int(item.get("play_count_difference") or 0),
        "digg_rate": item.get("digg_rate"),
    }


def embed_batch(client: genai.Client, texts: list[str]) -> list[list[float]]:
    """1件ずつembed（Gemini APIは複数件同時も対応するがレート制御のため逐次）.

    Gemini embedding-2-preview は個人鍵で ~60req/min 程度で 400/429 を返す場合あり。
    1秒ずつ間隔を空ける + 失敗時は指数バックオフ（最大60秒）で粘る。
    """
    vecs: list[list[float]] = []
    for i, t in enumerate(texts):
        # 基本レート制御: 1秒間隔
        if i > 0:
            time.sleep(1.1)
        for attempt in range(5):
            try:
                r = client.models.embed_content(
                    model=MODEL,
                    contents=t,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=EMBED_DIM,
                    ),
                )
                vecs.append(list(r.embeddings[0].values))
                break
            except Exception as e:
                msg = str(e)[:150]
                wait = min(60, 4 * (2 ** attempt))  # 4→8→16→32→60
                print(f"  [retry {attempt+1}/5 item={i}] {msg} → sleep {wait}s", flush=True)
                time.sleep(wait)
        else:
            print(f"  [fail] item {i} embedding failed, using zeros", flush=True)
            vecs.append([0.0] * EMBED_DIM)
        if (i + 1) % 10 == 0:
            print(f"  embedded {i+1}/{len(texts)}", flush=True)
    return vecs


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=API_KEY)

    patterns: list[dict[str, Any]] = []
    for genre_id, path in SOURCE_FILES.items():
        p = Path(path)
        if not p.exists():
            print(f"[skip] {p.name} not found")
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        items = data.get("items", [])
        print(f"[load] genre_id={genre_id} items={len(items)}")
        for it in items:
            # 縦長動画 + ad_all_sentence有り のみ採用（FV参考として有効）
            if not it.get("ad_all_sentence"):
                continue
            if it.get("video_shape") not in ("縦長", None):
                continue
            patterns.append(extract_pattern(it))

    print(f"\n[aggregate] {len(patterns)} patterns after filter")

    # 商品名+item_idでdedupe（同一広告がジャンル跨ぎで出る稀ケース対策）
    seen = set()
    unique: list[dict[str, Any]] = []
    for p in patterns:
        key = p.get("item_id")
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    patterns = unique
    print(f"[dedupe] {len(patterns)} patterns")

    # embed
    print(f"\n[embed] model={MODEL} dim={EMBED_DIM}", flush=True)
    texts = [build_embed_text(p) for p in patterns]
    vecs = embed_batch(client, texts)
    for p, v in zip(patterns, vecs):
        p["embedding"] = v
        p["embed_text"] = build_embed_text(p)

    zero_count = sum(1 for p in patterns if all(x == 0 for x in p["embedding"][:5]))
    print(f"[embed-stats] non-zero={len(patterns)-zero_count}, zero(failed)={zero_count}", flush=True)

    payload = {
        "model": MODEL,
        "dim": EMBED_DIM,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_genres": list(SOURCE_FILES.keys()),
        "count": len(patterns),
        "patterns": patterns,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_mb = OUT_PATH.stat().st_size / 1024 / 1024
    print(f"\n[done] {OUT_PATH} ({size_mb:.2f} MB, {len(patterns)} patterns)")


if __name__ == "__main__":
    main()
