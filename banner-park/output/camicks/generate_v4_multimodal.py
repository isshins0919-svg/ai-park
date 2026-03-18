"""
Camicks Banner v4 — 実写素材マルチモーダル入力版
実際の商品写真をGeminiへ直接渡して生成精度を最大化
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
assets_dir = f'{out_dir}/source_assets'
banner_dir = f'{out_dir}/banners_v4'
os.makedirs(banner_dir, exist_ok=True)

def load_img(filename):
    path = os.path.join(assets_dir, filename)
    if not os.path.exists(path):
        print(f"  ⚠️ 素材なし: {filename}")
        return None, None
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}.get(ext, 'image/jpeg')
    return data, mime

def make_part(filename):
    data, mime = load_img(filename)
    if data:
        return types.Part.from_bytes(data=data, mime_type=mime)
    return None

# ===========================================================
# Banner 定義（各バナー: 実写素材 + テキストプロンプト）
# ===========================================================

BANNERS = [
    {
        "index": 1,
        "filename": "banner_01_v4.png",
        "theme": "シークレット構造 — 種明かし",
        "headline": "これが、5本指なんです。",
        "ref_images": ["camicks-s-dgy_detail.jpg"],
        "prompt": """I'm providing a REFERENCE PHOTO of the actual Camicks sock product. Use it as the visual reference for the RIGHT side of the comparison.

Create a professional 1600x1600px Amazon product sub-image.

[CONCEPT: Before vs After reveal]
The headline delivers the "WOW" moment: people can't believe this is a 5-toe sock.

