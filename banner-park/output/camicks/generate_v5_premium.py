"""
Camicks Banner v5 — プレミアム差別化版
ブランドカラー #3ABCEE × 明朝体 × 余白設計 × 競合と真逆の世界観
"""

import subprocess, os, time, json
from datetime import datetime

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass

for _v in ['GEMINI_API_KEY_1','GEMINI_API_KEY_2','GEMINI_API_KEY_3']:
    _load_env(_v)

from google import genai
from google.genai import types

API_KEYS = [k for k in [os.environ.get(f'GEMINI_API_KEY_{i}','').strip() for i in range(1,4)] if k]
clients = [genai.Client(api_key=k) for k in API_KEYS]
print(f"✅ API Keys: {len(API_KEYS)}本")

slug = 'camicks'
out_dir = f'banner-park/output/{slug}'
assets_dir = f'{out_dir}/source_assets'
banner_dir = f'{out_dir}/banners_v5'
os.makedirs(banner_dir, exist_ok=True)

def make_part(filename):
    path = os.path.join(assets_dir, filename)
    if not os.path.exists(path):
        print(f"  ⚠️ 素材なし: {filename}")
        return None
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png'}.get(ext,'image/jpeg')
    return types.Part.from_bytes(data=data, mime_type=mime)

# ===========================================================
# デザインシステム（全バナー共通）
# ===========================================================
DESIGN_SYSTEM = """
[BRAND DESIGN SYSTEM — APPLY TO ALL ELEMENTS]

BRAND COLOR: #3ABCEE (calm sky blue — used as accent, NOT as background flood)
DARK ACCENT: #1a2e3d (deep navy charcoal — for headlines and authority)
BACKGROUND: #ffffff pure white OR #fafaf8 warm white — generous white space
TEXT PRIMARY: #1a2e3d dark navy
TEXT SECONDARY: #666666 mid gray

TYPOGRAPHY — CRITICAL FOR LUXURY FEEL:
- Japanese headlines: elegant MINCHO/SERIF style
  (Yu Mincho, Hiragino Mincho Pro, or similar thin-stroke Japanese serif)
  → Think: premium fashion magazine, NOT sports brand, NOT medical
- English/numbers: Garamond, Cormorant, or Playfair Display style
  → Thin, tall, elegant letterforms
- Body text: light weight, generous line spacing

DESIGN PHILOSOPHY — 引き算（subtraction）:
✓ Generous white space — let the product breathe
✓ One dominant visual, maximum 3 text elements
✓ #3ABCEE used sparingly as thin lines, small accents, or underlines
✓ Premium product photography feel
✓ Fashion editorial, NOT infographic

STRICTLY FORBIDDEN (競合との差別化):
✗ NO blue glowing bubbles or badge effects
✗ NO cotton flower or nature stock graphics
✗ NO dotted circle callouts
✗ NO "Check Point" labels
✗ NO cluttered information panels
✗ NO cheap gradient backgrounds
✗ NO rounded cartoon icons
✗ NO yellow highlight lines on product
✗ NO Comic Sans or rounded casual fonts
"""

