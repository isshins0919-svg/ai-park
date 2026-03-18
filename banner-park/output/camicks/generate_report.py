"""
Camicks クリエイティブ制作プロセス レポート生成
全バナー・メイン画像をbase64埋め込みした完全自己完結HTMLレポート
"""

import base64, os, json
from datetime import datetime

out_dir = 'banner-park/output/camicks'
assets_dir = f'{out_dir}/source_assets'

def img_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}.get(ext, 'image/jpeg')
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

def img_tag(path, alt='', cls=''):
    b64 = img_b64(path)
    if not b64:
        return f'<div class="img-placeholder">画像なし: {os.path.basename(path)}</div>'
    return f'<img src="{b64}" alt="{alt}" class="{cls}">'

# --- データ定義 ---

VERSIONS = [
    {
        "v": "v2",
        "label": "v2 — ビジュアル分析ベース",
        "date": "2026-03 初期",
        "approach": "競合バナーを視覚的に分析し、詳細なテキストプロンプトで生成",
        "learning": "プロンプトだけでは商品の正確な再現が難しい。ブランドカラーも#66b780（緑）を誤使用",
        "tag_color": "#6c757d",
        "dir": f"{out_dir}/banners_v2",
        "files": [f"banner_0{i}_v2.png" for i in range(1,7)]
    },
    {
        "v": "v3",
        "label": "v3 — コピー方向性確定版",
        "date": "2026-03 中期",
        "approach": "「諦めなくていい」型コピーを確定。「これが、5本指なんです。/5本指には、見えません。」の方向性でリビルド",
        "learning": "コピーの方向性が決まると生成の一貫性が上がる。ただし実写素材なしでは商品再現に限界あり",
        "tag_color": "#0d6efd",
        "dir": f"{out_dir}/banners_v3",
        "files": [f"banner_0{i}_v3.png" for i in range(1,7)]
    },
    {
        "v": "v4",
        "label": "v4 — マルチモーダル入力突破口",
        "date": "2026-03 後期",
        "approach": "実写商品写真をGeminiへ直接渡すマルチモーダル入力を初導入。各バナーに対応した参照画像を紐付け",
        "learning": "マルチモーダル入力が最大の品質ドライバー。Banner 3（Adidas）は実写とほぼ同等の再現度を実現",
        "tag_color": "#198754",
        "dir": f"{out_dir}/banners_v4",
        "files": [f"banner_0{i}_v4.png" for i in range(1,7)]
    },
    {
        "v": "v5",
        "label": "v5 — プレミアムブランド設計",
        "date": "2026-03 最終",
        "approach": "ブランドカラー#3ABCEE確定 + 明朝体/serif + 競合アンチパターン禁止 + marusawa PNG logo + DESIGN_SYSTEMで全バナー統一",
        "learning": "競合6枚の分析でアンチパターン（青い吹き出し/チェックポイントテンプレ）を特定→完全差別化。3倍価格を正当化するプレミアム感を実現",
        "tag_color": "#dc3545",
        "dir": f"{out_dir}/banners_v5",
        "files": [f"banner_0{i}_v5.png" for i in range(1,7)]
    }
]

