# 記事LP Park ver.3.0 — 戦略翻訳型 × ベクトル品質ゲート × hookVector × KV哲学フィルター × PDFレポート

strategy.json + Concept Park 完了前提。3つの魂 — **パラダイムシフトの教科書そのもの × キラーFVコピー × 別の仮説**。DPro KV哲学フィルター × ベクトル品質ゲート × Gemini 3 Pro Image × PDFマーケティングインテリジェンスレポート。
このスキルはultrathinkを使用して読者の心理を深く読み解く。hookVectorの選定とコピーの最終判断に拡張思考を自動発動する。

`/記事LP-park` で起動。

---

## 起動時表示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  記事LP PARK ver.3.0
  戦略翻訳型 × 仮説駆動 × ベクトル品質保証 × PDFレポート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  前提: /research-park + /concept-park 完了済み
  3つの魂:
    1. パラダイムシフトの教科書そのもの
    2. キラーFVコピー
    3. 別の仮説
  DPro KV哲学フィルター × ベクトル品質ゲート × PDFレポート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

ランダム1行:
- 「戦略を5分の論証に翻訳する。読者の常識を、ひっくり返す。」
- 「FV3パターン。どの入口が最強か、ベクトルが判定する。」
- 「仮想敵を設定して、パラダイムシフトを仕込む。」
- 「売れてる記事LP × 美しい構造。両方揃ったDNAだけ学ぶ。」
- 「N1の脳内に1番乗りする記事LP、作るぞ。」

---

## 3つの魂（哲学）

記事LP Park v3.0 が生み出す全ての記事LPは、この3つの魂を宿す。

### 魂1: パラダイムシフトの教科書そのもの

> **各記事LPが、読者の常識を覆し新パラダイムで納得させる「5分の教科書」であろうとする。**

記事LPは「商品を売るページ」ではない。読者が今まで信じていた間違った常識（仮想敵）を教育で覆し、新しい真実（パラダイム）で論理的に納得させ、「だからこの商品か」と自然に購買決定に至らせる体験。
strategy.json の `formatStrategy.articleLP.cognitiveFlow` を忠実に翻訳する。

### 魂2: キラーFVコピー

> **FVのキャッチコピーは、その1行で「先を読みたい」と思わせるキラーフレーズであろうとする。**

FVコピーは「説明文」ではない。ポメ太さんDIVE哲学の全てが凝縮された1行。
「この1行だけ見て、スクロールしたくなるか？」が基準。
シーン喚起 × 好奇心のギャップ × 情報の欠落。

### 魂3: 別の仮説

> **N本の記事LP — 数ではなく仮説の数。各記事LPが異なる検証仮説を持つ。**

同じコピーの色違いを量産しない。各記事LPが「このN1に、この仮想敵で、このフック角度で刺したら？」という固有の仮説を持つ。
配信後に「どの仮説が当たったか」が分かる設計。

---

## ver.2.2 → ver.3.0 の進化

| 領域 | ver.2.2 | ver.3.0 |
|------|---------|---------|
| **起点** | 自前でN1/コンセプト設計 | **strategy.json 翻訳**（上流確定済み） |
| **ベクトル活用** | エンベディング保存のみ | **3箇所活用: hookVector選択→品質ゲート→事後検証** |
| **hookVector** | なし（感覚でフック選定） | **ベクトル空間で多様性最大化選択** |
| **DPro記事LP選定** | 5軸スコアリング（数字のみ） | **KV哲学フィルター（数字 × 構造美）** |
| **品質ゲート** | 生成後チェックのみ | **生成前ベクトルゲート + 生成後3層検証** |
| **レポート** | ポートフォリオHTML | **PDFマーケティングインテリジェンスレポート** |
| **3つの魂** | なし | **各記事LP=固有の仮説** |
| **画像生成** | Imagen 4.0 | **Gemini 3 Pro Image** |
| **エンベディング** | OpenAI text-embedding-3-small | **Gemini Embedding（gemini-embedding-2-preview）** |
| **商材リサーチ** | Phase 1.5で毎回実行 | **strategy.json に集約済み（スキップ）** |
| **エージェント数** | 3〜4（リサーチ+分析+AIパク+品質） | **2（構造分析+品質ゲート）** |

---

## ワークフロー概要

```
Phase 0: 戦略読み込み + ヒアリング
    ├─ strategy.json + all_vectors.json 必須読み込み
    ├─ 素材・アセット確認
    └─ 媒体 / 生成本数 / ターゲット層確認
    ↓
Phase 1: DPro KV哲学フィルターリサーチ（記事LP版）
    ├─ Stage 1: 数字フィルター（cost_difference TOP100）
    ├─ Stage 2: 構造哲学フィルター（★1-5）
    ├─ 合格5-8本の構造分析（32要素タクソノミー）
    └─ 勝ちDNA抽出
    ↓
Phase 2: N本記事LP 仮説設計（戦略翻訳）
    ├─ strategy.json → 記事LP翻訳
    ├─ hookVector選択（ベクトル多様性最大化）
    ├─ 各記事LPの仮説カード
    ├─ 仮想敵パラダイムシフト具体化
    └─ FV3パターン × hookVector マッピング
    ↓
Phase 3: ベクトル品質ゲート（生成前検証）
    ├─ 検証1: コンセプト一貫性（FVコピー × concept ≥ 0.50）
    ├─ 検証2: 競合差別化（FVコピー × competitor_avg ≤ 0.55）
    ├─ 検証3: 記事LP間多様性（inter_lp_sim ≤ 0.70）
    └─ FAIL時: 自動修正 → 3回トライ → パク判断
    ↓
Phase 4: 記事LP HTML生成
    ├─ パラダイムシフト構造実装
    ├─ FV3パターン タブ切替+スワイプ UI
    ├─ ポメ太さんDIVE哲学 品質基準適用
    └─ Gemini 3 Pro Image 画像生成
    ↓
Phase 5: 3層品質検証
    ├─ Layer 1: コピー品質（ポメ太さん哲学チェック）
    ├─ Layer 2: HTML品質 + 法規チェック
    └─ Layer 3: ベクトル事後検証
    ↓
Phase 6: PDFマーケティングインテリジェンスレポート
    ├─ 戦略サマリー
    ├─ 記事LPポートフォリオ（各LP × 仮説カード）
    ├─ ベクトル検証レポート
    ├─ DProリサーチ分析
    ├─ A/Bテスト戦略
    └─ Next Action
```

