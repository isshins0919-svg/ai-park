#!/usr/bin/env python3
"""KOSURIちゃんのキャラクター画像を Gemini で生成する。
出力: video-ai/fv_studio/static/kosuri/ に 4枚保存
"""
import base64, json, os, urllib.request
from pathlib import Path

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
OUT_DIR = Path(__file__).parent / "static" / "kosuri"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={API_KEY}"

CHARACTER_BASE = (
    "ultra-realistic close-up portrait photo of a beautiful 20-year-old Korean-Japanese girl, "
    "straight black hair with neat bangs, "
    "very cute and innocent face, "
    "soft natural makeup with subtle lip tint and light blush, "
    "bright clear eyes with gentle gaze, "
    "idol-like fresh and youthful appearance similar to ILLIT group member, "
    "soft pastel or white background, warm soft studio lighting, "
    "selfie-style close portrait, face takes up most of the frame, "
    "high quality photorealistic, sharp focus on face"
)

IMAGES = [
    {
        "filename": "avatar.png",
        "prompt": (
            f"{CHARACTER_BASE}, "
            "gentle sweet smile, slightly tilted head, "
            "looking directly at camera with warm eyes, "
            "wearing a simple soft pastel top"
        ),
        "label": "アバター（チャットヘッダー用）",
    },
    {
        "filename": "greeting.png",
        "prompt": (
            f"{CHARACTER_BASE}, "
            "bright cheerful smile, eyes slightly curved in happiness, "
            "hand near cheek in a cute pose, "
            "welcoming and friendly expression"
        ),
        "label": "グリーティング（初回登場）",
    },
    {
        "filename": "thanks.png",
        "prompt": (
            f"{CHARACTER_BASE}, "
            "deeply touched and happy expression, eyes sparkling with gratitude, "
            "hands gently pressed together near chin as if saying thank you, "
            "warm heartfelt smile, slightly rosy cheeks, "
            "genuine joyful emotion"
        ),
        "label": "ありがとう（フィードバック受け取り後）",
    },
    {
        "filename": "ganbare.png",
        "prompt": (
            f"{CHARACTER_BASE}, "
            "excited determined expression with a big bright smile, "
            "one hand making a small fist near her cheek in a 'ganbare' pose, "
            "energetic and motivated, sparkling eyes full of enthusiasm, "
            "cute fighting spirit"
        ),
        "label": "がんばる（機能要望受け取り後）",
    },
]

def generate_image(prompt: str, out_path: Path, label: str) -> bool:
    print(f"\n[生成中] {label}")
    # Imagen 4.0 API format
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "personGeneration": "allow_adult",
        },
    }
    try:
        req = urllib.request.Request(
            URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())

        predictions = result.get("predictions", [])
        if predictions and "bytesBase64Encoded" in predictions[0]:
            img_data = base64.b64decode(predictions[0]["bytesBase64Encoded"])
            out_path.write_bytes(img_data)
            print(f"  ✅ 保存: {out_path} ({len(img_data)//1024}KB)")
            return True

        print(f"  ❌ 画像データなし: {json.dumps(result)[:300]}")
        return False
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

if __name__ == "__main__":
    print("=== KOSURIちゃん画像生成 ===")
    for img in IMAGES:
        out = OUT_DIR / img["filename"]
        if out.exists():
            print(f"  スキップ（既存）: {out.name}")
            continue
        generate_image(img["prompt"], out, img["label"])

    print("\n=== 完了 ===")
    for f in sorted(OUT_DIR.iterdir()):
        print(f"  {f.name}: {f.stat().st_size//1024}KB")