BANNERS_V5 = [
    {
        "index": 1,
        "theme": "シークレット構造 — 種明かし",
        "headline": "これが、5本指なんです。",
        "subline": "5本指には、見えません。",
        "hook": "常識逆転型",
        "ref": "camicks-s-dgy_detail.jpg",
        "concept": "「5本指=ダサい」という常識を逆転。「5本指に見えない5本指」という発見の瞬間を演出。Before/After比較で甲のフラットさを証明する。",
        "file": f"{out_dir}/banners_v5/banner_01_v5.png"
    },
    {
        "index": 2,
        "theme": "オフィス — 解放",
        "headline": "脱いでも、バレない。",
        "subline": "ローファーでも、フラットシューズでも。靴を脱いでも普通に見える。",
        "hook": "共感型（シーン想起）",
        "ref": "トリミング-レタッチ-_MG_7833.jpg",
        "concept": "オフィスで靴を脱ぐ瞬間の「バレるかも」という不安を解消。安心感と解放感を同時に演出。",
        "file": f"{out_dir}/banners_v5/banner_02_v5.png"
    },
    {
        "index": 3,
        "theme": "アクティブ — 理由提示",
        "headline": "一日中はいても、蒸れない理由がある。",
        "subline": "和紙40%の吸湿速乾。camifine®繊維が、足の蒸れを逃し続ける。",
        "hook": "理由提示型（機能証拠）",
        "ref": "IMG_8829.jpg",
        "concept": "「なぜ蒸れないのか」を明示することで機能への信頼を構築。実際のライフスタイル写真を直接使用した最高再現度バナー。",
        "file": f"{out_dir}/banners_v5/banner_03_v5.png"
    },
    {
        "index": 4,
        "theme": "機能解説 — 問いかけ",
        "headline": "なぜ、外から見えないのか。",
        "subline": "外から見えないパーティション構造。足指を正しく配置し、甲はフラットに保つ。",
        "hook": "好奇心型（問いかけ）",
        "ref": "camicks-women-inside.jpg",
        "concept": "「なぜ？」という知的好奇心を呼び起こす。内部構造（パーティション）と外見（フラット）を並べて技術力を可視化。",
        "file": f"{out_dir}/banners_v5/banner_04_v5.png"
    },
    {
        "index": 5,
        "theme": "品質 — 日本製の誇り",
        "headline": "日本製の丁寧さが、毎日に宿る。",
        "subline": "毛玉・穴あきが出にくい高耐久。洗濯機対応（30℃・ネット推奨）。",
        "hook": "権威型（産地品質）",
        "ref": "camicks-s-gy_detail-b.jpg",
        "concept": "生地のマクロ写真で素材の質感を伝える。日本製の誇りと毎日使える実用性を組み合わせたプレミアム訴求。",
        "file": f"{out_dir}/banners_v5/banner_05_v5.png"
    },
    {
        "index": 6,
        "theme": "澤田権威 — 55年の本気",
        "headline": "55年分の本気が、1足に入ってる。",
        "subline": "1969年創業、大阪泉州・澤田株式会社。靴下だけを作り続けた技術が、これを可能にした。",
        "hook": "権威型（ヘリテージ）",
        "ref": "camicks-women_detail03.jpg",
        "concept": "1969年創業・55年の専業メーカーという権威で価格を正当化。工場写真と製品を並べ、「技術の結晶」として位置づける。",
        "file": f"{out_dir}/banners_v5/banner_06_v5.png"
    }
]

MAIN_IMAGES = [
    {"index": 1, "theme": "ダークグレー ペア正面", "file": f"{out_dir}/main_images/main_01_darkgray_pair.png"},
    {"index": 2, "theme": "オフホワイト ペア正面", "file": f"{out_dir}/main_images/main_02_offwhite_pair.png"},
    {"index": 3, "theme": "真上アングル（甲フラット強調）", "file": f"{out_dir}/main_images/main_03_darkgray_top_angle.png"},
    {"index": 4, "theme": "カラバリラインナップ", "file": f"{out_dir}/main_images/main_04_multicolor_lineup.png"},
    {"index": 5, "theme": "ライフスタイル足元", "file": f"{out_dir}/main_images/main_05_lifestyle_foot.png"},
]

COPY_DIRECTION = {
    "theme": "諦めなくていい — シークレット逆転型",
    "positioning": "「5本指=ダサい」という諦めを壊す。外見は普通、中身は5本指。",
    "brand_color": "#3ABCEE",
    "font": "明朝体/Serif（Yu Mincho, Hiragino Mincho Pro）",
    "anti_patterns": [
        "青い光るバブル吹き出し（競合頻出）",
        "Check Point / チェックポイントラベル",
        "コットン花・もこもこグラフィック",
        "点線丸矢印コールアウト",
        "過剰なインフォグラフィック詰め込み",
        "過剰な緑グラデーション"
    ]
}