---

## 初回セットアップチェック

### Step 1: 環境変数チェック

```bash
echo "GEMINI_KEY: ${GEMINI_API_KEY:+SET}"
```

### Step 2: DPro MCP 接続チェック

`search_genres_api_v1_genres_get` を `keyword: "test"` で1回呼び出す。

### 判定

- 全てOK → Phase 0 へ
- 未設定あり → セットアップガイド表示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  初回セットアップが必要です
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Gemini APIキー（画像生成用）
     export GEMINI_API_KEY="your-gemini-api-key"

  2. DPro MCP接続（広告データ取得用）
     .mcp.json に設定してください

  設定が完了したら「OK」と入力してください。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ナレッジ読み込み

以下を **Read tool で必ず読む**:
- `.claude/knowledge/article-lp-rules.md` — 記事LPの鉄則10原則
- `.claude/knowledge/pak-philosophy.md` — パクの哲学 + ポメ太さんDIVE哲学

※ N1/コンセプト/KV/セールスコピー/フック角度は全て strategy.json に確定済み。

---

## Phase 0: 戦略読み込み + ヒアリング

### 0-A: strategy.json 読み込み（必須前提）

`research-park/output/{PRODUCT_SLUG}/strategy.json` を Read。
なければ → 「先に `/research-park` + `/concept-park` を実行してね」と案内して終了。

strategy.json から以下を取得:

| フィールド | 用途 |
|-----------|------|
| `productIntel` | 商品情報・USP・価格・オファー |
| `primaryN1` | ターゲットN1（層・ペルソナ・新認知戦略） |
| `concept` | コンセプト・Only1ポジション・conceptVector |
| `keyVisual` | ビジュアル方向性 |
| `salesCopy` | セールスコピーA/B・ベクトル |
| `messageSystem` | メッセージ体系・トーン・NG表現 |
| `formatStrategy.articleLP` | 記事LP固有の役割・認知フロー・FVメッセージ |
| `hookVectors` | フック角度バリエーション + ベクトル |
| `competitorAnalysis` | 競合分析（仮想敵設計に活用） |
| `assets` | ブランドアセット |

`all_vectors.json` も Read → 品質ゲートで使う。

**formatStrategy.articleLP / hookVectors が空の場合** → 「先に `/concept-park` を完了してね」と案内。

### 0-B: 素材・アセット確認

1. `assets/{slug}/manifest.json` の存在チェック
   - あり → ロゴ・ブランドカラー・商材URL を自動読み込み
   - なし → strategy.json の assets / keyVisual から推定

2. `.claude/knowledge/aporo-assets/` 等の商材固有素材フォルダをチェック
   - あり → INDEX.md を読み、利用可能な素材を把握

3. `記事LP-park/assets/{slug}/lp-structure.json` の存在チェック
   - あり → 既存LP構造データを再利用
   - なし → strategy.json の productIntel.url があれば WebFetch で取得

### 0-C: ヒアリング

パクに以下を**選択肢形式**で質問:

```
━━━ 記事LP設定 ━━━

1. 広告媒体は？
   a) Meta（Facebook + Instagram）
   b) TikTok
   c) Google
   d) その他（入力）

2. 生成本数は？
   a) 2本（標準 — 2つの異なる仮説）
   b) 3本（拡張 — 3つの仮説セット）
   c) 1本（最小 — 集中型）

3. ターゲット層確認:
   strategy.json のプライマリーN1は
   「{N1名前}（{N1層}）」です。
   a) このN1で進める
   b) 別の層を追加したい（入力）
━━━━━━━━━━━━━━━━━━
```

### 0-D: プリセット自動推定

strategy.json の `productIntel.category` から自動推定:

| プリセット | カテゴリキーワード | 記事LP方針 |
|----------|-----------------|-----------|
| **SaaS/BtoB系** | SaaS, AI, ツール, 営業, マーケ | 課題整理→比較→選定基準→導入メリット→事例 |
| **美容系** | 美容液, 肌, スキンケア, 脱毛 | 悩み共感→成分教育→変化の描写→社会的証明 |
| **サプリ系** | サプリ, 健康食品, 栄養, 成分 | 悩み共感→原因教育→成分→利用実感→オファー |
| **教育系** | 学習, スクール, 講座, 資格 | 課題整理→比較→選定基準→導入メリット |
| **クリニック系** | クリニック, 医療, 処方 | 不安解消→信頼性重視→根拠ベース |

---

## Phase 1: DPro KV哲学フィルターリサーチ（記事LP版）

**メインエージェントが DPro MCP を直接実行。**

### 哲学: 「数字 × 構造美」の2段階選定

