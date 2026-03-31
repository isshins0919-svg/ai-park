"""
Gemini 動画解析 — プルースト2 好調CR 1本分析
対象: FV123_インナーにワキガ臭_SV20_夏よりも冬_d30_台本4冬_ツボ君_診察.mp4
"""

import os
import io
import time
import warnings
warnings.filterwarnings("ignore")

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import google.genai as genai

SERVICE_ACCOUNT_FILE = "/Users/ca01224/Downloads/claude-x-api-51b0d4975bbb.json"
VIDEO_FILE_ID = "1AjTkZmY9wNunKRPbTRfAPJtbn8XSNOby"  # 25.12.23版
VIDEO_NAME = "FV123_インナーにワキガ臭_SV20_夏よりも冬_d30_台本4冬_ツボ君_診察.mp4"
LOCAL_PATH = "/tmp/proust2_sample.mp4"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY_1")

# ===== Step 1: Drive から動画ダウンロード =====
print(f"Step 1: Drive からダウンロード中...")
print(f"  {VIDEO_NAME}")

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
drive = build("drive", "v3", credentials=creds)

request = drive.files().get_media(fileId=VIDEO_FILE_ID, supportsAllDrives=True)
fh = io.FileIO(LOCAL_PATH, "wb")
downloader = MediaIoBaseDownload(fh, request)

done = False
while not done:
    status, done = downloader.next_chunk()
    print(f"  ダウンロード中... {int(status.progress() * 100)}%", end="\r")

fh.close()
size_mb = os.path.getsize(LOCAL_PATH) / 1024 / 1024
print(f"\n  完了 ({size_mb:.1f}MB) → {LOCAL_PATH}")

# ===== Step 2: Gemini Files API にアップロード =====
print(f"\nStep 2: Gemini にアップロード中...")
client = genai.Client(api_key=GEMINI_API_KEY)

with open(LOCAL_PATH, "rb") as f:
    uploaded = client.files.upload(
        file=f,
        config={"mime_type": "video/mp4", "display_name": VIDEO_NAME}
    )

print(f"  アップロード完了: {uploaded.name}")

# 処理待ち
print("  Gemini処理待ち...", end="")
while uploaded.state.name == "PROCESSING":
    time.sleep(3)
    uploaded = client.files.get(name=uploaded.name)
    print(".", end="", flush=True)
print(" 完了")

# ===== Step 3: Gemini で解析 =====
print(f"\nStep 3: 動画解析中...")

PROMPT = """
この動画は、好調（高インプレッション）だったショート動画広告です。
以下の観点で詳細に分析してください。

## 分析項目

### 1. FV（ファーストビュー）分析
- 冒頭0〜3秒で何が映っているか
- フックとなるセリフ・テキストは何秒に登場するか
- 視聴者を止めるための工夫は何か

### 2. ボディ構成
- FV後の展開（何を伝えているか）
- 悩み共感 → 解決策 → 証拠 の流れを秒数付きで

### 3. テロップスタイル
- 強調されているワード（大文字・色・アニメーション）
- テロップの文字量（1画面に何文字程度か）
- 2行表示 vs 1行大文字 の使い分けパターン

### 4. カット・テンポ
- 平均カット間隔（何秒に1カット程度か）
- テンポの緩急（速い部分・遅い部分）

### 5. 音声・BGM
- ナレーションのトーン（落ち着き / 感情的 / 親しみやすい）
- BGMの特徴

### 6. CTA（クロージング）
- 最後の誘導文言
- 何秒から始まるか

### 7. この動画が「好調だった理由」の仮説
- 3つ以内で簡潔に

出力は日本語で、マークダウン形式でお願いします。
"""

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        {"file_data": {"file_uri": uploaded.uri, "mime_type": "video/mp4"}},
        PROMPT,
    ]
)

print("\n" + "=" * 60)
print("【Gemini 動画解析結果】")
print("=" * 60)
print(response.text)

# 結果保存
output_path = "video-ai/proust2_gemini_analysis.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(f"# Gemini動画解析: {VIDEO_NAME}\n\n")
    f.write(response.text)

print(f"\n✅ 保存完了 → {output_path}")

# クリーンアップ
client.files.delete(name=uploaded.name)
