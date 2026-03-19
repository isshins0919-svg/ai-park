"""
Camicks Amazon商品画像 v1
メイン1枚 + サブ6枚 / 1600×1600px
戦略: 【外から見えない】×ビジネスシーン×和紙camifine®×日本製55年
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
amazon_dir = f'{out_dir}/amazon_v1'
os.makedirs(amazon_dir, exist_ok=True)

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

# ============================================================
# デザインシステム（全画像共通）
# ============================================================
DESIGN_SYSTEM = """
[CAMICKS BRAND DESIGN SYSTEM — APPLY TO ALL ELEMENTS]

PRIMARY COLOR: #3ABCEE (calm sky blue — accent lines, underlines, thin highlights only)
DARK BASE: #1a2e3d (deep navy — headlines, authority text)
BACKGROUND: #ffffff pure white (Amazon requirement) OR #fafaf8 warm white
TEXT PRIMARY: #1a2e3d
TEXT SECONDARY: #666666

TYPOGRAPHY — PREMIUM JAPANESE FEEL:
- Headlines: elegant MINCHO/SERIF (Yu Mincho, Hiragino Mincho Pro)
  → Premium fashion magazine tone. NOT sports, NOT clinical.
- Body: light weight, generous line spacing
- English/numbers: Garamond or Cormorant style — thin, tall, elegant

DESIGN PHILOSOPHY — 引き算（subtraction）:
✓ Generous white space — breathing room around product
✓ Maximum 3 text elements per image
✓ #3ABCEE as thin lines/accents ONLY — never as background flood
✓ Premium product photography aesthetic
✓ Fashion editorial, NOT infographic

