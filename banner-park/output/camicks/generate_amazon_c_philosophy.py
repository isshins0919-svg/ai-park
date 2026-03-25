"""
Camicks Amazon C案 — 素材哲学型
「素材が持つ性質を、現代の技術で正しく使い切る」

C案①: 「素材は、最初から答えを持っていた。」
  → 和紙 × 靴下。千年の素材と現代の技術が出会う瞬間

C案②: 「素材の声を、57年間聞いてきた。」
  → 老舗糸屋の哲学。糸=素材への敬意が全ての起点
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
out_dir = f'banner-park/output/{slug}'
assets_dir = f'{out_dir}/source_assets'
c_dir = f'{out_dir}/amazon_c_philosophy'
os.makedirs(c_dir, exist_ok=True)

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

PHILOSOPHY_DNA = """
[CAMICKS C案 — 素材哲学型 ビジュアルDNA]

CONCEPT PHILOSOPHY:
  Most brands use technology to FIGHT against nature's limitations.
  Camicks LISTENS to nature and uses technology to amplify what nature already does.
  Washi paper has been breathable for 1,000 years.
  Sawada has been listening to materials for 57 years.
  The sock is the conclusion of that conversation.

VISUAL DNA:
  - Japanese craft documentary aesthetic — NHK Beautiful Japan × Monocle Japan
  - Raw materials as the hero: washi paper, yarn, natural fibers — before the sock
  - The journey: nature → craft → product, shown poetically in one frame
  - Warm, reverent light — the kind that makes you feel you're in a craftsman's studio
  - Natural surfaces: aged wood, stone, ceramic, handmade paper
  - Muted, earthy palette: cream, warm ivory, flax, deep indigo, aged wood brown
  - Generous silence in the composition — 「間」at its most profound

TYPOGRAPHY:
  - Large, contemplative MINCHO — the words land slowly, like a haiku
  - Text is a declaration, not a description
  - One powerful headline + minimal sub

STRICTLY FORBIDDEN:
  - Any "product shot" visual language
  - Data panels, infographic elements, clinical imagery
  - Bright colors, synthetic materials in the scene
  - Anything that looks like advertising
  - The word "高級" or "プレミアム" in the image
"""

SPECS = [
    {
        "index": "c1",
        "filename": "amazon_c1_material_answer.png",
        "label": "C案①｜素材は、最初から答えを持っていた。",
        "assets": [
            "camicks-s_detail04.jpg",
            "camicks-s-dgy_detail.jpg",
        ],
        "prompt": f"""
{PHILOSOPHY_DNA}

[C案 IMAGE 01 — 「素材は、最初から答えを持っていた。」]

CORE INSIGHT:
Synthetic fibers fight against the foot's natural moisture.
Washi paper has managed moisture beautifully for 1,000 years.
Camicks didn't invent a solution. They found one that already existed.
This headline is a quiet, profound declaration: nature had the answer all along.

SCENE:
A still life of profound simplicity:
Several sheets of translucent Japanese washi paper — delicate, luminous, layered —
alongside or partially draped over the Camicks sock fabric.
The connection is visual poetry: this paper became this thread became this sock.
No explanation needed. The materials speak to each other.

VISUAL:
  - Washi paper: translucent sheets showing natural fiber texture, backlit or side-lit
    The light through the paper is beautiful — like shoji screens at golden hour
  - Sock fabric: extreme close-up where the weave echoes the paper grain
  - Both materials in the same frame — a quiet dialogue across 1,000 years
  - Surface: aged stone slab, or handmade ceramic tray, or worn wooden board
  - Light: diffused, reverent — as if this moment deserves to be treated gently
  - Palette: ivory, cream, warm white, traces of deep indigo — pure and considered
  - The overall feeling: standing in a Japanese paper museum at closing time

COMPOSITION:
  - The materials fill the frame generously — no empty product shot feeling
  - The headline appears in the cleanest area of the frame
  - Large, unhurried text — as if the words themselves have weight

JAPANESE TEXT (large mincho, contemplative):
  HEADLINE: 「素材は、最初から答えを持っていた。」
  SUB (small, almost a whisper): 「和紙の呼吸を、糸にした。camifine®」
"""
    },
    {
        "index": "c2",
        "filename": "amazon_c2_57years_voice.png",
        "label": "C案②｜素材の声を、57年間聞いてきた。",
        "assets": [
            "camicks-s_color.jpg",
            "camicks-s_detail04.jpg",
            "camicks_men_400x1000_09.jpg",
        ],
        "prompt": f"""
{PHILOSOPHY_DNA}

[C案 IMAGE 02 — 「素材の声を、57年間聞いてきた。」]

CORE INSIGHT:
Sawada Kabushiki-gaisha was not founded to make socks.
They were founded to understand yarn.
57 years of listening to materials — their behavior, their limits, their gifts.
The sock is simply what you make when you know yarn that deeply.
This headline honors the listening, not the making.

SCENE:
An artisan's arrangement of yarn spools in their natural state —
multiple cones of yarn in deep indigo, charcoal, ivory, and warm navy.
Arranged not for display, but as if placed down mid-work.
The Camicks sock rests among them — the inevitable conclusion of the yarn.
The scene feels like walking into a working yarn studio, mid-afternoon.

VISUAL:
  - Yarn cones/spools: the 4 Camicks colors — arranged with considered imperfection
  - The yarn texture: fiber-level detail visible, beautiful and tactile
  - The finished Camicks sock: placed naturally among the yarn — not centered, not posed
  - Surface: warm aged wood workbench, scarred from decades of craft
  - Light: low afternoon sun through a small window — rakes across the yarn creating shadow
  - Atmosphere: a studio where someone has been working for 57 years
    The dust motes are golden. The silence is earned.
  - Palette: deep indigo, charcoal, warm ivory, aged wood — rich and grounded

COMPOSITION:
  - Full frame of materials — abundance of craft, depth of expertise
  - The sock is a detail, not the hero — the yarn is the hero
  - Headline in the cleanest corner — a quiet, earned declaration

JAPANESE TEXT (large mincho, quiet authority):
  HEADLINE: 「素材の声を、57年間聞いてきた。」
  SUB (small): 「1969年創業。澤田株式会社 — 糸屋として始まり、糸から作り続ける。」
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks C案 素材哲学型 — 2枚生成")
print(f"  「素材が持つ性質を、現代の技術で正しく使い切る」")
print(f"{'='*60}\n")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(c_dir, fn)
    label = spec['label']

    print(f"[{idx}] {label}")

    contents = []
    for asset_name in spec.get('assets', []):
        part = load_asset(asset_name)
        if part:
            contents.append(part)
            print(f"  📎 {asset_name}")

    contents.append(spec['prompt'])

    generated = False
    client_idx = 0 if idx == 'c1' else 1
    for attempt in range(3):
        client = clients[(client_idx + attempt) % len(clients)]
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
            print(f"  ✅ 完了: {fn} ({len(img_data)//1024}KB)\n")
            ok += 1
            generated = True
            results.append({'index': idx, 'filename': fn, 'status': 'ok'})
            break
        except Exception as e:
            print(f"  ⚠️ attempt {attempt+1}: {e}")
            if attempt < 2: time.sleep(8)

    if not generated:
        print(f"  ❌ 失敗: {fn}\n")
        ng += 1
        results.append({'index': idx, 'filename': fn, 'status': 'failed'})

    time.sleep(4)

print(f"\n{'='*60}")
print(f"  完了: {ok}/2枚 成功 / {ng} 失敗")
print(f"  出力先: {c_dir}/")
print(f"{'='*60}")
