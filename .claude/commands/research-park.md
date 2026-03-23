# Research Park ver.1.0

商品理解 × N1需要 × 3層認知設計 × マーケティング戦略。全アウトプットSkills共通の土台を作る。
このスキルはultrathinkを使用して深い洞察を引き出す。複雑な分析が必要な場合は自動的に拡張思考を有効化する。

`/research-park` で起動。

---

## 起動時表示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RESEARCH PARK ver.1.0
  商品理解 × N1需要 × 3層認知設計 × マーケティング戦略
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - DPro MCP（Items / Genres / Products）
  - 3層分析（潜在・準顕在・顕在）
  - N1需要のニュアンス × 本能 × 試行錯誤
  - 競合メッセージ ベクトルマップ
  - マーケティング戦略 → strategy.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

ランダム1行:
- 「N1の脳内、丸裸にしていこう。」
- 「需要のニュアンス、掴みにいくぞ。」
- 「3層の全景、見えてからが本番。」
- 「競合の脳内ポジション、空きを見つける。」
- 「戦略が決まれば、あとは弾を込めるだけ。」

---

## セットアップチェック

```bash
echo "GEMINI_KEY_1: ${GEMINI_API_KEY_1:+SET}"
```

DPro MCP: `search_genres_api_v1_genres_get` を `genre_name: "test"` で1回呼ぶ。

全OK → Phase 1 へ。未設定あり → セットアップガイド表示。

---

## ナレッジ読み込み

以下を **Read tool で必ず読む**:
- `.claude/knowledge/pak-philosophy.md` — パクの哲学（メインモデル+補助原則）
- `.claude/knowledge/hook-db.md` と `.claude/knowledge/cta-db.md` のフック・CTAパターン
- `.claude/knowledge/hook-db.md` — フックDB BH1〜BH8
- `.claude/knowledge/cta-db.md` — CTADB BC1〜BC8

---

## Phase 1: ヒアリング

以下を質問。全て揃ってから次へ。

```
1. 商材名
2. 商材カテゴリ（スキンケア/ダイエット/不動産/SaaS等）
3. 商品の核心（何が、どう違うのか。一言で）
4. コアコンピタンス（この企業/ブランドだけが持つ根源的な強み。競合が真似できない源泉。技術/データ/ノウハウ/ネットワーク等）
5. USP（顧客への唯一の約束。「○○なのはこれだけ」と言い切れる一文）
6. ターゲット（ざっくりでOK）
7. 競合名（2-3社）
8. LP URL（任意）
9. 現在CPA / 目標CPA（任意）
10. 既存の勝ちクリエイティブ情報（任意。「○○訴求が強い」等）
11. NGワード・法規制約（任意。薬機法等）
```

変数格納: `PRODUCT_NAME`, `PRODUCT_CATEGORY`, `PRODUCT_CORE`, `CORE_COMPETENCE`, `USP`, `TARGET_ROUGH`, `COMPETITORS`, `LP_URL`, `CPA_INFO`, `EXISTING_WINS`, `NG_CONSTRAINTS`

`PRODUCT_SLUG` = 商材名から英数字スラッグ生成。

---

## Phase 2: 商品理解の解像度を上げる

**メインエージェントが直接実行。**

### 2-A: 商品の深掘り

WebSearch + WebFetch で以下を収集:
1. **公式サイト分析**: コンセプト、USP、成分/機能、価格帯、オファー
2. **口コミ・レビュー収集**: 良い口コミ5件 + 悪い口コミ5件 → インサイト抽出
3. **ブランドアセット**: ロゴ、ブランドカラー（primary/secondary/accent）、フォントトーン、ビジュアルトーン

結果を `PRODUCT_INTEL` に格納（JSON）。

### 2-A-2: 10訴求要素の整理

Phase 2-A の情報 + ヒアリング情報をもとに、以下の10要素を整理する。
全アウトプットSkills（バナー/動画/記事LP）で訴求素材として活用。

