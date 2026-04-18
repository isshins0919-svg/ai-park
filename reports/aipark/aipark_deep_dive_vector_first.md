# Vector-First 学習回路 — 技術深掘りレポート

> 出典: `vector_intelligence.py` v1.0 + CMO AIパク定義 Vector-First Learning 憲法
> 重要度: **最高**（VOYAGE ccdd-strategy.md Phase 1-4 の完成実装）

---

## 1. 思想の核 — 憲法6条

パクのCMO AIパク定義から抜粋した **Vector-First Learning 憲法**:

1. **仮説は vector-addressable でなければならない**
   - hypothesis / pattern / candidate / retrieved chunk / refine result / manifest / deploy result を `hypothesis_id`・`pattern_id`・vector参照で追跡
   - テキストだけの仮説は補助メモであり主記録ではない

2. **全ての採点は vector-first で設計する**
   - 主回路: `n1_fit / internal_harmony / winner_proximity / loser_collision / retrieval_support / novelty_band / refine_delta`
   - readability / quality gate / 自然言語コメントは補助。主審にしない

3. **self-refine は文章改善ではなく座標移動**
   - before / after の V/C/X, N1, winner/loser 近傍差分を残す
   - 「何を直したか」より「勝ち空間に近づいたか」で採点

4. **reflection は感想ではなく空間更新**
   - WIN は「どの空間が支配的だったか」、LOSE は「どの空間でズレたか」を更新
   - judge が外れた場合は閾値・重み・空間定義も更新対象

5. **exploit / repair / explore は同じ物差しで採点しない**
   - exploit: 勝ち近傍と loser 回避を最重視
   - repair: loser 脱出・harmony 回復・refine delta を重視
   - explore: novelty band と未探索 cluster 接近を重視

6. **CMOは長文プロンプト追加より vector trace の太化を優先する**
   - 新しい説明を増やす前に、`retrieved_chunk_ids`・vector score・before/after・judge根拠の接続を増やす
   - 可読性より計算可能性を優先

---

## 2. V/C/X 3空間の定義

パクの `vector_intelligence.py` は広告クリエイティブを3つの空間に分解する。

### V空間（Visual）
ビジュアル要素のみ（テキストは無視）:
- 構図パターン（Z型/N型/対角/中央集中）
- 色彩設計（メインカラー・アクセント・コントラスト）
- レイアウト構造（情報配置・余白）
- テロップのデザイン処理（袋文字・影・フォント）
- 視線誘導・情報階層

### C空間（Copy）
テキスト要素のみ（ビジュアルは無視）:
- メインコピーのフック力・新規性・緊急性
- サブコピーの説得構造
- CTA文言と強度
- バッジ/チップスの信頼構築要素
- 論理フロー（注目→共感→行動）
- 数字の使い方・感情トリガー

### X空間（コンセプト）
伝えようとしている本質（見た目・文言の具体は無視）:
- 根底の課題設定
- 提案する解決の新規性
- ターゲット信念の before→after
- 感情トリガー（焦燥/共感/発見/安心/緊急/解放）
- 「何それ？」の強度（報酬予測誤差）

---

## 3. 3空間Embeddingの手順

```
入力: 広告1本（画像PNG + コンセプトテキスト + N1情報）
  ↓
[V-space]
  Gemini Vision（gemini-2.5-flash）で画像を V_SPACE_PROMPT で記述
  ↓ 日本語3-5行のビジュアル記述
  ↓
  Gemini Embedding 2（gemini-embedding-2-preview, 3072次元, SEMANTIC_SIMILARITY）
  ↓ v_vector（3072次元配列）
  ↓
[C-space]
  Gemini Vision で画像を C_SPACE_PROMPT で記述
  ↓ 日本語3-5行のコピー記述
  ↓
  Gemini Embedding 2 → c_vector
  ↓
[X-space]
  コンセプトテキスト（concept名 + HOOK + 新認知1-4ナレーション）
  ↓ 直接 Embedding 2 → x_vector
  ↓
出力: { v_vector, c_vector, x_vector, v_description, c_description, x_description }
```

