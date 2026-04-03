"""
Amazon部長クン — サブ③ v2（ニッセンケン数値入り確定版）
コピー: 「和紙は、もともと呼吸している。」
データ: 酢酸95%削減 / イソ吉草酸90%削減（ニッセンケン繊維工業試験機関）
薬機法: 疾患名ゼロ / 試験データの提示として表現
"""
import subprocess, os, time

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
assets_dir = f'banner-park/output/{slug}/source_assets'
out_dir = f'banner-park/output/{slug}/amazon_c_final'

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

prompt = """
[CAMICKS LUXURY JAPANESE EDITORIAL DNA]

PHOTOGRAPHY STYLE:
  - Vogue Japan × Casa BRUTUS × 和の美意識
  - Warm, soft golden-hour light — fabric texture visible
  - Natural materials: washi paper, linen, raw textile threads, ceramic
  - Muted palette: ivory, warm cream, deep navy, charcoal
  - Generous negative space — the image breathes

STRICTLY FORBIDDEN:
  - Clinical white laboratory imagery
  - Generic infographic panels with gradients
  - Busy, cluttered compositions
  - Text label words like "HEADLINE" or "SUB"

---

[SUB IMAGE 03 v2 — 「和紙は、もともと呼吸している。」+ 試験データ]

CONCEPT:
Washi paper has been breathing for 1,000 years.
It absorbs. It releases. It never overwhelms.
camifine® takes this ancient material science and puts it inside a sock.
The data proves what history already knew.

SCENE:
A beautifully composed material editorial:
Strands of washi paper thread or delicate washi paper sheets — the raw material of camifine® —
arranged naturally on a warm ivory or linen surface.
Close-up texture shot: the fine weave of the fabric, threads visible in warm side-light.
The image communicates: this material has depth, history, and precision.

VISUAL REQUIREMENTS:
  - Primary visual: washi paper thread / fabric close-up OR elegant sock on washi paper
  - Light: warm, directional side-light — texture of the fabric glows
  - Background: warm ivory or natural linen — generous negative space
  - Mood: Japanese artisan craftsmanship meets material science

TYPOGRAPHY — embed these texts into the image:

Large text (large bold mincho, prominent): 「和紙は、もともと呼吸している。」
Medium text (fine mincho, below): 「camifine® — 和紙40%の自社開発素材」

DATA BADGE — this is the most important element for credibility:
Place an elegant rectangular data panel in the image.
Design: thin-line rectangle, sharp corners — matches the brand mark aesthetic.
Background: warm ivory (#f8f5f0). Text: deep navy (#1a2e3d).
Fine mincho/serif typeface.

Contents of the data panel (render exactly as shown):
┌─────────────────────────────┐
│  消臭試験結果（ニッセンケン）  │
│  酢酸     95% 削減           │
│  イソ吉草酸  90% 削減         │
└─────────────────────────────┘

Position: lower-left or lower-right area, sitting on the bright background.
Size: clearly readable but not dominating — elegant, not promotional.
The data badge should feel like a quiet proof, not a loud badge.

BRAND MARK (opposite corner from data badge):
Small rectangle: CAMICKS / 日本製 · 匠の技
Deep navy on ivory. Fine serif.
"""

assets = [
    "camicks-s_detail04.jpg",
    "トリミング-レタッチ-_MG_7824.jpg",
]

print(f"\n[サブ③ v2] 「和紙は、もともと呼吸している。」— ニッセンケン数値入り")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_03_c_washi_v2.png"
fp = os.path.join(out_dir, fn)

for attempt in range(3):
    client = clients[attempt % len(clients)]
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
        break
    except Exception as e:
        print(f"  ⚠️ attempt {attempt+1}: {e}")
        if attempt < 2: time.sleep(8)
else:
    print(f"  ❌ 失敗")

print(f"\n出力先: {fp}")
