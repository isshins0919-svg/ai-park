"""
Amazon部長クン — サブ② v4（薬機法クリア版・確定）
コピー: 「蒸れない足は、臭わない。」
薬機法: 疾患名ゼロ / 効能示唆ゼロ / 蒸れ→臭いの因果訴求
KW: 蒸れない・消臭・調湿（水虫系ユーザーにも届く）
CRITICAL: 外から普通の靴下に見えること必須
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
  - Cool, fresh morning light — clean, bright, airy
  - Natural materials: linen, washi paper, cool stone
  - Muted palette: deep navy or charcoal sock on bright ivory/linen background
  - Generous negative space — the image breathes

STRICTLY FORBIDDEN:
  - Any visible toe separation on the OUTSIDE of the sock — the exterior MUST look like a completely normal, seamless regular sock
  - Warm golden light — this image should feel fresh and clean, not warm
  - Infographic panels, badges, promotional visual language
  - Text label words like "HEADLINE" or "SUB" — do not render these as visual text in the image

---

[SUB IMAGE 02 — FINAL — 「蒸れない足は、臭わない。」]

CONCEPT:
The cause of foot odor is moisture. Remove moisture — odor disappears.
This simple truth is the entire philosophy behind camifine® washi paper technology.
A sock that breathes. A foot that stays dry. An environment where odor cannot begin.

SCENE:
A composed Japanese still life — serene and fresh.
One or two Camicks socks on natural linen or cool washi paper.
The socks look exactly like normal, elegant socks from the outside — smooth, seamless, no toe divisions visible.
Deep navy or charcoal coloring. Cool, clean morning light from the side.
Perhaps a small fresh green botanical element nearby — a cutting of eucalyptus or a small ceramic vessel with cool water.
The overall feeling: clean, hygienic, fresh. The quiet confidence of a foot that stays dry.

VISUAL REQUIREMENTS:
  - Sock exterior: completely smooth and normal-looking — zero visible toe separation from outside
  - Color: deep navy or dark charcoal — premium, refined
  - Background: bright off-white linen or cool pale washi paper — light, airy, generous
  - Light: fresh, cool morning light — bright and clean
  - Mood: Japanese apothecary meets editorial fashion

TYPOGRAPHY — embed these two texts beautifully into the image:

Large text (large bold mincho, prominent): 「蒸れない足は、臭わない。」
Small text (fine mincho, positioned below): 「camifine® 和紙の調湿力で、足を乾いた状態に保つ。」

Position the text in the generous bright negative space — elegant, floating, editorial.
The large text should be the dominant visual element alongside the socks.
Do NOT add any labels, headers, or instructional text — only these two lines.

BRAND MARK (lower-right corner):
Small rectangular mark on bright background area.
Deep navy text (#1a2e3d) on bright off-white (#f8f5f0).
Fine serif/mincho font. Sharp corners.
Contents: CAMICKS / 日本製 · 匠の技
"""

assets = [
    "camicks-s_darkgray.jpg",
    "camicks-s_detail04.jpg",
]

print(f"\n[サブ② v4 確定] 「蒸れない足は、臭わない。」— 薬機法クリア版")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_02_c_final.png"
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
