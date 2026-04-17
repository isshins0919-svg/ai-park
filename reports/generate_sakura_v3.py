#!/usr/bin/env python3
"""
さくら台本v3 追加画像 — 台本5本 × 各2枚追加 = 計10枚
テーマ：口元見えるけど顔は見えない / 小道具の引き / 目に絶対止まる絵
"""

import os, time, base64, subprocess, sys
from pathlib import Path

def load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'],
                               capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except Exception: pass

for v in ['GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
    load_env(v)

API_KEYS = [k for k in [
    os.environ.get('GEMINI_API_KEY_1', ''),
    os.environ.get('GEMINI_API_KEY_2', ''),
    os.environ.get('GEMINI_API_KEY_3', ''),
] if k.strip()]

if not API_KEYS:
    print("GEMINI_API_KEY_1 not set"); sys.exit(1)

from google import genai
from google.genai import types

clients = [genai.Client(api_key=k) for k in API_KEYS]
OUT_DIR = Path(__file__).parent / "sakura_v2_images"
OUT_DIR.mkdir(exist_ok=True)

# 共通スタイル
STYLE = """Photorealistic digital art, vertical 9:16 portrait format.
Japanese woman in her mid-20s. IMPORTANT: Face above the nose is NEVER shown.
Camera: iPhone-quality, slightly grainy for authenticity, like a real TikTok video screenshot."""

IMAGES = [
    # === S1追加: 口元+マイク / 野球チケット小道具 ===
    {
        "filename": "s1_lips.png",
        "prompt": f"""{STYLE}
Scene: EXTREME close-up from nose-down only. Beautiful lips slightly parted, about to speak into a professional studio microphone that's very close to her mouth. Warm amber light from the side catches her jawline and lower lip. She wears a thin gold necklace that catches the light.

The background is dark bedroom, completely blurred. Just her lips, the mic, and golden light.

Mood: The moment right before she says something. Tension. Intimacy. The viewer is RIGHT THERE.
This must be absolutely scroll-stopping. The lips + mic combination is the hook."""
    },
    {
        "filename": "s1_props.png",
        "prompt": f"""{STYLE}
Scene: A beautiful flat-lay still life on rumpled white bed sheets. Items arranged artfully:
- A crumpled handwritten script/notes with Japanese text visible
- A small vintage-looking microphone
- A baseball stadium lanyard/pass on a pink ribbon
- Cherry blossom petals scattered
- A glass of water half-empty
- An iPhone with screen glow

Lighting: Warm overhead light. Soft shadows. The items tell a story — this is a professional announcer's late night practice session.

No person in frame. Just the objects on the bed. But her presence is felt everywhere."""
    },

    # === S2追加: 口抑え横顔 / マイクASMRクローズアップ ===
    {
        "filename": "s2_lips_shh.png",
        "prompt": f"""{STYLE}
Scene: Close-up from nose down — a woman pressing her index finger to her lips in a 'shh' gesture. She's telling the viewer to be quiet. Her lips are slightly smiling. A thin spaghetti strap is visible on her shoulder.

Warm amber side-lighting. Dark background. Her finger and lips are in sharp focus.

Mood: Playful secrecy. "Shh, I'm about to whisper." Conspiratorial intimacy with the viewer.
The 'shh' gesture + visible lips + darkness = instant scroll stop."""
    },
    {
        "filename": "s2_mic_breath.png",
        "prompt": f"""{STYLE}
Scene: Side angle close-up of a woman's chin, neck and a large condenser microphone. Her mouth is very close to the mic — you can almost feel her breath on it. The mic's metal grille is in sharp focus. Her skin has a warm golden glow.

A ring light creates a perfect circular bokeh in the dark background. Her collarbone is visible.

Mood: Pure ASMR tension. The physical closeness to the microphone is the hook. The viewer's ears tingle just looking at this."""
    },

    # === S3追加: スマホ光+涙目 / 野球ユニフォームT ===
    {
        "filename": "s3_phone_glow.png",
        "prompt": f"""{STYLE}
Scene: A woman lying in bed in darkness, holding her phone up. The screen casts a cool blue-white glow on her chin, lips, and neck (face above nose is NOT visible). She's looking at something on the screen — maybe his stats, maybe his photo. Her lips are slightly pressed together — holding back emotion.

One tear track catches the phone light on her cheek (below the nose line).

The phone screen is the only light source. Everything else is deep black.

Mood: Late night loneliness. Scrolling through memories. Devastating intimacy."""
    },
    {
        "filename": "s3_jersey.png",
        "prompt": f"""{STYLE}
Scene: A woman sitting on a bed wearing an oversized men's baseball jersey as sleepwear — it's way too big for her, sliding off one shoulder. The jersey number '3' is visible on the back. She's hugging her knees, seen from behind.

Warm lamp light. The jersey implies a story — whose jersey is this? Why does she have it?

Mood: The jersey is the storytelling device. It raises questions. It's both sporty and intimate — wearing someone's jersey to bed."""
    },

    # === S4追加: 寝落ち口元 / リングライト+シーツ ===
    {
        "filename": "s4_sleeping_lips.png",
        "prompt": f"""{STYLE}
Scene: Close-up of a woman who has fallen asleep. Shot from the side — only her lips, chin, and neck are visible. Her lips are slightly parted in sleep. A microphone has slipped from her hand and rests near her face on the pillow. Her hair is spread across white sheets.

Soft ring light glow from above. Peaceful. Beautiful.

Mood: She fell asleep practicing. The microphone near her sleeping face tells the whole story. Adorable. Intimate. The viewer wants to pull the blanket over her."""
    },
    {
        "filename": "s4_ring_light.png",
        "prompt": f"""{STYLE}
Scene: Wide shot of a dark bedroom. A ring light stands on a small tripod on the bed, still glowing. In the warm circular light: crumpled white sheets, scattered script papers, a microphone on its side, and the silhouette of a woman curled up sleeping at the edge of the light's reach.

The ring light is the visual anchor — a perfect circle of warm light in darkness.

Mood: The aftermath. Practice is over. She's asleep. But the light is still on. Cinematic. Beautiful framing."""
    },

    # === S5追加: メガホン/選挙小道具 / 口元+笑顔 ===
    {
        "filename": "s5_megaphone.png",
        "prompt": f"""{STYLE}
Scene: A woman sitting on a bed holding a small portable megaphone/loudspeaker (the kind used in Japanese election campaigns) — but she's holding it up like she's about to use it, and then lowering it with a slight laugh. Only visible from nose down — her lips are curved in an amused smile.

She wears an oversized vintage baseball tee. The megaphone is bright white, contrasting with the dark bedroom.

Mood: The absurdity of practicing election announcements in bed at night. Playful. Charming. The megaphone is the unexpected prop that catches the eye."""
    },
    {
        "filename": "s5_smile_lips.png",
        "prompt": f"""{STYLE}
Scene: Close-up from nose down. A woman with a genuine, warm smile. Not a posed smile — a real one, like she just accomplished something small but important. Her teeth are slightly visible. Warm amber light catches the curve of her smile.

She's wearing a simple thin chain necklace. The background is soft dark bedroom blur.

Mood: The tiny private victory smile at 2am. She nailed the line. Nobody knows except her and the camera. This smile is the most human, relatable moment in the whole series."""
    },
]

def generate_image(prompt, filename, client_idx=0):
    client = clients[client_idx % len(clients)]
    print(f"  Generating: {filename}")
    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                path = OUT_DIR / filename
                data = part.inline_data.data
                if isinstance(data, str): data = base64.b64decode(data)
                path.write_bytes(data)
                print(f"  Saved: {path}")
                return True
        print(f"  No image data"); return False
    except Exception as e:
        print(f"  Error: {e}"); return False

if __name__ == "__main__":
    print(f"Generating {len(IMAGES)} additional images...")
    success = 0
    for i, img in enumerate(IMAGES):
        if generate_image(img["prompt"], img["filename"], client_idx=i):
            success += 1
        if i < len(IMAGES) - 1: time.sleep(4)
    print(f"\nDone: {success}/{len(IMAGES)}")