```json
{
  "persuasionElements": {
    "strength": "商品の強み（機能的優位性。他と比べて何が優れてるか）",
    "authority": "権威性（専門家推薦/メディア掲載/受賞歴/導入社数/監修者等）",
    "benefit": "特典（購入者が得られる追加価値。ノウハウ/サポート/付属品等）",
    "scarcity": "限定性（数量限定/期間限定/先着/地域限定等）",
    "trust": "信頼性（実績数値/継続率/満足度/第三者評価等）",
    "safety": "安心感（返金保証/無料トライアル/サポート体制/解約自由等）",
    "proof": "実証（ビフォーアフター/事例/データ/比較テスト結果等）",
    "simplicity": "簡便性（導入の簡単さ/使いやすさ/時短効果/手間の削減等）",
    "campaign": "キャンペーン（現在実施中の販促施策。割引/プレゼント/紹介特典等）",
    "offer": "オファー（最終的な購入条件のまとめ。価格+特典+保証+限定性の総合パッケージ）"
  }
}
```

不明な項目は「情報なし」で埋め、後でパクに確認する。
結果を `PRODUCT_INTEL.persuasionElements` に格納。

### 2-B: 競合の深掘り

各競合について:
1. **商品比較**: 価格、成分/機能、USP、オファー強度
2. **メッセージ収集**: 公式サイト・広告で使ってるキャッチコピー・訴求角度を5-10個収集
3. **口コミ比較**: 競合ユーザーの不満 → 自社商品が解決できるポイント

結果を `COMPETITOR_INTEL` に格納（JSON）。

### 2-C: LP分析（URL提供時のみ）

WebFetch で LP を分析:
- FVヘッドライン / FVオファー / FV CTA
- メッセージの流れ（ストーリー構造）
- 信頼構築要素（権威・社会的証明・リスクリバーサル）
- メッセージギャップ（LP上で弱い・欠けてる要素）

結果を `LP_INTEL` に格納（JSON）。

### 2-D: DPro広告インテリジェンス（DPro掲載がある場合）

**DPro MCP を叩いて、実際に出稿されてる広告データから市場のリアルを掴む。**

DPro に該当ジャンル/商材の掲載がない場合はスキップし、Phase 2-A〜C のWebリサーチのみで Phase 3 へ進む。

#### Step 1: ジャンル・商材の存在確認

```
1. search_genres(genre_name="{PRODUCT_CATEGORY のキーワード}")
   → ジャンルIDを取得。なければ関連キーワードで再検索
2. search_products(product_name="{PRODUCT_NAME}", genre_id=XX)
   → 自社商材のproduct_idを取得
3. 競合各社もsearch_products で product_id を取得
```

該当なし → 「DPro掲載なし。WebリサーチのみでPhase 3へ」と表示してスキップ。

#### Step 2: 自社の勝ちCR分析

```
get_items(product_id=XX, sort="cost_difference-desc", limit=10)
```

取得した勝ちCR TOP10 から以下を抽出:
- **ad_sentence / ad_start_sentence**: 広告文（特に冒頭フック）
- **narration**: ナレーション全文
- **推定広告費（cost_difference）**: どのCRにお金が投下されてるか
- **digg_rate / play_count**: エンゲージメント指標
- **transition_url_id**: 遷移先LP

抽出結果を `DPRO_OWN_WINS` に格納。

#### Step 3: 競合の勝ちCR分析

各競合について:
```
get_items(product_id=YY, sort="cost_difference-desc", limit=10)
```

競合の勝ちCR TOP10 から同様に抽出。
**特に重要**: 競合の広告文（ad_sentence）→ 競合メッセージベクトルの素材として Phase 4 で使う。

抽出結果を `DPRO_COMP_WINS` に格納。

#### Step 4: ジャンル全体のトレンド

```
get_items(genre_id=XX, sort="cost_difference-desc", limit=20)
```

ジャンル全体で今お金が動いてる広告 TOP20 → 訴求トレンドを抽出:
- **密集してる訴求角度**: 複数の広告主が同じ訴求を使ってる → レッドオーシャン
- **突出してる新しい訴求**: 1社だけが使ってて広告費が伸びてる → 注目

抽出結果を `DPRO_GENRE_TREND` に格納。

#### Step 5: 勝ちCRの遷移先LP分析（上位3件）

