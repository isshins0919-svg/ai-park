#!/usr/bin/env python3
"""
セツナトレイン2 ストーリーボード画像生成スクリプト
Gemini 2.0 Flash で各シーンのストーリーボードイラストを生成
"""

import os
import sys
import base64
import time
import json
from pathlib import Path
from google import genai
from google.genai import types

# Setup
OUTPUT_DIR = Path("/Users/ca01224/Desktop/一進VOYAGE号/reports/setsunatrain2_images")
OUTPUT_DIR.mkdir(exist_ok=True)

# Try multiple API keys
api_keys = [
    os.environ.get("GEMINI_API_KEY_1", ""),
    os.environ.get("GEMINI_API_KEY_2", ""),
    os.environ.get("GEMINI_API_KEY_3", ""),
]
api_key = next((k for k in api_keys if k), None)
if not api_key:
    print("ERROR: No GEMINI_API_KEY found")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Common style prefix for all prompts
STYLE_PREFIX = """Create a high-quality, photorealistic advertising storyboard frame.
The image should look like a real photograph that would be used in an Instagram Reels ad for a travel experience event.
Aspect ratio: 9:16 (vertical/portrait, smartphone format).
Style: Bright, warm, inviting. Think Japanese travel advertisement photography.
DO NOT include any text, logos, watermarks, or overlays in the image.
"""

