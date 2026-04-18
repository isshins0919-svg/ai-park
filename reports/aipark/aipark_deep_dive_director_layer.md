# Director層アーキテクチャ — 技術深掘りレポート

> 出典: director-banner-aipark / cr-self-refiner-aipark / cmo-aipark / agent-contracts.json
> VOYAGE対応: kiji-cko.md のカントクパターン（既に先行実装あり）

---

## 1. 組織構造の全体像

```
[パク（オーナー）]
    │
    ▼
[CEO AIパク] — 価値観・方針ガード / Lv.4リフレクション
    │ 方針を渡す（手順は渡さない）
    ▼
[CMO AIパク] — マーケティング実行統括
    │ ルーティング判断 → Gate-L3 → 業務後リフレクション
    │
    ├─ Director: Banner ─────────▶ banner-aipark (engine)
    ├─ Director: Video ──────────▶ shortad-aipark (engine)
    ├─ Director: Article LP 01 ──▶ architect + writer + visualizer (3直列)
    └─ Director: Article LP AB ──▶ diagnostician + rewriter (2直列)
    
    共通Agent（CMO直轄、Director非経由）:
    ├─ RAG AIパク        — データ番人
    ├─ 商品リサーチ AIパク — 商品LP 14要素分解
    ├─ N1 AIパク          — ターゲット分析
    ├─ コンセプト AIパク   — Only1コンセプト
    ├─ 入稿 AIパク        — Meta広告入稿
    ├─ 運用 AIパク        — CPA/ROAS最適化
    └─ RAGパク2号         — 記事LP Intelligence
```

---

## 2. 4層階層の役割定義

### Layer 1: CEO（方針ガード）
- CLAUDE.md に書かれた **価値観・原則** の守護者
- **実務禁止**: リサーチ・RAG構築・N1選定・CR生成・入稿・運用は全てCMOに委譲
- 唯一の仕事: 方針を渡してCMOを起動、価値観乖離時に介入
- Lv.4リフレクション: 週1でCMOのAgent定義・スキル・ナレッジを進化

### Layer 2: CMO（オーケストレーター）
- 4部長 + 7共通Agent の起動・順序制御・並列実行
- **CMOも実務禁止**（2026-04-11 パク指示）: 全てをAgentにルーティング
- CMOの4つの責務:
  1. ルーティング判断（どのAgentに振るか）
  2. Gate-L3 品質検証（3つの魂階層チェック）
  3. 業務後リフレクション（毎回必須）
  4. Lv.3リフレクション（成果データ→Agent改善）

### Layer 3: Director（部長 / 品質ゲート）
- 仮説選定 → engine起動 → Gemini検品 → director-review.json生成
- **director-review.json が "index manifest" となる**
- CMO Gate-L3 はこのマニフェストを入力とする
- Lv.2リフレクション: feedback蓄積・director-metrics更新

### Layer 4: Worker/Engine（実制作）
- work-order に従って制作に専念
- 品質検証は通らず、部長に返す
- engine-log.json でスキーマ凍結された記録を残す

---

## 3. 契約ベースのハンドオフ

### agent-contracts.json の構造

各Agent遷移に契約が定義されている。`validate_handoff.py` がチェック。

```json
{
  "contracts": {
    "concept→director-banner": {
      "description": "Conceptが確定した戦略をバナー部長に渡す",
      "output_path": "parks/strategies/{slug}/strategy.json",
      "required_fields": ["primaryN1", "concept", "layers", "brandGuard"],
      "field_rules": {
        "concept": {"type": "object", "required_nested": ["selected", "tagline"]},
        "brandGuard": {"type": "object"}
      },
      "abort_on_failure": true,
      "fallback": null
    }
  }
}
```

### 契約タイプ

| 遷移 | abort_on_failure | fallback |
|---|---|---|
| rag→n1 | true | null |
| n1→concept | true | null |
| concept→director-* | true | null |
| director-banner→banner-engine | true | null |
| banner-engine→director-banner | true | null |
| director-banner→cmo | true | null |
| cmo→deploy | true | **hold_and_alert** |
| shortad→deploy | true | null |
| director-article-lp-ab→sozai-inserter | false | 素材なしで続行 |

**hold_and_alert**: 入稿段階での失敗はCR生成より後なので、停止してパクに通知する設計。

---

## 4. Director の内部構造（director-banner-aipark 詳細）

### Phase 0: 入力検証

1. strategy.json 存在 + concept 確定確認
2. `validate_handoff.py "concept→director-banner" {slug}` で Gate-L2
3. `circuit_breaker.py check director-banner {slug}`
4. FAIL → CMO に報告して停止

