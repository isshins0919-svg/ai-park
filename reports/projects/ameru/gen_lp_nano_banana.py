#!/usr/bin/env python3
"""ameru LP 10 screens via Nano Banana Pro
- matches.json の top-3 refs を入力画像として渡す
- テキストプロンプト + 参考画像 → 新規画像生成
- P08「らぶいーずコレクター向け×IP推し」コンセプト
出力: reports/projects/ameru/screens_v4/01.png 〜 10.png
"""
import os, json, warnings
warnings.filterwarnings("ignore")
from pathlib import Path

from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
assert API_KEY, "GEMINI_API_KEY_1 未設定"

client = genai.Client(api_key=API_KEY)
MODEL = "nano-banana-pro-preview"

ROOT = Path(__file__).parent
REFS = ROOT / "refs"
OUT = ROOT / "screens_v4"
OUT.mkdir(exist_ok=True)
MATCHES = json.loads((ROOT / "matches.json").read_text())

STYLE = """Create a vertical 9:16 smartphone LP screen for a Japanese D2C amigurumi kit brand "ameru" (collaborating with Japanese IP「らぶいーず®」/loveeez, targeting 20-30s women who already collect らぶいーず characters).

BRAND RULES (strict):
- Color palette: dusty sky-blue #BCD8E8, ivory #F7F1E6, pink-beige #F0D8D0, sand beige #D9C4A7, gold #C9A36A
- NO English "Love is..." / "loveeez" text anywhere — if brand name appears, use hiragana「らぶいーず®」only
- Photorealistic Japanese high-end D2C LP aesthetic (like SHIRO / FUJIMI / Craftie Home Box)
- Soft natural light, generous whitespace, feminine, crafted, premium
- Hero subject in lower 65-70%, upper 30-35% reserved for headline text
- Beautiful Japanese typography: 丸ゴシック太字 headlines, 細字 body. Text must render cleanly without corruption.

USE THE PROVIDED REFERENCE IMAGES as strong style/composition/color guides — inherit their tonality, palette, props, and mood. Do NOT copy them literally; reinterpret for this specific screen.
"""