自社・競合の勝ちCR 上位3件の遷移先テキストを取得:
```
read_transition_url_text_content(transition_url_id="{id}")
```

LP上の訴求メッセージを抽出し、Phase 2-C の LP分析を補強する。

#### Step 6: DProインテリジェンスの統合

```json
{
  "dproIntel": {
    "available": true,
    "genreId": "XX",
    "ownWinningAds": [
      {
        "rank": 1,
        "adSentence": "広告文",
        "hook": "冒頭フック（ad_start_sentence）",
        "costDifference": 1000000,
        "diggRate": 0.05,
        "appealAngle": "訴求角度の要約"
      }
    ],
    "competitorWinningAds": {
      "競合A": [
        {
          "rank": 1,
          "adSentence": "競合の広告文",
          "hook": "冒頭フック",
          "costDifference": 500000,
          "appealAngle": "訴求角度の要約"
        }
      ]
    },
    "genreTrend": {
      "hotAppealAngles": ["今お金が動いてる訴求角度リスト"],
      "saturatedAngles": ["飽和してる訴求角度リスト"],
      "emergingAngles": ["新しく伸びてる訴求角度リスト"]
    },
    "winningMessages": ["Phase 4でベクトル化する勝ちCRのメッセージリスト"]
  }
}
```

`winningMessages` は Phase 4 のベクトル化で **⑥ 勝ちCRメッセージ** として追加ベクトル化する。

---

## Phase 3: 3層のN1を洗い出す

**メインエージェントが思考。Phase 2 の全データを使う。**

需要理論: 「需要 = 根本欲求 + パラメータ」
パラメータの成熟度で3層に分かれる。

### 3層定義

#### 潜在層 — パラメータ未形成
> 悩みはある。でも解決策のイメージがない。

- **根本欲求**: 漠然とした不満・不安（「なんか○○」）
- **パラメータ**: ほぼない。何が原因かも、何を基準に選べばいいかも分からない
- **脳内競合**: ゼロ〜曖昧（「放置」「そのうち治る」）
- **試行錯誤**: してない
- **本能**: 悩みを直視したくない。面倒。今のままでいい

定義するもの:
```json
{
  "layerName": "潜在層",
  "n1Persona": {
    "name": "", "age": "", "occupation": "",
    "dailyScene": "悩みを感じる具体的な日常シーン",
    "painLevel": "1-10",
    "currentBehavior": "今どうしてるか（放置/我慢/気づいてない）"
  },
  "rootDesire": "根本欲求（漠然とした不満）",
  "parameters": [],
  "brainCompetitors": [],
  "trialHistory": "なし",
  "instinct": "この層の本能（面倒/直視したくない/今のままでいい）",
  "estimatedVolume": "多/中/少",
  "estimatedCPA": "高/中/低",
  "requiredNewCognition": {
    "cognition1": "原因の気づき — 「あなたのその悩み、実は○○が原因」",
    "cognition2": "解決策の方向性 — 「こういうアプローチで解決できる」",
    "cognitionGoal": "形成したい新パラメータ"
  }
}
```

#### 準顕在層 — パラメータはあるが最適解に未到達
> 試行錯誤し始め。脳内競合あり。でも満足してない。

- **根本欲求**: 明確（「○○したい」と言語化できる）
- **パラメータ**: ある程度ある。でも「これだ！」の判断基準が定まってない
- **脳内競合**: 2-5個（試したことがある/検討中のもの）
- **試行錯誤**: している途中。どれもイマイチ
- **本能**: もう失敗したくない。でも諦めてもいない

定義するもの:
```json
{
  "layerName": "準顕在層",
  "n1Persona": {
    "name": "", "age": "", "occupation": "",
    "dailyScene": "試行錯誤してる具体的なシーン",
    "painLevel": "1-10",
    "currentBehavior": "今何を使ってる/何を試した"
  },
  "rootDesire": "根本欲求（明確な言語化）",
  "parameters": ["既に持ってる判断基準1", "判断基準2"],
  "brainCompetitors": ["競合A（不満点）", "競合B（不満点）"],
  "trialHistory": "試行錯誤の履歴と各不満",
  "instinct": "この層の本能（失敗したくない/時間を無駄にしたくない）",
  "estimatedVolume": "多/中/少",
  "estimatedCPA": "高/中/低",
  "requiredNewCognition": {
    "cognition1": "既存解決策の限界 — 「今までの方法が効かなかった理由は○○」",
    "cognition2": "新しい判断基準 — 「本当に見るべきは○○」",
    "cognitionGoal": "付与したい新パラメータ"
  }
}
```

