# CLAUDE.md — 一進AI

---

## 1. 起動アクション

起動時、最初のメッセージに応答する前に実行:

1. `.claude/identity.md` を読み、その人格で応答
2. `date '+%Y-%m-%d %H:%M (%a)'` で現在時刻取得・表示
3. `git pull origin main --rebase`（成功→✅ / 変更→⬇N件 / 失敗→⚠オフライン）
4. 起動メッセージに「⚓ Bon Voyage!」を含める
5. `おはよう` の場合 → `/morning` + 毎朝パトロール（後述）を並行実行

**ナレッジは起動時に読まない。** 各スキルが必要時に自分で読み込む。

### 毎朝パトロール（おはよう時のみ）

1. agents/ と commands/ の役割重複チェック
2. agents/ のフロントマター欠落チェック
3. .DS_Store / 古いhandoff（3日超） / 一時ファイル検出
4. CLAUDE.md 200行超 / agents 20体超 / commands 50個超 → 警告
5. clients/ の `last_updated` 14日超 → 指摘

### セッション終了（おつかれ/ばいばい/おわり/また明日/終了/寝る）

1. `git status` → 変更あり → `git add -A && git commit -m "sync: YYYY-MM-DD" && git push origin main`
2. うまくいかなかったSkillがあれば改善提案

### プランモード

- 作る時 → プランモード必須。動かす時 → 不要
- プランセッションで実行しない（コンテクスト枯渇→ハルシネーション）
- プラン完成 → `/handoff` → 次セッションで実行

### セッション管理

- `/handoff` — 次セッションへのコンテキスト引き継ぎ
- `/nice-dive` — セッションの学びをログに記録
- Skill自己改善: 期待と違う動きをしたSkillは即アップデート

---

## 2. コンテキストコスト設計（最重要）

Claude Codeの性能はコンテキスト管理で決まる。

```
Tier 0: CLAUDE.md + rules/    → 全メッセージに入る。1行でも減らす
Tier 1: Read（knowledge等）   → セッション中残る。必要時だけ読む
Tier 2: commands/              → /skill起動で親に読み込み。重いスキルは注意
Tier 3: agents/                → 独立コンテキスト。親にコスト0。並列可
```

### agents/ vs commands/ の判断基準

| | commands/ | agents/ |
|---|---|---|
| 起動 | ユーザーが `/skill` で手動 | Claude が Agent tool で自動 |
| コンテキスト | 親と共有（Tier 2） | 独立（Tier 3） |
| 適する用途 | オーケストレーター・対話型 | レビュー・評価・並列サブタスク |

**原則: 重い専門タスクはagents/、ユーザー対話が必要なものはcommands/**

---

## 3. ファイル構造

```
.claude/
  commands/   ← /skill で起動するスキル
  agents/     ← Agent tool で自動起動するサブエージェント
  knowledge/  ← スキルが必要時に読むナレッジDB
  clients/    ← クライアント情報（案件着手前に必ず読む。作業後にKPI更新）
  rules/      ← 自動適用ルール（anonymize / security / lp-rules）
  scripts/    ← 常駐Bot・分析スクリプト
  logs/       ← Nice Diveログ
  handoff/    ← セッション引き継ぎ
```

### ナレッジ（knowledge/）の使い方

| ファイル | 用途 | 読むタイミング |
|---|---|---|
| pak-philosophy.md | マーケ哲学（全判断基準） | クリエイティブ制作・評価時 |
| hook-db.md | フックコピーDB | フック設計・評価時 |
| cta-db.md | CTAコピーDB | CTA設計・評価時 |
| park-architecture.md | Park Skills設計原則 | スキル新規作成・改善時 |

### クライアント（clients/）

登録済み: sawada / ameru / gungun / onmyskin / proust / camicks / mauri / yomite

---

## 4. 技術設定

- 同期: `./sync.sh [pull|push|status]`（起動時auto-pull / 終了時auto-push）
- 出力先: `reports/` / `banner-park/output/` / `video-ai/output/`
- 環境変数: GEMINI_API_KEY_1〜3 / XAI_API_KEY / FISH_AUDIO_API_KEY（~/.zshrc）
