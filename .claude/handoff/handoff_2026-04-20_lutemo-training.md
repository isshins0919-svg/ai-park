# HANDOFF — 2026-04-20 Lutemo研修 緊急モード

## 🚨 状況
- 本番: **2026-04-29（水）対面** — Lutemo社員3名（ほぼ初心者）
- Lutemo社: Amazon EC運用 + 運用代行 + EC分析ツール開発・提供
- 残り日数: **9日**（AIセッションで動ける実働6日）

## 📅 スケジュール（決定済み）
| 日付 | タスク | 担当 |
|---|---|---|
| 4/20(月) | 方向性合意・スケジュール確定 | ✅ 完了 |
| 4/21(火) | ch04-ch06 実装 | AI |
| 4/22(水) | ch07-ch10 + completion 実装 / Amazon EC文脈調整 | AI |
| 4/23(木) 9:00 | **🏃 練習通し①** 理解フェーズ | 一進さん（scheduled-task登録済） |
| 4/24(金) | FB反映 + HTMLスライド化 + Lutemoスターターキット | AI |
| 4/25(土) 9:00 | **🏃 練習通し②** ハンズオン込み | 一進さん（scheduled-task登録済） |
| 4/26(日) | アンケートSkill + 磨き込み | AI |
| 4/27(月) 9:00 | **🏃 最終リハ** 時間配分確認 | 一進さん（scheduled-task登録済） |
| 4/28(火) | 最終調整・機材確認・バックアップ準備 | 両方 |
| 4/29(水) | 🎯 **本番** | 一進さん |

## 現在の完成状況
### ✅ 完成済み（Lutemoブランド化・オーシャンテーマ化済、ユーザー編集あり）
- style.css（オーシャンテーマ、island1-10カラー、glossary追加）
- index.html（11島構成、LUTEMO AI VOYAGE ブランド）
- ch00-prologue.html（Claude3兄弟・なぜ今・Lutemo未来像・Amazon活用例）
- ch01-agent-anatomy.html（7パーツ + glossary）
- ch02-prompt-engineering.html（5要素 + Shot + glossary）
- ch03-mcp-tools.html（MCP概念 + glossary）

### 🚧 要実装/確認
- ch04-skill-design.html（Part2後半ベース・初期版あり → Amazon EC文脈反映要）
- ch05-agent-architecture.html（初期版あり → 要確認）
- ch06-context-management.html（初期版あり → 要確認）
- ch07-embedding.html（初期版あり → 要確認・初心者向けに簡素化検討）
- ch08-feedback-loops.html（初期版あり → 要確認）
- ch09-marketing-ai.html（初期版あり → **Amazon EC運用に全面刷新**）
- ch10-capstone.html（初期版あり → 要確認）
- completion.html（初期版あり → 要確認）

## 🎯 Lutemo向け最優先調整ポイント

### 1. Amazon EC運用寄せ（ch09 最重要）
現状のch09はマーケ全般。Lutemo向けに全面刷新:
- 商品タイトル最適化
- 箇条書き・A+コンテンツ生成
- 広告データ分析
- レビュー分析
- 競合調査自動化
- バナー・画像ABテスト量産

Prologueのユースケース表（242-252行目）が参考になる。

### 2. デスクトップアプリ中心 + ターミナル補助
一進さんと同じ環境で進める。VS Code拡張の推しは軽めでOK。
ch03(MCP)やch04(Skill)の導入でデスクトップアプリ起点の説明にする。

### 3. Anthropic最新機能の反映
- **Checkpoints / `/rewind`** — ch01 or ch02 で「壊しても戻せる」安心感を伝える
- **Plan Mode** — ch02 or ch04 で暴走防止の安全装置として
- **Skills エコシステム**（pptx/pdf/xlsx/docx/skill-creator等） — ch04 で紹介
- **Sonnet 4.6 / Opus 4.7** — Prologue で一瞬触れる

### 4. HTMLスライド化（4/24 以降）
一進さんの希望: 資料は1つに集約、HTMLでスライドのような流れ。
- キーボード ← → で送れるナビゲーション
- 1チャプター = スライド数枚ぶん
- 既存のHTMLをスライド送り式に改造

### 5. Lutemo用スターターキット（4/24 以降）
既存の `reports/textbook/starter-kit/` をLutemo向けにカスタム:
- CLAUDE.md テンプレート（Amazon EC運用代行チーム向け）
- Amazon商品ページ最適化Skillの雛形
- 競合調査Skillの雛形
- よく使うMCP接続ガイド（Slack, Google, Amazon関連）

### 6. 研修後アンケートSkill（4/26 以降・余裕あれば）
スキル定着確認用。シンプルに:
- 今日学んだことで一番印象的だったのは？
- 月曜から業務で使いたいものは？
- 詰まったポイントは？

## ⚡ 次セッション(4/21予定)の最優先タスク
1. ch04-skill-design.html の現状確認 + Lutemo(Amazon EC)文脈反映
2. ch05-agent-architecture.html の現状確認
3. ch06-context-management.html の現状確認
4. 時間あれば ch07 も

すべて **Amazon EC運用の具体例に差し替える** のが重要ポイント。

## 注意点・degraded mode 反省
- 今回、私(AI)が「4/29」を「7/29」と勘違いしたコンテキストに引っ張られ、ユーザー発言を疑わず受け入れた
- 本質突っ込みルール適用: 日付が出たら必ず「今日からの残日数」を計算して違和感チェック
- 今後、重要な日付・数値は復唱して確認する

## scheduled-tasks 登録済み
- `lutemo-rehearsal-1-understanding` — 4/23 9:00
- `lutemo-rehearsal-2-handson` — 4/25 9:00
- `lutemo-rehearsal-3-final` — 4/27 9:00

## 次セッション用ワンライナー
> `.claude/handoff/handoff_2026-04-20_lutemo-training.md` を読んで、Lutemo研修（4/29本番）の準備続き。今日は ch04-ch06 を Amazon EC文脈に調整しながら実装・確認する。
