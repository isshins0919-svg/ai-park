# 一進VOYAGE号

> ⚓ **Bon Voyage!** — 広告クリエイティブ × マーケティング戦略の統合AI航海船
> Claude Code 上で動く、10クライアント運用中の本番環境

最終更新: 2026-04-18

---

## この船は何者か

**一進VOYAGE号** は、広告マーケティングの戦略〜制作〜運用を一気通貫で自動化する Claude Code 統合システム。

- 🧭 **船長**: 一進AI（`.claude/identity.md` 参照）
- ⚓ **クルー**: 29体の専門AI（gate-* / kiji-* / movie-* / sns-* / 他）
- 📋 **スキル**: 45種の Park Skills（`/banner-park`, `/kiji-cko` 等）
- 📚 **ナレッジ**: 30ファイル（pak-philosophy + aipark-imports 含む）
- 🏢 **クライアント**: 10社を実戦運用

---

## アーキテクチャ（2026-04-18 現行）

```
[ 船長: 一進AI ]
    │
    ├─ 見張り台（Gate部門）: 10クルー — 横断的品質評価
    │    gate-* : legal / brand / quality / n1 / hook / marketing / typography / visual / image-prompt
    │    cvr-crew : CVR評価
    │
    ├─ 記事甲板（Kiji部門）: 8クルー — 記事LP評価・制作
    │    kiji-cko（CKO・カントクパターン）
    │    kiji-hook / arc / trust / cta / offer / compass
    │    kiji-rewriter / kiji-validator / kiji-tester
    │
    ├─ 動画甲板（Movie部門）: 11クルー — 動画制作全工程
    │    movie-kantoku（カントク）
    │    movie-hook / arc / cta / visual / script / retention / tempo / style
    │    movie-judge / movie-bridge / movie-match
    │
    ├─ SNS甲板: 5クルー — SNS運用
    │    sns-script / edit / retake / post / analytics + sns-marketer
    │
    ├─ Amazon航路: amazon-captain（キャプテン）+ amazon-park
    │
    └─ 哲学: pak-sensei（師匠）+ pak-philosophy.md
```

---

## 主要スキル（`.claude/commands/` 配下 45スキル）

### 戦略・リサーチ
- `/research-park` v1.0 — 商材リサーチ → strategy.json v1
- `/concept-park` v1.2 — コンセプト壁打ち → strategy.json v2
- `/youtube-research` v1.0 — YouTubeチャンネル戦略

### 制作系（3パーク）
- `/banner-park` v7.0 — Nano Banana Pro画像生成 × ベクトル品質ゲート
- `/shortad-park` v7.0 — DNA転用 × Grok動画 × Fish Audio
- `/記事LP-park` v3.0 — 戦略翻訳型 × PDFレポート

### 記事LP特化（CKOパターン）
- `/kiji-cko` v3.0 — 診断→治療→テスト設計 一気通貫
- `/kiji-hook` / `/kiji-arc` / `/kiji-trust` / `/kiji-cta` / `/kiji-offer` / `/kiji-compass` / `/kiji-flow`
- `/kiji-rewriter` / `/kiji-validator` / `/kiji-tester`

### 動画特化（カントクパターン）
- `/movie-kantoku` — GO判定 + 自動実行
- `/movie-hook` / `/movie-arc` / `/movie-cta` / `/movie-retention` / `/movie-tempo` / `/movie-style` / `/movie-judge` / `/movie-bridge` / `/movie-match`

### Amazon
- `/amazon-captain` v3.0 — Amazon航路総指揮
- `/amazon-park` v1.0 — 商品ページ × 画像生成一気通貫

### 運用・改善
- `/weekly-review` v1.0 — 週次振り返り
- `/park-kaizen` — パクの鏡 × 改善壁打ち
- `/park-patrol` — スキル自動進化パトロール
- `/nice-dive` — セッション学びログ
- `/handoff` — 次セッション引き継ぎ
- `/lp-speed` v1.0 — LP高速化自動診断
- `/coach` / `/work-mentor` / `/meeting-prep` — 仕事支援

### セッション運用
- `/morning` — 朝のルーティン（AIニュース3選 + ゴール設定）
- `/client-context` — クライアントコンテキスト読込
- `/secretary-crew` — 秘書クルー（航路整理）
- `/anonymize` — 個人情報匿名化
- `/proposal-park` v1.0 — 提案書生成
- `/sns-marketer` v1.0 — SNS戦略
- `/chuka-log` — 中華調理ログ（生活記録）

---

## ナレッジ（`.claude/knowledge/` 30ファイル）

**目次**: `.claude/knowledge/INDEX.md`

### 核心哲学
- `pak-philosophy.md`（357行） — マーケ哲学の全体像。3価値観・3つの魂・戦略翻訳・ベクトル哲学等
- `park-architecture.md` — Park Skills設計原則
- `ccdd-strategy.md` — CCDD勉強会からのAI活用方針（Phase 1-4構想）

