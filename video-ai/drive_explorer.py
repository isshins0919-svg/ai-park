"""
Drive Explorer — プルーストクリーム2 素材確認スクリプト
"""

import json
from googleapiclient.discovery import build
from google.oauth2 import service_account

# ===== 設定 =====
SERVICE_ACCOUNT_FILE = "/Users/ca01224/Downloads/claude-x-api-51b0d4975bbb.json"
ROOT_FOLDER_ID = "1SIxc9PmxvITFl-Om31zbc961miNFWpw0"  # 好調クリエイティブフォルダ

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# ===== 認証 =====
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("drive", "v3", credentials=creds)


def list_items(folder_id, name="ROOT"):
    """フォルダの中身を一覧表示"""
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType, size, modifiedTime)",
        pageSize=100,
    ).execute()

    items = results.get("files", [])
    print(f"\n📁 {name} ({len(items)}件)")
    print("-" * 50)

    folders = []
    videos = []
    images = []
    others = []

    for item in items:
        mime = item["mimeType"]
        if mime == "application/vnd.google-apps.folder":
            folders.append(item)
        elif "video" in mime:
            videos.append(item)
        elif "image" in mime:
            images.append(item)
        else:
            others.append(item)

    for f in folders:
        print(f"  📁 {f['name']}  (id: {f['id']})")
    for v in videos:
        size_mb = int(v.get("size", 0)) / 1024 / 1024
        print(f"  🎬 {v['name']}  ({size_mb:.1f}MB)")
    for i in images:
        print(f"  🖼  {i['name']}")
    for o in others:
        print(f"  📄 {o['name']}  ({o['mimeType']})")

    return folders, videos, images


# ===== 実行 =====
print("=" * 50)
print("Drive Explorer — 好調クリエイティブフォルダ")
print("=" * 50)

# まずルートフォルダのサブフォルダ一覧
folders, videos, images = list_items(ROOT_FOLDER_ID)

# サブフォルダの中も全部表示
for folder in folders:
    sub_folders, sub_videos, sub_images = list_items(folder["id"], folder["name"])
    # さらに深いネストがあれば
    for sf in sub_folders:
        list_items(sf["id"], f"{folder['name']} / {sf['name']}")

print("\n" + "=" * 50)
print("✅ 完了")
