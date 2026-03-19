"""
Camicks Amazon出品 戦略レポート
16:00 Amazon代理店MTG用
"""

import os, base64, json
from datetime import datetime

out_dir = 'banner-park/output/camicks'
amazon_dir = f'{out_dir}/amazon_v1'
report_path = f'{out_dir}/amazon_strategy_report.html'

def img_to_base64(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

# 画像読み込み
images = []
image_specs = [
    {"file": "amazon_00_main.png",      "label": "メイン画像",                        "copy": "第一印象「普通の靴下」→タイトルとパンチライン成立"},
    {"file": "amazon_01_punchline.png", "label": "サブ①｜これが5本指なんです。",     "copy": "シークレット構造の驚き → CTR最大化を狙うパンチライン"},
    {"file": "amazon_02_material.png",  "label": "サブ②｜一日中、蒸れない理由がある。","copy": "camifine®和紙40%の独自素材 → 価格差の説明"},
    {"file": "amazon_03_structure.png", "label": "サブ③｜なぜ、外から見えないのか。", "copy": "パーティション構造×ホールガーメント製法の仕組み説明"},
    {"file": "amazon_04_health.png",    "label": "サブ④｜健康設計。アーチサポート。", "copy": "外反母趾・疲労軽減 → レビューの声で証拠"},
    {"file": "amazon_05_scene.png",     "label": "サブ⑤｜脱いでも、バレない。",      "copy": "ビジネス×カジュアル×スポーツ → オールシーン対応"},
    {"file": "amazon_06_brand.png",     "label": "サブ⑥｜55年分の本気が、1足に入ってる。","copy": "1969年創業・大阪泉州・日本製・糸から自社開発 → 価格正当化"},
]

for spec in image_specs:
    path = os.path.join(amazon_dir, spec['file'])
    b64 = img_to_base64(path)
    images.append({**spec, 'b64': b64, 'exists': b64 is not None})

html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Camicks Amazon出品戦略レポート</title>
<style>
  :root {{
    --blue: #3ABCEE;
    --navy: #1a2e3d;
    --gray: #666;
    --light: #f8f9fa;
    --border: #e5e7eb;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Hiragino Sans', 'Noto Sans JP', sans-serif; background: #fff; color: var(--navy); }}

  /* ============ COVER ============ */
  .cover {{
    background: var(--navy);
    color: #fff;
    padding: 80px 60px;
    min-height: 320px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .cover .tag {{ color: var(--blue); font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 24px; }}
  .cover h1 {{ font-size: 36px; font-weight: 700; line-height: 1.3; margin-bottom: 16px; }}
  .cover h1 span {{ color: var(--blue); }}
  .cover .meta {{ font-size: 14px; color: rgba(255,255,255,0.6); margin-top: 32px; border-top: 1px solid rgba(255,255,255,0.15); padding-top: 24px; display: flex; gap: 32px; }}

  /* ============ SECTION ============ */
  .section {{ padding: 64px 60px; border-bottom: 1px solid var(--border); }}
  .section:last-child {{ border-bottom: none; }}
  .section-alt {{ background: var(--light); }}
  .section-label {{ font-size: 11px; color: var(--blue); letter-spacing: 3px; text-transform: uppercase; font-weight: 600; margin-bottom: 12px; }}
  .section-title {{ font-size: 26px; font-weight: 700; margin-bottom: 32px; line-height: 1.3; }}
  .section-title span {{ color: var(--blue); }}

  /* ============ TABLES ============ */
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th {{ background: var(--navy); color: #fff; padding: 12px 16px; text-align: left; font-weight: 600; font-size: 12px; letter-spacing: 0.5px; }}
  td {{ padding: 12px 16px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f0f9ff; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }}
  .badge-blue {{ background: #e0f4fd; color: #0077a8; }}
  .badge-green {{ background: #e6f4ea; color: #1e7e34; }}
  .badge-orange {{ background: #fff3e0; color: #e65100; }}
  .badge-red {{ background: #fde8e8; color: #c0392b; }}
  .num {{ font-size: 20px; font-weight: 700; color: var(--blue); }}

  /* ============ TITLE BOX ============ */
  .title-box {{
    background: var(--navy);
    color: #fff;
    padding: 32px 40px;
    border-radius: 12px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
  }}
  .title-box::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 5px; height: 100%;
    background: var(--blue);
  }}
  .title-box .title-label {{ font-size: 11px; color: var(--blue); letter-spacing: 2px; margin-bottom: 12px; }}
  .title-box .title-text {{ font-size: 22px; font-weight: 700; line-height: 1.5; }}
  .title-box .title-intent {{ font-size: 13px; color: rgba(255,255,255,0.65); margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.15); }}

  /* ============ BULLETS ============ */
  .bullet-list {{ display: flex; flex-direction: column; gap: 16px; }}
  .bullet-item {{
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    display: flex;
    gap: 20px;
    align-items: flex-start;
    transition: box-shadow 0.2s;
  }}
  .bullet-item:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
  .bullet-num {{
    width: 32px; height: 32px;
    background: var(--blue);
    color: #fff;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; flex-shrink: 0;
  }}
  .bullet-text {{ flex: 1; }}
  .bullet-head {{ font-weight: 700; font-size: 15px; color: var(--navy); margin-bottom: 6px; }}
  .bullet-body {{ font-size: 13px; color: var(--gray); line-height: 1.7; }}

  /* ============ KW ============ */
  .kw-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .kw-card {{
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
  }}
  .kw-word {{ font-size: 15px; font-weight: 700; margin-bottom: 8px; }}
  .kw-vol {{ font-size: 28px; font-weight: 700; color: var(--blue); }}
  .kw-unit {{ font-size: 12px; color: var(--gray); }}
  .kw-tier {{ font-size: 11px; padding: 3px 10px; border-radius: 20px; display: inline-block; margin-top: 8px; font-weight: 600; }}
  .tier-1 {{ background: #e0f4fd; color: #0077a8; }}
  .tier-2 {{ background: #e6f4ea; color: #1e7e34; }}
  .tier-3 {{ background: #f3f0ff; color: #6c3cbe; }}

  /* ============ IMAGES ============ */
  .image-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }}
  .image-card {{
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }}
  .image-card.main-card {{ grid-column: 1 / -1; }}
  .image-card img {{ width: 100%; display: block; }}
  .image-info {{ padding: 16px 20px; }}
  .image-info .img-label {{ font-size: 12px; color: var(--blue); font-weight: 600; letter-spacing: 1px; margin-bottom: 6px; }}
  .image-info .img-copy {{ font-size: 13px; color: var(--gray); line-height: 1.6; }}
  .image-placeholder {{ background: var(--light); display: flex; align-items: center; justify-content: center; height: 200px; color: var(--gray); font-size: 14px; }}

  /* ============ STRATEGY ============ */
  .strategy-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }}
  .strategy-card {{
    border-radius: 12px;
    padding: 28px;
    border: 1px solid var(--border);
  }}
  .strategy-card.highlight {{ background: var(--navy); color: #fff; border-color: var(--navy); }}
  .strategy-card.highlight .s-label {{ color: var(--blue); }}
  .strategy-card.highlight .s-body {{ color: rgba(255,255,255,0.75); }}
  .s-label {{ font-size: 11px; letter-spacing: 2px; color: var(--blue); font-weight: 600; margin-bottom: 12px; }}
  .s-title {{ font-size: 18px; font-weight: 700; margin-bottom: 12px; line-height: 1.4; }}
  .s-body {{ font-size: 13px; color: var(--gray); line-height: 1.8; }}

  /* ============ PRICE ============ */
  .price-compare {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }}
  .price-card {{ border-radius: 12px; padding: 28px; border: 2px solid var(--border); }}
  .price-card.ours {{ border-color: var(--blue); }}
  .price-label {{ font-size: 12px; letter-spacing: 1px; color: var(--gray); margin-bottom: 12px; }}
  .price-main {{ font-size: 36px; font-weight: 700; color: var(--navy); }}
  .price-sub {{ font-size: 13px; color: var(--gray); margin-top: 8px; }}

  /* ============ NEXT ACTIONS ============ */
  .action-list {{ display: flex; flex-direction: column; gap: 12px; }}
  .action-item {{
    display: flex; align-items: center; gap: 16px;
    padding: 16px 20px; border: 1px solid var(--border); border-radius: 10px;
  }}
  .action-icon {{ width: 36px; height: 36px; background: var(--blue); color: #fff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }}
  .action-text {{ font-size: 14px; font-weight: 600; }}
  .action-sub {{ font-size: 12px; color: var(--gray); margin-top: 4px; }}

  /* ============ PRINT ============ */
  @media print {{
    body {{ background: #fff; }}
    .cover {{ background: #1a2e3d !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .section {{ padding: 40px 40px; }}
    .image-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .kw-grid {{ grid-template-columns: repeat(3, 1fr); }}
  }}
</style>
</head>
<body>

<!-- COVER -->
<div class="cover">
  <div class="tag">Amazon出品戦略レポート — {datetime.now().strftime('%Y年%m月%d日')}</div>
  <h1>Camicks｜Amazon出品<br><span>クリエイティブ × KW × 価格戦略</span></h1>
  <div class="meta">
    <span>🧦 ミドル丈シークレット五本指ソックス</span>
    <span>📦 単品4SKU + セット2SKU</span>
    <span>🎯 メンズ・レディース兼用 / ビジネス特化</span>
    <span>🏭 日本製・大阪泉州・創業55年</span>
  </div>
</div>

<!-- 1. 競合分析 -->
<div class="section section-alt">
  <div class="section-label">COMPETITIVE INTELLIGENCE</div>
  <div class="section-title">競合分析｜<span>SLEEPSINERO vs Camicks</span></div>
  <table>
    <thead><tr><th>指標</th><th>SLEEPSINERO（競合）</th><th>Camicks（自社）</th></tr></thead>
    <tbody>
      <tr><td>価格</td><td>¥1,343〜¥2,080 / <strong>5足セット</strong></td><td>¥1,540 / <strong>1足</strong>（単品）</td></tr>
      <tr><td>1足あたり</td><td>¥269〜¥416</td><td><strong>¥1,540</strong>（6倍の価格差）</td></tr>
      <tr><td>レビュー</td><td>4.5★ / 611件（72%が★5）</td><td>4.6★ / 9件（88.9%が★5）</td></tr>
      <tr><td>ランク</td><td>レディースランニングソックス <strong>1位</strong></td><td>未出品</td></tr>
      <tr><td>月間販売数</td><td>1,000点以上 / 7万人以上（3ヶ月）</td><td>—</td></tr>
      <tr><td>素材</td><td>コットン80-90%（汎用）</td><td><strong>camifine®和紙40%（自社開発）</strong></td></tr>
      <tr><td>構造</td><td>通常の5本指ソックス</td><td><strong>シークレット構造（外から見えない）</strong></td></tr>
      <tr><td>製造</td><td>不明</td><td><strong>日本製・大阪泉州・創業55年・糸から自社開発</strong></td></tr>
      <tr><td>ターゲット</td><td>レディース・スポーツ特化</td><td><strong>男女兼用・ビジネスシーン特化</strong></td></tr>
      <tr><td>主な弱点</td><td>指が入れにくい・薄手で冬は重ね履き必要</td><td>価格差の正当化が必要</td></tr>
    </tbody>
  </table>

  <div style="margin-top:32px; padding:24px; background:#fff3e0; border-radius:10px; border-left:4px solid #e65100;">
    <div style="font-weight:700; margin-bottom:8px; color:#e65100;">⚠️ 価格差の正当化が最大の課題</div>
    <div style="font-size:14px; color:#666; line-height:1.8;">
      SLEEPSINEROは5足で¥1,343。Camicksは1足で¥1,540。同じ土俵では戦えない。<br>
      →「別カテゴリ」として見せる戦略が必須。<strong>シークレット構造 × 和紙素材 × ビジネスシーン</strong>で土俵を変える。
    </div>
  </div>
</div>

<!-- 2. 価格・SKU戦略 -->
<div class="section">
  <div class="section-label">PRICING & SKU STRATEGY</div>
  <div class="section-title">価格 × <span>SKUラインナップ</span></div>

  <div class="price-compare">
    <div class="price-card">
      <div class="price-label">単品（4SKU）</div>
      <div class="price-main">¥1,540</div>
      <div class="price-sub">ブラック / ダークグレー / ネイビー / オフ</div>
    </div>
    <div class="price-card ours">
      <div class="price-label">セット — 1足あたり価格を下げてコスパ感を演出</div>
      <div class="price-main">¥3,980〜¥5,980</div>
      <div class="price-sub">3足カラーMIX（¥1,327/足）/ 5足カラーMIX（¥1,196/足）</div>
    </div>
  </div>

  <table>
    <thead><tr><th>#</th><th>商品</th><th>カラー</th><th>価格</th><th>1足あたり</th><th>ターゲット</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>単品</td><td>ブラック</td><td>¥1,540</td><td>¥1,540</td><td>男女・ビジネス鉄板</td></tr>
      <tr><td>2</td><td>単品</td><td>ダークグレー</td><td>¥1,540</td><td>¥1,540</td><td>ビジネス男性</td></tr>
      <tr><td>3</td><td>単品</td><td>ネイビー</td><td>¥1,540</td><td>¥1,540</td><td>ビジネス男性</td></tr>
      <tr><td>4</td><td>単品</td><td>オフ</td><td>¥1,540</td><td>¥1,540</td><td>女性・カジュアル</td></tr>
      <tr><td>5</td><td><span class="badge badge-blue">3足セット</span></td><td>カラーMIX</td><td>¥3,980</td><td>¥1,327</td><td>「まずお試し」層</td></tr>
      <tr><td>6</td><td><span class="badge badge-green">5足セット</span></td><td>カラーMIX</td><td>¥5,980</td><td>¥1,196</td><td>週5日ヘビーユーザー</td></tr>
    </tbody>
  </table>
</div>

<!-- 3. 商品タイトル -->
<div class="section section-alt">
  <div class="section-label">PRODUCT TITLE & BULLETS</div>
  <div class="section-title">商品タイトル × <span>箇条書き5項目</span></div>

  <div class="title-box">
    <div class="title-label">CONFIRMED TITLE — 確定済み</div>
    <div class="title-text">【外から見えない】Camicks 五本指靴下 メンズ レディース シークレット 蒸れない 和紙40% 日本製 23-27cm</div>
    <div class="title-intent">
      戦略意図：メイン画像（普通の靴下に見える）× タイトル冒頭「外から見えない」→ 認知ギャップでCTR最大化。
      SEOはタイトル後半にKWを配置（五本指靴下・シークレット・蒸れない・和紙・日本製）。
    </div>
  </div>

  <div class="bullet-list">
    <div class="bullet-item">
      <div class="bullet-num">1</div>
      <div class="bullet-text">
        <div class="bullet-head">【脱いでもバレない、シークレット5本指】</div>
        <div class="bullet-body">外側は普通の靴下。内側だけ5本指に分かれるパーティション構造。職場でも、デートでも、靴を脱ぐ場面を選ばない。</div>
      </div>
    </div>
    <div class="bullet-item">
      <div class="bullet-num">2</div>
      <div class="bullet-text">
        <div class="bullet-head">【和紙40%の吸湿速乾。一日中、蒸れない】</div>
        <div class="bullet-body">自社開発素材camifine®（カミファイン）は、和紙を糸から開発した独自ファイバー。汗を吸ってすぐ乾く。革靴・ブーツのビジネスシーンでも、夏の運動でも快適。</div>
      </div>
    </div>
    <div class="bullet-item">
      <div class="bullet-num">3</div>
      <div class="bullet-text">
        <div class="bullet-head">【外反母趾・足の疲れに。健康設計のアーチサポート】</div>
        <div class="bullet-body">足指を正しい位置に配置し、土踏まずを引き上げるアーチサポート構造。「痛みがなくなりました」というリピーターの声多数。</div>
      </div>
    </div>
    <div class="bullet-item">
      <div class="bullet-num">4</div>
      <div class="bullet-text">
        <div class="bullet-head">【縫い目ゼロ。細めの靴でも履ける】</div>
        <div class="bullet-body">ホールガーメント製法で立体的に編み上げるため縫い目なし。つま先のごつつきがなく、パンプスやスニーカーでもストレスなし。</div>
      </div>
    </div>
    <div class="bullet-item">
      <div class="bullet-num">5</div>
      <div class="bullet-text">
        <div class="bullet-head">【創業55年・大阪泉州の日本製。糸から自社開発】</div>
        <div class="bullet-body">1969年創業の澤田株式会社が、糸の開発から製造まで一貫生産。有害物質を含まない染料で15色展開。毎日履きたくなる品質。</div>
      </div>
    </div>
  </div>
</div>

<!-- 4. KW戦略 -->
<div class="section">
  <div class="section-label">KEYWORD STRATEGY</div>
  <div class="section-title">KW選定｜<span>3レイヤー戦略</span></div>

  <div style="margin-bottom:32px;">
    <div style="font-weight:700; margin-bottom:16px;">レイヤー① 集客KW（ボリューム最大・流入を稼ぐ）</div>
    <div class="kw-grid">
      <div class="kw-card"><div class="kw-word">靴下 5本指</div><div class="kw-vol">9,452</div><div class="kw-unit">件/月</div><div class="kw-tier tier-1">最優先</div></div>
      <div class="kw-card"><div class="kw-word">蒸れない靴下</div><div class="kw-vol">4,386</div><div class="kw-unit">件/月</div><div class="kw-tier tier-1">最優先</div></div>
      <div class="kw-card"><div class="kw-word">水虫 靴下</div><div class="kw-vol">3,443</div><div class="kw-unit">件/月</div><div class="kw-tier tier-1">優先</div></div>
      <div class="kw-card"><div class="kw-word">五本指靴下 レディース</div><div class="kw-vol">3,121</div><div class="kw-unit">件/月</div><div class="kw-tier tier-1">優先</div></div>
      <div class="kw-card"><div class="kw-word">五本指靴下</div><div class="kw-vol">2,379</div><div class="kw-unit">件/月</div><div class="kw-tier tier-1">最優先</div></div>
      <div class="kw-card"><div class="kw-word">足汗 靴下</div><div class="kw-vol">1,404</div><div class="kw-unit">件/月</div><div class="kw-tier tier-1">優先</div></div>
    </div>
  </div>

  <div style="margin-bottom:32px;">
    <div style="font-weight:700; margin-bottom:16px;">レイヤー② 差別化KW（競合ゼロ・転換率を上げる）</div>
    <div class="kw-grid">
      <div class="kw-card"><div class="kw-word">シークレット 五本指 靴下</div><div class="kw-vol">—</div><div class="kw-unit">競合ゼロ</div><div class="kw-tier tier-2">差別化</div></div>
      <div class="kw-card"><div class="kw-word">和紙 靴下</div><div class="kw-vol">—</div><div class="kw-unit">独自素材</div><div class="kw-tier tier-2">差別化</div></div>
      <div class="kw-card"><div class="kw-word">日本製 靴下</div><div class="kw-vol">—</div><div class="kw-unit">品質訴求</div><div class="kw-tier tier-2">差別化</div></div>
    </div>
  </div>

  <div>
    <div style="font-weight:700; margin-bottom:16px;">レイヤー③ 潜在層KW（悩み検索で引っかける）</div>
    <div class="kw-grid">
      <div class="kw-card"><div class="kw-word">ビジネス 蒸れない 靴下</div><div class="kw-vol">—</div><div class="kw-unit">ビジネス層</div><div class="kw-tier tier-3">潜在層</div></div>
      <div class="kw-card"><div class="kw-word">五本指 バレない</div><div class="kw-vol">—</div><div class="kw-unit">シークレット</div><div class="kw-tier tier-3">潜在層</div></div>
      <div class="kw-card"><div class="kw-word">外反母趾 靴下</div><div class="kw-vol">—</div><div class="kw-unit">健康悩み</div><div class="kw-tier tier-3">潜在層</div></div>
    </div>
  </div>
</div>

<!-- 5. Amazon商品画像 -->
<div class="section section-alt">
  <div class="section-label">CREATIVE — AMAZON PRODUCT IMAGES</div>
  <div class="section-title">Amazon商品画像｜<span>メイン1枚 + サブ6枚</span></div>
  <div style="margin-bottom:24px; font-size:13px; color:var(--gray);">
    設計思想：明朝体 × 余白 × #3ABCEE アクセント。競合の「インフォグラフィック過多・丸ゴシック・バブル吹き出し」と真逆の世界観で差別化。
  </div>
  <div class="image-grid">
"""

for i, spec in enumerate(images):
    is_main = i == 0
    card_class = "image-card main-card" if is_main else "image-card"
    html += f'<div class="{card_class}">'
    if spec['exists']:
        html += f'<img src="data:image/png;base64,{spec["b64"]}" alt="{spec["label"]}">'
    else:
        html += f'<div class="image-placeholder">画像なし: {spec["file"]}</div>'
    html += f"""
      <div class="image-info">
        <div class="img-label">{spec["label"]}</div>
        <div class="img-copy">{spec["copy"]}</div>
      </div>
    </div>"""

html += """
  </div>
</div>

<!-- 6. 差別化戦略 -->
<div class="section">
  <div class="section-label">DIFFERENTIATION STRATEGY</div>
  <div class="section-title">勝ち筋｜<span>土俵を変える戦略</span></div>
  <div class="strategy-grid">
    <div class="strategy-card highlight">
      <div class="s-label">CORE STRATEGY</div>
      <div class="s-title">「別カテゴリ」として戦う</div>
      <div class="s-body">SLEEPSINEROと同じ土俵（5足セット・低価格・コットン素材）では戦わない。<br><br>Camicksは「シークレット構造 × 和紙camifine® × 日本製55年」で全く異なるポジションを取る。</div>
    </div>
    <div class="strategy-card">
      <div class="s-label">TARGET</div>
      <div class="s-title">ビジネスシーンの蒸れ悩みに刺す</div>
      <div class="s-body">競合は「スポーツ・ランニング」特化。ビジネスマン（革靴・ブーツで蒸れる）層は空白地帯。23-27cmのミドル丈サイズ展開がメンズ対応を支える。</div>
    </div>
    <div class="strategy-card">
      <div class="s-label">CTR TACTIC</div>
      <div class="s-title">メイン画像 × タイトルのパンチライン</div>
      <div class="s-body">メイン画像は「普通の靴下に見える」→ タイトル冒頭「外から見えない」で認知ギャップ発生 → 「え？」でクリック率を上げる設計。</div>
    </div>
    <div class="strategy-card">
      <div class="s-label">PRICE JUSTIFICATION</div>
      <div class="s-title">セット展開で1足単価を下げる</div>
      <div class="s-body">単品¥1,540 vs 競合¥269/足の差を埋めるためセット展開。3足¥3,980（¥1,327/足）、5足¥5,980（¥1,196/足）で「コスパ感」を演出。</div>
    </div>
  </div>
</div>

<!-- 7. Next Actions -->
<div class="section section-alt">
  <div class="section-label">NEXT ACTIONS</div>
  <div class="section-title">出品完走に向けた<span>残りタスク</span></div>
  <div class="action-list">
    <div class="action-item">
      <div class="action-icon">1</div>
      <div>
        <div class="action-text">画像レビュー → 差し替え・修正対応</div>
        <div class="action-sub">今日生成したメイン+サブ6枚を確認。NGがあれば即修正して再生成。</div>
      </div>
    </div>
    <div class="action-item">
      <div class="action-icon">2</div>
      <div>
        <div class="action-text">JANコード取得 + 商標出願 → ブランドレジストリ申請</div>
        <div class="action-sub">出品前に必須。ブランド登録なしだとA+コンテンツが使えない。</div>
      </div>
    </div>
    <div class="action-item">
      <div class="action-icon">3</div>
      <div>
        <div class="action-text">KW精度向上 → SellerSpriteで競合流入KW調査</div>
        <div class="action-sub">今回のKWデータは代理店提供の概算値。SellerSpriteで競合（SLEEPSINERO ASIN: B0DX62GBMR）の流入KWを詳細取得。</div>
      </div>
    </div>
    <div class="action-item">
      <div class="action-icon">4</div>
      <div>
        <div class="action-text">Amazon Vine 申請 → 初期レビュー獲得</div>
        <div class="action-sub">出品直後に必ず申請。レビューゼロでは転換率が取れない。最優先初期設定。</div>
      </div>
    </div>
    <div class="action-item">
      <div class="action-icon">5</div>
      <div>
        <div class="action-text">SP/SD広告 → 出品直後に配信開始</div>
        <div class="action-sub">クリエイティブなしでも開始可能。まずオートターゲティングで走らせ、勝ちKWを特定してからマニュアルに切り替え。</div>
      </div>
    </div>
    <div class="action-item">
      <div class="action-icon">6</div>
      <div>
        <div class="action-text">A+コンテンツ制作（販売実績ができたら）</div>
        <div class="action-sub">ベーシック最大5枚から開始。プレミアム（最大7枚）は販売実績が必要。今回の画像素材を流用して制作。</div>
      </div>
    </div>
  </div>
</div>

<!-- FOOTER -->
<div style="background:var(--navy); color:rgba(255,255,255,0.5); padding:32px 60px; font-size:12px; display:flex; justify-content:space-between; align-items:center;">
  <span>Camicks Amazon出品戦略レポート</span>
  <span>Generated by 一進AI — Banner Park v7.0 × Amazon Park</span>
  <span>""" + datetime.now().strftime('%Y-%m-%d') + """</span>
</div>

</body>
</html>"""

with open(report_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ レポート生成完了: {report_path}")
print(f"   ファイルサイズ: {os.path.getsize(report_path)//1024}KB")