[LAYOUT]
White background (#ffffff).

TOP: Large bold headline
「これが、5本指なんです。」
Font: bold rounded Japanese sans-serif, dark green #2d5a3d, very large, full width

CENTER: Side-by-side comparison

LEFT PANEL — 「一般の5本指ソックス」(red label):
- Dark charcoal ankle sock on mannequin foot
- VISIBLE toe bumps/ridges on the instep — 5 individual toe pockets clearly protruding
- Red × mark below

CENTER: Large green "VS"

RIGHT PANEL — 「Camicks ✓」(green label):
- EXACTLY the sock from the reference photo (dark charcoal ankle sock, ribbed cuff, FLAT smooth instep — NO visible toe contours on top)
- Small arrow callout: 「甲がフラット」pointing to the flat instep area
- Green ✓ mark below

BOTTOM:
Bold medium text: 「5本指には、見えません。」 (#2d5a3d)
Smaller: 「外見は普通のソックス。中身は5本指の健康設計。」
Tiny brand tag: 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[COLORS]
Background: white
Headline/brand: dark green #2d5a3d
Camicks label: #66b780
Left label: warm red

[CRITICAL]
All Japanese text pixel-perfect. Headline VERY large and dominant. The flat instep on the right must look exactly like the reference photo."""
    },
    {
        "index": 2,
        "filename": "banner_02_v4.png",
        "theme": "オフィス — 解放",
        "headline": "脱いでも、バレない。",
        "ref_images": ["トリミング-レタッチ-_MG_7833.jpg"],
        "prompt": """I'm providing a REFERENCE PHOTO of the actual Camicks sock (off-white/cream color on mannequin). Use this exact sock as the product shown in the image.

Create a professional 1600x1600px Amazon product sub-image.

[CONCEPT]
The relief of not worrying when taking off shoes. Quiet confidence.

[LAYOUT: Split — photo left, text right]

LEFT HALF (60%):
- The exact off-white Camicks sock from the reference photo on a mannequin foot
- Add a black leather penny loafer next to/beside the foot (as if just removed)
- Light wood floor or soft neutral background
- Soft warm lighting — fashion magazine style
- The sock instep appears completely smooth and flat (matching reference)

RIGHT HALF (40%, white background):
Top: small icon of office building + loafer in dark green

Headline (bold, large, dark green #2d5a3d):
「脱いでも、
バレない。」
(two lines, very large)

Sub text (#555555):
「ローファーでも、フラットシューズでも。
靴を脱いでも普通に見える。」

Green rounded badge (#66b780, white text):
「靴を脱いでもバレない」

Brand tag (tiny, bottom right):
「Camicks | 和紙シークレット5本指ソックス」

[COLORS]
Headline: #2d5a3d | Badge: #66b780 | Background right: white

[CRITICAL]
Headline must be VERY LARGE — dominant element on right side. All Japanese perfect."""
    },
    {
        "index": 3,
        "filename": "banner_03_v4.png",
        "theme": "アクティブ — 理由提示",
        "headline": "一日中はいても、蒸れない理由がある。",
        "ref_images": ["IMG_8829.jpg"],
        "prompt": """I'm providing the ACTUAL LIFESTYLE PHOTO to use as the main visual. Recreate this scene faithfully: person wearing Camicks socks (light beige-gray) with black Adidas sneakers, denim jeans cuffed, standing on stone paving tiles with green plants/bushes in background.

Create a professional 1600x1600px Amazon product sub-image using this lifestyle scene.

[CONCEPT]
A promise backed by reason. "Finally, socks that actually solve the sweating problem."

[LAYOUT]
The lifestyle photo fills most of the frame (use it directly, crop to 1:1).

TOP OVERLAY on photo:
Headline (bold, large, white with dark shadow for readability):
「一日中はいても、蒸れない理由がある。」

Below headline — three green pill badges (#66b780, white text):
「和紙40%」　「吸湿速乾」　「抗菌防臭」

BOTTOM BAND (semi-transparent dark overlay or white band):
Sub text:
「和紙40%の吸湿速乾。camifine®繊維が、足の蒸れを逃し続ける。」

Brand tag (tiny):
「Camicks | 和紙シークレット5本指ソックス」

[CRITICAL]
Keep the lifestyle photo as authentic as possible — it's a real product photo.
Headline very large. All Japanese perfect."""
    },
    {
        "index": 4,
        "filename": "banner_04_v4.png",
        "theme": "機能解説 — 問いかけ",
        "headline": "なぜ、外から見えないのか。",
        "ref_images": ["camicks-women-inside.jpg", "camicks-s-dgy_detail.jpg"],
        "prompt": """I'm providing TWO reference photos:
1. FIRST IMAGE: Interior of the Camicks sock showing the partition structure — 5 individual toe chambers visible from inside (beige/natural color, laid flat showing the openings)
2. SECOND IMAGE: Exterior view of the sock on mannequin foot — completely flat, smooth instep visible

Use these as the main visuals for an explanatory infographic.

Create a professional 1600x1600px Amazon product sub-image.

[CONCEPT]
Answer the curiosity: "HOW does it hide the 5 toes?"

[LAYOUT]
Very light green background (#f0f7f2).

TOP: Large headline
「なぜ、外から見えないのか。」
Bold, dark green #2d5a3d, very large

CENTER: Two-image explanation side by side

LEFT (from first reference photo — sock interior):
- Show the interior partition structure photo
- Circle callout bubble: 「パーティション構造」
- Label below: 「内側で5本指を分離」

Arrow → pointing right

RIGHT (from second reference photo — exterior flat view):
- Show the exterior mannequin photo with flat instep
- Checkmark callout: 「外から見ると？」
- Label below: 「甲はフラット」

BOTTOM:
Sub text:
「外から見えないパーティション構造。足指を正しく配置し、甲はフラットに保つ。」

Four small feature badges in a row:
「和紙40%配合」「吸湿・速乾」「抗菌防臭」「日本製」

Brand tag: 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[CRITICAL]
The actual reference photos should be prominently featured.
All Japanese text perfect. Headline dominant."""
    },
    {
        "index": 5,
        "filename": "banner_05_v4.png",
        "theme": "品質 — 日本製の誇り",
        "headline": "日本製の丁寧さが、毎日に宿る。",
        "ref_images": ["camicks-s-gy_detail-b.jpg"],
        "prompt": """I'm providing a REFERENCE PHOTO: extreme close-up of the Camicks sock toe area showing the beautiful ribbed knit texture in light gray/silver-white color. The fabric shows fine vertical ribbing and high-quality yarn construction.

Create a professional 1600x1600px Amazon product sub-image.

[CONCEPT]
Premium Japanese craftsmanship. Beautifully and carefully made.

[LAYOUT]

TOP SECTION (upper 50%):
- The reference fabric close-up photo fills this area
- Natural, slightly warm lighting showing the fabric depth
- Top-right corner: badge reading 「JAPAN MADE 日本製」with subtle Japanese flag colors

HEADLINE overlaid on or above the photo:
「日本製の丁寧さが、毎日に宿る。」
Bold, dark green #2d5a3d, large

BOTTOM SECTION (lower 40%, white background):
Three icons in a row:

Left: 🫧 washing machine icon
「洗濯機OK」
Sub: 30℃・ネット推奨

Center: sock quality icon
「高耐久設計」
Sub: 毛玉・穴あきしにくい

Right: circular arrows
「型崩れしにくい」
Sub: 繰り返し使用OK

Sub copy:
「毛玉・穴あきが出にくい高耐久。洗濯機対応（30℃・ネット推奨）。」

Brand tag: 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[CRITICAL]
The fabric macro photo must look luxurious and premium.
All Japanese text perfect. Clean, premium feel."""
    },
    {
        "index": 6,
        "filename": "banner_06_v4.png",
        "theme": "澤田権威 — 55年の本気",
        "headline": "55年分の本気が、1足に入ってる。",
        "ref_images": ["camicks-women_detail03.jpg", "marusawa-logo.jpeg"],
        "prompt": """I'm providing TWO reference images:
1. FIRST IMAGE: Product + factory image — shows Camicks sock on mannequin (beige/natural, 5-toe visible from front) alongside a photo of professional Shima Seiki knitting machines in a modern factory
2. SECOND IMAGE: The "marusawa" brand logo (clean wordmark in dark brown/black)

Create a professional 1600x1600px Amazon product sub-image using these as the main visuals.

[CONCEPT]
Authority through heritage. 55 years of expertise is WHY this product is possible.

[LAYOUT]
Sophisticated, premium feel.

TOP HEADER BAND (dark green #2d5a3d, full width):
Headline in white, bold, large:
「55年分の本気が、1足に入ってる。」

CENTER (use the first reference image):
- The factory + sock image fills the center area
- Left: the Camicks sock on mannequin
- Right: the professional Shima Seiki knitting machines

BOTTOM INFO BAND (white or very light):
Large bold text (dark green):
「1969年創業、大阪泉州・澤田株式会社。」

Medium text below (#555555):
「靴下だけを作り続けた技術が、これを可能にした。」

Small text: 「SINCE 1969」

The marusawa logo (from second reference image) placed bottom-right, small size

Brand tag tiny:
「Camicks | 和紙シークレット5本指ソックス | marusawa」

[CRITICAL]
Dark green header with headline must feel authoritative and trustworthy.
The actual factory photo should be clearly visible.
marusawa logo must appear exactly as in the reference.
All Japanese text perfect."""
    }
]

# ===========================================================
# 生成実行
# ===========================================================
print("\n" + "="*60)
print("🍌 NANO BANANA PRO v4 — 実写素材マルチモーダル生成")
print("="*60)

ok = 0
ng = 0
results = []

for config in BANNERS:
    fn = config['filename']
    fp = os.path.join(banner_dir, fn)

    if os.path.exists(fp) and os.path.getsize(fp) > 50000:
        print(f"  ⏭ Banner {config['index']:02d} スキップ（既存）")
        ok += 1
        results.append({'index': config['index'], 'status': 'skipped'})
        continue

    print(f"\n  🎨 Banner {config['index']:02d}: {config['theme']}")
    print(f"     「{config['headline']}」")
    print(f"     素材: {', '.join(config['ref_images'])}")

    # マルチモーダルコンテンツ構築
    contents = []
    loaded_imgs = 0
    for img_fn in config['ref_images']:
        part = make_part(img_fn)
        if part:
            contents.append(part)
            loaded_imgs += 1
    contents.append(config['prompt'])
    print(f"     参照画像: {loaded_imgs}枚 読み込み済み")

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
print(f"📊 {ok}/{len(BANNERS)} OK, {ng}/{len(BANNERS)} NG")
print(f"📁 {banner_dir}/")
print("="*60)

with open(f'{out_dir}/v4_results.json', 'w', encoding='utf-8') as f:
    json.dump({'generated_at': datetime.now().isoformat(), 'ok': ok, 'ng': ng, 'results': results}, f, ensure_ascii=False, indent=2)