# Scene definitions: (filename, prompt)
SCENES = [
    # === SHARED/COMMON SCENES ===
    ("common_01_shinagawa_platform",
     STYLE_PREFIX + "Scene: Two young Japanese women (late 20s) standing excitedly on a train platform at Shinagawa Station, Tokyo. A sleek white limited express train (like JR Odoriko) is arriving. They're holding their phones, looking excited and happy. Morning light. The platform has a modern feel. One is pointing at the approaching train."),

    ("common_02_train_interior_drama",
     STYLE_PREFIX + "Scene: Inside a comfortable Japanese limited express train. A young Japanese woman is watching a drama on her smartphone while sitting by the window. On the fold-down table, there's an elegant mystery puzzle kit (like a premium escape room box). Sunlight streams through the window. The ocean is visible through the window in the distance."),

    ("common_03_window_view_ocean",
     STYLE_PREFIX + "Scene: Beautiful view through a train window. The landscape transitions from urban buildings to a stunning Pacific Ocean coastline. Blue sky with some white clouds. The Izu Peninsula coastline is visible. Warm afternoon light. The ocean sparkles. Shot from inside the train, window frame visible."),

    ("common_04_ito_station_arrival",
     STYLE_PREFIX + "Scene: Two young Japanese women stepping off a train at a charming Japanese coastal town station. Blue sky overhead. They look happy and excited, taking a deep breath of fresh sea air. The station has a small-town warmth. You can sense the ocean nearby. They're wearing casual fashionable outfits."),

    ("common_05_sweets_shop_1",
     STYLE_PREFIX + "Scene: Close-up of a beautiful Japanese artisanal cake on a plate in a cozy local patisserie. The cake has fresh strawberries and cream, beautifully plated. Warm cafe interior with vintage decor in the background. Natural light from a window. A hand reaching for the cake with a fork."),

    ("common_06_sweets_shop_2",
     STYLE_PREFIX + "Scene: A cute Japanese parfait dessert in a tall glass at a seaside cafe. Layers of fruit, cream, and gelato. The ocean is visible through the cafe window behind. Two young women are photographing it with their phones before eating. Bright, Instagram-worthy setting."),

    ("common_07_sweets_shop_3",
     STYLE_PREFIX + "Scene: Japanese traditional wagashi sweets beautifully arranged on a ceramic plate. A young woman is taking a bite and making a delighted expression. The shop has a blend of traditional and modern Japanese interior. Warm lighting. Close-up of her happy reaction."),

    ("common_08_sweets_collage",
     STYLE_PREFIX + "Scene: A flat-lay style arrangement of 4 different beautiful Japanese desserts on a wooden table. Include: a strawberry cake slice, a colorful parfait, traditional wagashi, and a cream puff. Bright natural lighting. Overhead shot. Each dessert looks photogenic and Instagram-worthy."),

    ("common_09_puzzle_solving",
     STYLE_PREFIX + "Scene: Two young Japanese women on a charming street in a coastal Japanese town, looking at a puzzle card together. One is pointing at something on a building in the distance while the other checks the clue card. They look engaged and excited. The street has traditional Japanese architecture mixed with small shops."),

    ("common_10_eureka_moment",
     STYLE_PREFIX + "Scene: A young Japanese woman having an 'aha!' moment while solving a puzzle outdoors. She's jumping with excitement, arms raised, in a beautiful Japanese coastal town setting. Her friend is laughing beside her. Afternoon golden light. Cherry blossoms or ocean in the background."),

    ("common_11_sunset_ito",
     STYLE_PREFIX + "Scene: Breathtaking sunset over the ocean in Ito, Shizuoka Prefecture, Japan. Two silhouettes of young women standing on a scenic overlook, looking at the view. Orange and pink sky reflected on the calm Pacific Ocean. Dramatic, emotional, cinematic. This is the climax of a day trip."),

    ("common_12_cta_endcard",
     STYLE_PREFIX + "Scene: A dreamy, soft-focus shot of the ocean at golden hour in Ito, Japan. Warm golden light. Some silhouetted palm trees or pine trees on the side. The image has a peaceful, inviting feel that makes you want to visit. Slightly blurred/bokeh effect for text overlay space."),

    # === SCRIPT A: VLOG TYPE - Female friends ===
    ("a_01_hook_selfie",
     STYLE_PREFIX + "Scene: Two young Japanese women taking a selfie at Shinagawa Station platform with a limited express train behind them. They're making peace signs, big smiles, very energetic. Shot looks like a phone selfie / Instagram story. Natural, not posed."),

    ("a_02_friends_walking",
     STYLE_PREFIX + "Scene: Two young Japanese women walking down a charming street in a Japanese seaside town, seen from behind. They're walking side by side, pointing at shops. The street has small cafes and traditional buildings. Warm afternoon light. They look like they're having the best day."),

    # === SCRIPT B: DATE TYPE - Couple ===
    ("b_01_hook_couple_hands",
     STYLE_PREFIX + "Scene: Close-up of a Japanese couple holding hands while walking through a train station. Only their hands and legs visible as they walk toward a platform. Romantic, cinematic feel. The man is leading her to the train."),

    ("b_02_couple_train",
     STYLE_PREFIX + "Scene: A young Japanese couple sitting side by side in a comfortable limited express train. She's resting her head on his shoulder while looking at his phone screen showing a drama. Through the window, ocean coastline is visible. Warm, romantic lighting."),

    ("b_03_couple_sunset",
     STYLE_PREFIX + "Scene: A young Japanese couple standing together looking at a sunset over the ocean. Shot from behind, showing their silhouettes against the orange sky. She's leaning against him. Very romantic, cinematic. The man has his arm around her. Ito, Japan coastal setting."),

    # === SCRIPT C: MYSTERY TYPE ===
    ("c_01_hook_cipher",
     STYLE_PREFIX + "Scene: A mysterious hand-written cipher code on aged paper, dramatically lit. The paper sits on a dark wooden table with a pen nearby. The code should look like symbols and numbers that form a puzzle. Mysterious, intriguing atmosphere. Close-up shot. Dark, moody lighting with a single spotlight."),

    ("c_02_puzzle_closeup",
     STYLE_PREFIX + "Scene: Close-up of hands holding a puzzle card with mysterious symbols, with a Japanese coastal town street blurred in the background. The person is studying the clue intently. One finger points at a specific part of the puzzle. Dramatic, mystery-thriller atmosphere."),

    # === SCRIPT D: HEALING/ESCAPE TYPE ===
    ("d_01_hook_tired",
     STYLE_PREFIX + "Scene: A tired young Japanese woman lying on her bed in a dark apartment room, scrolling her phone. The only light comes from the phone screen. She looks exhausted from work. Friday night feeling. Moody, blue-tinted lighting. Realistic, relatable scene."),

    ("d_02_morning_transform",
     STYLE_PREFIX + "Scene: The same young Japanese woman, now standing on a sunny train platform in the morning. She's wearing casual clothes and has a small bag. The sun is shining brightly behind her. She takes a deep breath, looking refreshed and hopeful. Complete contrast from the dark room scene."),

    ("d_03_bench_ocean_sweets",
     STYLE_PREFIX + "Scene: A young Japanese woman sitting alone on a bench overlooking the ocean, eating a beautiful dessert. She looks peaceful and content. The ocean stretches out in front of her. Warm afternoon light. Her shoes are kicked off casually. A healing, therapeutic atmosphere."),

    # === SCRIPT E: UGC/REVIEW TYPE ===
    ("e_01_hook_talking",
     STYLE_PREFIX + "Scene: A young Japanese woman (25, fashionable, casual) talking directly to camera in selfie mode. She's in a bright, casual setting (maybe her apartment or a cafe). Animated, excited expression, like she's telling a friend about something amazing. Natural lighting, Instagram story vibe."),

    ("e_02_showing_photos",
     STYLE_PREFIX + "Scene: A young Japanese woman holding up her phone to the camera, showing photos from her trip. On her phone screen, you can see a beautiful dessert photo. She's pointing at it excitedly. The shot is casual, handheld, like a friend showing you vacation photos. UGC style."),

    # === AD MOCKUP FRAMES (phone screen format) ===
    ("mock_01_reels_vlog",
     STYLE_PREFIX + "Scene: Two young Japanese women smiling and waving at the camera on a train platform, with a sleek express train behind them. The shot is framed vertically for Instagram Reels. They look genuinely happy and excited about their trip. Morning sunlight."),

    ("mock_02_reels_sweets",
     STYLE_PREFIX + "Scene: A beautiful Japanese parfait being held up by a young woman's hand with an ocean view behind it. Vertical framing for Instagram Reels. The dessert is colorful and photogenic. The ocean sparkles in the background. Perfect Instagram content."),

    ("mock_03_reels_mystery",
     STYLE_PREFIX + "Scene: A young person's hands holding a mysterious puzzle card with coded symbols, against a backdrop of a charming Japanese street. Vertical framing. The atmosphere is intriguing and mysterious. Dramatic shadows. Makes you want to solve the puzzle."),
]

