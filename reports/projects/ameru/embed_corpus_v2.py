#!/usr/bin/env python3
"""Phase A — metadata-biased embedding v2
- 各画像を「画像 + メタデータテキスト」のマルチパートで embed
- 10 スクリーンのクエリも embed
- セクション・ジャンルでフィルタ可能
- matches_v2.json 出力
"""
import os, json, math, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
assert API_KEY, "GEMINI_API_KEY_1 未設定"

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-embedding-2-preview"

ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus"
META = json.loads((ROOT / "corpus_metadata.json").read_text())
OUT_MATCHES = ROOT / "matches_v2.json"
OUT_VECS = ROOT / "corpus_vectors.json"

# 10スクリーンクエリ（セクションフィルタ付き）
SCREEN_QUERIES = {
    "01_FV": {
        "query": "らぶいーず公式IPコラボ5体集合FVヒーロー、ピンクベージュ背景、紙吹雪、コレクター訴求、可愛い手編みあみぐるみプラッシュ、プレミアムD2C",
        "filter_sections": ["hero","lineup"],
    },
    "02_chars": {
        "query": "公式5キャラ個別紹介セクション、キャラクターラインナップ、コレクション欲、IP紹介",
        "filter_sections": ["character","lineup"],
    },
    "03_hero": {
        "query": "すもっぴ水色クマヒーロー単体、朝日、マクロ、完成品、愛着",
        "filter_sections": ["hero","emotion","lifestyle"],
    },
    "04_only1": {
        "query": "編み始め完成済みビフォーアフター3段階、差別化証明、糸玉と完成品の対比",
        "filter_sections": ["only1_proof","process","kit"],
    },
    "05_kit": {
        "query": "キット内容フラットレイ、かぎ針糸パーツ、オールインワン俯瞰、プレミアムD2C",
        "filter_sections": ["kit"],
    },
    "06_video": {
        "query": "スマホ動画教材、手元で編む、チュートリアル、カフェ光",
        "filter_sections": ["video_tutorial","process"],
    },
    "07_process": {
        "query": "編む過程タイムライン、糸から完成へ3段階、物語性",
        "filter_sections": ["process","only1_proof"],
    },
    "08_life": {
        "query": "完成後の暮らし、窓辺、抱きしめる、情緒的ライフスタイル、完成品との時間",
        "filter_sections": ["lifestyle","emotion"],
    },
    "09_offer": {
        "query": "パッケージ箱オファーカード、リボン、プレミアムサブスク、上品",
        "filter_sections": ["offer_gift","kit","hero"],
    },
    "10_cta": {
        "query": "パッケージに手をかけるCTA、ゴールデンアワー、温かいクロージング",
        "filter_sections": ["cta","offer_gift","emotion"],
    },
}

def cosine(a, b):
    d = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    return d/(na*nb) if na and nb else 0

def meta_text(m):
    tags = " ".join(m.get("tags", []))
    return f"Brand: {m.get('brand','')}. Section: {m.get('section','')}. Genre: {m.get('genre','')}. Tags: {tags}."

def embed_img(path, m):
    mime = "image/webp" if path.suffix == ".webp" else "image/png"
    parts = [
        types.Part(inline_data=types.Blob(mime_type=mime, data=path.read_bytes())),
        types.Part(text=meta_text(m)),
    ]
    r = client.models.embed_content(
        model=MODEL,
        contents=types.Content(parts=parts),
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=3072),
    )
    return r.embeddings[0].values

def embed_query(q):
    r = client.models.embed_content(
        model=MODEL, contents=q,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=3072),
    )
    return r.embeddings[0].values

if __name__ == "__main__":
    print(f"=== embed {len(META)} corpus images with metadata ===")
    vecs = {}
    for fname, m in META.items():
        p = CORPUS / fname
        if not p.exists():
            print(f"  ⚠️  missing {fname}")
            continue
        try:
            v = embed_img(p, m)
            vecs[fname] = {"vec": v, "meta": m}
            print(f"  ✅ {fname}")
        except Exception as e:
            print(f"  ❌ {fname}: {type(e).__name__}: {str(e)[:120]}")
    OUT_VECS.write_text(json.dumps(vecs, ensure_ascii=False))
    print(f"\nsaved {len(vecs)} vectors → {OUT_VECS.name}")

    print(f"\n=== match top-4 per screen (with section filter) ===")
    matches = {}
    for sid, cfg in SCREEN_QUERIES.items():
        qv = embed_query(cfg["query"])
        fsec = set(cfg["filter_sections"])
        # 候補をセクションでフィルタ（ただし空集合になるなら全corpusから）
        pool = [(n, d) for n, d in vecs.items() if d["meta"]["section"] in fsec]
        if not pool:
            pool = list(vecs.items())
        scored = sorted(
            ((n, cosine(qv, d["vec"]), d["meta"]) for n, d in pool),
            key=lambda x: -x[1]
        )
        top = scored[:4]
        matches[sid] = [{"file": n, "score": round(s,4), "brand": m["brand"], "section": m["section"]} for n,s,m in top]
        print(f"\n  [{sid}]")
        for n,s,m in top:
            print(f"    {s:.3f}  {n}  ({m['brand']}/{m['section']})")

    OUT_MATCHES.write_text(json.dumps(matches, ensure_ascii=False, indent=2))
    print(f"\n=== saved → {OUT_MATCHES.name} ===")
