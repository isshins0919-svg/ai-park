#!/usr/bin/env python3
"""
search.py — kiji-rag 全記事を横断してセマンティック検索

使い方:
    python3 search.py "<query>" [--layer A|B|C|D|E]
                                [--element KEY:THR]
                                [--article ARTICLE_ID]
                                [--block-type text|image|video]
                                [-k N]
                                [--json]

全記事の embeddings.npy と chunks.json をロードして結合し、
query の embedding と cosine sim で ranking。20要素フィルタを重ねて最終出力。
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

# tools/search.py → project root
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from vector_store import embed  # type: ignore

KIJI_RAG = ROOT / ".claude" / "knowledge" / "kiji-rag"
ARTICLES_DIR = KIJI_RAG / "articles"


def load_all_articles():
    vecs_list, chunks_list = [], []
    article_meta = {}
    for art_dir in sorted(ARTICLES_DIR.iterdir()):
        if not art_dir.is_dir():
            continue
        emb_path = art_dir / "embeddings.npy"
        chunks_path = art_dir / "chunks.json"
        meta_path = art_dir / "meta.json"
        if not emb_path.exists() or not chunks_path.exists():
            continue
        arr = np.load(emb_path)
        data = json.loads(chunks_path.read_text(encoding="utf-8"))
        if meta_path.exists():
            article_meta[data["article_id"]] = json.loads(meta_path.read_text(encoding="utf-8"))
        for c in data["chunks"]:
            c["_article_id"] = data["article_id"]
        vecs_list.append(arr)
        chunks_list.extend(data["chunks"])
    if not vecs_list:
        print("No embedded articles found. Run embed_chunks.py first.", file=sys.stderr)
        sys.exit(1)
    return np.concatenate(vecs_list, axis=0), chunks_list, article_meta


def main():
    ap = argparse.ArgumentParser(description="kiji-rag semantic search")
    ap.add_argument("query")
    ap.add_argument("--layer", choices=["A", "B", "C", "D", "E"])
    ap.add_argument("--element", help="KEY:THRESHOLD (例: E1_urgency:0.8)")
    ap.add_argument("--article", help="特定記事IDに絞る")
    ap.add_argument("--block-type", dest="block_type", choices=["text", "image", "video"])
    ap.add_argument("-k", "--top-k", type=int, default=5, dest="k")
    ap.add_argument("--per-article-limit", type=int, default=0, dest="per_article_limit",
                    help="同一記事からの最大ヒット数 (0=制限なし)。記事多様性確保用。")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--scan", type=int, default=500,
                    help="フィルタ前に sim上位N件を保持（default 500）")
    args = ap.parse_args()

    arr, chunks, meta_map = load_all_articles()
    q = np.array(embed(args.query), dtype=np.float32)
    qn = q / np.linalg.norm(q)
    an = arr / np.linalg.norm(arr, axis=1, keepdims=True)
    sims = an @ qn
    order = np.argsort(-sims)[:args.scan]

    elem_key, elem_thr = None, 0.0
    if args.element:
        sep = ":" if ":" in args.element else "="
        if sep in args.element:
            elem_key, t = args.element.split(sep, 1)
            elem_thr = float(t)

    from collections import Counter
    per_article_counter = Counter()
    results = []
    for i in order:
        c = chunks[i]
        if args.layer and c.get("dominant_layer") != args.layer:
            continue
        if args.article and c["_article_id"] != args.article:
            continue
        if args.block_type and c["block_type"] != args.block_type:
            continue
        if elem_key and c["elements"].get(elem_key, 0.0) < elem_thr:
            continue
        if args.per_article_limit and per_article_counter[c["_article_id"]] >= args.per_article_limit:
            continue
        results.append({"index": int(i), "sim": float(sims[i]), "chunk": c})
        per_article_counter[c["_article_id"]] += 1
        if len(results) >= args.k:
            break

    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    filters = []
    if args.layer: filters.append(f"layer={args.layer}")
    if elem_key: filters.append(f"{elem_key}>={elem_thr}")
    if args.article: filters.append(f"article={args.article}")
    if args.block_type: filters.append(f"block={args.block_type}")

    print(f"🔎 Query: {args.query}")
    if filters: print(f"   Filters: {' / '.join(filters)}")
    print(f"   Top {len(results)} / {len(chunks)} chunks across {len(meta_map)} articles\n")

    for r in results:
        c = r["chunk"]
        text = (c.get("content_text") or "").replace("\n", " / ")[:140]
        if not text and c["block_type"] != "text":
            text = f"[{c['block_type']}×{len(c['content_media_urls'])}] {c.get('context_hint','')[:100]}"
        dom_layer = c.get("dominant_layer") or "-"
        dom_elems = ", ".join(c.get("dominant_elements", [])[:3]) or "-"
        brand = meta_map.get(c["_article_id"], {}).get("brand_name", "?")
        print(f"  [{r['sim']:.3f}] {c['chunk_id']}  ({brand})")
        print(f"         block={c['block_type']:<5} dom_layer={dom_layer}  funnel={c.get('funnel_position') or '-'}")
        print(f"         dom_elems: {dom_elems}")
        print(f"         └ {text}")
        print()


if __name__ == "__main__":
    main()
