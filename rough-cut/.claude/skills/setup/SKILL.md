# Skill: setup

初回セットアップを案内する。ユーザーが初めてこのスキルを使う時に実行。

## 実行条件

以下のいずれかが未完了の場合に実行:
- `.venv/` が存在しない
- `remotion/node_modules/` が存在しない
- `.env` が存在しない

## 手順

### Step 1: 環境確認

以下がインストールされているか確認:

```bash
python3.11 --version   # 3.11 以上
ffmpeg -version         # 必須
node --version          # 18 以上
```

未インストールの場合、案内:
- **Python 3.11**: `brew install python@3.11`
- **FFmpeg**: `brew install ffmpeg`
- **Node.js**: `brew install node` または https://nodejs.org/

### Step 2: ElevenLabs API キー取得

ElevenLabs の Speech-to-Text (文字起こし) API を使用する。API キーが必要。

ユーザーに以下を案内:

1. https://elevenlabs.io/ にアクセスしてアカウント作成 (無料プランでOK)
2. ログイン後、左サイドバーの「Developers」をクリック
3. 「API Keys」タブを開く
4. 「Create API Key」ボタンでキーを生成
5. 表示されたキーをコピー (一度しか表示されない)

無料プランで月20分の音声文字起こしが可能。
10分の動画1本で約10分消費する (動画の長さ分)。
有料プラン (Starter $5/月~) でより多くの分数が使える。

### Step 3: Python 環境セットアップ

```bash
cd {rough-cut ディレクトリ}
python3.11 -m venv .venv
source .venv/bin/activate

# 基本パッケージ
pip install -r python/requirements.txt

# PyTorch CPU版 (Silero VAD 用)
# *** 必ず --extra-index-url を付ける。付けないと CUDA 版 (10GB) がインストールされる ***
pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
```

PyTorch CPU版は約200MB。初回のみ時間がかかる。

### Step 4: Remotion セットアップ

```bash
cd remotion
npm install
cd ..
```

### Step 5: .env 設定

```bash
cp .env.example .env
```

.env を開いて ElevenLabs API キーを設定:
```
ELEVEN_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 6: 動作確認

Silero VAD モデルの初回ダウンロードを実行:

```bash
source .venv/bin/activate
cd python
PYTHONPATH=. ../.venv/bin/python -c "import torch; torch.hub.load('snakers4/silero-vad', 'silero_vad', trust_repo=True); print('Silero VAD OK')"
```

初回は torch.hub からモデルをダウンロードする (約10MB)。「Silero VAD OK」と表示されれば成功。

### 完了メッセージ

セットアップ完了後、ユーザーに以下を伝える:

```
セットアップ完了しました。

使い方:
  /generate {動画ファイルパス}

例:
  /generate ~/Desktop/talk_video.mp4

縦型 (TikTok/Shorts) も横型 (YouTube) も自動判定で対応します。
```