**ポイント**:
- Visionはflash（軽量・高速）、Embeddingはembedding-2-preview（3072次元・最新）
- Rate limiting: REQUEST_DELAY = 1.5秒（API制限回避）
- テキストは2000文字で切り詰め
- 画像はbase64エンコードしてinline_dataで送信

---

## 4. 7主審スコアの計算

### 4-1. overall_harmony（内部整合性）

1つのCRのV/C/X 3空間が「同じ方向」を向いているか。

```
vc = cosine(v_vector, c_vector)
vx = cosine(v_vector, x_vector)
cx = cosine(c_vector, x_vector)
overall_harmony = mean(vc, vx, cx)
```

- **harmony > 0.70**: 内部整合性高。メッセージ一貫。
- **harmony < 0.70**: 設計やり直し
- v9.0r の勝ちCR 実績: **harmony 0.77-0.83**

### 4-2. n1_stickiness（N1刺さり度）

CRのX空間ベクトルとN1テキストベクトルの類似度。

```
n1_text = f"N1: {persona_summary}。{whyThisN1}。{newCognitionStrategy}"
n1_vector = embed_text(n1_text)
n1_stickiness = cosine(x_vector, n1_vector)
```

- **stickiness > 0.45**: 目標達成（パクのKPI）
- コンセプト角度がN1のペインに近い = 刺さる

### 4-3. winner_proximity（勝ち空間近傍性）

勝ちDNAクラスタの重心からの距離。

```
winner_centroid = mean([w.x_vector for w in winning_dna])
winner_proximity = cosine(x_vector, winner_centroid)
```

- 高 → 勝ちゾーンに近い → 探索価値より活用価値
- 低 → 未探索領域（novelty_band 候補）

### 4-4. loser_collision（負け空間衝突）

負けDNAクラスタとの距離。

```
loser_distances = [cosine(x_vector, l.x_vector) for l in losing_dna]
loser_collision = max(loser_distances)  # 最も近い負けとの類似度
```

- 高 → 負けパターンと酷似。避けるべき
- 低 → 安全

### 4-5. retrieval_support（RAG根拠接続度）

そのCRの仮説が、RAGからretrieveされたどのchunkに裏付けられているか。

```
supporting_chunks = rag.search(hypothesis_text, top_k=5)
retrieval_support = mean([chunk.score for chunk in supporting_chunks])
```

- 高 → データ駆動の仮説
- 低 → 「なんとなく」仮説（禁止対象）

### 4-6. novelty_band（新規性帯）

既存DNAクラスタからの「ちょうど良い距離」。

```
all_distances = [cosine(x_vector, dna.x_vector) for dna in all_dnas]
avg_distance = mean(all_distances)
novelty_band = 1.0 - |avg_distance - 0.5|  # 0.5 付近が最適
```

- **近すぎる** → 焼き直し（novelty低）
- **遠すぎる** → 飛躍しすぎ（explore専用）
- **0.5付近** → 探索と活用のバランスが取れた新規性

### 4-7. refine_delta（座標移動量）

self-refine 前後の移動量。

```
before_vcx = embed_3space(cr_before)
after_vcx = embed_3space(cr_after)
refine_delta = {
  'v_move': 1 - cosine(before.v, after.v),
  'c_move': 1 - cosine(before.c, after.c),
  'x_move': 1 - cosine(before.x, after.x),
  'winner_approach': cosine(after.x, winner_centroid) - cosine(before.x, winner_centroid)
}
```

- `winner_approach > 0` → refineが勝ち空間に近づいた = 成功
- `winner_approach ≤ 0` → refineが無効 or 悪化

---

## 5. 支配的空間（dominant_space）の特定

### 勝ちCR vs 負けCRの空間別差分分析

