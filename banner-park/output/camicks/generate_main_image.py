"""
Camicks Main Image — Amazonメイン画像生成
純白背景 × 商品主役 × テキストなし × Amazonポリシー準拠
複数パターン（角度・カラバリ）を一括生成
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
main_dir = f'{out_dir}/main_images'
os.makedirs(main_dir, exist_ok=True)

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
# メイン画像 定義
# ===========================================================
# Amazonメイン画像ルール:
# - 純白背景(#ffffff)のみ
# - 商品がフレームの85%以上を占める
# - テキスト・ウォーターマーク・グラフィック禁止
# - 商品を全体的に見せる（切り取り禁止）

MAIN_IMAGES = [
    {
        "index": 1,
        "filename": "main_01_darkgray_pair.png",
        "theme": "ダークグレー — ペア正面",
        "ref_images": ["camicks-s-dgy_detail.jpg", "camicks-s_darkgray.jpg"],
        "prompt": """I'm providing REFERENCE PHOTOS of the actual Camicks secret 5-toe socks in dark charcoal/darkgray color on mannequin feet.

Create a professional Amazon main product image, 1600x1600px, pure white background.

[AMAZON MAIN IMAGE RULES]
- Pure white background (#ffffff) — no gradients, no shadows on background
- Product must fill approximately 85% of the frame
- NO text, NO logos, NO watermarks, NO badges, NO graphics
- Show the complete product — nothing cut off at edges

[PRODUCT PRESENTATION]
Show a PAIR of the Camicks dark charcoal ankle socks:
- Both socks displayed on mannequin feet or as a folded/arranged pair
- Key angle: show the TOP/INSTEP view prominently — the completely FLAT, SMOOTH instep (no toe bumps visible) is the hero feature
- Secondary: slightly angled to show the ribbed cuff at the ankle
- The socks should look exactly like the reference photos: dark charcoal color, clean ribbed cuff, perfectly flat instep

[LIGHTING & STYLE]
- Clean, bright studio lighting — product photography quality
- Soft shadows only directly beneath the product (if using mannequin feet)
- No harsh shadows on the white background
- Colors true to the reference: deep charcoal/dark gray

[COMPOSITION]
- Centered in frame with generous white space around all edges
- Product pair arranged naturally — side by side or slightly overlapping
- Professional product photography aesthetic — Amazon premium listing quality

CRITICAL: Pure white background only. No text. No graphics. Show the complete flat instep — that is the product's defining visual feature."""
    },
    {
        "index": 2,
        "filename": "main_02_offwhite_pair.png",
        "theme": "オフホワイト — ペア正面",
        "ref_images": ["トリミング-レタッチ-_MG_7833.jpg", "トリミング-レタッチ-_MG_7824.jpg"],
        "prompt": """I'm providing REFERENCE PHOTOS of the actual Camicks secret 5-toe socks in off-white/cream/ivory color on a mannequin foot.

Create a professional Amazon main product image, 1600x1600px, pure white background.

[AMAZON MAIN IMAGE RULES]
- Pure white background (#ffffff) — no gradients, no shadows on background
- Product must fill approximately 85% of the frame
- NO text, NO logos, NO watermarks, NO badges, NO graphics
- Show the complete product — nothing cut off at edges

[PRODUCT PRESENTATION]
Show the Camicks off-white/cream ankle socks:
- Display as a clean pair on mannequin feet, or an elegantly folded pair
- PRIMARY ANGLE: Top-down or slightly angled view showing the COMPLETELY FLAT, SMOOTH instep — this is the hero visual feature
- Show the full sock: ribbed cuff, body, and flat instep all visible
- Color must match exactly: warm off-white/cream/ivory (not bright white, not yellow — a refined natural tone)

[LIGHTING & STYLE]
- Bright, clean studio lighting — luxury product photography
- Pure white background with minimal shadow directly under product
- Warm, soft lighting to show the off-white tone accurately
- No harsh reflections

[COMPOSITION]
- Centered composition, 85%+ frame fill
- Elegant, simple presentation — no props, no accessories
- White space evenly distributed on all sides
- If using mannequin feet: feet pointing slightly toward viewer to show instep clearly

CRITICAL: Pure white (#ffffff) background only. No text. No graphics. The flat instep must be clearly visible and recognizable as the product's defining feature."""
    },
    {
        "index": 3,
        "filename": "main_03_darkgray_top_angle.png",
        "theme": "ダークグレー — 真上アングル",
        "ref_images": ["camicks-s-dgy_detail.jpg", "camicks-s_detail04.jpg"],
        "prompt": """I'm providing REFERENCE PHOTOS of the actual Camicks secret 5-toe socks in dark charcoal color.

Create a professional Amazon main product image, 1600x1600px, pure white background.

[AMAZON MAIN IMAGE RULES]
- Pure white background (#ffffff)
- Product fills 85%+ of frame
- NO text, NO logos, NO watermarks, NO badges
- Complete product visible — nothing cut off

[PRODUCT PRESENTATION — HERO TOP-DOWN ANGLE]
Show ONE Camicks dark charcoal sock in a dramatic overhead/top-down angle:
- Camera directly above, looking straight down at the sock
- The sock is laid FLAT on pure white — showing the TOP SURFACE (instep) completely
- The instep should appear PERFECTLY FLAT AND SMOOTH — absolutely no toe bumps, no ridges visible from above
- This is the key visual moment: "it looks like a regular sock from the top"
- Ribbed cuff at top of frame, flat body leading down to toe area
- The sock fills 80-90% of the frame vertically

[LIGHTING & STYLE]
- Pure overhead studio lighting
- Crisp, clean — like a fashion magazine flat lay
- No shadows (or micro soft shadow around edges only)
- Deep, rich charcoal color — premium quality look

[COMPOSITION]
- Single sock, centered, vertical orientation
- Top (cuff) toward top of frame, toe toward bottom
- Pure white (#ffffff) surrounds entirely

CRITICAL: This angle MUST clearly show the completely flat instep — no toe bumps visible from above. That IS the product's hero feature. No text. No graphics."""
    },
    {
        "index": 4,
        "filename": "main_04_multicolor_lineup.png",
        "theme": "カラーバリエーション — ラインナップ",
        "ref_images": ["camicks-s_color.jpg", "camicks-s_darkgray.jpg"],
        "prompt": """I'm providing REFERENCE PHOTOS of the Camicks secret 5-toe socks showing color variations including dark charcoal and other colors.

Create a professional Amazon main product image, 1600x1600px, pure white background.

[AMAZON MAIN IMAGE RULES]
- Pure white background (#ffffff)
- Products fill 85%+ of frame
- NO text, NO logos, NO watermarks, NO badges
- Complete products visible

[PRODUCT PRESENTATION — COLOR LINEUP]
Show a neat lineup of multiple Camicks socks in different colors:
- Display 3-4 pairs arranged in a clean, organized row or grid
- Include: dark charcoal, off-white/cream, and any other colors from the reference
- All socks shown from the SAME ANGLE — top-down flat lay or standing on mannequin feet
- Consistent presentation: all showing the flat instep, all same scale

[ARRANGEMENT OPTIONS — choose the most photogenic]
Option A: 3-4 folded/cuffed socks laid flat in a horizontal row
Option B: 3-4 pairs on mannequin feet in a row, all pointing same direction
Option C: Grid arrangement (2×2) flat lay showing instep of each

[LIGHTING & STYLE]
- Even, consistent lighting across all colors
- No one color overexposed or underexposed
- Clean, professional — e-commerce hero image quality
- No props, no accessories

CRITICAL: Pure white background. No text. No graphics. Show the color variety clearly. Each sock's flat instep visible."""
    },
    {
        "index": 5,
        "filename": "main_05_lifestyle_foot.png",
        "theme": "ライフスタイル — 足元クローズアップ",
        "ref_images": ["トリミング-レタッチ-_MG_7833.jpg", "camicks-s-dgy_detail.jpg"],
        "prompt": """I'm providing REFERENCE PHOTOS of the actual Camicks socks — off-white on mannequin foot, and dark charcoal.

Create a professional Amazon main product image, 1600x1600px, pure white background.

[AMAZON MAIN IMAGE RULES]
- Pure white background (#ffffff)
- Product fills 85%+ of frame
- NO text, NO logos, NO watermarks, NO badges
- Complete product visible

[PRODUCT PRESENTATION — FOOT CLOSE-UP]
Show a close-up of the Camicks sock on a human foot (or realistic mannequin foot):
- Frame from mid-calf down to just past the toes
- The foot is raised slightly — like someone sitting and showing the bottom/side of their foot
- SOCK: dark charcoal or off-white Camicks sock, clearly showing the SMOOTH FLAT INSTEP
- The toe area completely smooth — no bumps visible whatsoever
- Show the elegant ribbed cuff at the ankle
- Background pure white

[FOOT ANGLE]
- Foot at 45-degree angle from viewer — side view showing both instep and cuff
- Slightly elevated — natural "showing off the sock" pose
- Leg in natural skin tone, no shoes

[LIGHTING & STYLE]
- Soft, flattering studio light
- Clean, beauty-campaign aesthetic
- Foot looks clean and natural (not clinical)
- Sock color vivid and true to reference

[COMPOSITION]
- Centered, with foot filling most of frame
- Upper part of frame: ankle/cuff visible
- Lower part: toe area visible, completely smooth

CRITICAL: Pure white background. No text. Flat smooth instep clearly visible."""
    }
]

# ===========================================================
# 生成実行
# ===========================================================
print("\n" + "="*60)
print("🖼️  Camicks メイン画像生成")
print("="*60)

ok = 0
ng = 0
results = []

for config in MAIN_IMAGES:
    fn = config['filename']
    fp = os.path.join(main_dir, fn)

    if os.path.exists(fp) and os.path.getsize(fp) > 50000:
        print(f"  ⏭ {config['index']:02d} スキップ（既存）")
        ok += 1
        results.append({'index': config['index'], 'status': 'skipped'})
        continue

    print(f"\n  🎨 Main {config['index']:02d}: {config['theme']}")
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
print(f"📊 {ok}/{len(MAIN_IMAGES)} OK, {ng}/{len(MAIN_IMAGES)} NG")
print(f"📁 {main_dir}/")
print("="*60)

with open(f'{out_dir}/main_results.json', 'w', encoding='utf-8') as f:
    json.dump({
        'generated_at': datetime.now().isoformat(),
        'ok': ok, 'ng': ng,
        'results': results
    }, f, ensure_ascii=False, indent=2)
