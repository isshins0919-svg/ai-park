"""
Amazon部長クン v3.0 — KW層別プロフィール生成
3層のKW意図をベクトル化してall_vectors.jsonに追加。
各コピー・画像の「層への刺さり度」を測定できるインフラを構築する。
"""
import subprocess, os, json, time
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
    time.sleep(0.3)
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

slug = 'camicks'
out = f'research-park/output/{slug}'

# ============================================================
# 3層KWプロフィール定義
# ============================================================

kw_layers = {
    "Layer1_シークレット追求層": {
        "description": "外から5本指と分からない靴下を探している層。人前で靴を脱ぐシーンで恥ずかしくない靴下が欲しい",
        "weight": 0.40,
        "target_images": [1, 5],
        "kw_intents": [
            {"kw": "シークレット 5本指", "intent": "外から5本指と分からない靴下を探している。人前で靴を脱いでもバレない靴下が欲しい"},
            {"kw": "普通に見える 5本指靴下", "intent": "見た目がふつうの靴下なのに5本指構造の靴下を探している"},
            {"kw": "外から見えない 靴下", "intent": "5本指と外から気づかれない靴下が欲しい"},
            {"kw": "足指靴下 バレない", "intent": "職場や外出先で靴を脱いでも恥ずかしくない足指靴下を探している"},
            {"kw": "5本指靴下 見た目普通", "intent": "5本指でも外見が一般的なミドル丈靴下に見える商品を探している"},
        ]
    },
    "Layer2_機能健康層": {
        "description": "足の蒸れ・臭いを機能的に解決したい層。和紙素材など素材の機能性に関心がある",
        "weight": 0.35,
        "target_images": [2, 3],
        "kw_intents": [
            {"kw": "靴下 消臭 蒸れない", "intent": "足の蒸れや臭いを解決できる機能性靴下を探している"},
            {"kw": "和紙 靴下 機能性", "intent": "和紙素材の機能性靴下を探している。素材の機能に注目している"},
            {"kw": "5本指靴下 消臭", "intent": "5本指構造で消臭効果が高い靴下を探している"},
            {"kw": "足 蒸れ対策 靴下", "intent": "足の蒸れを根本から解決したい。夏場の足臭が悩み"},
            {"kw": "camifine 和紙素材", "intent": "camifineや和紙配合素材の靴下を具体的に探している"},
        ]
    },
    "Layer3_ブランド信頼層": {
        "description": "品質・製造背景・ブランドへの信頼を重視する層。日本製・老舗・職人への共感がある",
        "weight": 0.25,
        "target_images": [4, 6],
        "kw_intents": [
            {"kw": "日本製 靴下 高品質", "intent": "品質にこだわった日本製靴下を探している。安い海外製は嫌"},
            {"kw": "職人 靴下 本物", "intent": "本物の靴下が欲しい。職人が作った一品"},
            {"kw": "靴下 メーカー 老舗", "intent": "老舗靴下メーカーの商品を探している。歴史あるブランドへの信頼"},
            {"kw": "五本指靴下 おしゃれ", "intent": "スタイリッシュな5本指靴下を探している。ファッションとして成立するもの"},
            {"kw": "糸屋 靴下 こだわり", "intent": "糸・素材からこだわった靴下ブランドを探している"},
        ]
    }
}

# ============================================================
# ベクトル化
# ============================================================

print("=== KW層別プロフィール ベクトル化開始 ===")

layer_profiles = []

for layer_name, layer_data in kw_layers.items():
    print(f"\n  {layer_name} (weight={layer_data['weight']})")

    # 層全体のプロフィール文をベクトル化
    profile_text = f"{layer_data['description']}"
    profile_vec = embed(profile_text)

    layer_entry = {
        "category": "kw_layer_profile",
        "layer": layer_name,
        "weight": layer_data["weight"],
        "target_images": layer_data["target_images"],
        "text": profile_text,
        "vector": profile_vec
    }
    layer_profiles.append(layer_entry)
    print(f"    ✅ プロフィール: {profile_text[:40]}...")

    # 各KW意図をベクトル化
    for kw_intent in layer_data["kw_intents"]:
        combined_text = f"{kw_intent['kw']}：{kw_intent['intent']}"
        vec = embed(combined_text)

        kw_entry = {
            "category": "kw_layer_intent",
            "layer": layer_name,
            "weight": layer_data["weight"],
            "kw": kw_intent["kw"],
            "text": combined_text,
            "vector": vec
        }
        layer_profiles.append(kw_entry)
        print(f"    ✅ KW「{kw_intent['kw']}」")

print(f"\n  合計: {len(layer_profiles)}件ベクトル化完了")

# ============================================================
# all_vectors.json に追記
# ============================================================

vectors_path = f'{out}/all_vectors.json'
existing = []
if os.path.exists(vectors_path):
    existing = json.load(open(vectors_path))
    # 古いKW層データを除去（更新）
    existing = [v for v in existing if v.get('category') not in ['kw_layer_profile', 'kw_layer_intent']]

merged = existing + layer_profiles