```python
for loser in losers:
    v_sim = cosine(winner.v, loser.v)
    c_sim = cosine(winner.c, loser.c)
    x_sim = cosine(winner.x, loser.x)

# 空間別の平均距離
avg_v_dist = 1.0 - mean(v_sims)
avg_c_dist = 1.0 - mean(c_sims)
avg_x_dist = 1.0 - mean(x_sims)

dominant_space = argmax(avg_v_dist, avg_c_dist, avg_x_dist)
```

### 解釈ロジック

- **V空間が最大差** → ビジュアル（構図・色・レイアウト）が勝因
  - 次サイクル: 勝ちビジュアルを固定し、C空間でコピー角度を探索
- **C空間が最大差** → コピー構成（フック・CTA・数字使い）が勝因
  - 次サイクル: 勝ちコピー構造を固定し、V空間でビジュアル角度を探索
- **X空間が最大差 & クロスコンセプト** → コンセプト角度がN1により強く共鳴
  - 次サイクル: 勝ちコンセプトを固定し、V/C空間でバリエーション探索

**AIパク実績**: sample-saas-v2 は **C空間（コピー）が支配的** と判明。

---

## 6. Phase A/B/C の構造

### Phase A: 空間分析

```
[Phase A-1] 3空間Embedding化（全広告 × 3空間）
[Phase A-2] 空間別差分分析 — 支配的空間特定
[Phase A-3] N1刺さり度計算（X空間 × N1ベクトル）
[Phase A-4] 内部整合性分析（V×C, V×X, C×X harmony）
```

**出力**: `loop-state.json` に `space_analysis` + `n1_stickiness` + `harmony` を記録

### Phase B: 最適解探索

勝ちゾーン × 未探索領域 → 最適V/C/X座標を探索

```
optimal_v_direction = 勝ちCRのV空間重心
optimal_c_direction = 勝ちCRのC空間重心
optimal_x_direction = N1ベクトル × 勝ちX空間のバランス

next_cr_target = {
  'v_target_similarity': 0.85 ~ 0.95,  # 勝ちに近い
  'c_target_similarity': 0.85 ~ 0.95,  # 勝ちに近い
  'x_novelty_band': 0.45 ~ 0.55,       # 新規性
  'n1_stickiness_min': 0.45
}
```

### Phase C: CR設計指示

optimal-cr-spec.json を出力。バナー生成Agentへのwork-orderに添付。

---

## 7. reflection への接続

### judge_calibration（判定精度校正）

vector_intelligence が事前予測した「勝ちそう度」と実績を後から比較:

```
predicted_win_proba = f(winner_proximity, n1_stickiness, harmony)
actual_result = ops-snapshot の 48h判定 (WIN/LOSE)

judge_accuracy = sum(predicted == actual) / total
```

- judge_accuracy が低い → 閾値を更新（例: harmony 0.70 → 0.75）
- 空間定義自体を見直す（V/C/Xの切り分けが現実と合っていない可能性）

### 弱い judgeの改善

`judgment-accuracy.json` に記録:
```json
{
  "pattern_id": "BH4-v2",
  "predictions": 15,
  "correct": 6,
  "accuracy": 0.40,
  "failing_axis": "loser_collision too high"
}
```

→ 次回 ceo-reflection で「judge_calibration improvements」として改善提案

---

## 8. VOYAGE号への移植マップ

### 8-1. 既存資産との接続

VOYAGE `.claude/knowledge/vector-utils.md` の方向性:
- Gemini Embedding → コサイン類似度 → 品質ゲート
- 対象: hookVector / concept / competitor_message / N1需要

パクとの差:
- VOYAGE: **テキストのみ**ベクトル化
- パク: **画像→Vision記述→Embedding** で V空間も取れる

### 8-2. 移植優先順位

