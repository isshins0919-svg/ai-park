"""
Amazon部長クン — 競合クリエイティブ エンベディング
月商1,000万円へのインフラ強化: 競合の勝ちパターンをベクトル化して意思決定に使う
2026-04-02 競合調査結果に基づく
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
# 競合クリエイティブデータ（2026-04-02 Amazon調査結果）
# ============================================================

# 競合の勝ち画像コピーパターン（実際の商品ページから収集）
competitor_creative = [
    # SLEEPSINERO（BSR1位 / ¥1,343 5足セット）
    {"brand": "SLEEPSINERO", "type": "image_copy", "text": "抗菌防臭加工ソックス 5足セット 吸湿速乾 三重脱げ防止", "appeal_angle": "機能×セット×コスパ"},
    {"brand": "SLEEPSINERO", "type": "image_copy", "text": "足指を解放 指がセパレートされ通気性・放湿性向上 指1本1本を包み込み汗を素早く吸収", "appeal_angle": "5本指の通気メカニズム説明"},
    {"brand": "SLEEPSINERO", "type": "image_copy", "text": "三重脱げ防止 足首ニット編み 土踏まずニット編み 足指独立形状", "appeal_angle": "脱げない根拠を番号で構造化"},
    {"brand": "SLEEPSINERO", "type": "image_copy", "text": "春夏秋冬 幅広く使える靴下 オールシーズン対応", "appeal_angle": "年間使用の価値正当化"},

    # グンゼ BODYWILD（ブランド権威）
    {"brand": "グンゼ", "type": "image_copy", "text": "GUNZE BODYWILD 脱げない消臭 LR左右判別 深履き フットカバー 5本指", "appeal_angle": "ブランド権威×機能"},
    {"brand": "グンゼ", "type": "image_copy", "text": "トップシリコン仕様 脱げない構造 吸汗速乾 指間の汗を吸収し蒸れによる不快感を軽減", "appeal_angle": "機能の根拠提示"},

    # SUGATA LABO（最直接競合 / 和紙×シークレット5本指）
    {"brand": "SUGATA LABO", "type": "image_copy", "text": "呼吸する和紙靴下 シークレット5本指 日本製 抗菌 消臭 速乾 14色展開", "appeal_angle": "和紙×シークレット×カラー"},
    {"brand": "SUGATA LABO", "type": "image_copy", "text": "薬剤加工なしで機能性を実現 吸水速乾 抗菌活性値JIS・SEK基準超え 和紙糸", "appeal_angle": "科学的根拠×無添加"},
    {"brand": "SUGATA LABO", "type": "image_copy", "text": "消臭効果99%以上 試験データ グラフ ニッセンケン認証", "appeal_angle": "数値証拠×認証権威"},
    {"brand": "SUGATA LABO", "type": "image_copy", "text": "毛玉ができにくい 指先が裏返らない 洗濯後もそのまま履ける", "appeal_angle": "ユーザビリティ差別化"},

    # ラポスカ（日本製×無縫製）
    {"brand": "ラポスカ", "type": "image_copy", "text": "日本製 ホールガーメント 抗菌防臭 シークレット 5本指 かわいい 3足セット", "appeal_angle": "日本製×無縫製×デザイン"},

    # maffole（銅粒子×半永久防臭）
    {"brand": "maffole", "type": "image_copy", "text": "銅粒子配合 半永久防臭 洗濯しても防臭効果が持続 5本指ソックス", "appeal_angle": "耐久性×防臭の永続性"},
]

# 競合が密集している訴求ゾーン
saturated_angles = [
    {"theme": "脱げない訴求（三重脱げ防止・シリコン・構造説明）", "text": "三重脱げ防止 トップシリコン 脱げにくい フットカバー 落ちない"},
    {"theme": "コスパ×セット訴求", "text": "5足セット コスパ 1足あたり安い まとめ買い お得 割引"},
    {"theme": "抗菌防臭機能（一般的）", "text": "抗菌防臭 消臭 蒸れない 速乾 吸汗"},
    {"theme": "カラーバリエーション展示", "text": "カラー展開 豊富 14色 多色 選べる"},
    {"theme": "スポーツ×運動用途", "text": "ランニング スポーツ ウォーキング 運動 アクティブ"},
]

# 競合が誰もやっていない空白地帯
empty_zones = [
    {"theme": "シークレット性の感情訴求", "text": "外から5本指に見えない 普通の靴下に見える 人前で靴を脱いでも恥ずかしくない バレない シークレット構造の感動"},
    {"theme": "製造ストーリー×糸屋権威", "text": "1969年創業 糸屋として57年 糸の開発から製造まで一貫生産 老舗職人が作る"},
    {"theme": "洗濯後の利便性", "text": "洗濯後の裏返し不要 普通の靴下と同じ扱い 手間がかからない"},
    {"theme": "おしゃれ×ファッション着用シーン", "text": "おしゃれな着用シーン インテリア 室内着 日常のおしゃれ 5本指でもスタイリッシュ"},
    {"theme": "和紙素材の具体的な数値証拠", "text": "酢酸95%削減 イソ吉草酸90%削減 ニッセンケン試験機関 第三者機関認証 数値で証明"},
]

print("=== 競合クリエイティブ エンベディング開始 ===")
print(f"  競合コピー: {len(competitor_creative)}件")
print(f"  飽和ゾーン: {len(saturated_angles)}件")
print(f"  空白地帯:   {len(empty_zones)}件")

# ベクトル化
print("\n  ベクトル化中...")
for item in competitor_creative:
    item['vector'] = embed(item['text'])
    item['category'] = 'competitor_amazon_creative'
    print(f"    ✅ {item['brand']}: {item['text'][:30]}...")

for item in saturated_angles:
    item['vector'] = embed(item['text'])
    item['category'] = 'saturated_angle'

for item in empty_zones:
    item['vector'] = embed(item['text'])
    item['category'] = 'empty_zone'

# ============================================================
# all_vectors.json に追記
# ============================================================
vectors_path = f'{out}/all_vectors.json'
existing = []
if os.path.exists(vectors_path):
    existing = json.load(open(vectors_path))
    # 古い competitor_amazon_creative を除去（更新）
    existing = [v for v in existing if v.get('category') not in
                ['competitor_amazon_creative', 'saturated_angle', 'empty_zone']]

all_new = competitor_creative + saturated_angles + empty_zones
merged = existing + all_new

with open(vectors_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, default=lambda x: x if not hasattr(x,'tolist') else x.tolist())

print(f"\n  ✅ all_vectors.json 更新完了（合計{len(merged)}件）")

# ============================================================
# クロス距離分析: 自社コピー vs 競合 vs 空白地帯
# ============================================================
print("\n=== Camicksコピー × 競合 × 空白地帯 距離分析 ===")

camicks_copies = [
    {"index": 1, "text": "外は、ひとつ。中は、五つ。外から見えない、シークレット五本指構造。縫い目ゼロ。"},
    {"index": 2, "text": "蒸れない足は、臭わない。camifine® 和紙の調湿力で、足を乾いた状態に保つ。"},
    {"index": 3, "text": "和紙は、もともと呼吸している。camifine® 和紙40%の自社開発素材。酢酸95%削減 イソ吉草酸90%削減。"},
    {"index": 4, "text": "余計なことをさせない、という設計。洗濯後の裏返し不要。普通の靴下と同じでいい。"},
    {"index": 5, "text": "靴の中にも、美意識を。23cm〜27cm対応。メンズ・レディース兼用。"},
    {"index": 6, "text": "素材に、57年。糸の開発から製造まで、一貫生産。"},
]

comp_vecs = [np.array(c['vector']) for c in competitor_creative]
empty_vecs = [np.array(e['vector']) for e in empty_zones]

print(f"\n{'枚':4} {'タイトル':20} {'競合距離':10} {'空白地帯':10} {'判定':15}")
print("-" * 65)

results = []
for c in camicks_copies:
    vec = np.array(embed(c['text']))
    comp_avg = float(np.mean([cosine_sim(vec, cv) for cv in comp_vecs]))
    empty_avg = float(np.mean([cosine_sim(vec, ev) for ev in empty_vecs]))

    # 判定: 競合から遠い(差別化) × 空白地帯に近い(Only1) = 最強
    if comp_avg <= 0.55 and empty_avg >= 0.55:
        status = "✅ 最強（差別化×空白）"
    elif comp_avg <= 0.60:
        status = "✅ 差別化OK"
    elif empty_avg >= 0.55:
        status = "⚠️ 空白狙いOK"
    else:
        status = "⚠️ 競合に近い"

    results.append({
        "index": c['index'],
        "text": c['text'][:20],
        "comp_avg": round(comp_avg, 3),
        "empty_avg": round(empty_avg, 3),
        "status": status
    })
    print(f"  サブ{c['index']}  {c['text'][:18]:18}  {comp_avg:.3f}      {empty_avg:.3f}      {status}")

# ============================================================
# 結果をstrategy.jsonに保存
# ============================================================
strategy_path = f'{out}/strategy.json'
strategy = json.load(open(strategy_path))

strategy['competitorCreativeIntel'] = {
    "updatedAt": "2026-04-02",
    "source": "Amazon JP 競合リサーチ（5本指靴下カテゴリ）",
    "topCompetitors": [
        {"brand": "SLEEPSINERO", "price": "¥1,343（5足）", "position": "BSR1位 / コスパ×機能"},
        {"brand": "グンゼ BODYWILD", "price": "¥1,320（3足）", "position": "ブランド権威"},
        {"brand": "SUGATA LABO", "price": "¥1,980〜2,200", "position": "和紙×シークレット直接競合"},
        {"brand": "ラポスカ", "price": "¥1,380（3足）", "position": "日本製×無縫製"},
    ],
    "saturatedAngles": [s['theme'] for s in saturated_angles],
    "emptyZones": [e['theme'] for e in empty_zones],
    "copyAnalysis": results
}

with open(strategy_path, 'w', encoding='utf-8') as f:
    json.dump(strategy, f, ensure_ascii=False, indent=2)

print(f"\n✅ strategy.json 競合インテリジェンス追記完了")
print(f"\n=== 月商1,000万円インフラ強化 完了 ===")
print(f"  all_vectors.json: {len(merged)}件（競合クリエイティブ追加）")
print(f"  strategy.json: competitorCreativeIntel 追記")
