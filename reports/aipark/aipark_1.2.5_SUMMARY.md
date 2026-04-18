# AIパクくん1.2.5 解析セッション — 全成果物サマリー

> 作成: 2026-04-18
> 対象: `~/Downloads/AIパクくん1.2.5/` 完全解析
> 実行者: Claude Opus（一進VOYAGE号セッション）

---

## セッション概要

「AIパクくん1.2.5」配布版を完全解析し、一進VOYAGE号にどう活かすかの判断材料を構築した。
要望: (1) Phase A実行、(2) 差分マップ、(3) 3技術のdeep-dive、(4) PDFマニュアル解析、(5) 精度向上提案を全て実行。

---

## 生成物一覧（8ファイル）

### レポート群（`reports/` 配下、計6ファイル）

| ファイル | 目的 | サイズ |
|---|---|---|
| [aipark_1.2.5_diff_map.md](./aipark_1.2.5_diff_map.md) | **完全差分マップ**。VOYAGE × パクの優劣・輸入優先度を網羅 | 21KB |
| [aipark_deep_dive_alphago.md](./aipark_deep_dive_alphago.md) | **AlphaGo判断エンジン deep-dive**。UCB/ベイズ/期待値/Thompson解説 | 11KB |
| [aipark_deep_dive_vector_first.md](./aipark_deep_dive_vector_first.md) | **Vector-First学習回路 deep-dive**。V/C/X 3空間 + 7主審スコア | 14KB |
| [aipark_deep_dive_director_layer.md](./aipark_deep_dive_director_layer.md) | **Director層 deep-dive**。4部長体制 + Gate-L1/L2/L3 | 17KB |
| [aipark_pdf_manual_summary.md](./aipark_pdf_manual_summary.md) | **PDFマニュアル要約**。14MB, 16ページの販売資料を分析 | 15KB |
| [aipark_claude_md_merge_proposal.md](./aipark_claude_md_merge_proposal.md) | **CLAUDE.mdマージ提案**。5提案 + 適用判断 | 9KB |

### 輸入ナレッジ（`.claude/knowledge/aipark-imports/` 配下、計8ファイル）

| ファイル | 内容 | 使用場面 |
|---|---|---|
| [README.md](../.claude/knowledge/aipark-imports/README.md) | 輸入ポリシーと全体マップ | 最初に読む |
| [three-souls-judgment-hierarchy.md](../.claude/knowledge/aipark-imports/three-souls-judgment-hierarchy.md) | 愛→偉大→可能 階層判定 | CR評価時 |
| [vector-first-constitution.md](../.claude/knowledge/aipark-imports/vector-first-constitution.md) | Vector-First Learning 憲法 | データ・仮説設計時 |
| [alphago-judgment-principles.md](../.claude/knowledge/aipark-imports/alphago-judgment-principles.md) | AGI判断原則 | 運用判断時 |
| [cr-pdca-philosophy.md](../.claude/knowledge/aipark-imports/cr-pdca-philosophy.md) | CR運用4原則 | 日次/週次PDCA時 |
| [agent-requirements-5-questions.md](../.claude/knowledge/aipark-imports/agent-requirements-5-questions.md) | Agent/Skill 5本質問 | 新規Agent/Skill作成時 |
| [philosophy-constraints.md](../.claude/knowledge/aipark-imports/philosophy-constraints.md) | 哲学制約チェックリスト | CR仮説生成後、生成前 |
| [degraded-mode-reporting.md](../.claude/knowledge/aipark-imports/degraded-mode-reporting.md) | degraded mode 報告義務 | 全スキル完走時 |

---

## 解析の核心メッセージ

### 1. パクの正体
**「AIパクくん1.2.5」は、CEO/CMO/4部長/7共通Agent の階層組織をClaude Code上に実装したCMO SaaS**。
- 38 Agents × 37 Skills × 70+ Python scripts × 50+ ナレッジMD
- センターピン: 「XX万円 × 1000社」の販売を2026-05末達成
- 最大訴求: 「データ駆動（Embedding 2, 3072D）」

### 2. VOYAGE号の本質的欠落
VOYAGE `ccdd-strategy.md` が Phase 1-4 構想として残していた全項目が、**パク側で既に動くコードとして存在**:

| CCDD Phase | VOYAGE現状 | パク実装 |
|---|---|---|
| Phase 1: knowledge/ ベクトル化 | 未実装（構想のみ） | `knowledge_rag.py` + `embedding_utils.py` |
| Phase 2: 永続ベクトルDB | 未実装 | `vector_intelligence.py`（ChromaDB化はVOYAGEでも可） |
| Phase 3: リフレクションループ | 手動 `/nice-dive` のみ | `reflection_trigger.py` + `ceo-reflection-aipark` |
| Phase 4: DPro実績×ベクトル | 未実装 | `dpro_rag.py` + `judgment-accuracy.json` |

