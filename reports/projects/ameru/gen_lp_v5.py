#!/usr/bin/env python3
"""Phase A PoC — ameru LP v5 generation
- matches_v2.json の top-4 refs（メタデータフィルタ済）を使う
- nano-banana-pro-preview で生成
出力: reports/projects/ameru/screens_v5/01-10.png
"""
import os, json, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)
MODEL = "nano-banana-pro-preview"

ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus"
OUT = ROOT / "screens_v5"
OUT.mkdir(exist_ok=True)
MATCHES = json.loads((ROOT / "matches_v2.json").read_text())

STYLE = """Create a vertical 9:16 smartphone LP screen for Japanese D2C amigurumi kit brand "ameru" (collaborating with Japanese IP「らぶいーず®」/loveeez, targeting 20-30s female らぶいーず collectors).

BRAND RULES (strict):
- Color palette: dusty sky-blue #BCD8E8, ivory #F7F1E6, pink-beige #F0D8D0, sand beige #D9C4A7, gold #C9A36A
- NO English "Love is..." / "loveeez" / "love-eez" — if brand name appears, ひらがな「らぶいーず®」only
- Photorealistic Japanese premium D2C LP (SHIRO / FUJIMI / Craftie Home Box / The Woobles quality)
- Natural light, generous whitespace, feminine, crafted, premium, mature-cute
- Hero subject lower 65-70%, upper 30-35% headline zone
- Beautiful Japanese typography: 丸ゴシック太字 headlines, 細字 body. Text must render cleanly.

USE THE PROVIDED 4 REFERENCE IMAGES (section-filtered top matches from the Phase A visual corpus) as strong style/composition/color guides — inherit palette, props, mood, camera angle, lighting. Do NOT copy literally; reinterpret for this specific screen.
"""