#### 顕在層 — パラメータ成熟。でも悶々。
> 需要のニュアンスと商品がマッチ。試行錯誤しまくって、まだ満たされてない。

- **根本欲求**: 強烈（「もうこの悩み何年目？」）
- **パラメータ**: 充実。自分なりの判断基準がある。語れる
- **脳内競合**: 多数。でも全部に不満
- **試行錯誤**: 大量。だからこそ悶々
- **本能**: 「次こそは」と「もう疲れた」の間

定義するもの:
```json
{
  "layerName": "顕在層",
  "n1Persona": {
    "name": "", "age": "", "occupation": "",
    "dailyScene": "悶々としてる具体的なシーン",
    "painLevel": "1-10",
    "currentBehavior": "今使ってるもの/最後に試したもの"
  },
  "rootDesire": "根本欲求（強烈・切実）",
  "parameters": ["成熟した判断基準1", "判断基準2", "判断基準3"],
  "brainCompetitors": ["競合A（具体的不満）", "競合B（具体的不満）", "..."],
  "trialHistory": "詳細な試行錯誤履歴と各結果",
  "instinct": "この層の本能（次こそは/もう疲れた/でも諦められない）",
  "estimatedVolume": "多/中/少",
  "estimatedCPA": "高/中/低",
  "requiredNewCognition": {
    "cognition1": "根本的な違い — 「これは構造が違う。なぜなら○○」",
    "cognition2": "判断基準の書き換え or 合致 — 「あなたが求めてたのはこれ」",
    "cognitionGoal": "書き換える/合致させるパラメータ"
  }
}
```

---

## Phase 4: ベクトルインテリジェンス

Phase 2-3 の全データをベクトル化し、**距離と密度で意思決定する**。

### 4-A: 全ベクトル一括生成

5カテゴリ（+ DProデータがある場合は6カテゴリ）を一気にベクトル化する。

```python
from google import genai
import os, subprocess, json, numpy as np

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass
_load_env('GEMINI_API_KEY_1')

client = genai.Client(api_key=os.environ['GEMINI_API_KEY_1'])
slug = '{slug}'
out = f'research-park/output/{slug}'
os.makedirs(out, exist_ok=True)

def embed(text):
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# === ① 競合メッセージ ===
competitor_msgs = {COMPETITOR_MESSAGES}  # [{"source":"競合A","text":"コピー"}, ...]
for m in competitor_msgs:
    m['vector'] = embed(m['text'])
    m['category'] = 'competitor_message'

# === ② 口コミ ===
reviews = {REVIEWS}  # [{"source":"自社/競合A","sentiment":"positive/negative","text":"口コミ"}, ...]
for r in reviews:
    r['vector'] = embed(r['text'])
    r['category'] = 'review'

# === ③ 3層の需要（rootDesire + parameters を1文に結合） ===
layer_demands = {LAYER_DEMANDS}  # [{"layer":"潜在層","text":"根本欲求+パラメータの自然文"}, ...]
for d in layer_demands:
    d['vector'] = embed(d['text'])
    d['category'] = 'layer_demand'

# === ④ 3層の新認知候補 ===
new_cognitions = {NEW_COGNITIONS}  # [{"layer":"潜在層","text":"cognition1+2の自然文"}, ...]
for c in new_cognitions:
    c['vector'] = embed(c['text'])
    c['category'] = 'new_cognition'

# === ⑤ 商品USP ===
product_usp = {"text": "{PRODUCT_CORE}", "category": "product_usp"}
product_usp['vector'] = embed(product_usp['text'])

# === ⑥ DPro勝ちCRメッセージ（Phase 2-D で取得した場合のみ） ===
winning_msgs = []
if DPRO_INTEL.get('available'):
    for msg in DPRO_INTEL['winningMessages']:
        entry = {"text": msg, "category": "winning_ad", "source": "dpro"}
        entry['vector'] = embed(entry['text'])
        winning_msgs.append(entry)

all_vectors = competitor_msgs + reviews + layer_demands + new_cognitions + [product_usp] + winning_msgs
json.dump(all_vectors, open(f'{out}/all_vectors.json','w'), ensure_ascii=False, default=lambda x: x.tolist() if hasattr(x,'tolist') else x)
print(f'=== {len(all_vectors)}件ベクトル化完了 ===')
```

