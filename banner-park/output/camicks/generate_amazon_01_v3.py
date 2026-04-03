"""
Amazon部長クン — サブ① v3（断面図＋シークレット視覚化版）
コピー: 「外は、ひとつ。中は、五つ。」
改善点: 競合全社が断面図で機能視覚化 → Camicksもビジュアルで見せる
戦略: 外側（普通）↔ 内側（5本指）のビフォーアフター構図
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
  - Warm, golden-hour side light — fabric texture luminous
  - Natural materials: linen, warm ivory background
  - Deep navy sock — premium and refined
  - Generous negative space

STRICTLY FORBIDDEN:
  - Text labels like "HEADLINE" or "SUB" — never render these
  - Harsh clinical lighting
  - Cluttered composition

---

[SUB IMAGE 01 v3 — 「外は、ひとつ。中は、五つ。」— シークレット構造 視覚化]

THE CORE CONCEPT:
This product has a secret. From the outside: one seamless, completely normal-looking sock.
From the inside: five individual fingers, each separate.
This image must make that revelation visual and beautiful.

COMPOSITION (KEY):
Show TWO socks side by side in elegant editorial arrangement:

LEFT SOCK — "外は、ひとつ。" (The outside)
  The sock shown from OUTSIDE — completely smooth, seamless.
  Looks exactly like a normal, elegant mid-ankle navy sock.
  Perfect, flawless exterior. No hint of what's inside.
  This is the secret face.

RIGHT SOCK — "中は、五つ。" (The inside)
  The SAME sock, but gently turned/folded to reveal the interior.
  The five-finger structure is beautifully visible inside.
  Each toe pocket clearly separated.
  The interior shows the five-finger architecture.
  Elegant hands or natural fold showing the inner structure.

THE GAP BETWEEN THEM tells the story:
  Left: seamless outside → Right: five-finger inside
  The viewer understands instantly: "you'd never know from outside"

VISUAL REQUIREMENTS:
  - Both socks: deep navy color
  - Arrangement: side by side on warm linen or ivory surface
  - Light: warm golden side-light — beautiful fabric texture
  - The contrast between outside and inside is the hero of the image

TYPOGRAPHY:
Large text left side (bold mincho): 「外は、ひとつ。」
Large text right side (bold mincho): 「中は、五つ。」
Small text below (fine mincho): 「外から見えない、シークレット五本指構造。縫い目ゼロ。」

The headline mirrors the composition: left text = left sock, right text = right sock.

BRAND MARK (lower-right):
Small rectangle: CAMICKS / 日本製 · 匠の技
Deep navy on ivory. Fine serif. Clearly legible.
"""

assets = [
    "camicks-women-inside.jpg",
    "camicks-s_detail04.jpg",
    "トリミング-レタッチ-_MG_7824.jpg",
]

print(f"\n[サブ① v3] 「外は、ひとつ。中は、五つ。」— 断面図×シークレット視覚化")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_01_c_secret_v3.png"
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
