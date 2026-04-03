# 記事競合君 ver.1.0 — mCVR+着地CVR × DPro benchmark.json 勝ちパターン実装率

> CKO配下 AGENT 06。通常は `/article-fb-cmo` 経由で自動起動される。
> 本体: `.claude/agents/article-fb-competitive.md`

単独で起動した場合、Agent tool で `article-fb-competitive` エージェントを実行する。

## 単独起動時の入力

Agent tool 起動時に以下を渡す:

```json
{
  "genre": "（ジャンル名）",
  "article_text": "（記事テキスト全文）"
}
```

## 評価軸（概要）

| 軸 | 配点 |
|---|---|
| 勝ちパターン実装率 | 60% |
| 競合差分の少なさ | 40% |

GO基準: `competitive_score >= 65`
データソース: `.claude/scripts/dpro_benchmark.json`

詳細な評価ロジック・出力フォーマットは agents/ 本体を参照。