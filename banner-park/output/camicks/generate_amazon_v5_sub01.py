"""
Camicks Amazon サブ画像 v5 — サブ①再生成
A案・B案 両方をLuxury Japanese Editorial DNAで統一

A案①: 「これが、5本指なんです。」→ Luxury Editorial スタイルに昇格
B案①: 「美しい5本指の完成形」→ A案ビジュアルスタイルに寄せて再生成
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
v5_dir = f'{out_dir}/amazon_v5_sub01'
os.makedirs(v5_dir, exist_ok=True)

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

JAPANESE AESTHETIC:
  - 「間」— meaningful empty space
  - Natural textures that evoke touch
  - The product as a craft object worthy of quiet admiration
  - Warmth of a Japanese artisan's atelier

TEXT PHILOSOPHY:
  - Large, elegant MINCHO/SERIF — the typography IS part of the art
  - Text floats in white/negative space, never clutters

STRICTLY FORBIDDEN:
  - Infographic panels, bullet points, data badges in boxes
  - Blue glowing effects, gradient backgrounds
  - Clinical white product photography
  - Side-by-side comparison panels / before/after split layouts
  - Any "Amazon product page" visual language
"""

SPECS = [
    {
        "index": "1a",
        "filename": "amazon_01_a_luxury.png",
        "label": "サブ①A案 v5｜これが、5本指なんです。（Luxury Editorial）",
        "assets": [
            "camicks-women-inside.jpg",
            "camicks-s_detail04.jpg",
            "トリミング-レタッチ-_MG_7824.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 01 A v5 — 「これが、5本指なんです。」]

CONCEPT: The quiet reveal. A sock that looks perfectly normal from outside —
but holds a secret inside. The discovery is elegant, not clinical.
The headline is a gentle surprise: "This? This is a 5-toe sock."

SCENE:
An elegant hand gently holding or turning a Camicks sock against soft natural light —
revealing the clean, seamless silhouette from outside.
The form is beautiful. Nothing about it looks like a "5-toe sock."
The reveal is the message: you'd never know.

VISUAL:
  - The sock displayed as a beautiful object — deep navy or charcoal
  - Clean form, no visible toe ridges — looks like a premium normal sock
  - Hand gesture: deliberate, unhurried — like showing fine craftsmanship
  - Background: warm off-white or pale linen surface, soft natural light
  - Light: single directional warm source — reveals fabric texture beautifully
  - The feeling: "I can't believe this is a 5-toe sock"

COMPOSITION:
  - The sock/hand centered with generous breathing space around it
  - Headline in the negative space — large, elegant, slightly surprised tone
  - NOT a side-by-side panel — ONE beautiful image, ONE discovery moment

JAPANESE TEXT (large mincho):
  HEADLINE: 「これが、5本指なんです。」
  SUB (small): 「外から見えない、シークレット五本指構造。縫い目ゼロ。」
"""
    },
    {
        "index": "1b",
        "filename": "amazon_01_b_luxury.png",
        "label": "サブ①B案 v5｜美しい5本指の完成形（A案テイスト寄せ）",
        "assets": [
            "camicks-women_detail01.jpg",
            "camicks-women_detail02.jpg",
            "トリミング-レタッチ-_MG_7824.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 01 B v5 — 「美しい5本指の完成形」]

CONCEPT: The perfected form. This is what a 5-toe sock was always meant to be.
Not a compromise — the definitive answer. Beautiful, complete, resolved.

SCENE:
A single pair of Camicks socks displayed as beautiful objects —
held in elegant hands, or laid carefully on a natural surface (linen, stone, pale wood).
The silhouette is completely clean — nothing like a typical 5-toe sock.
The form itself is the entire statement.

VISUAL:
  - The sock as sculpture — its silhouette is perfectly elegant
  - Color: deep navy — the most refined of the 4 colors
  - Surface or hands: warm, refined, unhurried
  - Light: soft warm side-light — rakes across the fabric, showing beautiful texture
  - Background: natural, muted — off-white linen or pale warm stone
  - The feeling: "this is exactly right. This is what it should always have been."

COMPOSITION:
  - Sock (or socks) centered or slightly off-center — generous negative space
  - Headline above or below — large, confident, certain
  - The image breathes — no clutter, no explanation needed

JAPANESE TEXT (large mincho, quiet conviction):
  HEADLINE: 「美しい5本指の完成形」
  SUB (small): 「シークレット構造 × camifine® × 日本製」
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks サブ①再生成 v5 — A案・B案 2枚")
print(f"  Luxury Japanese Editorial DNA 統一")
print(f"{'='*60}\n")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(v5_dir, fn)
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
    client_idx = 0 if idx == '1a' else 1
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
print(f"  出力先: {v5_dir}/")
print(f"{'='*60}")
