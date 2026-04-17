#!/usr/bin/env python3
"""
さくらTikTokプロフィール画像 — 10パターン生成
条件:
- 正方形 1:1（TikTokは円クロップ）
- 顔上部（鼻から上）は絶対に映さない
- 中央構図（円クロップで端が切れる）
- 暖色の照明、暗背景、親密な空気感
- ブランド: 声 × マイク × ウグイス嬢 × 深夜のベッド
"""

import os, time, base64, subprocess, sys
from pathlib import Path

def load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'], capture_output=True, text=True, timeout=5)
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
OUT_DIR = Path(__file__).parent / "sakura_profile_candidates"
OUT_DIR.mkdir(exist_ok=True)

# 共通スタイル
BASE_STYLE = """Photorealistic portrait, SQUARE 1:1 format (this is critical — will be center-cropped into a circle for TikTok profile).
Japanese woman in mid-20s. ABSOLUTE RULE: Face above the upper lip is NEVER visible — cropped out, in deep shadow, or out of frame.
Composition: Subject centered, dramatic lighting, intimate nighttime atmosphere.
Mood: mysterious, elegant, sensual but tasteful. Professional photography quality."""

IMAGES = [
    # === 01: 唇+マイク 王道（s1_lipsの進化版、背景をボカして中央集中）===
    {
        "filename": "p01_lips_mic_classic.png",
        "concept": "唇+マイク 王道",
        "reasoning": "ブランドの核。声のプロ × 親密さ を最短距離で伝える",
        "prompt": f"""{BASE_STYLE}

Scene: Extreme close-up of soft parted lips touching a professional studio microphone. Only the lips, chin, jawline, and lower cheek are visible — the upper face (nose, eyes) is cropped out above. The microphone fills the right side of the frame. Her lips are slightly glossy, natural color, about to whisper.

Lighting: Single warm amber rim light from the right side, creating a golden glow on her lips and chin. Deep black background. A subtle second light catches her jawline.

Center the lips in the frame (they will be inside the circular crop on TikTok).

Color palette: warm gold, deep blacks, soft skin tones, touch of rose on the lips.
Composition: subject centered, symmetric, instantly scroll-stopping."""
    },

    # === 02: 鎖骨+マイクストラップ ===
    {
        "filename": "p02_collarbone_strap.png",
        "concept": "鎖骨 × マイクストラップ",
        "reasoning": "色気と声のプロ感を両立。顔を全く映さなくても成立する角度",
        "prompt": f"""{BASE_STYLE}

Scene: Close-up of a woman's elegant collarbone, neck, and shoulder area. A thin black microphone strap crosses her collarbone diagonally. A delicate gold chain necklace rests on her skin. Her face is completely cropped out above the neck.

She wears a thin black silk camisole with one spaghetti strap sliding slightly off her shoulder.

Lighting: Warm golden light from the upper left catches her collarbone and neck curve. The rest fades to deep black.

Center the collarbone in the frame. The image should feel like elegant studio portrait photography.

Color palette: warm gold, cream skin, deep black, subtle rose."""
    },

    # === 03: 唇+指をシーっ ===
    {
        "filename": "p03_shh_gesture.png",
        "concept": "「しーっ」ジェスチャー",
        "reasoning": "視聴者と秘密を共有する親密感。ASMR系で最強のアイコン",
        "prompt": f"""{BASE_STYLE}

Scene: Close-up of lips and a single index finger pressed vertically against them in a classic "shh" gesture. Only the lips, finger, chin, and lower jawline are visible. Slight smile curving the corners of her mouth. Nail is clean, natural, well-manicured.

Lighting: Soft warm light from the upper right, creating dramatic shadows on her finger and lips. The background is completely dark.

Center the finger+lips combo in the middle of the frame for circular crop safety.

Color palette: warm amber, deep black, natural skin tones. Intimate, conspiratorial mood."""
    },

    # === 04: 口元+野球帽のつば ===
    {
        "filename": "p04_lips_cap_brim.png",
        "concept": "唇 × 野球帽のつば",
        "reasoning": "ウグイス嬢の野球要素を唯一ビジュアル化できる構図。ジャンル明示",
        "prompt": f"""{BASE_STYLE}

Scene: Close-up from below. Her lips and chin are visible, and above the lips you can see the underside of a vintage baseball cap brim casting a shadow across her upper face. The cap is dark navy blue with subtle embroidery. Only the brim is visible — no face above the nose.

She wears a thin white t-shirt or camisole underneath.

Lighting: Warm light from below (like a phone screen), illuminating her lips and the underside of the cap brim. Dramatic shadow where her eyes would be.

The cap brim creates the "face is hidden" effect naturally. Center the lips and cap brim in frame.

Color palette: navy blue, warm gold, cream skin, deep shadow."""
    },

    # === 05: 後ろ姿+ヘッドホン ===
    {
        "filename": "p05_back_headphones.png",
        "concept": "後ろ姿 × プロ用ヘッドホン",
        "reasoning": "声を聴く・録る側の象徴。ASMR制作者としてのポジショニング",
        "prompt": f"""{BASE_STYLE}

Scene: Back view of a woman wearing large professional studio headphones (black with gold accents). Long dark hair flowing down her bare shoulders. She wears a thin black camisole. Only her back, shoulders, hair, and the headphones are visible — her face is completely turned away.

Lighting: Single warm amber light from the right creates a beautiful rim light along her shoulder and hair. Deep black background.

The headphones are the visual anchor — large, circular, professional. They will remain centered in the circular TikTok crop.

Color palette: deep black, warm gold rim light, dark hair, skin tones."""
    },

    # === 06: 手でマイクを包む ===
    {
        "filename": "p06_hands_cradle_mic.png",
        "concept": "両手で包むマイク",
        "reasoning": "「この声、大切に」感。プロ感 × 愛着 × 親密さ",
        "prompt": f"""{BASE_STYLE}

Scene: Two elegant hands cradling a small vintage-style microphone, held close to the lower face. Only the lips and lower chin are visible at the top of the frame. The hands are the main subject — delicate, feminine, with a thin gold bracelet.

She wears a thin black silk top.

Lighting: Warm focused light on the hands and microphone, like a stage spotlight. Everything else fades to black.

Center the hands + microphone in the frame. The composition should look like a precious object being offered.

Color palette: warm gold, brass/copper microphone, cream skin, deep black."""
    },

    # === 07: 口元+台本をなぞる指 ===
    {
        "filename": "p07_lips_script_finger.png",
        "concept": "唇 × 台本をなぞる指",
        "reasoning": "練習中のリアルさ。ウグイス嬢の「仕事の延長」文脈が伝わる",
        "prompt": f"""{BASE_STYLE}

Scene: Close-up showing lips slightly parted (about to read), and an index finger pointing at a handwritten script paper. Japanese text is visible on the paper (looks like announcer notes). The lips and the finger-on-paper are the two focal points.

Lighting: Warm desk lamp light from the upper left, creating a cozy late-night study atmosphere.

Compose so both the lips and the pointing finger are visible in the central circle.

Color palette: warm amber, cream paper, skin tones, subtle shadows. Intimate, studious mood."""
    },

    # === 08: 横顔シルエット + ネオン ===
    {
        "filename": "p08_silhouette_neon.png",
        "concept": "横顔シルエット × ピンクネオン",
        "reasoning": "アート性。TikTok内で埋もれない差別化。完全匿名性",
        "prompt": f"""{BASE_STYLE}

Scene: Pure silhouette of a woman's side profile — only the outline of her jawline, chin, lips, and neck visible as a black silhouette. Behind her is a soft pink/magenta neon glow creating a halo effect around her silhouette.

No facial features visible — pure shape against the glowing background.

Lighting: Strong pink neon backlight creating dramatic silhouette. The front of her face is in deep shadow.

This is a highly artistic, minimalist, instantly recognizable image.

Color palette: pure black silhouette, vibrant pink/magenta neon, soft purple edges.
Composition: profile centered, fills the circular crop area."""
    },

    # === 09: 唇+口紅 ===
    {
        "filename": "p09_lips_lipstick.png",
        "concept": "唇 × 口紅を塗る瞬間",
        "reasoning": "フェミニン × 準備の儀式感。女性ファン・カップル層にもリーチ",
        "prompt": f"""{BASE_STYLE}

Scene: Extreme close-up of lips with a tube of rose-red lipstick being applied. The lipstick is mid-application, touching the lower lip. Her upper face is cropped out.

Lighting: Clean warm light from the front, showing off the soft texture of the lips and the glossy lipstick.

Center the lips and lipstick in the frame.

Color palette: rose red, warm amber, cream skin, dark background. Feminine, sensual, ready-for-showtime mood."""
    },

    # === 10: 耳元+マイク ===
    {
        "filename": "p10_ear_mic_asmr.png",
        "concept": "耳元 × マイク（究極ASMR）",
        "reasoning": "ASMRアイコンとして完璧。耳元トリガーで視聴者の脳に直接届く印象",
        "prompt": f"""{BASE_STYLE}

Scene: Close-up of a woman's ear, jawline, and neck — a small professional microphone is positioned right at her ear level, as if she's whispering to the mic. Her hair is swept behind the ear, revealing a delicate gold earring.

Only the side of her face from the nose down, ear, jawline, and neck are visible.

Lighting: Warm golden light catches the ear, earring, and microphone. Deep black background.

Center the ear + microphone in the frame. This represents the ultimate ASMR experience.

Color palette: warm gold, cream skin, dark hair, deep black. Ultimate ASMR atmosphere."""
    },
]

def generate_image(prompt, filename, client_idx=0):
    client = clients[client_idx % len(clients)]
    print(f"  [{client_idx % len(clients) + 1}/3] Generating: {filename}")
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
                print(f"    Saved: {path.name}")
                return True
        print(f"    No image data"); return False
    except Exception as e:
        print(f"    Error: {e}"); return False

if __name__ == "__main__":
    print(f"=== さくらプロフィール画像 10パターン生成 ===")
    print(f"Output: {OUT_DIR}\n")
    success = 0
    for i, img in enumerate(IMAGES):
        print(f"[{i+1}/10] {img['concept']}")
        if generate_image(img["prompt"], img["filename"], client_idx=i):
            success += 1
        if i < len(IMAGES) - 1: time.sleep(3)
    print(f"\n=== Done: {success}/10 ===")