普通のリサーチ = 売れてる記事LPを集める。
KV哲学フィルター = **売れてる × 構造が美しい記事LPだけ学ぶ**。

### Step 1: ジャンル特定

`search_genres` で関連ジャンル1-3個特定。
strategy.json の `dproIntel.genreId` があればそれを使用。

### Step 2: DPro データ取得

`get_items` で以下の条件で取得:

| 条件 | パラメータ |
|------|-----------|
| 月間安定勝ち | interval=30, sort=cost_difference-desc, limit=100 |

### Step 3: 候補20件選出

100件から候補20件を以下の3カテゴリで各6-7件リストアップ:

| # | 記事タイプ | 選別キーワード | 狙い |
|---|----------|--------------|------|
| 1 | **比較/ランキング型** | ランキング, おすすめ, 比較, TOP | 比較記事の勝ちパターン |
| 2 | **体験談/レビュー型** | 使ってみた, 体験, 口コミ, レビュー | UGC記事の勝ちパターン |
| 3 | **教育/解説型** | 原因, なぜ, 知らない, 理由, 実は | 教育型記事の勝ちパターン |

### Step 4: KV哲学フィルター（構造哲学スコア）

20件の ad_all_sentence + 遷移先テキストを分析し、**2軸で評価**。

**遷移先テキスト取得**: `read_transition_url_text_content` MCP ツールを使用。`transition_url_id` を渡すと、記事LP本文（HTMLテキスト + OCRテキスト）を取得できる。これにより記事LP構造を分析可能。

```
各記事LPに対して:

■ 数字スコア（DProデータから自動）
  cost_difference / play_count

■ 構造哲学スコア（AIが判定）
  「この記事LPは、パラダイムシフトの教科書として美しく成立しているか？」
  5段階: ★1（単なる商品紹介）〜 ★5（パラダイムシフトの教科書レベル）

  判定基準:
  - パラダイムシフト構造の完成度（仮想敵 → 教育 → 新パラダイム → 商品）
  - FVのフック力（好奇心のギャップ、シーン喚起）
  - CTA導線の設計品質（配置 × テキストバリエーション × 心理トリガー）
  - セクション密度のバランス
  - コピーの引き出し力（ポメ太さん哲学基準）

合格ライン: 数字TOP20 かつ 構造哲学 ★3以上 → 学習対象
```

### Step 5: 合格記事LPの構造分析

**Agent設定**: `subagent_type: "general-purpose"`, `name: "記事LP構造分析くん"`
合格5-8本の遷移先テキスト（Step 4で取得済み）を渡し、**32要素タクソノミー** でマッピングさせる。メインはDPro MCP実行に専念、分析はサブに委譲。

32要素は以下の6カテゴリ:
- カテゴリ1: 導入・共感（anchor_cta, problem_empathy, statistics, persona_voice, read_time）
- カテゴリ2: 教育・解説（cause_education, existing_denial, fear_appeal, solution_intro, qa_bubble, ingredient_education）
- カテゴリ3: 商品紹介・比較（selection_guide, fake_warning, comparison_table, product_detail, brand_story, competitors_brief）
- カテゴリ4: 信頼性・エビデンス（authority_media, clinical_evidence, expert_endorsement, third_party_review）
- カテゴリ5: 口コミ・社会的証明（testimonials, before_after, usage_flow, merit_demerit）
- カテゴリ6: CTA・オファー（discount_offer, risk_reversal, urgency_scarcity, postscript_urgency, loss_amount, survey_cta, final_summary）

各記事LPから抽出:
1. 要素構成 + 出現順序
2. パラダイムシフト構造（旧パラダイム → ピボットポイント → 新パラダイム）
3. FV分析（フックタイプ、視線設計、シーン喚起度）
4. CTA導線（出現回数/位置/テキストバリ/心理トリガー）
5. セクション密度（フェーズ別%配置）
6. コピー哲学分析（ポメ太さん基準: シーン喚起/情報欠落/Before→After/再現性）
7. **構造再現プロンプト（reconstructionPrompt）** — 400-600文字
8. **FV再現プロンプト（fvReconstructionPrompt）** — 200-300文字

### Step 6: 勝ちDNA抽出

合格記事LP群から、共通する勝ちパターンをサマリー:

```json
{
  "winningDNA": {
    "fvPatterns": ["最頻出FVパターン3つ"],
    "paradigmShiftStructure": "最も多い構造パターン",
    "ctaDesign": "最適なCTA導線設計",
    "sectionBalance": "理想的なセクション密度比率",
    "copyPhilosophy": "勝ち記事LPに共通するコピーの特徴",
    "topReconstructionPrompts": ["再現用プロンプトTOP3"]
  }
}
```

---

## Phase 2: N本記事LP 仮説設計（戦略翻訳）

### 設計の原則

**N本 = N個の仮説。** 各記事LPが固有の検証仮説を持つ。

仮説の変数:
- **仮想敵**: どの「間違った常識」を覆すか
- **フック角度**: hookVectors から選択
- **認知フロー**: strategy.json の cognitiveFlow をどの角度から展開するか
- **FV3パターン**: 各パターンがどのhookVectorに対応するか
- **パラダイムシフト構造**: 旧→新の転換ポイント

### Step 1: strategy.json → 記事LP翻訳

strategy.json のデータを記事LP用に翻訳:

| strategy.json | 記事LP翻訳 |
|--------------|-----------|
| `concept.selected` | 記事全体の論理の核 |
| `concept.tagline` | FVサブコピーの軸 |
| `primaryN1.persona` | 記事のペルソナトーン決定 |
| `primaryN1.newCognitionStrategy` | パラダイムシフトの方向性 |
| `salesCopy.primary/primaryB` | 記事内の見出し群の軸 |
| `messageSystem` | トーン&マナー / NG表現チェック |
| `formatStrategy.articleLP.cognitiveFlow` | 記事構成の骨格 |
| `formatStrategy.articleLP.fvMessage` | FVキャッチコピーの方向性 |
| `hookVectors` | フック角度バリエーション |
| `competitorAnalysis` | 仮想敵の具体化素材 |
| `productIntel.usp` | 「新パラダイム → 商品」の接続点 |
| `productIntel.caseStudies` | 社会的証明セクション素材 |

### Step 2: hookVector 選択（ベクトル多様性最大化）

N本分のフック角度を、ベクトル空間上で最大限バラけるように自動選択。

**実装コード → `.claude/knowledge/vector-utils.md`「hookVector 選択アルゴリズム」セクションを参照。**

- 閾値: N1需要 sim >= 0.45 / hookVector間 sim <= 0.70
- `target_count = article_count` として実行

### Step 3: 仮想敵パラダイムシフト具体化

strategy.json の `competitorAnalysis` + `primaryN1.newCognitionStrategy` + `concept` を元に、各記事LP用の仮想敵を設計:

```json
{
  "lpIndex": 1,
  "virtualEnemy": {
    "falseBeliief": "読者が今信じている間違った常識",
    "whyWrong": "なぜその常識が間違いか（教育フェーズの核）",
    "newParadigm": "覆した後の新しい真実",
    "effortlessSolution": "「頑張りたくない」解決策",
    "shiftMoment": "パラダイムシフトが起きる瞬間の設計",
    "sceneEvocation": "読者の脳内に描かせるシーン（Before / After）",
    "curiosityGap": "好奇心のギャップ設計"
  },
  "hookAngle": "hookVectors[X] — 選択されたフック角度",
  "hookSource": "hookVectors[X].text",
  "hypothesis": "この記事LPが検証する仮説",
  "testHypothesis": "配信後に検証したい具体的な問い"
}
```

### Step 4: FV3パターン × hookVector マッピング

各記事LPの FV3パターンを設計。**各パターンが hookVector のどの角度に対応するか**を明示:

```
パターンA: 痛み直撃型（Problem-First）
  - 視線設計: F型
  - hookVector: 共感型フックを使用
  - ポメ太さん: シーン喚起（悩みのシーンを脳内に描かせる）
  - 情報欠落: 解決策を一切示さず好奇心のギャップを作る

パターンB: 新常識提示型（Paradigm-First）
  - 視線設計: Z型
  - hookVector: 常識否定型フックを使用
  - ポメ太さん: Before→Afterの飛躍
  - 情報欠落: 新常識の結論だけ言い「なぜ」を後に（ひよこ理論）

パターンC: ストーリー導入型（Story-First）
  - 視線設計: 中央集中型
  - hookVector: 好奇心型フックを使用
  - ポメ太さん: 読者の内側から引き出す
  - 情報欠落: 結論の手前で止め「でも…」の先を読ませたくさせる
```

各パターンの品質基準（全FV必須）:

| チェック項目 | 基準 |
|-----------|------|
| シーン喚起力 | 5段階で **4以上** 必須 |
| 好奇心のギャップ | 「知りたい」を生む情報の欠落 |
| 100人100通り | 多解釈可能性 |
| 精緻化見込み | 読者が自分事化するか |
| 再現性の匂わせ | 「私でもできそう」の予感 |
| 「頑張りたくない」本能 | 「楽そう」の印象 |

### Step 5: 記事LP設計書（lpSpec）生成

各記事LPの完全設計書を JSON で生成:

```json
{
  "lpIndex": 1,
  "hypothesis": "常識否定型フック × 比較検討層 — 既存ツールへの不満を新基準提示で解消",
  "hookAngle": "常識否定型",
  "hookSource": "hookVectors[0]",
  "targetN1": "strategy.primaryN1 の情報",
  "virtualEnemy": { "... Step 3 の設計 ..." },

  "fvPatterns": {
    "patternA": {
      "mainCopy": "痛み直撃型FVコピー",
      "subCopy": "サブコピー",
      "eyeFlow": "F型",
      "visualDirection": "暗めトーン、悩みの表情",
      "sceneEvocationScore": 4,
      "curiosityGapScore": 4
    },
    "patternB": { "..." },
    "patternC": { "..." }
  },

  "articleStructure": {
    "sections": [
      {"order": 1, "elementId": "anchor_cta", "content": "..."},
      {"order": 2, "elementId": "problem_empathy", "content": "...", "sceneEvocation": "..."},
      "..."
    ],
    "paradigmShiftPoint": 7,
    "ctaPositions": ["15%", "45%", "70%", "95%"],
    "sectionDensity": {
      "introduction": "18%",
      "education": "30%",
      "productComparison": "25%",
      "socialProof": "17%",
      "ctaOffer": "10%"
    }
  },

  "copyGuidelines": {
    "tone": "strategy.messageSystem.toneOfVoice",
    "ngExpressions": "strategy.messageSystem.ngExpressions",
    "conceptKeyword": "strategy.concept.selected",
    "salesCopyAxis": "strategy.salesCopy.primary"
  },

  "testHypothesis": "配信後に検証したい仮説"
}
```

---

## Phase 3: ベクトル品質ゲート（生成前検証）

**HTML生成に進む前に、FVコピーと記事構成の品質をベクトルで検証する。**