SOURCE_ASSETS = [
    ("camicks-s-dgy_detail.jpg", "ダークグレー詳細（甲フラット）"),
    ("トリミング-レタッチ-_MG_7833.jpg", "オフホワイト マネキン足"),
    ("IMG_8829.jpg", "Adidasライフスタイル写真"),
    ("camicks-women-inside.jpg", "内部パーティション構造"),
    ("camicks-s-gy_detail-b.jpg", "生地マクロ（グレー）"),
    ("camicks-women_detail03.jpg", "工場+製品写真"),
    ("marusawa_logo.png", "marusawaロゴ PNG"),
    ("camicks-s_color.jpg", "カラーバリエーション"),
    ("camicks-s_darkgray.jpg", "ダークグレー全体"),
]

# --- HTML生成 ---

def version_section(v):
    files_html = ""
    for fn in v["files"]:
        fp = os.path.join(v["dir"], fn)
        tag = img_tag(fp, fn, "thumb-img")
        files_html += f'<div class="thumb">{tag}</div>'

    return f"""
    <div class="version-block">
        <div class="version-header">
            <span class="version-tag" style="background:{v['tag_color']}">{v['label']}</span>
            <span class="version-date">{v['date']}</span>
        </div>
        <p class="version-approach"><strong>アプローチ:</strong> {v['approach']}</p>
        <div class="thumb-grid">{files_html}</div>
        <div class="learning-box">
            <span class="learning-icon">💡</span>
            <span>{v['learning']}</span>
        </div>
    </div>
    """

def banner_v5_card(b):
    img = img_tag(b["file"], b["theme"], "banner-img")
    ref_img = img_tag(os.path.join(assets_dir, b["ref"]), b["ref"], "ref-thumb")
    hook_colors = {
        "常識逆転型": "#dc3545",
        "共感型（シーン想起）": "#198754",
        "理由提示型（機能証拠）": "#0d6efd",
        "好奇心型（問いかけ）": "#6610f2",
        "権威型（産地品質）": "#fd7e14",
        "権威型（ヘリテージ）": "#6c3483"
    }
    hc = hook_colors.get(b["hook"], "#555")
    return f"""
    <div class="banner-card">
        <div class="banner-img-wrap">{img}</div>
        <div class="banner-info">
            <div class="banner-num">0{b['index']}</div>
            <div class="banner-theme">{b['theme']}</div>
            <div class="banner-headline">「{b['headline']}」</div>
            <div class="banner-subline">{b['subline']}</div>
            <div class="hook-badge" style="background:{hc}">{b['hook']}</div>
            <div class="banner-concept">{b['concept']}</div>
            <div class="ref-row">
                <span class="ref-label">参照素材</span>
                {ref_img}
                <span class="ref-name">{b['ref']}</span>
            </div>
        </div>
    </div>
    """

def main_card(m):
    img = img_tag(m["file"], m["theme"], "main-img")
    return f"""
    <div class="main-card">
        {img}
        <div class="main-label">
            <span class="main-num">M{m['index']:02d}</span>
            <span class="main-theme">{m['theme']}</span>
        </div>
    </div>
    """

def asset_card(filename, label):
    fp = os.path.join(assets_dir, filename)
    img = img_tag(fp, label, "asset-img")
    return f"""
    <div class="asset-card">
        {img}
        <div class="asset-label">{label}</div>
    </div>
    """

# Anti-patterns
anti_html = "".join([f'<li>❌ {p}</li>' for p in COPY_DIRECTION["anti_patterns"]])

