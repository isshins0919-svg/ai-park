# 記事信頼君 ver.1.0 — 着地CVR直結 × 3層信頼スコア算出

> CKO配下 AGENT 03。通常は `/article-fb-cmo` 経由で自動起動される。
> 本体: `.claude/agents/article-fb-trust.md`

単独で起動した場合、Agent tool で `article-fb-trust` エージェントを実行する。

## 単独起動時の入力

Agent tool 起動時に以下を渡す:

```json
{
  "n1_profile": "（ターゲット属性・悩み）",
  "agent_directives": { "trust": "（追加指示があれば）" },
  "article_text": "（記事テキスト全文）"
}
```

## 評価軸（概要）

| 軸 | 配点 |
|---|---|
| 権威層 (Authority) | 35% |
| 証拠層 (Evidence) | 35% |
| 口コミ層 (Social Proof) | 30% |

GO基準: `trust_score >= 70`
ボーナス: 権威が記事1/3以内に登場 → +10点

詳細な評価ロジック・出力フォーマットは agents/ 本体を参照。