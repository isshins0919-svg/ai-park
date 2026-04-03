# Concept Park ver.1.2

strategy.json のコア要素 — **コンセプト × キービジュアル × セールスコピー × メッセージ体系 × フォーマット別戦略** — をパクと壁打ちで磨き上げ、全アウトプットSkillsの武器にする。
このスキルはultrathinkを使用してコンセプトの本質を深掘りする。パラダイムシフトを起こす言葉を見つけるために拡張思考を自動発動する。

`/concept-park` で起動。

---

## 起動時表示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CONCEPT PARK ver.1.2
  コンセプト × キービジュアル × セールスコピー × 戦略 — 壁打ち
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  推奨: /research-park 完了済み（strategy.json）
  ライトモード: 既存ナレッジから仮strategy構築も可
  - コンセプト: 頭に残る言葉。パラダイムシフト
  - キービジュアル: 全フォーマット共通のビジュアル方向
  - セールスコピー: N1の心を動かす一文
  - マーケ戦略: フォーマット別の攻め方 + フック角度
  - ベクトル検証 → strategy.json 更新
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

ランダム1行:
- 「10文字で世界を変える。」
- 「脳内に1番乗りする言葉、見つけにいこう。」
- 「コンセプトは弾丸。磨くほど遠くまで届く。」
- 「パクと俺で、最高の一言を作る時間だ。」

---

## このスキルの性質

**他のPark Skillsと違い、壁打ち型。**

- Research Park = 自走して完遂 → 事後レビュー
- Concept Park = **パクと一緒に考えて磨く** → 対話型
- 1ターンで終わらない。何往復もする。パクのアイディアが乗ってこそ完成する
- AIパクは提案を出す。パクがアイディアを返す。それを磨く。このサイクルを回す

---

## Phase 1: strategy.json 読み込み + 現状確認

### 1-A: strategy.json 読み込み

`research-park/output/{PRODUCT_SLUG}/strategy.json` を Read。
`all_vectors.json` も Read。

**strategy.json が存在しない場合 → ライトモード起動:**

1. `.claude/knowledge/` 配下に該当商材のナレッジファイルがあるか検索
2. ナレッジがある場合 → そこからN1ペルソナ・コンセプト・Only1・ゴールデンサークルを抽出して**仮strategy構造**を組み立てる
3. ナレッジもない場合 → 「先に `/research-park` を実行するか、商材情報を教えてね」と案内

ライトモードの制約:
- ベクトルインテリジェンス（Phase 5）は実行不可（all_vectors.json がないため）
- Phase 5 は「strategy.json 書き出し + ベクトル検証は /research-park 実行後に追加実行」と案内
- 壁打ちそのものはフルスペックで実施可能

```
⚡ LIGHT MODE — 既存ナレッジから仮strategy構築
  ベクトル検証は /research-park 完了後に追加実行可能
```

### 1-B: 現状のコンセプトをプレゼン

strategy.json（またはライトモードの仮strategy）から以下を抽出し、**パクに一覧で見せる**:

```
━━━━━ 現状の戦略サマリー ━━━━━
商品: {productIntel.name}
N1: {primaryN1.layer} — {primaryN1.persona.name}（{persona.age}歳、{persona.occupation}）
  └ 層の判定根拠: {なぜこの層を選んだかの1行理由}
新認知戦略: {primaryN1.newCognitionStrategy}

コンセプト候補:
  選択済み: {concept.selected}（ベクトル検証: {concept.vectorValidation.verdict}）
  tagline: {concept.tagline}

Only1ポジション: {concept.only1Position}
ゴールデンサークル:
  WHY: {goldenCircle.why}
  HOW: {goldenCircle.how}
  WHAT: {goldenCircle.what}
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

→ 「ここからコンセプト・キービジュアル・セールスコピーを磨いていこう。何から始める？」
→ 「N1の層や狙い先を変えたい場合は、いつでも言ってくれ。コンセプトの軸ごと組み替える。」

パクが方向性を示したら、Phase 2 へ。
パクが「全部やって」なら、Phase 2→3→4 を順に提案ベースで進める。

### 1-C: ベクトルマップ（壁打ちの地図）

**all_vectors.json が存在する場合のみ実行。ライトモードではスキップ。**

Research Park が作ったベクトル資産から、コンセプトを考えるための「地図」を生成してパクに見せる。
壁打ちの方向性を「空間的に」理解した上で言葉を作る。

```python
# all_vectors.json から各カテゴリを抽出
comp_vecs = [v for v in all_vectors if v['category'] == 'competitor_message']
reviews = [v for v in all_vectors if v['category'] == 'review']
layer_demands = [v for v in all_vectors if v['category'] == 'layer_demand']
new_cognitions = [v for v in all_vectors if v['category'] == 'new_cognition']
product_usp = [v for v in all_vectors if v['category'] == 'product_usp'][0]