BANNERS = [
    {
        "index": 1,
        "filename": "banner_01_v5.png",
        "theme": "シークレット構造 — 種明かし",
        "headline": "これが、5本指なんです。",
        "ref_images": ["camicks-s-dgy_detail.jpg"],
        "prompt": f"""{DESIGN_SYSTEM}

REFERENCE PHOTO: The actual Camicks dark charcoal ankle sock on mannequin foot. Use this EXACT sock for the Camicks side.

Create a 1600x1600px Amazon product sub-image.

[CONCEPT: Elegant reveal — the shocking truth]
Viewer reaction: "Wait... THAT is a 5-toe sock?!"

[LAYOUT: Clean editorial split]

TOP: Headline in elegant mincho serif, very large, dark navy #1a2e3d
「これが、5本指なんです。」
— Thin, graceful letterforms. Strong but refined.

CENTER: Side-by-side comparison on white background
Thin #3ABCEE line divider between panels (elegant, not "VS" bubble)

LEFT panel — 「一般の5本指」(small, light gray caption below):
- Dark charcoal ankle sock, mannequin foot
- Clearly shows 5 individual toe bumps protruding from instep
- Soft natural lighting

Small elegant text center: "vs"  (lowercase, Garamond style, #3ABCEE)

RIGHT panel — 「Camicks」(small caption below, #3ABCEE color):
- EXACTLY the sock from reference photo — dark charcoal, flat smooth instep
- NO visible toe contours on top
- Same soft lighting
- Tiny elegant arrow: 「甲、フラット」in light gray

BOTTOM:
Elegant subline in mincho: 「5本指には、見えません。」
Smaller, #666666: 「外見は普通のソックス。中身は5本指の健康設計。」
Bottom right corner: marusawa wordmark, very small, #1a2e3d

[SPACING]
Minimum 8% margin all edges. Let it breathe.
The comparison photos should feel like editorial lookbook photography.

[CRITICAL]
All Japanese in elegant mincho/serif — NO rounded casual fonts.
Perfect rendering. Premium feel throughout."""
    },
    {
        "index": 2,
        "filename": "banner_02_v5.png",
        "theme": "オフィス — 解放",
        "headline": "脱いでも、バレない。",
        "ref_images": ["トリミング-レタッチ-_MG_7833.jpg"],
        "prompt": f"""{DESIGN_SYSTEM}

REFERENCE PHOTO: Off-white/cream Camicks ankle sock on mannequin foot (side view, clean background). Use this as the product visual.

Create a 1600x1600px Amazon product sub-image.

[CONCEPT: Quiet confidence. The relief of not worrying.]

[LAYOUT: Fashion editorial — large photo, minimal text]

The reference photo fills LEFT 58% of the frame.
Background behind sock: soft warm gray or the original background.
Lighting: clean, diffused — premium product photography.

Add a black leather penny loafer elegantly positioned next to/below the foot.
The sock instep appears completely flat and smooth.

RIGHT 42%: Pure white background, generous vertical spacing.

TOP-RIGHT: Tiny horizontal rule in #3ABCEE (thin line, decorative)

HEADLINE (right side, large, elegant mincho serif, #1a2e3d):
「脱いでも、
バレない。」
— Two lines, very large. The dominant visual on the right.

Below headline, generous space, then:
Small elegant text (#666666, mincho light):
「ローファーでも、フラットシューズでも。
靴を脱いでも、普通に見える。」

Below that:
Thin #3ABCEE underline (2px), then small text:
「靴を脱いでもバレない」

BOTTOM-RIGHT corner: marusawa wordmark, tiny, #1a2e3d

[CRITICAL]
NO badge or button. The #3ABCEE underline replaces it — elegant, not garish.
Large white space on right half. Let the headline dominate.
Mincho serif throughout. Premium."""
    },
    {
        "index": 3,
        "filename": "banner_03_v5.png",
        "theme": "アクティブ — 理由提示",
        "headline": "一日中はいても、蒸れない理由がある。",
        "ref_images": ["IMG_8829.jpg"],
        "prompt": f"""{DESIGN_SYSTEM}

REFERENCE PHOTO: Actual lifestyle photo — person wearing beige-gray Camicks socks with black Adidas sneakers, denim jeans cuffed, standing on stone paving tiles with green plants behind. Use this photo as the main visual.

Create a 1600x1600px Amazon product sub-image.

[CONCEPT: A confident claim with substance behind it.]

[LAYOUT: Editorial full-bleed photo with restrained text overlay]

The lifestyle photo fills the entire frame (crop to 1:1 square, focus on feet and lower legs).

TOP OVERLAY:
Dark semi-transparent band (#1a2e3d at 85% opacity) across top 30% of image.
Inside this band:
Headline in elegant mincho serif, WHITE:
「一日中はいても、蒸れない理由がある。」
— Graceful, thin strokes. Legible against dark band.

Below headline in same band, smaller white text (light weight):
「和紙40%配合 camifine® — 吸湿速乾」

BOTTOM OVERLAY:
Narrow dark band (#1a2e3d at 75%) across bottom 15%.
Inside: three elegant text labels separated by thin #3ABCEE vertical rules:
「和紙40%」｜「吸湿速乾」｜「抗菌防臭」
— Small, spaced, elegant. NO pill badges or buttons.

Bottom right corner in band: marusawa wordmark, tiny, white.

[CRITICAL]
The lifestyle photo must remain the hero — text overlays are restrained.
NO bubble graphics, NO icons, NO infographic elements.
Mincho serif for all Japanese text.
The overall feel: premium outdoor/lifestyle brand, NOT medical/functional."""
    },
    {
        "index": 4,
        "filename": "banner_04_v5.png",
        "theme": "機能解説 — 問いかけ",
        "headline": "なぜ、外から見えないのか。",
        "ref_images": ["camicks-women-inside.jpg", "camicks-s-dgy_detail.jpg"],
        "prompt": f"""{DESIGN_SYSTEM}

REFERENCE PHOTOS:
1. FIRST: Interior of Camicks sock — beige/natural color, sock turned inside out or folded, showing 5 individual toe chambers (partition structure visible)
2. SECOND: Exterior of dark charcoal Camicks sock on mannequin — completely flat smooth instep

Create a 1600x1600px Amazon product sub-image.

[CONCEPT: Satisfy curiosity with elegance, not a cheap infographic.]

[LAYOUT: Minimalist editorial explanation]

Background: #fafaf8 warm white

TOP: Large headline, elegant mincho serif, #1a2e3d:
「なぜ、外から見えないのか。」
— Thin horizontal rule in #3ABCEE below headline (full width, 1.5px)

CENTER: Two photos side by side with generous spacing

LEFT photo (from first reference — interior):
- The interior partition structure photo, slightly cropped for square feel
- Below photo, small elegant caption in mincho, #666666:
  「内側：パーティション構造」
  smaller: 「5本指を個別に収納」

Elegant thin arrow → center

RIGHT photo (from second reference — exterior):
- The flat instep mannequin photo
- Below photo, small caption in #3ABCEE mincho:
  「外側：フラット」
  smaller: 「指の輪郭、出ません」

BOTTOM:
Thin horizontal rule #3ABCEE, then:
Elegant body text (#666666, mincho light):
「外から見えないパーティション構造。足指を正しく配置し、甲はフラットに保ちます。」

Four small text labels (NO pill badges — just text with thin dividers):
「和紙40%配合」 · 「吸湿・速乾」 · 「抗菌防臭」 · 「日本製」

Bottom right: marusawa wordmark, tiny.

[CRITICAL]
NO blue bubbles, NO dotted circles, NO cartoon icons.
Clean, editorial, architect-level layout.
Mincho serif throughout. Maximum restraint = maximum premium."""
    },
    {
        "index": 5,
        "filename": "banner_05_v5.png",
        "theme": "品質 — 日本製の誇り",
        "headline": "日本製の丁寧さが、毎日に宿る。",
        "ref_images": ["camicks-s-gy_detail-b.jpg"],
        "prompt": f"""{DESIGN_SYSTEM}

REFERENCE PHOTO: Close-up macro of Camicks sock toe area — light gray/silver-white fine ribbed knit fabric. Beautiful, precise textile craftsmanship.

Create a 1600x1600px Amazon product sub-image.

[CONCEPT: Japanese craft heritage. Made with care, built to last.]

[LAYOUT: Luxury goods editorial — fabric macro hero]

The macro fabric photo fills TOP 55% of frame.
Lighting: soft, slightly warm. Shows the depth and quality of the knit.
Minimal or no text overlay on the photo itself — let the fabric speak.

Small top-right element: 「日本製」in elegant mincho, tiny, #3ABCEE
Below it: thin horizontal rule #3ABCEE

HEADLINE overlaid at very bottom edge of photo or just below:
「日本製の丁寧さが、毎日に宿る。」
Elegant mincho serif, large, #1a2e3d

BOTTOM 40%: White background (#ffffff), generous spacing

Three care qualities presented as elegant text columns (NO icons):

Left column:
「洗濯機 可」
(thin rule)
30℃・ネット推奨

Center column:
「高耐久 設計」
(thin rule)
毛玉・穴あきしにくい

Right column:
「型崩れ しにくい」
(thin rule)
繰り返し使用可

Between columns: thin vertical rules in #3ABCEE

Below: thin full-width rule #3ABCEE, then:
Small body text (#666666, mincho):
「大阪泉州、1969年創業。靴下だけを作り続けた技術が、品質を保証します。」

Bottom right: marusawa wordmark.

[CRITICAL]
The fabric macro must look LUXURIOUS — like cashmere or premium wool photography.
Text columns: NO icons, NO badges — pure elegant typography.
Mincho serif throughout. This should feel like a Japanese craft brand, not a health goods brand."""
    },
    {
        "index": 6,
        "filename": "banner_06_v5.png",
        "theme": "澤田権威 — 55年の本気",
        "headline": "55年分の本気が、1足に入ってる。",
        "ref_images": ["camicks-women_detail03.jpg", "marusawa_logo.png"],
        "prompt": f"""{DESIGN_SYSTEM}

REFERENCE PHOTOS:
1. FIRST: Product + factory image — Camicks sock on mannequin beside Shima Seiki knitting machines in a bright modern factory
2. SECOND: marusawa logo (black wordmark on white) — use this EXACT logo

Create a 1600x1600px Amazon product sub-image.

[CONCEPT: 55 years of focused expertise = the only brand that could make this.]

[LAYOUT: Heritage brand editorial — authoritative and refined]

TOP HEADER: Deep navy band (#1a2e3d), full width, top 22% of frame.
Inside band, headline in elegant mincho serif, WHITE, large:
「55年分の本気が、1足に入ってる。」
— Graceful, thin strokes. The most authoritative-feeling text of all 6 banners.
Right-aligned in the band: thin #3ABCEE vertical accent line.

CENTER 52%: The factory + sock reference photo, full width.
- Show both the precision Shima Seiki machinery and the sock
- Clean, professional framing
- #3ABCEE thin border frame around the photo (1.5px)

BOTTOM 26%: White background.
Left-aligned content:

Large elegant text (mincho, #1a2e3d):
「1969年創業、大阪泉州」
Smaller below (#666666):
「澤田株式会社 — 靴下だけを作り続けて、55年。」

Thin #3ABCEE horizontal rule.

Even smaller (#999999):
「その技術が、シークレット5本指を可能にした。」

RIGHT side of bottom section:
The marusawa logo from reference photo, placed cleanly.
Below logo: 「SINCE 1969」in small elegant serif, #3ABCEE.

[CRITICAL]
The dark header band gives immediate authority.
NO cheap effects, NO "SINCE 1969" badge/bubble.
The marusawa logo must appear EXACTLY as in reference.
Mincho serif throughout. This should feel like a 100-year-old Japanese craft house."""
    }
]