### ベクトル品質ゲート

**実装コード → `.claude/knowledge/vector-utils.md`「4段階ベクトル品質ゲート」セクションを参照。**

記事LP固有の準備:
```python
# 各記事LPのFVコピー（3パターン分）をベクトル化して item_vecs を作成
item_vecs = []
for spec in lpSpecs:
    for pattern_key in ['patternA', 'patternB', 'patternC']:
        fv = spec['fvPatterns'][pattern_key]
        vec = embed(fv['mainCopy'] + ' ' + fv['subCopy'])
        item_vecs.append({'index': f"LP{spec['lpIndex']}_{pattern_key}", 'vector': vec, 'label': fv['mainCopy']})
```

- 検証3（多様性）は同一パターン間で比較（LP1のA vs LP2のA）
- ゲート不通過時: FVコピー/フック角度/仮想敵を変更して再検証（最大3回）

---

## Phase 4: 記事LP HTML生成

### 4-A: パラダイムシフト構造実装

Phase 2 の lpSpec に基づき、各記事LPのHTMLを生成。

共通フロー（strategy.json の cognitiveFlow を翻訳）:

```
[floating-cta] アンカーCTA（常時表示）
    ↓
[FV3パターン タブ切替] — Phase 2 Step 4 の3パターン
    ↓
[悩み共感] 旧パラダイムの世界 — N1のペインを言語化
  ★シーン喚起: 悩みのシーンを脳内に描かせる
  ★好奇心ギャップ: 解決策を匂わせつつ情報を欠落
    ↓
[統計データ/ペルソナの声] 社会的証明
    ↓
--- 教育フェーズ ---
[原因教育] 仮想敵の正体を暴く
  ★情報欠落: 「ではどうすれば」をまだ言わない
    ↓
[既存解決策の限界] 今までの方法がダメな理由
    ↓
[放置リスク] このままだとどうなるか
    ↓
--- ★パラダイムシフトポイント★ ---
[解決策提示] 新パラダイム！
  ★シーン喚起: 理想のシーンを脳内に描かせる
    ↓
[成分/機能教育] なぜ楽に解決できるか
    ↓
--- 商品紹介フェーズ ---
[比較表/推し商品詳細] コンセプト一貫した商品紹介
    ↓
[権威付け/専門家推薦]
    ↓
[口コミ/Before After]
  ★再現性: 「私でもできた」をシーンで描く
    ↓
[利用フロー] 「たった3ステップ」
    ↓
--- CTAフェーズ ---
[オファー] 価格ハードル除去
    ↓
[リスクリバーサル]
    ↓
[緊急性]
    ↓
[最終まとめ + CTA]
  ★シーン喚起: 理想の未来を最後にもう一度描かせる
```

### 4-B: FV3パターン タブ切替+スワイプ UI

v2.2 と同じ UI コンポーネントを使用:

```html
<div class="fv-selector">
  <div class="fv-tabs">
    <button class="fv-tab active" data-fv="a">A: 痛み直撃</button>
    <button class="fv-tab" data-fv="b">B: 新常識</button>
    <button class="fv-tab" data-fv="c">C: ストーリー</button>
  </div>
  <div class="fv-indicator">1 / 3</div>
</div>
<div class="fv-swipe-container" id="fv-swipe">
  <div class="fv-panel active" id="fv-a">...</div>
  <div class="fv-panel" id="fv-b">...</div>
  <div class="fv-panel" id="fv-c">...</div>
</div>
```

FVタブ+スワイプ JavaScript（バニラJS）:
```javascript
(function(){
  const tabs = document.querySelectorAll('.fv-tab');
  const panels = document.querySelectorAll('.fv-panel');
  const indicator = document.querySelector('.fv-indicator');
  let current = 0;
  function switchTo(idx){
    current = idx;
    tabs.forEach(t=>t.classList.remove('active'));
    panels.forEach(p=>p.classList.remove('active'));
    tabs[idx].classList.add('active');
    panels[idx].classList.add('active');
    if(indicator) indicator.textContent = (idx+1)+' / '+panels.length;
  }
  tabs.forEach((tab,i)=>tab.addEventListener('click',()=>switchTo(i)));
  const container = document.getElementById('fv-swipe');
  let startX=0;
  if(container){
    container.addEventListener('touchstart',e=>{startX=e.touches[0].clientX},{passive:true});
    container.addEventListener('touchend',e=>{
      const diff=startX-e.changedTouches[0].clientX;
      if(Math.abs(diff)>50){
        if(diff>0 && current<panels.length-1) switchTo(current+1);
        if(diff<0 && current>0) switchTo(current-1);
      }
    },{passive:true});
  }
})();
```

### 4-C: HTML基本仕様

- モバイルファースト1カラム
- max-width: 420px, margin: 0 auto
- 単一HTMLファイル、外部依存ゼロ
- フォント: `"Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", sans-serif`
- **カラーは strategy.json の keyVisual.colorDirection を優先適用**
- **トーンは strategy.json の messageSystem.toneOfVoice を反映**

### 4-D: コンポーネントライブラリ（class名参照）

| 要素 | class名 | 用途 |
|------|---------|------|
| 記事ラップ | `.article-wrap` | max-width:420px コンテナ |
| リードボックス | `.lead-box` | 共感ボックス |
| 専門家引用 | `.doc-quote` | 権威付け引用ブロック |
| 比較テーブル | `.compare-table` | 商品比較表 |
| ステップカード | `.step-card` | 利用フロー |
| 口コミカード | `.testimonial` | ユーザーレビュー |
| FAQアイテム | `.faq-item` | Q&A |
| CTAセクション | `.cta-section` + `.cta-btn` | CTAブロック |
| フローティングCTA | `.floating-cta` | 固定フッターCTA |
| ソーシャルプルーフ | `.social-proof` | 数字実績バッジ |

