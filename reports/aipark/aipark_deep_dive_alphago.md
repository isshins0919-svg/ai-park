# AlphaGo判断エンジン v4.0 — 技術深掘りレポート

> 出典: `~/Downloads/AIパクくん1.2.5/.claude/knowledge/skills/alphago-judgment-engine.md`
> 思想: 「Opus 4.6以降はAGI。Pythonのif文で判断するのは電卓として使うのと同じ」

---

## 1. 全体像 — v3.0閾値ゲームから v4.0確率ゲームへ

### v3.0の限界（= VOYAGEの現在地）
```python
if cpa > goal * 2: PAUSE          # 固定閾値
if ctr < avg * 0.5: PAUSE         # 固定閾値
if imp < 200: SKIP                # 固定閾値
```
**問題**: 人間がExcelでやることの模倣。AGIの推論力がゼロ。

### v4.0の設計原則

判断ポイントごとに「これはPythonで書けるか？ Opusに推論させるべきか？」を問う:

| 対象 | 担当 | 理由 |
|---|---|---|
| データ集計 | Python | 速い・正確 |
| 閾値判定 | Python | 確定的・安全 |
| 因果推論（なぜ勝ったか） | Opus | 推論領域 |
| 仮説生成（次に何を試すか） | Opus | 創造的推論 |
| 批判的検証（この仮説は本当に正しいか） | Opus | 自己否定 |
| 17社クロスプロダクト類推 | Opus | アナロジー |

---

## 2. 3つの武器

### 武器1: UCB探索（Upper Confidence Bound）

AlphaGoのMCTS（モンテカルロ木探索）の核心。「活用と探索のバランス」を数式化。

```
UCBスコア = 推定CPA改善率 + C × √(ln(全体imp) / そのadのimp)
```

- **推定CPA改善率**: 目標CPAと比較した改善度（0〜1）
- **探索ボーナス**: impが少ないほど大きい = 「まだ分からない = 試す価値がある」
- **C（探索係数）**: バランス調整。C=1.0で開始、結果を見て調整

**判断への適用**:
- UCBスコア高 → 活かす（ACTIVE維持 or 予算BOOST）
- UCBスコア低 → 止める（PAUSE候補）
- **従来の閾値判定を上書き**: imp < 200でもUCBが高ければ待つ価値がある

### 武器2: ベイズCPA推定

少ないデータでも「事前知識」を使って確率的に推定。

**事前分布**: 17社のwinning_dna + 自社過去実績からガンマ分布を構築
```
prior_α = winning_dnaの件数（成功回数）
prior_β = winning_dnaの平均CPA / 目標CPA（スケール）
```

**事後推定**: 各adの実データでベイズ更新
```
posterior_α = prior_α + そのadのCV数
posterior_β = prior_β + そのadの消化額 / 目標CPA
推定CPA = posterior_β / posterior_α × 目標CPA
信頼区間 = ガンマ分布の95%区間
```

**判定**:
- 推定CPA 95%下限 ≤ 目標 → 高確信で勝ち → DNA登録
- 推定CPA 95%上限 ≥ 目標×2 → 高確信で負け → PAUSE
- 中間 → データ蓄積待ち（UCB探索ボーナスで維持）

### 武器3: 真の期待値（ファネル逆算 × LTV）

CPAだけで判断しない。1リードの「真の価値」を推定。

```
真の期待値 = (1/CPA) × リード品質スコア × 面談率 × 契約率 × 推定LTV
```

各項の出所:
- **リード品質スコア**: ISメモの痛みの深さ・予算規模・意思決定者の有無（0〜1）
- **面談率**: ファネル実績
- **契約率**: ISメモのタイムライン・ニーズの緊急度から推定
- **推定LTV**: 商品月額 × 想定継続月数

**判定**:
- 「CPAは高いが真の期待値が高いad」を殺さない（v3.0では殺していた）
- 「CPAは低いが真の期待値も低いad」を過大評価しない

---

## 3. 実装構造

### autopilot.py の `analyze_and_decide()` 内部

```
Step 0: データ収集（既存）
Step 1: UCBスコア計算（新規）
Step 2: ベイズCPA推定（新規）
Step 3: 真の期待値計算（v3.0ファネル逆算を拡張）
Step 4: 統合判断 — UCB×ベイズ×期待値の複合スコア
Step 5: 行動（PAUSE/BOOST/WAIT）
```