### 4-B: 5つのクロス距離分析

ベクトル間の距離を測定し、**5つの問い**に答える。

#### 問い1: 競合はどこに密集してるか？（競合 × 競合）

競合メッセージ同士のcos sim > 0.80 = 密集ゾーン（レッドオーシャン）。
密集してないゾーン = **Only1を取れる空き**。

```
  ●●● ← 「保湿」訴求に密集
  ●●
    ●
         ◎ ← ここが空いてる
  ●
```

#### 問い2: ユーザーの生の声はどこに集まってるか？（口コミクラスタ）

- 自社の良い口コミクラスタ = **ユーザーが本当に感じてる価値**
- 競合の悪い口コミクラスタ = **市場の共通不満**
- 自社の良い口コミ × 競合の悪い口コミの距離が**近い** = 「競合の不満を自社が解決してる」の証拠

#### 問い3: 商品USPはどの層に一番近いか？（USP × 3層需要）

商品USPベクトル × 各層のrootDesire+parametersベクトルの距離。
**最も近い層 = 商品が自然に刺さる層**。

```python
for d in layer_demands:
    sim = cosine_sim(product_usp['vector'], d['vector'])
    print(f"USP × {d['layer']}: sim={sim:.3f}")
```

#### 問い4: 新認知は競合から十分遠いか？（新認知 × 競合）

各層の新認知ベクトル × 競合メッセージ群の平均距離。
**遠いほどOnly1**。近い = 競合と同じこと言おうとしてる。

```python
comp_vectors = [np.array(m['vector']) for m in competitor_msgs]
for c in new_cognitions:
    avg_sim = np.mean([cosine_sim(c['vector'], cv) for cv in comp_vectors])
    print(f"{c['layer']}の新認知 × 競合平均: sim={avg_sim:.3f} {'⚠️近い' if avg_sim > 0.65 else '✅遠い'}")
```

#### 問い5: 口コミは3層の定義と合ってるか？（口コミ × 3層需要）

口コミベクトル × 各層の需要ベクトルの距離。
**「俺たちが定義した需要」と「ユーザーが実際に言ってること」のギャップ検出**。
ギャップが大きい = 層の定義がリアルからズレてる → 修正。

```python
for d in layer_demands:
    matching_reviews = [(r, cosine_sim(d['vector'], r['vector'])) for r in reviews]
    matching_reviews.sort(key=lambda x: -x[1])
    top = matching_reviews[0]
    print(f"{d['layer']} に最も近い口コミ: sim={top[1]:.3f}「{top[0]['text'][:30]}」")
```

### 4-C: N1決定（ベクトルデータ駆動）

5つの問いの結果を統合し、スコアリング:

| 判断軸 | 使うベクトル距離 | 重み |
|--------|----------------|------|
| Only1取りやすさ | 問い1（競合密度の空き）+ 問い4（新認知 × 競合距離） | ★★★ |
| 商品マッチ度 | 問い3（USP × 3層需要距離） | ★★★ |
| 需要のリアリティ | 問い5（口コミ × 3層需要の一致度） | ★★☆ |
| 競合弱点の突きやすさ | 問い2（自社良口コミ × 競合悪口コミ距離） | ★★☆ |
| 人数 × CVR × CPA | Phase 3 の定性推定 | ★☆☆ |

**最終判断:**
- ベクトルスコア上位の層 = 第一候補
- 定性判断（人数・CVR・CPA）で最終確認
- 1人のN1を選定、残り2層はサブターゲット