### 4-E: 画像生成（Gemini 3 Pro Image）

**FV画像6枚 + 本文画像（各LP 5枚）を Gemini 3 Pro Image で生成。**

```python
import subprocess, os, time
from google import genai
from google.genai import types

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass
for _v in ['GEMINI_API_KEY','GEMINI_API_KEY_2','GEMINI_API_KEY_3']:
    _load_env(_v)

API_KEYS = [os.environ.get(k,'').strip() for k in ['GEMINI_API_KEY','GEMINI_API_KEY_2','GEMINI_API_KEY_3']]
API_KEYS = [k for k in API_KEYS if k]
clients = [genai.Client(api_key=k) for k in API_KEYS]

slug = '{slug}'
out_dir = f'記事LP-park/output/{slug}/images'
os.makedirs(out_dir, exist_ok=True)

images = [
    # FV画像（各LP × 3パターン）
    ('lp1_fv_a.png', '{英語プロンプト — FVパターンA}', '16:9'),
    ('lp1_fv_b.png', '{英語プロンプト — FVパターンB}', '16:9'),
    ('lp1_fv_c.png', '{英語プロンプト — FVパターンC}', '1:1'),
    # 本文画像（各LP 5枚）
    ('lp1_hero.png', '{ヒーロー画像}', '16:9'),
    ('lp1_problem.png', '{問題提起画像}', '16:9'),
    ('lp1_shift.png', '{パラダイムシフト画像}', '16:9'),
    ('lp1_product.png', '{商品画像}', '16:9'),
    ('lp1_cta.png', '{CTA周辺画像}', '16:9'),
    # LP2 も同様...
]

ok = ng = 0
for i, (fn, prompt, aspect) in enumerate(images):
    fp = os.path.join(out_dir, fn)
    if os.path.exists(fp):
        ok += 1; continue
    for attempt in range(3):
        c = clients[(i + attempt) % len(clients)]
        try:
            resp = c.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(aspect_ratio=aspect)))
            img = next((p.inline_data.data for p in resp.parts if p.inline_data), None)
            if not img or len(img) < 10240:
                if attempt < 2: time.sleep(3); continue
                ng += 1; break
            with open(fp, 'wb') as f: f.write(img)
            ok += 1; break
        except Exception as e:
            if attempt < 2: time.sleep(5)
            else: ng += 1
    time.sleep(2)

print(f'\n=== 画像生成結果: {ok}/{len(images)} OK, {ng}/{len(images)} NG ===')
```

**画像プロンプトルール:**
- 全プロンプト英語。`Japanese person` / `Japanese daily life` を含める
- パターンA（痛み直撃）: 暗めトーン、不安の表情
- パターンB（新常識）: 明るめトーン、希望の表情
- パターンC（ストーリー）: ナチュラルトーン、日常シーン
- strategy.json の keyVisual.mood / colorDirection を反映

### 4-F: ファイル保存

```
記事LP-park/output/{PRODUCT_SLUG}/
├── article-lp-{slug}-01.html    ← 記事LP 1
├── article-lp-{slug}-02.html    ← 記事LP 2
├── specs/
│   ├── lp_01_spec.json          ← LP1設計書
│   └── lp_02_spec.json          ← LP2設計書
├── images/                       ← 生成画像
│   ├── lp1_fv_a.png ... lp1_cta.png
│   └── lp2_fv_a.png ... lp2_cta.png
├── report.html                   ← レポート原本
└── report.pdf                    ← PDFレポート
```

---

## Phase 5: 3層品質検証

### Layer 1: コピー品質検証（ポメ太さん哲学チェック）

**Agent設定**: `subagent_type: "general-purpose"`, `name: "品質チェッカーくん"`

各セクションのテキストを以下の基準で評価:

| チェック項目 | 基準 | 不合格条件 |
|-----------|------|----------|
| シーン喚起力 | 具体的シーンが浮かぶか | 抽象的な説明文のみ |
| 「頑張りたくない」一貫性 | 「楽さ」を伝えているか | 「努力」「頑張る」等の表現 |
| 情報欠落設計 | 先に結論→後で補完か | 全てを一度に説明 |
| コンセプト一貫性 | strategy.json のコンセプトが貫かれているか | コンセプトと無関係な訴求 |
| 好奇心ギャップ | 「先が気になる」仕掛け | セクション末尾で完結 |
| NG表現 | messageSystem.ngExpressions に該当しないか | NG表現の使用 |

### Layer 2: HTML品質 + 法規チェック

| チェック | 基準 |
|---------|------|
| レスポンシブ | モバイル表示崩れなし |
| 画像パス | 全画像が正しくリンク |
| FVタブ切替 | 3パターンが正常動作 |
| CTA導線 | 全CTAのリンクが有効 |
| 薬機法 | カテゴリ別NG表現チェック |
| 景表法 | 不当表示チェック |

### Layer 3: ベクトル事後検証

記事LP本文テキストをベクトル化し、コンセプトとの乖離をチェック:

```python
for lp_path in lp_html_paths:
    # HTMLからテキスト抽出
    with open(lp_path) as f:
        html = f.read()
    # テキスト部分を抽出（タグ除去）
    import re
    text = re.sub('<[^>]+>', '', html)
    text = ' '.join(text.split()[:500])  # 先頭500語

    actual_vec = embed(text)
    sim = cosine_sim(actual_vec, concept_vec)
    print(f"  {os.path.basename(lp_path)} 本文×コンセプト: sim={sim:.3f} {'✅' if sim >= 0.40 else '⚠️乖離'}")
```