### Phase 1: 仮説選定

1. **RAGハイブリッド検索**（勝ち/負けパターン取得）
   ```bash
   dpro_rag.py search {slug} "{concept_keyword}" --media banner --label win --top 20
   dpro_rag.py search {slug} "{concept_keyword}" --media banner --label lose --top 10
   ```
2. strategy.json の hookVectors + layers + primaryN1 を分析
3. **生成パターン判定**:
   - A: フルテスト 4層×N1 2人×4枚=32枚
   - B: 高速テスト 4層×N1 1人×4枚=16枚
   - custom
4. hypothesis_matrix 構築。各仮説に **selectionReason**（type/source_label/evidence/rationale）必須
5. comparisonPair で A/B比較設計
6. **素材セマンティック検索**（asset Embedding）

### Phase 2: engine起動

1. director-work-order-banner.json 生成（hypothesis_matrix 含む）
2. Agent tool で banner-aipark spawn
3. banner完了後: `validate_handoff.py "director-banner→banner-engine"`
4. engine-log検証（3段階）:
   - (a) Gate-L1 self_check: B0-B9 全PASS
   - (b) B10（コンセプト到達リファイン）
   - (c) B11（テキスト品質リファイン）
5. `circuit_breaker.py record banner {slug} ok/error`
6. **物理ファイル実在検証**:
   - `verify_output_substance.py --type banner --slug {slug}`
   - 部長の自己申告を信じない。CMOが独立検証する

### Phase 3: Gemini検品

1. 生成バナー画像を Gemini に投入
2. スコアリング 4軸: KV一致度 / テキスト視認性 / N1共鳴度 / 技術品質
3. copyRefineLog.aggregate をコンテキストに含める
4. 基準未達 → Phase 2 リトライ（改善指示付き、最大3回）

### Phase 4: director-review.json 生成

```json
{
  "director": "director-banner",
  "slug": "sample-saas-v2",
  "timestamp": "...",
  "cr_artifacts": [...],
  "leaf_outputs": {
    "banner-aipark": {
      "engine_log": "banner-engine-log.json",
      "cr_files": ["banner_01.png", ...],
      "self_check": { "all_pass": true, ... },
      "copy_refine_aggregate": {
        "avg_composite_before": 2.8,
        "avg_composite_after": 4.2,
        "avg_delta": 1.4,
        "phase2_5_pass_rate": 0.88,
        "most_common_fix": "emotion_trigger_strengthening"
      }
    }
  },
  "gemini_qa": { "pass": true, "scores": {...} },
  "kpi_snapshot": {...}
}
```

### Phase 5: Lv.2 リフレクション

1. 品質分析（Gemini検品 + engine-log + 過去feedback RAG）
2. FB蓄積（`rag/banner/feedback/`）
3. **コピーリファインリフレクション起動判定**（20件蓄積で起動）
4. リフレクションAgent spawn（非同期、次回から反映）
5. director-metrics に first-pass率 / retry回数 / lead time 記録

---

## 5. CR Self-Refiner Agent（Director と Gate-L3 の間）

### 起動タイミング

```
Director/Engine → Gate-L1 (self-check) → ★CR Self-Refiner★ → Gate-L3 (CMO)
```

### 検査項目（フォーマット別）

**動画（V系列）**:
- V-01: モーション検出（Gemini Vision「動きなし/Ken Burnsのみ」→ FAIL）
- V-02: 動画尺（ffprobe, 目標±20%超でFAIL）
- V-03: 解像度（1080x1920未満）
- V-04: ファイルサイズ（<5MB）
- V-05: テロップ可読性（Gemini Vision 3シーンサンプリング）
- V-06: 感情アーク整合（HOOK→PAIN→NEW→PROOF→CTA崩れ検出）

**バナー（B系列）**:
- B-01: テキスト可読性（Gemini Vision OCR）
- B-02: カラーパレット逸脱（strategy.json palette照合）
- B-03: NG表現混入（brandGuard.ngExpressions照合）
- B-04: コンセプト間類似（「同じ雰囲気」回避）

### 自律修正ループ（最大3回）

FAIL検出 → 修正アクション自動選定 → engine再呼び出し → 再検査。3回失敗でCMOエスカレーション。

---

## 6. CMO Gate-L3（3段階判定）

### Stage 0: 実ファイル実在検証（2026-04-12 追加）

> 部長の自己申告を信じない。CMOが独立して実ファイルの存在を検証する。

