"""
Phase 4: ベクトルインテリジェンス — Camicks
"""
import os, subprocess, json
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
slug = 'camicks'
out = f'research-park/output/{slug}'
os.makedirs(out, exist_ok=True)

def embed(text):
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

print("=== Phase 4: ベクトルインテリジェンス 開始 ===")

# === ① 競合メッセージ ===
competitor_msgs = [
    {"source": "ゴソックス", "text": "臭い・蒸れを防ぐ消臭機能と高通気性の両立"},
    {"source": "maffole", "text": "洗っても消えない抗菌防臭。水虫・臭いに悩む方の定番"},
    {"source": "小野商事ACE", "text": "シルクのさらさら感で足元快適。水虫・乾燥肌に悩む女性向け"},
    {"source": "Tabio", "text": "靴を脱いでもかわいい。おしゃれな5本指ソックス"},
    {"source": "Vraquir", "text": "水虫・蒸れに悩む方の定番。汗をすばやく吸収・蒸散"},
    {"source": "一般5本指競合", "text": "足指を1本1本分けて蒸れを防ぐ5本指ソックス"},
    {"source": "競合全般", "text": "抗菌防臭で足の臭いを防ぐ靴下"},
]

# === ② 口コミ ===
reviews = [
    {"source": "自社ポジティブ", "sentiment": "positive", "text": "五本指の靴下しか履けません。指がくっつかないので履き心地は最高です。可愛いのが沢山あるので、選ぶ楽しみもあります"},
    {"source": "自社ポジティブ", "sentiment": "positive", "text": "最初はオッサン臭いなと思っていましたが、いざ履いてみたら蒸れにくいし、疲れにくくてとても快適。今ではとても愛用しています"},
    {"source": "自社ポジティブ", "sentiment": "positive", "text": "特に汗をかく時期はとても良い。ストレスなく、めっちゃいい"},
    {"source": "専門家", "sentiment": "positive", "text": "5本指ソックスに変えるだけで水虫の治療成功率が3倍近く変わる。薬を塗っているのに治らない患者のほとんどが、足の蒸れ環境を改善していなかった"},
    {"source": "競合ネガティブ", "sentiment": "negative", "text": "靴を脱いだときに見えると恥ずかしい。指の形が出る独特の見た目が嫌で、おしゃれな場所では脱げない"},
    {"source": "競合ネガティブ", "sentiment": "negative", "text": "1本1本の足指に履かせる手間が面倒。急いでいるときに時間がかかって困る"},
    {"source": "競合ネガティブ", "sentiment": "negative", "text": "脱ぐとき気を使わないと指の部分が中に入ってしまい、洗濯して干すときに乾きにくいし戻すのが面倒くさい"},
    {"source": "競合ネガティブ", "sentiment": "negative", "text": "健康に気を遣う人が履くものというイメージで、どうしてもおしゃれなイメージが持てない。人前で見せたくない"},
]

# === ③ 3層の需要 ===
layer_demands = [
    {"layer": "潜在層", "text": "足が蒸れやすくて臭いが気になる。でも水虫だとは思っていない。普通の靴下で我慢しているが、もっと快適に過ごしたい。5本指ソックスはダサいから選択肢に入っていない"},
    {"layer": "準顕在層", "text": "水虫になってしまって薬を塗っているが治らない。5本指ソックスが良いとは知っているが、見た目がダサくて人前で脱げない。何か良い方法はないか"},
    {"layer": "顕在層", "text": "水虫を何年も繰り返している。5本指ソックスも試したが見た目が嫌で続かなかった。おしゃれしたいのに足の問題が邪魔。脱いでもバレない5本指があれば完璧なのに"},
]

# === ④ 3層の新認知 ===
new_cognitions = [
    {"layer": "潜在層", "text": "そのムレや臭い、実は水虫の初期症状かもしれない。足の蒸れ環境を変えるだけで根本から防げる。見た目が普通のソックスと同じシークレット5本指という選択肢がある"},
    {"layer": "準顕在層", "text": "薬だけでは治らない。足の蒸れ環境の改善が必要。でもダサい見た目の5本指を我慢する必要はない。外見は普通のソックス、中だけ5本指というシークレット設計がある"},
    {"layer": "顕在層", "text": "脱いでも5本指とわからない靴下がある。ホールガーメント編みで縫い目もごわつきもなく、和紙糸で蒸れない。おしゃれを諦めずに水虫から解放される"},
]

# === ⑤ 商品USP ===
product_usp = {
    "text": "外見は普通のソックス、内部パーティション構造で5本指機能を実現。和紙糸とホールガーメント編みで、おしゃれを諦めずに水虫・蒸れを根本解決できる唯一のシークレット5本指ソックス",
    "category": "product_usp"
}

print("ベクトル生成中...")

# ベクトル化
for m in competitor_msgs:
    m['vector'] = embed(m['text'])
    m['category'] = 'competitor_message'
    print(f"  競合: {m['source']} ✅")

for r in reviews:
    r['vector'] = embed(r['text'])
    r['category'] = 'review'
    print(f"  口コミ: {r['source']} ✅")

for d in layer_demands:
    d['vector'] = embed(d['text'])
    d['category'] = 'layer_demand'
    print(f"  需要: {d['layer']} ✅")

for c in new_cognitions:
    c['vector'] = embed(c['text'])
    c['category'] = 'new_cognition'
    print(f"  新認知: {c['layer']} ✅")

