"""
Camicks Banner v2 — 実写素材ベース再生成スクリプト
実際の商品写真12枚を視覚分析し、超詳細プロンプトで6枚再生成
gemini-3-pro-image-preview × マルチモーダル入力
"""

import subprocess, os, time, json, glob, base64
from datetime import datetime

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[v.split('=')[0] if '=' in v else var] = v
        except: pass
    # Fix: load the actual key
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
    raise RuntimeError("GEMINI_API_KEY_1 が設定されていません。~/.zshrc を確認してください。")

clients = [genai.Client(api_key=k) for k in API_KEYS]
print(f"✅ API Keys: {len(API_KEYS)}本 確認")

slug = 'camicks'
out_dir = f'banner-park/output/{slug}'
banner_dir = f'{out_dir}/banners_v2'
os.makedirs(banner_dir, exist_ok=True)

# ===========================================================
# ソース素材パス（source_assets/ に保存済みか確認）
# ===========================================================
assets_dir = f'{out_dir}/source_assets'
asset_files = glob.glob(f'{assets_dir}/*.jpg') + glob.glob(f'{assets_dir}/*.jpeg') + glob.glob(f'{assets_dir}/*.png') + glob.glob(f'{assets_dir}/*.webp')
print(f"📁 ソース素材: {len(asset_files)}枚 検出")

def load_image(path):
    """画像ファイルをbase64バイトとして読み込む"""
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
    return data, mime

# ===========================================================
# Banner v2 プロンプト定義
# 実際の商品写真を視覚分析した超詳細版
# ===========================================================

