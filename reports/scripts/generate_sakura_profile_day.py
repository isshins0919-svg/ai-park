#!/usr/bin/env python3
"""
さくら プロフィール画像 — 昼のウグイス嬢版 5パターン
コンセプト: ブランドの"表側"を確立する
条件:
- 野球場・プロの仕事感が一目で伝わる
- 顔上部は見えない（鼻から上NG）
- 明るい昼 or 夕方の屋外光 or スタジアム照明
- 中央構図（TikTok円クロップ対応）
- スーツ・制服・フォーマル感
"""

import os, time, base64, sys
from pathlib import Path

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
OUT_DIR = Path(__file__).parent / "sakura_profile_candidates"
OUT_DIR.mkdir(exist_ok=True)

BASE_STYLE = """Photorealistic portrait, SQUARE 1:1 format (will be circle-cropped for TikTok profile).
Japanese woman in mid-20s, professional stadium announcer (ウグイス嬢) at work during daytime.
ABSOLUTE RULE: Face above the upper lip is NEVER visible — always cropped out or from behind.
Setting: A real Japanese baseball stadium during daytime or golden hour. Feel of a public, professional, legitimate workplace — not sensual, not nighttime bedroom."""

IMAGES = [
    {
        "filename": "d01_booth_mic.png",
        "concept": "アナウンスブース × プロマイク",
        "reasoning": "室内のブース越しに球場を臨む。昼の仕事感が最強で伝わる",
        "prompt": f"""{BASE_STYLE}

Scene: View from inside a baseball stadium announcer booth. A woman's hands are holding a classic announcer's microphone close to her chin. Only her lower face (from nose down) and hands are visible. She wears a crisp white blouse with a thin navy ribbon tie or scarf at the neck. A handwritten announcer's script is visible on the wooden desk in front of her.

Through the glass window of the booth: a sunny baseball stadium with green field, brown infield dirt, and blurred crowd in the stands. Bright daylight pours in from behind.

Lighting: Natural sunlight from the window behind her creates a golden rim light on her hair and shoulders. Professional daytime atmosphere.

Center the microphone + lips in the frame for circular crop.

Color palette: white blouse, navy accents, green field, golden sunlight, natural skin tones. Legitimate, professional, cinematic."""
    },

    {
        "filename": "d02_back_stadium.png",
        "concept": "後ろ姿 × 球場全景",
        "reasoning": "完全匿名 × 球場の情景。一目で「球場で働いてる人」と分かる",
        "prompt": f"""{BASE_STYLE}

Scene: Back view of a young woman standing in an announcer's booth, looking out at a baseball stadium below. Her long dark hair falls down her back. She wears a crisp white blouse and a professional navy vest or jacket. Her hand holds a small microphone near her ear (about to make an announcement).

Through the large glass window in front of her: a full baseball stadium view — green outfield, infield diamond, bleacher seats dotted with fans, blue sky, scoreboard visible in the distance.

Lighting: Bright daylight from the stadium fills the scene. Her silhouette is outlined by the bright window behind her.

Composition: centered on her back, with the stadium framing her on all sides.

Color palette: white, navy, stadium green, sky blue, warm daylight. Legitimate and powerful."""
    },

    {
        "filename": "d03_script_hands_stadium.png",
        "concept": "台本を持つ手 × 球場背景",
        "reasoning": "顔ゼロ × 手と紙だけで職業が伝わる。完全匿名の極み",
        "prompt": f"""{BASE_STYLE}

Scene: Close-up of a woman's delicate hands holding an announcer's script (typed lineup roster with Japanese text) and a small lapel microphone. Only the hands, the paper, and a hint of a crisp white blouse cuff are visible. A thin gold bracelet on her wrist.

Background: Softly blurred Japanese baseball stadium during golden hour — the scoreboard and field visible but out of focus. Warm late-afternoon sunlight.

Lighting: Soft warm golden hour light bathes the hands and the paper. The stadium in the background is beautifully blurred with bokeh.

Composition: hands centered, occupying the middle 80% of the frame.

Color palette: cream paper, white cuffs, gold, stadium green bokeh, warm sunset tones. Elegant, professional, no face at all."""
    },

    {
        "filename": "d04_sideprofile_headset.png",
        "concept": "横顔シルエット × ヘッドセットマイク",
        "reasoning": "プロアナウンサー感 × 匿名性。球場照明のドラマチックさ",
        "prompt": f"""{BASE_STYLE}

Scene: Side profile view from chin-down only. A woman wearing a professional thin headset microphone (the kind stadium announcers use) near her mouth. Only her chin, lips, jawline, neck, and the ear with the headset mic are visible. Her hair is swept into a neat professional bun or ponytail.

She wears a crisp white blouse collar visible at the bottom of the frame.

Background: Out-of-focus baseball stadium during golden hour — stadium lights starting to come on, warm sunset in the sky. Blurred silhouettes of players on the field.

Lighting: Warm golden hour sunlight from the left catches her jaw, the headset mic, and her ear. Professional, legitimate, broadcast atmosphere.

Composition: jawline + headset mic centered.

Color palette: warm gold, white, skin tones, hints of stadium green and sunset orange. Elite professional aesthetic."""
    },

    {
        "filename": "d05_uniform_mic.png",
        "concept": "胸元+制服 × マイク",
        "reasoning": "球場制服の雰囲気 × プロマイク。職業明示力No.1",
        "prompt": f"""{BASE_STYLE}

Scene: Chest-level close-up of a woman wearing a formal Japanese baseball stadium announcer uniform — a crisp white blouse with a small team-colored scarf or tie at the neck, and a dark blazer or vest. A small enamel stadium pass / press badge clips to her chest pocket. She holds a small professional microphone just below her chin. Only her hand, the mic, the uniform details, and her lower jaw/lips are visible.

Background: Sunny stadium infield visible but softly blurred behind her.

Lighting: Clean, bright daylight. Crisp professional photography feel.

Composition: uniform badge + microphone + lips all within the central circular area.

Color palette: white, navy, team color accents (red or blue), warm daylight, natural skin. Absolutely legitimate and professional — like an official team photo."""
    },
]


def generate_image(prompt, filename, client_idx=0):
    client = clients[client_idx % len(clients)]
    print(f"  [{client_idx % len(clients) + 1}/3] Generating: {filename}")
    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE","TEXT"])
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                path = OUT_DIR / filename
                data = part.inline_data.data
                if isinstance(data, str): data = base64.b64decode(data)
                path.write_bytes(data)
                print(f"    Saved: {path.name}")
                return True
        return False
    except Exception as e:
        print(f"    Error: {e}"); return False


if __name__ == "__main__":
    print(f"=== さくら 昼ウグイス嬢プロフ 5パターン生成 ===")
    print(f"Output: {OUT_DIR}\n")
    success = 0
    for i, img in enumerate(IMAGES):
        print(f"[{i+1}/5] {img['concept']}")
        if generate_image(img["prompt"], img["filename"], client_idx=i):
            success += 1
        if i < len(IMAGES) - 1: time.sleep(3)
    print(f"\n=== Done: {success}/5 ===")
