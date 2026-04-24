#!/usr/bin/env python3
"""DR-LP corpus embed + ameru 10 screen matching (DR-focused query).
出力: matches_dr.json
"""
import os, json, math, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-embedding-2-preview"

ROOT = Path(__file__).parent
DR_DIR = ROOT / "corpus" / "dr"
META = json.loads((ROOT / "corpus_dr_metadata.json").read_text())
OUT = ROOT / "matches_dr.json"
MIN_SIZE = 50 * 1024

# DR骨格で再設計したameru 10セクションクエリ
# （DR-LP本質：FV→共感→解決→証拠→オファー→FAQ→CTA反復）
DR_SCREENS = {
    "01_FV": {
        "query": "D2Cサブスク商品LP FV、価格大きく訴求、%OFF割引表示、初回¥1,980強調、CTAボタン、数値ベネフィット",
        "sections_hint": ["fv","offer"],
    },
    "02_empathy": {
        "query": "こんなお悩みありませんか、共感セクション、ペイン箇条書き、悩みリスト、困りごと",
        "sections_hint": ["empathy","fv"],
    },
    "03_solution": {
        "query": "◯つのこだわり、独自成分、解決策提示、差別化セクション、Only1証明",
        "sections_hint": ["solution","fv"],
    },
    "04_proof_number": {
        "query": "累計販売数、満足度パーセント、数値証拠、実績アピール、数字で訴求",
        "sections_hint": ["proof_voice","other","fv"],
    },
    "05_proof_voice": {
        "query": "ユーザー愛用者の声、実名年齢付きレビュー、顔写真付き推薦、口コミ証拠",
        "sections_hint": ["proof_voice","other"],
    },
    "06_proof_media": {
        "query": "メディア掲載ロゴ、テレビ番組掲載、雑誌掲載、権威性、公式監修",
        "sections_hint": ["proof_media","fv","logo"],
    },
    "07_offer_anchor": {
        "query": "通常価格から割引、価格アンカー、初回大幅OFF、定期便特典、限定価格",
        "sections_hint": ["offer","fv"],
    },
    "08_guarantee": {
        "query": "返金保証、縛りなし、いつでも解約OK、安心保証、リスクリバーサル",
        "sections_hint": ["guarantee","offer","faq"],
    },
    "09_faq": {
        "query": "よくある質問、FAQ、Q&A、不安回収セクション",
        "sections_hint": ["faq","other"],
    },
    "10_cta": {
        "query": "購入CTAボタン、今すぐお試し、申し込みボタン、カートに入れる、強調ボタン",
        "sections_hint": ["cta","offer","fv"],
    },
}

def cosine(a,b):
    d=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
    return d/(na*nb) if na and nb else 0

def meta_text(m):
    return f"Brand: {m.get('brand','')}. Genre: {m.get('genre','')}. Category: {m.get('category','')}. Section: {m.get('section','')}."

def embed_img(path, m):
    ext = path.suffix.lower().lstrip(".")
    mime = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp","gif":"image/gif"}.get(ext,"image/png")
    parts = [
        types.Part(inline_data=types.Blob(mime_type=mime, data=path.read_bytes())),
        types.Part(text=meta_text(m)),
    ]
    r = client.models.embed_content(
        model=MODEL, contents=types.Content(parts=parts),
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=3072),
    )
    return r.embeddings[0].values

def embed_q(q):
    r = client.models.embed_content(
        model=MODEL, contents=q,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=3072),
    )
    return r.embeddings[0].values

if __name__ == "__main__":
    print(f"=== embed DR corpus (>={MIN_SIZE//1024}KB) ===")
    vecs = {}
    targets = [(f, m) for f, m in META.items() if (DR_DIR/f).exists() and (DR_DIR/f).stat().st_size >= MIN_SIZE]
    print(f"targets: {len(targets)}")
    for i, (f, m) in enumerate(targets):
        try:
            v = embed_img(DR_DIR/f, m)
            vecs[f] = {"vec": v, "meta": m}
            if (i+1)%30==0: print(f"  ..{i+1}/{len(targets)}")
        except Exception as e:
            print(f"  ❌ {f}: {type(e).__name__}: {str(e)[:100]}")
    print(f"\n{len(vecs)} embedded")

    print(f"\n=== match top-5 per ameru DR-screen ===")
    matches = {}
    for sid, cfg in DR_SCREENS.items():
        qv = embed_q(cfg["query"])
        scored = sorted(
            ((n, cosine(qv, d["vec"]), d["meta"]) for n, d in vecs.items()),
            key=lambda x: -x[1]
        )
        top = scored[:5]
        matches[sid] = [{"file":n,"score":round(s,4),"brand":m["brand"],"section":m["section"]} for n,s,m in top]
        print(f"\n  [{sid}]")
        for n,s,m in top:
            print(f"    {s:.3f}  {m['brand']:20s}  {m['section']:12s}  {n}")

    OUT.write_text(json.dumps(matches, ensure_ascii=False, indent=2))
    print(f"\n=== saved → {OUT.name} ===")
