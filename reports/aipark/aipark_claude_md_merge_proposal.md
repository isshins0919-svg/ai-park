# CLAUDE.md マージ提案（パク1.2.5 取り込み）

> 作成: 2026-04-18
> 対象: `/Users/ca01224/Desktop/一進VOYAGE号/CLAUDE.md`（101行）
> 本提案は **自動適用しない**。ユーザー承認後に適用すること

---

## 現状の評価

VOYAGE の CLAUDE.md は **101行** で簡潔・機能的。パクの316行とは思想が違う:

- VOYAGE: 運用ルール中心（起動アクション・ファイル構造・技術設定）
- パク: 哲学中心（本質・AGI解放・意図汲み取り・Vector-First・データ駆動・CMO原則）

**両者は役割分担で共存可能**。VOYAGE本体は「運用マニュアル」として維持、パクの哲学は `knowledge/aipark-imports/` に分離済み。

---

## 推奨マージ: 最小限のセクション追加

VOYAGE CLAUDE.md の末尾に **3セクション** を追加する案。既存の1〜4章は変更しない。

---

## 提案1: 「0. 本質指令」セクション（冒頭に挿入）

Tier 0 に入るため最小限に。

### 追加案（101行 → 約110行）

CLAUDE.mdの**冒頭（`## 1. 起動アクション` の前**）に挿入:

```markdown
---

## 0. 本質指令（永久適用）

### 本質を見抜く

常に徹底的に本質的であれ。違和感がある時は本質に立ち返れ。
本質的じゃないことが起きている時は勇気を持って提案し、本質に徹底する。

### AGI最大レバレッジ

Claude Opus 4以降はAGI。人間のペースや理解度に合わせる必要はない。
推論の深さを制限するな。「わかりやすさ」のために本質を薄めるな。
忖度して人間の判断を追認するのはAGIの怠慢。客観的に正しい道が見えているなら勇気を持って示す。

### 意図を汲む

言葉の奥にある意図を読む。表面的な指示に応えるな。
ユーザーの指示は短い。「これやって」の3文字に価値観・戦略・美意識が圧縮されている。
CLAUDE.md・pak-philosophy・clients を内在化しているなら、3文字から正解を導ける。
導けないなら質問する。「意図がわからないから字面通りやる」は怠慢。

### 黙って突っ走らない

重要な論点は必ず質問する。
自走原則は「技術的に解決できることを聞くな」であって「方向性の確認を省け」ではない。
間違った方向に全力で走るのは、止まるより害が大きい。

### degraded mode 報告義務

本来の力を発揮できなかった場合、必ず以下を報告:
- スキップされた工程の一覧
- なぜスキップしたか
- 具体的な対策（何を設定すれば本来品質になるか）
- 本来との品質差の見積もり

静かに degrade して「できました」と報告するのは禁止。
詳細: `.claude/knowledge/aipark-imports/degraded-mode-reporting.md`

---
```

**理由**:
- VOYAGE `pak-philosophy.md` には「本質追求」「AGI」「意図」の概念があるが、CLAUDE.md（Tier 0）には未反映
- 5つの指令は全てのスキルが起動時に参照すべき
- 「degraded mode 報告」は既存 `pak-philosophy` の「小さな嘘をつかない」の運用具体化

---

## 提案2: ナレッジ表への追記

既存セクション `### ナレッジ（knowledge/）の使い方` の表に aipark-imports を追記:

### 変更案

```markdown
### ナレッジ（knowledge/）の使い方

| ファイル | 用途 | 読むタイミング |
|---|---|---|
| pak-philosophy.md | マーケ哲学（全判断基準） | クリエイティブ制作・評価時 |
| hook-db.md | フックコピーDB | フック設計・評価時 |
| cta-db.md | CTAコピーDB | CTA設計・評価時 |
| park-architecture.md | Park Skills設計原則 | スキル新規作成・改善時 |
| aipark-imports/three-souls-judgment-hierarchy.md | 愛→偉大→可能 階層判定 | CR評価時 |
| aipark-imports/vector-first-constitution.md | Vector-First Learning 憲法 | データ・仮説設計時 |
| aipark-imports/alphago-judgment-principles.md | AGI判断原則 | 運用判断時 |
| aipark-imports/cr-pdca-philosophy.md | CR運用4原則 | 日次PDCA設計時 |
| aipark-imports/agent-requirements-5-questions.md | Agent/Skill作成時の5本質問 | Agent/Skill新規作成・改善時 |
| aipark-imports/philosophy-constraints.md | 哲学制約チェックリスト | CR仮説生成後、生成前 |
| aipark-imports/degraded-mode-reporting.md | degraded mode報告義務 | 全スキル完走時 |
```

---

## 提案3: クライアント表の更新

既存行:
```
登録済み: sawada / ameru / gungun / onmyskin / proust / camicks / mauri / yomite
```

