"""
Camicks Amazon C案 権威マーク版 — ③④⑥
C案コピー（糸・和紙テーマ）× 権威を滲ませるデザイン

③「千年呼吸してきた和紙が、糸になった。」× ニッセンケン認証スタンプ
④「余計なことをさせない、という設計。」× 上品なケアラベル
⑥「57年、糸だけを見てきた。」× 老舗創業シール
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
auth_dir = f'{out_dir}/amazon_c_authority'
os.makedirs(auth_dir, exist_ok=True)

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

AUTHORITY MARK PHILOSOPHY:
  The mark of authority must feel EARNED, not claimed.
  Reference: Japanese whisky age statements, artisan sake labels, Swiss watch dials.
  NOT: Amazon promotional badges, glossy circles, gradient bursts, stars.

  CORRECT authority mark style:
  - Thin single-line rectangular border (not rounded corners)
  - Small, fine serif/mincho typeface inside
  - Positioned with intention — corner or clean negative space
  - Understated: the mark whispers authority, it does not shout it
  - Color: same tone as the text (dark navy or warm ivory) — never contrasting highlight

STRICTLY FORBIDDEN:
  - Circular badges, starburst shapes, rounded pill badges
  - Gradient fills, glow effects, drop shadows on badges
  - Bright accent colors on the authority mark
  - Any visual language that reads as "promotional"
  - Multiple competing badges — ONE mark per image maximum
"""

SPECS = [
    {
        "index": 3,
        "filename": "amazon_03_c_washi_auth.png",
        "label": "サブ③C｜千年呼吸してきた和紙が、糸になった。× ニッセンケン認証",
        "assets": [
            "camicks-s_detail04.jpg",
            "camicks-s-dgy_detail.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 03 C — 「千年呼吸してきた和紙が、糸になった。」]

SCENE:
A poetic still life: translucent Japanese washi paper sheets placed alongside
the Camicks sock fabric. Both materials in quiet dialogue —
the paper that became the thread that became the sock.
Warm diffused light, natural stone or ceramic surface.
Ivory and cream tones throughout.

AUTHORITY MARK — ニッセンケン認証スタンプ:
Place ONE small, elegant rectangular certification mark in the lower area.
It should look like a laboratory certification seal on a high-end product label.

Exact text inside the mark:
┌─────────────────────────────┐
│  ニッセンケン品質評価センター  │
│  足臭の原因  90% 減少         │
│  酢  酸      95% 減少         │
└─────────────────────────────┘

Design requirements for the mark:
- Single thin line border, sharp right-angle corners (NOT rounded)
- Fine mincho or serif typeface — small, precise, confident
- Color: deep navy (#1a2e3d) — same tone as headline text
- Size: small enough to feel like a footnote, large enough to read clearly
- Positioned: lower-right corner OR lower-center in clean negative space
- The mark feels like a pharmaceutical certification or watch movement spec — earned, not advertised

JAPANESE TEXT:
  HEADLINE (large mincho): 「千年呼吸してきた和紙が、糸になった。」
  SUB (small): 「camifine® — 和紙40%の自社開発素材」
"""
    },
    {
        "index": 4,
        "filename": "amazon_04_c_laundry_auth.png",
        "label": "サブ④C｜余計なことをさせない、という設計。× ケアラベル",
        "assets": [
            "camicks-s_darkgray.jpg",
            "camicks-women_detail04.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 04 C — 「余計なことをさせない、という設計。」]

SCENE:
Two or three pairs of Camicks socks arranged beautifully on a natural linen surface.
Morning light, soft and unhurried. The scene communicates:
"This is simple. This is how it should always have been."
The arrangement is artful — like objects in a Japanese still life photograph.

AUTHORITY MARK — ケアラベル（上品な洗濯表示）:
Place ONE small elegant care specification panel, styled like a luxury clothing label.
Reference: the inside label of a fine Japanese garment — Issey Miyake, Commes des Garçons.

Exact text:
╔══════════════════════╗
║   EASY CARE          ║
║   洗濯機 OK          ║
║   裏返し不要         ║
║   毎日使えるイージーケア ║
╚══════════════════════╝

Design requirements for the mark:
- Double thin line border (inner and outer) — like a premium clothing tag
- Clean, minimal sans-serif typeface — precise and calm
- Color: warm ivory or off-white text on deep navy background
  OR deep navy text on clean white/ivory — whichever reads better in context
- Size: compact, discreet — positioned lower-left or lower-right
- Feels like a garment care instruction from a luxury fashion house
- The mark communicates thoughtful design, not promotional noise

JAPANESE TEXT:
  HEADLINE (large mincho): 「余計なことをさせない、という設計。」
  SUB (small): 「洗濯後の裏返し不要。普通の靴下と同じでいい。」
"""
    },
    {
        "index": 6,
        "filename": "amazon_06_c_brand_auth.png",
        "label": "サブ⑥C｜57年、糸だけを見てきた。× 創業シール",
        "assets": [
            "camicks-s_color.jpg",
            "camicks-s_detail04.jpg",
            "camicks_men_400x1000_09.jpg",
        ],
        "prompt": f"""
{LUXURY_DNA}

[SUB IMAGE 06 C — 「57年、糸だけを見てきた。」]

SCENE:
Yarn spools in the 4 Camicks colors — deep navy, charcoal, black, off-white —
arranged on a warm aged wood surface. The finished Camicks sock rests among them.
Afternoon light rakes across the yarn, creating beautiful shadow and texture.
The feeling: a craftsman's studio where someone has worked for 57 years.

AUTHORITY MARK — 創業シール（老舗の焼印）:
Place ONE prestigious founding mark, styled like a Japanese artisan's seal
or a heritage whisky distillery stamp.
Reference: Nikka Whisky "Since 1934", Kagoshima shochu estate seals,
traditional Japanese confectionery founding marks (老舗の焼印).

Exact text:
◆ 創 業 1969 ◆
澤 田 株 式 会 社
大 阪 ・ 泉 州

Design requirements for the mark:
- Elegant diamond or thin horizontal rule as ornament top and bottom
- Wide letter-spacing (字間を広く) — stately, unhurried
- Fine mincho typeface — every character has weight and dignity
- Color: deep navy or warm gold-adjacent ivory — NOT metallic, but warm
- Positioned: lower area or corner — like a winery estate seal on a label
- Size: compact but commanding — this mark has been here for 57 years
- The overall feeling: this company was here before you were born,
  and they will be here after you are gone

JAPANESE TEXT:
  HEADLINE (large mincho): 「57年、糸だけを見てきた。」
  SUB (small): 「糸の開発から製造まで、一貫生産」
"""
    }
]

print(f"\n{'='*60}")
print(f"  Camicks C案 権威マーク版 — 3枚生成")
print(f"  ③ニッセンケン認証 / ④ケアラベル / ⑥創業シール")
print(f"{'='*60}\n")

results = []
ok = ng = 0

for spec in SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(auth_dir, fn)
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

    time.sleep(4)

print(f"\n{'='*60}")
print(f"  完了: {ok}/3枚 成功 / {ng} 失敗")
print(f"  出力先: {auth_dir}/")
print(f"{'='*60}")
