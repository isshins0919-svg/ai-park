#!/usr/bin/env python3
"""
さくら提案書用イメージ生成 — 3枚
テーマ：夜のベッド × 声 × ちょいエロい部屋着 × オシャレなアニメ
"""

import os, time, base64, subprocess
from pathlib import Path

def load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'],
                               capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v:
                os.environ[var] = v
        except Exception:
            pass

for v in ['GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
    load_env(v)

API_KEYS = [k for k in [
    os.environ.get('GEMINI_API_KEY_1', ''),
    os.environ.get('GEMINI_API_KEY_2', ''),
    os.environ.get('GEMINI_API_KEY_3', ''),
] if k.strip()]

if not API_KEYS:
    print("❌ GEMINI_API_KEY_1 が未設定です")
    exit(1)

from google import genai
from google.genai import types

clients = [genai.Client(api_key=k) for k in API_KEYS]

OUT_DIR = Path(__file__).parent / "sakura_images"
OUT_DIR.mkdir(exist_ok=True)

IMAGES = [
    {
        "filename": "sakura_img1.png",
        "prompt": """Stylish anime illustration, vertical 9:16 portrait format.

Scene: A young Japanese woman sitting on a soft bed at night. She is seen from behind or from the shoulders down only — face NOT visible. She wears a slightly revealing, off-shoulder pastel silk pajama top, showing her collarbone and shoulder. Long dark hair falls loosely.

The room is dimly lit by a warm amber bedside lamp. Soft purple and deep blue shadows. She holds a small vintage-style microphone gently, practicing whispering something.

Art style: Modern anime, clean linework, soft watercolor-style shading. Elegant, slightly sensual but tasteful. Color palette: deep navy, warm amber glow, rose pink accents, cream skin tones.

No face shown. Focus on the atmosphere — late night, intimate, quiet, beautiful."""
    },
    {
        "filename": "sakura_img2.png",
        "prompt": """Stylish anime illustration, vertical 9:16 portrait format.

Scene: Close-up of a Japanese anime girl's neck, collarbone, and upper chest area. She wears a loose white satin camisole that slides slightly off one shoulder. The skin is softly illuminated by a glowing phone screen in the dark room.

Scattered around her: tiny music notes floating in the air, a vintage microphone, cherry blossom petals drifting slowly.

The mood is dreamy and sensual but artistic. Deep indigo night background with bokeh city lights through a window.

Art style: Premium anime key visual style, detailed fabric texture, soft glow effects. Color palette: midnight blue, warm gold, soft white, cherry blossom pink.

No full face. Atmospheric, poetic, slightly erotic but beautifully tasteful."""
    },
    {
        "filename": "sakura_img3.png",
        "prompt": """Stylish anime illustration, vertical 9:16 portrait format.

Scene: A beautiful Japanese anime bedroom at 2am. Unmade bed with white linen, a ring light glowing softly, a professional-looking microphone on a small stand. On the nightstand: a baseball stadium ticket stub, a glass of water, and a phone showing a TikTok recording screen.

The room feels lived-in and intimate. Warm amber light mingles with cool blue moonlight from a window. Cherry blossom branches visible through the window.

Suggestion of a woman having just left the frame — her silk robe draped over the bedpost, indentation in the pillow.

Art style: Cinematic anime background art, hyper-detailed, Makoto Shinkai influenced. Lush color grading: deep teal shadows, golden warm highlights, soft pink bokeh.

No person visible. Just the beautiful, intimate, slightly mysterious room."""
    }
]

def generate_image(prompt, filename, client_idx=0):
    client = clients[client_idx % len(clients)]
    print(f"🎨 生成中: {filename}")
    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                path = OUT_DIR / filename
                path.write_bytes(base64.b64decode(part.inline_data.data)
                                 if isinstance(part.inline_data.data, str)
                                 else part.inline_data.data)
                print(f"  ✅ 保存: {path}")
                return True
        print(f"  ⚠️ 画像データなし")
        return False
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

for i, img in enumerate(IMAGES):
    generate_image(img["prompt"], img["filename"], client_idx=i)
    if i < len(IMAGES) - 1:
        time.sleep(3)

print("\n✅ 画像生成完了")
