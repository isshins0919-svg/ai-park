"""
Camicks Amazon C案 FINAL — 全6枚
コピー確定版 × Luxury Japanese Editorial × 権威マーク（③④⑥）

① 外は、ひとつ。中は、五つ。
② 表に出ない仕事ほど、本物だ。
③ 和紙は、もともと呼吸している。  × ニッセンケン認証
④ 余計なことをさせない、という設計。× ケアラベル
⑤ 靴の中にも、美意識を。
⑥ 素材に、57年。              × 創業シール
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
final_dir = f'{out_dir}/amazon_c_final'
os.makedirs(final_dir, exist_ok=True)

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

AUTHORITY MARK STYLE (③④⑥のみ):
  - Thin single-line rectangular border, sharp corners (NOT rounded)
  - Fine mincho or serif typeface, small and precise
  - Deep navy color — same tone as headline text
  - Feels like whisky age statement, artisan certification, garment label
  - One mark per image, positioned with intention

STRICTLY FORBIDDEN:
  - Infographic panels, circular badges, gradient bursts
  - Clinical white product photography
  - Any "Amazon promotional" visual language
  - Cluttered text or multiple competing elements
"""

SPECS = [
    {
        "index": 1,
        "filename": "amazon_01_c_secret.png",
        "label": "サブ① C｜外は、ひとつ。中は、五つ。",
        "assets": [
            "camicks-women-inside.jpg",
            "camicks-s_detail04.jpg",
            "トリミング-レタッチ-_MG_7824.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 01 — 「外は、ひとつ。中は、五つ。」]

CONCEPT:
The headline IS the structure. One outside. Five inside.
The sock looks like a normal sock. Inside it divides into 5.
The words mirror the form. No explanation needed.

SCENE:
An elegant pair of Camicks socks — one shown from outside (seamless, beautiful),
the other gently turned to suggest the inner structure.
Or: refined hands holding the sock in soft warm light,
the exterior showing no hint of what's inside.
The image asks a quiet question: "Can you tell?"

VISUAL:
  - Sock in deep navy or charcoal — its form is perfectly clean from outside
  - Warm single light source from the side — fabric texture visible
  - Background: off-white linen or pale stone — natural, breathing
  - The feeling: a beautiful object with a hidden secret

COMPOSITION:
  - Generous negative space — the sock floats in the frame
  - Headline positioned with weight — the two lines balanced like the two halves of the secret

JAPANESE TEXT (large mincho):
  HEADLINE LINE 1 (large): 「外は、ひとつ。」
  HEADLINE LINE 2 (large): 「中は、五つ。」
  SUB (small): 「外から見えない、シークレット五本指構造。縫い目ゼロ。」
"""
    },
    {
        "index": 2,
        "filename": "amazon_02_c_craft.png",
        "label": "サブ② C｜表に出ない仕事ほど、本物だ。",
        "assets": [
            "camicks-women-inside.jpg",
            "camicks-s_detail04.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 02 — 「表に出ない仕事ほど、本物だ。」]

CONCEPT:
A declaration about craft. The finest work is never visible.
The 5-toe interior partition is invisible from outside — that IS the point.
This headline speaks to anyone who has ever cared about quality.

SCENE:
Refined hands gently revealing the interior of the Camicks sock —
the inner partition structure emerging like a craftsperson showing hidden work.
The gesture: intimate, deliberate, like opening a handmade Japanese lacquer box.

VISUAL:
  - Hands: unhurried, refined — perhaps a trace of simple jewelry
  - The sock interior partially revealed — elegant, not clinical
  - Background: soft washi paper wall or blurred linen surface
  - Light: single warm directional source — rakes across the fabric texture
  - Color: deep navy sock, warm ivory background

COMPOSITION:
  - Hands and sock in center — generous dark negative space around them
  - Headline floats in clean space — a quiet, absolute statement

JAPANESE TEXT (large mincho, absolute):
  HEADLINE: 「表に出ない仕事ほど、本物だ。」
  SUB (small): 「5本の指それぞれを、個別に包む内側構造。」
"""
    },
    {
        "index": 3,
        "filename": "amazon_03_c_washi.png",
        "label": "サブ③ C｜和紙は、もともと呼吸している。× ニッセンケン認証",
        "assets": [
            "camicks-s_detail04.jpg",
            "camicks-s-dgy_detail.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 03 — 「和紙は、もともと呼吸している。」]

CONCEPT:
A statement of discovery, not invention.
Washi paper has been breathable for 1,000 years.
Camicks didn't create breathability — they found the material that already had it.
The headline is a declaration of natural truth.

SCENE:
Translucent washi paper sheets — luminous, delicate, layered —
placed alongside the Camicks sock fabric.
Backlit or side-lit so the paper glows with natural fiber texture.
The paper and the sock fabric echo each other: this paper became this thread.

VISUAL:
  - Washi paper: translucent, beautiful, natural fibers visible inside
  - Sock fabric: extreme close-up showing the weave — it breathes visually
  - Surface: aged stone or ceramic tray, warm and natural
  - Light: soft diffused — like a cloudy Japanese morning
  - Palette: ivory, cream, warm white throughout

AUTHORITY MARK — ニッセンケン認証:
ONE small rectangular certification mark, lower area of image.
Thin single-line border, sharp corners, fine mincho type, deep navy.
Text inside:
  ニッセンケン品質評価センター
  足臭の原因  90%減少
  酢　酸      95%減少
Size: compact, reads like a pharmaceutical certification — earned authority.

JAPANESE TEXT (large mincho):
  HEADLINE: 「和紙は、もともと呼吸している。」
  SUB (small): 「camifine® — 和紙40%の自社開発素材」
"""
    },
    {
        "index": 4,
        "filename": "amazon_04_c_care.png",
        "label": "サブ④ C｜余計なことをさせない、という設計。× ケアラベル",
        "assets": [
            "camicks-s_darkgray.jpg",
            "camicks-women_detail04.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 04 — 「余計なことをさせない、という設計。」]

CONCEPT:
A philosophy of considered design.
Every unnecessary step was removed by intention.
The sock asks nothing of you. That took 57 years to achieve.

SCENE:
Two or three Camicks socks arranged beautifully on natural linen —
as if returned from laundry and placed simply, without fuss.
Morning light, soft and unhurried. Nothing out of place.

VISUAL:
  - Socks: artfully arranged — charcoal and navy, calm and sculptural
  - Surface: pale natural linen or warm stone
  - Light: soft morning side-light, golden
  - The feeling: a calm Japanese morning where everything is exactly right

AUTHORITY MARK — ケアラベル:
ONE small care specification panel, styled as a luxury garment label.
Double thin-line border, deep navy on ivory background.
Text inside (clean sans-serif, precise):
  EASY CARE
  洗濯機  OK
  裏返し  不要
Feels like the care label of an Issey Miyake garment — thoughtful, quiet, confident.

JAPANESE TEXT (large mincho):
  HEADLINE: 「余計なことをさせない、という設計。」
  SUB (small): 「洗濯後の裏返し不要。普通の靴下と同じでいい。」
"""
    },
    {
        "index": 5,
        "filename": "amazon_05_c_aesthetic.png",
        "label": "サブ⑤ C｜靴の中にも、美意識を。",
        "assets": [
            "camicks-women_detail01.jpg",
            "camicks-women_detail02.jpg",
            "トリミング-レタッチ-_MG_7833.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 05 — 「靴の中にも、美意識を。」]

CONCEPT:
The most hidden space deserves the most care.
Nobody sees inside your shoes. That's exactly why Camicks made this beautiful.
This headline speaks to people who choose with intention — even where no one looks.

SCENE:
A woman in an elegant Japanese domestic setting —
at an entrance, or seated with legs gracefully positioned.
The Camicks sock fully visible: clean, elegant, beautiful.
This is a person for whom every choice is considered.

VISUAL:
  - The sock: seamlessly elegant — deep navy or charcoal
  - Woman: effortless, unhurried — natural beauty in an everyday moment
  - Setting: Japanese interior, natural materials, warm and composed
  - Light: warm directional, golden — the light of a considered life
  - The feeling: "I choose everything I wear. Even what no one else sees."

COMPOSITION:
  - Fashion editorial framing — the sock is a detail in a beautiful picture
  - Headline floats with quiet confidence

JAPANESE TEXT (large mincho):
  HEADLINE: 「靴の中にも、美意識を。」
  SUB (small, caption): 「23cm〜27cm対応 / メンズ・レディース兼用」
"""
    },
    {
        "index": 6,
        "filename": "amazon_06_c_legacy.png",
        "label": "サブ⑥ C｜素材に、57年。× 創業シール",
        "assets": [
            "camicks-s_color.jpg",
            "camicks-s_detail04.jpg",
            "camicks_men_400x1000_09.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 06 — 「素材に、57年。」]

CONCEPT:
The most compressed possible statement of authority.
Not "we've been making socks for 57 years."
"We have devoted 57 years to materials."
The sock is the product. The devotion to materials is the brand.

SCENE:
Yarn spools/cones in the 4 Camicks colors — deep navy, charcoal, black, warm off-white —
arranged on a warm aged wood workbench.
The finished Camicks sock rests among them — the inevitable conclusion.
Afternoon light through a studio window, raking across the yarn.

VISUAL:
  - Yarn: multiple cones, arranged with considered imperfection — mid-work
  - Yarn texture: fiber-level beautiful, warm and tactile
  - The sock: placed naturally, not posed — it belongs here
  - Surface: aged wood, scarred by decades of craft
  - Light: low golden afternoon — the light of earned experience
  - Atmosphere: you walked into this studio and work has been happening here for 57 years

AUTHORITY MARK — 創業シール（老舗の焼印）:
ONE prestigious founding mark, styled as a Japanese artisan's heritage seal.
Reference: Nikka Whisky "Since 1934", traditional sake estate marks.
Text with elegant wide letter-spacing:
  ◆ 創 業 1 9 6 9 ◆
  澤 田 株 式 会 社
  大 阪 ・ 泉 州
Fine mincho, deep navy or warm ivory — the weight of 57 years in every character.

JAPANESE TEXT (large mincho, quiet authority):
  HEADLINE: 「素材に、57年。」
  SUB (small): 「糸の開発から製造まで、一貫生産」
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks C案 FINAL — 全6枚生成")
print(f"  コピー確定版 × Luxury Editorial × 権威マーク")
print(f"{'='*60}\n")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(final_dir, fn)
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

    if idx < 6:
        time.sleep(4)

print(f"\n{'='*60}")
print(f"  完了: {ok}/6枚 成功 / {ng} 失敗")
print(f"  出力先: {final_dir}/")
print(f"{'='*60}")
