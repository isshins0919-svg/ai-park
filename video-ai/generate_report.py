"""
プルースト2 好調CR — 分析レポート HTML生成
"""
import json

with open("video-ai/batch_results.json", encoding="utf-8") as f:
    data = json.load(f)

# 共通パターン集計
hook_seconds = [int(d["fv"]["hook_second"]) for d in data if d["fv"]["hook_second"].isdigit()]
cut_intervals = [float(d["tempo"]["cut_interval_sec"]) for d in data]
chars = [int(d["telop"]["chars_per_screen"]) for d in data if d["telop"]["chars_per_screen"].isdigit()]
cta_seconds = [int(d["cta"]["start_second"]) for d in data if d["cta"]["start_second"].isdigit()]

avg_cut = sum(cut_intervals) / len(cut_intervals)
avg_chars = sum(chars) / len(chars)
avg_cta = sum(cta_seconds) / len(cta_seconds)

html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>プルースト2 好調クリエイティブ 分析レポート</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Helvetica Neue', sans-serif; background: #0f0f0f; color: #f0f0f0; }}
  .hero {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 60px 40px; text-align: center; border-bottom: 2px solid #e94560; }}
  .hero h1 {{ font-size: 2rem; font-weight: 900; color: #fff; margin-bottom: 8px; }}
  .hero p {{ color: #aaa; font-size: 0.95rem; }}
  .badge {{ display: inline-block; background: #e94560; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-bottom: 16px; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}
  h2 {{ font-size: 1.3rem; font-weight: 800; color: #e94560; margin: 40px 0 20px; border-left: 4px solid #e94560; padding-left: 12px; }}
  h3 {{ font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 10px; }}

  /* KPI Cards */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 40px; }}
  .kpi {{ background: #1a1a2e; border: 1px solid #333; border-radius: 12px; padding: 24px 16px; text-align: center; }}
  .kpi .num {{ font-size: 2.2rem; font-weight: 900; color: #e94560; }}
  .kpi .label {{ font-size: 0.8rem; color: #aaa; margin-top: 6px; }}

  /* Pattern grid */
  .pattern-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
  .card {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 12px; padding: 24px; }}
  .card-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }}
  .pattern-badge {{ background: #e94560; color: #fff; font-size: 0.75rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; white-space: nowrap; }}
  .card-title {{ font-size: 0.85rem; color: #ccc; }}
  .hook {{ background: #0f3460; border-radius: 8px; padding: 12px; margin-bottom: 12px; font-size: 0.95rem; font-weight: 700; color: #fff; }}
  .hook span {{ color: #ffd700; }}
  .detail-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #2a2a4a; font-size: 0.82rem; }}
  .detail-row:last-child {{ border-bottom: none; }}
  .detail-key {{ color: #aaa; }}
  .detail-val {{ color: #fff; font-weight: 600; text-align: right; max-width: 60%; }}
  .reasons {{ margin-top: 12px; }}
  .reason {{ background: #0f1b35; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-size: 0.8rem; color: #ccc; }}
  .reason::before {{ content: "✓ "; color: #4caf50; font-weight: 700; }}

  /* Template section */
  .template-box {{ background: #1a1a2e; border: 2px solid #e94560; border-radius: 12px; padding: 28px; }}
  .template-row {{ display: grid; grid-template-columns: 120px 1fr; gap: 16px; padding: 14px 0; border-bottom: 1px solid #2a2a4a; align-items: start; }}
  .template-row:last-child {{ border-bottom: none; }}
  .template-label {{ background: #e94560; color: #fff; border-radius: 6px; padding: 6px 10px; font-size: 0.8rem; font-weight: 700; text-align: center; }}
  .template-content {{ font-size: 0.88rem; color: #f0f0f0; line-height: 1.7; }}
  .template-content strong {{ color: #ffd700; }}

  /* Telop rules */
  .telop-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .telop-card {{ background: #1a1a2e; border-radius: 10px; padding: 20px; border: 1px solid #333; }}
  .telop-card .icon {{ font-size: 1.8rem; margin-bottom: 10px; }}
  .telop-card h4 {{ font-size: 0.9rem; color: #e94560; margin-bottom: 8px; }}
  .telop-card p {{ font-size: 0.82rem; color: #ccc; line-height: 1.6; }}

  /* Insight */
  .insight-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .insight {{ background: #1a1a2e; border-radius: 10px; padding: 20px; border-top: 3px solid #e94560; }}
  .insight h4 {{ font-size: 0.9rem; color: #fff; margin-bottom: 8px; }}
  .insight p {{ font-size: 0.82rem; color: #bbb; line-height: 1.6; }}

  @media (max-width: 768px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .pattern-grid {{ grid-template-columns: 1fr; }}
    .telop-grid {{ grid-template-columns: 1fr; }}
    .insight-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="hero">
  <div class="badge">好調CR分析レポート</div>
  <h1>プルースト2 勝ちクリエイティブ 解剖</h1>
  <p>7パターン × Gemini動画解析 — 好調の構造を数値化</p>
</div>

<div class="container">

  <h2>サマリー KPI</h2>
  <div class="kpi-grid">
    <div class="kpi">
      <div class="num">0秒</div>
      <div class="label">全7本のフック出現タイミング<br>（全員0秒スタート）</div>
    </div>
    <div class="kpi">
      <div class="num">{avg_cut:.1f}秒</div>
      <div class="label">平均カット間隔<br>（最速2秒〜最遅5秒）</div>
    </div>
    <div class="kpi">
      <div class="num">{avg_chars:.0f}文字</div>
      <div class="label">1画面あたり平均文字数<br>（12〜15文字が適正）</div>
    </div>
    <div class="kpi">
      <div class="num">{avg_cta:.0f}秒〜</div>
      <div class="label">CTA開始タイミング<br>（51〜59秒が黄金帯）</div>
    </div>
  </div>

  <h2>7パターン 詳細解析</h2>
  <div class="pattern-grid">
"""

for d in data:
    html += f"""
    <div class="card">
      <div class="card-header">
        <span class="pattern-badge">{d['pattern']}</span>
        <span class="card-title">{d['video_name'][:35]}...</span>
      </div>
      <div class="hook">「<span>{d['fv']['hook_text']}</span>」</div>
      <div class="detail-row"><span class="detail-key">フック出現</span><span class="detail-val">{d['fv']['hook_second']}秒</span></div>
      <div class="detail-row"><span class="detail-key">カット間隔</span><span class="detail-val">約{d['tempo']['cut_interval_sec']}秒</span></div>
      <div class="detail-row"><span class="detail-key">文字数/画面</span><span class="detail-val">{d['telop']['chars_per_screen']}文字</span></div>
      <div class="detail-row"><span class="detail-key">テロップ強調</span><span class="detail-val">{d['telop']['emphasis_style']}</span></div>
      <div class="detail-row"><span class="detail-key">CTA開始</span><span class="detail-val">{d['cta']['start_second']}秒〜</span></div>
      <div class="detail-row"><span class="detail-key">CTA文言</span><span class="detail-val">{d['cta']['text']}</span></div>
      <div class="detail-row"><span class="detail-key">ボディ構造</span><span class="detail-val">{d['body']['structure'][:40]}...</span></div>
      <div class="reasons">
        {''.join(f'<div class="reason">{r}</div>' for r in d['winning_reasons'])}
      </div>
    </div>
"""

html += f"""
  </div>

  <h2>勝ちテンプレート（全パターン共通）</h2>
  <div class="template-box">
    <div class="template-row">
      <div class="template-label">FV<br>0秒</div>
      <div class="template-content">
        <strong>「〇〇な人、絶対見て」</strong>でターゲット名指し<br>
        → 全7本が0秒スタート。視聴者に「自分のことだ」と思わせる
      </div>
    </div>
    <div class="template-row">
      <div class="template-label">共感<br>3〜8秒</div>
      <div class="template-content">
        悩んでいた「誰か」の体験を語る（母・姉・友人）<br>
        → 直接的な自己主張より第三者の体験が信頼度UP
      </div>
    </div>
    <div class="template-row">
      <div class="template-label">解決策<br>8〜25秒</div>
      <div class="template-content">
        原因の科学的説明 → 「特攻ケア」への期待醸成<br>
        → <strong>「ワキガ手術医と共同開発」</strong>が権威付けの定番
      </div>
    </div>
    <div class="template-row">
      <div class="template-label">証拠<br>25〜50秒</div>
      <div class="template-content">
        商品名 + 具体的な変化（匂いが消えた・自信が持てた）<br>
        → 数字・称号（No.1）で信頼性を数値化
      </div>
    </div>
    <div class="template-row">
      <div class="template-label">CTA<br>51〜59秒</div>
      <div class="template-content">
        <strong>「絶対使ってみて」「今すぐ詳細をクリック」</strong><br>
        → 初回980円・送料無料・縛りなし を必ず添える
      </div>
    </div>
  </div>

  <h2>テロップ設計ルール</h2>
  <div class="telop-grid">
    <div class="telop-card">
      <div class="icon">🎨</div>
      <h4>強調スタイル</h4>
      <p>
        <strong>黄色背景 × 黒文字</strong>が最多（5/7本）<br>
        赤文字・白文字に青フチも使用<br>
        → 感情ワードに色を集中させる
      </p>
    </div>
    <div class="telop-card">
      <div class="icon">📏</div>
      <h4>文字量</h4>
      <p>
        1画面あたり <strong>12〜15文字</strong>が適正<br>
        平均 {avg_chars:.0f}文字<br>
        → これ以上は読み飛ばされる
      </p>
    </div>
    <div class="telop-card">
      <div class="icon">📐</div>
      <h4>レイアウト使い分け</h4>
      <p>
        <strong>1行大文字</strong>: 感情ワード（ヤバイ / 絶対見て）<br>
        <strong>2行表示</strong>: 悩み描写・解説・体験談<br>
        → メリハリが離脱防止になる
      </p>
    </div>
  </div>

  <h2>パターン別 使い分けインサイト</h2>
  <div class="insight-grid">
    <div class="insight">
      <h4>語り系（最多）</h4>
      <p>カット2〜3秒の高速展開。早口でまくしたてるテンポ。産後・インナー着用者がコアターゲット。北口さん・ちゃそが好実績。</p>
    </div>
    <div class="insight">
      <h4>AIキャラ系</h4>
      <p>医者キャラで権威付け。カット5秒とやや落ち着いたテンポ。冬訴求・季節限定感との相性が良い。CTA文言が「今すぐ詳細クリック」に統一。</p>
    </div>
    <div class="insight">
      <h4>耳垢FV系</h4>
      <p>「耳垢型ワキガ」という超具体的ターゲット絞り込みがフック。内視鏡映像など医療ビジュアルとの組み合わせで高信頼感を演出。</p>
    </div>
  </div>

</div>
</body>
</html>"""

path = "reports/proust2_creative_analysis.html"
with open(path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ レポート生成完了 → {path}")
