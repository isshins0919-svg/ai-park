# CHANGELOG — 一進VOYAGE号 進化の記録

> VOYAGE号の主要アップデートを時系列で記録
> 書式: `YYYY-MM-DD` / 主な変更 / 影響範囲

---

## 2026-04-18 — AIパクくん1.2.5 統合 + 全資料整備 🎈

### 🎯 ハイライト
**AIパクくん1.2.5 配布版（CMO SaaS）を完全解析し、哲学・判断階層・Vector-First 憲法を VOYAGE号の土台に統合。加えて reports/ 完全構造化・CLAUDE.md 本質指令0章追加・INDEX.md 体制確立。**

### 追加（新規作成）

#### ナレッジ: `aipark-imports/` 新設（8ファイル）
- `.claude/knowledge/aipark-imports/README.md`
- `.claude/knowledge/aipark-imports/three-souls-judgment-hierarchy.md` — 愛→偉大→可能 階層判定
- `.claude/knowledge/aipark-imports/vector-first-constitution.md` — Vector-First 憲法6条
- `.claude/knowledge/aipark-imports/alphago-judgment-principles.md` — AGI判断原則
- `.claude/knowledge/aipark-imports/cr-pdca-philosophy.md` — CR運用4原則
- `.claude/knowledge/aipark-imports/agent-requirements-5-questions.md` — Agent/Skill 5本質問
- `.claude/knowledge/aipark-imports/philosophy-constraints.md` — 哲学制約チェックリスト
- `.claude/knowledge/aipark-imports/degraded-mode-reporting.md` — degraded mode 報告義務

#### レポート: `reports/aipark/` 新設（7ファイル）
- `aipark_1.2.5_SUMMARY.md` — 全成果物サマリー
- `aipark_1.2.5_diff_map.md` — VOYAGE × パク 完全差分マップ
- `aipark_deep_dive_alphago.md` — AlphaGo判断エンジン解析
- `aipark_deep_dive_vector_first.md` — Vector-First 学習回路解析
- `aipark_deep_dive_director_layer.md` — Director層解析
- `aipark_pdf_manual_summary.md` — PDFマニュアル14MB解析
- `aipark_claude_md_merge_proposal.md` — CLAUDE.md統合提案
- `evolution_20260418_SUMMARY.md` — 進化実行レポート

#### 新規INDEXファイル
- `reports/INDEX.md` — レポート全体目次
- `.claude/knowledge/INDEX.md` — ナレッジ30ファイル分類目次
- `CHANGELOG.md` — 本ファイル

### 変更

#### CLAUDE.md: 本質指令0章を追加（101行 → 124行）
- 本質を見抜く / AGI最大レバレッジ / 意図を汲む / 黙って突っ走らない / degraded mode 報告義務
- ナレッジ表に `aipark-imports/` 行を追加
- クライアントリスト 8社 → 10社（`sawada-co` / `sakura` 追加）
- バックアップ作成: `CLAUDE.md.backup-20260418`

#### README.md: 全面改訂
- 古いスキル一覧（8個 → 45個の実態反映）
- クルー構成の階層化（Gate/Kiji/Movie/SNS/Amazon）
- パク輸入ナレッジの明記
- 直近の進化記録リンク

#### `park-architecture.md`: 35行 → 拡張
- カントクパターン原則を追記
- 判断階層（パク輸入）を統合
- Vector-First原則を統合
- Phase A-F ロードマップを記載

#### `ccdd-strategy.md`: 実装ステータスを追記
- Phase 1-4 の構想にパク側実装の存在を明記
- VOYAGE号は自力実装 → パク実装の段階移植に戦略転換