BANNER_CONFIGS = [
    {
        "index": 1,
        "filename": "banner_01_v2.png",
        "hypothesis": "シークレット構造差別化（常識逆転）",
        "headline": "5本指なのに、足元に「指の跡」が出ない",
        "sub": "外見は普通のソックス。中身は5本指の健康設計。",
        "ref_asset_hint": "dark_gray_mannequin",  # ダークグレーマネキン
        "prompt": """You are creating a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks (Japanese brand, made in Japan).

[PRODUCT DESCRIPTION - CRITICAL FOR ACCURACY]
Camicks socks are ankle/quarter-crew length socks. The KEY feature: when worn, the INSTEP (top of foot) appears completely FLAT and SMOOTH — there are NO visible toe separations on the outside. The sock looks like a completely normal ankle sock from outside. It has a ribbed texture (縦リブ) throughout the ankle portion. Colors available: off-white (cream), light gray, dark charcoal, black, navy.

[IMAGE CONCEPT: Before vs After Comparison]
Create a clean side-by-side comparison on white background:

LEFT PANEL (labeled: 一般の5本指ソックス):
- Show a typical 5-toe sock worn on a mannequin foot
- The instep shows VISIBLE toe bumps/ridges (5 individual toe pockets bulging out)
- Dark charcoal color, ankle length
- Label with red X or "×" mark

RIGHT PANEL (labeled: Camicks):
- Show Camicks sock worn on a mannequin foot
- The instep is COMPLETELY FLAT — smooth, NO visible toe contours at all
- Same dark charcoal color, ankle length, ribbed texture
- Label with green checkmark "✓"
- A subtle callout arrow: 「甲がフラット」

[CENTER DIVIDER]
Large "VS" text in dark green (#2d5a3d) between the two panels

[LAYOUT: 中央集中型]
- Two sock images take up 70% of frame, centered
- Top area: headline text
- Bottom area: sub copy + brand tag

[JAPANESE TEXT - CRITICAL: Must be perfectly rendered]
TOP HEADLINE (bold, large, dark green #2d5a3d, Noto Sans JP style):
「5本指なのに、足元に「指の跡」が出ない」

MIDDLE LABEL LEFT (red, medium): 一般の5本指ソックス
MIDDLE LABEL RIGHT (green #66b780, medium): Camicks ✓

BOTTOM SUB (smaller, dark gray):
「外見は普通のソックス。中身は5本指の健康設計。」

BRAND TAG (smallest, bottom center, green):
「Camicks | 和紙シークレット5本指ソックス | marusawa」

[COLOR SCHEME]
Background: pure white #ffffff
Headline: dark green #2d5a3d
Accent elements: medium green #66b780
Left panel label: warm red
Right panel label: #66b780 green

[QUALITY REQUIREMENTS]
- White Amazon-style background
- All Japanese text perfectly legible, no blurring, no errors
- Clean professional product photography style
- Minimum 5% margin from edges
- No watermarks, no stock photo marks""",
        "use_ref_image": False
    },
    {
        "index": 2,
        "filename": "banner_02_v2.png",
        "hypothesis": "ローファー・オフィス共感",
        "headline": "オフィスでも使える、バレない5本指",
        "sub": "ローファーでも、フラットシューズでも。靴を脱いでも普通に見える。",
        "prompt": """You are creating a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[PRODUCT DESCRIPTION]
Camicks ankle socks: when worn, the instep (top of foot) is completely flat — looks like normal socks outside. Ribbed vertical texture. Off-white/cream color option available. Short ankle-length height.

[IMAGE CONCEPT: Office/Loafer Scene]
Elegant foot photo in professional setting:
- Mannequin foot or model foot wearing OFF-WHITE (cream) Camicks ankle socks
- With dark leather loafers (one shoe slightly removed/half off to show the sock)
- Clean light wood floor or white/light gray background
- Natural, soft lighting — fashion magazine style
- The sock instep appears completely smooth and flat, just like a regular sock
- Shot from a 45-degree angle showing both the ankle and the toe area
- Elegant and understated — office-appropriate aesthetic

[LAYOUT: Z型]
TOP-LEFT: Large headline in dark green
TOP-RIGHT: Small icon cluster (office building icon, loafer icon)
BOTTOM-LEFT: The foot/sock/shoe photograph (main visual, 60% of frame)
BOTTOM-RIGHT: Brand tag + sub copy

[JAPANESE TEXT - CRITICAL: perfectly rendered]
HEADLINE (bold, large, dark green #2d5a3d):
「オフィスでも使える、バレない5本指」

SUB TEXT (smaller):
「ローファーでも、フラットシューズでも。靴を脱いでも普通に見える。」

SMALL BADGE (rounded rectangle, green #66b780, white text):
「靴を脱いでもバレない」

BRAND TAG (tiny, bottom right):
「Camicks | 和紙シークレット5本指ソックス」

[COLOR SCHEME]
Background: clean white #ffffff
Text: dark green #2d5a3d
Accents: #66b780 medium green
Sock color in image: cream/off-white

[QUALITY]
- Amazon white background style
- Perfect Japanese text rendering
- Premium product photo feel — fashion magazine quality
- No clutter, clean and minimal""",
        "use_ref_image": False
    },
    {
        "index": 3,
        "filename": "banner_03_v2.png",
        "hypothesis": "スニーカー・アクティブ共感",
        "headline": "歩き回っても蒸れない、ズレない",
        "sub": "和紙40%の吸湿速乾。ウォーキング・ヨガ・立ち仕事にも。",
        "prompt": """You are creating a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[PRODUCT DESCRIPTION]
Camicks ankle socks in light beige-gray/oatmeal color, short ankle length with ribbed texture. The sock is worn with black Adidas running sneakers. Looks like normal socks from outside (flat instep, no toe bumps visible).

[IMAGE CONCEPT: Active Outdoor Scene - Based on actual product photo]
Recreate this scene VERY CLOSELY:
- Two feet standing on outdoor stone/brick paving tiles
- Wearing: Light beige-gray (natural/oatmeal tone) Camicks ankle socks — ribbed texture visible above shoe
- Shoes: Black Adidas-style running sneakers (black mesh upper, white sole)
- Pants: Dark blue denim jeans, cuffed/rolled up slightly at ankle
- Background: Outdoor scene with green foliage/plants behind
- The sock ankle portion (~3-4cm) is visible above the shoe collar
- Socks appear as completely normal ankle socks — no toe separation visible
- Shot from above/slightly angled down looking at feet

[LAYOUT: 中央集中型]
- Main visual (feet photo) takes up 70% center of frame
- Top area: headline overlay on photo or on white band
- Bottom area: sub copy + feature badges

[JAPANESE TEXT - CRITICAL]
HEADLINE (bold, large, white or dark green, high contrast with background):
「歩き回っても蒸れない、ズレない」

FEATURE BADGES (3 small rounded rectangles, green #66b780, white text):
「和紙40%」 「吸湿速乾」 「抗菌防臭」

SUB TEXT:
「和紙40%の吸湿速乾。ウォーキング・ヨガ・立ち仕事にも。」

BRAND TAG (bottom):
「Camicks | 和紙シークレット5本指ソックス」

[COLOR SCHEME]
Primary accent: green #66b780
Text overlay: white with dark shadow, or on white band
Background: the outdoor lifestyle photo

[QUALITY]
- Lifestyle photography style — natural and authentic
- Perfect Japanese text
- The socks should look genuinely normal/casual, not medical""",
        "use_ref_image": False
    },
    {
        "index": 4,
        "filename": "banner_04_v2.png",
        "hypothesis": "素材・機能インフォグラフィック（根拠訴求）",
        "headline": "和紙40%が、足の蒸れをリセットする",
        "sub": "吸湿・速乾・抗菌防臭。大阪泉州、1969年創業の老舗が編む日本製。",
        "prompt": """You are creating a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[IMAGE CONCEPT: Feature Infographic]
Clean, informational product image showing the 4 key features:

CENTER: Product photo of gray Camicks ankle sock on mannequin foot (side view, white background). The sock has visible ribbed texture on the ankle band, and the instep appears completely smooth/flat.

FOUR FEATURE BOXES (one in each corner area, with icon + Japanese text):
TOP-LEFT:
  Icon: Japanese washi paper / leaf symbol (light green)
  Text: 「和紙40%配合」
  Sub: 吸湿性・速乾性

TOP-RIGHT:
  Icon: water droplet / speed arrow (blue-green)
  Text: 「吸湿・速乾」
  Sub: camifine®繊維使用

BOTTOM-LEFT:
  Icon: shield / protection symbol (green)
  Text: 「抗菌防臭」
  Sub: 長時間快適

BOTTOM-RIGHT:
  Icon: Japan map outline or "JAPAN" flag element (red/white)
  Text: 「日本製」
  Sub: 大阪泉州 1969年創業

LAYOUT: F型
- Top horizontal band: large headline
- Central product image
- Four corner feature callouts with connecting lines to product
- Bottom band: sub copy + brand

[JAPANESE TEXT - CRITICAL]
HEADLINE (top, bold, large, dark green #2d5a3d):
「和紙40%が、足の蒸れをリセットする」

FEATURE LABELS (each box, medium, dark):
「和紙40%配合」「吸湿・速乾」「抗菌防臭」「日本製」

SUB TEXT (bottom):
「吸湿・速乾・抗菌防臭。大阪泉州、1969年創業の老舗が編む日本製。」

BRAND TAG: 「Camicks | 和紙シークレット5本指ソックス | marusawa」

[COLOR SCHEME]
Background: very light green #f0f7f2 or pure white
Feature box borders: #66b780 green
Headline: #2d5a3d dark green
Icons: #66b780 or #4a9e6b
Text: #333333 charcoal

[QUALITY]
- Clean infographic design
- All Japanese text perfectly rendered
- Professional Amazon product image style
- Not cluttered — each feature has breathing room""",
        "use_ref_image": False
    },
    {
        "index": 5,
        "filename": "banner_05_v2.png",
        "hypothesis": "カラーバリエーション・コーデ訴求",
        "headline": "全15色。おしゃれを犠牲にしない5本指。",
        "sub": "今日の気分や服で選べる豊富なカラー。ギフトにも最適。",
        "prompt": """You are creating a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[PRODUCT DESCRIPTION - CRITICAL FOR ACCURACY]
Recreate the EXACT appearance of Camicks socks as seen in product photos:
- Short ankle-length socks
- Slightly textured/bumpy fabric on the body (not completely smooth — subtle looped texture)
- Ribbed cuff/top band (vertical ribbing on the ankle portion)
- The toe area is slightly separated into 5 individual toe pockets (visible from below, but NOT visible from top/instep)
- The instep (top) appears flat and normal

[IMAGE CONCEPT: 4-Color Flat Lay]
Recreate this EXACT composition (based on actual product photo):
- 4 Camicks socks laid flat on pure white background
- Arranged in a row, evenly spaced, slightly angled (not perfectly vertical)
- Each sock laid with the heel down, showing the full length from cuff to toe
- The toe area shows subtle 5-pocket separation at the very bottom
- Socks appear to have a slightly textured, natural fabric quality

COLORS (left to right):
1. OFF-WHITE / cream (#f5f0e8 range) — labeled: 「オフ」
2. LIGHT GRAY (#c8c5bc range) — labeled: 「グレー」
3. DARK CHARCOAL (#504f51 range) — labeled: 「ダークグレー」
4. BLACK (#1a1a1a) — labeled: 「ブラック」

Color labels: elegant thin Japanese text BELOW each sock, with small arrow pointing up

[LAYOUT: 中央集中型]
- 4 socks take up 60% of center frame
- Top area: large headline
- Below socks: color labels
- Bottom band: sub copy + badge + brand tag

[JAPANESE TEXT - CRITICAL]
HEADLINE (bold, large, dark green #2d5a3d):
「全15色。おしゃれを犠牲にしない5本指。」

COLOR LABELS (thin, charcoal, below each sock):
「オフ」「グレー」「ダークグレー」「ブラック」

BADGE (green rounded rect): 「全15色展開」

SUB TEXT:
「今日の気分や服で選べる豊富なカラー。ギフトにも最適。」

BRAND TAG: 「Camicks | 和紙シークレット5本指ソックス」

[COLOR SCHEME]
Background: pure white #ffffff (Amazon style)
Headline: dark green #2d5a3d
Badge: #66b780 green, white text
Labels: #555555 charcoal

[QUALITY]
- Professional flat lay product photography
- Perfect Japanese text, especially color names
- Clean, minimal, premium feel
- The 4 sock colors must be clearly distinguishable""",
        "use_ref_image": False
    },
    {
        "index": 6,
        "filename": "banner_06_v2.png",
        "hypothesis": "品質・耐久性・ケア安心感",
        "headline": "洗濯を繰り返しても、型崩れしない",
        "sub": "毛玉・穴あきが出にくい高耐久。洗濯機対応（30℃・ネット推奨）。",
        "prompt": """You are creating a professional 1600x1600px Amazon product sub-image for Camicks Secret 5-Toe Socks.

[PRODUCT DESCRIPTION]
Camicks sock in light gray/off-white: the fabric shows a beautiful ribbed knit texture (縦リブ). Fine, high-quality knit with visible individual yarn loops. The toe area shows 5 separated sections. Appears handcrafted/artisanal quality.

[IMAGE CONCEPT: Quality & Durability Focus]
This image emphasizes the premium fabric quality:

MAIN VISUAL (upper 60%):
Extreme close-up (macro) of the sock fabric texture:
- Light gray or off-white Camicks sock
- Focus on the ribbed ankle band — shows fine vertical ribbing
- Part of the toe area visible, showing the individual toe pocket structure
- Beautiful, detailed knit pattern — like a fine textile photograph
- Soft, diffused lighting showing fabric depth and texture
- Background: pure white

LOWER SECTION (bottom 40%):
Clean infographic band showing care/durability info:
3 icons in a row:

Left icon: washing machine (洗濯機)
Text: 「洗濯機OK」
Sub: 30℃・ネット推奨

Center icon: sock with quality badge (耐久)
Text: 「高耐久設計」
Sub: 毛玉・穴あきしにくい

Right icon: shape/form preservation
Text: 「型崩れしにくい」
Sub: 繰り返し使用OK

[LAYOUT: Z型]
TOP-LEFT: Headline on white band above the fabric close-up
TOP-RIGHT: Sub text / quality badge
BOTTOM-LEFT: The fabric macro photo
BOTTOM-RIGHT: Brand tag + care icons

[JAPANESE TEXT - CRITICAL]
HEADLINE (bold, large, dark green #2d5a3d):
「洗濯を繰り返しても、型崩れしない」

CARE ICON LABELS (medium, dark):
「洗濯機OK」「高耐久設計」「型崩れしにくい」

SUB TEXT:
「毛玉・穴あきが出にくい高耐久。洗濯機対応（30℃・ネット推奨）。」

BRAND TAG (tiny, bottom):
「Camicks | 和紙シークレット5本指ソックス | marusawa」

[COLOR SCHEME]
Background: white #ffffff
Headline: #2d5a3d dark green
Icons and accents: #66b780 medium green
Fabric in photo: light gray or off-white natural tone

[QUALITY]
- Macro photography style — shows luxury of the fabric
- All Japanese text perfectly rendered
- Clean infographic section
- Premium, craftsmanship feel""",
        "use_ref_image": False
    }
]

