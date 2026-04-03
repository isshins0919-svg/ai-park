# 記事フッククルー ver.1.0 — mCVR直結 × フック強度アナリスト

> CKO配下 AGENT 01。通常は `/kiji-cko` 経由で自動起動される。
> 本体: `.claude/agents/kiji-hook-crew.md`

単独で起動した場合、Agent tool で 'kiji-hook-crew' エージェントを実行する。

## 単独起動時の入力

Agent tool 起動時に以下を渡す:

```json
{
  "n1_profile": "（ターゲット属性・悩み）",
  "agent_directives": { "hook": "（追加指示があれば）" },
  "article_text": "（記事冒頭200文字）"
}
```

## 評価軸（概要）

| 軸 | 配点 |
|---|---|
| 悩み解像度 | 35% |
| N1自己投影度 | 35% |
| 感情温度 | 20% |
| 数字パワー | 10% |

GO基準: `hook_score >= 75`

詳細な評価ロジック・出力フォーマットは agents/ 本体を参照。