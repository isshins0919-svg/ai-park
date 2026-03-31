# rough-cut: トーク動画ラフカット自動化スキル

動画を用意するだけ。無音カット、フィラーカット、リテイク検出、文字起こし、テロップ改行最適化、句読点削除、誤字脱字修正、MP4書き出し。全部自動。

## クイックスタート

```
# 初回セットアップ (未実行の場合)
/setup

# 動画をラフカット
/generate ~/Desktop/talk_video.mp4
```

## 環境要件

| 要件 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.11+ | パイプライン実行 |
| FFmpeg | 6+ | 音声抽出、セグメント分割 |
| Node.js | 18+ | Remotion レンダリング |
| ElevenLabs API Key | - | 文字起こし (STT) |

## セットアップ

初回は `/setup` を実行。以下が自動で案内される:
1. Python 3.11 / FFmpeg / Node.js の確認
2. ElevenLabs API キーの取得方法 (https://elevenlabs.io/ で無料登録)
3. Python venv + PyTorch CPU版 (Silero VAD用) のインストール
4. Remotion npm install
5. .env への API キー設定

### 手動セットアップ (上級者向け)

```bash
# Python
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r python/requirements.txt
pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cpu

# Remotion
cd remotion && npm install && cd ..

# API キー
cp .env.example .env
# .env の ELEVEN_API_KEY を設定
```

## パイプライン

| # | ステップ | 実行方式 | 説明 |
|---|---------|---------|------|
| 1 | preprocess | Python CLI | FFmpeg音声抽出 + 縦横自動判定 |
| 2 | stt | Python CLI | ElevenLabs word-level 文字起こし |
| 3 | vad | Python CLI | Silero VAD 無音区間検出 (ML高精度) |
| 4 | filler_detect | Python CLI | フィラー検出 (29パターン辞書) |
| 4b | filler_review | Claude Code | テキスト通し読みでフィラー確認・修正 |
| 5 | retake_detect | Claude Code | 言い直し・メタコメンタリー検出 |
| 6 | review | Claude Code | 誤字脱字修正 + 品質チェック |
| 7 | cut_proposal | Python CLI | 全結果統合→カット提案 (短セグメント自動マージ) |
| 8 | composition | Python CLI | テロップ生成 + セグメント分割 + 漢数字→算用数字変換 |
| 9 | preview | Remotion Studio | プレビュー確認 (レンダリング前に必ず実行) |
| 10 | render | Remotion CLI | MP4書き出し (concurrency=4固定) |

## 縦横自動判定

Step 1 で FFprobe + rotation 検出 → 自動で設定を切り替え:

| 設定 | 縦型 (9:16) | 横型 (16:9) |
|------|------------|------------|
| 解像度 | 1080x1920 | 1920x1080 |
| テロップ文字数 | 12字/行 | 16字/行 |
| テロップ位置 | 画面下 (0.75) | 画面下 (0.85) |
| DPペナルティ | 縦型最適化 | 横型最適化 |

iPhone縦撮り動画 (1920x1080 + rotation=-90) も正しく縦型と判定。

## テロップ品質

- overlay 2層方式 (stroke層 + fill層) で高品質な縁取り
- フォント: Zen Kaku Gothic Antique 900 (@remotion/google-fonts)
- 漢数字→算用数字の自動変換 (kanjize): 「三十八度」→「38度」
- 固有名詞の正式表記: 「YOUTUBE」→「YouTube」
- 句読点自動削除 (表示テキストから)
- BudouX + DP最適改行 (禁則処理付き)

## テキスト正規化

Step 8 で自動適用:
- 漢数字+助数詞 → 算用数字 (「千九百円」→「1900円」「1万フォロワー」)
- 固有名詞 (YouTube, Instagram, TikTok, X)

Step 6 (review) で Claude Code が追加修正:
- STT 誤認識の修正 (corrections)
- 話者名の正式表記

## プロジェクト設定

`templates/` にYAML設定ファイル:
- `vertical.yaml` - 縦型動画用
- `horizontal.yaml` - 横型動画用

カスタマイズ可能な項目:
```yaml
telop:
  max_chars_per_line: 12    # 1行の最大文字数
  y_position: 0.75          # テロップ縦位置 (0.0=上, 1.0=下)
  font_size: 52              # フォントサイズ
  animation_in: "none"       # stamp | popIn | fadeIn | none
  animation_out: "none"      # popOut | fadeOut | none

edit:
  max_gap_ms: 600            # 無音カットの閾値 (ms)
  filler_confidence_threshold: 0.6  # フィラー判定の閾値

text_rules:
  corrections:               # STT誤認識の自動置換
    "間違い": "正しい"
  normalize_numbers: true    # 漢数字→算用数字
  normalize_proper_nouns: true  # 固有名詞正規化
```

## 出力構造

```
runs/{run_name}/
├── step01_preprocess/    audio.wav, preprocess.json (orientation含む)
├── step02_stt/           stt_result.json (words[], sentences[])
├── step03_vad/           vad_result.json (speech_segments[], silence_regions[])
├── step04_filler_detect/ fillers.json
├── step05_retake_detect/ retakes.json
├── step06_review/        review.json (corrections, quality_notes)
├── step07_cut_proposal/  cut_proposal.json (keep_segments[], stats)
├── step08_composition/   composition.json, segments/*.mp4
└── output/               final.mp4
```

## 注意事項

- Python は必ず `.venv/bin/python` を使う (system python 3.14 では動かない)
- PyTorch は `--extra-index-url .../cpu` で CPU版をインストール (CUDA版は10GB)
- Silero VAD は初回実行時にモデルをダウンロード (約10MB, 数秒)
- レンダリングの concurrency は 4 固定 (8以上で OffthreadVideo タイムアウト)
- Remotion Studio でプレビュー確認してからレンダリングする
- 長時間動画 (30分超) は STT API の消費分数に注意

## スキル一覧

| コマンド | 説明 |
|---------|------|
| `/setup` | 初回セットアップ (API キー取得案内含む) |
| `/generate {動画パス}` | ラフカット全自動実行 |
