# 記事オファークルー ver.1.0 — 着地CVR直結 × 購買衝動スコア算出

> CKO配下 AGENT 05。通常は `/kiji-cko` 経由で自動起動される。
> 本体: `.claude/agents/kiji-offer-crew.md`

単独で起動した場合、Agent tool で 'kiji-offer-crew' エージェントを実行する。

## 単独起動時の入力

Agent tool 起動時に以下を渡す:

```json
{
  "n1_profile": "（ターゲット属性・悩み）",
  "agent_directives": { "offer": "（追加指示があれば）" },
  "article_text": "（記事テキスト全文・特にオファー部分）"
}
```

## 評価軸（概要）

| 軸 | 配点 |
|---|---|
| 価格魅力度 | 40% |
| 緊急性・希少性 | 25% |
| 特典設計 | 20% |
| 縛りなし設計 | 15% |

GO基準: `offer_score >= 70`
ボーナス: 縛りなし明記 → +15点

詳細な評価ロジック・出力フォーマットは agents/ 本体を参照。