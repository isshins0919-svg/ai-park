"""
プルーストクリーム2 新台本 cream2_002 vs cream2_001 ベクトル比較
勝ちDNA継承性と訴求角度の新規性を数値で検証
"""
import os, json, time, re
from pathlib import Path
import numpy as np

def _load_env(var):
    if os.environ.get(var):
        return
    for rc in [Path.home() / ".zshrc", Path.home() / ".zshenv"]:
        if not rc.exists():
            continue
        try:
            for line in rc.read_text().splitlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                m = re.match(rf'export\s+{var}=["\']?([^"\'#\s]+)["\']?', line)
                if m:
                    os.environ[var] = m.group(1)
                    return
        except Exception:
            pass

_load_env('GEMINI_API_KEY_1')

from google import genai
client = genai.Client(api_key=os.environ['GEMINI_API_KEY_1'])

def embed(text):
    time.sleep(0.3)
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

slug = 'proust'
out = f'research-park/output/{slug}'

# 既存ベクトルDB読み込み
vectors = json.load(open(f'{out}/all_vectors.json'))
v001 = {v['section']: v for v in vectors if v.get('script_id') == 'cream2_001' and v.get('category') == 'winner_script_section'}
v001_full = [v for v in vectors if v.get('script_id') == 'cream2_001' and v.get('category') == 'winner_script_full'][0]

# 新台本 cream2_002
full_002 = """【悔しい】市販のデオドラントでは絶対に消えない理由。実は汗を止めてもワキガは消えない。原因はワキの奥に住み着いた100種類以上の菌。しかもこの菌、放置すれば年々濃くなる。50代以降に悪化する人は約8割と報告されている。そこで、ワキガ手術医が監修。市販品では届かない"菌のコア"に挑むために開発したのが「切らないワキガ対策」。殺菌成分を2種類配合し角質層の奥まで浸透。朝のひと塗りで夜までニオイを封じ込める。だからワキガに悩む30万人に選ばれてる。そんなクリニック専売品の「切らないワキガ対策」がこの動画から初回97%OFFの210円でGETできる。少しでも多くの人に使って欲しいから、送料無料お届け回数の約束もナシ！ワキガ悩み卒業したい人は今すぐ詳細をクリック"""

sections_002 = [
    {"section": "hook", "text": "【悔しい】市販のデオドラントでは絶対に消えない理由"},
    {"section": "problem", "text": "実は汗を止めてもワキガは消えない。原因はワキの奥に住み着いた100種類以上の菌"},
    {"section": "urgency", "text": "しかもこの菌、放置すれば年々濃くなる。50代以降に悪化する人は約8割と報告されている"},
    {"section": "solution_origin", "text": "そこで、ワキガ手術医が監修。市販品では届かない菌のコアに挑むために開発したのが「切らないワキガ対策」"},
    {"section": "mechanism", "text": "殺菌成分を2種類配合し角質層の奥まで浸透。朝のひと塗りで夜までニオイを封じ込める"},
    {"section": "social_proof", "text": "だからワキガに悩む30万人に選ばれてる"},
    {"section": "offer", "text": "そんなクリニック専売品の「切らないワキガ対策」がこの動画から初回97%OFFの210円でGETできる"},
    {"section": "risk_reversal", "text": "少しでも多くの人に使って欲しいから、送料無料お届け回数の約束もナシ！"},
    {"section": "cta", "text": "ワキガ悩み卒業したい人は今すぐ詳細をクリック"},
]

print("=== cream2_002 ベクトル化中 ===")
full_vec_002 = embed(full_002)
print(f"  ✅ 全文 (dim={len(full_vec_002)})")

for s in sections_002:
    s['vector'] = embed(s['text'])
    print(f"  ✅ {s['section']}")

# ============================================================
# 全文類似度
# ============================================================
full_sim = cosine_sim(full_vec_002, v001_full['vector'])

