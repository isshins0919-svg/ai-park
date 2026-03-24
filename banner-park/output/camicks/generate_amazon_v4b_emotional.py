"""
Camicks Amazon サブ画像 v4b — B案 情緒系コピー × Luxury Japanese Editorial
全6枚

① 美しい5本指の完成形
② 見えないところに、本物がある。
③ 爽やかさでたどり着いた、和紙の糸
④ 洗濯の手間ゼロを目指して
⑤ 1足ずつ作る、美しさ
⑥ 創業57年の糸屋のこだわり
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
v4b_dir = f'{out_dir}/amazon_v4b_emotional'
os.makedirs(v4b_dir, exist_ok=True)

NEW_LOGO_PATH = '/Users/ca01224/Desktop/Camicks読み込み用(Claude code)/新marusawa_logo.png'

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

def load_logo():
    path = NEW_LOGO_PATH
    if not os.path.exists(path):
        path = os.path.join(assets_dir, 'marusawa_logo.png')
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        data = f.read()
    return types.Part.from_bytes(data=data, mime_type='image/png')

LUXURY_DNA = """
[CAMICKS LUXURY JAPANESE EDITORIAL DNA — B案 情緒系]

PHOTOGRAPHY STYLE:
  - Vogue Japan × Casa BRUTUS × 和の美意識
  - Warm, golden-hour quality light — never harsh studio light
  - Shallow depth of field — foreground sharp, soft dreamy background
  - Natural materials: linen, washi paper, wood, ceramic
  - Muted palette: ivory, navy, charcoal, warm cream, deep teal
  - Generous negative space — the image breathes
  - Asymmetric editorial composition

COPY PHILOSOPHY:
  - These headlines do NOT explain. They evoke.
  - They speak to someone who already has taste.
  - NO word like "おしゃれ" "高級" "プレミアム" appears in the image
  - The luxury is shown, never stated
  - Typography IS part of the art — large mincho, floating in white space

JAPANESE AESTHETIC:
  - 「間」— meaningful empty space
  - Natural textures that evoke touch
  - The product as a craft object worthy of quiet admiration
  - Warmth of a Japanese artisan's atelier

STRICTLY FORBIDDEN:
  - Infographic panels, bullet points, data badges in boxes
  - Blue glowing effects, gradient backgrounds
  - Clinical white product photography
  - Any "functional product" visual language
  - The words おしゃれ、高級、プレミアム in the image
