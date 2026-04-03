"""
Amazon部長 一進 — サブ② 差し替え生成
「表に出ない仕事ほど、本物だ。」→「指が、自由になる。」（外反母趾×むくみ訴求）
KWスコア改善 + 未カバー訴求の補完
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

LUXURY_DNA = """
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
  - These headlines do NOT explain. They declare.
  - Typography IS part of the art — large mincho, floating in clean space
  - The luxury is shown, never stated

STRICTLY FORBIDDEN:
  - Infographic panels, circular badges, gradient bursts
  - Clinical white product photography
  - Any "Amazon promotional" visual language
  - Cluttered text or multiple competing elements
"""

prompt = f"""
{LUXURY_DNA}

[SUB IMAGE 02 REPLACEMENT — 「指が、自由になる。」]

CONCEPT:
Five toes, each free. Each finger of the foot breathing independently.
The sock disappears. The foot returns to its natural form.
This headline speaks directly to people with bunions, swollen feet, fatigue —
people who have been cramped and compressed for too long.

CORE INSIGHT:
The five-finger structure allows each toe to move naturally.
The arch stabilizes. The pressure redistributes.
外反母趾 pain decreases. むくみ reduces.
The foot finds freedom inside the shoe.

SCENE:
A single, beautifully composed shot of feet at rest —
the moment of quiet relief after a long day.
Perhaps bare feet on a cool stone floor, or on tatami,
the Camicks sock gently removed and the toes naturally spreading.
OR: feet wearing the Camicks sock, each toe subtly visible through the natural line of the foot.
Warm, intimate light. A moment of private peace.

VISUAL:
  - Feet: graceful, feminine — the natural beauty of a foot finally free
  - Surface: cool stone, natural tatami, or warm wooden floor
  - Light: soft warm side-light — the golden relief of evening
  - Atmosphere: the exhale after a long day
  - The overall feeling: "my feet can finally breathe"

COMPOSITION:
  - The feet are the hero — intimate, close, beautiful
  - Headline in generous negative space above or beside
  - No distracting elements — just feet and light

JAPANESE TEXT (large mincho, quiet declaration):
  HEADLINE (large): 「指が、自由になる。」
  SUB (small): 「外反母趾・むくみに。5本の指が、それぞれ解放される。」
"""

assets = [
    "camicks-women_detail01.jpg",
    "camicks-women_detail02.jpg",
    "トリミング-レタッチ-_MG_7833.jpg",
]

print(f"\n[サブ②差し替え] 「指が、自由になる。」（外反母趾×むくみ）")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_02_c_freedom.png"
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
