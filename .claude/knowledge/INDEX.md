# knowledge/ — 目次

> VOYAGE号の全ナレッジDB（30ファイル / 2026-04-18）
> スキルは必要時に読む。起動時には読まない
>
> 📌 進化の記録: [CHANGELOG.md](../../CHANGELOG.md)
> 📌 レポート目次: [reports/INDEX.md](../../reports/INDEX.md)

---

## 🧭 最上位（全判断基準）

| ファイル | 用途 |
|---|---|
| [pak-philosophy.md](pak-philosophy.md) | **マーケ哲学の核**（357行）。全スキル共通の判断基準。3価値観・3つの魂・戦略翻訳・KV哲学・エンベディング哲学・組織設計・プランモード・フィードバック・ポメ太DIVE9原則 |
| [park-architecture.md](park-architecture.md) | Park Skillsパイプライン設計原則 |
| [ccdd-strategy.md](ccdd-strategy.md) | CCDD勉強会からのAI活用方針（Phase 1-4構想） |
| [lp-n1-framework.md](lp-n1-framework.md) | **LP N1フレーム**（買う瞬間の動機軸）。`/lp-park`から必読。ameru案件で確立 |

---

## 🎣 フック・コピーDB

| ファイル | 用途 |
|---|---|
| [hook-db.md](hook-db.md) | フックコピーDB |
| [cta-db.md](cta-db.md) | CTAコピーDB |
| [fv-detection-revolution.md](fv-detection-revolution.md) | FV検出ロジック |

---

## 🎬 フォーマット別DNA

| ファイル | 用途 |
|---|---|
| [banner-dna-templates.md](banner-dna-templates.md) | バナー広告DNA |
| [shortad-dna-templates.md](shortad-dna-templates.md) | ショート動画DNA |
| [shortad-reference.md](shortad-reference.md) | ショート動画リファレンス |
| [ai-video-pipeline.md](ai-video-pipeline.md) | AI動画パイプライン |
| [article-lp-rules.md](article-lp-rules.md) | 記事LPルール |
| [motion-patterns.md](motion-patterns.md) | モーションパターン |
| [telop-platform-guidelines.md](telop-platform-guidelines.md) | テロップ設計ガイド |
| [scene-role-tags.md](scene-role-tags.md) | シーン役割タグ |

---

## 🎨 ビジュアル・素材

| ファイル | 用途 |
|---|---|
| [asset-guide.md](asset-guide.md) | 素材ガイド |
| [creative-reference.md](creative-reference.md) | クリエイティブリファレンス |
| [music-selection.md](music-selection.md) | 音楽選定 |
| [bgm-catalog.md](bgm-catalog.md) | BGMカタログ |

---

## 🏢 ブランド・クライアント共通

| ファイル | 用途 |
|---|---|
| [sakura-brand-guide.md](sakura-brand-guide.md) | さくら ブランドガイド |
| [sakura-edit-guide.md](sakura-edit-guide.md) | さくら 編集ガイド |
| [sakura-post-guide.md](sakura-post-guide.md) | さくら 投稿ガイド |
| [sakura-script-guide.md](sakura-script-guide.md) | さくら 台本ガイド |
| [sawada-article-lp-philosophy.md](sawada-article-lp-philosophy.md) | sawada 記事LP哲学 |
| [amazon-algorithm.md](amazon-algorithm.md) | Amazonアルゴリズム |
| [slack-error-notification.md](slack-error-notification.md) | Slack通知設定 |
| [video-edit-kantoku-rules.md](video-edit-kantoku-rules.md) | 動画編集カントクルール |
| [google-slides-recipe.md](google-slides-recipe.md) | Googleスライド生成レシピ |
| [vector-utils.md](vector-utils.md) | ベクトルユーティリティ設計 |

---

## 🎈 パク1.2.5 輸入ナレッジ（2026-04-18 新規）

[aipark-imports/](aipark-imports/) 配下の8ファイル。VOYAGE本体を尊重しつつ、パクCMOの判断階層・Vector-First憲法・CR運用原則を追加レイヤーで取り込み。

| ファイル | 使う場面 |
|---|---|
| [aipark-imports/README.md](aipark-imports/README.md) | 輸入ナレッジ全体マップ |
| [aipark-imports/three-souls-judgment-hierarchy.md](aipark-imports/three-souls-judgment-hierarchy.md) | CR評価時（愛→偉大→可能） |
| [aipark-imports/vector-first-constitution.md](aipark-imports/vector-first-constitution.md) | データ・仮説設計時 |
| [aipark-imports/alphago-judgment-principles.md](aipark-imports/alphago-judgment-principles.md) | 運用判断時 |
| [aipark-imports/cr-pdca-philosophy.md](aipark-imports/cr-pdca-philosophy.md) | 日次/週次PDCA時 |
| [aipark-imports/agent-requirements-5-questions.md](aipark-imports/agent-requirements-5-questions.md) | Agent/Skill新規作成時 |
| [aipark-imports/philosophy-constraints.md](aipark-imports/philosophy-constraints.md) | CR仮説生成後、生成前 |
| [aipark-imports/degraded-mode-reporting.md](aipark-imports/degraded-mode-reporting.md) | 全スキル完走時 |

---

## 📖 使い方

### スキル起動時
各スキルが**自身の判断で**必要なファイルを読む。起動時にCLAUDE.mdから一括読み込みはしない（Tier 0を肥大化させない）。

### ファイル選定の判断フロー
```
タスク受領
  ↓
「何を作る？」→ フォーマット別DNA を読む（banner / shortad / article-lp）
「どう評価する？」→ pak-philosophy + aipark-imports/three-souls を読む
「データはある？」→ ccdd-strategy + aipark-imports/vector-first を読む
「仮説の根拠は？」→ hook-db + cta-db + aipark-imports/philosophy-constraints を読む
「運用判断？」→ aipark-imports/alphago + cr-pdca を読む
「新Agent作る？」→ aipark-imports/agent-requirements-5-questions を読む
```

### 全ファイル検索
```bash
grep -rn "{keyword}" .claude/knowledge/ --include="*.md"
```
