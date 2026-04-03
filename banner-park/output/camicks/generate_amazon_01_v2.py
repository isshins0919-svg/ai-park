"""
Amazon部長クン — サブ① v2 再生成
修正: 権威マーク（CAMICKS LUXURY バッジ）を明るく、視認性を上げる
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
  - Warm, golden-hour quality light — never harsh studio light
  - Shallow depth of field — foreground sharp, soft dreamy background
  - Natural materials: linen, washi paper, wood, ceramic
  - Muted palette: ivory, navy, charcoal, warm cream, deep teal
  - Generous negative space — the image breathes
  - Asymmetric editorial composition

COPY PHILOSOPHY:
  - Headlines declare, never explain
  - Large mincho typography floating in clean space
  - The luxury is shown, never stated

STRICTLY FORBIDDEN:
  - Infographic panels, circular badges, gradient bursts
  - Clinical white product photography
  - Any "Amazon promotional" visual language
  - Cluttered text or multiple competing elements

---

[SUB IMAGE 01 v2 — 「外は、ひとつ。中は、五つ。」]

CONCEPT:
The headline IS the structure. One outside. Five inside.
The sock looks like a normal sock. Inside it divides into 5.
The words mirror the form. No explanation needed.

SCENE:
An elegant pair of Camicks socks — one shown from outside (seamless, perfectly normal looking),
the other gently turned to reveal the inner five-finger structure.
Refined hands holding the sock in soft warm light.
The exterior shows NO hint of what's inside.
The image asks a quiet question: "Can you tell?"

VISUAL:
  - Sock exterior: perfectly clean, seamless, looks like a completely normal sock
  - Inside partially revealed: five-finger structure visible
  - Warm single light source from the side — fabric texture visible
  - Background: bright off-white linen or pale warm stone — light and airy
  - The feeling: a beautiful object with a hidden secret

COMPOSITION:
  - Generous negative space — the sock floats in the bright frame
  - Headline positioned with weight — two lines balanced

BRAND MARK — IMPORTANT VISIBILITY FIX:
Place ONE small rectangular brand mark in the lower-right corner.
CRITICAL: Place it on a BRIGHT, LIGHT area of the image (off-white linen or pale background).
The mark must be clearly visible and legible.

Mark design:
  - Single thin-line rectangular border, sharp corners
  - DEEP NAVY text (#1a2e3d) on BRIGHT OFF-WHITE background (#f8f5f0)
  - Small fine mincho/serif typeface
  - Text inside:
      CAMICKS
      日本製 · 匠の技
  - Size: small but clearly readable
  - Positioned: lower-right, sitting on the bright background — NOT overlapping dark areas
  - The mark must have strong contrast — dark navy on light ivory

JAPANESE TEXT (large mincho):
  HEADLINE LINE 1 (large): 「外は、ひとつ。」
  HEADLINE LINE 2 (large): 「中は、五つ。」
  SUB (small): 「外から見えない、シークレット五本指構造。縫い目ゼロ。」
"""

assets = [
    "camicks-women-inside.jpg",
    "camicks-s_detail04.jpg",
    "トリミング-レタッチ-_MG_7824.jpg",
]

print(f"\n[サブ① v2] 「外は、ひとつ。中は、五つ。」— ロゴ明るく修正")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_01_c_secret_v2.png"
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
