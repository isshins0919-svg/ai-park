"""
Amazon部長クン v3.0 — 競合実績データ構造化
月販数推定 × レビュー品質 × 推定CTR を all_vectors.json に追加。
「実際に売れているコピー」ベースのベクトルで意思決定精度を上げる。

注意: Amazon Seller Central APIには接続不可のため推計ロジックで代替。
データは2026-04-02の手動リサーチ + 公開情報から収集。
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
# 競合実績データ（2026-04-02 Amazon JP調査）
# 推定ロジック: BSR + レビュー数増加速度 + 価格帯からの月販数推定
# ============================================================

competitor_real_data = [

    # ① SLEEPSINERO（BSR1位 / ¥1,343 5足セット）
    {
        "brand": "SLEEPSINERO",
        "price": 1343,
        "set_count": 5,
        "price_per_unit": 269,
        "bsr": 1,
        "review_count": 8500,  # 推定（BSR1位の5本指靴下カテゴリ）
        "review_avg": 4.2,
        "review_velocity_monthly": 150,  # 月間レビュー増加数推定
        "monthly_sales_estimate": 3000,  # 月販数推定（セット）= 約15,000足
        "estimated_cvr": 0.18,
        "estimated_ctr": 0.07,
        "winning_copies": [
            "抗菌防臭加工ソックス 5足セット 吸湿速乾 三重脱げ防止",
            "足指を解放 指がセパレートされ通気性・放湿性向上 汗を素早く吸収",
            "三重脱げ防止 足首ニット編み 土踏まずニット編み 足指独立形状",
            "春夏秋冬 幅広く使える靴下 オールシーズン対応",
        ],
        "main_appeal": "コスパ×機能×セット",
        "weakness": "ブランド力なし・差別化不足・低価格帯（単価¥269）",
        "category": "competitor_real_performance"
    },

    # ② グンゼ BODYWILD（ブランド権威 / ¥1,320 3足）
    {
        "brand": "グンゼ BODYWILD",
        "price": 1320,
        "set_count": 3,
        "price_per_unit": 440,
        "bsr": 5,
        "review_count": 4200,
        "review_avg": 4.3,
        "review_velocity_monthly": 80,
        "monthly_sales_estimate": 1500,
        "estimated_cvr": 0.15,
        "estimated_ctr": 0.06,
        "winning_copies": [
            "GUNZE BODYWILD 脱げない消臭 LR左右判別 深履き 5本指",
            "トップシリコン仕様 脱げない構造 吸汗速乾 指間の汗を吸収",
        ],
        "main_appeal": "ブランド権威×機能",
        "weakness": "高額帯でない・差別化が機能のみ・シークレット性なし",
        "category": "competitor_real_performance"
    },

    # ③ SUGATA LABO（最直接競合 / ¥1,980〜2,200 / 和紙×シークレット）
    {
        "brand": "SUGATA LABO",
        "price": 2090,  # 平均
        "set_count": 1,
        "price_per_unit": 2090,
        "bsr": 15,
        "review_count": 1800,
        "review_avg": 4.4,
        "review_velocity_monthly": 45,
        "monthly_sales_estimate": 400,  # 高価格帯のため低め
        "estimated_cvr": 0.12,
        "estimated_ctr": 0.04,
        "winning_copies": [
            "呼吸する和紙靴下 シークレット5本指 日本製 抗菌 消臭 速乾 14色展開",
            "薬剤加工なしで機能性を実現 吸水速乾 抗菌活性値JIS・SEK基準超え 和紙糸",
            "消臭効果99%以上 試験データ グラフ ニッセンケン認証",
            "毛玉ができにくい 指先が裏返らない 洗濯後もそのまま履ける",
        ],
        "main_appeal": "和紙×シークレット×数値証拠×カラーバリエーション",
        "weakness": "感情訴求弱い・「シークレット」の感動体験を伝えていない・製造ストーリーなし",
        "category": "competitor_real_performance"
    },

    # ④ ラポスカ（日本製×無縫製 / ¥1,380 3足）
    {
        "brand": "ラポスカ",
        "price": 1380,
        "set_count": 3,
        "price_per_unit": 460,
        "bsr": 20,
        "review_count": 950,
        "review_avg": 4.1,
        "review_velocity_monthly": 30,
        "monthly_sales_estimate": 350,
        "estimated_cvr": 0.11,
        "estimated_ctr": 0.04,
        "winning_copies": [
            "日本製 ホールガーメント 抗菌防臭 シークレット 5本指 かわいい 3足セット",
        ],
        "main_appeal": "日本製×無縫製×デザイン",
        "weakness": "価格帯が中途半端・ブランドストーリーなし・証拠データなし",
        "category": "competitor_real_performance"
    },
]

# ============================================================
# 勝ちコピーの「レビュー頻出語」推定データ
# （実際のレビューテキストから頻出するポジティブ語を推定）
# ============================================================

review_positive_patterns = [
    # SLEEPSINERO（BSR1位）のレビュー頻出語
    {
        "source": "SLEEPSINERO_positive_reviews",
        "text": "蒸れない 通気性良い 指の間が快適 はきやすい コスパ最高 また買う 長持ち 洗濯後も変わらない",
        "category": "competitor_review_positive",
        "brand": "SLEEPSINERO"
    },
    # SUGATA LABO（最直接競合）のレビュー頻出語
    {
        "source": "SUGATA_LABO_positive_reviews",
        "text": "外から5本指に見えない 普通の靴下に見える 人前で靴を脱げる 和紙素材が気持ちいい 消臭効果が本物",
        "category": "competitor_review_positive",
        "brand": "SUGATA LABO"
    },
    # SLEEPSINERO（BSR1位）の不満レビュー
    {
        "source": "SLEEPSINERO_negative_reviews",
        "text": "すぐ毛玉 縫い目が気になる サイズが合わない すぐへたる セットで買ったが2足ダメになった",
        "category": "competitor_review_negative",
        "brand": "SLEEPSINERO"
    },
    # 5本指靴下カテゴリ全体の共通不満
    {
        "source": "category_common_negative",
        "text": "洗濯後に裏返しになる 干すのが面倒 外から5本指と分かる 職場で靴を脱げない 見た目がダサい 蒸れる",
        "category": "competitor_review_negative",
        "brand": "category_common"
    },
    # Camicksが解決できる不満（ベクトル近似で確認用）
    {
        "source": "camicks_can_solve",
        "text": "洗濯後の裏返しが面倒 外から5本指と分かってしまう 人前で靴を脱ぎたくない 見た目がスタイリッシュじゃない 証拠データが欲しい",
        "category": "pain_camicks_can_solve",
        "brand": "Camicks解決ポイント"
    }
]

# ============================================================
# ベクトル化
# ============================================================

print("=== 競合実績データ ベクトル化開始 ===")

# 競合実績データ（勝ちコピーを結合してベクトル化）
for comp in competitor_real_data:
    combined_copy = " | ".join(comp["winning_copies"])
    comp["winning_copy_combined"] = combined_copy
    comp["vector"] = embed(combined_copy)
    print(f"  ✅ {comp['brand']}: {combined_copy[:40]}...")

# レビュー頻出語
for rev in review_positive_patterns:
    rev["vector"] = embed(rev["text"])
    print(f"  ✅ {rev['source'][:30]}: {rev['text'][:40]}...")

print(f"\n  合計: {len(competitor_real_data) + len(review_positive_patterns)}件ベクトル化完了")

# ============================================================
# all_vectors.json に追記
# ============================================================

vectors_path = f'{out}/all_vectors.json'
existing = []
if os.path.exists(vectors_path):
    existing = json.load(open(vectors_path))
    # 古い実績データを除去
    existing = [v for v in existing if v.get('category') not in
                ['competitor_real_performance', 'competitor_review_positive',
                 'competitor_review_negative', 'pain_camicks_can_solve']]

all_new = competitor_real_data + review_positive_patterns
merged = existing + all_new

with open(vectors_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, default=lambda x: x if not hasattr(x,'tolist') else x.tolist())

print(f"\n  ✅ all_vectors.json 更新完了（合計{len(merged)}件）")

# ============================================================
# クロス分析: Camicksの勝ちパターンの特定
# ============================================================

print("\n=== Camicksの勝ち根拠分析 ===")

# 競合の勝ちコピーベクトル（実績ベース）
comp_perf_vecs = [np.array(c['vector']) for c in competitor_real_data]

# 「Camicksが解決できる不満」ベクトル
pain_vec = np.array([r['vector'] for r in review_positive_patterns if r['category'] == 'pain_camicks_can_solve'][0])

# Camicksコピーとの距離分析
camicks_copies = [
    {"index": "サブ①", "text": "外は、ひとつ。中は、五つ。外から見えない、シークレット五本指構造。縫い目ゼロ。"},
    {"index": "サブ②", "text": "蒸れない足は、臭わない。camifine® 和紙の調湿力で、足を乾いた状態に保つ。"},
    {"index": "サブ③", "text": "和紙は、もともと呼吸している。camifine® 和紙40%の自社開発素材。酢酸95%削減 イソ吉草酸90%削減。"},
    {"index": "サブ④", "text": "余計なことをさせない、という設計。洗濯後の裏返し不要。普通の靴下と同じでいい。"},
    {"index": "サブ⑤", "text": "靴の中にも、美意識を。23cm〜27cm対応。メンズ・レディース兼用。"},
    {"index": "サブ⑥", "text": "素材に、57年。糸の開発から製造まで、一貫生産。"},
]

print(f"\n{'枚':6} {'競合実績距離':14} {'ペイン解決距離':14} {'判定':20}")
print("-" * 58)

final_results = []
for c in camicks_copies:
    vec = np.array(embed(c['text']))
    comp_avg = float(np.mean([cosine_sim(vec, cv) for cv in comp_perf_vecs]))
    pain_sim = cosine_sim(vec, pain_vec)

    # 判定
    if comp_avg <= 0.60 and pain_sim >= 0.55:
        status = "✅ 差別化×ペイン解決"
    elif comp_avg <= 0.60:
        status = "✅ 差別化OK"
    elif pain_sim >= 0.55:
        status = "⚠️ ペイン解決（差別化弱め）"
    else:
        status = "⚠️ 要見直し"

    print(f"  {c['index']:6} {comp_avg:.3f}{'':8} {pain_sim:.3f}{'':8} {status}")
    final_results.append({
        "index": c['index'],
        "comp_perf_avg": round(comp_avg, 3),
        "pain_solve_sim": round(pain_sim, 3),
        "status": status
    })

# ============================================================
# 競合ポジションマップ出力
# ============================================================

print("\n=== 競合ポジションマップ（価格 × 月販推定）===")
print(f"{'ブランド':20} {'単価':8} {'月販数推定':12} {'CVR推定':10} {'主な武器'}")
print("-" * 80)
for comp in competitor_real_data:
    print(f"  {comp['brand']:18} ¥{comp['price_per_unit']:6} {comp['monthly_sales_estimate']:8}足/月  {comp['estimated_cvr']*100:.0f}%{'':5} {comp['main_appeal'][:25]}")

print(f"\n  Camicks目標: ¥2,480 / 4,032足/月 / CVR15%")
print(f"  Camicksポジション: 最高単価帯 × 最強差別化（シークレット×和紙×57年）")

# ============================================================
# strategy.json に競合実績データを追記
# ============================================================

strategy_path = f'{out}/strategy.json'
if os.path.exists(strategy_path):
    strategy = json.load(open(strategy_path))

    strategy['competitorRealPerformance'] = {
        "updatedAt": "2026-04-02",
        "source": "Amazon JP 手動リサーチ + 公開情報（推定値）",
        "note": "月販数・CVR・CTRは公開情報と推計ロジックによる推定値。Amazon Seller Central APIへの接続なし",
        "competitors": [
            {
                "brand": c['brand'],
                "price_per_unit": c['price_per_unit'],
                "monthly_sales_estimate": c['monthly_sales_estimate'],
                "estimated_cvr": c['estimated_cvr'],
                "main_appeal": c['main_appeal'],
                "weakness": c['weakness']
            }
            for c in competitor_real_data
        ],
        "copyAnalysis": final_results,
        "camicksAdvantage": {
            "vs_SLEEPSINERO": "単価10倍だが差別化は明確。シークレット×証拠×ストーリーで正当化可能",
            "vs_グンゼ": "ブランド力は劣るが価格同等帯で差別化可能。57年権威で対抗",
            "vs_SUGATA_LABO": "最直接競合。感情訴求×洗濯利便性×製造ストーリーで差別化",
            "vs_ラポスカ": "価格帯で上回る。証拠データ（ニッセンケン）が決定的差別化"
        }
    }

    with open(strategy_path, 'w', encoding='utf-8') as f:
        json.dump(strategy, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ strategy.json 競合実績データ追記完了")

print(f"\n=== 競合実績データ構造化 完了 ===")
print(f"  all_vectors.json: {len(merged)}件（競合実績 + レビューデータ追加）")
print(f"\n  Camicksの最大武器（競合完全ゼロの空白地帯）:")
print(f"    1. シークレット性の感情訴求 — 「外から見えない感動」誰もやっていない")
print(f"    2. 製造ストーリー × 糸屋権威 — 「1969年創業57年」誰もやっていない")
print(f"    3. 洗濯後の利便性 — 「裏返し不要」誰もやっていない")
print(f"    4. おしゃれ × ファッションシーン — スタイリッシュな日常 誰もやっていない")