with open(vectors_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, default=lambda x: x if not hasattr(x,'tolist') else x.tolist())

print(f"\n  ✅ all_vectors.json 更新完了（合計{len(merged)}件）")

# ============================================================
# クロス距離分析: 各コピーの「層への刺さり度」
# ============================================================

print("\n=== Camicksコピー × 3層別 刺さり度分析 ===")

# 層別プロフィールベクトル（プロフィール文のみ使用）
profile_vecs = {}
for entry in layer_profiles:
    if entry['category'] == 'kw_layer_profile':
        profile_vecs[entry['layer']] = np.array(entry['vector'])

# Camicksコピー（確定版）
camicks_copies = [
    {"index": "メイン", "text": "Amazon商品ページメイン画像 白背景 商品単体 シンプル"},
    {"index": "サブ①", "text": "外は、ひとつ。中は、五つ。外から見えない、シークレット五本指構造。縫い目ゼロ。"},
    {"index": "サブ②", "text": "蒸れない足は、臭わない。camifine® 和紙の調湿力で、足を乾いた状態に保つ。"},
    {"index": "サブ③", "text": "和紙は、もともと呼吸している。camifine® 和紙40%の自社開発素材。酢酸95%削減 イソ吉草酸90%削減。"},
    {"index": "サブ④", "text": "余計なことをさせない、という設計。洗濯後の裏返し不要。普通の靴下と同じでいい。"},
    {"index": "サブ⑤", "text": "靴の中にも、美意識を。23cm〜27cm対応。メンズ・レディース兼用。"},
    {"index": "サブ⑥", "text": "素材に、57年。糸の開発から製造まで、一貫生産。"},
]

print(f"\n{'枚':6} {'Layer1(×0.40)':16} {'Layer2(×0.35)':16} {'Layer3(×0.25)':16} {'加重':8} {'担当層'}")
print("-" * 80)

layer_order = list(kw_layers.keys())

results = []
for c in camicks_copies:
    vec = np.array(embed(c['text']))

    scores = {}
    for layer_name in layer_order:
        pv = profile_vecs.get(layer_name)
        scores[layer_name] = cosine_sim(vec, pv) if pv is not None else 0.0

    weighted = sum(scores[l] * kw_layers[l]['weight'] for l in layer_order)

    # 最も近い層を特定
    best_layer = max(scores, key=scores.get)
    best_layer_short = best_layer.replace("Layer1_", "L1:").replace("Layer2_", "L2:").replace("Layer3_", "L3:")

    print(f"  {c['index']:6} {scores[layer_order[0]]:.3f}{'':10} {scores[layer_order[1]]:.3f}{'':10} {scores[layer_order[2]]:.3f}{'':10} {weighted:.3f}{'':2} {best_layer_short}")

    results.append({
        "index": c['index'],
        "text": c['text'][:30],
        "layer_scores": {l: round(scores[l], 3) for l in layer_order},
        "weighted_score": round(weighted, 3),
        "best_layer": best_layer
    })

# ============================================================
# 設計意図との整合チェック
# ============================================================

print("\n=== 設計意図との整合チェック ===")

intended_layers = {
    "サブ①": "Layer1_シークレット追求層",
    "サブ②": "Layer2_機能健康層",
    "サブ③": "Layer2_機能健康層",
    "サブ④": "Layer1_シークレット追求層",
    "サブ⑤": "全層",
    "サブ⑥": "Layer3_ブランド信頼層",
}

for r in results:
    if r['index'] == 'メイン':
        continue
    intended = intended_layers.get(r['index'], '?')
    if intended == '全層':
        print(f"  {r['index']}: 全層担当（整合チェックスキップ）")
        continue

    best = r['best_layer']
    match = "✅ 整合" if best == intended else f"⚠️ ズレ（設計={intended.split('_')[0]} / 実際={best.split('_')[0]}）"
    print(f"  {r['index']}: {match} | 加重スコア={r['weighted_score']:.3f}")

# ============================================================
# strategy.json に KW層分析結果を追記
# ============================================================

strategy_path = f'{out}/strategy.json'
if os.path.exists(strategy_path):
    strategy = json.load(open(strategy_path))

    strategy['kwLayerProfiles'] = {
        "updatedAt": "2026-04-02",
        "layers": {
            layer_name: {
                "description": kw_layers[layer_name]['description'],
                "weight": kw_layers[layer_name]['weight'],
                "target_images": kw_layers[layer_name]['target_images'],
                "kw_intents": [ki['kw'] for ki in kw_layers[layer_name]['kw_intents']]
            }
            for layer_name in layer_order
        },
        "copyAnalysis": results
    }

    with open(strategy_path, 'w', encoding='utf-8') as f:
        json.dump(strategy, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ strategy.json KW層プロフィール追記完了")

print(f"\n=== KW層別プロフィール生成 完了 ===")
print(f"  all_vectors.json: {len(merged)}件（KW層追加）")
print(f"  3層 × 意図5件 + プロフィール3件 = {len(layer_profiles)}件追加")
print(f"\n出力先: {vectors_path}")
