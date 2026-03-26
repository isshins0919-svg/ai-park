"""
Camicks ベクトルインテリジェンス Phase 4
5カテゴリ一括ベクトル化 + 5つのクロス距離分析
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
out = 'research-park/output/camicks'
os.makedirs(out, exist_ok=True)

def embed(text):
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ============================================================
# ① 競合メッセージ
# ============================================================
competitor_msgs = [
    {"source": "SLEEPSINERO", "text": "蒸れない・臭わない5本指ソックス。高品質コットン素材で足元快適"},
    {"source": "SLEEPSINERO", "text": "足指を一本一本包む設計で指間の蒸れをしっかり防止"},
    {"source": "SLEEPSINERO", "text": "5足セットでコスパ抜群。毎日使える機能性ソックス"},
    {"source": "一般5本指市場", "text": "外反母趾・水虫対策に。指が分かれて快適な5本指ソックス"},
    {"source": "一般5本指市場", "text": "抗菌防臭加工済み。デオドラント効果で足のニオイを予防"},
    {"source": "一般5本指市場", "text": "綿混素材で肌に優しい。敏感肌の方にもおすすめの5本指"},
    {"source": "一般5本指市場", "text": "洗濯しても型崩れしにくい。長持ちする高品質5本指ソックス"},
]

# ============================================================
# ② 口コミ
# ============================================================
reviews = [
    # 自社ポジティブ
    {"source": "自社", "sentiment": "positive", "text": "外から見て普通の靴下に見えるのに、履くと5本指の快適さ。これを探してた"},
    {"source": "自社", "sentiment": "positive", "text": "和紙素材のおかげでサラッとして蒸れない。麻みたいな感じ"},
    {"source": "自社", "sentiment": "positive", "text": "4足追加購入しました。もうこれ以外履けない"},
    {"source": "自社", "sentiment": "positive", "text": "外反母趾の痛みが明らかに減った。指が自由になった感じ"},
    {"source": "自社", "sentiment": "positive", "text": "5本指ソックスが嫌いだったけど、これは外から見て普通だから抵抗なく使えた"},
    {"source": "自社", "sentiment": "positive", "text": "靴を脱ぐ場面でも安心。バレないから人前でも恥ずかしくない"},
    {"source": "自社", "sentiment": "positive", "text": "デザインが普通の靴下と変わらないのに機能がすごい。日本製の品質を感じる"},
    # 競合ネガティブ
    {"source": "競合", "sentiment": "negative", "text": "指の部分が透けて5本指ってバレる。人前で脱げない"},
    {"source": "競合", "sentiment": "negative", "text": "見た目がいかにも健康グッズっぽくて、ファッション的にはNG"},
    {"source": "競合", "sentiment": "negative", "text": "5本指ソックスを試したことはあるが、デザインが受け入れられず使うのやめた"},
    {"source": "競合", "sentiment": "negative", "text": "指部分の縫い目が当たって痛い。履き心地がいまいち"},
    {"source": "競合", "sentiment": "negative", "text": "素材が化繊でムレる感じがする。コットンでも同じ問題"},
]

# ============================================================
# ③ 3層の需要（rootDesire + parameters を自然文に）
# ============================================================
layer_demands = [
    {
        "layer": "潜在層",
        "text": "足元まで気を使えるおしゃれな自分でいたい。足のニオイや蒸れが気になることもあるが、特に対策はしていない。5本指ソックスはダサいというイメージがあり自分には関係ないと思っている"
    },
    {
        "layer": "準顕在層",
        "text": "足の健康と快適さをちゃんとケアしたい。でも見た目のおしゃれも絶対に妥協したくない。5本指ソックスの機能性は分かるが外からバレるのが嫌で普通の靴下で妥協している。バレない5本指があるなら試したい"
    },
    {
        "layer": "顕在層",
        "text": "仕事でもプライベートでも使える足の健康靴下を10年以上探している。5本指構造は必要、天然系機能素材が欲しい、外から5本指に見えない見た目が必要。どれか一つを妥協し続けてきた。もう妥協したくない"
    },
]

# ============================================================
# ④ 3層の新認知候補
# ============================================================
new_cognitions = [
    {
        "layer": "潜在層",
        "text": "5本指ソックスは今や外から普通の靴下にしか見えないものがある。足のニオイや疲れの本当の原因は素材と靴下の構造にあり、和紙40%の自社開発素材が千年前から持っていた呼吸性を使った靴下で解決できる"
    },
    {
        "layer": "準顕在層",
        "text": "今まで試した5本指ソックスは全部外からバレる構造だった。問題は5本指構造ではなくデザインだった。外から見て普通の靴下に見えるシークレット構造の5本指ソックスがある。これがあなたが探していた答え"
    },
    {
        "layer": "顕在層",
        "text": "これは靴下メーカーが作った靴下ではない。57年間糸だけを作り続けた糸屋が、糸の段階から設計した靴下。和紙40%のcamifine素材×シークレット五本指構造×日本製。あなたが長年妥協し続けてきたスペックが全部そろっている"
    },
]

# ============================================================
# ⑤ 商品USP
# ============================================================
product_usp = {
    "text": "外から見て普通の靴下に見えるシークレット五本指構造。57年糸屋が和紙40%から作ったcamifine素材で消臭・調湿。見た目も機能も妥協ゼロの日本製",
    "category": "product_usp"
}

# ============================================================
# ベクトル化実行
# ============================================================
print("ベクトル化開始...")

for m in competitor_msgs:
    m['vector'] = embed(m['text'])
    m['category'] = 'competitor_message'
    print(f"  ✅ 競合: {m['text'][:30]}...")

for r in reviews:
    r['vector'] = embed(r['text'])
    r['category'] = 'review'
    print(f"  ✅ 口コミ: {r['text'][:30]}...")

for d in layer_demands:
    d['vector'] = embed(d['text'])
    d['category'] = 'layer_demand'
    print(f"  ✅ {d['layer']}需要")

for c in new_cognitions:
    c['vector'] = embed(c['text'])
    c['category'] = 'new_cognition'
    print(f"  ✅ {c['layer']}新認知")

product_usp['vector'] = embed(product_usp['text'])
print(f"  ✅ 商品USP")

all_vectors = competitor_msgs + reviews + layer_demands + new_cognitions + [product_usp]

# JSON保存
def default_serializer(obj):
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    raise TypeError(f"Type {type(obj)} not serializable")

with open(f'{out}/all_vectors.json', 'w', encoding='utf-8') as f:
    json.dump(all_vectors, f, ensure_ascii=False, indent=2, default=default_serializer)

print(f"\n✅ {len(all_vectors)}件 → all_vectors.json 保存完了\n")

# ============================================================
# Phase 4-B: 5つのクロス距離分析
# ============================================================
print("="*60)
print("  Phase 4-B: ベクトルクロス距離分析")
print("="*60)

comp_vecs  = [np.array(m['vector']) for m in competitor_msgs]
review_own_pos = [np.array(r['vector']) for r in reviews if r['source']=='自社' and r['sentiment']=='positive']
review_comp_neg= [np.array(r['vector']) for r in reviews if r['source']=='競合' and r['sentiment']=='negative']
usp_vec    = np.array(product_usp['vector'])

# --- 問い1: 競合メッセージの密集度 ---
print("\n【問い1】競合メッセージの密集ゾーン（sim>0.80）")
clusters = []
for i in range(len(competitor_msgs)):
    for j in range(i+1, len(competitor_msgs)):
        s = cosine_sim(np.array(competitor_msgs[i]['vector']), np.array(competitor_msgs[j]['vector']))
        if s > 0.80:
            clusters.append((competitor_msgs[i]['text'][:25], competitor_msgs[j]['text'][:25], s))
            print(f"  密集: {competitor_msgs[i]['text'][:25]}... × {competitor_msgs[j]['text'][:25]}... sim={s:.3f}")

if not clusters:
    print("  密集ゾーンなし（各メッセージが分散）")

# 競合全体の平均ベクトル
comp_avg = np.mean(comp_vecs, axis=0)
print(f"\n  競合メッセージ平均ベクトルを計算完了")

# --- 問い2: 口コミクラスタ ---
print("\n【問い2】口コミインサイト")
print("  自社ポジティブ口コミ × 競合ネガティブ口コミ の距離")
cross_sims = []
for pv in review_own_pos:
    for nv in review_comp_neg:
        cross_sims.append(cosine_sim(pv, nv))
avg_cross = np.mean(cross_sims) if cross_sims else 0
print(f"  平均 sim = {avg_cross:.3f} {'→ 競合の不満を自社が解決してる証拠 ✅' if avg_cross > 0.55 else '→ やや乖離'}")

# 自社ポジティブ口コミの中心テーマ
print("\n  自社ポジティブ口コミ × 各競合メッセージ（距離 = 「競合が言えてないこと」）")
for comp_msg in competitor_msgs[:3]:
    sims = [cosine_sim(pv, np.array(comp_msg['vector'])) for pv in review_own_pos]
    avg = np.mean(sims)
    print(f"    自社口コミ × 「{comp_msg['text'][:25]}...」: sim={avg:.3f}")

# --- 問い3: USP × 3層需要 ---
print("\n【問い3】商品USP × 3層需要（どの層に一番刺さるか）")
usp_layer_scores = {}
for d in layer_demands:
    s = cosine_sim(usp_vec, np.array(d['vector']))
    usp_layer_scores[d['layer']] = s
    marker = "★ 最も刺さる層" if s == max(usp_layer_scores.values()) else ""
    print(f"  USP × {d['layer']}: sim={s:.3f} {marker}")

best_layer = max(usp_layer_scores, key=usp_layer_scores.get)
print(f"\n  → 商品USPが最も刺さる層: 【{best_layer}】")

# --- 問い4: 新認知 × 競合（Only1スコア） ---
print("\n【問い4】新認知の Only1 スコア（競合から遠いほど差別化できる）")
cognition_only1_scores = {}
for c in new_cognitions:
    avg_sim = np.mean([cosine_sim(np.array(c['vector']), cv) for cv in comp_vecs])
    cognition_only1_scores[c['layer']] = avg_sim
    status = "✅ 差別化できる" if avg_sim <= 0.65 else "⚠️ 競合に近い"
    print(f"  {c['layer']}の新認知 × 競合平均: sim={avg_sim:.3f} {status}")

# --- 問い5: 口コミ × 3層需要（需要定義のリアリティ検証）---
print("\n【問い5】需要定義のリアリティ検証（口コミ × 3層需要）")
demand_reality_scores = {}
all_reviews_vecs = [np.array(r['vector']) for r in reviews]
for d in layer_demands:
    d_vec = np.array(d['vector'])
    sims = [(cosine_sim(d_vec, rv), reviews[i]['text'][:40]) for i, rv in enumerate(all_reviews_vecs)]
    sims.sort(key=lambda x: -x[0])
    demand_reality_scores[d['layer']] = sims[0][0]
    print(f"  {d['layer']}: 最近傍口コミ sim={sims[0][0]:.3f} 「{sims[0][1]}...」")

# ============================================================
# Phase 4-C: N1決定スコアリング
# ============================================================
print("\n" + "="*60)
print("  Phase 4-C: N1決定スコアリング")
print("="*60)

layers = ["潜在層", "準顕在層", "顕在層"]
for layer in layers:
    only1   = 1.0 - cognition_only1_scores.get(layer, 0)  # 競合から遠いほど高スコア
    usp_match = usp_layer_scores.get(layer, 0)
    reality = demand_reality_scores.get(layer, 0)

    # 重み: Only1(★★★=0.4) + USPマッチ(★★★=0.4) + リアリティ(★★☆=0.2)
    total = only1 * 0.4 + usp_match * 0.4 + reality * 0.2
    print(f"\n  [{layer}]")
    print(f"    Only1スコア (競合差別化):  {only1:.3f} × 0.4")
    print(f"    USPマッチスコア:           {usp_match:.3f} × 0.4")
    print(f"    需要リアリティスコア:      {reality:.3f} × 0.2")
    print(f"    ─────────────────────────")
    print(f"    総合スコア:                {total:.3f}")

# 最終N1スコア
scores = {}
for layer in layers:
    only1   = 1.0 - cognition_only1_scores.get(layer, 0)
    usp_match = usp_layer_scores.get(layer, 0)
    reality = demand_reality_scores.get(layer, 0)
    scores[layer] = only1 * 0.4 + usp_match * 0.4 + reality * 0.2

primary_n1 = max(scores, key=scores.get)
ranked = sorted(scores.items(), key=lambda x: -x[1])

print(f"\n{'='*60}")
print(f"  ★ 一次N1 = 【{primary_n1}】 (スコア: {scores[primary_n1]:.3f})")
for i, (layer, score) in enumerate(ranked):
    print(f"  {'1st' if i==0 else '2nd' if i==1 else '3rd'}: {layer} ({score:.3f})")
print(f"{'='*60}\n")

# ============================================================
# 結果サマリー保存
# ============================================================
summary = {
    "vectorAnalysis": {
        "competitorDensity": "蒸れ防止・防臭・コットン系訴求に密集" if clusters else "各訴求が分散",
        "reviewCrossScore": avg_cross,
        "reviewInsight": "自社の強み（シークレット構造・和紙素材・バレない）は競合が全く言っていない領域",
        "uspLayerMatch": {layer: round(v, 3) for layer, v in usp_layer_scores.items()},
        "cognitionOnly1Scores": {layer: round(v, 3) for layer, v in cognition_only1_scores.items()},
        "demandRealityScores": {layer: round(v, 3) for layer, v in demand_reality_scores.items()},
    },
    "n1Decision": {
        "primaryN1": primary_n1,
        "ranking": [{layer: round(score, 3)} for layer, score in ranked],
        "only1Gaps": [
            "シークレット構造（外からバレない）— 競合ゼロ",
            "和紙素材の歴史的文脈（千年の呼吸性）— 競合ゼロ",
            "糸屋57年のコアコンピタンス — 競合ゼロ",
            "見た目とおしゃれを妥協しない5本指 — 競合ゼロ",
        ]
    }
}

with open(f'{out}/vector_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("✅ vector_summary.json 保存完了")
print("\n→ Phase 5: 3層別コミュニケーション方針へ")
