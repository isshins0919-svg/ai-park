"""
Camicks Amazon サブ画像 v4 — LUXURY JAPANESE EDITORIAL
v3b ⑤⑥の「高級感・和の感じ」を全画像に展開

② 「秘密は、内側にある。」
③ 「和紙だから、蒸れない。」
④ 「洗濯後の裏返し、不要です。」
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
v4_dir = f'{out_dir}/amazon_v4_luxury'
os.makedirs(v4_dir, exist_ok=True)

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

# ========================================
# 勝ちDNA — v3b ⑤⑥から抽出
# ========================================
LUXURY_DNA = """
[CAMICKS LUXURY JAPANESE EDITORIAL DNA]

This is the visual DNA that MUST permeate every image:

PHOTOGRAPHY STYLE:
  - Vogue Japan × Casa BRUTUS × 和の美意識
  - Warm, golden-hour quality light — never harsh studio light
  - Shallow depth of field — foreground sharp, soft dreamy background
  - Natural materials: linen, washi paper, wood, ceramic, cotton
  - Muted, sophisticated color palette: ivory, navy, charcoal, warm cream, deep teal
  - Generous negative space — the image breathes
  - Asymmetric, editorial composition — NOT centered product shot

JAPANESE AESTHETIC:
  - 「間」（Ma）— meaningful empty space
  - Natural textures that evoke touch and sensation
  - The product feels like a craft object, worthy of quiet admiration
  - Warmth of a Japanese artisan's atelier or a calm morning at home

BRAND POSITIONING:
  - ¥2,000 per pair — fashion item, not utility item
  - The sock is a deliberate lifestyle choice, not a compromise

TEXT PHILOSOPHY:
  - Absolute minimum text — 1 headline + 1 sub at most
  - Large, elegant MINCHO/SERIF — the typography IS part of the art
  - Text floats in white space, never clutters
  - If the image can speak without text, let it

STRICTLY FORBIDDEN:
  - Infographic panels, bullet point boxes, data badges
  - Blue glowing effects, gradient backgrounds
  - Clinical white product photography
  - Cartoon icons, rounded badge elements
  - Any "Amazon product page" visual language
"""

SPECS = [
    {
        "index": 2,
        "filename": "amazon_02_structure_v4.png",
        "label": "サブ②｜秘密は、内側にある。",
        "assets": ["camicks-women-inside.jpg", "camicks-s_detail04.jpg"],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 02 — 「秘密は、内側にある。」]

CONCEPT: A quiet reveal. Like opening a luxury gift box and finding something unexpected inside.
The sock looks beautiful from outside. The 5-toe interior is the secret.
Emotion: "I didn't expect this. I want to know more."

SCENE:
An elegant pair of hands gently holding or turning the Camicks sock,
revealing the interior partition structure.
The gesture should feel intimate and deliberate — like a craftsperson showing their work.

VISUAL:
  - Close-up of hands + sock in warm natural light (window light, morning)
  - The interior of the sock partially revealed — elegant, not clinical
  - Background: soft, out-of-focus Japanese interior (washi paper wall, linen textile)
  - The sock fabric texture is visible and beautiful — premium quality obvious
  - Color of sock shown: deep navy or charcoal

COMPOSITION:
  - Hands centered or slightly off-center
  - Upper half: the reveal / Lower half: clean space for text
  - OR: full bleed image with text floating in a dark/negative space area

JAPANESE TEXT (mincho, elegant):
  HEADLINE (large): 「秘密は、内側にある。」
  SUB (small): 「外から見えない、5本指構造。縫い目なし。」
"""
    },
    {
        "index": 3,
        "filename": "amazon_03_material_v4.png",
        "label": "サブ③｜和紙だから、蒸れない。",
        "assets": ["camicks-s_detail04.jpg", "camicks-s-dgy_detail.jpg"],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 03 — 「和紙だから、蒸れない。」]

CONCEPT: The sensation of the material before the explanation.
Make the viewer almost feel the fabric through the screen.
Washi paper = natural, breathable, Japanese craft heritage.

SCENE:
An extreme close-up of the Camicks sock fabric — macro-level detail.
The weave should be visible, beautiful, almost like Japanese washi paper.
Perhaps a single sheet of actual washi paper placed beside or behind the fabric
as a visual metaphor — "this thread came from this paper."

VISUAL:
  - Macro fabric texture: the weave, the thread, the subtle texture
  - Natural, organic feel — like touching cool morning air
  - Warm side-light that rakes across the fabric surface showing texture
  - Washi paper element: translucent, delicate, placed artfully in scene
  - Color palette: ivory/cream/warm white — evokes cleanliness and coolness
  - Background: soft blur, perhaps a Japanese ceramic bowl or linen cloth

COMPOSITION:
  - Texture fills 60-70% of the frame
  - Text area: clean off-white space with generous breathing room
  - Could be split: macro fabric on left, text on right — OR full bleed with text overlay

DATA (small, elegant — NOT in a box or badge):
  「足臭の原因 90% 減少 / 酢酸 95% 減少」
  「※ニッセンケン品質評価センター（DCB24-T03482）」

JAPANESE TEXT (mincho):
  HEADLINE (large): 「和紙だから、蒸れない。」
  SUB (small): 「camifine® — 和紙40%の自社開発素材」
"""
    },
    {
        "index": 4,
        "filename": "amazon_04_laundry_v4.png",
        "label": "サブ④｜洗濯後の裏返し、不要です。",
        "assets": ["camicks-s_detail04.jpg", "camicks-women_detail04.jpg", "camicks-s_darkgray.jpg"],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 04 — 「洗濯後の裏返し、不要です。」]

CONCEPT: The small daily luxury of simplicity.
A morning ritual made effortless. The sock asks nothing of you.
Emotion: quiet relief, calm, "this is how it should be."

SCENE:
A peaceful domestic morning scene.
Camicks socks neatly placed or gently folded on a clean surface —
linen fabric, natural wood shelf, or a simple ceramic tray.
Perhaps morning light streaming through a window.
The scene communicates: "This is easy. This is elegant. This is your morning."

VISUAL:
  - Socks arranged beautifully — like a still life by a minimalist photographer
  - Natural morning light (soft, directional, golden)
  - Props: white linen cloth, ceramic tray, wooden surface — very Japanese minimal
  - Colors: the 4 Amazon colors (navy, black, dark gray, off-white) — 2-3 pairs arranged
  - The overall feeling: a calm, unhurried morning in a beautiful Japanese home
  - Think: Muji catalog × Japanese lifestyle magazine

COMPOSITION:
  - Socks as the quiet hero — beautiful objects at rest
  - Generous negative space around them
  - Text floats gracefully in the clean space

JAPANESE TEXT (mincho):
  HEADLINE (large): 「洗濯後の裏返し、不要です。」
  SUB (small): 「普通の靴下と同じ手間で、5本指の機能を。」
  POINT (very small): 「洗濯機OK / 毎日使えるイージーケア」
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks サブ画像 v4 LUXURY — 3枚生成")
print(f"  DNA: 高級感 × 和の美意識 × ファッション誌テイスト")
print(f"{'='*60}\n")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(v4_dir, fn)
    label = spec['label']

    print(f"\n[{idx}] {label}")

    contents = []
    for asset_name in spec.get('assets', []):
        part = load_asset(asset_name)
        if part:
            contents.append(part)
            print(f"  📎 {asset_name}")

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
print(f"  完了: {ok}/3枚 成功 / {ng} 失敗")
print(f"  出力先: {v4_dir}/")
print(f"{'='*60}")