出力:
```json
{
  "primaryN1": {
    "layer": "潜在層/準顕在層/顕在層",
    "persona": {},
    "whyThisN1": "選定理由（ベクトル距離データ付き）",
    "newCognitionStrategy": "この人にどんな新認知を形成するか",
    "vectorScores": {
      "only1Gap": 0.00,
      "uspMatch": 0.00,
      "demandReality": 0.00,
      "competitorWeakness": 0.00
    }
  },
  "secondaryTargets": [
    { "layer": "...", "persona": {}, "priority": "2nd/3rd" }
  ]
}
```

---

## Phase 5: 3層別コミュニケーション方針

Phase 1-4 の全データを統合し、3層それぞれへの打ち手を設計する。

> **注意**: コンセプト設計・メッセージ体系・セールスコピーは **Concept Park** の責務。
> Research Park は「素材を揃える」ところまで。磨き上げは `/concept-park` で。

```json
{
  "潜在層": {
    "goal": "新パラメータを植え付ける",
    "approach": "教育型。原因気づき → 解決策の存在",
    "hookAngle": "問題提起・衝撃の事実",
    "expressionElements": ["要素7（体験談）", "要素8（根本原因）", "要素2（衝撃）"]
  },
  "準顕在層": {
    "goal": "新パラメータを付与する",
    "approach": "比較型。既存の限界 → 新基準の提示",
    "hookAngle": "既存解決策の否定・新常識",
    "expressionElements": ["要素9（既存の限界）", "要素12（独自性）", "要素6（秘訣）"]
  },
  "顕在層": {
    "goal": "パラメータを書き換える/合致させる",
    "approach": "直球型。Only1コンセプト → 即オファー",
    "hookAngle": "根本的な違い・運命の出会い",
    "expressionElements": ["要素11（運命的商品）", "要素13（デモ）", "要素16（オファー）"]
  }
}
```

※ 要素番号は広告表現要素23選に対応。

---

## Phase 6: 素材リスト + strategy.json 出力

### 6-A: 素材リスト

リサーチ過程で収集した全素材を整理:

```json
{
  "brandAssets": {
    "logo": "パスまたはURL",
    "primaryColor": "#HEX",
    "secondaryColor": "#HEX",
    "accentColor": "#HEX",
    "fontStyle": "ゴシック/明朝/...",
    "visualTone": "清潔感/高級感/カジュアル/..."
  },
  "productImages": ["収集した商品画像URLリスト"],
  "competitorVisuals": ["競合ビジュアル参考URLリスト"],
  "reviewQuotes": {
    "positive": ["良い口コミ引用5件"],
    "negative": ["悪い口コミ引用5件"]
  }
}
```

### 6-B: strategy.json 書き出し

全出力を1ファイルに統合:

```
research-park/output/{PRODUCT_SLUG}/
├── strategy.json          ← 全アウトプットSkillsが読むメインファイル
├── all_vectors.json       ← 全ベクトル（5カテゴリ。アウトプットSkillsで再利用）
└── research-log.md        ← リサーチ過程の記録
```

