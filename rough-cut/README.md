# rough-cut: トーク動画ラフカット自動化

Claude Code で動画編集を自動化するスキルです。

## できること

- 無音カット (Silero VAD)
- フィラーカット (「えーと」「あのー」等)
- リテイク検出 (言い直し・カット指示)
- 文字起こし + テロップ自動生成
- テロップ改行最適化 (BudouX + DP)
- 漢数字→算用数字変換
- 句読点削除
- MP4書き出し

縦型 (TikTok/Shorts) も横型 (YouTube) も自動判定で対応。

## 必要なもの

- Claude Code (Pro/Max)
- Python 3.11+
- FFmpeg
- Node.js 18+
- ElevenLabs アカウント (無料プランOK)

## 使い方

1. このフォルダを Claude Code で開く
2. `/setup` で初回セットアップ
3. `/generate ~/Desktop/動画.mp4` で実行

詳細は CLAUDE.md を参照。
