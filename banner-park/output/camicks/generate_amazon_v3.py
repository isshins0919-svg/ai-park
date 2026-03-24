"""
Camicks Amazon サブ画像 v3
確定コピー × おしゃれ×機能 プレミアムトーン

サブ② 「秘密は、内側にある。」     — 構造
サブ③ 「和紙だから、蒸れない。」   — 素材
サブ④ 「洗濯後の裏返し、不要です。」— 洗濯
サブ⑤ 「脱いだ後も、おしゃれ。」   — 着用シーン
サブ⑥ 「57年分の本気が、一足に。」 — ブランド
"""

import subprocess, os, time
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
v3_dir = f'{out_dir}/amazon_v3'
os.makedirs(v3_dir, exist_ok=True)

# 新ロゴ（Camicks読み込み用フォルダ）
NEW_LOGO_PATH = '/Users/ca01224/Desktop/Camicks読み込み用(Claude code)/新marusawa_logo.png'

def load_asset(filename):
    # source_assetsから読む
    path = os.path.join(assets_dir, filename)
    if not os.path.exists(path):
        print(f"  ⚠️ 素材なし: {filename}")
        return None
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png'}.get(ext,'image/jpeg')
    return types.Part.from_bytes(data=data, mime_type=mime)

def load_logo():
    path = NEW_LOGO_PATH
    if not os.path.exists(path):
        # フォールバック: source_assets内のロゴ
        path = os.path.join(assets_dir, 'marusawa_logo.png')
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        data = f.read()
    return types.Part.from_bytes(data=data, mime_type='image/png')

DESIGN_SYSTEM = """
[CAMICKS BRAND DESIGN SYSTEM — v3 PREMIUM]

BRAND TONE: Fashion-first × Function as bonus. Premium ¥2,000/pair positioning.
NOT a "functional sock brand". A "fashion item that happens to have 5-toe technology".

COLOR:
  PRIMARY ACCENT: #3ABCEE (sky blue — thin lines, data highlights only)
  HEADLINE: #1a2e3d (deep navy)
  BACKGROUND: #ffffff pure white OR #fafaf8 warm off-white
  NEVER: gradient backgrounds, blue glowing effects

TYPOGRAPHY:
  HEADLINES: elegant MINCHO/SERIF — bold, generous size, Japanese perfectly rendered
  BODY: light weight, generous line-height, minimal text
  Feel: high-end fashion magazine editorial

VISUAL FEEL:
  Fashion editorial, NOT infographic
  Generous white space
  Photography-forward
  Sophisticated, adult, minimal

STRICTLY FORBIDDEN:
  Blue glowing bubbles, cotton flower graphics, Check Point labels,
  cluttered info panels, rounded cartoon icons, Comic Sans,
  "functional product" infographic style, medical imagery
"""