# 各画面の詳細プロンプト（コピー焼き込み含む）
SCREENS = {
    "01.png": """SCREEN: FV (ファーストビュー). The hero of the entire LP.
COMPOSITION: 5 handmade amigurumi plush characters in らぶいーず style arranged softly on a pink-beige / ivory gradient background with small paper-confetti flying. Cloud-shaped ivory cushion holds them. Soft warm studio light.
HEADLINE TEXT TO BURN IN (in Japanese, 丸ゴシック太字, 2 lines, upper portion):
  らぶいーず、ぜんぶ、
  自分の手で。
SUB TEXT (細字, below):
  はじめての編みぐるみ、公式コラボ。
BADGE (top-right, small pill):
  らぶいーず® 日本テレビ 公式
BRAND MARK (bottom-left, gold tiny):
  ameru
Target mood: FUJIMI magazine ad quality, feminine, collector's joy.""",

    "02.png": """SCREEN: 5 official characters introduction section.
COMPOSITION: All 5 らぶいーず characters (すもっぴ sky-blue bear / ぴょんちー pink rabbit / にゃぽ cream cat with yellow ribbon / うるる gray-purple / ぱおぱお mint green elephant) arranged in a soft arch — 1 center, 2 on each side. Clean ivory background, soft paper confetti falling gently. Each character labeled.
HEADLINE (upper, 丸ゴシック太字):
  5体で、ひとつの世界。
SUB (細字):
  すもっぴ・ぴょんちー・にゃぽ・うるる・ぱおぱお
NAME LABELS under each character (small hiragana).
BOTTOM PILL BADGE:
  5回定期便で、ぜんぶ揃う。""",

    "03.png": """SCREEN: Hero shot of the first delivery character "すもっぴ" (sky-blue crocheted bear).
COMPOSITION: A single sky-blue & white crocheted teddy bear amigurumi sitting on a fluffy ivory cloud-like cushion or knit blanket. Soft morning light from the left. Macro close-up showing chunky tubular-yarn crochet texture. Shallow DoF, background softly dreamy.
HEADLINE (upper, 丸ゴシック太字, 2 lines):
  届くのは、キット。
  生まれるのは、あなたの子。
SUB (細字):
  1体目は、すもっぴ。
BOTTOM-RIGHT BADGE (ivory × gold):
  公式らぶいーず® 第1弾""",

    "04.png": """SCREEN: Only-1 proof section — "編み始め完成済み" (pre-started piece) differentiation.
COMPOSITION: 3-stage horizontal comparison on ivory linen background:
  Stage 1: ordinary tangled wool yarn ball (grayish, messy) with × mark
  Stage 2: a clean pre-started sky-blue tubular yarn piece, magic ring + 6 stitches already done (the ameru advantage)
  Stage 3: a completed sky-blue すもっぴ bear
Arrows between stages (hand-drawn gold).
HEADLINE (upper, 丸ゴシック太字, 2 lines):
  いちばん難しい最初の一目、
  編んでおきました。
STAGE LABELS (tiny 細字, under each):
  ふつうの編み物  →  ameruの編み始め  →  完成
BOTTOM CENTER BADGE (gold × ivory):
  ameru ONLY 1 — 編み始め完成済み""",

    "05.png": """SCREEN: All-in-one kit contents flat-lay.
COMPOSITION: Top-down flat-lay: a sky-blue × ivory matte gift box (center), surrounded by: one sky-blue tubular yarn ball, a natural wooden crochet hook with pink ribbon, a needle, tiny eye parts, a white QR-code instruction card. On ivory linen, soft daylight. Kinfolk-magazine aesthetic.
HEADLINE (upper, 丸ゴシック太字):
  ひらけば、すぐ始められる。
SUB (細字):
  かぎ針・糸・パーツ・動画教材、ぜんぶ同梱。
BOTTOM-RIGHT BADGE:
  買い足し、ゼロ。""",

    "06.png": """SCREEN: Video tutorial section — phone-and-hands-and-yarn scene.
COMPOSITION: Gently tilted flat-lay, a modern iPhone playing a vertical Japanese-subtitled crochet tutorial (progress bar visible), next to a half-finished sky-blue すもっぴ head, sky-blue yarn ball, wooden crochet hook, ivory knit blanket, white ceramic tea cup. Warm afternoon café lighting, golden tone.
HEADLINE (upper, 丸ゴシック太字):
  スマホ片手に、5分ずつ。
SUB (細字, 2 lines):
  右利きも、左利きも。
  字幕だけで分かる縦型動画。
BOTTOM PILL:
  LINE公式から、あなたのペースで届く。
PHONE SCREEN chapter list at bottom:
  わ編み／こま編み／増やし目／とじ方／組み立て""",

    "07.png": """SCREEN: Crocheting process timeline — 3 progressive stages.
COMPOSITION: Three small images of sky-blue すもっぴ progression arranged in a vertical sequence on cream paper, connected by gold hand-drawn arrows:
  1. Starting from yarn ball (1 stitch done)
  2. Head completed, body in progress
  3. About to attach eyes (button eyes beside)
HEADLINE (upper, 明朝風丸ゴシック太字):
  糸から、あなたの子へ。
STEP LABELS (tiny 細字):
  STEP 01. 編み始める
  STEP 02. 形になる
  STEP 03. 命が宿る
BOTTOM 細字:
  ひとつの子を編み上げるまで、8〜10時間。""",

    "08.png": """SCREEN: Finished product in lifestyle — emotional completion scene.
COMPOSITION: A sky-blue すもっぴ sits on a windowsill in morning golden-hour light. Next to it: a white ceramic mug and a small green plant. A woman's hand (no face, cream cardigan sleeve) gently touches the bear's head. Shallow DoF, rim light, lens flare.
HEADLINE (upper, 明朝風丸ゴシック太字, 2 lines):
  完成した瞬間、
  もう、いっしょにいる。
SUB (細字):
  自分で編んだ1体は、世界でひとつ。
BOTTOM small tags:
  #ameruできた ／ #らぶいーず""",

    "09.png": """SCREEN: Offer panel — pricing card.
COMPOSITION: Upper half: a pristine sky-blue × ivory ameru gift box with ribbon, on pale ivory paper. Lower half: a clean white offer card with gold accent lines.
OFFER CARD CONTENT (in Japanese, 丸ゴシック typography, crisp):
  Label (gold letter-spaced small): SPECIAL OFFER
  Big headline: はじめの1体は、¥1,980。
  Price table (aligned):
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
  Bottom red soft badge: 限定300セット
  Footer 細字: 5回定期便／単品購入も選べます。""",

    "10.png": """SCREEN: Final CTA — emotional closing.
COMPOSITION: Woman's hands (no face, cream cardigan sleeves) gently about to untie the ribbon on an unopened sky-blue × ivory ameru gift box. Next to the box on the table, a tiny completed sky-blue すもっぴ watches. Golden-hour warm side lighting, creamy bokeh background, cinematic shallow DoF.
HEADLINE (upper, 明朝風丸ゴシック太字, 2 lines):
  らぶいーず、
  ぜんぶ、迎えに行く。
SUB (細字):
  はじめての1体は、¥1,980から。
MID-LOWER sky-blue pill-shaped CTA button, bold white text:
  ¥1,980で はじめてみる
BELOW BUTTON reassurance row (細字, equal spacing):
  いつでも解約OK ／ 送料込み ／ 限定300セット
BOTTOM gold logomark:
  ameru × らぶいーず®""",
}

def generate(screen_id: str, detail_prompt: str, ref_files: list[str], out: Path):
    print(f"\n[{out.name}] refs: {', '.join(ref_files)}")
    parts = [types.Part(text=STYLE + "\n\n" + detail_prompt)]
    for rf in ref_files:
        p = REFS / rf
        if not p.exists():
            print(f"  ⚠️  ref missing: {rf}")
            continue
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
                    return True
        print(f"  ❌ no image. text={resp.text[:200] if resp.text else '?'}")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {str(e)[:300]}")
    return False

if __name__ == "__main__":
    print(f"=== ameru LP v4 via {MODEL} with image-referenced generation ===")
    key_map = {
        "01.png": "01_FV", "02.png": "02_chars", "03.png": "03_hero", "04.png": "04_only1",
        "05.png": "05_kit", "06.png": "06_video", "07.png": "07_process", "08.png": "08_life",
        "09.png": "09_offer", "10.png": "10_cta",
    }
    for fname, prompt in SCREENS.items():
        out = OUT / fname
        if out.exists() and out.stat().st_size > 30000:
            print(f"[skip] {fname}")
            continue
        refs = [m["file"] for m in MATCHES[key_map[fname]]]
        generate(fname, prompt, refs, out)
    print("\n=== done ===")
    for f in sorted(OUT.glob("*.png")):
        print(f"  {f.name}: {f.stat().st_size//1024}KB")
