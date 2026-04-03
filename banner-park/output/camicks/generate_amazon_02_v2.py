"""
Amazon部長 一進 — サブ② v2 再生成
KW: 水虫系（蒸れない・消臭・調湿）
画像: 外から見て普通の靴下に見えること必須（5本指がバレてはいけない）
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
  - Natural materials: linen, washi paper, wood, ceramic
  - Muted palette: ivory, navy, charcoal, warm cream
  - Generous negative space — the image breathes

COPY PHILOSOPHY:
  - Headlines declare, never explain
  - Large mincho typography floating in clean space

STRICTLY FORBIDDEN:
  - Any sock that shows 5 individual toe sections from the outside
  - The outside of the sock must look like a completely normal, regular sock
  - No clinical imagery, no infographic panels, no promotional badges

---

[SUB IMAGE 02 v2 — 「蒸れない足に、水虫は棲めない。」]

CRITICAL VISUAL RULE — READ THIS FIRST:
This product looks like a COMPLETELY NORMAL SOCK from the outside.
The five-finger structure is INVISIBLE from the exterior.
DO NOT show any toe separation on the outside of the sock.
The sock exterior must look smooth, seamless, and identical to a regular sock.
This is the entire point of the product.

CONCEPT:
The enemy of foot odor and fungal problems is moisture.
Washi paper has been managing moisture for 1,000 years.
camifine® brings that breathability to the inside of your shoe.
The sock looks completely normal. But inside — it's breathing.
Dry. Fresh. Protected.

SCENE:
A beautifully composed still life:
One or two Camicks socks — looking completely like normal, elegant socks —
arranged on natural linen or washi paper.
Morning light, cool and fresh. The mood is clean, hygienic, serene.
Perhaps a small branch of green leaves or a ceramic vessel nearby —
the feeling of freshness, nature, cleanliness.

VISUAL:
  - Sock exterior: MUST look like a normal seamless sock — NO visible toe divisions
  - Deep navy or charcoal color — the sock looks premium, regular, elegant
  - Surface: natural linen, cool stone, or handmade paper
  - Light: fresh morning light — clean and airy, not warm golden
  - The feeling: "this sock is doing something quietly, invisibly"

COMPOSITION:
  - Socks arranged simply and beautifully — like objects in a Japanese still life
  - Generous negative space — the image breathes and feels fresh
  - Headline in the cleanest area of the frame

JAPANESE TEXT (large mincho):
  HEADLINE (large): 「蒸れない足に、水虫は棲めない。」
  SUB (small): 「camifine® 和紙の調湿力で、足を乾いた状態に保つ。」
"""

assets = [
    "camicks-s_darkgray.jpg",
    "camicks-s_detail04.jpg",
]

print(f"\n[サブ② v2] 「蒸れない足に、水虫は棲めない。」")
print(f"  KW: 水虫系 / 画像: 外から普通の靴下に見える必須")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_02_c_nomoisture.png"
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
