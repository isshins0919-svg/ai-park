"""
プルースト2 好調CR — 7本バッチ解析 → レポート生成
"""

import os, io, time, json, warnings
warnings.filterwarnings("ignore")

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import google.genai as genai

SERVICE_ACCOUNT_FILE = "/Users/ca01224/Downloads/claude-x-api-51b0d4975bbb.json"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY_1")

# ===== 解析対象7本（パターン最大化） =====
VIDEOS = [
    {
        "id": "1AjTkZmY9wNunKRPbTRfAPJtbn8XSNOby",
        "name": "FV123_インナーにワキガ臭_SV20_夏よりも冬_ツボ君_診察",
        "pattern": "AIキャラ×季節訴求",
        "mime": "video/mp4",
    },
    {
        "id": "1N9ieyDSCI9i5JolHbq05nWGsS3tEz49f",
        "name": "FV90_ワキガなのにインナー着てる_SV2_産後_通常語り_北口さん",
        "pattern": "通常語り×産後",
        "mime": "video/mp4",
    },
    {
        "id": "1BT4juSTHX_6bYk1deHN0poJLeicabx9F",
        "name": "AI医者_①",
        "pattern": "AI医者キャラ",
        "mime": "video/quicktime",
    },
    {
        "id": "1UI-QJ2Z4QkO4VKBDlfV9AQb13DNSnjqI",
        "name": "AI女性_①",
        "pattern": "AI女性キャラ",
        "mime": "video/quicktime",
    },
    {
        "id": "1J44ufZHMVlbkGodxtAj_L_qjDxpNw43O",
        "name": "FV4_耳垢型_SV1_お風呂入ってもワキ_通常語り",
        "pattern": "耳垢FV×語り",
        "mime": "video/mp4",
    },
    {
        "id": "1IauF_Ozb1Yrnf9htuzxkIcUjoaifoJtN",
        "name": "29_d4_ちゃそ_語り_耳掃除_FV4_本棚前",
        "pattern": "リアル出演者_ちゃそ",
        "mime": "video/mp4",
    },
    {
        "id": "1wXsjKVeSZiamF33tOKAqDzzcu9WM3NZP",
        "name": "0116_daigo_ツボ×グレーニット",
        "pattern": "男性出演者_daigo",
        "mime": "video/mp4",
    },
]

ANALYSIS_PROMPT = """
この動画は好調（高インプレッション）だったショート動画広告です。
以下を分析してJSON形式で返してください。

{
  "fv": {
    "hook_second": "フックテキストが出る秒数（数字のみ）",
    "hook_text": "冒頭のフックとなるセリフ/テキスト",
    "visual": "冒頭0-3秒の映像描写"
  },
  "body": {
    "structure": "悩み共感→解決策→証拠の流れを1-2行で",
    "key_message": "一番伝えたいメッセージ"
  },
  "telop": {
    "emphasis_style": "強調スタイル（色・サイズ・アニメーション）",
    "chars_per_screen": "1画面あたりの文字数（数字）",
    "layout": "2行表示と1行大文字の使い分けルール"
  },
  "tempo": {
    "cut_interval_sec": "平均カット間隔（秒数・数字のみ）",
    "rhythm": "テンポ感の特徴"
  },
  "cta": {
    "text": "最後のCTA文言",
    "start_second": "CTAが始まる秒数（数字のみ）"
  },
  "winning_reasons": ["勝ちの理由1", "勝ちの理由2", "勝ちの理由3"],
  "summary": "この動画の特徴を2行で"
}

JSONのみ返してください。説明文不要。
"""

# ===== 実行 =====
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
drive_service = build("drive", "v3", credentials=creds)
client = genai.Client(api_key=GEMINI_API_KEY)

results = []

for i, video in enumerate(VIDEOS):
    print(f"\n[{i+1}/7] {video['pattern']}: {video['name'][:40]}...")

    # Download
    local_path = f"/tmp/proust2_{i}.mp4"
    try:
        request = drive_service.files().get_media(
            fileId=video["id"], supportsAllDrives=True
        )
        fh = io.FileIO(local_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.close()
        size_mb = os.path.getsize(local_path) / 1024 / 1024
        print(f"  ✅ DL完了 ({size_mb:.0f}MB)")
    except Exception as e:
        print(f"  ❌ DL失敗: {e}")
        continue

    # Upload to Gemini
    try:
        with open(local_path, "rb") as f:
            uploaded = client.files.upload(
                file=f,
                config={"mime_type": video["mime"], "display_name": video["name"]}
            )
        while uploaded.state.name == "PROCESSING":
            time.sleep(3)
            uploaded = client.files.get(name=uploaded.name)
        print(f"  ✅ Geminiアップロード完了")
    except Exception as e:
        print(f"  ❌ アップロード失敗: {e}")
        continue

    # Analyze
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {"file_data": {"file_uri": uploaded.uri, "mime_type": video["mime"]}},
                ANALYSIS_PROMPT,
            ]
        )
        raw = response.text.strip().strip("```json").strip("```").strip()
        analysis = json.loads(raw)
        analysis["video_name"] = video["name"]
        analysis["pattern"] = video["pattern"]
        results.append(analysis)
        print(f"  ✅ 解析完了")
        client.files.delete(name=uploaded.name)
    except Exception as e:
        print(f"  ❌ 解析失敗: {e}")
        print(f"  raw: {response.text[:200] if 'response' in dir() else 'N/A'}")

    time.sleep(2)

# ===== 結果保存 =====
with open("video-ai/batch_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n\n✅ {len(results)}/7本 解析完了 → video-ai/batch_results.json")
print("次: python3 video-ai/generate_report.py")