print(f"\n=== 全文 × 全文 類似度 ===")
print(f"  cream2_001 vs cream2_002: {full_sim:.4f}")
zone = "✅ 勝ちDNA継承ゾーン" if 0.75 <= full_sim <= 0.90 else ("⚠️ 似すぎ（冗長リスク）" if full_sim > 0.90 else "⚠️ 離れすぎ（DNA継承弱い）")
print(f"  判定: {zone}")

# ============================================================
# セクション別類似度
# ============================================================
print(f"\n=== セクション別 001 vs 002 類似度 ===")
print(f"  (目標: hook/problem/urgency/solution_origin/mechanism = 0.70〜0.85 / social_proof/offer/risk_reversal/cta = 0.95+)")
print()
print(f"  {'セクション':18} {'類似度':8} {'目標':18} {'判定'}")
print(f"  {'-'*60}")

novel_sections = ['hook', 'problem', 'urgency', 'solution_origin', 'mechanism']
preserved_sections = ['social_proof', 'offer', 'risk_reversal', 'cta']

results = []
for s in sections_002:
    sec = s['section']
    sim = cosine_sim(s['vector'], v001[sec]['vector'])

    if sec in novel_sections:
        target = "0.70〜0.85(新角度)"
        if 0.70 <= sim <= 0.85:
            judge = "✅ 理想"
        elif sim > 0.85:
            judge = "⚠️ 変化弱い"
        elif sim >= 0.55:
            judge = "✓ 大幅刷新"
        else:
            judge = "⚠️ DNA逸脱"
    else:
        target = "0.95+(保持)"
        if sim >= 0.95:
            judge = "✅ 勝ち要素保持"
        else:
            judge = "⚠️ 意図せず改変"

    print(f"  {sec:18} {sim:.4f}   {target:18} {judge}")
    results.append({"section": sec, "sim": round(sim, 4), "target": target, "judge": judge})

# ============================================================
# 総合評価
# ============================================================
print(f"\n=== 総合評価 ===")
novel_avg = np.mean([r['sim'] for r in results if r['section'] in novel_sections])
preserved_avg = np.mean([r['sim'] for r in results if r['section'] in preserved_sections])

print(f"  刷新セクション平均類似度: {novel_avg:.4f}  (目標: 0.70〜0.85)")
print(f"  保持セクション平均類似度: {preserved_avg:.4f}  (目標: 0.95+)")
print(f"  全文類似度:              {full_sim:.4f}  (目標: 0.75〜0.90)")

novel_ok = 0.70 <= novel_avg <= 0.85
preserved_ok = preserved_avg >= 0.95
full_ok = 0.75 <= full_sim <= 0.90

if novel_ok and preserved_ok and full_ok:
    print(f"\n  🏆 判定: 勝ちDNA継承×新規訴求の両立成功")
elif novel_ok and full_ok and not preserved_ok:
    print(f"\n  ⚠️  判定: 保持すべきセクションが意図せず動いている。offer/CTA周辺の表現を戻す")
elif preserved_ok and not novel_ok:
    print(f"\n  ⚠️  判定: 新角度が弱い。hook/problem の言語を更に遠くへ")
else:
    print(f"\n  🔧 判定: 調整の余地あり")

# JSON 保存
analysis = {
    "base_script": "cream2_001",
    "new_script": "cream2_002",
    "analyzed_at": "2026-04-24",
    "full_similarity": round(full_sim, 4),
    "sections": results,
    "novel_avg": round(float(novel_avg), 4),
    "preserved_avg": round(float(preserved_avg), 4),
    "verdict": {
        "novel_ok": novel_ok,
        "preserved_ok": preserved_ok,
        "full_ok": full_ok,
    }
}
with open(f'{out}/winners/cream2_002_vs_001_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

print(f"\n  📝 分析結果保存: {out}/winners/cream2_002_vs_001_analysis.json")