```
Phase 1: embedding_utils.py 移植
         → Gemini Embedding 2 (3072D) の共通関数
         → VOYAGE 既存 vector-utils.md を実装化

Phase 2: knowledge_rag.py 移植
         → VOYAGE knowledge/ 全ファイルをチャンク分割→ベクトル化
         → ChromaDB に永続化
         → CCDD Strategy Phase 1 完全実現

Phase 3: vector_intelligence.py の簡略版
         → C空間のみ（テキストのみ）から開始
         → V空間は Vision API料金とデザイナーレビューのトレードオフ見てから

Phase 4: 7主審スコア化
         → harmony / n1_stickiness を VOYAGE クルー群（gate-*）の採点基準に組み込む
         → 既存の主観評価を vector score で裏打ち

Phase 5: 支配的空間特定
         → VOYAGE 10クライアントで「どの空間が勝因か」分析
         → クライアント別 strategy.json に dominant_space 記録

Phase 6: reflection loop 接続
         → judge_calibration を VOYAGE kiji-cko / movie-kantoku の出力に追加
         → 週次 ceo-reflection-voyage で閾値更新
```

### 8-3. 移植時の判断

| パクの仕様 | VOYAGE移植時の調整 |
|---|---|
| gemini-embedding-2-preview (3072D) | 採用（Gemini API 既使用） |
| gemini-2.5-flash for Vision | 採用 |
| REQUEST_DELAY 1.5s | Gemini 無料枠前提で維持 |
| np.array + cosine_similarity | numpy 導入（既に使ってる可能性高） |
| ~/Documents/AIパク-runtime/ | VOYAGE は repo 内完結。`scripts/vectors/` 等に保存 |
| 広告単位（CR）の Embedding | VOYAGE は SNS/Amazon/記事LP にも展開 |

### 8-4. VOYAGE独自拡張の余地

パクは **広告CR** に特化。VOYAGEは以下への拡張余地あり:

1. **SNS投稿ベクトル化**
   - V=サムネ、C=キャプション、X=コンセプト
   - sns-analytics-crew の採点基準化

2. **Amazon商品ページベクトル化**
   - V=メイン画像、C=タイトル+箇条書き、X=ブランドコンセプト
   - amazon-park v2.0 への統合

3. **記事LP全文ベクトル化**
   - V=FV画像群、C=全セクション見出し+本文、X=記事全体コンセプト
   - kiji-cko の診断精度向上

4. **動画フレーム分解 + ベクトル化**
   - V=3秒ごとのキーフレーム、C=テロップ+ナレーション、X=コンセプト
   - movie-kantoku に統合

---

## 9. CCDD Strategy との完全一致

VOYAGE `knowledge/ccdd-strategy.md` の Phase 1-4:

| CCDD Phase | パクの実装 |
|---|---|
| Phase 1: knowledge/ ベクトル化 | knowledge_rag.py + embedding_utils.py |
| Phase 2: 永続ベクトルDB（ChromaDB） | 部分実装（file-based）→ ChromaDB化はVOYAGE側で |
| Phase 3: リフレクションループ | reflection_trigger + reflection_tracker + ceo-reflection |
| Phase 4: DPro実績×ベクトルDB紐付け | dpro_rag + judgment-accuracy.json + learning-distillate |

**結論**: 文太（AX社）がCCDDで語った設計を、パク陣営が **先に実装済み**。VOYAGEは構想→実装の最短パスとしてパクのコードを参考にすべき。

---

## 10. 最重要テイクアウェイ

1. **CRを作ったら必ずベクトル化する**（Embedding 2, 3072D）
2. **ベクトルは「守護神」ではなく「羅針盤」に昇格する**
   - VOYAGE旧: ダメなCRを止める守護神
   - 新: 勝ち空間へ向かう羅針盤
3. **harmony 0.70 を下回るCRは配信するな**
4. **支配的空間を特定してから次のCRを作る**
5. **judge_calibration を週次で行い、閾値を進化させる**
6. **self-refineは「文章改善」ではなく「座標移動」として記録**
7. **テキストだけでなく画像→Vision記述→Embedding で V空間も取る**

---

*Vector-First 学習回路は、VOYAGE号の CCDD Strategy Phase 1-4 を具現化する最短パス。パクの実装を土台に、10クライアントの実戦データで検証する構造が最強の組み合わせになる。*