def generate_image(prompt, filename):
    """Generate an image using Gemini and save it."""
    filepath = OUTPUT_DIR / f"{filename}.png"

    # Skip if already exists
    if filepath.exists() and filepath.stat().st_size > 1000:
        print(f"  SKIP (exists): {filename}")
        return True

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = part.inline_data.data
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    print(f"  OK: {filename} ({filepath.stat().st_size // 1024}KB)")
                    return True

        print(f"  WARN: No image in response for {filename}")
        return False

    except Exception as e:
        print(f"  ERROR: {filename} - {e}")
        return False

def main():
    print(f"=== セツナトレイン2 画像生成 ===")
    print(f"Total scenes: {len(SCENES)}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    success = 0
    fail = 0

    for i, (filename, prompt) in enumerate(SCENES):
        print(f"[{i+1}/{len(SCENES)}] {filename}")
        if generate_image(prompt, filename):
            success += 1
        else:
            fail += 1

        # Rate limiting - small delay between calls
        if i < len(SCENES) - 1:
            time.sleep(2)

    print(f"\n=== DONE: {success} success, {fail} fail ===")

    # List generated files
    files = sorted(OUTPUT_DIR.glob("*.png"))
    print(f"\nGenerated files ({len(files)}):")
    for f in files:
        print(f"  {f.name} ({f.stat().st_size // 1024}KB)")

if __name__ == "__main__":
    main()
