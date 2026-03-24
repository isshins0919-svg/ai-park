"""
Camicks Amazon サブ画像 v3b
サブ⑤ × サブ⑥ 再生成

⑤ ビジュアル全振り。コピー1行だけ、あとは画像に委ねる
⑥ 糸巻き × 完成品。「糸屋」の権威を視覚化
"""

import subprocess, os, time
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
v3b_dir = f'{out_dir}/amazon_v3b'
os.makedirs(v3b_dir, exist_ok=True)

NEW_LOGO_PATH = '/Users/ca01224/Desktop/Camicks読み込み用(Claude code)/新marusawa_logo.png'

def load_asset(filename):
    path = os.path.join(assets_dir, filename)
    if not os.path.exists(path):
        print(f"  ⚠️ 素材なし: {filename}")
        return None
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png'}.get(ext,'image/jpeg')
    return types.Part.from_bytes(data=data, mime_type=mime)

def load_logo():
    path = NEW_LOGO_PATH
    if not os.path.exists(path):
        path = os.path.join(assets_dir, 'marusawa_logo.png')
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        data = f.read()
    return types.Part.from_bytes(data=data, mime_type='image/png')

DESIGN_SYSTEM = """
[CAMICKS BRAND — v3b]
BRAND POSITION: Fashion-first × ¥2,000 premium. NOT a functional sock brand.
COLOR: accent #3ABCEE lines only / headline #1a2e3d / background #ffffff or #fafaf8
TYPOGRAPHY: elegant MINCHO/SERIF — minimal text, maximum visual impact
STRICTLY FORBIDDEN: infographic style, blue glowing bubbles, cluttered text, medical feel
"""

