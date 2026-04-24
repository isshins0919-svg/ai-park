#!/usr/bin/env python3
"""ameru LP 10スクリーンを Imagen 4.0 (9:16) で生成。
出力: reports/projects/ameru/screens/01.png 〜 10.png
"""
import base64, json, os, urllib.request, time
from pathlib import Path

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
assert API_KEY, "GEMINI_API_KEY_1 が未設定"

MODEL = "imagen-4.0-generate-001"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:predict?key={API_KEY}"
OUT_DIR = Path(__file__).parent / "screens"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COMMON = (
    "smartphone vertical 9:16 composition, Japanese D2C brand aesthetic, "
    "muted dusty pastel palette (dusty sky blue, ivory, warm beige, soft pink), "
    "editorial product photography style, soft natural morning light, shallow depth of field, "
    "Kinfolk-magazine feminine mood, high-end, crafted, feminine, calm. "
)

SCREENS = [
    ("01.png", "FV / Hero",
     "A beautifully designed crochet kit package box in pale sky-blue and ivory white, "
     "sitting at a gentle angle on a soft cream paper background with subtle woven texture. "
     "A half-finished sky-blue bear-like amigurumi plush rests on the box, with a chunky "
     "tube-yarn ball, a wooden crochet hook, and a small pattern booklet. Tiny white flower "
     "petals scattered. Hero composition, centered. No text in the image. "
     "Leave bottom 15% quiet space for overlay text later."),
    ("02.png", "Empathy",
     "Two-panel vertical storytelling. Upper half: faded desaturated still life of a tangled "
     "messy yarn ball with a printed crochet pattern sheet full of dense symbols, a half-abandoned "
     "lumpy amigurumi looking sad. Lower half: bright airy soft-focus close-up of a young woman's "
     "hands (no face, neat nude manicure) smoothly working sky-blue tube yarn with a pre-started "
     "piece already formed, a smartphone playing a vertical tutorial beside her. Warm cafe light. "
     "No text in the image."),
    ("03.png", "Pre-started Only1",
     "Macro close-up product photo of a pre-started magic ring crochet piece in sky-blue tube yarn, "
     "neatly formed, ready to continue. Next to it a cream pattern card with a tiny arrow icon. "
     "A subtle comparison inset showing a tangled yarn vs the clean pre-started piece with a soft "
     "check-mark. Soft woven paper background. Ivory, sky blue, gentle coral accent. Top-down with "
     "slight depth. Editorial. No text in the image."),
    ("04.png", "Yarn Secret",
     "Five chunky tube-yarn balls lined up diagonally in dusty sky blue, powder pink, cream yellow, "
     "lavender gray, and mint green on a warm beige linen backdrop. One ball is cut in cross-section "
     "showing its tubular hollow structure. A wooden crochet hook passes cleanly through a stitch, "
     "ultra clear visibility. Minimal, feminine, Kinfolk product shot. Side natural light. "
     "No text in the image."),
    ("05.png", "Video Tutorial",
     "Cozy lifestyle flat-lay tilted composition: corner of a soft blanket, ceramic mug of tea, "
     "an iPhone showing a vertical crochet tutorial video (hands demonstrating a single stitch, "
     "UI chrome visible), a wooden crochet hook, pre-started sky-blue yarn, and a half-finished "
     "sky-blue bear amigurumi emerging. Ivory, dusty blue, soft peach palette. Cafe afternoon "
     "light. No readable text, just UI shapes."),
    ("06.png", "5 Characters Lineup",
     "Five finished soft amigurumi plush characters arranged in a semicircle on a cream cloud-shaped "
     "cushion, slightly derpy lovable style: a sky-blue and white bear-like plush (center forward), "
     "a pink rabbit-like plush, a cream-to-light-purple cat-like plush with a yellow ribbon, a "
     "gray-to-light-purple plush, and a mint green elephant-like plush. Soft gradient cream-to-blush "
     "backdrop, studio-soft lighting. Cute toy campaign photography. No text."),
    ("07.png", "Delivery Order Story",
     "Vertical soft watercolor illustration timeline down the center of the frame with 5 stops, "
     "each a small character silhouette in pastel signature colors (sky blue, pink, cream/lilac, "
     "gray/lilac, mint green) connected by a dotted line. Ivory background with subtle texture. "
     "Elegant infographic aesthetic, feminine, minimal. No text labels."),
    ("08.png", "Fiero & UGC",
     "Scrapbook moodboard composition of 4-5 overlapping Polaroid-style photos: a small sky-blue "
     "bear amigurumi plush on a coffee cup edge, in a woman's palm (hands only), sitting on a book "
     "stack by a window, on a desk with a succulent, and one Polaroid with a faint Instagram-story-"
     "style frame. Warm ivory, soft blush, gentle sage palette. Paper texture background. "
     "Emotional editorial lifestyle. No readable text."),
    ("09.png", "Offer Panel",
     "Clean offer-card layout: center-stage a pristine ameru kit package box with a small ribbon "
     "badge on the corner, on a soft cream paper background. Subtle stock-bar illustration and a "
     "minimal gold accent line. Ivory, dusty blue, soft gold. Editorial product layout. Leave "
     "large clean margins for price table overlay. No readable text, only graphic shapes."),
    ("10.png", "Final CTA",
     "A woman's hands (no face, around 30, soft cream cardigan sleeves) gently holding an unopened "
     "ameru kit package box, about to pull the ribbon. Warm golden hour light from the side, "
     "shallow depth of field, cinematic. Ivory, dusty blue, warm gold palette. Emotionally warm "
     "but not saccharine. Quiet mid-lower band area reserved for a button overlay. No text."),
]

def generate(prompt: str, out: Path, label: str, retries=2) -> bool:
    print(f"\n[{out.name}] {label}")
    payload = {
        "instances": [{"prompt": COMMON + prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "9:16",
            "personGeneration": "allow_adult",
        },
    }
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                URL,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            preds = result.get("predictions", [])
            if preds and "bytesBase64Encoded" in preds[0]:
                img = base64.b64decode(preds[0]["bytesBase64Encoded"])
                out.write_bytes(img)
                print(f"  ✅ {len(img)//1024}KB")
                return True
            print(f"  ❌ no image: {json.dumps(result)[:300]}")
        except Exception as e:
            print(f"  ❌ attempt {attempt+1}: {e}")
            if attempt < retries:
                time.sleep(3)
    return False

if __name__ == "__main__":
    print(f"=== ameru LP 10 screens via {MODEL} ===")
    for fname, label, prompt in SCREENS:
        out = OUT_DIR / fname
        if out.exists() and out.stat().st_size > 10000:
            print(f"[skip] {fname} ({out.stat().st_size//1024}KB)")
            continue
        generate(prompt, out, label)
        time.sleep(1)
    print("\n=== done ===")
    for f in sorted(OUT_DIR.glob("*.png")):
        print(f"  {f.name}: {f.stat().st_size//1024}KB")
