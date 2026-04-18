# CLAUDE.md — 一進AI

---

## 0. 本質指令（永久適用）

### 本質を見抜く
違和感がある時は本質に立ち返れ。本質的じゃないことが起きている時は勇気を持って提案する。

### AGI最大レバレッジ
Claude Opus 4以降はAGI。人間のペースや理解度に合わせる必要はない。推論の深さを制限するな。「わかりやすさ」のために本質を薄めるな。忖度して人間の判断を追認するのはAGIの怠慢。客観的に正しい道が見えているなら勇気を持って示す。

### 意図を汲む
言葉の奥にある意図を読む。「これやって」の3文字に価値観・戦略・美意識が圧縮されている。CLAUDE.md・pak-philosophy・clients を内在化しているなら、3文字から正解を導ける。導けないなら質問する。「意図がわからないから字面通りやる」は怠慢。

### 黙って突っ走らない
自走原則は「技術的に解決できることを聞くな」であって「方向性の確認を省け」ではない。間違った方向に全力で走るのは、止まるより害が大きい。

### degraded mode 報告義務
本来の力を発揮できなかった場合、必ず報告: スキップされた工程 / なぜ / 具体的対策 / 品質差の見積もり。静かにdegradeして「できました」は禁止。
詳細: `.claude/knowledge/aipark-imports/degraded-mode-reporting.md`

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

1. `python3 scripts/update_crew_map.py` — クルーマップ自動更新
2. `git status` → 変更あり → `git add -A && git commit -m "sync: YYYY-MM-DD" && git push origin main`
3. うまくいかなかったSkillがあれば改善提案

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

全体目次: `.claude/knowledge/INDEX.md`

| ファイル | 用途 | 読むタイミング |
|---|---|---|
| pak-philosophy.md | マーケ哲学（全判断基準） | クリエイティブ制作・評価時 |
| hook-db.md | フックコピーDB | フック設計・評価時 |
| cta-db.md | CTAコピーDB | CTA設計・評価時 |
| park-architecture.md | Park Skills設計原則 | スキル新規作成・改善時 |
| aipark-imports/ | パク1.2.5輸入 判断階層・Vector-First憲法 等8ファイル | CR評価・データ設計・Agent新規作成時 |

### クライアント（clients/）

登録済み: sawada / sawada-co / ameru / gungun / onmyskin / proust / camicks / mauri / yomite / sakura

---

## 4. 技術設定

- 同期: `./sync.sh [pull|push|status]`（起動時auto-pull / 終了時auto-push）
- 出力先: `reports/` / `banner-park/output/` / `video-ai/output/`
- 環境変数: GEMINI_API_KEY_1〜3 / XAI_API_KEY / FISH_AUDIO_API_KEY（~/.zshrc）