product_usp['vector'] = embed(product_usp['text'])
print(f"  USP ✅")

all_vectors = competitor_msgs + reviews + layer_demands + new_cognitions + [product_usp]
json.dump(all_vectors, open(f'{out}/all_vectors.json','w'), ensure_ascii=False,
          default=lambda x: x.tolist() if hasattr(x,'tolist') else x)
print(f"\n=== {len(all_vectors)}件ベクトル化完了 ===")

# === 4-B: 5つのクロス距離分析 ===
print("\n=== 4-B: クロス距離分析 ===")

comp_vectors = [np.array(m['vector']) for m in competitor_msgs]

# 問い1: 競合密度
print("\n【問い1】競合メッセージ密集分析")
comp_sims = []
for i, a in enumerate(competitor_msgs):
    for j, b in enumerate(competitor_msgs):
        if i < j:
            sim = cosine_sim(a['vector'], b['vector'])
            comp_sims.append((a['source'], b['source'], sim))
            print(f"  {a['source']} × {b['source']}: {sim:.3f}")

avg_comp_sim = np.mean([s[2] for s in comp_sims])
print(f"  平均類似度: {avg_comp_sim:.3f} (0.70超=密集ゾーン)")

# 問い2: 口コミクラスタ
print("\n【問い2】口コミクラスタ分析")
own_pos = [r for r in reviews if r['sentiment'] == 'positive']
comp_neg = [r for r in reviews if r['sentiment'] == 'negative']
for p in own_pos[:2]:
    for n in comp_neg[:2]:
        sim = cosine_sim(p['vector'], n['vector'])
        print(f"  自社ポジ×競合ネガ: {sim:.3f} — [{p['text'][:20]}] × [{n['text'][:20]}]")

# 問い3: USP × 3層需要
print("\n【問い3】USP × 3層需要距離")
usp_layer_scores = {}
for d in layer_demands:
    sim = cosine_sim(product_usp['vector'], d['vector'])
    usp_layer_scores[d['layer']] = sim
    print(f"  USP × {d['layer']}: {sim:.3f}")

# 問い4: 新認知 × 競合距離
print("\n【問い4】新認知 × 競合距離（Only1チェック）")
cognition_scores = {}
for c in new_cognitions:
    avg_sim = np.mean([cosine_sim(c['vector'], cv) for cv in comp_vectors])
    cognition_scores[c['layer']] = avg_sim
    flag = "⚠️近い" if avg_sim > 0.65 else "✅遠い(Only1)"
    print(f"  {c['layer']}の新認知 × 競合平均: {avg_sim:.3f} {flag}")

# 問い5: 口コミ × 3層需要の一致度
print("\n【問い5】口コミ × 3層需要の一致度")
demand_reality_scores = {}
for d in layer_demands:
    sims = [cosine_sim(d['vector'], np.array(r['vector'])) for r in reviews]
    avg = np.mean(sims)
    demand_reality_scores[d['layer']] = avg
    best_r = max(reviews, key=lambda r: cosine_sim(d['vector'], np.array(r['vector'])))
    print(f"  {d['layer']}: 平均={avg:.3f} 最近口コミ=「{best_r['text'][:35]}...」")

# === 4-C: N1決定 ===
print("\n=== 4-C: N1スコアリング ===")
results = {}
for layer in ["潜在層", "準顕在層", "顕在層"]:
    # Only1スコア = 新認知が競合から遠いほど高い（1-sim）
    only1_gap = 1.0 - cognition_scores.get(layer, 0.5)
    usp_match = usp_layer_scores.get(layer, 0.0)
    demand_reality = demand_reality_scores.get(layer, 0.0)
    # 重み付き合計
    score = (only1_gap * 3 + usp_match * 3 + demand_reality * 2) / 8
    results[layer] = {
        "only1Gap": round(only1_gap, 3),
        "uspMatch": round(usp_match, 3),
        "demandReality": round(demand_reality, 3),
        "totalScore": round(score, 3)
    }
    print(f"  {layer}: Only1={only1_gap:.3f} USP合致={usp_match:.3f} 需要リアリティ={demand_reality:.3f} → 総合={score:.3f}")

primary_layer = max(results.keys(), key=lambda k: results[k]['totalScore'])
print(f"\n  → PRIMARY N1: {primary_layer}")

# 結果保存
vector_intel = {
    "avgCompetitorSimilarity": round(avg_comp_sim, 3),
    "competitorDensity": "高い" if avg_comp_sim > 0.70 else "中程度",
    "only1Gaps": ["シークレット設計（外見普通）", "おしゃれ × 足健康の両立", "水虫対策 × ファッション性の融合"],
    "saturatedAngles": ["抗菌防臭", "吸汗速乾", "水虫対策機能"],
    "uspLayerMatch": {k: v["uspMatch"] for k, v in results.items()},
    "newCognitionOnly1Scores": {k: v["only1Gap"] for k, v in results.items()},
    "demandRealityScores": {k: v["demandReality"] for k, v in results.items()},
    "totalScores": {k: v["totalScore"] for k, v in results.items()},
    "primaryN1Layer": primary_layer
}

json.dump(vector_intel, open(f'{out}/vector_intel.json','w'), ensure_ascii=False)
print(f"\n✅ vector_intel.json 保存完了")
print("=== Phase 4 完了 ===")