# N1層の需要・新認知ベクトルを特定
primary_layer = strategy['primaryN1']['layer']
n1_demand = [d for d in layer_demands if d['layer'] == primary_layer][0]
n1_cognition = [c for c in new_cognitions if c['layer'] == primary_layer][0]

# 口コミの種スコア = N1需要に近い × 競合から遠い
for r in reviews:
    r_vec = np.array(r['vector'])
    n1_sim = cosine_sim(r_vec, np.array(n1_demand['vector']))
    comp_sim = np.mean([cosine_sim(r_vec, np.array(c['vector'])) for c in comp_vecs])
    r['seed_score'] = n1_sim * (1 - comp_sim)
seed_reviews = sorted(reviews, key=lambda x: -x['seed_score'])[:5]
```

表示フォーマット:

```
━━━━━ ベクトルマップ — コンセプト設計の地図 ━━━━━
■ 競合密集ゾーン（ここは避ける）:
  {vectorIntelligence.competitorDensityClusters}

■ Only1空白ゾーン（ここを狙う）:
  {vectorIntelligence.only1Gaps}

■ N1の需要ニュアンス（{primaryN1.layer}）:
  「{n1_demand.text}」
  → 最も近い口コミ: 「{最近口コミ.text}」(sim=X.XXX)

■ コンセプトの種（N1需要に近い × 競合から遠い口コミ表現）:
  1. 「{seed_review_1.text}」 seed=X.XX
  2. 「{seed_review_2.text}」 seed=X.XX
  3. 「{seed_review_3.text}」 seed=X.XX

■ USP × 各層の刺さり度:
  潜在層: {sim} / 準顕在層: {sim} ★ / 顕在層: {sim}

■ 新認知 × 競合距離（Only1度）:
  {primary_layer}: sim={avg_sim} {✅遠い/⚠️近い}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

この地図があることで、24案生成時に「狙うべき空間に向かって言葉を当てはめる」ことができる。

### 1-D: N1層の変更（パクが途中で変更を希望した場合）

壁打ち中、どのPhaseでもパクが「やっぱ○○層を狙おう」「N1違うな」と言った場合:

1. strategy.json の3層データ（潜在/準顕在/顕在）から、指定された層のN1ペルソナ・新認知戦略を再読み込み
2. Phase 1-B の戦略サマリーを更新して再プレゼン
3. 壁打ち中の仮コンセプトがあればリセットし、新しいN1に合わせてPhase 2 から再スタート
4. **「層を変えた理由」をパクに確認** — これが後のコンセプト精度に直結する

ライトモードの場合は3層データがないので、パクから口頭で新N1の情報をヒアリングして進める。

---

## Phase 2: コンセプト壁打ち

### コンセプトとは

> **頭の中に残す言葉。パラダイムシフトを起こすレベル。**

- **名詞形**（動詞形/命令形は不可。「○○リスト」「○○営業」のように名詞で着地させる）
- 10文字以内（パクの基準）
- N1の脳内に1番乗りする言葉
- 競合が言ってない言葉（圧倒的Only1 = 差別化 × 圧倒的価値）
- 聞いた瞬間に「え、何それ？」と思考が動く

### 壁打ちの進め方

#### Step 1: 現状コンセプトの診断

7つの問いで診断（問い3/4/7はベクトルデータ駆動）:

1. **パラダイムシフトか？** — N1の「常識」を壊せるか。「え、そうなの？」が起きるか
2. **10文字で言えるか？** — 長い = 弱い。研ぎ澄まされてるか
3. **Only1か？** — コンセプトをベクトル化 × 競合メッセージベクトル群の平均距離。sim < 0.60 = ✅Only1
4. **N1の需要に近いか？** — コンセプトベクトル × N1需要ベクトルの距離。sim > 0.65 = ✅近い
5. **一言で「買いたい」が生まれるか？** — コンセプト = 需要 + ベネフィット + 独自性
6. **商品のOnly1を直接表現しているか？** — コンセプトが商品の核心的差別化要素を伝えているか。抽象的すぎないか。商品名を隠してコンセプトだけ見たとき、別の商品にも使えてしまわないかチェック
7. **新認知を運べるか？** — コンセプトベクトル × N1新認知ベクトルの距離。sim > 0.55 = ✅運べる。「このコンセプトを聞いたN1の脳内で、狙った新認知が形成されるか」の指標

```python
# Step 1 ベクトル診断（all_vectors.json がある場合）
concept_vec = embed(current_concept)
# 問い3: Only1度
comp_avg = np.mean([cosine_sim(concept_vec, np.array(c['vector'])) for c in comp_vecs])
# 問い4: N1需要距離
n1_sim = cosine_sim(concept_vec, np.array(n1_demand['vector']))
# 問い7: 新認知運搬力
cognition_sim = cosine_sim(concept_vec, np.array(n1_cognition['vector']))
```

各問いに ✅ / ⚠️ / ❌ で判定 → パクに提示。

⚠️/❌ が付いた場合、**具体的に何が弱いか・どう直すか**を提案付きで指摘する。
「⚠️ Only1表現が弱い」だけでなく「→ 広告データ連動という核を入れた方が刺さる。例: ○○」のように。
ベクトル数値がある問い（3/4/7）は数値も併記する。

#### Step 1.5: コンセプトの種を確認

Phase 1-C のベクトルマップで抽出した「コンセプトの種」を参照する。

- **口コミ起点の種**: N1需要に近い × 競合から遠い口コミ表現（Phase 1-C で算出済み）
- **Only1空白ゾーン**: 競合が密集してない訴求空間
- **N1の生の言葉**: 口コミの中でN1が自然に使ってる表現

これらを方向A〜Eの候補生成時の「素材」として意識的に活用する。
特に方向D/Eでは、口コミの生の言葉をベースにすると刺さりやすい。

※ ライトモード（all_vectors.json なし）の場合はスキップ。

#### Step 2: 代替案の提示

現状コンセプトに ⚠️ / ❌ がある場合、**5つの方向性**を提案:

- **方向A: 研ぎ澄ます** — 同じ軸で、もっと短く、もっと鋭く
- **方向B: 軸をずらす** — N1の別の需要/本能に刺す
- **方向C: パラダイムシフト** — 常識を完全に裏返す。「○○は間違いだった」系
- **方向D: 国民的HIT構造の横転** — 世の中で圧倒的に成功してるコンセプトの「構造」を抽出し、商品に横展開する
- **方向E: 造語 × 本能直撃** — 全く聞いたことない新しい言葉。なのに需要のニュアンスにまるで刺さるし、根っこにある本能にブッ刺さる

#### 方向D の進め方

**超大HITのみ使用**。誰もが知ってるレベルの国民的コンセプトに限る。

1. **構造を抽出する**: 超大HIT国民的コンセプトを5-10個挙げ、その構造パターンを言語化する
   - 例: 「食べるラー油」→ [意外な動詞] [既存カテゴリ] = 用途のパラダイムシフト
   - 例: 「俺のフレンチ」→ [所有者] の [高級カテゴリ] = 高級の民主化
   - 例: 「大人のふりかけ」→ [ターゲット] の [日常カテゴリ] = カテゴリの格上げ
   - 例: 「写ルンです」→ [動詞+驚き] [です] = 機能そのものが名前
   - 例: 「お値段以上ニトリ」→ [価値の逆転] [ブランド] = 期待値超え宣言
   - 例: 「お、ねだん以上。」→ [感嘆] [価値表現] = 体験の言語化
   - 例: 「それ、早く言ってよ」→ [N1の心の声] = 共感からの認知
   - ※「誰もが知ってる」が基準。ニッチなHIT商品は使わない