SPECS = [
    {
        "index": 5,
        "filename": "amazon_05_scene_v3b.png",
        "label": "サブ⑤｜ビジュアル全振り「脱いだ後も、おしゃれ。」",
        "assets": [
            "camicks-women_detail01.jpg",
            "camicks-women_detail02.jpg",
            "トリミング-レタッチ-_MG_7824.jpg",
            "トリミング-レタッチ-_MG_7833.jpg",
        ],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 05 v3b — ほぼ全部ビジュアル。テキスト最小限。]

CORE CONCEPT:
This image should feel like a page from a Japanese fashion magazine.
The sock IS the fashion item. No explanation needed. The image speaks for itself.
Target emotion: "I want this. This is beautiful."

VISUAL DIRECTION (最重要):
- A woman in an elegant, casual outfit has just removed her shoes at an entrance foyer
- The socks are FULLY VISIBLE and look completely stylish — like a deliberate fashion choice
- The overall composition: clean Japanese interior, natural warm light, effortless style
- Sock colors shown: dark navy or black (the premium colors)
- The photo should look like it belongs in a high-end lifestyle magazine
- NO clinical product photography. NO white background product shot.
- Fashion editorial: candid, warm, real-life moment, beautifully lit

IMPORTANT VISUAL RULES:
- The sock must look like a NORMAL, STYLISH sock — NOT like a 5-toe sock
- Show the full sock silhouette — it should look sleek and elegant
- Woman's styling: minimal, clean, fashionable (not sporty, not casual-casual)
- Composition: generous white space, off-center, asymmetric is fine
- Color palette of the scene: muted, sophisticated (cream, navy, warm wood tones)

TEXT — ABSOLUTE MINIMUM:
Place ONLY this one line of Japanese text, small and elegant:
  「脱いだ後も、おしゃれ。」 — mincho, small size, positioned subtly (bottom-left or bottom-right)

Also add, even smaller:
  「23cm〜27cm / メンズ・レディース兼用」 — very small, bottom area

NO OTHER TEXT. No bullet points. No feature explanations. No brand name needed here.
The image carries 95% of the communication.

FINAL CHECK: Would this image look at home in Vogue Japan or Casa BRUTUS?
If yes, it's correct. If it looks like an Amazon product page, regenerate.
"""
    },
    {
        "index": 6,
        "filename": "amazon_06_brand_v3b.png",
        "label": "サブ⑥｜糸屋の権威「57年分の本気が、一足に。」",
        "assets": [
            "camicks-s_color.jpg",
            "camicks_men_400x1000_09.jpg",
            "camicks-s_detail04.jpg",
        ],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 06 v3b — 糸屋の権威 × 老舗の温かみ]

CORE CONCEPT:
Sawada was founded in 1969 as a YARN company — not a sock company.
They obsess over thread before the sock even exists.
This image must show the JOURNEY: from yarn to finished sock.
The visual says: "57 years of caring about thread. That's why this sock is different."

VISUAL DIRECTION (最重要):
PRIMARY VISUAL: Colorful yarn spools / thread cones in warm, natural light
  → The yarn should feel artisanal, premium, Japanese craft
  → Rich, warm colors: navy, deep teal, ivory, charcoal — the 4 Amazon colors
  → Background: warm white or natural wood surface

SECONDARY ELEMENT: The finished Camicks sock placed alongside the yarn
  → Shows the connection: THIS yarn became THAT sock
  → Like a craftsman's studio — raw material and finished product coexist

LIGHTING & ATMOSPHERE:
  → Warm, golden-hour-quality light (NOT harsh studio light)
  → Depth of field: yarns in front sharp, soft background
  → Japanese atelier / traditional craft workshop feeling
  → "老舗" (long-established artisan) aesthetic — not modern factory, not industrial

LAYOUT:
  → Full-bleed photography fills most of the frame
  → Text overlaid elegantly on a clean area (top or bottom)
  → Deep navy (#1a2e3d) text area OR text directly on the warm background if contrast allows

JAPANESE TEXT (perfectly rendered, mincho):
  HEADLINE (large, bold): 「57年分の本気が、一足に。」
  SUB (medium): 「1969年創業。糸屋として始まり、糸から作り続けてきた。」
  FACTS (small, elegant):
    「澤田株式会社 / 大阪・泉州 / 糸の開発から製造まで一貫生産」

TONE: Heritage luxury. Warm. Human. Craftsmanship.
Think: Japanese whisky brand heritage ad × artisan sock brand.
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks サブ画像 v3b — 2枚再生成")
print(f"  ⑤ビジュアル全振り / ⑥糸屋の権威")
print(f"{'='*60}\n")

logo_part = load_logo()
if logo_part:
    print(f"✅ ロゴ: 新marusawa_logo.png")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(v3b_dir, fn)
    label = spec['label']

    print(f"\n[{idx}] {label}")

    contents = []
    for asset_name in spec.get('assets', []):
        part = load_asset(asset_name)
        if part:
            contents.append(part)
            print(f"  📎 {asset_name}")

    if logo_part and idx == 6:
        contents.append(logo_part)
        print(f"  📎 ロゴ追加")

    contents.append(spec['prompt'])

    generated = False
    for attempt in range(3):
        client = clients[(idx + attempt) % len(clients)]
        try:
            resp = client.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(aspect_ratio='1:1')
                )
            )
            img_data = next((p.inline_data.data for p in resp.parts if p.inline_data), None)
            if not img_data or len(img_data) < 10240:
                if attempt < 2: time.sleep(5)
                continue
            with open(fp, 'wb') as f:
                f.write(img_data)
            print(f"  ✅ 完了: {fn} ({len(img_data)//1024}KB)")
            ok += 1
            generated = True
            results.append({'index': idx, 'filename': fn, 'status': 'ok'})
            break
        except Exception as e:
            print(f"  ⚠️ attempt {attempt+1}: {e}")
            if attempt < 2: time.sleep(8)

    if not generated:
        print(f"  ❌ 失敗: {fn}")
        ng += 1
        results.append({'index': idx, 'filename': fn, 'status': 'failed'})

    if idx < SPECS[-1]['index']:
        time.sleep(3)

print(f"\n{'='*60}")
print(f"  完了: {ok}/2枚 成功 / {ng} 失敗")
print(f"  出力先: {v3b_dir}/")
print(f"{'='*60}")
