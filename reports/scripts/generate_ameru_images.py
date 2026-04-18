#!/usr/bin/env python3
"""
ameru LP 画像生成スクリプト v1
ずもっぴ（白丸あみぐるみ）× スカイブルーブランドの7カット生成
参考: The Woobles / lululun / fanfare のLP画像スタイル

出力先: reports/ameru_images/
"""

import os, sys, time, subprocess
from pathlib import Path

# ── 環境変数ロード ──
def load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'],
                               capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except Exception:
            pass

for v in ['GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
    load_env(v)

API_KEYS = [k for k in [
    os.environ.get('GEMINI_API_KEY_1', ''),
    os.environ.get('GEMINI_API_KEY_2', ''),
    os.environ.get('GEMINI_API_KEY_3', ''),
] if k.strip()]

if not API_KEYS:
    print("❌ GEMINI_API_KEY_1 が設定されていません。~/.zshrc を確認してください。")
    sys.exit(1)

from google import genai
from google.genai import types

clients = [genai.Client(api_key=k) for k in API_KEYS]
print(f"✅ API Keys: {len(API_KEYS)}本 確認")

# ── 出力先 ──
OUT_DIR = Path(__file__).parent / "ameru_images"
OUT_DIR.mkdir(exist_ok=True)

# ── パッケージ画像をリファレンスとして読み込む ──
PKG_PATH = Path(__file__).parent / "ameru_pkg_3rd.png"
def load_pkg_image():
    if PKG_PATH.exists():
        return types.Part.from_bytes(data=PKG_PATH.read_bytes(), mime_type='image/png')
    return None

pkg_ref = load_pkg_image()
print(f"📦 パッケージ参照: {'あり ✅' if pkg_ref else 'なし（テキストのみで生成）'}")

# ── ブランドDNA ──
BRAND_DNA = """
[AMERU BRAND DNA — MUST APPLY TO ALL IMAGES]

Brand: ameru (アメル) — "amigurumi for everyone"
Character: ZUMOPPI (ずもっぴ) — A round, chubby white crochet amigurumi stuffed animal.
  - Pure white yarn texture, round body, small round ears (like a bunny or bear)
  - Tiny dot eyes (black safety eyes), tiny curved smile, stubby arms and legs
  - Extremely cute, kawaii aesthetic, plush and soft-looking
  - About the size of a fist (approx 10cm tall)

Brand Colors:
  - Primary: Sky blue (#4CBAD4) — fresh, cute, craft-inspired
  - Secondary: White (#FFFFFF) — clean, pure
  - Accent: Soft pink (#F5A8C0) — warmth, kawaii

Photography Style:
  - D2C product photography quality — clean, lifestyle-oriented
  - Soft natural lighting (not harsh studio flash)
  - Pastel, airy, slightly warm color tone
  - Props: craft supplies, pastel fabrics, wooden surfaces, white backgrounds
  - Mood: cozy, creative, achievable, joyful
  - Japanese kawaii aesthetic meets modern D2C brand
  - Similar vibe to: The Woobles (USA), lululun (JP), cute D2C brands

IMPORTANT: ずもっぴ should always look like a handmade crochet amigurumi — visible yarn texture is essential.
"""

# ── 画像定義 ──
IMAGES = [
    {
        "filename": "01_zumoppi_hero.png",
        "label": "ずもっぴ ヒーローショット",
        "prompt": f"""{BRAND_DNA}

IMAGE TYPE: Hero product shot — the STAR of the LP

Create a professional, beautiful product photograph of ZUMOPPI (ずもっぴ) — a round, white crochet amigurumi stuffed animal.

SCENE:
- Zumoppi is centered, slightly elevated, as if floating or sitting on a soft cloud-white surface
- Clean white or very pale sky blue gradient background
- Soft, directional light from the upper-left creates gentle shadows that show the yarn texture beautifully
- The crochet texture (individual yarn stitches) is clearly visible and beautiful
- Zumoppi's tiny face: two round black eyes, small curved smile — radiating warmth

STYLING:
- A few tiny pink heart confetti pieces scattered around (very subtle)
- Small star decorations in the background (very faint, not distracting)
- The overall feel: "this is the most adorable thing I've ever seen and I want to make one"

COMPOSITION:
- Portrait orientation (vertical 4:5 ratio)
- Zumoppi takes up about 50% of the frame
- Generous white space — clean and premium

This image must make someone scroll to a stop and say "wait, I MADE that?!" — it's the emotional anchor of the entire LP.
"""
    },
    {
        "filename": "02_package_lifestyle.png",
        "label": "パッケージ + ずもっぴ ライフスタイル",
        "prompt": f"""{BRAND_DNA}

IMAGE TYPE: Package + finished product lifestyle flat-lay

SCENE:
- Elegant flat-lay (bird's eye view, slightly angled) on a soft white surface
- The ameru crochet kit package (sky blue pouch with kawaii design) is the centerpiece
- Zumoppi (finished white crochet amigurumi) is placed naturally next to the package — "before and after" visual
- A few kit items peek out or are artfully arranged around: a crochet hook, a small ball of white yarn, printed pattern instructions
- Soft pastel pink flowers or dried flowers as organic props (small, not overwhelming)
- The vibe: "this beautiful package arrives at your door, you open it, and this cute little friend emerges"

LIGHTING: Soft, diffused natural light from a window. Warm but bright.

COLORS: White surface, sky blue package, white yarn, pastel accents — clean and cohesive.

This image must convey: "I want this to arrive at MY door."
"""
    },
    {
        "filename": "03_unboxing_flatlay.png",
        "label": "キット内容 フラットレイ",
        "prompt": f"""{BRAND_DNA}

IMAGE TYPE: Kit contents flat-lay — "everything you need" visualization

SCENE:
- Perfect flat-lay (overhead, perfectly symmetrical) on a soft textured white background
- All kit contents artfully arranged:
  * 2-3 small balls of white and sky-blue yarn (wound into neat balls)
  * A small crochet hook (cute pastel or wooden handle)
  * Printed instruction card / pattern sheet with Japanese text
  * 2 small black safety eyes (the tiny plastic eyes for the amigurumi)
  * Small amount of fiberfill/stuffing (fluffy, cloud-like)
  * Stitch markers (tiny colorful rings)
  * The finished Zumoppi amigurumi as the "result" in the corner
- Items arranged in a grid or circular pattern — beautiful and organized
- Sky blue ameru package visible at the top

COMPOSITION: Perfect symmetry, every item visible and identifiable.
MOOD: "Wow, so much comes inside!" — communicates value and completeness.

Caption space at bottom: "All Materials Included"
"""
    },
    {
        "filename": "04_hands_crafting.png",
        "label": "制作中 手元アップ",
        "prompt": f"""{BRAND_DNA}

IMAGE TYPE: Lifestyle — hands crafting the amigurumi

SCENE:
- Close-up of a woman's hands (30s, natural nails, clean, delicate) crocheting
- She is holding a round white crochet piece — clearly in progress of making Zumoppi
- A pastel-colored crochet hook (sky blue or blush pink) held naturally in her right hand
- White yarn running between her fingers
- Background: slightly blurred cozy interior — wooden table, soft natural light from window
- Perhaps a cup of tea/coffee visible blurred in the background

MOOD: "This looks easy. She looks relaxed. I could do this on a weekend afternoon."

IMPORTANT: The crochet work in her hands looks ACHIEVABLE, not difficult. Beginner-friendly vibe.
The focus is on the peaceful, meditative joy of creating something cute with your hands.

Lighting: Warm golden afternoon light. Cozy and calm.
"""
    },
    {
        "filename": "05_lifestyle_finished.png",
        "label": "完成品 ライフスタイル",
        "prompt": f"""{BRAND_DNA}

IMAGE TYPE: Lifestyle — finished Zumoppi being held / displayed

SCENE:
- A woman's hands (we see only from wrists down — no face) hold Zumoppi gently with both hands
- She's sitting on a bed with soft white bedding, or at a wooden desk by a window
- Zumoppi is held up, slightly toward the camera, as if she's showing it off with pride
- Soft, warm natural light
- She's wearing a cozy sweater (cream, white, or soft pink)
- In the background: soft bokeh, perhaps some plants or shelves

MOOD: "I MADE THIS. And it's adorable."
This is the moment of フィエロ (achievement joy) — the emotional payoff of the entire LP.

The image should make viewers feel: "I want to feel that satisfaction too."

COMPOSITION: Portrait vertical. Hands and Zumoppi in lower-center. Warm, cozy, intimate.
"""
    },
    {
        "filename": "06_shelf_display.png",
        "label": "飾る ライフスタイル",
        "prompt": f"""{BRAND_DNA}

IMAGE TYPE: Lifestyle — Zumoppi displayed in a living space

SCENE:
- Zumoppi sits on a small wooden shelf or bookshelf
- Surrounded by small, tasteful decor items: a tiny succulent plant, a small candle, a few books
- The shelf is in a cozy room — natural wood tones, white walls, soft light
- Perhaps 2-3 Zumoppis of different pastel colors are displayed together (imagining the full collection: white, sky blue, mint green, soft pink, lilac)
- The image shows: "this is what your room looks like AFTER you complete the collection"

MOOD: "This belongs in my home. This is the aesthetic I want."
SNS-worthy, Pinterest-worthy interior shot.

LIGHTING: Golden hour, soft through gauze curtains.
COMPOSITION: Slightly elevated angle, warm and inviting.
"""
    },
    {
        "filename": "07_collection_preview.png",
        "label": "5種コレクション予告",
        "prompt": f"""{BRAND_DNA}

IMAGE TYPE: Collection preview — 5 characters in a row

SCENE:
- 5 round crochet amigurumi characters lined up in a row
- Each is the same round, chubby Zumoppi-style character but in different colors:
  1. White (No.1 ずもっぴ — the hero)
  2. Sky blue (#4CBAD4)
  3. Soft pink (#F5A8C0)
  4. Mint green (#A8E6CF)
  5. Lavender (#C8A8E6)
- They're all the same size, same face, same round shape — like a family
- Arranged on a white surface with subtle pastel confetti/stars
- The No.1 white one is slightly in front or has a tiny gold star badge

MOOD: "I need all 5. I will not rest until I have all 5."
Pure collector's desire. FOMO by design.

COMPOSITION: Wide horizontal shot (16:9 or landscape), all 5 characters clearly visible.
BACKGROUND: Clean white with very subtle sky blue gradient at top.
"""
    },
]

# ── 生成ロジック ──
def generate_image(img_def, client_idx=0):
    client = clients[client_idx % len(clients)]
    filename = img_def["filename"]
    label = img_def["label"]
    out_path = OUT_DIR / filename

    if out_path.exists():
        print(f"  ⏭️  スキップ（既存）: {filename}")
        return True

    print(f"\n🎨 生成中: [{label}]")
    print(f"   → {filename}")

    # パッケージ参照付きで生成（ライフスタイル系のみ）
    use_pkg = pkg_ref and ("package" in filename or "lifestyle" in filename.lower())
    if use_pkg:
        contents = [
            "Reference image — this is the ameru crochet kit package design. "
            "Use the sky blue color and kawaii brand style as visual reference. "
            "Generate a NEW lifestyle photograph as described below.",
            pkg_ref,
            img_def["prompt"]
        ]
    else:
        contents = [img_def["prompt"]]

    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(aspect_ratio='4:5')
                )
            )

            img_data = next((p.inline_data.data for p in resp.parts if p.inline_data), None)
            if not img_data or len(img_data) < 5120:
                print(f"   ⚠️ attempt {attempt+1}: 画像データなし or 小さすぎ")
                time.sleep(5)
                continue

            out_path.write_bytes(img_data)
            print(f"   ✅ 保存: {out_path.name} ({len(img_data)//1024}KB)")
            return True

        except Exception as e:
            print(f"   ❌ attempt {attempt+1}: {e}")
            if attempt < 2:
                time.sleep(8)

    return False

# ── メイン実行 ──
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"  ameru LP 画像生成 — {len(IMAGES)}カット")
    print(f"  出力先: {OUT_DIR}")
    print(f"{'='*60}\n")

    success = 0
    for i, img in enumerate(IMAGES):
        ok = generate_image(img, client_idx=i)
        if ok:
            success += 1
        time.sleep(3)  # レート制限対策

    print(f"\n{'='*60}")
    print(f"  完了: {success}/{len(IMAGES)}枚 生成")
    print(f"  出力先: {OUT_DIR}")
    print(f"{'='*60}")