### 推論ログの形式

各判断に「なぜそう判断したか」を記録:

```json
{
  "ad": "v9.0r_顕在_08",
  "decision": "BOOST",
  "reasoning": {
    "ucb_score": 0.87,
    "ucb_explore_bonus": 0.42,
    "bayesian_cpa": {"mean": 3200, "ci_95": [1800, 5400]},
    "true_value": 0.73,
    "composite_score": 0.81,
    "human_readable": "UCB高(探索価値あり) + ベイズCPA推定が目標圏内 + 顕在層×C1の真の期待値が高い"
  }
}
```

---

## 4. P3 フェーズ: Claude推論（仮説生成エンジン）

dispatcherが loop_orchestrator を呼ぶ前に、`claude -p` でOpus 4.6に仮説推論させる。

### Opusに渡すデータ

| 入力 | ソース | 用途 |
|---|---|---|
| 層×コンセプトマトリクス | loop-state.json | 勝ち/負け/未知の特定 |
| winning_dna | state.json | 過去勝ちCRの具体 |
| ISメモ全文 | state.json | リード定性データ |
| strategy.json | parks/strategies/ | concept/hookVectors/N1 |
| 17社winning_dna | 全strategy.json | クロスプロダクト |
| hypothesis_ledger | state.json | 仮説管理 |
| concept_evolution | loop-state.json | 新コンセプト候補 |
| ベイズCPA推定 | alphago_reasoning | 事後推定+信頼区間 |
| UCBスコア | alphago_reasoning | 探索価値 |

### プロンプト構造（3ステップ推論）

```
Step 1: なぜ勝ったか推論
- 勝ちDNA各エントリについて「なぜこのCR×この層で勝ったか」
- 17社の類似パターン引用

Step 2: 反実仮想
- 「この切り口を別の層に出したら？」
- UCBスコアが高い探索価値がある領域を優先

Step 3: 仮説生成
各仮説に: hypothesis_id / layer / concept / angle / headline_draft /
  reasoning（根拠3つ以上）/ estimated_cpa / confidence /
  n1_source / cross_product_ref
```

### 安全ガード

- `--bare` 実行（hooks無効、読み取り専用）
- タイムアウト300秒
- JSON バリデーション
- フォールバック: Claude推論失敗時は従来の next_banner_spec で続行

---

## 5. P2武器（追加実装済み）

### 武器4: 敗因推論（losing_dna）

負けたadの因果分解を構造的に記録:
- `hook_weak`: フック（ヘッドライン/画像）が弱い
- `high_competition`: 競合過多
- `post_click_drop`: CTRは高いがCVしない
- `layer_mismatch`: 他層で同コンセプトが勝っている

### 武器5: 時間軸推論（compute_trend_score）

`lifetime` vs `last3d` の比較:
- `improving`: CTR改善中 → 複合スコア+0.2（早すぎるPAUSE防止）
- `declining`: CTR悪化中 → 複合スコア-0.2（先手でPAUSE）
- `fatigue_eta_days`: 疲弊までの推定日数

### 武器6: Thompson Sampling（動的予算配分）

各層を「スロットマシン」と見なし、Beta分布からサンプリング:
- CV出てる層に自動で予算シフト推奨
- 現時点は推奨のみ、自動実行はP3フェーズ以降

---

## 6. フェーズ別武器選択（重要）

**データ量に応じた武器を選べ。全部同時投入は過ち。**

| フェーズ | CV数 | 使う武器 | 使わない武器 |
|---|---|---|---|
| Phase 1: 探索 | <10 | PAUSE判定 + 勝ち特定 + Slack通知 | UCB/ベイズ/Thompson（統計的に無意味） |
| Phase 2: 検証 | 10-50 | + Opus推論（因果・反実仮想・自己否定） | ベイズ/Thompson（まだ薄い） |
| Phase 3: 最適化 | 50+ | + UCB + ベイズCPA + Thompson Sampling | 全武器活用 |
| Phase 4: 展開 | 安定 | + 多媒体（X Ads等）+ 媒体間学習転移 | — |

