# 記事CTAクルー ver.1.0 — mCVR直結 × CTA必然性スコア

> CKO配下 AGENT 04。通常は `/kiji-cko` 経由で自動起動される。
> 本体: `.claude/agents/kiji-cta-crew.md`

単独で起動した場合、Agent tool で 'kiji-cta-crew' エージェントを実行する。

## 単独起動時の入力

Agent tool 起動時に以下を渡す:

```json
{
  "n1_profile": "（ターゲット属性・悩み）",
  "agent_directives": { "cta": "（追加指示があれば）" },
  "article_text": "（記事テキスト全文）"
}
```

## 評価軸（概要）

| 軸 | 配点 |
|---|---|
| CTA本数 | 25% |
| 配置 (黄金比) | 25% |
| 文言強度 | 30% |
| 必然性 (感情連動) | 20% |

GO基準: `cta_score >= 80`
ボーナス: アンケート/クーポン型あり → +5点

詳細な評価ロジック・出力フォーマットは agents/ 本体を参照。