### パク1.2.5 輸入ナレッジ（`aipark-imports/` 配下8ファイル）
2026-04-18 に AIパクくん1.2.5 配布版から輸入した判断階層・Vector-First憲法:
- `three-souls-judgment-hierarchy.md` — 愛→偉大→可能 階層判定
- `vector-first-constitution.md` — Vector-First Learning 憲法
- `alphago-judgment-principles.md` — AGI判断原則
- `cr-pdca-philosophy.md` — CR運用4原則
- `agent-requirements-5-questions.md` — Agent/Skill 5本質問
- `philosophy-constraints.md` — 哲学制約チェックリスト
- `degraded-mode-reporting.md` — degraded mode 報告義務

### コピー・DNA・ブランド
- `hook-db.md` / `cta-db.md` / `banner-dna-templates.md` / `shortad-dna-templates.md`
- `sakura-brand-guide.md` / `sakura-edit-guide.md` / `sakura-post-guide.md` / `sakura-script-guide.md`
- `sawada-article-lp-philosophy.md` / `amazon-algorithm.md`

### 動画・ビジュアル
- `scene-role-tags.md` / `motion-patterns.md` / `fv-detection-revolution.md` / `article-lp-rules.md`
- `creative-reference.md` / `shortad-reference.md` / `ai-video-pipeline.md`
- `telop-platform-guidelines.md` / `video-edit-kantoku-rules.md`
- `asset-guide.md` / `music-selection.md` / `bgm-catalog.md`

### 技術・運用
- `vector-utils.md` / `google-slides-recipe.md` / `slack-error-notification.md`

---

## クライアント（`.claude/clients/` 10社）

登録済み: `sawada` / `sawada-co` / `ameru` / `gungun` / `onmyskin` / `proust` / `camicks` / `mauri` / `yomite` / `sakura`

各クライアントの過去レポート・LP・提案書は `reports/clients/{slug}/` に整理。

---

## クイックスタート

### 1. 前提
- Claude Code（[claude.ai/claude-code](https://claude.com/download)）
- Python 3.12+ 推奨（video-ai系含む場合）
- FFmpeg（動画生成）
- 環境変数（`~/.zshrc`）:
  - `GEMINI_API_KEY_1` / `_2` / `_3`（Nano Banana Pro）
  - `XAI_API_KEY`（Grok動画）
  - `FISH_AUDIO_API_KEY`（TTS）

### 2. 起動
```bash
cd ~/Desktop/一進VOYAGE号
claude
```

### 3. 基本フロー

```
1. /research-park で商材リサーチ → strategy.json v1
2. /concept-park でコンセプト確定 → strategy.json v2
3. /banner-park or /shortad-park or /記事LP-park で制作
4. gate-* クルーが品質評価
5. 納品 → クライアント別 reports/clients/{slug}/ に保存
```

---

## 運用資産

### MCP接続
- **DPro MCP**: 競合広告データ（スコアリング付き）
- **Slack MCP**: 通知・コミュニケーション
- **Google Calendar / Canva / Drive**: 業務連携
- **Chrome**: ブラウザ操作

### 常駐Bot（`scripts/` 配下）
- `slack_dpro_bot.py` — DProデータの定期Slack配信
- `slack_feedback_bot.py` — FB収集Bot

### 2台同期
```bash
./sync.sh [pull|push|status]
```

---

## 進化の記録

**CHANGELOG**: `CHANGELOG.md` 参照

直近の主要進化:
- 2026-04-18 — AIパクくん1.2.5 解析 + 哲学統合 + reports/ 完全構造化（詳細: `reports/aipark/evolution_20260418_SUMMARY.md`）

---

## 注意事項

- APIキーは必ず環境変数。`.env` / コードに直書きしない
- `clients/` のクライアント情報は機密。外部送信前に `/anonymize` で匿名化
- Grok動画は横型（848x480）で出力 → FFmpegでポートレート変換（スキル内自動）
- 破壊的操作（`rm -rf` / `git push --force`）は `.claude/rules/security.md` で禁止

---

## ドキュメント

| ファイル | 用途 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | プロジェクト基本設定・起動ルール |
| [CHANGELOG.md](CHANGELOG.md) | VOYAGE号の進化記録 |
| [.claude/identity.md](.claude/identity.md) | 一進AIの人格定義 |
| [.claude/knowledge/INDEX.md](.claude/knowledge/INDEX.md) | ナレッジ30ファイルの目次 |
| [.claude/knowledge/pak-philosophy.md](.claude/knowledge/pak-philosophy.md) | マーケ哲学全文 |
| [reports/INDEX.md](reports/INDEX.md) | 全レポート目次 |
| [reports/aipark/aipark_1.2.5_SUMMARY.md](reports/aipark/aipark_1.2.5_SUMMARY.md) | AIパクくん1.2.5 解析サマリー |
| [reports/aipark/evolution_20260418_SUMMARY.md](reports/aipark/evolution_20260418_SUMMARY.md) | 2026-04-18 進化レポート |

---

> ⚓ **本質 × 速度** — 一進VOYAGE号の航海哲学