```bash
verify_output_substance.py --from-manifest --review {director-review.json} --slug {slug}
verify_output_substance.py --type {type} --slug {slug}
```

FAIL → 即REJECT。Stage 1-3 は実行しない。該当部長に差し戻し。

### Stage 1: 3つの魂 階層チェック

```
[愛チェック] N1感情への寄り添い / 相手否定禁止 / 恐怖→希望の道
  ↓ FAIL → 即REJECT（偉大・可能は評価しない）
  ↓ PASS
[偉大さチェック] 時間耐久性 / コンセプト浸透率 / 非コモディティ
  ↓ FAIL → 条件付きPASS（P0修正リスト付き）
  ↓ PASS
[可能チェック] 未探索の可能性 / AGI活用度 / パターン超越
  ↓ FAIL → PASS（可能不足は次回改善）
  ↓ PASS → FULL PASS
```

### Stage 2: 深掘りレビュー（3軸×Agent別）

条件付きPASS以上で実行。

- 本質的価値 / コンセプト一貫性 / 改善余地
- 部長別の固有問い: director-banner は「1秒停止力」「上位4枚と下位の差」等

### Stage 3: 根本原因分析（2026-04-03 追加）

P0/P1発見時、「設計/執筆/素材/データ/パイプラインのどこが原因か」を特定。
Agent定義の恒久改修提案を `rootCauseAnalysis` フィールドに記録。

---

## 7. サーキットブレーカー

`circuit_breaker.py` + `circuit-breakers.json`:

```json
{
  "director-banner": {
    "failure_threshold": 3,
    "cooldown_seconds": 1800,
    "fallback": "skip"
  },
  "deploy-aipark": {
    "failure_threshold": 1,
    "cooldown_seconds": 3600,
    "fallback": "hold_and_alert"
  }
}
```

- Deploy は **1回失敗で即停止**（広告費の事故防止）
- 制作系は 3回連続失敗で発動、cooldown 後に復帰可能

### 実行フロー

```
CMO: 各部長起動前に
  circuit_breaker.py check director-banner {slug}
  → PASS なら spawn
  → FAIL なら skip（該当formatをパイプラインから除外）

部長: engine完了時に
  circuit_breaker.py record banner {slug} ok
  または
  circuit_breaker.py record banner {slug} error {error_msg}
```

---

## 8. VOYAGE号への移植設計

### 8-1. VOYAGEの既存「Director的存在」

VOYAGEには既にDirector概念の実装がある:

| VOYAGE既存 | 役割 | パク相当 |
|---|---|---|
| `kiji-cko` (v3.0) | 記事LP 診断→治療→テスト設計 | director-article-lp-01-aipark + 一部CMO機能 |
| `movie-kantoku` | 動画制作の指揮 | director-video-aipark 相当 |
| `pak-sensei` | コンセプト壁打ち | concept-aipark 相当 |
| `amazon-captain` | Amazon出品指揮 | なし（VOYAGE独自） |

**教訓**: カントクパターン（「俺がGO出すまで帆を張るな」「診断なき治療は座礁する」）は既にVOYAGE独自の言語で確立。パクの Director は **同じ思想の別実装**。

### 8-2. 4部長体制の VOYAGE版提案

パクの4部長構成をVOYAGEに移植すると:

```
[VOYAGE船長（= CMO相当）]
    │
    ├─ 記事LP Director = kiji-cko（拡張）
    │      ├─ kiji-hook-crew ┐
    │      ├─ kiji-trust-crew │ 既存クルー
    │      ├─ kiji-cta-crew   │
    │      ├─ kiji-offer-crew │
    │      ├─ kiji-arc-crew   │
    │      ├─ kiji-compass-crew
    │      ├─ kiji-rewriter
    │      ├─ kiji-validator
    │      └─ kiji-tester
    │
    ├─ Banner Director = 新設 `director-banner-voyage`
    │      └─ banner-park スキル（engine）
    │
    ├─ Movie Director = movie-kantoku（拡張）
    │      ├─ movie-hook-crew
    │      ├─ movie-arc-crew
    │      ├─ movie-cta-crew
    │      ├─ movie-visual-crew
    │      ├─ movie-script-crew
    │      ├─ movie-retention-crew
    │      ├─ movie-tempo-crew
    │      ├─ movie-style-crew
    │      └─ movie-judge, movie-bridge, movie-match
    │
    ├─ Amazon Director = amazon-captain（既存）
    │      └─ amazon-park スキル
    │
    └─ SNS Director = 新設 `director-sns-voyage`（pak-senseiと分離）
           ├─ sns-script-crew
           ├─ sns-edit-crew
           ├─ sns-retake-crew
           ├─ sns-post-crew
           └─ sns-analytics-crew

共通クルー（Director非経由、CMO直轄）:
  ├─ gate-* 9体（全Director横断の品質ゲート）
  └─ pak-sensei（哲学壁打ち、Director起動前のコンセプト確立）
```