2. **横転する**: 抽出した構造に、商品のコアコンピタンス/USP/N1需要を当てはめる
   - 構造 × coreCompetence = コアコンピタンス軸の横転
   - 構造 × usp = USP軸の横転
   - 構造 × N1のrootDesire = N1需要軸の横転

3. **同じ言葉の2回以上使用を禁止**: 10案の中で、同じ名詞・キーワードが2回以上出てはいけない。語彙のバリエーションを強制し、多角的な発想を引き出す

4. **圧倒的Only1チェック**: 横転した案が「ただの言葉遊び」で終わってないか確認
   - N1にとって圧倒的に価値が高いか？
   - 商品のOnly1が構造の中に組み込まれているか？

方向A/B/Cは各3案、**方向Dは10案**、**方向Eは5案** = 合計24案提示。

#### 方向E の進め方

**造語 × 本能直撃**。この世に存在しない新語を作る。でも聞いた瞬間に「分かる」。

1. **N1の本能を特定する**: strategy.json の `primaryN1.rootDesire` と `layers[N1層].instinct` から、N1の根っこにある本能（恐怖/欲望/焦り/安心/支配/承認等）を抽出
2. **需要のニュアンスを言語化する**: 「何が欲しいか」ではなく「どんな感覚が欲しいか」まで掘る
3. **造語を生成する**: 以下のパターンで新語を作る
   - **合成型**: 既存の2語を融合（例: 「確撃」= 確実 + 狙撃）
   - **擬態語派生型**: オノマトペから名詞化（例: 「ザクザク営業」）
   - **転用型**: 別業界の専門用語を転用（例: 「精密弾道」← 軍事用語）
   - **体感型**: N1の体感・五感を言語化（例: 「一発実感」）
   - **矛盾融合型**: 相反する概念を1語に（例: 「静かな爆発」）
4. **本能チェック**: 造語を見た瞬間に本能が反応するか？
   - 「え、何それ？」（好奇心）→ ✅
   - 「あ、それ欲しい」（欲望）→ ✅
   - 「ふーん」（無反応）→ ❌ 作り直し

#### Step 2.5: ライトスクリーニング（ベクトル即時評価）

**24案を生成した直後に、全案をベクトル化してスコアリング。**
パクに見せる前に数値根拠を付ける。感覚と数値のハイブリッド判断を可能にする。

※ ライトモード（all_vectors.json なし）の場合はスキップし、定性評価のみで提示。

```python
# 24案を一気にベクトル化 + 3指標算出
for c in candidates:
    c['vector'] = embed(c['text'])
    c['only1_score'] = 1 - np.mean([cosine_sim(c['vector'], np.array(cv['vector'])) for cv in comp_vecs])
    c['n1_demand_sim'] = cosine_sim(c['vector'], np.array(n1_demand['vector']))
    c['new_cognition_sim'] = cosine_sim(c['vector'], np.array(n1_cognition['vector']))
    c['total'] = c['only1_score'] * 0.4 + c['n1_demand_sim'] * 0.3 + c['new_cognition_sim'] * 0.3

# ランクA/B/Cを付与
for c in sorted(candidates, key=lambda x: -x['total']):
    if c['only1_score'] > 0.40 and c['n1_demand_sim'] > 0.55 and c['new_cognition_sim'] > 0.50:
        c['rank'] = 'A'
    elif c['only1_score'] < 0.30 or c['n1_demand_sim'] < 0.40:
        c['rank'] = 'C'
    else:
        c['rank'] = 'B'
```

表示フォーマット:

```
━━━ 24案 ベクトルスクリーニング ━━━
方向 | コンセプト          | Only1度 | N1刺さり | 新認知力 | 総合 | ランク
A    | ○○○○○            | 0.45 ✅ | 0.68 ✅  | 0.62 ✅  | 0.57 | A
D    | ○○○○○            | 0.52 ✅ | 0.61 ✅  | 0.58 ✅  | 0.56 | A
E    | ○○○○○            | 0.48 ✅ | 0.55 ✅  | 0.54 ✅  | 0.52 | A
...
C    | ○○○○○            | 0.22 ⚠️ | 0.72 ✅  | 0.45 ⚠️  | 0.44 | C

A = 全指標OK（壁打ちの主軸候補）
B = 一部要改善（磨けば化ける可能性）
C = 再考推奨（数値的に弱い）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**重要**: ランクCだからといって即却下しない。数値は「参考」。パクの直感がAランクを超えることもある。
ランクと直感が乖離した場合、それ自体が議論の種になる。

#### Step 3: パクとラリー

パクが気になった案を選ぶ or 自分のアイディアを出す → それを軸にさらに磨く。
**パクが「これだ」と言うまで繰り返す。**

### コンセプト確定条件

- パクが「これ」と明言
- 10文字以内
- 7つの問い全て ✅

**確定の合意**:
```
コンセプト: 「{確定コンセプト}」
これでいく？
```
パクの「いく」「OK」「これ」等の明確な承認を得てから次へ。確定したらベクトル化して一時保持。Phase 6 でまとめて検証。

---

## Phase 3: キービジュアル壁打ち

### キービジュアルとは

> **コンセプトを一枚の絵にしたもの。全フォーマットで統一する視覚の核。**

- バナーでも、動画のサムネでも、記事LPのFVでも、この「絵の方向性」は同じ
- 商品写真の見せ方、背景、色、光、構図、モデルの有無
- ブランドアセット（strategy.json の assets.brandAssets）と整合する

### 壁打ちの進め方

#### Step 0: 先に絵を出す（初めに絵にすると進む理論）

> **頭で考えるより先に絵を出す。絵にした瞬間に分かることがある。**

Phase 3 に入ったら、分析より先に**ラフなビジュアルイメージを3枚提案する**。
Step 1の言語化は「絵を見てから」やる。絵が先、言語化は後。

提案フォーマット:
```
━━━ まず絵を出す ━━━
[絵A] {コンセプトをそのままビジュアル化したラフイメージ説明}
[絵B] {N1のBefore/After感情を絵にしたラフイメージ説明}
[絵C] {競合と全然違う切り口のラフイメージ説明}

