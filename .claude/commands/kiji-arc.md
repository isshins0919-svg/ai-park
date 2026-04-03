# 記事アーククルー ver.1.0 — mCVR+着地CVR × 感情アーク設計評価

> CKO配下 AGENT 02。通常は `/kiji-cko` 経由で自動起動される。
> 本体: `.claude/agents/kiji-arc-crew.md`

単独で起動した場合、Agent tool で 'kiji-arc-crew' エージェントを実行する。

## 単独起動時の入力

Agent tool 起動時に以下を渡す:

```json
{
  "n1_profile": "（ターゲット属性・悩み）",
  "agent_directives": { "narrative": "（追加指示があれば）" },
  "article_text": "（記事テキスト全文 or セクション構成）"
}
```

## 評価軸（概要）

| 軸 | 配点 |
|---|---|
| V字アーク完成度 | 40% |
| 中だるみ検出 | 30% |
| 新認識フック数 | 20% |
| 感情温度変化 | 10% |

GO基準: `narrative_score >= 70`

詳細な評価ロジック・出力フォーマットは agents/ 本体を参照。