# ===========================================================
# Phase 4: Nano Banana Pro 生成
# ===========================================================
print("\n" + "="*60)
print("🍌 NANO BANANA PRO — Banner v2 生成開始")
print("="*60)

ok = 0
ng = 0
results = []

for config in BANNER_CONFIGS:
    fn = config['filename']
    fp = os.path.join(banner_dir, fn)

    if os.path.exists(fp) and os.path.getsize(fp) > 50000:
        print(f"  ⏭ Banner {config['index']:02d} スキップ（既存）: {fn}")
        ok += 1
        results.append({'index': config['index'], 'status': 'skipped', 'file': fp})
        continue

    print(f"\n  🎨 Banner {config['index']:02d}: {config['hypothesis']}")
    print(f"     見出し: {config['headline']}")

    prompt = config['prompt']

    for attempt in range(3):
        c = clients[(config['index'] - 1 + attempt) % len(clients)]
        try:
            resp = c.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=prompt,
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
                print(f"     ⚠️ attempt {attempt+1}: 画像データなし or 小さすぎ ({len(img_data) if img_data else 0} bytes)")
                if attempt < 2:
                    time.sleep(5)
                    continue
                ng += 1
                results.append({'index': config['index'], 'status': 'failed', 'file': None})
                break

            with open(fp, 'wb') as f:
                f.write(img_data)

            size_kb = len(img_data) // 1024
            print(f"     ✅ 生成成功: {fn} ({size_kb}KB)")
            ok += 1
            results.append({'index': config['index'], 'status': 'ok', 'file': fp, 'size_kb': size_kb})
            break

        except Exception as e:
            print(f"     ❌ attempt {attempt+1} エラー: {str(e)[:120]}")
            if attempt < 2:
                time.sleep(8)
            else:
                ng += 1
                results.append({'index': config['index'], 'status': 'error', 'error': str(e)[:200], 'file': None})

    time.sleep(3)

# ===========================================================
# 結果サマリー
# ===========================================================
print("\n" + "="*60)
print(f"📊 生成結果: {ok}/{len(BANNER_CONFIGS)} OK, {ng}/{len(BANNER_CONFIGS)} NG")
print("="*60)

for r in results:
    status_icon = {'ok': '✅', 'skipped': '⏭', 'failed': '❌', 'error': '❌'}.get(r['status'], '?')
    size_str = f"({r.get('size_kb')}KB)" if r.get('size_kb') else ''
    print(f"  {status_icon} Banner {r['index']:02d}: {r['status']} {size_str}")

print(f"\n📁 出力先: {banner_dir}/")
print("完了！")

# 結果保存
with open(f'{out_dir}/v2_generation_results.json', 'w', encoding='utf-8') as f:
    json.dump({
        'generated_at': datetime.now().isoformat(),
        'total': len(BANNER_CONFIGS),
        'ok': ok,
        'ng': ng,
        'results': results
    }, f, ensure_ascii=False, indent=2)
