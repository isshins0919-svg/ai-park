"""
プルースト2 好調CR — ファイル名パターン分析
FV × SV × 台本 × 動画タイプの組み合わせを抽出
"""

import re
import json
from collections import Counter, defaultdict
from googleapiclient.discovery import build
from google.oauth2 import service_account
import warnings
warnings.filterwarnings("ignore")

SERVICE_ACCOUNT_FILE = "/Users/ca01224/Downloads/claude-x-api-51b0d4975bbb.json"
PROUST2_FOLDER_ID = "1CuHUqUbf50JL68dQ-_SDhFFUk11oq2LK"

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
service = build("drive", "v3", credentials=creds)


def get_all_videos(folder_id):
    """フォルダ配下の全動画を再帰取得"""
    videos = []
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType, modifiedTime)",
        pageSize=200,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
    ).execute()

    for item in results.get("files", []):
        if item["mimeType"] == "application/vnd.google-apps.folder":
            videos.extend(get_all_videos(item["id"]))
        elif "video" in item["mimeType"] or "vid" in item["mimeType"]:
            videos.append(item)

    return videos


def parse_filename(name):
    """ファイル名からFV/SV/台本/タイプを抽出"""
    info = {"raw": name, "fv_num": None, "fv_text": None, "sv_num": None,
            "sv_text": None, "d_num": None, "type": None, "talent": None}

    # FV番号とテキスト
    fv_match = re.search(r"FV(\d+)[_　]([^_　SV]+)", name)
    if fv_match:
        info["fv_num"] = int(fv_match.group(1))
        info["fv_text"] = fv_match.group(2).strip()

    # SV番号とテキスト
    sv_match = re.search(r"SV(\d+)[_　]([^_　d\d]+)", name)
    if sv_match:
        info["sv_num"] = int(sv_match.group(1))
        info["sv_text"] = sv_match.group(2).strip()

    # 台本番号
    d_match = re.search(r"_d(\d+)", name)
    if d_match:
        info["d_num"] = d_match.group(1)

    # 動画タイプ
    if "AI医者" in name:
        info["type"] = "AI医者"
    elif "AI女性" in name:
        info["type"] = "AI女性"
    elif "ツボ君" in name or "ツボ" in name:
        info["type"] = "ツボ君"
    elif "語り" in name:
        info["type"] = "語り"
    else:
        info["type"] = "その他"

    # 出演者
    talents = ["ちゃそ", "北口", "シーナ", "daigo", "nanae", "kira"]
    for t in talents:
        if t in name:
            info["talent"] = t
            break

    return info


# === 実行 ===
print("プルースト2 好調CR — パターン分析")
print("=" * 60)

videos = get_all_videos(PROUST2_FOLDER_ID)
print(f"\n総動画数: {len(videos)}本\n")

parsed = [parse_filename(v["name"]) for v in videos]

# 1. 動画タイプ分布
print("【動画タイプ分布】")
types = Counter(p["type"] for p in parsed)
for t, c in types.most_common():
    bar = "█" * c
    print(f"  {t:10s} {bar} {c}本")

# 2. FVフック分布
print("\n【FVフック（上位）】")
fv_texts = [p["fv_text"] for p in parsed if p["fv_text"]]
fv_counter = Counter(fv_texts)
for text, count in fv_counter.most_common(10):
    print(f"  {count}回 | {text}")

# 3. SVボディ分布
print("\n【SVボディ（上位）】")
sv_texts = [p["sv_text"] for p in parsed if p["sv_text"]]
sv_counter = Counter(sv_texts)
for text, count in sv_counter.most_common(10):
    print(f"  {count}回 | {text}")

# 4. 勝ち組み合わせ（FV × SV）
print("\n【FV × SV 組み合わせ（上位）】")
combos = Counter(
    f"FV{p['fv_num']}_{p['fv_text']}  ×  SV{p['sv_num']}_{p['sv_text']}"
    for p in parsed if p["fv_num"] and p["sv_num"]
)
for combo, count in combos.most_common(8):
    print(f"  {count}回 | {combo}")

# 5. 出演者分布
print("\n【出演者分布】")
talents = Counter(p["talent"] for p in parsed if p["talent"])
for t, c in talents.most_common():
    print(f"  {t:10s} {c}本")

# JSONで保存
output = {
    "total": len(videos),
    "types": dict(types),
    "fv_patterns": dict(fv_counter.most_common(20)),
    "sv_patterns": dict(sv_counter.most_common(20)),
    "top_combos": dict(combos.most_common(10)),
    "talents": dict(talents),
    "all_videos": parsed,
}
with open("video-ai/proust2_analysis.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n✅ 分析完了 → video-ai/proust2_analysis.json に保存")
