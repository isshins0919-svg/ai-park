#!/usr/bin/env python3
"""
Banner Park v7.0 — mauri MANUKA HONEY
Meta 1080x1080 (1:1) × 5枚 × 仮説ベース設計
"""

import os, json, time, subprocess, base64
from pathlib import Path
from datetime import datetime

# ─── 環境変数読み込み ───────────────────────────────────────
def load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'],
                               capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v:
                os.environ[var] = v
        except Exception:
            pass

for v in ['GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
    load_env(v)

API_KEYS = [k for k in [
    os.environ.get('GEMINI_API_KEY_1', ''),
    os.environ.get('GEMINI_API_KEY_2', ''),
    os.environ.get('GEMINI_API_KEY_3', ''),
] if k.strip()]

if not API_KEYS:
    print("❌ GEMINI_API_KEY_1 が未設定です。~/.zshrc を確認してください。")
    exit(1)

print(f"✅ API KEY: {len(API_KEYS)}本 確認")

from google import genai
from google.genai import types

clients = [genai.Client(api_key=k) for k in API_KEYS]

# ─── 出力パス ────────────────────────────────────────────────
SLUG = "mauri"
OUT_DIR = Path(__file__).parent.parent / "output" / SLUG
BANNER_DIR = OUT_DIR / "banners"
SPEC_DIR = OUT_DIR / "specs"
BANNER_DIR.mkdir(parents=True, exist_ok=True)
SPEC_DIR.mkdir(parents=True, exist_ok=True)

# ─── 5枚 バナースペック定義 ──────────────────────────────────
BANNER_SPECS = [
    {
        "bannerIndex": 1,
        "hypothesis": "常識否定型フック × Z型視線 — 「美味しさで選ぶ」常識を破壊し、本物の選び方を提示",
        "hookAngle": "常識否定型",
        "hookSource": "hook_01",
        "gazeFlow": "Z型",
        "gazeDescription": "左上: ヘッドライン → 右上: 商品ビジュアル → 左下: サブコピー → 右下: CTA",
        "headline": "美味しさで\n選んでた。",
        "subHeadline": "本当に守られていますか？",
        "ctaText": "本物をチェック →",
        "aspectRatio": "1:1",
        "templateId": "BN-A",
        "kvPhilosophy": "琥珀色の蜂蜜が木製スプーンから瓶へ垂れる瞬間。本物の天然感と高級感を1枚で体現。",
        "testHypothesis": "常識否定フックは準顕在層60代女性のCTR向上に効くか",
        "fullBannerPrompt": """Create a professional 1:1 square Japanese advertisement banner (1080x1080px) for 'mauri MANUKA HONEY' premium New Zealand manuka honey.

VISUAL CONCEPT: Amber golden honey slowly dripping from a natural wooden spoon into a beautiful glass honey jar. The honey is thick, rich, and glowing with warm golden light. NZ nature background subtly blurred - green meadows, pure white sky. The overall feeling is authentic, premium, and trustworthy.

COLOR PALETTE: Primary rich amber gold (#D4A017), cream white background (#FDF8EF), deep forest green accent (#2D5016). Warm, natural lighting.

LAYOUT (Z-type eye flow):
- Top-left zone: Main Japanese headline text on semi-transparent dark overlay band
- Top-right to center: Hero shot - wooden spoon dripping honey into jar
- Bottom zone: Subtitle text + CTA button

JAPANESE TEXT (place exactly as written, large and legible):
- MAIN HEADLINE (top-left, large bold white text): '美味しさで選んでた。'
- SUBTITLE (below headline, medium white text): '本当に守られていますか？'
- CTA BUTTON (bottom-right, gold rounded button with dark text): '本物をチェック →'

TEXT REQUIREMENTS:
- All Japanese characters must be perfectly clear and readable
- White text on semi-transparent dark overlay for contrast
- Gold CTA button with high contrast dark text
- No text bleeding off edges (keep 5% margin)

STYLE: Photorealistic, cinematic lighting, premium food photography aesthetic
DO NOT include: watermarks, blurry text, English translations, stock photo watermarks, excessive clutter, artificial-looking honey
IMPORTANT: NO ENGLISH TEXT. Japanese text only as specified above."""
    },
    {
        "bannerIndex": 2,
        "hypothesis": "恐怖訴求型 × 中央集中型 — MGO表示値と実測値の乖離への不安で強制注目",
        "hookAngle": "恐怖訴求型",
        "hookSource": "hook_02",
        "gazeFlow": "中央集中型",
        "gazeDescription": "中央: 衝撃コピー → 周辺: 証明書ビジュアル → 下部: CTA",
        "headline": "そのMGO263+\n実測値は？",
        "subHeadline": "mauri 実測値MGO345 証明書つき",
        "ctaText": "証明書を確認 →",
        "aspectRatio": "1:1",
        "templateId": "BN-F",
        "kvPhilosophy": "NZ政府認定ラボの証明書が画面中央に配置。数値の信頼性を視覚的に証明する1枚。",
        "testHypothesis": "MGO詐称への不安フックは比較検討中の顕在層に刺さるか",
        "fullBannerPrompt": """Create a professional 1:1 square Japanese advertisement banner (1080x1080px) for 'mauri MANUKA HONEY' - focusing on laboratory certification and verified MGO values.

VISUAL CONCEPT: Center of the image shows a close-up of an official New Zealand government-certified laboratory analysis certificate document with scientific-looking data tables (MGO values, test results). Surrounding the certificate: a beautiful glass jar of golden manuka honey and a wooden spoon. Clean, clinical-meets-premium aesthetic.

COLOR PALETTE: Deep navy blue (#1A2A4A) background for authority, gold (#D4A017) accents for premium, white (#FFFFFF) for text clarity. Certificate paper texture is cream/off-white.

LAYOUT (Center-focused eye flow):
- Center: Certificate document visual (prominent, clear)
- Top-left overlay: Main question headline
- Bottom: Product detail subtitle + CTA button

JAPANESE TEXT (place exactly as written):
- MAIN HEADLINE (top area, large bold white text on dark overlay): 'そのMGO263+実測値は？'
- SUBTITLE (below center, medium white text): 'mauri 実測値MGO345 証明書つき'
- CTA BUTTON (bottom center, gold rounded button): '証明書を確認 →'

TEXT REQUIREMENTS:
- Bold, authoritative typography
- High contrast - white text on dark navy
- CTA button in gold to stand out
- Japanese characters perfectly rendered

STYLE: Authoritative, trustworthy, scientific credibility, premium product photography
DO NOT include: watermarks, blurry text, fake certificates, stock photo watermarks
IMPORTANT: NO ENGLISH TEXT. Japanese text only as specified above."""
    },
    {
        "bannerIndex": 3,
        "hypothesis": "共感型 × F型視線 — 「毎日摂っても実感ない」悩みで60代女性の心を掴む",
        "hookAngle": "共感型",
        "hookSource": "hook_03",
        "gazeFlow": "F型",
        "gazeDescription": "左上: ヘッドライン → 右方向: 人物ビジュアル → 左下: サブコピー → 右方向: CTA",
        "headline": "毎日摂っているのに\n守られてる感じがしない",
        "subHeadline": "選び方が、違うのかもしれない。",
        "ctaText": "本物の選び方を見る →",
        "aspectRatio": "1:1",
        "templateId": "BN-E",
        "kvPhilosophy": "60代日本人女性が朝の静かな時間にマヌカハニーをスプーンで掬う日常シーン。共感と親しみやすさを体現。",
        "testHypothesis": "共感フックは潜在〜準顕在層の60代女性に有効か",
        "fullBannerPrompt": """Create a professional 1:1 square Japanese advertisement banner (1080x1080px) for 'mauri MANUKA HONEY' - focusing on emotional connection with Japanese women in their 60s.

VISUAL CONCEPT: A Japanese woman in her 60s, elegant and healthy-looking, in a bright, warm kitchen in the morning. She is gently scooping manuka honey from a beautiful glass jar with a wooden spoon, looking thoughtful and slightly concerned. The scene feels intimate and relatable. Morning light streams through the window. The honey jar is prominently visible with a natural, premium label.

COLOR PALETTE: Warm cream tones (#FDF8EF), soft morning light, golden honey accents (#D4A017), light sage green (#8FAF7A). Soft, warm, emotional aesthetic.

LAYOUT (F-type eye flow):
- Top-left: Main empathy headline on soft overlay
- Right side: Full lifestyle photo of woman with honey
- Bottom-left: Subtitle text
- Bottom-right: CTA button

JAPANESE TEXT (place exactly as written):
- MAIN HEADLINE (top-left, large warm brown text or white with soft shadow): '毎日摂っているのに守られてる感じがしない'
- SUBTITLE (bottom area, medium text): '選び方が、違うのかもしれない。'
- CTA BUTTON (bottom-right, warm green rounded button): '本物の選び方を見る →'

TEXT REQUIREMENTS:
- Warm, gentle typography (not aggressive)
- Soft contrast - warm colors on light background
- CTA button in forest green for natural feel
- Japanese characters perfectly rendered and emotionally resonant

STYLE: Lifestyle photography, warm and intimate, authentic Japanese daily life, not staged or artificial
DO NOT include: watermarks, blurry text, stock photo watermarks, models that look too young or too glamorous
IMPORTANT: NO ENGLISH TEXT. Japanese text only as specified above."""
    },
    {
        "bannerIndex": 4,
        "hypothesis": "権威型 × 対角線型 — 薬剤師が毎日選ぶ理由で信頼構築 × 購入障壁除去",
        "hookAngle": "権威型（薬剤師軸）",
        "hookSource": "薬剤師×錠剤疲れ新軸",
        "gazeFlow": "対角線型",
        "gazeDescription": "左上: 薬剤師ビジュアル → 右下: 商品+CTA （権威者の視線が商品に向く構図）",
        "headline": "現役薬剤師が\n毎日食べているマヌカハニー",
        "subHeadline": "選んだ理由は「本物の証明書」",
        "ctaText": "その理由を見る →",
        "aspectRatio": "1:1",
        "templateId": "BN-F",
        "kvPhilosophy": "白衣の薬剤師とmauri商品のツーショット。専門家の信頼を商品に転嫁するKVとして機能。",
        "testHypothesis": "薬剤師権威フックは「薬より天然」志向の60代女性の信頼獲得に有効か",
        "fullBannerPrompt": """Create a professional 1:1 square Japanese advertisement banner (1080x1080px) for 'mauri MANUKA HONEY' - focusing on pharmacist professional endorsement.

VISUAL CONCEPT: A Japanese pharmacist (female, 40-50s, wearing a clean white lab coat, professional and trustworthy appearance) holding a jar of premium manuka honey and smiling warmly. She looks like an expert who genuinely recommends this product. In the background, slightly blurred pharmacy/clinical setting. The honey jar is clearly visible with a premium label. Her expression conveys genuine trust and recommendation.

COLOR PALETTE: Clean white (#FFFFFF) for medical authority, rich gold (#D4A017) for premium honey, deep navy (#1A2A4A) for text. Professional yet warm aesthetic.

LAYOUT (Diagonal eye flow - top-left to bottom-right):
- Top-left: Professional headshot of pharmacist
- Top-right: Small authority badge/icon
- Center-diagonal: Main headline text
- Bottom-right: Product jar photo + CTA button

JAPANESE TEXT (place exactly as written):
- MAIN HEADLINE (center-left area, bold dark navy text): '現役薬剤師が毎日食べているマヌカハニー'
- SUBTITLE (below headline, medium text): '選んだ理由は「本物の証明書」'
- CTA BUTTON (bottom-right, gold rounded button): 'その理由を見る →'

TEXT REQUIREMENTS:
- Authoritative, trustworthy typography
- Dark navy text on white/light background for clinical feel
- Gold CTA button for premium product feel
- Japanese characters clearly rendered

STYLE: Professional photography, clinical yet warm, authoritative yet approachable, authentic Japanese healthcare professional
DO NOT include: watermarks, blurry text, obvious stock photo look, overly glamorous models
IMPORTANT: NO ENGLISH TEXT. Japanese text only as specified above."""
    },
    {
        "bannerIndex": 5,
        "hypothesis": "価格訴求型 × 中央集中型 — 58%OFFと定期縛りなしで価格敏感層を即獲得",
        "hookAngle": "価格オファー型",
        "hookSource": "offerAxis",
        "gazeFlow": "中央集中型",
        "gazeDescription": "中央: 58%OFF巨大数字 → 周辺: 商品写真+条件テキスト → 下部: CTA",
        "headline": "初回 58%OFF",
        "subHeadline": "通常7,200円 → 2,980円\nNZ直送 定期縛りなし",
        "ctaText": "今すぐ試す →",
        "aspectRatio": "1:1",
        "templateId": "BN-D",
        "kvPhilosophy": "金色を基調としたオファーバナー。商品のプレミアム感を保ちつつ価格メリットを最大強調。",
        "testHypothesis": "価格訴求×低リスク訴求の組み合わせが直接購入層に有効か",
        "fullBannerPrompt": """Create a professional 1:1 square Japanese advertisement banner (1080x1080px) for 'mauri MANUKA HONEY' - focusing on special introductory price offer.

VISUAL CONCEPT: Premium product hero shot - a beautiful glass jar of golden mauri manuka honey with a natural wooden spoon, set on a clean light surface with soft natural lighting. The jar has an elegant premium label. The background has a subtle gradient from rich amber gold to cream white. The overall feeling is premium yet accessible, inviting purchase.

COLOR PALETTE: Rich amber gold (#D4A017) as dominant color, cream white (#FDF8EF), deep forest green (#2D5016) as accent. High energy but premium aesthetic.

LAYOUT (Center-focused for maximum impact):
- Center-top: Large bold Japanese price offer text (58%OFF)
- Center: Premium product jar photo
- Center-bottom: Price details and conditions
- Bottom: Large CTA button

JAPANESE TEXT (place exactly as written, make the price numbers VERY LARGE):
- OFFER BADGE (top-center, very large bold text, gold on dark): '初回 58%OFF'
- PRICE (center, large bold dark text): '通常7,200円 → 2,980円'
- CONDITIONS (below price, medium text): 'NZ直送 定期縛りなし'
- CTA BUTTON (bottom-center, wide dark green button, white text): '今すぐ試す →'

TEXT REQUIREMENTS:
- The '58%OFF' and price numbers must be VERY LARGE and immediately visible
- High contrast between all text and background
- CTA button must be prominent and clickable-looking
- Japanese characters perfectly rendered

STYLE: Premium product photography, clean e-commerce aesthetic, compelling offer presentation
DO NOT include: watermarks, blurry text, cheap-looking design, cluttered layout
IMPORTANT: NO ENGLISH TEXT. Japanese text only as specified above."""
    }
]

# ─── 画像生成 ───────────────────────────────────────────────
def generate_banner(spec, client_idx=0):
    fn = f"banner_{spec['bannerIndex']:02d}.png"
    fp = BANNER_DIR / fn

    if fp.exists():
        print(f"  ⏭ banner_{spec['bannerIndex']:02d}.png 既存スキップ")
        return True

    prompt = spec['fullBannerPrompt']
    print(f"\n  🎨 Banner {spec['bannerIndex']:02d} 生成中...")
    print(f"     フック: {spec['hookAngle']}")
    print(f"     HL: {spec['headline'][:20].replace(chr(10), ' ')}")

    for attempt in range(3):
        c = clients[(client_idx + attempt) % len(clients)]
        try:
            resp = c.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE', 'TEXT'],
                    image_config=types.ImageConfig(aspect_ratio='1:1')
                )
            )
            img_data = None
            for part in resp.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = part.inline_data.data
                    break

            if not img_data or len(img_data) < 5000:
                print(f"     ⚠️ attempt {attempt+1}: 画像データなし or サイズ不足")
                if attempt < 2:
                    time.sleep(5)
                continue

            with open(fp, 'wb') as f:
                f.write(img_data)
            print(f"     ✅ 保存完了: {fn} ({len(img_data)//1024}KB)")
            return True

        except Exception as e:
            err = str(e)
            print(f"     ⚠️ attempt {attempt+1} エラー: {err[:100]}")
            if attempt < 2:
                time.sleep(5)

    print(f"     ❌ Banner {spec['bannerIndex']:02d} 生成失敗")
    return False


