"""
Amazon部長 一進 — KW分析君
6枚コピー × 検索意図ベクトル強度スコア + 価格正当化スコア
"""
import subprocess, os, json
import numpy as np

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass

_load_env('GEMINI_API_KEY_1')

from google import genai
client = genai.Client(api_key=os.environ['GEMINI_API_KEY_1'])

def embed(text):
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ============================================================
# KW検索意図ベクトル
# ============================================================
kw_intents = {
    "靴下 5本指":       "5本指ソックスを買いたい。足の蒸れ・ニオイ・外反母趾が気になっている。機能性重視だが見た目も気になる",
    "シークレット 5本指": "外から5本指と分からない靴下を探している。人前で靴を脱ぐ場面でバレたくない",
    "外反母趾 靴下":     "外反母趾に悩んでいる。足の痛み・変形を靴下でケアしたい",
    "和紙 靴下":         "和紙素材の靴下に興味がある。天然素材×機能性を重視している",
    "5本指靴下 おしゃれ": "5本指ソックスはおしゃれじゃないイメージがあったが、おしゃれなものを探している",
}

price_concept = "なぜ1足2480円なのか。57年糸屋が素材から設計した日本製。和紙40%自社開発素材camifine®。この価値があるから高い。安い5足セットとは根本が違う"

print("KW意図ベクトル生成中...")
kw_vecs = {kw: embed(intent) for kw, intent in kw_intents.items()}
price_vec = embed(price_concept)

# ============================================================
# 6枚コピー評価
# ============================================================
strategy = json.load(open('research-park/output/camicks/strategy.json'))
copies = strategy['salesCopy']['amazon6images']

results = []
print("\n" + "="*60)
print("  KW分析君 — コピー強度スコアリング")
print("="*60)

for copy in copies:
    text = copy['headline'] + "。" + copy['sub']
    vec = embed(text)

    kw_scores = {}
    for kw, kw_vec in kw_vecs.items():
        kw_scores[kw] = round(cosine_sim(vec, kw_vec), 3)

    price_score = round(cosine_sim(vec, price_vec), 3)
    avg_kw = round(np.mean(list(kw_scores.values())), 3)

    # 最も刺さるKW
    best_kw = max(kw_scores, key=kw_scores.get)
    worst_kw = min(kw_scores, key=kw_scores.get)

    status = "✅ GO" if avg_kw >= 0.68 else ("⚠️ REVISE" if avg_kw >= 0.62 else "❌ BLOCK→差し替え")

    results.append({
        "index": copy['index'],
        "headline": copy['headline'],
        "avg_kw": avg_kw,
        "price_score": price_score,
        "kw_scores": kw_scores,
        "best_kw": best_kw,
        "worst_kw": worst_kw,
        "status": status
    })

    print(f"\n[サブ{copy['index']}] 「{copy['headline']}」")
    print(f"  KW平均: {avg_kw}  価格正当化: {price_score}  → {status}")
    print(f"  最強KW: {best_kw}({kw_scores[best_kw]}) / 最弱KW: {worst_kw}({kw_scores[worst_kw]})")

# ============================================================
# 差し替え判定
# ============================================================
print("\n" + "="*60)
print("  差し替え判定")
print("="*60)

sorted_results = sorted(results, key=lambda x: x['avg_kw'])
weakest = sorted_results[0]
print(f"\n最弱: サブ{weakest['index']}「{weakest['headline']}」avg={weakest['avg_kw']}")

block_list = [r for r in results if "BLOCK" in r['status']]
revise_list = [r for r in results if "REVISE" in r['status']]

if block_list:
    print(f"❌ BLOCK（差し替え必須）: サブ{[r['index'] for r in block_list]}")
if revise_list:
    print(f"⚠️ REVISE（改善推奨）: サブ{[r['index'] for r in revise_list]}")
if not block_list and not revise_list:
    print("✅ 全枚 GO（差し替え不要）")

# ============================================================
# 保存
# ============================================================
os.makedirs('banner-park/output/camicks/amazon_cmo', exist_ok=True)
with open('banner-park/output/camicks/amazon_cmo/kw_scores.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n✅ kw_scores.json 保存完了")
print("→ Phase 2: コピー君 へ")