# ===========================================================
# 生成
# ===========================================================
print("\n" + "="*60)
print("🍌 NANO BANANA PRO v5 — プレミアム差別化版")
print("ブランドカラー #3ABCEE × 明朝体 × 余白設計")
print("="*60)

ok = 0
ng = 0
results = []

for config in BANNERS:
    fn = config['filename']
    fp = os.path.join(banner_dir, fn)

    if os.path.exists(fp) and os.path.getsize(fp) > 50000:
        print(f"  ⏭ Banner {config['index']:02d} スキップ")
        ok += 1
        results.append({'index': config['index'], 'status': 'skipped'})
        continue

    print(f"\n  🎨 Banner {config['index']:02d}: {config['theme']}")
    print(f"     「{config['headline']}」")

    contents = []
    loaded = 0
    for img_fn in config['ref_images']:
        part = make_part(img_fn)
        if part:
            contents.append(part)
            loaded += 1
    contents.append(config['prompt'])
    print(f"     参照素材: {loaded}枚")

    for attempt in range(3):
        c = clients[(config['index'] - 1 + attempt) % len(clients)]
        try:
            resp = c.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(aspect_ratio='1:1')
                )
            )

            img_data = None
            for part in resp.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = part.inline_data.data
                    break

            if not img_data or len(img_data) < 10240:
                if attempt < 2:
                    time.sleep(5)
                    continue
                ng += 1
                results.append({'index': config['index'], 'status': 'failed'})
                break

            with open(fp, 'wb') as f:
                f.write(img_data)
            size_kb = len(img_data) // 1024
            print(f"     ✅ {fn} ({size_kb}KB)")
            ok += 1
            results.append({'index': config['index'], 'status': 'ok', 'size_kb': size_kb})
            break

        except Exception as e:
            print(f"     ❌ attempt {attempt+1}: {str(e)[:100]}")
            if attempt < 2:
                time.sleep(8)
            else:
                ng += 1
                results.append({'index': config['index'], 'status': 'error'})

    time.sleep(3)

print("\n" + "="*60)
print(f"📊 {ok}/{len(BANNERS)} OK, {ng}/{len(BANNERS)} NG")
print(f"📁 {banner_dir}/")
print("="*60)

with open(f'{out_dir}/v5_results.json', 'w', encoding='utf-8') as f:
    json.dump({'generated_at': datetime.now().isoformat(), 'ok': ok, 'ng': ng, 'results': results}, f, ensure_ascii=False, indent=2)
