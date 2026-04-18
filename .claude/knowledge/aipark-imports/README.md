# AIパクくん1.2.5 輸入ナレッジ

> 出典: `~/Downloads/AIパクくん1.2.5/`
> 輸入日: 2026-04-18
> 輸入者: 解析セッション（Claude Opus）

---

## この配下にあるもの

VOYAGE号本体の哲学・ナレッジを補完するために、パクの配布版から **判断階層系** と **運用設計系** の思想ドキュメントを輸入したもの。

**既存の VOYAGE `pak-philosophy.md` は本体として尊重**。ここにあるのは追加レイヤー。

## ファイル一覧と使い分け

| ファイル | 使う場面 | 既存VOYAGEとの関係 |
|---|---|---|
| `three-souls-judgment-hierarchy.md` | CR評価時 | 既存「3つの魂（CR構成）」と補完 |
| `vector-first-constitution.md` | データ・仮説設計時 | `vector-utils.md` / `ccdd-strategy.md` の実装指針 |
| `alphago-judgment-principles.md` | 運用判断時 | 運用系スキルに組み込む思想 |
| `cr-pdca-philosophy.md` | 日次PDCA設計時 | CMO/船長系スキル参照 |
| `agent-requirements-5-questions.md` | 新Agent/Skill作成時 | `/agent-factory` 的ワークフロー |
| `philosophy-constraints.md` | 品質検証時 | gate-* クルー共通参照 |
| `degraded-mode-reporting.md` | スキル完了時 | 全スキル共通の報告義務 |

## 輸入ポリシー

- **パクの哲学を丸呑みしない**。VOYAGE独自の文化（船長・クルー・甲板）を維持しつつ、本質を取り込む
- **再輸入前提**: パクの版が更新されたら、差分を確認して選択的に再輸入
- **VOYAGEが既に持っている思想は輸入しない**。重複は避ける

## 次のステップ

これらを起点に:
- CLAUDE.md マージ提案（`reports/aipark_claude_md_merge_proposal.md`）
- Phase B/C/D/E の段階導入（`reports/aipark_1.2.5_diff_map.md` 参照）
