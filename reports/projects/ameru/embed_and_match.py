#!/usr/bin/env python3
"""ameru embedding-2 パイプライン
1. refs/ 配下43枚を gemini-embedding-2-preview でベクトル化
2. 10スクリーンのプロンプトテキストを同じモデルでベクトル化
3. コサイン類似度で各スクリーンにtop-3の参考画像を割り当て
4. 結果を reports/projects/ameru/matches.json に保存

※ gemini-embedding-2-preview がマルチモーダル空間でテキスト×画像比較を同一空間で行える前提。
"""
import os, json, math, base64, warnings
warnings.filterwarnings("ignore")
from pathlib import Path

from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
assert API_KEY, "GEMINI_API_KEY_1 未設定"

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-embedding-2-preview"

ROOT = Path(__file__).parent
REFS = ROOT / "refs"
OUT = ROOT / "matches.json"

# 10スクリーンのプロンプト（短めの意味ベクトル用。詳細プロンプトは生成時に使う）
SCREEN_QUERIES = {
    "01_FV": "らぶいーずコレクター向けLP FV。5体あみぐるみ集合、IP訴求、ピンクベージュ背景、紙吹雪、可愛い世界観、IP推し全力",
    "02_chars": "公式5キャラ紹介セクション。すもっぴ ぴょんちー にゃぽ うるる ぱおぱお、可愛く並ぶ、コレクター魂、コンプリート感",
    "03_hero": "すもっぴ水色クマあみぐるみヒーローショット、完成した子、朝日、優しい光、マクロ、愛着、可愛らしい完成品",
    "04_only1": "編み始め完成済みビフォーアフター3段階、糸玉→編み始め→完成、差別化ビジュアル証明",
    "05_kit": "キット内容フラットレイ、かぎ針糸パーツ動画QR、オールインワン、俯瞰、上品",
    "06_video": "スマホ動画教材、手元で編む、LINEチュートリアル、カフェ光、安心、誰でも編める",
    "07_process": "編む過程タイムライン、糸から完成へ、手編みの進行、物語性、ステップ3段",
    "08_life": "完成後の暮らし、窓辺に飾る、抱きしめる、愛着、一緒の時間、情緒的ライフスタイル",
    "09_offer": "パッケージ箱単体、オファーカード、リボン、上品、初回¥1,980、プレミアムD2Cサブスク",
    "10_cta": "パッケージに手をかける、リボンを解く直前、ゴールデンアワー、CTA、温かい感情的クロージング",
}

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    return dot / (na*nb) if na and nb else 0

def embed_text(text: str):
    r = client.models.embed_content(
        model=MODEL, contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=3072),
    )
    return r.embeddings[0].values

def embed_image(path: Path):
    # マルチモーダルimage embedding
    try:
        img_bytes = path.read_bytes()
        mime = "image/webp" if path.suffix == ".webp" else "image/png"
        r = client.models.embed_content(
            model=MODEL,
            contents=types.Content(parts=[types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes))]),
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=3072),
        )
        return r.embeddings[0].values
    except Exception as e:
        print(f"  image embed failed {path.name}: {type(e).__name__}: {str(e)[:150]}")
        return None

if __name__ == "__main__":
    print(f"=== embed 43 images via {MODEL} ===")
    image_vecs = {}
    for p in sorted(REFS.glob("*")):
        if p.suffix.lower() not in {".png", ".webp", ".jpg", ".jpeg"}:
            continue
        v = embed_image(p)
        if v:
            image_vecs[p.name] = v
            print(f"  ✅ {p.name} ({len(v)} dim)")
    print(f"\n{len(image_vecs)} images embedded")

    print(f"\n=== embed 10 screen queries ===")
    screen_vecs = {}
    for sid, q in SCREEN_QUERIES.items():
        screen_vecs[sid] = embed_text(q)
        print(f"  ✅ {sid}")

    print(f"\n=== match top-3 refs per screen ===")
    matches = {}
    for sid, qv in screen_vecs.items():
        scored = sorted(
            ((name, cosine(qv, iv)) for name, iv in image_vecs.items()),
            key=lambda x: -x[1]
        )
        top3 = scored[:3]
        matches[sid] = [{"file": n, "score": round(s, 4)} for n, s in top3]
        print(f"  {sid}: {', '.join(f'{n} ({s:.3f})' for n,s in top3)}")

    OUT.write_text(json.dumps(matches, ensure_ascii=False, indent=2))
    print(f"\n=== saved → {OUT} ===")