どれが「なんか近い」感じする？全部違う？
━━━━━━━━━━━━━━━
```

パクが「絵Bが近い」「こういう感じじゃなくて」など反応したら、**その反応を起点にStep 1へ進む**。
絵を見ないと分からなかった方向性が、ここで一気に見えてくる。

#### Step 1: ビジュアルコンセプトの言語化

コンセプトから逆算して、以下を定義:

```json
{
  "visualConcept": "一言でどんな絵か",
  "mood": "清潔/高級/カジュアル/衝撃/温かみ/科学的/...",
  "colorDirection": {
    "primary": "strategy.jsonのブランドカラー",
    "accent": "コンセプトを強調するアクセント色",
    "background": "背景の方向性（白/暗/グラデ/自然/...）"
  },
  "productPresentation": "商品をどう見せるか（手持ち/俯瞰/使用中/Before-After/成分フォーカス/...）",
  "humanElement": "人の有無（モデル/手/なし）＋表情方向（笑顔/驚き/悩み/安心/...）",
  "typography": "文字の方向性（太ゴシック/細明朝/手書き/...）",
  "composition": "構図の方向性（センター/三分割/対比/...）"
  "differentiator": "競合ビジュアルとの差別化ポイント"
}
```

#### Step 2: 3方向の提案

- **方向A: コンセプト直球** — コンセプトの言葉をそのままビジュアル化
- **方向B: 感情フォーカス** — N1のBefore/Afterの感情を絵にする
- **方向C: 新常識ビジュアル** — 「え、こんな見せ方あるの？」の驚き

#### Step 3: パクとラリー

パクのフィードバックを受けて磨く。
「もっと○○な感じ」「△△は違う」→ 反映して再提案。

### キービジュアル確定条件

- パクが「これ」と明言
- ブランドアセットと矛盾しない
- 全フォーマット（バナー/動画/記事LP）で使える汎用性

**確定の合意**:
```
キービジュアル: 「{visualConcept}」
ムード: {mood} / 構図: {composition}
これでいく？
```
パクの承認を得てから次へ。

---

## Phase 4: セールスコピー壁打ち

### セールスコピーとは

> **N1の心を動かす、最も大事な一文。全クリエイティブの核弾頭。**

- コンセプトを「人に伝わる言葉」に変換したもの
- バナーのヘッドライン、動画の冒頭テロップ、記事LPのFV — 全部ここから派生
- 新認知を形成できる一文（strategy.json の newCognitionStrategy を体現）

### 壁打ちの進め方

#### Step 1: セールスコピーの種を出す

strategy.json の以下を材料に:
- `concept.selected` — コンセプト
- `primaryN1.newCognitionStrategy` — 新認知戦略
- `layerCommunication[primaryN1.layer].hookAngle` — フック角度
- `messageSystem.primaryMessage` — メインメッセージ

**15文字以内のセールスコピー候補を10案**出す。

#### Step 2: 10案を3軸で評価

| 軸 | 基準 |
|----|------|
| **新認知形成力** | この一文で、N1の「常識」が変わるか |
| **感情起動力** | 読んだ瞬間に感情が動くか（驚き/共感/欲求） |
| **記憶残存力** | 3秒後に思い出せるか。リズム・語感・意外性 |

各案を ★1-5 で採点。パクに上位3案を提示。

#### Step 3: パクとラリー

パクが選ぶ or 自分のアイディアを出す。
「表現を生み出すコツ」:
- ゴール（判断）からストレートに作るのではなく
- **「こういう思考になってもらうとよさそう」→ そのための表現**
- N1の脳内で何が起きるかを逆算して言葉を選ぶ

#### Step 4: コピーA/Bペアの生成

確定したセールスコピーをベースに:
- **A案**: 確定コピーそのまま（ストレート）
- **B案**: 同じコンセプトを別角度で表現（フックを変える）

このA/Bペアが全アウトプットSkillsの起点になる。

### セールスコピー確定条件

- パクが「これ」と明言
- 15文字以内
- 新認知形成力 ★4以上
- コンセプトと一貫している

**確定の合意**:
```
セールスコピーA: 「{primary}」
セールスコピーB: 「{primaryB}」
これでいく？
```
パクの承認を得てから次へ。

---

## Phase 5: マーケティング戦略整理（壁打ち）

### このPhaseの位置づけ

> **コンセプト・KV・セールスコピーが確定した。次は「どう届けるか」の戦略。**

コンセプトが「何を言うか」なら、マーケ戦略は「誰に・どのフォーマットで・どう言うか」。
各アウトプットSkill（Banner/ShortAd/記事LP）が**同じ戦略のもとで動く**ための共通設計図を作る。

### 5-A: フォーマット別戦略マトリクス

確定コンセプト・KV・セールスコピーを前提に、各フォーマットの役割とメッセージを整理する。

→ `.claude/knowledge/creative-reference.md`「フォーマット別戦略マトリクス」参照。
各フォーマットの{メッセージ}{ストーリーアーク}{認知変化フロー}等はこのセッションで生成・表示する。

→ 「修正したいところある？フォーマットごとの攻め方、これでいい？」

### 5-B: フック角度のバリエーション

セールスコピーA/Bをベースに、**フック角度のバリエーション**を3-5個生成する。
各フォーマットのA/Bテスト（バナー10枚の多様性、動画冒頭3パターン、記事FV3パターン）の核になる。

フック角度の分類:
- **常識否定型**: 「○○は逆効果だった」— N1の常識を壊す
- **共感型**: 「○○で悩んでませんか」— N1の痛みに寄り添う
- **結果提示型**: 「○○が○日で○○に」— Before→Afterを圧縮
- **権威型**: 「○○専門家が警告」— 権威の力を借りる
- **好奇心型**: 「なぜ○○は○○なのか」— 答えが知りたくなる

```
━━━ フック角度バリエーション ━━━
角度1: {type} — 「{hook_text}」
角度2: {type} — 「{hook_text}」
角度3: {type} — 「{hook_text}」
角度4: {type} — 「{hook_text}」
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5-C: メッセージ体系

コンセプト・セールスコピー・フック角度を束ねた、全クリエイティブ共���のメッセージ体系を定義。

```json
{
  "primaryMessage": "メインメッセージ（N1に刺す一文）",
  "supportingMessages": [
    "サポートメッセージ1（ベネフィット）",
    "サポートメッセージ2（信頼）",
    "サポートメッセージ3（差別化）"
  ],
  "toneOfVoice": "ブランドの語り口",
  "ngExpressions": ["法規NG表現リスト"]
}
```

