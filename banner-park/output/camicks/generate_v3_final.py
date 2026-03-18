"""
Camicks Banner v3 — 確定コピー × 感情点火版
「これが、5本指なんです。」コンセプト × 澤田権威追加
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
if not API_KEYS:
    raise RuntimeError("GEMINI_API_KEY_1 が設定されていません")

clients = [genai.Client(api_key=k) for k in API_KEYS]
print(f"✅ API Keys: {len(API_KEYS)}本")

slug = 'camicks'
out_dir = f'banner-park/output/{slug}'
banner_dir = f'{out_dir}/banners_v3'
os.makedirs(banner_dir, exist_ok=True)

BANNER_CONFIGS = [
    {
        "index": 1,
        "filename": "banner_01_v3.png",
        "theme": "シークレット構造 — 種明かし",
        "headline": "これが、5本指なんです。",
        "sub": "5本指には、見えません。",
        "prompt": """Create a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks (Japanese brand).

[EMOTIONAL CONCEPT]
The viewer sees this image and thinks: "Wait... THAT is a 5-toe sock?!"
This is a reveal moment. The image IS the punchline.

[VISUAL LAYOUT: Before → After reveal]
Clean white background (#ffffff).

TOP SECTION — Headline:
Large bold Japanese text at top: 「これが、5本指なんです。」
Font: rounded sans-serif (Noto Sans JP Bold style), dark green #2d5a3d
Very prominent, takes up full width, large size

CENTER — Two sock comparison side by side:
LEFT panel (labeled 一般の5本指ソックス, red small text):
  - Dark charcoal ankle sock on mannequin foot
  - CLEARLY shows 5 individual toe bumps/ridges on the instep (top of foot)
  - Ribbed ankle cuff
  - Red × mark below

RIGHT panel (labeled Camicks, green small text):
  - Same dark charcoal ankle sock on mannequin foot
  - Instep is COMPLETELY FLAT and SMOOTH — zero toe contours visible
  - Looks like a completely normal ankle sock
  - Ribbed ankle cuff visible
  - Green ✓ mark below
  - Small arrow callout: 「甲がフラット」

Large green "VS" text centered between the two panels

BOTTOM — Sub copy:
Medium Japanese text: 「5本指には、見えません。」
Color: #555555 dark gray
Then smaller: 「外見は普通のソックス。中身は5本指の健康設計。」
Brand tag tiny at very bottom: 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[COLOR PALETTE]
Background: white #ffffff
Headline: dark green #2d5a3d
Accent/brand: medium green #66b780
Left label: warm red
Right label: #66b780

[TEXT REQUIREMENTS — CRITICAL]
ALL Japanese text must be pixel-perfect, no blurring, no artifacts
Headline must be LARGE and DOMINANT — biggest element on page
Clean font, high contrast, legible at thumbnail size
5% safe margin from all edges"""
    },
    {
        "index": 2,
        "filename": "banner_02_v3.png",
        "theme": "オフィス — 解放",
        "headline": "脱いでも、バレない。",
        "sub": "ローファーでも、フラットシューズでも。靴を脱いでも普通に見える。",
        "prompt": """Create a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[EMOTIONAL CONCEPT]
The anxious moment of taking off shoes in someone's home or office — that fear disappears.
Feeling: relief, freedom, quiet confidence.

[VISUAL]
Main photo (left 60% of frame):
  - Elegant foot in off-white/cream Camicks ankle sock
  - One black leather loafer beside/near the foot (as if just removed)
  - Light wood floor or very light gray background
  - Soft natural lighting — fashion magazine quality
  - The sock instep appears completely smooth and flat
  - Shot from 45° angle, showing ankle and toe area clearly

RIGHT SIDE — Text area (white background):
  Top: Building/office icon + loafer icon in dark green (small, decorative)
  Headline: 「脱いでも、バレない。」
    - Bold, large, dark green #2d5a3d
    - This is the dominant text element

  Sub text below headline:
  「ローファーでも、フラットシューズでも。
   靴を脱いでも普通に見える。」
  Color: #555555, medium size

  Green badge (rounded rectangle, #66b780 background, white text):
  「靴を脱いでもバレない」

  Brand tag bottom right (tiny):
  「Camicks | 和紙シークレット5本指ソックス」

[LAYOUT: Z型]
Top-left to top-right → bottom-left to bottom-right flow
Main photo bottom-left, headline top, sub text bottom-right

[COLOR PALETTE]
Background: white #ffffff
Headline: #2d5a3d dark green
Badge: #66b780 green, white text
Photo sock color: cream/off-white

[TEXT — CRITICAL]
「脱いでも、バレない。」must be very large and bold — the hero copy
All Japanese perfectly rendered"""
    },
    {
        "index": 3,
        "filename": "banner_03_v3.png",
        "theme": "アクティブ — 理由提示",
        "headline": "一日中はいても、蒸れない理由がある。",
        "sub": "和紙40%の吸湿速乾。camifine®繊維が、足の蒸れを逃し続ける。",
        "prompt": """Create a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[EMOTIONAL CONCEPT]
Not a feature list — a promise with proof behind it.
Feeling: "Finally, something that actually works."

[VISUAL — Lifestyle outdoor scene]
Recreate this exact scene:
  - Two feet standing on outdoor stone/brick paving tiles
  - Wearing: light beige-gray/oatmeal Camicks ankle socks (ribbed texture visible above shoe)
  - Shoes: black Adidas-style running sneakers (black mesh upper, white sole)
  - Pants: dark indigo denim jeans, slightly cuffed at ankle
  - Background: outdoor, green foliage/plants behind
  - Shot from slightly above, looking down at feet
  - Natural sunlight, slightly warm tone
  - The socks look like completely normal ankle socks (flat instep, no toe bumps)

[TEXT OVERLAY]
Top of image — on dark semi-transparent band or directly over photo with white text:
HEADLINE (bold, large, white with slight shadow):
「一日中はいても、蒸れない理由がある。」

Below headline, three green rounded badge pills in a row:
「和紙40%」  「吸湿速乾」  「抗菌防臭」
(#66b780 green background, white text)

Bottom of image:
Sub text (white or light, medium):
「和紙40%の吸湿速乾。camifine®繊維が、足の蒸れを逃し続ける。」

Brand tag (tiny, bottom):
「Camicks | 和紙シークレット5本指ソックス」

[LAYOUT: 中央集中型]
Full-bleed lifestyle photo as background
Text overlaid top and bottom

[TEXT — CRITICAL]
Headline must be large, bold, readable over the photo
All Japanese perfectly rendered, no artifacts"""
    },
    {
        "index": 4,
        "filename": "banner_04_v3.png",
        "theme": "機能解説 — 問いかけ",
        "headline": "なぜ、外から見えないのか。",
        "sub": "外から見えないパーティション構造。足指を正しく配置し、甲はフラットに保つ。",
        "prompt": """Create a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[EMOTIONAL CONCEPT]
Satisfy curiosity. The viewer who saw Banner 1 now wants to know: "HOW does it work?"
This image answers that question with visual evidence.

[VISUAL LAYOUT]
Clean light green (#f0f7f2) or white background. Infographic style but with curiosity-driven headline.

TOP — Large headline:
「なぜ、外から見えないのか。」
Bold, large, dark green #2d5a3d
Creates a question that the image below answers

CENTER — Dual visual explanation:
LEFT side:
  - Close-up illustration or photo of the sock INTERIOR showing the partition structure
  - 5 individual toe pocket chambers visible from inside
  - Natural beige/oatmeal sock color
  - Circle callout label: 「パーティション構造」
  - Arrow pointing to the structure
  - Sub text: 「内側で5本指を分離」

RIGHT side:
  - The same sock EXTERIOR (instep view from above)
  - Completely flat, smooth, no toe contours visible
  - Circle or checkmark: 「外から見ると？」
  - The answer: completely normal flat sock
  - Sub text: 「外はフラット」

CENTER DIVIDER: Arrow or "→" showing inside → outside transformation

BOTTOM — Sub copy and features:
「外から見えないパーティション構造。足指を正しく配置し、甲はフラットに保つ。」
Small text, #555555

Below that, 4 feature badges in a row:
「和紙40%配合」「吸湿・速乾」「抗菌防臭」「日本製」
(small rounded rectangles, green #66b780 border, green text)

Brand tag: 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[COLOR PALETTE]
Background: very light green #f0f7f2
Headline: #2d5a3d dark green
Callout labels: #66b780 green
Text: #333333

[TEXT — CRITICAL]
「なぜ、外から見えないのか。」must be LARGE and prominent — it's the hook
All Japanese perfectly rendered"""
    },
    {
        "index": 5,
        "filename": "banner_05_v3.png",
        "theme": "品質 — 日本製の誇り",
        "headline": "日本製の丁寧さが、毎日に宿る。",
        "sub": "毛玉・穴あきが出にくい高耐久。洗濯機対応（30℃・ネット推奨）。",
        "prompt": """Create a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[EMOTIONAL CONCEPT]
Premium Japanese craftsmanship. Not just functional — beautifully made.
Feeling: "This is the kind of thing that's made with care."

[VISUAL]
MAIN VISUAL (upper 55% of frame):
  - Extreme close-up macro shot of sock fabric
  - Light gray or off-white Camicks sock
  - The ribbed vertical knit texture fills the frame beautifully
  - Shows the fine, high-quality yarn — individual fibers visible
  - Part of the ankle ribbing visible
  - Soft, professional studio lighting
  - White background, clean shadow
  - The fabric looks genuinely premium and carefully crafted

TOP-RIGHT corner — small quality badge:
Rounded rectangle: 「JAPAN MADE」or「日本製」with subtle flag element
Color: #2d5a3d green, white text

HEADLINE (over or above the macro photo):
「日本製の丁寧さが、毎日に宿る。」
Bold, dark green #2d5a3d, large

BOTTOM SECTION (white band, bottom 35%):
3 icons in a row with Japanese labels:

Left: washing machine icon
「洗濯機OK」
Sub: 30℃・ネット推奨

Center: sock with quality badge icon
「高耐久設計」
Sub: 毛玉・穴あきしにくい

Right: circular arrows icon
「型崩れしにくい」
Sub: 繰り返し使用OK

Sub copy below icons:
「毛玉・穴あきが出にくい高耐久。洗濯機対応（30℃・ネット推奨）。」
Small, #555555

Brand tag (tiny): 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[LAYOUT: Z型]
Top-left: headline, Top-right: Japan badge
Bottom-left: macro photo, Bottom-right: care icons

[COLOR PALETTE]
Background: white
Headline: #2d5a3d
Icons: #66b780
Care icons background: very light green tint

[TEXT — CRITICAL]
「日本製の丁寧さが、毎日に宿る。」large and premium-feeling
All Japanese perfectly rendered"""
    },
    {
        "index": 6,
        "filename": "banner_06_v3.png",
        "theme": "澤田権威 — 55年の本気",
        "headline": "55年分の本気が、1足に入ってる。",
        "sub": "1969年創業、大阪泉州・澤田株式会社。靴下だけを作り続けた技術が、これを可能にした。",
        "prompt": """Create a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[EMOTIONAL CONCEPT]
Authority and trust through heritage. This is not a trendy startup product.
55 years of sock manufacturing expertise is why the "secret" is possible.
Feeling: "This is backed by serious craftsmanship."

[VISUAL LAYOUT]
Sophisticated, heritage brand feel. Dark green tones. Artisanal quality.

TOP — Large headline (bold, white or cream on dark green header band):
「55年分の本気が、1足に入ってる。」
Dark background (#2d5a3d or #1a3d28), white text
This is the dominant element

CENTER — Split image:
LEFT half (60%):
  - Off-white/oatmeal Camicks sock on mannequin foot
  - Clean product photography, white background
  - Shows the sock elegantly — quality feel
  - The instep appears flat and smooth

RIGHT half (40%):
  - Industrial knitting machine (Shima Seiki style — modern white precision machinery)
  - Shows rows of sophisticated textile equipment
  - Slightly cropped, industrial but clean
  - Suggests precision manufacturing

Thin vertical divider line between the two halves

BOTTOM — Authority information band (light green #f0f7f2 or white):
「1969年創業、大阪泉州・澤田株式会社。」
Bold, medium size, dark green

Below that:
「靴下だけを作り続けた技術が、これを可能にした。」
Smaller, #555555

Small "SINCE 1969" text element (tasteful, small)

Brand tag: 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[COLOR PALETTE]
Header band: dark green #2d5a3d, white text
Background: white or very light
Authority text: #2d5a3d
Body text: #555555
Accent: #66b780

[TEXT — CRITICAL]
「55年分の本気が、1足に入ってる。」must be LARGE, bold, commanding
「1969年創業、大阪泉州・澤田株式会社。」clearly readable
All Japanese perfectly rendered, no blurring"""
    }
]

# ===========================================================
# 生成
# ===========================================================
print("\n" + "="*60)
print("🍌 NANO BANANA PRO — Banner v3 生成開始")
print("コンセプト: 「これが、5本指なんです。」")
print("="*60)

ok = 0
ng = 0
results = []

for config in BANNER_CONFIGS:
    fn = config['filename']
    fp = os.path.join(banner_dir, fn)

    if os.path.exists(fp) and os.path.getsize(fp) > 50000:
        print(f"  ⏭ Banner {config['index']:02d} スキップ（既存）")
        ok += 1
        results.append({'index': config['index'], 'status': 'skipped', 'file': fp})
        continue

    print(f"\n  🎨 Banner {config['index']:02d}: {config['theme']}")
    print(f"     「{config['headline']}」")

    for attempt in range(3):
        c = clients[(config['index'] - 1 + attempt) % len(clients)]
        try:
            resp = c.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=config['prompt'],
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
                print(f"     ⚠️ attempt {attempt+1}: データなし")
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
                results.append({'index': config['index'], 'status': 'error', 'error': str(e)[:200]})

    time.sleep(3)

print("\n" + "="*60)
print(f"📊 {ok}/{len(BANNER_CONFIGS)} OK, {ng}/{len(BANNER_CONFIGS)} NG")
print(f"📁 {banner_dir}/")
print("="*60)

with open(f'{out_dir}/v3_results.json', 'w', encoding='utf-8') as f:
    json.dump({'generated_at': datetime.now().isoformat(), 'ok': ok, 'ng': ng, 'results': results}, f, ensure_ascii=False, indent=2)
