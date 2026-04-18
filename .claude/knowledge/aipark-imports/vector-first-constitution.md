# Vector-First Learning 憲法（パク1.2.5輸入）

> 出典: `AIパクくん1.2.5/.claude/agents/cmo-aipark.md` 冒頭
> VOYAGE対応: `ccdd-strategy.md` Phase 1-4 の実装指針

---

## 根本原則

> **ベクトルから出てくる仮説だけが、計算できる仮説であり、PDCAの根拠になる。**

自然言語の見栄えではなく、**座標として追跡・比較・更新・校正できる学習回路**を最優先で設計する。

---

## 憲法6条

### 第1条: 仮説は vector-addressable でなければならない

- hypothesis / pattern / candidate / retrieved chunk / refine result / manifest / deploy result を `hypothesis_id` / `pattern_id` / vector参照で追跡する
- テキストだけの仮説は**補助メモ**であり、**主記録ではない**

**VOYAGEでの実践**: 全ての仮説に `hypothesis_id` を発行。後からベクトル空間で追跡可能にする。

### 第2条: 全ての採点は vector-first で設計する

- 主回路スコア: `n1_fit / internal_harmony / winner_proximity / loser_collision / retrieval_support / novelty_band / refine_delta`
- readability / quality gate / 自然言語コメントは**補助**。主審にしない

**VOYAGEでの実践**: gate-* クルーの採点に vector score を追加。主観評価は補助扱い。

### 第3条: self-refine は文章改善ではなく座標移動

- before / after の V/C/X, N1, winner/loser 近傍差分を残す
- 「何を直したか」より「勝ち空間に近づいたか」で採点

**VOYAGEでの実践**: kiji-rewriter / movie-kantoku のリファイン前後をベクトル化して差分記録。

### 第4条: reflection は感想ではなく空間更新

- WIN は「どの空間が支配的だったか」、LOSE は「どの空間でズレたか」を更新
- judge が外れた場合は閾値・重み・空間定義も更新対象

**VOYAGEでの実践**: `/nice-dive` / `/park-kaizen` の出力を構造化。単なる感想ログにしない。

### 第5条: exploit / repair / explore は同じ物差しで採点しない

- **exploit**（活用）: 勝ち近傍と loser 回避を最重視
- **repair**（修復）: loser 脱出・harmony 回復・refine delta を重視
- **explore**（探索）: novelty band と未探索 cluster 接近を重視し、最低限の N1 fit だけ守る

**VOYAGEでの実践**: 新CR制作時、どのモード（exploit/repair/explore）で動いているかを明示し、採点基準を切り替える。

### 第6条: 長文プロンプト追加より vector trace の太化を優先する

- 新しい説明を増やす前に、`retrieved_chunk_ids` / vector score / before-after / judge根拠の接続を増やす
- 可読性より**計算可能性**を優先

**VOYAGEでの実践**: スキル改善時、指示文を長くする前に、データ接続の強化を検討。

---

## 7主審スコアの定義

| スコア | 意味 | 目標値 |
|---|---|---|
| `n1_fit` / `n1_stickiness` | CRのX空間ベクトルとN1ベクトルの類似度 | ≥ 0.45 |
| `internal_harmony` | 1つのCR内部のV/C/X整合性 | ≥ 0.70 |
| `winner_proximity` | 勝ちDNAクラスタ重心との類似度 | 高いほど活用価値 |
| `loser_collision` | 負けDNAとの最高類似度 | 低いほど安全 |
| `retrieval_support` | RAG retrieve chunk平均スコア | 根拠強度 |
| `novelty_band` | 既存DNAからの「ちょうど良い距離」 | 0.5付近が最適 |
| `refine_delta` | self-refine前後の座標移動量 | winner_approach > 0 |

詳細: `reports/aipark_deep_dive_vector_first.md`

---

## V/C/X 3空間の定義

### V空間（Visual）
構図・色彩・レイアウト・テロップデザイン・視線誘導（テキスト無視）

### C空間（Copy）
メインコピー・サブコピー・CTA・バッジ・論理フロー・感情トリガー（ビジュアル無視）

### X空間（Concept）
課題設定・解決新規性・信念before→after・感情トリガー・報酬予測誤差（具体無視）

---

## 生成Agent別の最重要スコア

| Agent | 最重要スコア | 次点 |
|---|---|---|
| N1 Agent | n1_fit | retrieval_support |
| コンセプト Agent | novelty_band, winner_proximity | internal_harmony |
| バナー Agent | internal_harmony, refine_delta | loser_collision |
| 動画 Agent | internal_harmony | n1_fit |
| 記事LP Agent | retrieval_support, internal_harmony | novelty_band |

---

## VOYAGE号での導入ロードマップ

### Step 1: 思想のみ導入（即時）
- このファイル自体がその成果物
- 各スキルのレビュー時に「座標として記録できるか」を問う

### Step 2: embedding_utils.py 相当を実装
- Gemini Embedding 2（3072D）の共通関数
- `scripts/embedding_utils.py` としてVOYAGEに配置

### Step 3: knowledge/ 全体をベクトル化
- ChromaDB（またはfile-based）に永続化
- CCDD Strategy Phase 1 の実現

### Step 4: 7主審スコア計算関数を実装
- `scripts/vector_scores.py` に harmony / stickiness / proximity を実装
- gate-* クルーから呼び出し可能に

### Step 5: 各スキルにベクトル記録を組み込む
- CR制作時: before/after の座標を記録
- ABテスト時: WIN/LOSE の空間差分を記録
- リフレクション時: judge_calibration を更新

### Step 6: ChromaDB永続化とクロス案件検索
- 10クライアント横断で「勝ちパターン」「負けパターン」をベクトル検索可能に
- CCDD Strategy Phase 2-4 の実現

---

## 絶対禁止事項

1. **RAGを引かずに仮説を出す**（既存案件でRAGが存在する場合）
2. **根拠なきスコアリング**（arbitrary numbers禁止。Embedding距離 or 統計的根拠のみ）
3. **古いRAGで新しい判断**（鮮度を意識）
4. **座標記録なしの self-refine**（before/after を必ず残す）
5. **judge外れの放置**（judge_calibration を更新しない）