SPECS = [
    {
        "index": 2,
        "filename": "amazon_02_structure_v3.png",
        "label": "サブ②｜構造「秘密は、内側にある。」",
        "assets": ["camicks-women-inside.jpg", "camicks-s_detail04.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 02 — 構造説明「秘密は、内側にある。」]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The mystery of the invisible 5-toe structure.
The sock looks completely normal — even stylish — from outside.
The 5-toe secret is only on the INSIDE. This is the key differentiator.

LAYOUT (中央集中 × ミステリアス):
  TOP: Headline — large, elegant, creates intrigue
  CENTER: Visual comparison — outside looks like stylish ordinary sock / inside reveals 5-toe partition
  BOTTOM: Brief functional note

JAPANESE TEXT (perfectly rendered):
  HEADLINE (large, mincho bold): 「秘密は、内側にある。」
  SUB: 「外から見えない、5本指構造。」
  BODY (small): 「シークレット構造だから、細めの靴でも履ける。縫い目なし。」

VISUAL DIRECTION:
  - Show a beautiful, stylish-looking sock on the outside
  - Reveal the interior partition structure in an elegant, almost architectural way
  - Dark, sophisticated feeling — like revealing a luxury product's secret craftsmanship
  - NOT a technical diagram. More like a fashion editorial showing inner beauty.
  - Subtle #3ABCEE accent line as divider

TONE: Mysterious × Premium. "The secret is inside" feeling.
"""
    },
    {
        "index": 3,
        "filename": "amazon_03_material_v3.png",
        "label": "サブ③｜素材「和紙だから、蒸れない。」",
        "assets": ["camicks-s_detail04.jpg", "camicks-s-dgy_detail.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 03 — 素材訴求「和紙だから、蒸れない。」]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The reason behind the comfort — Japanese washi paper fiber.
NOT a chemistry lesson. A sensory experience communicated visually.
The headline is a direct causal statement: "Because washi, no stuffiness."

LAYOUT (F型):
  TOP: Headline — bold causal statement
  CENTER-LEFT: Close-up of the premium fabric texture
  CENTER-RIGHT: 3 key facts — clean typographic hierarchy
  BOTTOM: Third-party certification note (small)

JAPANESE TEXT (perfectly rendered):
  HEADLINE (large, mincho bold): 「和紙だから、蒸れない。」
  SUB: 「自社開発素材 camifine®（カミファイン）— 和紙40%」

  3 FACTS (elegant list, NOT bullet points — use thin #3ABCEE lines):
    「天然由来の吸湿速乾」
    「一日中、さらさらが続く」
    「足臭の原因を最大95%除去（第三者機関試験済み）」

  SMALL NOTE: 「※ニッセンケン品質評価センター 機器分析試験（DCB24-T03482）」

VISUAL:
  - Extremely close-up fabric texture — you can almost feel the washi paper weave
  - Warm, natural, organic feeling (washi paper aesthetic)
  - Clean white/off-white background
  - Premium material photography, like luxury fashion brand fabric close-up

TONE: Natural × Premium × Scientific credibility. "You can feel the quality just by looking."
"""
    },
    {
        "index": 4,
        "filename": "amazon_04_laundry_v3.png",
        "label": "サブ④｜洗濯「洗濯後の裏返し、不要です。」",
        "assets": ["camicks-s_detail04.jpg", "camicks-women_detail04.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 04 — 洗濯メリット「洗濯後の裏返し、不要です。」]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The small daily joy of zero-hassle laundry.
For 5-toe sock users, fixing each toe after washing is a real annoyance.
Camicks eliminates this completely — same as regular socks.

LAYOUT (中央集中型 — clean, simple):
  TOP: Headline — relief, almost a sigh of comfort
  CENTER: Clean visual of socks in laundry / hung to dry naturally
  BOTTOM: 3 convenience points

JAPANESE TEXT (perfectly rendered):
  HEADLINE (large, mincho bold): 「洗濯後の裏返し、不要です。」
  SUB: 「シークレット構造だから、普通の靴下と同じでいい。」

  3 POINTS (thin #3ABCEE accent lines):
    「指袋を一本一本直す手間、ゼロ。」
    「縫い目なし。細めの靴でも、ごつつかない。」
    「洗濯機OK。毎日使えるイージーケア。」

VISUAL:
  - Clean, simple imagery — perhaps socks hung to dry or neatly folded
  - Domestic but elegant — warm, natural light
  - The feeling: "this is surprisingly easy" — small daily luxury
  - White/warm white background, minimal styling
  - NOT clinical. Warm, comfortable home atmosphere.

TONE: Relief × Ease × Small daily joy. Premium but practical.
"""
    },
    {
        "index": 5,
        "filename": "amazon_05_scene_v3.png",
        "label": "サブ⑤｜着用シーン「脱いだ後も、おしゃれ。」",
        "assets": ["camicks-women_detail01.jpg", "camicks-women_detail02.jpg", "トリミング-レタッチ-_MG_7824.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 05 — 着用シーン「脱いだ後も、おしゃれ。」]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The moment that matters most — taking off shoes at someone's home.
The target's deepest fear: "What if people see my 5-toe socks?"
Camicks answer: Even after removing shoes, you still look stylish.

LAYOUT (対角線型 — fashion editorial):
  Dominant: Lifestyle scene — woman at entrance/foyer, removing shoes
  The socks look completely stylish, no hint of 5-toe
  Overlay: Headline positioned with fashion magazine confidence

JAPANESE TEXT (perfectly rendered):
  HEADLINE (large, mincho bold, positioned confidently): 「脱いだ後も、おしゃれ。」
  SUB (smaller): 「外から、5本指には見えない。」
  SIZE INFO (small, bottom): 「23cm〜27cm対応 / メンズ・レディース兼用」

VISUAL DIRECTION:
  - Woman in elegant casual style, at an entrance foyer
  - She has just removed her shoes — the socks are visible
  - The socks look like a stylish, intentional fashion choice — NOT like "functional socks"
  - Colors visible: use dark/navy/off-white tones (the 4 Amazon colors)
  - Photography style: natural light, clean Japanese interior, fashion editorial feel
  - The overall mood: "I chose this sock as part of my outfit, not despite it"
  - High-end fashion magazine aesthetic — could appear in Vogue Japan

TONE: Confidence × Fashion × "5本指とバレない安心感". Premium lifestyle.
"""
    },
    {
        "index": 6,
        "filename": "amazon_06_brand_v3.png",
        "label": "サブ⑥｜ブランド「57年分の本気が、一足に。」",
        "assets": ["camicks-s_color.jpg", "camicks_men_400x1000_09.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 06 — ブランドストーリー「57年分の本気が、一足に。」]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: Not a sock company. A yarn company that makes socks.
Founded in 1969 as a yarn craftsman — 57 years of obsession with thread.
This is the authority that justifies the ¥2,000 price point.

LAYOUT (Z型 — brand storytelling):
  TOP: Headline — confident, legacy brand feel
  CENTER: Product image + brand heritage visual elements
  BOTTOM: Key brand facts — clean typographic hierarchy

JAPANESE TEXT (perfectly rendered):
  HEADLINE (large, mincho bold): 「57年分の本気が、一足に。」
  SUB: 「1969年創業。糸屋として始まり、糸から作り続けてきた。」

  BRAND FACTS (elegant typographic layout):
    「創業：1969年 / 大阪・泉州」
    「糸の開発から製造まで、一貫生産」
    「自社開発素材 camifine® — 和紙を糸から設計」
    「澤田株式会社」

VISUAL:
  - Premium product photography — the Camicks sock as a crafted object, worthy of admiration
  - Heritage brand aesthetic — clean, serious, confident
  - Perhaps a subtle yarn/thread texture element referencing the "started as yarn makers" story
  - NOT nostalgic or old-fashioned — modern luxury heritage brand feel (like Muji meets high-end craft)
  - Deep navy (#1a2e3d) elements, thin #3ABCEE accent line

TONE: Heritage × Craftsmanship × Modern luxury. "This is why it costs ¥2,000."
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks Amazon サブ画像 v3 — 5枚生成")
print(f"  トーン: おしゃれ×機能 / プレミアム¥2,000")
print(f"{'='*60}\n")

# ロゴ読み込み
logo_part = load_logo()
if logo_part:
    print(f"✅ ロゴ読み込み: 新marusawa_logo.png")
else:
    print(f"⚠️ ロゴなし — ロゴなしで生成")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(v3_dir, fn)
    label = spec['label']

    print(f"\n[{idx}] {label}")

    # 素材読み込み
    contents = []
    for asset_name in spec.get('assets', []):
        part = load_asset(asset_name)
        if part:
            contents.append(part)
            print(f"  📎 素材: {asset_name}")

    # ロゴ追加（ブランド画像には必ず）
    if logo_part and idx == 6:
        contents.append(logo_part)
        print(f"  📎 ロゴ追加")

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
                if attempt < 2:
                    time.sleep(5)
                continue
            with open(fp, 'wb') as f:
                f.write(img_data)
            print(f"  ✅ 完了: {fn} ({len(img_data)//1024}KB)")
            ok += 1
            generated = True
            results.append({'index': idx, 'filename': fn, 'status': 'ok', 'size_kb': len(img_data)//1024})
            break
        except Exception as e:
            print(f"  ⚠️ attempt {attempt+1} エラー: {e}")
            if attempt < 2:
                time.sleep(8)

    if not generated:
        print(f"  ❌ 失敗: {fn}")
        ng += 1
        results.append({'index': idx, 'filename': fn, 'status': 'failed'})

    if idx < SPECS[-1]['index']:
        time.sleep(3)

print(f"\n{'='*60}")
print(f"  完了: {ok}/5枚 成功 / {ng}/5枚 失敗")
print(f"  出力先: {v3_dir}/")
print(f"{'='*60}")

import json
result_path = os.path.join(out_dir, 'v3_sub_results.json')
with open(result_path, 'w', encoding='utf-8') as f:
    json.dump({'generated_at': datetime.now().isoformat(), 'results': results}, f, ensure_ascii=False, indent=2)
print(f"\n📄 結果ログ: {result_path}")