FORBIDDEN (vs competitors):
✗ NO blue glowing bubbles
✗ NO cotton flower graphics
✗ NO "Check Point" labels
✗ NO cluttered info panels
✗ NO gradient backgrounds
✗ NO rounded cartoon icons
✗ NO Comic Sans or casual fonts
✗ NO overlapping text
"""

# ============================================================
# Amazon画像スペック（7枚）
# ============================================================
AMAZON_SPECS = [
    {
        "index": 0,
        "filename": "amazon_00_main.png",
        "label": "メイン画像",
        "hypothesis": "白背景×商品×ブラック。第一印象で「普通の靴下に見える」→タイトルとパンチライン成立",
        "assets": ["camicks-s_darkgray.jpg", "camicks-s_color.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON MAIN IMAGE — Image 00]
Create a premium Amazon main product image (1600x1600px, 1:1 square).

PRODUCT: Camicks Secret 5-Toe Socks (シークレット五本指ソックス), black/dark gray colorway, mid-ankle length (ミドル丈).

VISUAL GOAL: The socks must look like REGULAR stylish socks from the outside — this is the core product concept (secret 5-toe structure invisible from outside).

COMPOSITION:
- Pure white background (#ffffff)
- 1-2 pairs of socks displayed elegantly — folded pair OR worn on feet (white background foot shot)
- If worn: clean foot/ankle on pure white, slightly above ground, artistic angle
- If folded: arranged with premium product photography styling
- Show dark gray / black colorway as hero

TEXT IN IMAGE:
- Small brand tag only: "Camicks" + small "marusawa" — bottom right corner, very subtle
- NO large text headlines (Amazon main image guideline — product focus)

MOOD: Premium sock brand, fashion editorial, Japanese craftsmanship quality.
Clean, minimal, aspirational.

TECHNICAL:
- 1600x1600px output
- White background must be pure #ffffff
- Product must fill ~70-80% of frame
- Safe margin: 5% all edges
"""
    },
    {
        "index": 1,
        "filename": "amazon_01_punchline.png",
        "label": "サブ1：パンチライン（シークレット構造）",
        "hypothesis": "「これが5本指？」という認知ギャップ → 即クリック誘発",
        "assets": ["camicks-women-inside.jpg", "camicks-s_detail04.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 01 — パンチライン / シークレット構造]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The "reveal" image. Outside looks like normal sock. Inside reveals 5-toe partition.

LAYOUT (中央集中型):
TOP: Large headline text
CENTER: Side-by-side or before/after visual — LEFT shows sock from outside (normal looking), RIGHT shows inner 5-toe structure
BOTTOM: Sub-text + thin #3ABCEE accent line

JAPANESE TEXT (perfectly rendered, no errors):
HEADLINE (largest, bold mincho): 「これが、5本指なんです。」
SUB (smaller): 「外から見えない。シークレット五本指構造。」
CAPTION LABEL left side: 「外から見ると」 right side: 「中は5本指」

VISUAL ELEMENTS:
- Left panel: elegant sock exterior view — clean, flat, no toe ridges visible
- Right panel: interior cross-section or inside view showing 5 individual toe pockets
- Thin #3ABCEE dividing line between panels
- Arrow or reveal effect between left and right

COLOR: White background, #1a2e3d text, #3ABCEE accents
FONT: Mincho serif headline, clean sans body text
"""
    },
    {
        "index": 2,
        "filename": "amazon_02_material.png",
        "label": "サブ2：素材訴求（camifine®和紙）",
        "hypothesis": "「和紙40%」という独自素材が競合と根本的に違うことを伝える",
        "assets": ["camicks-s_detail04.jpg", "camicks-s-dgy_detail.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 02 — 素材訴求 / camifine®和紙]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: The material story. Japanese washi paper fiber = moisture control, no stuffiness.

LAYOUT (F型 — top headline, then visual):
TOP: Headline
CENTER-LEFT: Elegant product close-up showing texture/weave
CENTER-RIGHT: Text explanation with camifine® branding
BOTTOM: Supporting detail text + thin line

JAPANESE TEXT (perfectly rendered):
HEADLINE (large, mincho bold): 「一日中、蒸れない理由がある。」
SUB HEADLINE: 「和紙40%の独自素材 camifine®（カミファイン）」
BODY TEXT (small, clean):
  「汗を吸い、素早く乾かす。」
  「革靴でも、夏の運動でも。」
BRAND NOTE (very small): 「camifine® — 澤田株式会社 自社開発素材」

VISUAL ELEMENTS:
- Close-up of sock fabric texture showing fine weave
- Abstract washi paper texture element (subtle, elegant) in background corner
- Premium textile photography feel

ACCENT: Thin #3ABCEE horizontal line separating sections
"""
    },
    {
        "index": 3,
        "filename": "amazon_03_structure.png",
        "label": "サブ3：構造説明（パーティション×ホールガーメント）",
        "hypothesis": "「なぜシークレットなのか」の仕組みを理解させ、価格正当化につなげる",
        "assets": ["camicks-s_detail04.jpg", "camicks-s-gy_detail-b.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 03 — 構造説明 / パーティション構造]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: Engineering story. Explain HOW the secret structure works.

LAYOUT (Z型):
TOP-LEFT: Headline
TOP-RIGHT: Secondary visual
CENTER: Diagram showing partition structure (elegant infographic style)
BOTTOM: Three key features listed

JAPANESE TEXT (perfectly rendered):
HEADLINE (large, mincho): 「なぜ、外から見えないのか。」
STRUCTURE NAME: 「パーティション構造」

THREE POINTS (with thin #3ABCEE bullet lines):
① 「内側だけ、5本の仕切り。外は通常ソックスの甲。」
② 「ホールガーメント製法 — 縫い目なし、ごつつきなし。」
③ 「細めの靴でも履ける。23-27cm対応。」

VISUAL ELEMENTS:
- Elegant cross-section diagram of sock showing partition inside
- Clean technical illustration style — think premium watch manual, NOT medical diagram
- Thin lines, minimal annotations, #3ABCEE accent color for diagram lines
- Small sock silhouette with interior structure revealed

FEEL: Japanese precision engineering, premium craftsmanship explanation
"""
    },
    {
        "index": 4,
        "filename": "amazon_04_health.png",
        "label": "サブ4：健康設計（外反母趾×アーチサポート）",
        "hypothesis": "「痛みがなくなった」レビューの声が刺さる外反母趾層への訴求",
        "assets": ["camicks-women_detail01.jpg", "camicks-women_detail02.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 04 — 健康設計 / アーチサポート]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: Health benefits. Arch support + correct toe positioning = comfort.

LAYOUT (対角線型):
TOP: Headline
CENTER: Elegant foot/sock visual with minimal annotation
BOTTOM: Customer voice quote + feature summary

JAPANESE TEXT (perfectly rendered):
HEADLINE (large, mincho): 「外反母趾・足の疲れに。健康設計。」
SUB: 「アーチサポートが土踏まずを引き上げ、足底筋を保護。」

CUSTOMER VOICE (in elegant quote box):
「履き始めて1ヶ月。足の痛みがなくなりました。」
— Camicks公式ストア レビューより

FEATURES (3 items, clean list):
• 足指を正しい位置に配置
• 土踏まずを引き上げるアーチサポート
• 長時間歩いても快適

VISUAL ELEMENTS:
- Sock worn on foot, elegant angle showing arch area
- Very subtle anatomical indicator (thin line, minimal) pointing to arch support area
- Warm, comfortable feel — NOT clinical/medical
- #3ABCEE thin accent lines for quote box border
"""
    },
    {
        "index": 5,
        "filename": "amazon_05_scene.png",
        "label": "サブ5：シーン訴求（ビジネス×カジュアル×スポーツ）",
        "hypothesis": "「オールシーン使える」訴求でメンズビジネス層を取り込む",
        "assets": ["camicks_men_400x1000_09.jpg", "camicks-women_detail03.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 05 — シーン訴求 / オールシーン対応]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: Versatility. Business shoes, casual sneakers, sports — all covered.

LAYOUT (Z型):
TOP: Headline
CENTER: Split visual — 2-3 scenes OR elegant lifestyle shot
BOTTOM: Scene labels + summary text

JAPANESE TEXT (perfectly rendered):
HEADLINE (large, mincho): 「脱いでも、バレない。」
SUB: 「革靴でも。スニーカーでも。スポーツでも。」

SCENE LABELS (3 panels or elegant icons):
① 「ビジネス」— 革靴・ブーツシーン
② 「カジュアル」— スニーカー・デイリー
③ 「スポーツ」— ランニング・ウォーキング

BOTTOM TEXT: 「23-27cm / メンズ・レディース兼用 / 15色展開」

VISUAL ELEMENTS:
- Elegant lifestyle feel — not stock photo, editorial quality
- Show socks in context: office floor, casual setting, outdoors
- OR: Three elegant sock arrangement photos (different colors for different scenes)
- Muted, sophisticated color palette matching brand

SPECIAL NOTE: The "脱いでも、バレない" headline connects to the main title punchline.
Business context is KEY — show dress shoes or formal setting if possible.
"""
    },
    {
        "index": 6,
        "filename": "amazon_06_brand.png",
        "label": "サブ6：ブランドストーリー（55年×日本製×大阪泉州）",
        "hypothesis": "価格正当化の最終説明。「なぜCamicksは高いのか」に答える",
        "assets": ["marusawa_logo.png", "camicks-s_color.jpg"],
        "prompt": f"""
{DESIGN_SYSTEM}

[AMAZON SUB IMAGE 06 — ブランドストーリー / 日本製55年]
Create a premium Amazon product sub-image (1600x1600px).

CONCEPT: Brand legacy. 55 years. Osaka Senshu. Made in Japan. Custom yarn to finished sock.

LAYOUT (中央集中型):
TOP: Brand statement headline
CENTER: Premium brand visual (product lineup or logo treatment)
BOTTOM: Key facts arranged elegantly

JAPANESE TEXT (perfectly rendered):
HEADLINE (large, elegant mincho): 「55年分の本気が、1足に入ってる。」
SUB: 「1969年創業。大阪泉州・澤田株式会社。」

BRAND FACTS (elegant horizontal arrangement):
「創業55年以上」 ｜ 「糸から自社開発」 ｜ 「日本製」

BODY (small):
「camifine®は澤田株式会社が糸の段階から開発する独自素材。」
「靴下だけを作り続けた技術が、Camicksを可能にした。」

BOTTOM: 「Camicks | marusawa | SAWADA YARNS」

VISUAL ELEMENTS:
- Premium brand presentation feel — like a luxury watchmaker's heritage page
- Multiple sock colors arranged in elegant lineup OR single hero product shot
- Japanese craftsmanship aesthetic — subtle washi texture element in corner
- #3ABCEE thin line separating headline from body
- Logo treatment if possible (marusawa brand mark)
- Heritage/artisan feel without being old-fashioned

COLOR NOTE: This image should feel the most "premium" of all 7.
Maximum white space. Maximum elegance. The proof of quality.
"""
    }
]

# ============================================================
# 生成実行
# ============================================================
print(f"\n{'='*60}")
print(f"  Camicks Amazon画像生成 v1")
print(f"  {len(AMAZON_SPECS)}枚 / 1600×1600px")
print(f"  出力先: {amazon_dir}/")
print(f"{'='*60}\n")

results = []
ok = ng = 0

for spec in AMAZON_SPECS:
    idx = spec['index']
    fn = spec['filename']
    fp = os.path.join(amazon_dir, fn)
    label = spec['label']

    print(f"[{idx+1}/{len(AMAZON_SPECS)}] {label} — 生成中...")

    if os.path.exists(fp):
        print(f"  ✅ スキップ（既存）: {fn}")
        ok += 1
        results.append({'index': idx, 'filename': fn, 'status': 'skipped'})
        continue

    # アセット読み込み
    contents = []
    for asset_name in spec.get('assets', []):
        part = load_asset(asset_name)
        if part:
            contents.append(part)
            print(f"  📎 素材: {asset_name}")

    contents.append(spec['prompt'])

    # 生成（3回リトライ）
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
                print(f"  ⚠️ attempt {attempt+1}: データ不足 ({len(img_data) if img_data else 0}bytes)")
                if attempt < 2:
                    time.sleep(5)
                continue
            with open(fp, 'wb') as f:
                f.write(img_data)
            print(f"  ✅ 生成完了: {fn} ({len(img_data)//1024}KB)")
            ok += 1
            generated = True
            results.append({'index': idx, 'filename': fn, 'status': 'ok', 'size_kb': len(img_data)//1024})
            break
        except Exception as e:
            print(f"  ⚠️ attempt {attempt+1} エラー: {e}")
            if attempt < 2:
                time.sleep(8)

    if not generated:
        print(f"  ❌ 生成失敗: {fn}")
        ng += 1
        results.append({'index': idx, 'filename': fn, 'status': 'failed'})

    time.sleep(3)

# ============================================================
# 結果出力
# ============================================================
result_data = {
    'generated_at': datetime.now().isoformat(),
    'total': len(AMAZON_SPECS),
    'ok': ok,
    'ng': ng,
    'results': results
}
with open(f'{out_dir}/amazon_v1_results.json', 'w', encoding='utf-8') as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"  完了: {ok}/{len(AMAZON_SPECS)} 枚生成成功")
if ng:
    print(f"  失敗: {ng} 枚")
print(f"  出力: {amazon_dir}/")
print(f"{'='*60}")
