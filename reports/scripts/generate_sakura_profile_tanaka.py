#!/usr/bin/env python3
"""
さくら プロフィール画像 — 田中みな実似キャラ × 地方球場 × 10パターン
コンセプト: 清楚・ベテラン感・地方球場の情緒

参照画像: d04_sideprofile_headset.png をキャラ参照として使用
(顔の特徴・髪型・服装の一貫性を保つため)
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

# 参照画像（キャラクターの一貫性用）
REFERENCE_IMAGE = OUT_DIR / "d04_sideprofile_headset.png"

BASE = """Photorealistic SQUARE 1:1 photo, smartphone-captured candid quality with natural iPhone grain and slight softness.

IMPORTANT - Character consistency: Use the reference image. The woman in this photo is:
- Late 20s to early 30s Japanese woman
- Looks like Japanese TV announcer Minami Tanaka (田中みな実)
- Elegant, clean, very professional "清楚" aesthetic
- Dark brown hair usually in a neat low bun or ponytail
- Wears a crisp clean white blouse
- Slim, refined features, mature veteran vibe
- Experienced stadium announcer (ウグイス嬢) - not a rookie

ABSOLUTE RULE: Face above the nose is NEVER shown. Always from behind, distant profile silhouette, or cropped out above.

Setting: A SMALL LOCAL JAPANESE BASEBALL STADIUM - NOT Koshien, NOT Jingu, NOT Tokyo Dome. A quiet regional ballpark in countryside/suburban area with modest bleachers, simple scoreboard, few spectators. Feels personal, intimate, regional. NOT a famous landmark stadium.

Background: Heavily blurred (strong bokeh), the stadium is soft and dreamy. Focus is on the subject."""

IMAGES = [
    {
        "fn": "t01_back_sunset_empty.png",
        "concept": "夕陽の地方球場 × 白ブラウスの後ろ姿",
        "prompt": f"""{BASE}

Scene: Back view of her standing at the edge of a quiet local baseball stadium during golden hour sunset. She wears a crisp clean white blouse and a simple thin navy ribbon tied at her nape (visible from behind). Her dark hair is neatly pulled into a low elegant bun. Shoulders look calm, composed - a woman at the end of a long working day.

Background: Heavily bokeh-blurred local stadium. Distant simple bleachers, a basic scoreboard, the setting sun creating warm orange light. No crowds, maybe 5-10 scattered silhouettes of people in the stands.

Lighting: Golden hour sunlight from the front-left creates a beautiful rim light along her shoulders and hair bun. Warm cinematic atmosphere.

Composition: her back centered, bun at upper third, blurred stadium surrounding her.

Color palette: warm gold, soft orange sunset, cream white blouse, dark brown hair. Nostalgic, contemplative mood."""
    },

    {
        "fn": "t02_back_booth_window.png",
        "concept": "ブース窓際の後ろ姿 × 地方球場",
        "prompt": f"""{BASE}

Scene: Back view of her sitting or standing in a modest announcer booth, looking out through a window at a local baseball field. Her dark hair is in a low bun. She wears a white blouse. One hand gently touches the window frame or rests on the announcer desk.

Through the window: a quiet local stadium with dusty infield, modest green outfield, simple old scoreboard, minimal crowd. Bright daylight.

Background: The window fills most of the frame behind her. Heavy depth of field blur on everything outside.

Lighting: Natural daylight from the window creates a soft silhouette effect. The back of her blouse has a soft luminous quality.

Composition: back of her head + bun centered, window framing her.

Color palette: white blouse, warm daylight, soft blurred greens and browns."""
    },

    {
        "fn": "t03_bun_closeup_stadium.png",
        "concept": "低めお団子ヘア × 肩のアップ",
        "prompt": f"""{BASE}

Scene: Close-up from behind - focused on her elegant low bun hairstyle, nape of her neck, and the collar of her crisp white blouse. A small thin silver hair clip catches the light. Her shoulders and a bit of her upper back are visible.

Background: Extremely blurred local stadium - you can barely make out green field and wooden bleachers. Golden hour warmth fills the background.

Lighting: Soft warm afternoon light catches her hair, the silver clip, and the white fabric of her blouse.

Composition: bun + nape centered in the frame.

Color palette: warm gold, dark brown hair, crisp white, hints of silver. Delicate and refined."""
    },

    {
        "fn": "t04_profile_distant_silhouette.png",
        "concept": "遠目の横顔シルエット × 夕陽",
        "prompt": f"""{BASE}

Scene: Distant side silhouette shot - she is standing at the edge of a local stadium, her profile facing the sunset. The camera is pulled back so she appears as a graceful silhouette in the middle distance. Only her refined posture, hair bun, and the outline of her blouse are visible. Face is too far and in shadow to see features.

Background: Expansive bokeh of a modest local baseball stadium, warm sunset sky with pink and orange clouds, distant field lights just starting to glow.

Lighting: Strong backlight from the sunset, creating a near-silhouette effect. Her figure is outlined by golden rim light.

Composition: her silhouette in the center, sunset filling the frame.

Color palette: warm orange/pink sunset, dark silhouette, hints of golden highlights."""
    },

    {
        "fn": "t05_back_walking_corridor.png",
        "concept": "球場通路を歩く後ろ姿",
        "prompt": f"""{BASE}

Scene: Back view of her walking away from the camera through a concrete corridor/tunnel of a small local stadium, toward the bright light of the field ahead. She wears a crisp white blouse and a thin navy ribbon. Her hair in an elegant low bun. She holds a small script or folder in her right hand.

