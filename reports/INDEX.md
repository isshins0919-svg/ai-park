# reports/ — 目次

> VOYAGE号の全レポート・成果物・スクリプトの航海日誌
> 最終更新: 2026-04-18

---

## 📁 ディレクトリ構成

```
reports/
├── aipark/        ← AIパクくん1.2.5 解析成果物（2026-04-18）
├── clients/       ← クライアント別レポート・LP・提案書
│   ├── ameru/
│   ├── sawada/
│   ├── gungun/
│   ├── proust/
│   ├── mauri/
│   ├── yomite/
│   ├── camicks/
│   ├── the-woobles/
│   ├── kosuri/
│   └── sakura/
├── projects/      ← プロジェクト別（案件横断）
│   ├── setsunatrain2/   — 瀬津奈TRAIN2 動画プロジェクト
│   ├── ccdd-mini-dive/  — CCDD勉強会 ミニダイブ
│   └── world-trip/      — VOYAGE 2026 世界旅ルート
├── archive/       ← 古い分析レポート
├── scripts/       ← 一時生成スクリプト（画像生成等）
├── edit-sheets/   ← 編集シート
├── templates/     ← テンプレート
├── textbook/      ← 教材・学習資料
└── index.html     ← トップindex
```

---

## 🎯 最新の重要レポート

### AIパクくん1.2.5 統合 + VOYAGE号進化（2026-04-18、最新）

**最重要**: [reports/aipark/evolution_20260418_SUMMARY.md](aipark/evolution_20260418_SUMMARY.md) — 進化実行の全体像

[reports/aipark/aipark_1.2.5_SUMMARY.md](aipark/aipark_1.2.5_SUMMARY.md) — 解析成果物の目次

- **evolution_SUMMARY**: 2026-04-18 進化実行レポート（本日の最新）
- **1.2.5_SUMMARY**: パク解析の全成果物サマリー
- **diff_map**: VOYAGE × パク 完全差分マップ
- **deep_dive (3本)**: AlphaGo / Vector-First / Director の技術解析
- **pdf_manual_summary**: PDFマニュアル14MB解析
- **claude_md_merge_proposal**: CLAUDE.md統合提案（適用済み）

### 全体進化の追跡
- [CHANGELOG.md](../CHANGELOG.md) — VOYAGE号の進化記録（時系列）

---

## 📊 クライアント別ショートカット

| クライアント | 主要レポート |
|---|---|
| ameru | [LP v4](clients/ameru/ameru_lp_v4.html) / [参考LP解析30件](clients/ameru/ameru_reference_lp_30.md) |
| sawada | [AI training proposal](clients/sawada/sawada-ai-training-proposal.html) |
| gungun | [Insight report](clients/gungun/gungun_insight_report.html) / [薬機法対応LP](clients/gungun/gungun_article_lp_yakki.html) |
| proust | [LP最適化](clients/proust/proust-lp-optimization.html) / [CR分析](clients/proust/proust2_creative_analysis.html) |
| mauri | [LP診断](clients/mauri/mauri-lp-diagnosis.html) |
| yomite | [AIポリシー](clients/yomite/yomite-ai-policy.html) / [マーケタースキル評価](clients/yomite/yomite-marketer-skillset.html) |
| camicks | [Amazon モックアップ](clients/camicks/camicks-amazon-final-mockup.html) |
| the-woobles | [リサーチ](clients/the-woobles/the-woobles-research.md) / [ビジュアル](clients/the-woobles/the-woobles-visual-report.html) |
| kosuri | [GCP アーキテクチャ](clients/kosuri/kosuri-gcp-architecture.html) / [進化レポート](clients/kosuri/kosuri_evolution_report_20260418.md) |
| sakura | （scripts/ にgenerator、docs/sakura_images/ に素材） |

---

## 🗂️ アーカイブ

[archive/](archive/) に以下を格納:
- growth-supplement-competitive-report.html（2026-03）
- video-production-system-report.md（2026-04）

30日以上アクセスされていないレポートは将来ここへ移動予定。

---

## 🔧 運用ルール

### 新規レポート作成時
1. クライアント案件なら → `clients/{slug}/` 配下
2. 横断プロジェクトなら → `projects/{name}/` 配下
3. 戦略・解析系なら → トップ直下（後で archive/ へ移動）
4. スクリプトは → `scripts/` 配下

### アーカイブ判断基準
- 30日以上参照されていない
- クライアントがactive statusから外れた
- プロジェクトが完了・中止した

### 整理のタイミング
- 週次（/weekly-review 時）
- セッション終了時（必要に応じて）