"""

SPECS = [
    {
        "index": 1,
        "filename": "amazon_01_b_knowing.png",
        "label": "サブ①B｜美しい5本指の完成形",
        "assets": [
            "camicks-women_detail01.jpg",
            "camicks-women_detail02.jpg",
            "トリミング-レタッチ-_MG_7824.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 01 B — 「履いた人だけが、知っている。」]

CONCEPT: The perfected form of a 5-toe sock. Beautiful, complete, resolved.
Not a compromise between fashion and function — the final answer.
The headline declares: this is what the 5-toe sock was always meant to be.

SCENE:
A single pair of Camicks socks displayed as a beautiful object —
perhaps laid flat on linen, or held up against soft light.
The silhouette is clean and elegant — nothing like a typical 5-toe sock.
No toe division visible. Just a beautifully shaped sock.

VISUAL:
  - The sock as sculpture — its form is the statement
  - Clean, pure background: warm off-white or pale stone surface
  - Light: soft side-light that reveals the fabric texture and clean form
  - Color: deep navy or charcoal — the most elegant of the 4 colors
  - The feeling: "this is the sock that finally got it right"

COMPOSITION:
  - The sock centered or slightly off-center, generous breathing space
  - Headline above or below, large and confident

JAPANESE TEXT (large mincho):
  HEADLINE: 「美しい5本指の完成形」
  SUB (small): 「シークレット構造 × camifine® × 日本製」
"""
    },
    {
        "index": 2,
        "filename": "amazon_02_b_authentic.png",
        "label": "サブ②B｜見えないところに、本物がある。",
        "assets": [
            "camicks-women-inside.jpg",
            "camicks-s_detail04.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 02 B — 「見えないところに、本物がある。」]

CONCEPT: True quality lives where no one looks.
The 5-toe interior structure is invisible from outside — that IS the point.
This headline speaks to people who understand that real craft hides in detail.

SCENE:
Elegant hands gently revealing the interior of the sock —
like a craftsperson showing the hidden quality of their work.
The gesture is intimate, deliberate. Like opening a handmade Japanese box.

VISUAL:
  - Hands: refined, unhurried — perhaps with subtle jewelry
  - The sock interior partially revealed in warm light
  - Background: soft focus, washi paper texture wall or linen surface
  - Light: single warm directional source — rakes across the fabric
  - The fabric texture itself should be exquisite up close

COMPOSITION:
  - Hands and sock occupy center, generous dark or light negative space
  - Headline in the negative space — large, quiet, certain

JAPANESE TEXT (large mincho):
  HEADLINE: 「見えないところに、本物がある。」
  SUB (small): 「外から見えない、5本指構造。縫い目なし。」
"""
    },
    {
        "index": 3,
        "filename": "amazon_03_b_washi.png",
        "label": "サブ③B｜爽やかさでたどり着いた、和紙の糸",
        "assets": [
            "camicks-s_detail04.jpg",
            "camicks-s-dgy_detail.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 03 B — 「たどり着いたのは、和紙だった。」]

CONCEPT: A journey of material discovery. Not "we used washi" but "we searched, and washi was the answer."
The headline implies years of R&D, craft obsession, and a profound conclusion.

SCENE:
A still life: actual washi paper sheets (translucent, beautiful) placed alongside
or partially under the Camicks sock fabric.
The connection between the paper and the thread is visual poetry —
"this paper became this thread became this sock."

VISUAL:
  - Washi paper: translucent sheets, natural fiber visible, backlit or side-lit
  - Sock fabric: extreme close-up where the weave is visible and beautiful
  - Both materials together — a quiet dialogue between raw and refined
  - Natural surface: stone, wood, ceramic tray
  - Light: diffused, soft — like a cloudy Japanese morning
  - Color: ivory, cream, warm white — pure and natural

COMPOSITION:
  - Still life fills frame beautifully
  - The headline placed in clean space — conveys the conclusion of a long journey

JAPANESE TEXT (large mincho, contemplative):
  HEADLINE: 「爽やかさでたどり着いた、和紙の糸」
  SUB (small): 「camifine® — 和紙40%の自社開発素材」
  DATA (very small, NOT in a box): 「足臭の原因90%減少 / 酢酸95%減少（ニッセンケン機器分析試験）」
"""
    },
    {
        "index": 4,
        "filename": "amazon_04_b_effortless.png",
        "label": "サブ④B｜洗濯の手間ゼロを目指して",
        "assets": [
            "camicks-s_detail04.jpg",
            "camicks-s_darkgray.jpg",
            "camicks-women_detail04.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 04 B — 「余計なことを、させない。」]

CONCEPT: Design philosophy as a statement.
"We designed away every unnecessary step."
This speaks to people who value thoughtful design — not convenience, but intention.

SCENE:
Two or three pairs of Camicks socks arranged beautifully on a natural surface —
as if just returned from laundry, placed simply without fuss.
Morning light. Peaceful. Nothing out of place.
The scene communicates: "This is how it should always have been."

VISUAL:
  - Socks: beautifully arranged, almost sculptural — dark navy, charcoal, off-white
  - Surface: natural linen, pale wood, or stone
  - Light: soft morning light from the side
  - Props: nothing extra — the socks ARE the scene
  - The overall feeling: Japanese minimalism, deliberate simplicity, calm mastery

COMPOSITION:
  - Socks as quiet heroes — artful arrangement with generous negative space
  - Headline: confident, matter-of-fact, as if this is simply the right way

JAPANESE TEXT (large mincho, matter-of-fact):
  HEADLINE: 「洗濯の手間ゼロを目指して」
  SUB (small): 「洗濯後の裏返し不要。普通の靴下と同じでいい。」
"""
    },
    {
        "index": 5,
        "filename": "amazon_05_b_craft.png",
        "label": "サブ⑤B｜1足ずつ作る、美しさ。",
        "assets": [
            "camicks-women_detail01.jpg",
            "camicks-women_detail02.jpg",
            "トリミング-レタッチ-_MG_7833.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 05 B — 「1足ずつ作る、美しさ。」]

CONCEPT: Craftsmanship expressed through the wearing moment.
"Made one pair at a time" — this implies hand-level care, attention to every detail.
The beauty is not in the sock alone, but in the life it enables.

SCENE:
A woman in an elegant Japanese domestic setting — at an entrance, stepping out,
or seated with her legs gracefully positioned.
The Camicks sock is fully visible and looks beautiful — a considered detail in a composed life.
This is the WEARING moment — the proof that the craft translates to beauty in real life.

VISUAL:
  - The sock: clean, elegant lines — no 5-toe visible, just beautiful form
  - Woman: effortless, unhurried — natural beauty in an everyday moment
  - Setting: Japanese interior, natural materials, calm and considered
  - Light: warm, directional, golden
  - The overall feeling: "I chose this. Everything in my life is chosen."
  - Show size info naturally: 「23-27cm / メンズ・レディース兼用」as a small caption

COMPOSITION:
  - Fashion editorial — the sock is a detail in a bigger, beautiful picture
  - Headline floats with confidence

JAPANESE TEXT (large mincho):
  HEADLINE: 「1足ずつ作る、美しさ。」
  SIZE (very small): 「23cm〜27cm対応 / メンズ・レディース兼用」
"""
    },
    {
        "index": 6,
        "filename": "amazon_06_b_yarn.png",
        "label": "サブ⑥B｜創業57年の糸屋のこだわり",
        "assets": [
            "camicks-s_color.jpg",
            "camicks_men_400x1000_09.jpg",
            "camicks-s_detail04.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 06 B — 「57年間、糸だけを見てきた。」]

CONCEPT: 57 years of singular obsession. Not "experience" — obsession.
Sawada didn't make socks. They made yarn. The sock came later.
This headline is the most powerful possible justification for ¥2,000.

SCENE:
A beautiful arrangement of yarn spools/cones in the 4 Amazon colors —
navy, charcoal, black, off-white — alongside the finished Camicks sock.
The journey from raw yarn to finished product visible in one frame.
Artisan atelier aesthetic — warmth, craft, decades of knowledge in one image.

VISUAL:
  - Yarn spools: multiple, colorful, beautifully arranged — the 4 colors
  - Finished sock: placed naturally among the yarn — the conclusion of 57 years
  - Surface: natural wood workshop table or warm stone
  - Light: warm golden light — afternoon sun in a craftsman's studio
  - Texture: the yarn texture, the sock fabric — both beautiful up close
  - Atmosphere: Japanese whisky heritage ad × artisan craft brand
  - The feeling: "these people have been doing this since before I was born"

COMPOSITION:
  - Yarn and sock fill the frame — abundance of craft
  - Headline in clean space — a quiet declaration

JAPANESE TEXT (large mincho, quiet conviction):
  HEADLINE: 「創業57年の糸屋のこだわり」
  SUB (small): 「1969年創業。澤田株式会社 / 大阪・泉州」
  FACT (very small): 「糸の開発から製造まで、一貫生産」
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks サブ画像 v4b EMOTIONAL — 6枚生成")
print(f"  B案: 情緒系コピー × Luxury Japanese Editorial")
print(f"{'='*60}\n")

logo_part = load_logo()
if logo_part:
    print(f"✅ ロゴ: 新marusawa_logo.png\n")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(v4b_dir, fn)
    label = spec['label']

    print(f"[{idx}] {label}")

    contents = []
    for asset_name in spec.get('assets', []):
        part = load_asset(asset_name)
        if part:
            contents.append(part)
            print(f"  📎 {asset_name}")

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

    if idx < SPECS[-1]['index']:
        time.sleep(3)

print(f"\n{'='*60}")
print(f"  完了: {ok}/6枚 成功 / {ng} 失敗")
print(f"  出力先: {v4b_dir}/")
print(f"{'='*60}")