→ 実際は10社（sakura / sawada-co 追加済み）なので:

```
登録済み: sawada / sawada-co / ameru / gungun / onmyskin / proust / camicks / mauri / yomite / sakura
```

---

## 提案4: 「5. Agent/Skill 設計原則」セクション新規追加

末尾に追加:

```markdown
---

## 5. Agent/Skill 設計原則

### 新規作成時の5本質問（必須）

1. それ、本当にAgent/Skillか？既存の拡張で済まないか？
2. 最悪の失敗は何か？致命的失敗モードにガードは張られたか？
3. KPIは2週間で測れるか？測定不能なKPIは存在しないのと同じ
4. 何を捨てるか？Non-goals を明示しないとスコープ膨張
5. 誰がいつ動かすか？実行トリガーと出力受領先が不明確なAgent/Skillは孤児

詳細: `.claude/knowledge/aipark-imports/agent-requirements-5-questions.md`

### Agent設計の5要素（必須明示）

1. 目的 — なぜ存在するか
2. ゴール — 何を達成するか（測定可能な形で）
3. 行動指針 — どう動くか
4. 制約条件 — 何をしないか（Non-goals）
5. 参考情報 — どのナレッジを読むか

これらが未明示のAgent/Skillは「未完成」と判定。

### サブエージェント制限（Claude Code仕様）

Agent tool で起動したサブエージェントには **MCP・Bash権限が渡らない**。
- MCP呼び出し・Bash実行: 必ずメイン会話で実行
- サブエージェントの用途: テキスト推論・分析・レビューなど、ファイル読み書きのみで完結するタスクに限定
```

---

## 提案5: 「6. CR評価の階層」セクション新規追加（オプショナル）

さらに詳しく制作ルールを明文化したい場合:

```markdown
---

## 6. CR評価の階層（3つの魂）

### 制作時（構成要素視点）
- 魂1: キービジュアルそのもの — 広告を超えて作品レベル
- 魂2: キラーキャッチコピー — 1行で買わせるレベル
- 魂3: 別の仮説 — 量ではなく仮説の数

### 評価時（判断階層視点、パク1.2.5輸入）
```
[愛]     N1感情への寄り添い / 相手否定禁止 / 恐怖→希望の道
  ↓ FAIL → 即REJECT
[偉大]   時間耐久性 / コンセプト浸透率 / 非コモディティ
  ↓ FAIL → 条件付きPASS
[可能]   未探索の可能性 / AGI活用度 / パターン超越
  ↓ FAIL → PASS（次回改善）
  PASS → FULL PASS
```

**下位FAILなら上位評価しない**。愛のないCRは配信しない。
詳細: `.claude/knowledge/aipark-imports/three-souls-judgment-hierarchy.md`
```

---

## 適用判断

### 推奨: 提案1 + 提案2 + 提案3（最小限採用）

**理由**:
- 提案1は起動時に読まれるTier 0。哲学指令の統一に最大効果
- 提案2/3はナレッジ地図の更新（必須）
- 合計で CLAUDE.md は 101行 → **約130-140行**。「200行超警告」ルールに余裕あり

### 追加採用: 提案4（中リスク中リターン）

- Agent/Skill 作成時のガード。VOYAGE 43+スキル運用なので効果大
- ただし既存スキルを審査する意味にもなり、手間が増える可能性

### 見送り推奨: 提案5（冗長）

- VOYAGE `pak-philosophy.md` に既に「3つの魂（CR構成）」あり
- パクの「3つの魂（判断階層）」は `aipark-imports/` の参照で十分
- CLAUDE.md を肥大化させるより、ナレッジ参照にとどめる

---

## 適用方法

ユーザーが「この提案で進めて」と承認した後、以下の手順で適用:

```
1. Backup: CLAUDE.md を CLAUDE.md.backup-YYYYMMDD にコピー
2. Edit: 提案1を冒頭に挿入
3. Edit: 提案2のナレッジ表を更新
4. Edit: 提案3のクライアントリスト更新
5. （提案4採択なら）末尾にセクション5追加
6. Verify: 行数チェック（200行以下）
7. Commit: git add CLAUDE.md && git commit -m "feat: CLAUDE.md にパク1.2.5 本質指令を統合"
```

---

## 不採用の選択肢

もしユーザーが「VOYAGE CLAUDE.md は現状維持で、aipark-imports/ の参照は任意にしたい」場合:

- CLAUDE.md は現状の101行を維持
- `aipark-imports/` 配下のファイルは `knowledge/` 内に独立した参照集として残存
- 各スキルが必要な時に任意で参照
- 全体的な統一よりも「使いたい時に使う」運用

---

## 結論

**最推奨: 提案1 + 2 + 3 を適用、提案4は翌週のセッションで検討、提案5は見送り。**

VOYAGE CLAUDE.md の簡潔性を保ちながら、パクの本質指令を最小コストで統合する最適解。