### 3. VOYAGEの先行優位
- 10クライアント運用中（sawada / sawada-co / ameru / gungun / onmyskin / proust / camicks / mauri / yomite / sakura）
- Slack常駐bot（dpro / feedback）稼働中
- `kiji-cko` カントクパターンがパクの Director より**豊か**
- `gate-*` / `kiji-*` / `movie-*` の細分化クルー群で専門性高い
- SNS運用 / Amazon運用 / 記事LP評価 の**フォーマット多様性**

### 4. 採択ロードマップ（6フェーズ）
- **Phase A**: 哲学・ナレッジ輸入（今回完了）
- **Phase B**: DNAテンプレート差分輸入（hook-db/cta-db等を2層構造化）
- **Phase C**: strategy.json スキーマ導入（clients/*.md → strategy.json 段階移行）
- **Phase D**: Director層再編（kiji-cko 拡張 + Director for banner/movie/amazon/sns）
- **Phase E**: Vector-First 基盤（CCDD Phase 1-4 本番実装）
- **Phase F**: OODA + Reflection Lv.4（night-brain/morning-check/ceo-reflection）

---

## Phase A で実際に完了したこと

### 新規作成ファイル（9個）

1. `.claude/knowledge/aipark-imports/README.md`
2. `.claude/knowledge/aipark-imports/three-souls-judgment-hierarchy.md`
3. `.claude/knowledge/aipark-imports/vector-first-constitution.md`
4. `.claude/knowledge/aipark-imports/alphago-judgment-principles.md`
5. `.claude/knowledge/aipark-imports/cr-pdca-philosophy.md`
6. `.claude/knowledge/aipark-imports/agent-requirements-5-questions.md`
7. `.claude/knowledge/aipark-imports/philosophy-constraints.md`
8. `.claude/knowledge/aipark-imports/degraded-mode-reporting.md`
9. `reports/aipark_claude_md_merge_proposal.md`（CLAUDE.md 本体変更は提案のみ）

### 変更していないファイル

- `CLAUDE.md` — 提案のみ（自動適用なし）
- `.claude/knowledge/pak-philosophy.md` — 現状維持
- `.claude/knowledge/ccdd-strategy.md` — 現状維持
- `.claude/commands/` 配下 — 一切変更なし
- `.claude/agents/` 配下 — 一切変更なし
- `.claude/clients/` 配下 — 一切変更なし

**破壊性ゼロ**。既存VOYAGEの動作に影響なし。

---

## 解析精度向上のために追加実施した内容

ユーザー要望「こうした方が正確になる、を必ず反映」に応じて以下を追加実施:

### (A) 本体コードの深掘り読込
- `vector_intelligence.py`（200行読破）— V/C/X 3空間Embedding実装詳細
- `director-banner-aipark.md`（250行）— Director内部フロー詳細
- `cr-self-refiner-aipark.md` — Self-Refiner の検査項目
- `ceo-reflection-aipark.md` — 週次Lv.4リフレクション実装
- `circuit_breaker.py` — サーキットブレーカー実装
- `agent-contracts.json` — Agent間契約 30+遷移の全定義
- `strategy-schema.json` — V1-V5 成熟度レベル定義
- `night-brain.md` Phase 1-2 — OODAループ Python層データ収集

### (B) VOYAGE本体との突き合わせ
- `.claude/agents/` 29体リスト確認
- `.claude/commands/` 44+スキルリスト確認
- `.claude/knowledge/` 26ファイルリスト確認
- `.claude/clients/` 10社確認（sakura, sawada-co 追加検知）
- `pak-philosophy.md` 357行の既存哲学と差分確認
- `ccdd-strategy.md` Phase 1-4 構想との照合

### (C) PDFマニュアル14MB解析
- v1.2.4 ユーザーマニュアル全16ページ読破
- 販売コンセプト（Agentic AI マーケティング会社）抽出
- 公開Agent（9体）vs 内部Agent（38体）の差分確認
- ターゲット・価格・価値提案の戦略推定

### (D) 補完関係の発見
- VOYAGE「3つの魂」(CR構成) × パク「3つの魂」(判断階層) → **補完**
- VOYAGE `kiji-cko` カントクパターン × パク Director → **同思想の別実装**
- VOYAGE `ccdd-strategy.md` 構想 × パク実装 → **VOYAGEの構想を先に実装済み**

これらの発見により、「一方的な輸入」ではなく「**対等な統合**」の視点で全レポートを構成できた。

---

## 次のアクション候補（優先順位付き）

### すぐやる候補

1. **CLAUDE.md マージ提案の適用判断**
   - `reports/aipark_claude_md_merge_proposal.md` を確認
   - 提案1（本質指令）+ 提案2（ナレッジ表）+ 提案3（クライアント）の3点最小適用を推奨

2. **aipark-imports の利用開始**
   - 次にCR評価する時に `three-souls-judgment-hierarchy.md` を参照
   - 次にAgent/Skillを作る時に `agent-requirements-5-questions.md` を参照
   - 次にスキル完走時に `degraded-mode-reporting.md` を参照

### 1-2週間以内

3. **Phase B: DNAテンプレート差分輸入**
   - hook-db.md / cta-db.md を 2層構造化
   - パクの自動進化ゾーン（`<!-- AUTO-EVOLUTION-ZONE -->`）導入
   - `shortad-dpro-winning-patterns.md` 等を新規輸入

4. **learnings-db.json 導入**
   - 各クライアント配下に `learnings-db.json` 作成
   - 48h / 7日 / 30日判定の自動記録

### 1-2ヶ月以内

5. **Phase C: strategy.json 移行**
   - `parks/strategies/strategy-schema.json` 配置
   - sawada / ameru を先行移行

6. **Phase D: Director層強化**
   - `agent-contracts.json` 相当をVOYAGEに
   - director-review.json manifest 形式統一

### 3-6ヶ月（本命）

7. **Phase E: Vector-First 本番実装**
   - `embedding_utils.py` / `vector_intelligence.py` 相当を移植
   - 7主審スコア計算関数の実装
   - ChromaDB 永続化でクロスクライアント検索

8. **Phase F: OODA + Reflection Lv.4**
   - night-brain / morning-check を既存Slack bot と統合
   - ceo-reflection を月曜10:00 cron

---

## リスク整理

| リスク | 対策 |
|---|---|
| 輸入ナレッジと既存 pak-philosophy.md の食い違い | `aipark-imports/` に隔離、本体は現状維持 |
| スキル名衝突（banner-park 等） | VOYAGE版を維持、パク版は参照のみ |
| Python runtime 依存（3.12+） | bootstrap script は段階導入 |
| `settings.json` 権限衝突 | VOYAGE `rules/security.md` を優先 |
| Runtime dir 非採用 | VOYAGE repo完結派のポリシーを維持 |
| クライアント実データ流出 | `rules/anonymize.md` で継続保護 |
| CLAUDE.md 200行超警告 | マージ提案は130-140行想定、余裕あり |

---

## 最終評価

### パク1.2.5 の価値
**★★★★☆**
- 技術実装は極めて高い完成度
- 組織アーキ（CEO/CMO/Director/Worker）は参考価値大
- Vector-First 実装が CCDD Strategy の完成形
- ユーザー向けパッケージングも優秀（PDFマニュアル）

### VOYAGEでの活用見込み
**★★★★★**
- VOYAGE構想（CCDD Strategy）の完全実装として使える
- 実戦10クライアントとパク技術の組み合わせで独自優位性
- パク単体・VOYAGE単体では到達できないフェーズへの道筋が見えた

### 即座の価値
**★★★☆☆**
- Phase A（今回）で哲学・ナレッジの基盤が整った
- 実運用への影響は Phase B 以降で顕在化
- 小さく始めて段階拡張の方針が現実的

---

## セッション成果物の物理マップ

```
/Users/ca01224/Desktop/一進VOYAGE号/
├── CLAUDE.md  (変更なし。マージ提案は reports/ に)
├── .claude/
│   └── knowledge/
│       └── aipark-imports/   ← 今回新設
│           ├── README.md
│           ├── three-souls-judgment-hierarchy.md
│           ├── vector-first-constitution.md
│           ├── alphago-judgment-principles.md
│           ├── cr-pdca-philosophy.md
│           ├── agent-requirements-5-questions.md
│           ├── philosophy-constraints.md
│           └── degraded-mode-reporting.md
└── reports/   ← 今回追加
    ├── aipark_1.2.5_SUMMARY.md          (本ファイル)
    ├── aipark_1.2.5_diff_map.md
    ├── aipark_deep_dive_alphago.md
    ├── aipark_deep_dive_vector_first.md
    ├── aipark_deep_dive_director_layer.md
    ├── aipark_pdf_manual_summary.md
    └── aipark_claude_md_merge_proposal.md
```

---

## 結び

VOYAGE号は既に10社の実戦経験と多様なフォーマット対応で**独自の強み**を持つ。
パク1.2.5は**基盤技術と組織アーキ**で補完する。

この2つの統合は「VOYAGE が自ら到達するのに3-6ヶ月かかった Phase 1-4」を**圧縮する近道**になる。
ただし、パクを丸呑みしない。VOYAGE文化（船長・クルー・甲板・カントクパターン）を核に、パクを**素材**として使う姿勢が最適解。

次のセッションで「次のアクション」の何をやるか決めればOK。今回の成果物が参考資料として残る。

> ⚓ Bon Voyage — VOYAGE号のAGI時代航海、次のフェーズへ