SCREENS = {
    "01.png": ("01_FV", """SCREEN: FV HERO. 5 handmade amigurumi plushies in らぶいーず style arranged on cloud ivory cushion. Gold confetti floating. Pink-beige background.
HEADLINE (upper, 丸ゴシック太字, 2 lines):
  らぶいーず、ぜんぶ、
  自分の手で。
SUB (細字):
  はじめての編みぐるみ、公式コラボ。
TOP-RIGHT BADGE:
  らぶいーず® 日本テレビ 公式
BOTTOM-LEFT GOLD LOGO:
  ameru"""),

    "02.png": ("02_chars", """SCREEN: 5 official らぶいーず character introduction.
All 5 characters in arch arrangement on ivory background. Soft paper confetti.
HEADLINE (upper, 丸ゴシック太字):
  5体で、ひとつの世界。
SUB (細字):
  すもっぴ・ぴょんちー・にゃぽ・うるる・ぱおぱお
NAME LABELS under each in hiragana.
BOTTOM PILL:
  5回定期便で、ぜんぶ揃う。"""),

    "03.png": ("03_hero", """SCREEN: Sky-blue すもっぴ hero shot. Morning light, cloud blanket or pink-beige background, macro crochet texture, soft dreamy bokeh.
HEADLINE (upper, 丸ゴシック太字, 2 lines):
  届くのは、キット。
  生まれるのは、あなたの子。
SUB (細字):
  1体目は、すもっぴ。
BOTTOM-RIGHT BADGE (ivory × gold):
  公式らぶいーず® 第1弾"""),

    "04.png": ("04_only1", """SCREEN: Only-1 proof — 3-stage comparison on ivory linen:
  1: ordinary tangled wool ball (×)
  2: ameru pre-started sky-blue tubular yarn piece (clean magic ring + 6 stitches)
  3: completed sky-blue すもっぴ
Hand-drawn gold arrows between.
HEADLINE (upper, 丸ゴシック太字, 2 lines):
  いちばん難しい最初の一目、
  編んでおきました。
STAGE LABELS (細字):
  ふつうの編み物  →  ameruの編み始め  →  完成
BOTTOM CENTER GOLD BADGE:
  ameru ONLY 1 — 編み始め完成済み"""),

    "05.png": ("05_kit", """SCREEN: All-in-one kit contents flat-lay. Sky-blue × ivory matte gift box center, yarn ball, wooden hook with ribbon, needle, parts, QR card.
HEADLINE (upper, 丸ゴシック太字):
  ひらけば、すぐ始められる。
SUB (細字):
  かぎ針・糸・パーツ・動画教材、ぜんぶ同梱。
BOTTOM-RIGHT BADGE:
  買い足し、ゼロ。"""),

    "06.png": ("06_video", """SCREEN: Video tutorial. Tilted flat-lay with iPhone playing vertical Japanese-subtitled crochet tutorial, half-finished sky-blue すもっぴ head, yarn ball, hook, mug, blanket.
HEADLINE (upper, 丸ゴシック太字):
  スマホ片手に、5分ずつ。
SUB (細字, 2 lines):
  右利きも、左利きも。
  字幕だけで分かる縦型動画。
BOTTOM PILL:
  LINE公式から、あなたのペースで届く。"""),

    "07.png": ("07_process", """SCREEN: Crocheting progression — 3 vertical stages of sky-blue すもっぴ on cream paper with gold arrows:
  STEP 01: starting from yarn ball (1 stitch done)
  STEP 02: head done, body in progress
  STEP 03: about to attach eye parts
HEADLINE (upper, 丸ゴシック太字):
  糸から、あなたの子へ。
STEP LABELS (細字):
  STEP 01. 編み始める
  STEP 02. 形になる
  STEP 03. 命が宿る
BOTTOM (細字):
  ひとつの子を編み上げるまで、8〜10時間。"""),

    "08.png": ("08_life", """SCREEN: Lifestyle emotional completion. Sky-blue すもっぴ on windowsill in golden-hour light, mug and small plant, woman's hand (no face, cream cardigan) gently touching bear's head. Rim light, shallow DoF.
HEADLINE (upper, 丸ゴシック太字, 2 lines):
  完成した瞬間、
  もう、いっしょにいる。
SUB (細字):
  自分で編んだ1体は、世界でひとつ。
BOTTOM small tags:
  #ameruできた ／ #らぶいーず"""),

    "09.png": ("09_offer", """SCREEN: Offer card. Upper: pristine sky-blue × ivory ameru gift box with ribbon on ivory paper. Lower: clean white offer card with gold accents.
CARD (crisp 丸ゴシック Japanese typography):
  Gold label: SPECIAL OFFER
  Headline: はじめの1体は、¥1,980。
  Price table:
    F1（初回）体験価格        ¥1,980
    F2〜F5 通常価格           ¥4,200 × 4回
    ─────────────────
    5回総額（税込）           ¥18,780
  Checklist (細字):
    ✓ かぎ針・糸・パーツ、すべて同梱
    ✓ LINEで届く動画教材つき
    ✓ 編み始め、完成済み
    ✓ いつでも解約OK
    ✓ 送料込み
  Soft red badge: 限定300セット
  Footer (細字): 5回定期便／単品購入も選べます。"""),

    "10.png": ("10_cta", """SCREEN: Final CTA. Woman's hands (no face, cream cardigan) gently about to untie ribbon on sky-blue × ivory ameru gift box. Tiny completed sky-blue すもっぴ watching beside. Golden-hour warm side light, creamy bokeh, cinematic.
HEADLINE (upper, 丸ゴシック太字, 2 lines):
  らぶいーず、
  ぜんぶ、迎えに行く。
SUB (細字):
  はじめての1体は、¥1,980から。
MID sky-blue pill CTA button, bold white:
  ¥1,980で はじめてみる
REASSURANCE row (細字, equal spacing):
  いつでも解約OK ／ 送料込み ／ 限定300セット
BOTTOM gold logomark:
  ameru × らぶいーず®"""),
}

def gen(fname, sid, detail):
    out = OUT / fname
    if out.exists() and out.stat().st_size > 30000:
        print(f"[skip] {fname}"); return
    refs = [m["file"] for m in MATCHES[sid]]
    print(f"\n[{fname}] refs: {refs}")
    parts = [types.Part(text=STYLE + "\n\n" + detail)]
    for rf in refs:
        p = CORPUS / rf
        if not p.exists(): continue
        mime = "image/webp" if p.suffix == ".webp" else "image/png"
        parts.append(types.Part(inline_data=types.Blob(mime_type=mime, data=p.read_bytes())))
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=[types.Content(parts=parts, role="user")],
        )
        for cand in resp.candidates:
            for part in cand.content.parts:
                if part.inline_data and part.inline_data.data:
                    out.write_bytes(part.inline_data.data)
                    print(f"  ✅ {len(part.inline_data.data)//1024}KB")
                    return
        print(f"  ❌ no image")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {str(e)[:200]}")

if __name__ == "__main__":
    print(f"=== ameru LP v5 (Phase A PoC) via {MODEL} ===")
    for fname, (sid, detail) in SCREENS.items():
        gen(fname, sid, detail)
    print("\n=== done ===")
    for f in sorted(OUT.glob("*.png")):
        print(f"  {f.name}: {f.stat().st_size//1024}KB")
