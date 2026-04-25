#!/usr/bin/env python3
"""
embed_chunks.py — kiji-rag の chunks.json を embedding-2 でベクトル化する。

使い方:
    python3 embed_chunks.py <path/to/chunks.json>

入力: chunks.json (apply_scores.py の出力)
生成物:
  - <article_dir>/embeddings.npy        : np.float32 shape=(N_chunks, 3072)
  - <article_dir>/embedding_index.jsonl : chunk_id ↔ npy index マッピング
  - chunks.json を上書き更新: embedding_model / embedding_dim / embedding_index / embedding_generated_at 付与

埋め込みテキスト組立方針:
  context_hint + funnel_position + content_text + captions + alt + dominant_elements + dominant_layer

  20要素の dominant_elements を連結することで、
  「意味が近く、かつ同じ機能（権威性・緊急性など）を持つチャンク」が検索で引きやすくなる。

※ 画像ブロックのマルチモーダル埋め込み（実画像バイト）は、
    Squad Beyond の lazy.png 問題を解決してから実装する（現状はテキスト/キャプションのみ）。
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# path: .../kiji-rag/tools/embed_chunks.py → project root = 4 levels up
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))

from vector_store import embed, EMBED_MODEL, EMBED_DELAY  # type: ignore


def build_embed_text(chunk):
    parts = []
    if chunk.get("context_hint"):
        parts.append(f"[文脈] {chunk['context_hint']}")
    if chunk.get("funnel_position"):
        parts.append(f"[ファネル位置] {chunk['funnel_position']}")
    if chunk.get("content_text"):
        parts.append(chunk["content_text"])
    captions = [c for c in chunk.get("content_captions", []) if c]
    if captions:
        parts.append(f"[キャプション] {' / '.join(captions)}")
    alts = [a for a in chunk.get("content_alt", []) if a]
    if alts:
        parts.append(f"[alt] {' / '.join(alts)}")
    # Image description (Gemini Vision で生成、describe_images.py の出力)
    img_desc = chunk.get("image_description")
    if img_desc:
        parts.append(f"[画像説明] {img_desc}")
    dom = chunk.get("dominant_elements", [])
    if dom:
        parts.append(f"[主要訴求要素] {', '.join(dom)}")
    if chunk.get("dominant_layer"):
        parts.append(f"[訴求層] {chunk['dominant_layer']}")
    text = "\n".join(parts).strip()
    return text or "[media block without textual content]"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    chunks_path = Path(sys.argv[1]).resolve()
    art_dir = chunks_path.parent

    data = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = data["chunks"]
    n = len(chunks)

    print(f"Embedding {n} chunks with {EMBED_MODEL}...")
    vecs = []
    index_map = []
    for i, c in enumerate(chunks):
        text = build_embed_text(c)
        try:
            vec = embed(text)
        except Exception as e:
            print(f"  [{i+1:>3}/{n}] FAILED {c['chunk_id']}: {e}", file=sys.stderr)
            vec = [0.0] * 3072
        vecs.append(vec)
        index_map.append({
            "chunk_id": c["chunk_id"],
            "index": i,
            "block_type": c["block_type"],
            "dominant_layer": c.get("dominant_layer"),
            "text_length": len(text),
        })
        if (i + 1) % 10 == 0 or i == n - 1:
            print(f"  [{i+1:>3}/{n}] done")
        time.sleep(EMBED_DELAY)

    arr = np.array(vecs, dtype=np.float32)
    emb_path = art_dir / "embeddings.npy"
    np.save(emb_path, arr)

    idx_path = art_dir / "embedding_index.jsonl"
    with idx_path.open("w", encoding="utf-8") as f:
        for entry in index_map:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    for i, c in enumerate(chunks):
        c["embedding_model"] = EMBED_MODEL
        c["embedding_dim"] = int(arr.shape[1])
        c["embedding_generated_at"] = now
        c["embedding_index"] = i
        c["embedding"] = f"embeddings.npy[{i}]"
    data["embedding_model"] = EMBED_MODEL
    data["embedding_generated_at"] = now
    data["embedding_file"] = "embeddings.npy"
    data["embedding_index_file"] = "embedding_index.jsonl"

    chunks_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✓ Embedded {n} chunks, shape={arr.shape}")
    print(f"  embeddings : {emb_path}")
    print(f"  index      : {idx_path}")
    print(f"  updated    : {chunks_path}")


if __name__ == "__main__":
    main()
