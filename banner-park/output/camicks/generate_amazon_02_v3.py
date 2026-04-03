"""
Amazon部長クン — サブ② v3 再生成
修正: 「HEADLINE」「SUB」ラベルを除去。テキスト指示を自然言語に書き換え
KW: 水虫系（蒸れない・消臭・調湿）
CRITICAL: 外から普通の靴下に見えること必須（5本指構造は外から絶対に見えない）
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
  - Cool, fresh morning light — clean and airy, never warm golden
  - Natural materials: linen, washi paper, cool stone
  - Muted palette: deep navy, charcoal, ivory, cool white
  - Generous negative space — the image breathes and feels fresh

COPY PHILOSOPHY:
  - Typography IS art — large mincho floating in clean space
  - The luxury is shown, never stated

STRICTLY FORBIDDEN — READ CAREFULLY:
  - The sock exterior MUST look like a completely normal, seamless, regular sock
  - Absolutely NO visible toe divisions or five-finger separation on the outside of the sock
  - NO infographic panels, circular badges, gradient bursts
  - NO clinical imagery, NO promotional visual language
  - NO text labels like "HEADLINE" or "SUB" — these are instructions, not image content

---

[SUB IMAGE 02 v3 — 「蒸れない足に、水虫は棲めない。」]

THE PRODUCT SECRET:
This Camicks sock looks completely identical to a regular sock from the outside.
The five-finger structure is completely INVISIBLE from the exterior.
This is the entire point of the product — the secret is inside.

CONCEPT:
Moisture is the root cause of foot odor and fungal problems.
Washi paper has been managing moisture for 1,000 years.
camifine® brings that breathability to the foot — invisibly, from inside the shoe.
The sock looks completely normal. But inside — it's breathing.
Dry. Fresh. Protected. Quietly.

SCENE:
A beautifully composed Japanese still life:
One or two Camicks socks arranged on natural linen or handmade washi paper.
The socks look like completely normal, elegant deep navy or charcoal socks from the outside — smooth and seamless, with zero visible toe divisions.
Morning light, cool and fresh. A small sprig of fresh green leaves or a simple ceramic vessel nearby — the feeling of freshness, cleanliness, and quiet protection.
The atmosphere: clean, hygienic, serene. Like a high-end Japanese apothecary.

VISUAL REQUIREMENTS:
  - Sock exterior: smooth, seamless, completely normal-looking — NO toe separation visible at all
  - Sock color: deep navy or charcoal — premium and elegant
  - Surface: natural linen or cool washi paper — textured and beautiful
  - Light: fresh morning light from the side — clean, bright, airy
  - Background: bright off-white or pale cool linen — generous and breathing

TYPOGRAPHY IN THE IMAGE:
Place two lines of large Japanese mincho text floating in the generous negative space:

First text (large, bold mincho): 「蒸れない足に、水虫は棲めない。」
Second text (small, fine mincho, below the first): 「camifine® 和紙の調湿力で、足を乾いた状態に保つ。」

The text should float elegantly in the bright negative space — NOT overlapping the socks.
Typography should look like a Japanese editorial magazine layout — beautiful, considered, quiet.

BRAND MARK:
Place one small rectangular brand mark in the lower-right corner on the bright background.
Deep navy text on bright ivory background. Sharp corners. Fine serif font.
Text inside: CAMICKS / 日本製 · 匠の技
"""

assets = [
    "camicks-s_darkgray.jpg",
    "camicks-s_detail04.jpg",
]

print(f"\n[サブ② v3] 「蒸れない足に、水虫は棲めない。」— ラベル除去版")
print(f"  KW: 水虫系 / 外から普通の靴下に見える必須")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_02_c_nomoisture_v3.png"
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