# Competitor images
comp_dir = f"{assets_dir}/競合の画像_Amazon"
comp_imgs_html = ""
if os.path.exists(comp_dir):
    for fn in sorted(os.listdir(comp_dir)):
        if fn.endswith(('.jpg','.jpeg','.png')) and not fn.startswith('.'):
            fp = os.path.join(comp_dir, fn)
            tag = img_tag(fp, fn, "comp-img")
            comp_imgs_html += f'<div class="comp-card">{tag}<div class="comp-label">{fn.replace(".jpg","").replace("-","")}</div></div>'

versions_html = "".join([version_section(v) for v in VERSIONS])
banners_html = "".join([banner_v5_card(b) for b in BANNERS_V5])
mains_html = "".join([main_card(m) for m in MAIN_IMAGES])
assets_html = "".join([asset_card(fn, label) for fn, label in SOURCE_ASSETS])

now = datetime.now().strftime("%Y-%m-%d %H:%M")

HTML = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Camicks クリエイティブ制作レポート</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: #0d1117;
    --bg2: #161b22;
    --bg3: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --accent: #3ABCEE;
    --accent2: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --yellow: #d29922;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(0,0,0,0.4);
  }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', sans-serif;
    line-height: 1.7;
    font-size: 14px;
  }}
  a {{ color: var(--accent2); }}

  /* COVER */
  .cover {{
    background: linear-gradient(135deg, #0d1117 0%, #1a2535 50%, #0d1117 100%);
    border-bottom: 1px solid var(--border);
    padding: 80px 40px 60px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}
  .cover::before {{
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(58,188,238,0.15) 0%, transparent 70%);
  }}
  .cover-badge {{
    display: inline-block;
    background: rgba(58,188,238,0.15);
    border: 1px solid rgba(58,188,238,0.4);
    color: var(--accent);
    border-radius: 100px;
    padding: 4px 16px;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 20px;
  }}
  .cover h1 {{
    font-size: clamp(28px, 5vw, 52px);
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #fff 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
  }}
  .cover-sub {{
    font-size: 16px;
    color: var(--text-muted);
    margin-bottom: 32px;
  }}
  .cover-meta {{
    display: flex;
    justify-content: center;
    gap: 32px;
    flex-wrap: wrap;
  }}
  .meta-item {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 20px;
    text-align: center;
  }}
  .meta-num {{ font-size: 28px; font-weight: 700; color: var(--accent); }}
  .meta-label {{ font-size: 11px; color: var(--text-muted); margin-top: 2px; }}

  /* LAYOUT */
  .container {{ max-width: 1100px; margin: 0 auto; padding: 0 24px; }}
  .section {{
    padding: 64px 0 0;
  }}
  .section-header {{
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }}
  .section-num {{
    width: 36px; height: 36px;
    background: var(--accent);
    color: #fff;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px;
    flex-shrink: 0;
  }}
  .section-title {{
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
  }}
  .section-desc {{
    font-size: 13px;
    color: var(--text-muted);
  }}

  /* STRATEGY BOX */
  .strategy-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .strategy-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
  }}
  .strategy-card-label {{
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 8px;
  }}
  .strategy-card-value {{
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.4;
  }}
  .color-swatch {{
    display: inline-block;
    width: 16px; height: 16px;
    border-radius: 4px;
    vertical-align: middle;
    margin-right: 6px;
    border: 1px solid rgba(255,255,255,0.1);
  }}

  /* ANTI-PATTERNS */
  .anti-wrap {{
    background: rgba(248,81,73,0.08);
    border: 1px solid rgba(248,81,73,0.3);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 24px;
  }}
  .anti-title {{ font-size: 13px; font-weight: 700; color: var(--red); margin-bottom: 12px; }}
  .anti-wrap ul {{ list-style: none; display: flex; flex-wrap: wrap; gap: 8px; }}
  .anti-wrap li {{
    background: rgba(248,81,73,0.12);
    border: 1px solid rgba(248,81,73,0.2);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    color: #ff7b72;
  }}

  /* VERSIONS */
  .version-block {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 20px;
  }}
  .version-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }}
  .version-tag {{
    color: #fff;
    border-radius: 6px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 700;
  }}
  .version-date {{ font-size: 12px; color: var(--text-muted); }}
  .version-approach {{
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 16px;
  }}
  .thumb-grid {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
    margin-bottom: 16px;
  }}
  .thumb-img {{
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid var(--border);
  }}
  .img-placeholder {{
    width: 100%;
    aspect-ratio: 1;
    background: var(--bg3);
    border: 1px dashed var(--border);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: var(--text-muted);
  }}
  .learning-box {{
    background: rgba(63,185,80,0.08);
    border: 1px solid rgba(63,185,80,0.25);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: #7ee787;
    display: flex;
    gap: 8px;
    align-items: flex-start;
  }}
  .learning-icon {{ flex-shrink: 0; margin-top: 1px; }}

  /* BANNER V5 CARDS */
  .banner-card {{
    display: grid;
    grid-template-columns: 400px 1fr;
    gap: 28px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 24px;
    transition: border-color 0.2s;
  }}
  .banner-card:hover {{ border-color: var(--accent); }}
  .banner-img-wrap {{
    background: #111;
    overflow: hidden;
  }}
  .banner-img {{
    width: 100%;
    display: block;
    aspect-ratio: 1;
    object-fit: cover;
  }}
  .banner-info {{
    padding: 24px 24px 24px 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .banner-num {{
    font-size: 11px;
    letter-spacing: 2px;
    color: var(--text-muted);
    font-weight: 600;
  }}
  .banner-theme {{
    font-size: 13px;
    color: var(--accent);
    font-weight: 600;
  }}
  .banner-headline {{
    font-size: 20px;
    font-weight: 800;
    color: var(--text);
    line-height: 1.3;
  }}
  .banner-subline {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.6;
  }}
  .hook-badge {{
    display: inline-block;
    color: #fff;
    border-radius: 100px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 600;
    width: fit-content;
  }}
  .banner-concept {{
    font-size: 13px;
    color: #cdd9e5;
    line-height: 1.7;
    background: var(--bg3);
    border-radius: 8px;
    padding: 12px 14px;
    border-left: 3px solid var(--accent);
  }}
  .ref-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 4px;
  }}
  .ref-label {{
    font-size: 10px;
    letter-spacing: 1px;
    color: var(--text-muted);
    text-transform: uppercase;
    white-space: nowrap;
  }}
  .ref-thumb {{
    width: 44px;
    height: 44px;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid var(--border);
  }}
  .ref-name {{ font-size: 11px; color: var(--text-muted); }}

  /* MAIN IMAGES */
  .main-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
  }}
  .main-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }}
  .main-img {{
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    display: block;
  }}
  .main-label {{
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .main-num {{
    background: var(--accent);
    color: #fff;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    flex-shrink: 0;
  }}
  .main-theme {{ font-size: 12px; color: var(--text-muted); }}

  /* SOURCE ASSETS */
  .asset-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 12px;
  }}
  .asset-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  .asset-img {{
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    display: block;
  }}
  .asset-label {{
    padding: 8px 10px;
    font-size: 10px;
    color: var(--text-muted);
    line-height: 1.4;
  }}

  /* COMPETITORS */
  .comp-grid {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }}
  .comp-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  .comp-img {{
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    display: block;
  }}
  .comp-label {{
    padding: 6px 8px;
    font-size: 10px;
    color: var(--text-muted);
    text-align: center;
  }}

  /* INSIGHTS */
  .insight-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }}
  .insight-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 18px 20px;
  }}
  .insight-card h4 {{
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 8px;
    color: var(--accent);
  }}
  .insight-card p {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.7;
  }}

  /* FOOTER */
  .footer {{
    margin-top: 80px;
    padding: 40px 0;
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
  }}

  /* PRINT */
  @media print {{
    body {{ background: #fff; color: #111; }}
    .cover {{ background: #f8f9fa; }}
    .cover h1 {{ -webkit-text-fill-color: #111; color: #111; }}
    .version-block, .banner-card, .strategy-card, .main-card, .asset-card {{
      background: #fff;
      border-color: #ddd;
    }}
  }}

  @media (max-width: 768px) {{
    .banner-card {{
      grid-template-columns: 1fr;
    }}
    .banner-info {{
      padding: 16px;
    }}
    .thumb-grid {{
      grid-template-columns: repeat(3, 1fr);
    }}
    .comp-grid {{
      grid-template-columns: repeat(3, 1fr);
    }}
  }}
</style>
</head>
<body>

<!-- COVER -->
<div class="cover">
  <div class="cover-badge">Creative Report</div>
  <h1>Camicks クリエイティブ<br>制作プロセスレポート</h1>
  <p class="cover-sub">和紙シークレット5本指ソックス — Amazon商品画像 全プロセス記録</p>
  <div class="cover-meta">
    <div class="meta-item">
      <div class="meta-num">4</div>
      <div class="meta-label">改善バージョン</div>
    </div>
    <div class="meta-item">
      <div class="meta-num">6</div>
      <div class="meta-label">サブ画像（最終版）</div>
    </div>
    <div class="meta-item">
      <div class="meta-num">5</div>
      <div class="meta-label">メイン画像パターン</div>
    </div>
    <div class="meta-item">
      <div class="meta-num">6</div>
      <div class="meta-label">競合分析</div>
    </div>
  </div>
  <div style="margin-top:24px;font-size:12px;color:var(--text-muted)">生成日時: {now} | marusawa / 澤田株式会社</div>
</div>

<div class="container">

<!-- SECTION 1: 戦略 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">1</div>
    <div>
      <div class="section-title">ポジショニング戦略</div>
      <div class="section-desc">競合との差別化設計 / コピー方向性 / ブランドデザインシステム</div>
    </div>
  </div>

  <div class="strategy-grid">
    <div class="strategy-card">
      <div class="strategy-card-label">コピー方向性</div>
      <div class="strategy-card-value">{COPY_DIRECTION['theme']}</div>
    </div>
    <div class="strategy-card">
      <div class="strategy-card-label">Only1ポジション</div>
      <div class="strategy-card-value">{COPY_DIRECTION['positioning']}</div>
    </div>
    <div class="strategy-card">
      <div class="strategy-card-label">ブランドカラー</div>
      <div class="strategy-card-value">
        <span class="color-swatch" style="background:{COPY_DIRECTION['brand_color']}"></span>
        {COPY_DIRECTION['brand_color']}（スカイブルー）
      </div>
    </div>
    <div class="strategy-card">
      <div class="strategy-card-label">タイポグラフィ</div>
      <div class="strategy-card-value">{COPY_DIRECTION['font']}</div>
    </div>
  </div>

  <div class="anti-wrap">
    <div class="anti-title">競合アンチパターン — 意図的に排除した要素</div>
    <ul>{anti_html}</ul>
  </div>

  <div style="margin-bottom:16px;font-size:13px;font-weight:700;color:var(--text-muted)">競合 Amazon 画像（分析対象）</div>
  <div class="comp-grid">{comp_imgs_html}</div>
</div>

<!-- SECTION 2: 制作プロセス -->
<div class="section">
  <div class="section-header">
    <div class="section-num">2</div>
    <div>
      <div class="section-title">制作プロセス — 4バージョンの進化</div>
      <div class="section-desc">各バージョンで何を学び、何を改善したか</div>
    </div>
  </div>
  {versions_html}
</div>

<!-- SECTION 3: 主要学習 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">3</div>
    <div>
      <div class="section-title">主要インサイト</div>
      <div class="section-desc">AI画像生成 × ブランディングで発見した重要知見</div>
    </div>
  </div>
  <div class="insight-grid">
    <div class="insight-card">
      <h4>🔑 最大の品質ドライバー: マルチモーダル入力</h4>
      <p>実写商品写真をGeminiへ直接渡すことが最大の品質向上要因。テキストプロンプトだけでは商品の正確な再現が困難。特にBanner 3（Adidas）は実写と同等の再現度を実現。</p>
    </div>
    <div class="insight-card">
      <h4>🎨 ブランドカラー確定の重要性</h4>
      <p>v2〜v4まで#66b780（緑）を誤使用。実際は#3ABCEE（スカイブルー）が正しいブランドカラー。AIは間違った前提でも疑わず生成するため、インプット情報の正確性が成果を左右する。</p>
    </div>
    <div class="insight-card">
      <h4>🚫 アンチパターン定義で差別化</h4>
      <p>「やらないこと」を明文化したDESIGN_SYSTEMがブランドの一貫性を保つ。競合6枚を分析して禁止要素を抽出→Camicksが全く異なるビジュアルトーンを実現。</p>
    </div>
    <div class="insight-card">
      <h4>💰 3倍価格正当化の3本柱</h4>
      <p>①エディトリアル品質のビジュアル ②「隠す」という逆張りポジショニング ③白地余白設計（詰め込まない）。プレミアム感は「加えること」より「引くこと」で生まれる。</p>
    </div>
    <div class="insight-card">
      <h4>📖 明朝体 × 余白 = 高級感</h4>
      <p>競合は全てゴシック体・角丸・情報密度高め。Camicksは明朝体・直線・余白多めを採用。フォントと余白だけで価格帯の印象が大きく変わる。</p>
    </div>
    <div class="insight-card">
      <h4>🔬 仮説1枚・証拠1枚の設計</h4>
      <p>6枚の構成: 構造証拠→シーン共感→機能証拠→技術解説→品質証拠→権威証拠。各画像が独立した「なぜ買うか」の理由を持ち、合計で購買決断を完結させる設計。</p>
    </div>
  </div>
</div>

<!-- SECTION 4: 素材ライブラリ -->
<div class="section">
  <div class="section-header">
    <div class="section-num">4</div>
    <div>
      <div class="section-title">素材ライブラリ</div>
      <div class="section-desc">AI生成に渡した実写素材一覧</div>
    </div>
  </div>
  <div class="asset-grid">{assets_html}</div>
</div>

<!-- SECTION 5: 最終版サブ画像 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">5</div>
    <div>
      <div class="section-title">最終版 Amazon サブ画像 — v5 Premium</div>
      <div class="section-desc">ブランドカラー #3ABCEE × 明朝体 × マルチモーダル入力 × 競合差別化</div>
    </div>
  </div>
  {banners_html}
</div>

<!-- SECTION 6: メイン画像 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">6</div>
    <div>
      <div class="section-title">Amazon メイン画像 — 5パターン</div>
      <div class="section-desc">純白背景 × テキストなし × Amazon ポリシー準拠</div>
    </div>
  </div>
  <div class="main-grid">{mains_html}</div>
</div>

<!-- FOOTER -->
<div class="footer">
  <p>Camicks | 和紙シークレット5本指ソックス | marusawa / 澤田株式会社</p>
  <p style="margin-top:8px">Generated by Banner Park v7.0 × Nano Banana Pro (gemini-3-pro-image-preview) | {now}</p>
</div>

</div><!-- /container -->
</body>
</html>"""

report_path = f'{out_dir}/process_report.html'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(HTML)

size_kb = os.path.getsize(report_path) // 1024
print(f"✅ レポート生成完了!")
print(f"   {report_path}")
print(f"   サイズ: {size_kb:,}KB")
print(f"\n📂 open \"{report_path}\"")