### 5-D: 戦略の合意

```
━━━ マーケティング戦略まとめ ━━━
コンセプト: 「{concept}」 ✅確定済み
KV: 「{visualConcept}」 ✅確定済み
セールスコピーA: 「{primary}」 ✅確定済み
セールスコピーB: 「{primaryB}」 ✅確定済み

フォーマット別戦略:
  バナー: {role要約}
  動画30秒: {role要約}
  記事LP: {role要約}

フック角度: {N}個
メッセージ体系: 定義済み

修正点があればここで！なければ、これも決定？
━━━━━━━━━━━━��━━━━━━━━━━━━━━━━━━━━━
```

**パクの「決定」を得てからPhase 6（ベクトル化）に進む。**
修正があればラリーして、パクが納得するまで磨く。

---

## Phase 6: ベクトル検証 + strategy.json 更新

### 6-A: 確定要素のベクトル検証

**共通関数（embed / cosine_sim）→ `.claude/knowledge/vector-utils.md` を参照。**

Concept Park固有の6検証:

```python
# 共通関数は vector-utils.md から。以下はConcept固有ロジックのみ

# 確定3要素をベクトル化
concept_vec = embed(confirmed_concept)
visual_vec = embed(confirmed_visual_concept)
copy_vec = embed(confirmed_sales_copy)
copy_b_vec = embed(confirmed_sales_copy_b)

# 検証1: 競合との距離（Only1度） — sim > 0.60 なら ⚠️
# 検証2: N1需要との距離（刺さり度）
# 検証3: 3要素の一貫性（コンセプト×コピー×ビジュアル） — sim < 0.45 なら ⚠️乖離
# 検証4: A/Bの差異 — sim > 0.80 なら ⚠️似すぎ
# 検証5: フック角度の多様性 — 平均sim > 0.75 なら ⚠️
# 検証6: フック × N1需要
```

**閾値基準**:
| 検証 | OK基準 | NG時 |
|---|---|---|
| 競合距離 | sim <= 0.60 | Only1度が足りない → コンセプト差別化 |
| 3要素一貫性 | sim >= 0.45 | コンセプト⇔コピー⇔ビジュアルが乖離 |
| A/B差異 | sim <= 0.80 | テスト意味なし → 片方のフック角度変更 |
| フック多様性 | 平均sim <= 0.75 | 似たフックが多い → 角度追加 |

### 6-B: strategy.json 更新

確定した全要素 + ベクトルをstrategy.jsonに書き込み:

```json
{
  "concept": {
    "selected": "確定コンセプト（10文字以内）",
    "tagline": "サブコピー",
    "goldenCircle": { "why": "", "how": "", "what": "" },
    "only1Position": "確定Only1ポジション",
    "conceptVector": [0.01, 0.02, ...],
    "vectorValidation": {
      "vsCompetitorAvgSim": 0.00,
      "vsN1DemandSim": 0.00,
      "verdict": "Only1確認済み"
    }
  },

  "keyVisual": {
    "visualConcept": "一言でどんな絵か",
    "mood": "",
    "colorDirection": {},
    "productPresentation": "",
    "humanElement": "",
    "typography": "",
    "composition": "",
    "differentiator": "",
    "visualVector": [0.01, 0.02, ...]
  },

  "salesCopy": {
    "primary": "確定セールスコピー（15文字以内）",
    "primaryB": "B案（別角度、15文字以内）",
    "primaryVector": [0.01, 0.02, ...],
    "primaryBVector": [0.01, 0.02, ...],
    "evaluation": {
      "newCognitionPower": 5,
      "emotionTrigger": 5,
      "memoryRetention": 5
    },
    "vectorValidation": {
      "vsCompetitorAvgSim": 0.00,
      "vsN1DemandSim": 0.00,
      "abDifference": 0.00
    }
  },

  "messageSystem": {
    "primaryMessage": "メインメッセージ（N1に刺す一文）",
    "supportingMessages": [
      "サポートメッセージ1（ベネフィット）",
      "サポートメッセージ2（信頼）",
      "サポートメッセージ3（差別化）"
    ],
    "toneOfVoice": "ブランドの語り口",
    "ngExpressions": ["法規NG表現リスト"]
  },

  "formatStrategy": {
    "banner": {
      "role": "1秒で新認知のフックを刺す — 興味の入口",
      "primaryMessage": "バナー用に研ぎ澄ましたメッセージ",
      "vectorCheckpoints": {
        "headline_vs_concept": ">= 0.50（一貫性）",
        "headline_vs_competitor": "<= 0.55（差別化）",
        "inter_banner_diversity": "<= 0.70（多様性）"
      }
    },
    "shortAd": {
      "role": "30秒で感情体験させる — Before→新認知→After",
      "storyArc": "Before→新認知→After の感情曲線",
      "openingHook": "動画冒頭3秒のフック方針",
      "vectorCheckpoints": {
        "hook_vs_n1demand": ">= 0.55（刺さり度）",
        "story_vs_concept": ">= 0.50（一貫性）",
        "hook_vs_competitor": "<= 0.55（差別化）"
      }
    },
    "articleLP": {
      "role": "5分で論理的に納得させる — 問題深掘り→新基準→商品証明→購買決定",
      "cognitiveFlow": "問題提起→常識の否定→新基準→商品証明→購買決定",
      "fvMessage": "FVヘッドラインの方針",
      "vectorCheckpoints": {
        "fv_vs_concept": ">= 0.55（一貫性）",
        "section_flow_coherence": ">= 0.40（論理の流れ）",
        "cta_vs_purchase_motivation": ">= 0.50（購買接続）"
      }
    }
  },

  "hookVectors": [
    {
      "angle": "常識否定型",
      "text": "フック文",
      "vector": [0.01, 0.02, ...]
    }
  ]
}
```