`strategy.json` の構造:
```json
{
  "version": "1.0",
  "productSlug": "",
  "createdAt": "YYYY-MM-DD",

  "productIntel": {
    "name": "",
    "category": "",
    "core": "",
    "coreCompetence": "この企業/ブランドだけが持つ根源的な強み（競合が真似できない源泉）",
    "usp": "顧客への唯一の約束（「○○なのはこれだけ」と言い切れる一文）",
    "persuasionElements": {
      "strength": "", "authority": "", "benefit": "", "scarcity": "",
      "trust": "", "safety": "", "proof": "", "simplicity": "",
      "campaign": "", "offer": ""
    }
  },
  "competitorIntel": {},
  "lpIntel": {},

  "dproIntel": {
    "available": false,
    "genreId": "",
    "ownWinningAds": [],
    "competitorWinningAds": {},
    "genreTrend": {
      "hotAppealAngles": [],
      "saturatedAngles": [],
      "emergingAngles": []
    },
    "winningMessages": []
  },

  "layers": {
    "潜在層": { "persona": {}, "rootDesire": "", "parameters": [], "requiredNewCognition": {}, "estimatedVolume": "", "estimatedCPA": "" },
    "準顕在層": { "persona": {}, "rootDesire": "", "parameters": [], "requiredNewCognition": {}, "estimatedVolume": "", "estimatedCPA": "" },
    "顕在層": { "persona": {}, "rootDesire": "", "parameters": [], "requiredNewCognition": {}, "estimatedVolume": "", "estimatedCPA": "" }
  },

  "primaryN1": {
    "layer": "",
    "persona": {},
    "whyThisN1": "",
    "newCognitionStrategy": "",
    "vectorScores": {
      "only1Gap": 0.00,
      "uspMatch": 0.00,
      "demandReality": 0.00,
      "competitorWeakness": 0.00
    }
  },

  "vectorIntelligence": {
    "competitorDensityClusters": ["密集ゾーンの訴求テーマリスト"],
    "only1Gaps": ["空きゾーンの訴求テーマリスト"],
    "reviewInsights": {
      "ownPositiveCluster": "自社良口コミが集まるテーマ",
      "competitorNegativeCluster": "競合悪口コミが集まるテーマ",
      "overlapScore": 0.00
    },
    "uspLayerMatch": { "潜在層": 0.00, "準顕在層": 0.00, "顕在層": 0.00 },
    "newCognitionOnly1Scores": { "潜在層": 0.00, "準顕在層": 0.00, "顕在層": 0.00 },
    "demandRealityScores": { "潜在層": 0.00, "準顕在層": 0.00, "顕在層": 0.00 }
  },

  "_comment_concept": "concept / keyVisual / salesCopy / messageSystem / formatStrategy / hookVectors は Concept Park が書き込む。Research Park では空のまま出力",
  "concept": {},
  "keyVisual": {},
  "salesCopy": {},
  "messageSystem": {},
  "formatStrategy": {},
  "hookVectors": [],

  "layerCommunication": {
    "潜在層": { "goal": "", "approach": "", "hookAngle": "", "expressionElements": [] },
    "準顕在層": { "goal": "", "approach": "", "hookAngle": "", "expressionElements": [] },
    "顕在層": { "goal": "", "approach": "", "hookAngle": "", "expressionElements": [] }
  },

  "assets": {
    "brandAssets": {},
    "productImages": [],
    "competitorVisuals": [],
    "reviewQuotes": {}
  },

  "vectorFile": "all_vectors.json"
}
```

---

## Phase 7: ユーザーへの戦略プレゼン

strategy.json の内容を構造化して提示:

1. **商品理解サマリー**（3行）
2. **3層マップ**（各層のN1ペルソナ + 新認知 + ボリューム/CPA）
3. **N1決定の根拠**（ベクトルスコア付き）
4. **3層別コミュニケーション方針**
5. **次のアクション提案**:
   - → `/concept-park` でコンセプト・キービジュアル・セールスコピーを磨く
   - → `/banner-park` でバナー生成
   - → `/shortad-park` で動画広告生成
   - → `/記事LP-park` で記事LP生成

「strategy.json 保存済み。次は `/concept-park` でコンセプトを磨こう。」

---

## 注意事項

- Phase 2: メインが直列実行（WebSearch/WebFetch依存）
- Phase 2-D: DPro MCP活用。DPro掲載がある商材/ジャンルでは勝ちCR・競合・トレンドを取得。掲載なしならスキップ
- Phase 3: メインの思考タスク（外部API不要）
- Phase 4: ベクトルインテリジェンス。GEMINI_API_KEY必要。5カテゴリ一括ベクトル化（+ DProデータがあれば6カテゴリ）
- Phase 5: 3層別コミュニケーション方針のみ。コンセプト設計・メッセージ体系はConcept Parkの責務
- strategy.json + all_vectors.json = アウトプットSkillsの共通入力
- all_vectors.json はアウトプットSkillsで再利用:
  - コピーの一貫性チェック（コンセプトベクトルとの距離）
  - コピーの差別化チェック（競合ベクトルとの距離）
  - 生成物の多様性チェック（生成物同士のcos sim）
- 同一商材で2回目以降: 既存strategy.json + all_vectors.json を読み込み、差分更新