# ─── スペックJSON保存 ────────────────────────────────────────
def save_spec(spec):
    spec_path = SPEC_DIR / f"banner_{spec['bannerIndex']:02d}_spec.json"
    spec_to_save = {k: v for k, v in spec.items() if k != 'fullBannerPrompt'}
    with open(spec_path, 'w', encoding='utf-8') as f:
        json.dump(spec_to_save, f, ensure_ascii=False, indent=2)


# ─── メイン実行 ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  BANNER PARK v7.0 — mauri MANUKA HONEY")
    print(f"  生成枚数: {len(BANNER_SPECS)}枚 / Meta 1:1 / EC購入")
    print("=" * 60)

    ok = ng = 0
    for i, spec in enumerate(BANNER_SPECS):
        save_spec(spec)
        success = generate_banner(spec, client_idx=i)
        if success:
            ok += 1
        else:
            ng += 1
        if i < len(BANNER_SPECS) - 1:
            time.sleep(3)

    print("\n" + "=" * 60)
    print(f"  生成結果: {ok}/{len(BANNER_SPECS)} 枚成功  {ng} 枚失敗")
    print(f"  出力先: {BANNER_DIR}")
    print("=" * 60)

    # 簡易HTMLレポート
    generate_html_report(ok, ng)


def generate_html_report(ok, ng):
    report_path = OUT_DIR / "report.html"

    banner_cards = ""
    for spec in BANNER_SPECS:
        fn = f"banners/banner_{spec['bannerIndex']:02d}.png"
        img_exists = (BANNER_DIR / f"banner_{spec['bannerIndex']:02d}.png").exists()
        img_tag = f'<img src="{fn}" alt="Banner {spec["bannerIndex"]}" style="width:100%;border-radius:8px;">' if img_exists else '<div style="background:#333;height:200px;display:flex;align-items:center;justify-content:center;color:#888;border-radius:8px;">生成中...</div>'

        banner_cards += f"""
        <div class="banner-card">
            {img_tag}
            <div class="card-body">
                <div class="banner-num">Banner {spec['bannerIndex']:02d}</div>
                <div class="hook-badge">{spec['hookAngle']}</div>
                <div class="gazeflow">{spec['gazeFlow']}</div>
                <div class="headline">「{spec['headline'].replace(chr(10), ' ')}」</div>
                <div class="hypothesis">{spec['hypothesis']}</div>
                <div class="test-hypo">🔬 {spec['testHypothesis']}</div>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Banner Park v7.0 — mauri MANUKA HONEY</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#0d0d0d;color:#e8e8e8;font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;}}
.cover{{padding:60px 40px;text-align:center;background:linear-gradient(135deg,#1a1a1a,#0d0d0d);border-bottom:1px solid #333;}}
.cover h1{{font-size:28px;color:#D4A017;letter-spacing:2px;}}
.cover .concept{{font-size:16px;color:#aaa;margin-top:12px;}}
.cover .meta{{font-size:13px;color:#666;margin-top:8px;}}
.section{{padding:40px 24px;max-width:900px;margin:0 auto;}}
.section h2{{font-size:20px;color:#D4A017;margin-bottom:24px;border-bottom:1px solid #333;padding-bottom:12px;}}
.portfolio{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:24px;}}
.banner-card{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;overflow:hidden;}}
.card-body{{padding:16px;}}
.banner-num{{font-size:11px;color:#666;margin-bottom:6px;}}
.hook-badge{{display:inline-block;background:#D4A017;color:#000;font-size:11px;font-weight:bold;padding:3px 10px;border-radius:12px;margin-bottom:8px;}}
.gazeflow{{font-size:11px;color:#888;margin-bottom:8px;}}
.headline{{font-size:14px;color:#fff;font-weight:bold;margin-bottom:8px;line-height:1.5;}}
.hypothesis{{font-size:12px;color:#aaa;line-height:1.6;margin-bottom:8px;}}
.test-hypo{{font-size:11px;color:#666;line-height:1.5;}}
.strategy-table{{width:100%;border-collapse:collapse;font-size:13px;}}
.strategy-table th{{background:#1a1a1a;color:#D4A017;padding:10px 14px;text-align:left;border-bottom:1px solid #333;}}
.strategy-table td{{padding:10px 14px;border-bottom:1px solid #1a1a1a;color:#ccc;}}
.strategy-table tr:nth-child(even){{background:#111;}}
.result-badge{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:bold;}}
.ok{{background:#1a4a1a;color:#4ade80;}}
.ng{{background:#4a1a1a;color:#f87171;}}
</style>
</head>
<body>

<div class="cover">
  <h1>BANNER PARK v7.0 — mauri MANUKA HONEY</h1>
  <div class="concept">「本物が守る」× Meta 1080×1080 / 5仮説</div>
  <div class="meta">生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')} ／
    <span class="result-badge ok">{ok}枚 成功</span>
    {f'<span class="result-badge ng">{ng}枚 失敗</span>' if ng > 0 else ''}
  </div>
</div>

<div class="section">
  <h2>戦略サマリー</h2>
  <table class="strategy-table">
    <tr><th>商品</th><td>mauri MANUKA HONEY MGO263+ 200g</td></tr>
    <tr><th>コンセプト</th><td>「本物が守る」— MGO実測値×農薬不検出×NZ直送</td></tr>
    <tr><th>プライマリーN1</th><td>山田恵子（仮名）60代女性 / 準顕在層 / 本物志向</td></tr>
    <tr><th>訴求仮説数</th><td>5本（常識否定 / 恐怖訴求 / 共感 / 薬剤師権威 / 価格オファー）</td></tr>
    <tr><th>媒体</th><td>Meta（Instagram / Facebook）</td></tr>
    <tr><th>サイズ</th><td>1080×1080 (1:1)</td></tr>
    <tr><th>獲得タイプ</th><td>EC購入（記事LP経由）</td></tr>
  </table>
</div>

<div class="section">
  <h2>バナーポートフォリオ</h2>
  <div class="portfolio">
    {banner_cards}
  </div>
</div>

<div class="section">
  <h2>テスト戦略</h2>
  <table class="strategy-table">
    <tr><th>Round 1</th><td>フック角度の大分類テスト — 常識否定 vs 共感 vs 権威 で最強CTR軸を特定</td></tr>
    <tr><th>Round 2</th><td>勝ちフック軸で価格オファー vs 本物証明 を比較 → CVR最大化</td></tr>
    <tr><th>勝ち判定基準</th><td>CTR: 業界平均×1.5以上 / CVR: 直近平均×1.2以上 / CPA: 直近平均×0.8以下</td></tr>
  </table>
</div>

</body>
</html>"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n  📄 HTMLレポート生成: {report_path}")


if __name__ == '__main__':
    main()