all_vectors.json にも確定ベクトルを追加:
- category: "confirmed_concept" — 確定コンセプト
- category: "confirmed_visual" — 確定キービジュアル
- category: "confirmed_copy" — 確定セールスコピーA/B
- category: "confirmed_hook" — 確定フック角度（各角度ごとに1エントリ）

---

## Phase 7: 確定プレゼン

パクに最終確認:

```
━━━━━ CONCEPT PARK 確定 ━━━━━
コンセプト: 「{concept}」
キービジュアル: 「{visualConcept}」
セールスコピーA: 「{salesCopy.primary}」
セールスコピーB: 「{salesCopy.primaryB}」

フォーマット別戦略:
  バナー: {formatStrategy.banner.role}
  動画30秒: {formatStrategy.shortAd.role}
  記事LP: {formatStrategy.articleLP.role}

フック角度: {hookVectors.length}個
  {角度1} / {角度2} / {角度3} / ...

ベクトル検証:
  Only1度:  コンセプト {sim} / コピーA {sim} / コピーB {sim}
  N1刺さり: コンセプト {sim} / コピーA {sim} / コピーB {sim}
  一貫性:   コンセプト×コピーA {sim} / コンセプト×ビジュアル {sim}
  A/B差異:  {sim}
  フック多様性: {フック間平均sim} {✅多様/⚠️似すぎ}

strategy.json 更新済み。

次のアクション:
  → /banner-park でバナー生成
  → /shortad-park で動画広告生成
  → /記事LP-park で記事LP生成
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 注意事項

- 壁打ち型スキル。パクとの対話が前提。自走で完遂しない
- **2つの合意ポイント**:
  1. Phase 2/3/4 末の「これでいく？」— コンセプト/KV/セールスコピーの各確定
  2. Phase 5-D の「これも決定？」— マーケティング戦略の確定
- ベクトルは3段階で活用: 入口（Phase 1-C 地図）→ 中間（Step 2.5 スクリーニング）→ 出口（Phase 6 最終検証）
- strategy.json の concept / keyVisual / salesCopy / messageSystem / formatStrategy / hookVectors を更新する
- all_vectors.json にも確定ベクトルを追加する（concept, visual, copy, hook）
- **フォーマット別戦略 = 各アウトプットSkillの設計図**:
  - Banner Park: formatStrategy.banner + hookVectors → ヘッドライン多様性 + ビジュアル指示
  - ShortAd Park: formatStrategy.shortAd + hookVectors → 30秒ストーリー + 冒頭3パターン
  - 記事LP Park: formatStrategy.articleLP → 認知変化フロー + FVヘッドライン