---

## Phase 6: PDFマーケティングインテリジェンスレポート

### 6-A: レポートデータ収集

Phase 0〜5 の全データを集約:

```python
report_data = {
    'product': strategy['productIntel'],
    'n1': strategy['primaryN1'],
    'concept': strategy['concept'],
    'formatStrategy': strategy['formatStrategy']['articleLP'],
    'hookVectors': strategy['hookVectors'],
    'lpSpecs': lpSpecs,
    'gateResults': gate_results,
    'qualityCheck': quality_results,
    'dproResearch': dpro_research_summary,
    'generatedAt': datetime.now().isoformat(),
    'lpCount': len(lpSpecs)
}
```

### 6-B: HTML レポート生成

`記事LP-park/output/{slug}/report.html` を生成。

レポート構成:

```html
<!-- セクション1: 表紙 -->
<div class="cover">
  <h1>{product_name}</h1>
  <p class="concept">「{concept}」</p>
  <p class="date">記事LP Park v3.0 — {YYYY-MM-DD}</p>
  <p class="count">{N}本の記事LP × {N}個の仮説 × 各FV3パターン</p>
</div>

<!-- セクション2: 戦略サマリー -->
<div class="strategy-summary">
  <h2>戦略サマリー</h2>
  <!-- N1ペルソナ -->
  <!-- コンセプト / Only1ポジション -->
  <!-- 記事LPの役割（formatStrategy.articleLP） -->
  <!-- フック角度一覧 -->
  <!-- 仮想敵パラダイムシフト設計 -->
</div>

<!-- セクション3: 記事LPポートフォリオ -->
<div class="portfolio">
  <h2>記事LPポートフォリオ</h2>
  <!-- 各記事LP: FV3パターン プレビュー + 仮説カード -->
  <!--
    仮説カード:
    - 仮説: {hypothesis}
    - 仮想敵: {virtualEnemy.falseBelief}
    - フック角度: {hookAngle}
    - パラダイムシフト: {旧→新}
    - FVパターン: A/B/Cのプレビュー
    - 狙い: {testHypothesis}
  -->
</div>

<!-- セクション4: ベクトル検証レポート -->
<div class="vector-report">
  <h2>ベクトル検証レポート</h2>
  <!-- コンセプト一貫性スコア -->
  <!-- 競合差別化スコア -->
  <!-- 記事LP間多様性 -->
  <!-- N1需要刺さり度 -->
</div>

<!-- セクション5: DProリサーチ分析 -->
<div class="dpro-research">
  <h2>DProリサーチ分析</h2>
  <!-- KV哲学フィルター結果 -->
  <!-- 勝ちDNAサマリー -->
  <!-- 構造トレンド -->
</div>

<!-- セクション6: A/Bテスト戦略 -->
<div class="test-strategy">
  <h2>A/Bテスト戦略</h2>
  <!--
    Round 1: FVパターン ABC テスト
      仮説: どのFVが最強か
      指標: CTR / スクロール率
      判定: 業界平均×1.5

    Round 2: 記事LP仮説テスト
      仮説: どの仮想敵/フック角度が効くか
      指標: CVR
      判定: 直近平均×1.2

    Round 3: 構成バリエーション
      指標: CPA
      判定: 直近平均×0.8
  -->
</div>

<!-- セクション7: Next Action -->
<div class="next-action">
  <h2>Next Action</h2>
  <!--
    ベクトルマップ上の空白地帯
    次回攻めるべき仮想敵/フック角度
    勝ちパターン仮説
  -->
</div>
```

HTMLはダークテーマ。プリント時はライトテーマに自動切替（`@media print`）。

### 6-C: PDF 変換

```python
try:
    from weasyprint import HTML
    HTML(filename=f'{out_dir}/report.html').write_pdf(f'{out_dir}/report.pdf')
    print(f"✅ PDF生成完了: {out_dir}/report.pdf")
except ImportError:
    print("⚠️ weasyprint未インストール。HTMLレポートのみ。")
    print(f"  report.html をブラウザで開いて Cmd+P でPDF化")
```

### 6-D: 完了プレゼン