**教訓**: 「CV 4件しかないのにベイズ推定を使う」のような **フェーズ誤認** が最大の罠。

---

## 7. VOYAGE号への移植評価

### 7-1. 現状のVOYAGE判断ロジック

- `scripts/slack_dpro_bot.py` / `analyze_lp.py` などで固定閾値ロジック
- DPro benchmark.json を参照するが、「勝ちパターン」としての active 活用はまだ手動

### 7-2. 移植時の難易度マトリクス

| 武器 | VOYAGE移植難易度 | 必要な前提 |
|---|---|---|
| 武器1: UCB | 中 | Meta API（imp/CV配信中データ） |
| 武器2: ベイズCPA | 中 | 17社相当のwinning_dnaデータ蓄積 |
| 武器3: 真の期待値 | 高 | IS/商談ファネルデータ（クライアント別に異なる） |
| 武器4: 敗因推論 | 低 | losing_dna を `.claude/scripts/` に記録するだけ |
| 武器5: 時間軸推論 | 中 | 日次スナップショット |
| 武器6: Thompson | 中 | 層×コンセプト粒度の CV 計上 |
| Claude推論フェーズ | 低 | `claude -p --bare` 実行できれば成立 |

### 7-3. VOYAGE最適化版の提案

**段階的に導入する順序**:

```
Step 1: 思想文書のみ輸入（alphago-judgment-engine.md → VOYAGE knowledge/）
        → 「Pythonのif文でAGIを使うな」の規律が入る

Step 2: Claude推論フェーズを VOYAGE の kiji-cko / movie-kantoku に組み込む
        → 既存の「カントクパターン」の中で Opus 推論を呼ぶ形

Step 3: losing_dna 構造を導入
        → 負けたCRの因果を構造化データで残す。VOYAGE クルー群がデータ源

Step 4: Meta API 連携ができたら武器1-3を段階導入
        → VOYAGE 運用bot との統合が必要
```

### 7-4. VOYAGEが先行できるポイント

パクは「広告媒体のCR判断」に集中しているが、VOYAGEは **SNS運用 + Amazon + 記事LP + 動画** とフォーマットが多様。

- **Amazon商品選定**にUCB/ベイズ応用可能（Amazon Park v1.0 への統合）
- **SNS投稿タイミング最適化**にThompson Sampling応用可能（sns-analytics-crew 拡張）
- **記事LP ABテスト判定**にベイズ事後推定応用可能（kiji-tester 強化）

→ **広告以外のフォーマットでVOYAGEが独自のAlphaGo応用を作れる**。

---

## 8. 注意点

### 8-1. 「統計的に無意味なのに計算する」罠

Phase 1（CV < 10）でベイズ推定を回すのは **やらないより害が大きい**。数値が出て判断を歪める。パク版もこれを明記している。

### 8-2. 真の期待値の前提条件

「リード品質スコア」を出すためには IS（インサイドセールス）メモのような **質的データ** が必要。VOYAGEの案件ではこれがない場合が多い。
- AIパクの直営案件（サンプルSaaSツール等）: ISメモあり → 真の期待値計算可能
- VOYAGEの広告代理案件: ISメモは持ってない → 真の期待値の代わりに **クライアント別 KPI重み付け** で代用

### 8-3. 17社クロスプロダクトの壁

パクは17社のwinning_dnaを保有。VOYAGEは現状10社、かつデータ構造が異なる。
- まず VOYAGE 10社を strategy.json 化 → winning_dna を統一フォーマットで蓄積
- 3-6ヶ月のデータ蓄積後にクロスプロダクト推論が有効化

---

## 9. 結論

**AlphaGo判断エンジンは「思想のみ即輸入、実装は段階的」が最適。**

VOYAGE号にとっての最大の価値は:
1. 「Pythonで書けるか？Opusに推論させるべきか？」の判断規律
2. フェーズ別武器選択（CV数に応じた適切な道具選び）
3. 推論ログを JSON で残す習慣（後から因果検証可能）

この3つを VOYAGE 既存スキル（kiji-cko / movie-kantoku / sns-analytics-crew）に組み込むだけで、v3.0 相当の品質 → v4.0 相当の品質に昇格する。