#### 主要7スキル/Agentに aipark-imports 参照を結線
- `/kiji-cko` — three-souls-hierarchy + philosophy-constraints + alphago-principles
- `/banner-park` — three-souls-hierarchy + philosophy-constraints + vector-first
- `/movie-kantoku` — three-souls-hierarchy + philosophy-constraints + alphago-principles
- `/park-kaizen` — agent-requirements-5-questions + vector-first
- `/amazon-captain` — three-souls-hierarchy + alphago-principles + cr-pdca-philosophy
- `/weekly-review` — vector-first + cr-pdca-philosophy + agent-requirements-5-questions
- `pak-sensei` (agent) — three-souls-hierarchy + philosophy-constraints

### 整理（移動・削除）

#### `reports/` 構造化（58ファイルのフラット → 10ディレクトリ + INDEX）
```
reports/
├── INDEX.md             ← 新規
├── aipark/              ← 今日の成果物7ファイル
├── clients/             ← 10社別（ameru/sawada/gungun/proust/mauri/yomite/camicks/the-woobles/kosuri/sakura）
├── projects/            ← setsunatrain2/ccdd-mini-dive/world-trip
├── archive/             ← 古いレポート
├── scripts/             ← 生成スクリプト
└── (既存: edit-sheets / templates / textbook / index.html)
```

#### `.claude/handoff/` の古いファイル archive化
- `archive/` に 11件を移動（3日超ルール適用）
- 残存: `handoff_2026-04-17_kosuri.md` の1件のみ

#### ゴミ削除
- `.DS_Store` 7箇所 → 0

### 発見・診断
- VOYAGE ccdd-strategy.md Phase 1-4 の構想 ≒ パク1.2.5 の実装済み機能
- VOYAGE `kiji-cko` カントクパターン ≒ パクの Director 思想（VOYAGE版の方が豊か）
- VOYAGE独自優位: SNS運用 × Amazon × 多様な制作フォーマット × 10クライアント実戦
- パク独自優位: Vector-First 基盤 × AlphaGo判断エンジン × OODA自動化

### 既知の課題（次回以降）
- `scripts/update_crew_map.py` Python 3.9 正規表現バグ
- `chuka-park/` の位置付け未整理
- Phase B（hook-db/cta-db 2層化）未着手
- Phase C（strategy.json スキーマ導入）未着手

---

## 2026-04-17 — kosuri 案件進行 + yomite ポリシー整備
- `.claude/clients/yomite.md` 更新
- `reports/clients/kosuri/kosuri_evolution_report_20260418.md` 作成

## 2026-04-15 — KOSURIちゃん仕上げ + deploy.sh PATH修正
- ユーザーの声シート統合
- FV Studio 関連更新

## 2026-04-11〜12 — CCDD（Claude Code DEEP DIVE）勉強会
- 文太（AX社代表）から学習
- `.claude/knowledge/ccdd-strategy.md` 作成
- Phase 1-4 構想を記録

## 2026-04-03 — フィードバック哲学・プランモード哲学の整備
- `pak-philosophy.md` に4哲学追記
  - 制約・クリエイティブ哲学
  - フィードバック品質の哲学
  - プランモード哲学
  - ベクトル空間での指定

## 2026-04-01 — エンベディング哲学 + エージェント組織設計哲学
- `pak-philosophy.md` に核心哲学追加
- 「エンベディングなしで良いクリエイティブは作れない」原則

## 2026-03-29 — CEO/CMO分離思想（パクから）
- リフレクションループ Lv.4 概念

## 2026-03-26 — AGI最大レバレッジ原則
- Opus 4.6 以降はAGI。if文で電卓化しない

## 2026-02-25 — クリエイティブの3つの魂 確立
- KV魂 / キラーコピー魂 / 仮説魂
- 戦略翻訳の思想
- KV哲学フィルター
- ベクトルは守護神

---

## 書式ルール

- セクション: 日付降順（最新が上）
- タグ: 🎈 マイルストーン / 🔧 運用 / 📚 ナレッジ / 🎨 制作
- 各エントリに **追加 / 変更 / 整理 / 発見** の4区分で記述
- 破壊的変更があればバックアップパスを明記
