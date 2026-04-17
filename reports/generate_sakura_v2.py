#!/usr/bin/env python3
"""
さくら台本v2用イメージ生成 — 台本5本 × 各2-3枚 = 計13枚
テーマ：リアルな撮影イメージ（ベッドの上でどう映るか、具体的に）
スタイル：フォトリアリスティック（アニメではなく実写風）
"""

import os, time, base64, subprocess, sys
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
    print("GEMINI_API_KEY_1 が未設定です")
    sys.exit(1)

from google import genai
from google.genai import types

clients = [genai.Client(api_key=k) for k in API_KEYS]

OUT_DIR = Path(__file__).parent / "sakura_v2_images"
OUT_DIR.mkdir(exist_ok=True)

# 共通スタイル指示
STYLE = """Photorealistic digital art, vertical 9:16 portrait format.
Japanese woman in her mid-20s. Face is NEVER shown — always shot from behind, side profile silhouette, or shoulders-down only.
Camera: iPhone-quality, slightly grainy for authenticity.
IMPORTANT: This should look like a real TikTok screenshot, not a polished studio photo."""

IMAGES = [
    # === Script 1: スタメン発表の練習 ===
    {
        "filename": "s1_hook.png",
        "prompt": f"""{STYLE}
Scene: A woman sitting on an unmade bed at night, seen from behind. She wears a loose off-shoulder white sleep camisole. Long black hair falls across her bare shoulders. She holds a crumpled paper (script) in one hand.

Lighting: Single warm amber bedside lamp on the left. The rest of the room is in deep shadow. Soft orange glow highlights her shoulder and the curve of her neck.

Mood: Intimate, quiet, late-night practice session. The bed sheets are slightly rumpled. A phone with TikTok recording screen glows on the nightstand.

This is the HOOK frame — the very first thing viewers see. It must stop the scroll."""
    },
    {
        "filename": "s1_pro_voice.png",
        "prompt": f"""{STYLE}
Scene: Close-up from collarbone down. A woman in a thin white satin camisole, the strap sliding slightly off one shoulder. She sits upright on a bed, posture suddenly straight and professional — a stark contrast to the casual setting.

Lighting: Warm side-lighting from the left. Her skin has a soft golden glow. Deep shadows on the right side.

Detail: A small vintage-style microphone is visible at the edge of frame, suggesting she's practicing announcements. Her hand is raised slightly as if gesturing during a professional announcement.

Mood: The tension between professional posture and intimate bedroom setting. This is the GAP moment."""
    },
    {
        "filename": "s1_end.png",
        "prompt": f"""{STYLE}
Scene: A woman has just flopped backwards onto the bed, seen from above at a 45-degree angle. Only her body from shoulders down is visible. White camisole has shifted, showing more of her collarbone. Her hair fans out on the white pillow. One hand rests near her face (but face is cropped out). The script paper has fallen beside her.

Lighting: Dim amber lamp creates warm pools of light. Blue moonlight from a window adds cool contrast on the sheets.

Mood: Exhaustion after practice. Vulnerable. Beautiful. The moment of "...I'm going to sleep now." """
    },

    # === Script 2: ホームラン実況（囁きver） ===
    {
        "filename": "s2_hook.png",
        "prompt": f"""{STYLE}
Scene: Extreme close-up of a woman's neck, chin (from below, no eyes visible), and a microphone. She's leaning very close to a small condenser microphone on a bed. Thin spaghetti-strap tank top. Her lips are almost touching the mic — about to whisper.

Lighting: Single ring light creating a soft halo effect. The rest is darkness. The light catches the fine hairs on her skin.

Mood: ASMR intimacy. The viewer feels like they're right there, about to hear her whisper. Extreme closeness.

This is the hook frame — pure visual ASMR tension."""
    },
    {
        "filename": "s2_shout.png",
        "prompt": f"""{STYLE}
Scene: A woman on a bed, captured mid-motion. She's sitting up suddenly, one hand covering her mouth in surprise at her own loudness. Seen from the side — only her silhouette and shoulder visible against the warm lamplight. Tank top strap has slipped off one shoulder.

Lighting: Dramatic side-lighting. Her silhouette is sharp against the warm glow. A slight motion blur to convey sudden movement.

Mood: The moment she accidentally shouts "HOME RUN!" at full volume in the middle of the night. Comic and endearing. The gap between whisper and shout."""
    },

    # === Script 3: 4番バッターに言えなかったこと ===
    {
        "filename": "s3_hook.png",
        "prompt": f"""{STYLE}
Scene: A woman lying on her side on a bed, curled up slightly. Seen from behind/above. She wears a loose oversized t-shirt that has ridden up slightly, showing a sliver of her waist. She's looking at her phone screen (the glow illuminates the curve of her body). Her hair is spread across the pillow.

Lighting: Only the phone screen glow (cool blue-white) and a faint amber light from somewhere off-frame. Mostly darkness.

Mood: Late night loneliness. Scrolling through something — maybe his stats, maybe his photos. Vulnerable and beautiful.

This is the hook — intimate vulnerability that stops the scroll."""
    },
    {
        "filename": "s3_confession.png",
        "prompt": f"""{STYLE}
Scene: A woman lying on her back on white sheets, shot from above. Only her body from neck down is visible. One arm across her chest, the other draped to the side. Wearing a thin silk camisole. Her skin glows warmly against the cool white sheets.

Lighting: Soft, diffused warm light from above (like a ring light). Creates beautiful shadows along her collarbone and arms.

Mood: The moment of confession — she's talking to the ceiling, admitting she gets nervous when she calls his name. Raw emotional vulnerability mixed with physical beauty."""
    },
    {
        "filename": "s3_darkness.png",
        "prompt": f"""{STYLE}
Scene: Near-total darkness. Only the faintest outline of a woman's shoulder and the edge of a pillow is visible. A bedside lamp has just been turned off — there's a faint afterglow. The very last frame before sleep.

Lighting: Almost none. Just the faintest warm glow fading. Deep blacks and subtle grays.

Mood: "...Let's stop. Let's sleep." The finality. The secret stays in this dark room. Powerful emotional ending."""
    },

    # === Script 4: 深夜の囁き練習（純ASMR） ===
    {
        "filename": "s4_hook.png",
        "prompt": f"""{STYLE}
Scene: A woman's hands gently holding a small professional microphone in bed. The microphone is in sharp focus, her hands slightly soft. She wears a delicate bracelet. In the very soft background, the suggestion of her body in a silk nightgown, but deeply out of focus.

Lighting: Single small LED light (warm white) creating a spotlight effect on the microphone and her hands. Everything else fades to black.

Mood: Pure ASMR setup. The mic is the star, but her presence is felt. Quiet, intimate, professional equipment in an intimate setting."""
    },
    {
        "filename": "s4_sleep.png",
        "prompt": f"""{STYLE}
Scene: A woman has fallen asleep on the bed, still holding the microphone loosely. Shot from above at an angle — face hidden by her hair spread across the pillow. Silk nightgown draped softly. One leg slightly bent. The script papers are scattered on the bed around her.

Lighting: The ring light is still on but dimmed, casting a soft circular glow. Moonlight through curtains adds blue tones.

Mood: She fell asleep while practicing. Adorable and intimate. The viewer watches her drift off. This is the loop point — "I should go back to the beginning and listen again." """
    },

    # === Script 5: 声が裏返った日 ===
    {
        "filename": "s5_hook.png",
        "prompt": f"""{STYLE}
Scene: A woman sitting on a bed, hugging a pillow against her chest. Seen from the side — profile silhouette only. Her shoulders are slightly hunched (embarrassment). Wearing an oversized baseball-style t-shirt as sleepwear.

Lighting: Warm lamp behind her creates a beautiful rim-light effect outlining her silhouette. Her face is in shadow.

Mood: "Today was the worst. I messed up." Embarrassment and vulnerability. The pillow-hugging gesture is relatable and endearing.

This is the hook — emotional vulnerability in silhouette."""
    },
    {
        "filename": "s5_practice.png",
        "prompt": f"""{STYLE}
Scene: A woman sitting on the edge of a bed, back straight, one hand holding a script paper. Shot from behind at a low angle — she looks determined. The oversized baseball t-shirt has slipped off one shoulder revealing a tank top strap underneath.

Lighting: Warm golden light from the front (ring light) illuminating the script. Her back is in slight shadow.

Mood: Determination. She's going to nail it this time. The posture shift from slouching (embarrassment) to sitting straight (determination) tells the story.

The gap between vulnerable girl and determined professional."""
    },
    {
        "filename": "s5_victory.png",
        "prompt": f"""{STYLE}
Scene: A woman making a small fist pump gesture, seen from the side. Just her arm and shoulder visible, with the soft blur of the bedroom behind her. A genuine, subtle celebration — not over the top.

Lighting: Warm, celebratory. The lamp seems to glow a little brighter in this moment.

Mood: "...Yes." She nailed the line. A tiny private victory at 2am that nobody will ever know about. Except this camera. Except these viewers.

This is the ending frame — small, intimate triumph."""
    },
]

def generate_image(prompt, filename, client_idx=0):
    client = clients[client_idx % len(clients)]
    print(f"  Generating: {filename}")
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
                data = part.inline_data.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                path.write_bytes(data)
                print(f"  Saved: {path}")
                return True
        print(f"  No image data in response")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    print(f"Generating {len(IMAGES)} images...")
    print(f"Output: {OUT_DIR}")
    print(f"API keys: {len(API_KEYS)}")
    print()

    success = 0
    for i, img in enumerate(IMAGES):
        if generate_image(img["prompt"], img["filename"], client_idx=i):
            success += 1
        if i < len(IMAGES) - 1:
            time.sleep(4)

    print(f"\nDone: {success}/{len(IMAGES)} images generated")
