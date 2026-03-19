"""
Camicks Amazon商品画像 v2
更新: ②消臭試験データ追加 / ④洗濯メリット追加
"""

import subprocess, os, time, json
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
v1_dir = f'{out_dir}/amazon_v1'
v2_dir = f'{out_dir}/amazon_v2'
os.makedirs(v2_dir, exist_ok=True)

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

DESIGN_SYSTEM = """
[CAMICKS BRAND DESIGN SYSTEM]
PRIMARY COLOR: #3ABCEE (sky blue — accent lines only)
DARK BASE: #1a2e3d (deep navy — headlines)
BACKGROUND: #ffffff pure white OR #fafaf8 warm white
TYPOGRAPHY: elegant MINCHO/SERIF headlines. Light body text. Generous white space.
STRICTLY FORBIDDEN: blue glowing bubbles, cotton flower graphics, Check Point labels,
cluttered info panels, gradient backgrounds, rounded cartoon icons, Comic Sans.
Fashion editorial feel. NOT infographic. NOT medical.
"""

# v2で更新する2枚のみ生成（残り5枚はv1から流用）
UPDATE_SPECS = [
    {
        "index": 2,
        "filename": "amazon_02_material_v2.png",
        "label": "サブ②｜消臭試験データ追加版",
        "assets": ["camicks-s_detail04.jpg", "camicks-s-dgy_detail.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 02 v2 — 素材訴求 + 消臭試験データ]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The material story + scientific proof of odor elimination.

LAYOUT (F型):
TOP: Main headline
CENTER-LEFT: Elegant product close-up (fabric texture)
CENTER-RIGHT: Key data points with clean visual hierarchy
BOTTOM: Third-party test certification note

JAPANESE TEXT (perfectly rendered, no errors):
HEADLINE (large, mincho bold): 「一日中、蒸れない。足臭の原因を最大95%除去。」
SUB HEADLINE: 「和紙40%の独自素材 camifine®（カミファイン）」

DATA POINTS (clean, elegant layout — NOT infographic style):
  「足臭原因物質（イソ吉草酸）」→「90% 減少」
  「酢酸（汗臭の原因）」→「95% 減少」
  ※ニッセンケン品質評価センター 機器分析試験（DCB24-T03482）

BODY TEXT (small):
「革靴でも、夏の運動でも。汗を吸い、素早く乾かす。」

VISUAL: Close-up of premium sock fabric texture. Subtle washi paper texture element.
Thin #3ABCEE horizontal accent line. Numbers should be LARGE and prominent (95%, 90%).
Clean, minimal. Data presented as elegant typography, NOT as charts or badges.
"""
    },
    {
        "index": 4,
        "filename": "amazon_04_laundry_v2.png",
        "label": "サブ④｜洗濯メリット追加版",
        "assets": ["camicks-s_detail04.jpg", "camicks-women_detail04.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 04 v2 — 洗濯メリット + 構造メリット]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The everyday convenience story. No turning inside out after laundry.
This is a KEY differentiator vs regular 5-toe socks.

LAYOUT (中央集中型):
TOP: Main headline
CENTER: Visual showing easy laundry / simple sock handling
BOTTOM: Three convenience points

JAPANESE TEXT (perfectly rendered):
HEADLINE (large, mincho bold): 「洗濯後の裏返し、不要です。」
SUB: 「シークレット構造だから、普通の靴下と同じ手間でいい。」

THREE POINTS (elegant list with thin #3ABCEE lines):
① 「指袋を一本一本直す手間、ゼロ。」
② 「縫い目なし。細めの靴でも、ごつつかない。」
③ 「洗濯機OK。毎日使えるイージーケア。」

COMPARISON NOTE (small, elegant):
「通常の5本指靴下：洗濯後に指を1本ずつ整える必要あり」
「Camicks：普通の靴下と同じ、そのまま干すだけ」

VISUAL ELEMENTS:
- Clean, simple sock imagery — folded or hung to dry naturally
- Emphasize simplicity and ease
- Warm, domestic, comfortable feeling (NOT clinical)
- #3ABCEE thin accent line separating sections
- The "裏返し不要" message should feel like a relief / small joy discovery
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks Amazon画像 v2 — 2枚更新")
print(f"{'='*60}\n")

results = []
ok = ng = 0

for spec in UPDATE_SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(v2_dir, fn)
    label = spec['label']

    print(f"[{idx}] {label} — 生成中...")

    contents = []
    for asset_name in spec.get('assets', []):
        part = load_asset(asset_name)
        if part:
            contents.append(part)
            print(f"  📎 素材: {asset_name}")
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
            print(f"  ✅ 生成完了: {fn} ({len(img_data)//1024}KB)")
            ok += 1
            generated = True
            results.append({'index': idx, 'filename': fn, 'status': 'ok'})
            break
        except Exception as e:
            print(f"  ⚠️ attempt {attempt+1} エラー: {e}")
            if attempt < 2: time.sleep(8)

    if not generated:
        print(f"  ❌ 失敗: {fn}")
        ng += 1
        results.append({'index': idx, 'filename': fn, 'status': 'failed'})

    time.sleep(3)

print(f"\n{'='*60}")
print(f"  完了: {ok}/2枚 成功")
print(f"{'='*60}")