```
━━━━━ 記事LP PARK v3.0 完了 ━━━━━
商品: {product_name}
コンセプト: 「{concept}」

生成結果:
  記事LP: {N}本 × 各FV3パターン
  画像: {ok}/{total} 枚 生成成功

ベクトル検証:
  コンセプト一貫性: 平均 sim={avg_concept_sim:.3f}
  競合差別化: 平均 sim={avg_comp_sim:.3f}
  記事LP間多様性: {diversity_status}

品質検証:
  コピー品質: {copy_status}
  法規チェック: {legal_status}

納品物:
  📄 article-lp-{slug}-01.html
  📄 article-lp-{slug}-02.html
  📁 specs/ — 設計書JSON
  📁 images/ — 生成画像
  📄 report.html — インタラクティブレポート
  📄 report.pdf — マーケティングインテリジェンスレポート

テスト戦略:
  Round 1: FVパターン ABC テスト
  Round 2: 仮説テスト（仮想敵/フック角度）

Next Action:
  {next_action_summary}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 注意事項

- **前提**: `/research-park` + `/concept-park` 完了済み。strategy.json に concept / formatStrategy.articleLP / hookVectors が入っていること
- **Phase 0**: strategy.json 必須読み込み。なければ案内して終了
- **Phase 1**: メインが直列実行（DPro MCP依存）。KV哲学フィルターで「構造が美しい × 売れてる」だけ学ぶ
- **Phase 2**: Claude が strategy.json を読み解いて lpSpec(JSON) を生成。N1/コンセプトは上流で確定済み — ここでは「翻訳」に専念
- **Phase 3**: ベクトル品質ゲートは**生成前**。FVコピーの一貫性/差別化/多様性を数値検証
- **Phase 4**: Gemini 3 Pro Image。GEMINI_API_KEY 3キーローテーション
- **Phase 5**: コピー + HTML + 法規 + ベクトルの多層検証
- **Phase 6**: HTMLレポート + PDF。「人が次に活かせる情報」を全て含む
- **3つの魂**: 全Phaseを通じて、パラダイムシフトの教科書 × キラーFVコピー × 別の仮説 を常に意識
- **ベクトル活用3箇所**: Phase 2（hookVector選択）→ Phase 3（品質ゲート）→ Phase 5-Layer3（事後検証）
- **ポメ太さんDIVE哲学4原則**: Phase 2（FV設計）+ Phase 4（本文生成）+ Phase 5（品質チェック）で全面適用
  - 原則6: 読者の内側から引き出す
  - 原則7: シーンを描く
  - 原則8: 意図的に情報を欠落させる
  - 原則9: Before→Afterの飛躍を楽にする

---

## 環境設定（全Phase共通）

- `WORK_DIR` = カレントディレクトリ
- `GEMINI_KEYS` = 3キーローテーション（GEMINI_API_KEY / _2 / _3）
- 出力先は全て `WORK_DIR` からの相対パスを使用
- サブエージェントは MCP / WebSearch / WebFetch にアクセス不可 → 外部データ取得はメイン、分析のみサブ

---

## 共有アセットフォルダ TIPS

記事LP生成時、以下のフォルダに商材固有の素材がある場合はそれを優先利用する:

```
.claude/knowledge/{slug}-assets/INDEX.md    ← 素材一覧（まず読む）
記事LP-park/assets/{slug}/                   ← LP固有素材
research-park/output/{slug}/                 ← リサーチ出力
```

- **INDEX.md があれば必ず読む** — 利用可能な画像・ロゴ・素材を把握してから生成に入る
- 素材フォルダにFV画像やロゴがある場合、Gemini生成ではなく実素材をbase64埋め込みで使用
- 既存LPの lp-structure.json がある場合、ブランドカラーやコピーのトーンを参照
- 実写素材 > AI生成画像。信頼性のために実素材を最大限活用する

---

## FV法則 — BtoB SaaS × FB広告 LP（2026-02-25 確立）

DPro BtoB(genre:215) TOP20 + Sansan + SATORI + Salesforce + リードダイナミクス + ビューティーパレット + SmartNews Ads から抽出した、FVの勝ちパターン法則。

Phase 2 Step 4 の FV3パターン設計時に適用する。

→ `.claude/knowledge/creative-reference.md` の以下セクションを参照:
- **FV 7要素フレームワーク**（法則1）
- **FVコピー3パターン**（法則2: 痛み直撃/成果証明/新常識）
- **FB広告→LP 設計原則**（法則3）
- **信頼性の階層**（法則4: S/A/B/C レベル）
- **FV素材活用ルール**（法則5: バッジPNG/マスコット/テキストなし生成等）

### 法則6: HTML構造テンプレート

```html
<!-- FV Section -->
<section class="fv-section">
  <!-- Level C: ロゴ + PRバッジ -->
  <div class="fv-header">
    <img src="images/fv_logo.svg" alt="{商品名}">
    <span class="fv-badge">PR</span>
  </div>

  <!-- FVタブ + パネル -->
  <div class="fv-selector">...</div>
  <div class="fv-swipe-container" id="fvSwipe">
    <div class="fv-panel active">
      <div class="fv-img-wrap">
        <img src="..." class="fv-hero-img">
        <!-- マスコット/AIキャラ（あれば） -->
        <img src="images/mascot_robot.png" alt="" class="fv-mascot">
        <div class="fv-overlay">
          <!-- 要素3: 信頼バッジPNG -->
          <div class="fv-badges">
            <img src="images/badge_xxx.png" alt="{実績}">
            <img src="images/badge_yyy.png" alt="{実績}">
          </div>
          <!-- 要素1: メインコピー（数字は big-num で強調） -->
          <div class="fv-main-copy">{4行以内、数字に big-num クラス}</div>
          <!-- 要素2: サブコピー -->
          <div class="fv-sub-copy">{差別化ポイント1行}</div>
          <!-- 要素5: CTA -->
          <a href="#cta-final" class="fv-cta-btn">{低ハードルCTA}</a>
          <div class="fv-cta-sub">{価格・条件サマリ}</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Level B: 実績数字バー -->
<div class="social-proof-bar">
  <div class="sp-item">{指標1}</div>
  <div class="sp-item">{指標2}</div>
  <div class="sp-item">{指標3}</div>
</div>

<!-- Level A: 導入企業ロゴ -->
<div class="client-logos">
  <span class="client-logos-label">導入企業</span>
  <img src="..." alt="企業名">
</div>
```

### データソース

- **DPro**: genre_id=215（ビジネスサービスBtoB）、cost_difference-desc で取得
- **競合LP**: リードダイナミクス、GeAIne、Sansan、SATORI、Salesforce
- **分析観点**: FV要素の出現頻度 × 広告費TOP10相関
