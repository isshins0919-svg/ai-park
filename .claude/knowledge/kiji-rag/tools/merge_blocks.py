#!/usr/bin/env python3
"""
merge_blocks.py — 記事LPの隣接同種ブロックを統合してチャンク化する。

使い方:
    python3 merge_blocks.py <blocks_raw.json> <chunks_skeleton.json>

入力: blocks_raw.json (WebFetch等で取得した生ブロック配列)
出力: chunks_skeleton.json (隣接同種統合済みのチャンク配列。20要素スコアは空)

チャンク境界ルール:
- block_type が切り替わったところでチャンク区切り
- 同種ブロックが連続するなら1チャンクに統合
- テキストは改行連結、画像/動画はURL/caption/altを配列で保持
"""
import json
import sys
from pathlib import Path


EMPTY_ELEMENTS = {
    "A1_pain_empathy": 0.0,
    "A2_fear_appeal": 0.0,
    "A3_regret_avoidance": 0.0,
    "A4_anxiety_trigger": 0.0,
    "B1_authority": 0.0,
    "B2_social_proof": 0.0,
    "B3_data_evidence": 0.0,
    "B4_transparency": 0.0,
    "C1_causality": 0.0,
    "C2_unique_mechanism": 0.0,
    "C3_differentiation": 0.0,
    "C4_objection_handling": 0.0,
    "D1_transformation": 0.0,
    "D2_aspiration": 0.0,
    "D3_scenario": 0.0,
    "D4_scarcity": 0.0,
    "E1_urgency": 0.0,
    "E2_offer_appeal": 0.0,
    "E3_risk_reversal": 0.0,
    "E4_cta_clarity": 0.0,
}


def merge_adjacent_blocks(blocks):
    chunks = []
    current = None
    for b in blocks:
        btype = b["block_type"]
        if current is None or current["block_type"] != btype:
            if current is not None:
                chunks.append(current)
            current = {
                "chunk_order": len(chunks) + 1,
                "block_type": btype,
                "source_block_orders": [],
                "content_text": "",
                "content_media_urls": [],
                "content_captions": [],
                "content_alt": [],
                "has_cta": False,
                "cta_urls": [],
            }
        current["source_block_orders"].append(b["order"])
        if btype == "text":
            text = (b.get("content") or "").strip()
            if text:
                if current["content_text"]:
                    current["content_text"] += "\n"
                current["content_text"] += text
        else:
            current["content_media_urls"].append(b.get("media_url", ""))
            current["content_captions"].append(b.get("caption", "") or "")
            current["content_alt"].append(b.get("alt_text", "") or "")
        if b.get("is_cta_block") or b.get("cta"):
            current["has_cta"] = True
            if b.get("cta_url"):
                if b["cta_url"] not in current["cta_urls"]:
                    current["cta_urls"].append(b["cta_url"])
    if current is not None:
        chunks.append(current)
    return chunks


def build_chunk_ids(article_id, chunks):
    for i, c in enumerate(chunks):
        c["chunk_id"] = f"{article_id}__c{i+1:03d}"
        c["chunk_order"] = i + 1
        c["elements"] = dict(EMPTY_ELEMENTS)
        c["layer_scores"] = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0}
        c["dominant_layer"] = None
        c["dominant_elements"] = []
        c["total_intensity"] = 0.0
        c["funnel_position"] = None
        c["context_hint"] = ""
        c["embedding"] = None
        c["embedding_model"] = None
        c["embedding_generated_at"] = None
    return chunks


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    raw = json.loads(in_path.read_text(encoding="utf-8"))
    article_id = raw["article_id"]
    blocks = raw["blocks"]
    chunks = merge_adjacent_blocks(blocks)
    chunks = build_chunk_ids(article_id, chunks)
    out = {
        "article_id": article_id,
        "schema_version": "1.0",
        "chunks": chunks,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    n_text = sum(1 for c in chunks if c["block_type"] == "text")
    n_image = sum(1 for c in chunks if c["block_type"] == "image")
    n_video = sum(1 for c in chunks if c["block_type"] == "video")
    print(f"  total chunks   : {len(chunks)}")
    print(f"    text         : {n_text}")
    print(f"    image        : {n_image}")
    print(f"    video        : {n_video}")
    print(f"  source blocks  : {len(blocks)}")
    print(f"  output         : {out_path}")


if __name__ == "__main__":
    main()