Background: The corridor frames her, with the bright green field visible in the distance. Heavy motion blur suggesting she's walking.

Lighting: Silhouette-style - she's backlit by the field light, rim-lit from behind. Her blouse has a glow where the light touches.

Composition: her walking figure centered, corridor framing her on all sides.

Color palette: dark corridor, warm field light ahead, white blouse glowing softly."""
    },

    {
        "fn": "t06_back_bleachers_empty.png",
        "concept": "無人スタンド × 後ろ姿",
        "prompt": f"""{BASE}

Scene: Back view of her sitting or standing in the empty wooden bleachers of a quiet local baseball stadium (before or after a game). She looks out at the empty field. White blouse, low bun, simple and composed posture.

Background: Rows of empty wooden bleacher seats, the empty field beyond, distant modest scoreboard. Heavily blurred, dreamy atmosphere.

Lighting: Late afternoon soft warm light. A few scattered sunbeams through clouds.

Composition: her back centered, surrounded by empty seats - evokes solitude and quiet pride in her work.

Color palette: weathered wood brown, soft greens, cream white blouse, warm sunlight. Melancholic and beautiful."""
    },

    {
        "fn": "t07_hand_script_blur_field.png",
        "concept": "台本を持つ手 × ぼけた地方球場",
        "prompt": f"""{BASE}

Scene: Close-up of her hands holding a handwritten announcer's lineup script with Japanese kanji characters. A thin gold bracelet on her wrist. White blouse cuffs visible. Only hands and the paper.

Background: Extremely blurred local baseball stadium - you can barely tell it's a ballpark. Soft greens and browns with warm sunset light.

Lighting: Warm golden hour light bathes the paper and her delicate hands.

Composition: hands + paper centered, taking up the main subject area.

Color palette: cream paper, white cuffs, gold bracelet, blurred warm stadium tones. Elegant, understated, professional."""
    },

    {
        "fn": "t08_back_field_light_tower.png",
        "concept": "ナイター照明塔を見上げる後ろ姿",
        "prompt": f"""{BASE}

Scene: Back view of her standing on the field or near the dugout of a small local stadium at dusk, looking up at an old-fashioned stadium light tower that's just starting to glow. White blouse, low bun, graceful posture. One hand lightly touches her own elbow - a contemplative pose.

Background: A modest local baseball stadium at twilight. An old light tower dominates the background, glowing warmly against the purple-blue sky. Dusty infield, worn grass. Blurred slightly.

Lighting: Magic hour - soft purple-blue sky + warm glow from the light tower. She is backlit subtly.

Composition: her back in the lower third, the light tower rising above her in the background.

Color palette: purple-blue twilight, warm tungsten light tower glow, white blouse, dark hair. Cinematic, poetic."""
    },

    {
        "fn": "t09_side_profile_far_crowd.png",
        "concept": "横顔遠景 × まばらな観客",
        "prompt": f"""{BASE}

Scene: A distant side profile shot of her in the announcer's booth during a game. The camera is pulled back so her face is barely readable - just the graceful shape of her bun, the line of her white collar, and the suggestion of her posture. Her face is in shadow or too small to make out features.

Background: A modest local stadium during a day game. Sparse crowd (maybe 50-80 people scattered in the bleachers, not full), simple old scoreboard, dusty field. Everything softly blurred.

Lighting: Natural daylight with warm tones. Soft and slightly overexposed like a real iPhone photo.

Composition: her profile silhouette on one side, the stadium filling the rest of the frame.

Color palette: stadium greens and browns, white blouse highlight, soft blue sky. Natural and authentic."""
    },

    {
        "fn": "t10_back_ribbon_detail.png",
        "concept": "白ブラウスとリボンの後ろ姿ディテール",
        "prompt": f"""{BASE}

Scene: Back view detail shot - focused on the nape of her neck, the elegant low bun, and the thin navy ribbon tied at the back of her white blouse collar. Her neck is graceful, refined. Small silver earring studs visible in her ears.

Background: Completely bokeh-blurred local stadium scene - soft warm sunset colors, suggestion of green field and wooden seats, but nothing is in focus.

Lighting: Soft warm directional light from the right, catching the hair bun, the ribbon, and the blouse.

Composition: nape + bun + ribbon centered in the frame - this is an intimate detail shot that feels like a candid moment.

Color palette: dark brown hair, cream white blouse, deep navy ribbon, warm sunset bokeh. Delicate, elegant, refined."""
    },
]


def generate_image(prompt, filename, client_idx=0):
    client = clients[client_idx % len(clients)]
    print(f"  [{client_idx % len(clients) + 1}/3] Generating: {filename}")
    try:
        # Load reference image
        from PIL import Image
        ref_img = Image.open(REFERENCE_IMAGE)

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt, ref_img],
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
    if not REFERENCE_IMAGE.exists():
        print(f"Reference image not found: {REFERENCE_IMAGE}"); sys.exit(1)

    print(f"=== さくら 田中みな実系 × 地方球場 × 10パターン ===")
    print(f"Reference: {REFERENCE_IMAGE.name}")
    print(f"Output: {OUT_DIR}\n")
    success = 0
    for i, img in enumerate(IMAGES):
        print(f"[{i+1}/10] {img['concept']}")
        if generate_image(img["prompt"], img["fn"], client_idx=i):
            success += 1
        if i < len(IMAGES) - 1: time.sleep(3)
    print(f"\n=== Done: {success}/10 ===")