### 8-3. 移植時のベストプラクティス

1. **既存の "カントクパターン" を残す**
   - kiji-cko の「診断→治療→テスト設計」はパクの director-article-lp-01 より豊かな設計
   - 名称は Director に統一せず、VOYAGE の文化（船長・船員・甲板）を維持

2. **contracts.json 相当をVOYAGEにも**
   - `.claude/agent-contracts.json` を作成
   - 契約の種類: kiji→cko, cko→rewriter, cko→validator, movie→kantoku, banner→park

3. **director-review.json 相当の導入**
   - 各Directorが生成する manifest
   - gate-* クルーが検品 → Gate-L3 に入力

4. **circuit_breaker 概念の軽量化**
   - VOYAGE は個人運用のため、パクの本格実装ほどの必要はない
   - `scripts/circuit_breaker_log.json` に失敗ログを残す程度で十分

5. **サブエージェント制限を意識**
   - パクのCLAUDE.md 明記: 「Agent tool で起動したサブエージェントにはMCP・Bash権限が渡らない」
   - VOYAGE でも同じ制約。Director は Bash/MCP を使える状態でメイン会話から起動、Worker はテキスト推論に限定

### 8-4. 段階的移植ロードマップ

```
Phase D-1: Director契約の明文化（1セッション）
  - VOYAGE .claude/agent-contracts.json 新規作成
  - kiji-cko が出力する JSON を agent-review-kiji.json として規格化

Phase D-2: director-review.json 相当を全Director導入（2-3セッション）
  - kiji-cko → director-review-kiji.json
  - movie-kantoku → director-review-movie.json
  - amazon-captain → director-review-amazon.json
  - banner-park に Director 層を新設

Phase D-3: CMO Gate-L3 相当の判定クルー導入（3セッション）
  - VOYAGE「船長」を新設（commands/captain.md）
  - 全 Director の review を統合判定
  - 3つの魂（愛→偉大→可能）階層チェックを導入

Phase D-4: サーキットブレーカー軽量実装（1セッション）
  - scripts/cb_log.py に失敗記録
  - 連続FAIL検出時に warning 表示

Phase D-5: CR Self-Refiner 相当の導入（2セッション）
  - VOYAGE 既存 gate-quality-crew を Self-Refiner として昇格
  - B-01〜B-04 (banner)、V-01〜V-06 (movie) の自律修正ループ
```

---

## 9. VOYAGE独自の強みを活かす設計

### 「細分化クルー × 束ねるDirector」が最強

パクの Director は all-in-one で仮説選定からGemini検品まで全部やる。
VOYAGE は gate-* / kiji-* / movie-* の細分化クルー群を持っているので、**Director は "オーケストレーター" に徹する**設計が可能:

```
Paku方式（all-in-one）:
  director-banner が 仮説選定 + engine呼び出し + Gemini検品 + review生成 を全部やる

VOYAGE方式（Director + 専門クルー）:
  director-banner-voyage が
    1. pak-sensei に仮説方向性を壁打ち
    2. banner-park に生成指示
    3. gate-hook-crew / gate-n1-crew / gate-typography-crew / gate-legal-crew 並列召集
    4. 各 gate の review を統合して director-review-banner.json 生成
```

→ パクの all-in-one より **専門性が高く、学習対象が分散**する。リフレクションで「どのgateの精度が低いか」を特定できる。

---

## 10. 最終提案

VOYAGE号に Director層を導入する際の **3原則**:

1. **"カントクパターン" を軸にする**（kiji-cko の設計思想）
   - Director は一切実行しない。判断と指名だけ

2. **"細分化クルー" を活かす**
   - Director は gate-* / kiji-* / movie-* を束ねるオーケストレーター
   - Director が直接制作物に手を出さない

3. **契約ベースで接続する**
   - agent-contracts.json 相当で遷移を明文化
   - director-review.json を共通 manifest 形式に

これで、パクの「CEO/CMO/Director/Worker」4層 を VOYAGE 独自の「船長/Director/クルー群/Worker」構造に自然統合できる。VOYAGE の既存資産を尊重しつつ、パクの組織アーキの強さを取り込む最適解。
