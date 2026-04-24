#!/usr/bin/env python3
"""ameru banner16: Geminiで4コンセプト × 各2枚 = 計8枚生成
モデル: Nano Banana Pro (nano-banana-pro-preview)
出力: banner-park/output/ameru/banner16/P{N}/gemini_{1..2}.png

各コンセプトから Gemini 向け角度（フォトリアル・質感・手元・ライフスタイル）を抽出。
API key rotation (GEMINI_API_KEY_1/2/3) 対応。
"""
import os, sys, time, warnings, traceback
warnings.filterwarnings("ignore")
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from google import genai
from google.genai import types

# ----------------------------------------------------------------------------
# API keys (rotation)
# env → fallback to parsing ~/.zshrc
# ----------------------------------------------------------------------------
def _load_keys_from_zshrc():
    import re
    zshrc = Path.home() / ".zshrc"
    if not zshrc.exists():
        return {}
    out = {}
    for line in zshrc.read_text().splitlines():
        m = re.match(r'\s*export\s+(GEMINI_API_KEY(?:_\d+)?)\s*=\s*"([^"]+)"', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out

_zshrc = _load_keys_from_zshrc()
API_KEYS = []
for i in (1, 2, 3):
    k = os.environ.get(f"GEMINI_API_KEY_{i}") or _zshrc.get(f"GEMINI_API_KEY_{i}")
    if k:
        API_KEYS.append(k)
if not API_KEYS:
    fallback = os.environ.get("GEMINI_API_KEY") or _zshrc.get("GEMINI_API_KEY")
    if fallback:
        API_KEYS = [fallback]
# dedupe preserving order
seen = set(); API_KEYS = [k for k in API_KEYS if not (k in seen or seen.add(k))]
assert API_KEYS, "GEMINI_API_KEY_1〜3 または GEMINI_API_KEY が未設定 (env / ~/.zshrc 双方で見つからず)"

print(f"=== Gemini API keys loaded: {len(API_KEYS)} ===")

MODEL = "nano-banana-pro-preview"

# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------
OUT_ROOT = Path("/Users/ca01224/Desktop/一進VOYAGE号/banner-park/output/ameru/banner16")
for p in ("P1", "P2", "P3", "P4"):
    (OUT_ROOT / p).mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Shared style preamble (brand-guide / forbidden を全プロンプトに内包)
# ----------------------------------------------------------------------------
STYLE = """Generate a square 1:1 (1024x1024) social banner for Japanese D2C amigurumi kit brand "ameru" — a collaboration with Japanese IP「らぶいーず®」(official Nippon TV property). Target: Japanese women 25-40s, Instagram / Meta feed.

=== ABSOLUTE BRAND RULES (STRICT) ===
- The IP name is ALWAYS written in hiragana: 「らぶいーず」 — NEVER use English "Love is...", "loveeez", "LOVE IS" anywhere in the image.
- 5 official characters ONLY (use the correct hiragana name when referenced):
    * すもっぴ (sumoppi) — sky-blue and white small bear-like plush
    * ぴょんちー (pyonchii) — pink bunny plush
    * にゃぽ (nyapo) — cream / pale-lavender cat plush with a yellow ribbon
    * うるる (ururu) — gray / pale-lavender dreamy plush
    * ぱおぱお (paopao) — mint-green small elephant plush
- Color palette base: pink-beige #F4E5DC, ivory #FBF5EC, milk-white. Accent colors follow character palette above.
- Typography (if Japanese text is rendered in the image): 和文ゴシック太字・角丸, clean, high legibility. Text must render perfectly — no garbled glyphs, no fake characters.
- Photorealistic Japanese high-end D2C aesthetic (FUJIMI / SHIRO / Craftie Home Box magazine quality). Soft natural window light, generous whitespace, warm, feminine, crafted.
- The amigurumi must look HAND-CROCHETED with visible tubular-yarn crochet stitches — not industrial plush.

=== FORBIDDEN (NEVER INCLUDE) ===
- English "Love is..." / "loveeez" / any romanization of the IP name.
- Counter "1匹" / "1個" for plush — only 「1体」 is correct.
- Time-dependent words in any burned-in copy: "本日より", "今日から", "24時間限定", "いまだけ".
- Negative anchor copy "買うより" / "買うのではなく".
- Competitor brand names or comparison to specific products.
- The same image being reused across banners — each banner must be visually distinct.
- Birthday-specific triggers ("誕生月", "すもっぴ誕生日").

=== COMPOSITION PRINCIPLES ===
- Square 1:1 format, Instagram feed-safe.
- If copy is burned in, keep it to <= 12 Japanese characters max, positioned with generous margin.
- Brand marks: tiny ameru wordmark bottom-left, tiny 「らぶいーず® 日本テレビ公式」 pill badge top-right (optional — omit if it clutters).
- Prefer leaving negative space for potential overlay text (most banners will have copy applied later in post).
"""

# ----------------------------------------------------------------------------
# 8 banner prompts (4 concepts × 2 Gemini angles)
# ----------------------------------------------------------------------------
BANNERS = {
    # ===== P1: 推し活IP発見（田中さとみ）=====
    "P1/gemini_1.png": {
        "title": "P1-2 N=1所有欲×固有性（手の中のすもっぴ・マクロ）",
        "prompt": """CONCEPT P1 / ANGLE: N=1 ownership × uniqueness. Macro photoreal hero.
HEADCOPY (optional overlay reference, do NOT burn in): 「世界で1体の、わたしのすもっぴ。」

VISUAL DESCRIPTION:
A hand-crocheted sky-blue-and-white amigurumi plush character「すもっぴ」(roughly the size to sit in a cupped palm) gently held in both hands of a 30s Japanese woman. Only the hands and wrists are visible, cream knit cardigan sleeves, natural unpainted short nails, soft skin tone. The plush is rendered with rich crochet-stitch macro detail — you can see individual yarn fibers, the tubular crochet texture, tiny black bead eyes, a soft white round muzzle.
Background: soft out-of-focus creamy ivory / pink-beige (#FBF5EC → #F4E5DC) bokeh, suggesting a sunny morning living room. The light is a diffused north-window quality — soft, warm, no harsh shadow.
Depth of field: shallow (f/2.0 feel), focus locked on the plush face and the woman's fingertips.
Camera angle: slightly top-down, intimate — like she is showing it to herself.
Feeling: hushed delight, "this one is mine, one in the world". No confetti, no multiple characters — just this single すもっぴ and the two hands.
No burned-in text. Leave the top third clean for potential copy overlay.
""",
    },
    "P1/gemini_2.png": {
        "title": "P1-4 UGC保存数ドリブン（手元×スマホ×完成すもっぴ）",
        "prompt": """CONCEPT P1 / ANGLE: UGC-ready lifestyle — finished plush shot alongside a phone.
HEADCOPY reference (not burned in): 「保存数がつく、推しができた。」

VISUAL DESCRIPTION:
Overhead 45-degree angled flat-lay on an ivory linen table. On the table:
- A completed hand-crocheted sky-blue-and-white すもっぴ amigurumi (roughly palm-sized), sitting upright.
- An iPhone (neutral, no specific logo visible) lying next to it, screen showing a soft-focus generic photo-grid Instagram-style layout (DO NOT render any real UI elements, no "Love is..." text, no brand names — only an abstract photo-grid feel with pink-beige and ivory thumbnails). Screen is dimly lit, not glaring.
- A pink-beige ameru package box partially in frame (corner), with clean ivory and sky-blue design.
- A small ball of sky-blue tubular yarn and a natural wooden crochet hook with a thin pink ribbon.
- A 30s Japanese woman's hand (only wrist and fingers visible) resting casually next to the plush, reaching toward it — as if she just finished photographing it.
Lighting: late-morning soft daylight from upper-left window, warm white balance.
Mood: "I just made this and I want to share it" — curated, calm, proud but not flashy.
Depth of field: medium, everything in the scene readable.
No burned-in copy. The image itself should feel shareable — the kind someone would save.
""",
    },

    # ===== P2: デジタル解毒（村上あかり）=====
    "P2/gemini_1.png": {
        "title": "P2-03 静謐の夜・手元マクロ（ランプ・かぎ針・湯気）",
        "prompt": """CONCEPT P2 / ANGLE: Digital-detox quiet night — photoreal hand-macro in low warm light.
HEADCOPY reference (not burned in): 「今夜、手のなかだけを見ていたい。」

VISUAL DESCRIPTION:
Interior scene, 22:00 at night, small Tokyo apartment. A 30s Japanese woman (no face — only hands, forearms, cream linen sleeves visible) sits at a small round wooden side table. In her hands: a natural wooden crochet hook and a half-finished sky-blue tubular-yarn amigurumi piece (looks like the early body of a すもっぴ — not yet a full character, to avoid "completed plush" porn).
On the table:
- A small skein of sky-blue yarn, softly lit.
- A white ceramic mug with faint steam rising (herbal tea or hojicha).
- A single warm amber pendant lamp (color temperature ~2700K) casting a soft circle of light — the ceiling lights are OFF.
- An iPhone placed FACE-DOWN at the edge of the table (screen not visible — this is important: the device is silenced and hidden).
- A small window in the deep background shows softly blurred city lights (bokeh, very distant).
Lighting: single-source warm amber lamp, deep soft shadows, rim light on the yarn fibers showing crochet texture beautifully.
Color palette: ivory #FBF5EC + amber lamp glow #E8B86D + muted sky-blue yarn + warm brown wood.
Mood: 静謐 (seihitsu / hushed stillness). You can almost hear the breathing. No confetti, no multiple characters, no gold.
Camera: 3/4 downward angle from over her shoulder, shallow DoF on the crochet hook tip.
No burned-in text. Leave negative space on the upper-right for potential vertical copy overlay.
""",
    },
    "P2/gemini_2.png": {
        "title": "P2-04 開封の瞬間・編み始め完成済みキット",
        "prompt": """CONCEPT P2 / ANGLE: Unboxing moment under warm lamp — the "already started" kit.
HEADCOPY reference (not burned in): 「編み始めは、済ませてあります。」

VISUAL DESCRIPTION:
Overhead macro shot at night, on a dark warm-wood table lit by a single amber desk lamp. An opened ameru package box (sky-blue and ivory color, clean minimalist design, matte finish) is centered. Inside the opened box:
- A pre-started amigurumi piece — a small tubular sky-blue crochet work with the magic ring and first few rounds already clearly completed (5-6 rounds of stitches visible), a wooden crochet hook tucked in with a neat small pink ribbon, a small skein of sky-blue yarn, tiny black bead eyes in a glassine paper packet, a small white instruction card.
- A 30s Japanese woman's fingertips (only index and thumb visible) gently touching the edge of the pre-started crochet piece, as if discovering it for the first time.
Lighting: one warm amber lamp overhead-left, deep velvety shadows, rich crochet-yarn fiber texture visible in the light.
Background: softly out-of-focus ivory linen cloth, corner of a book, a white ceramic mug.
Mood: quiet opening, a small gasp — "oh, it's already begun". Intimate, calm.
No English text on the package. The package design is minimalist — subtle ivory and sky-blue bands, optionally a tiny hiragana label「ameru」. NEVER write "Love is..." or English IP names.
Camera: near-top-down, slight tilt. Shallow DoF focused on the pre-started stitches.
Leave the lower-left corner clean for overlay copy.
""",
    },

    # ===== P3: フィエロ完結（小林ゆきの）=====
    "P3/gemini_1.png": {
        "title": "P3-1 5体全員集合・完結スナップ（水平正面・白背景マクロ）",
        "prompt": """CONCEPT P3 / ANGLE: All-5-together "completion" hero shot — photoreal, daylit.
HEADCOPY reference (not burned in): 「5体揃う日に、会いに行く。」

VISUAL DESCRIPTION:
A clean, bright photoreal shot of ALL FIVE hand-crocheted amigurumi plush characters arranged in a clear pair-structure on a soft ivory linen surface against a creamy pink-beige (#F4E5DC) seamless backdrop.
Arrangement (left to right, all roughly palm-size, shoulder-to-shoulder):
1. すもっぴ — sky-blue and white bear-like plush (leftmost, paired with 2)
2. ぴょんちー — pink rabbit plush with long soft ears (couple with 1)
3. ぱおぱお — mint-green small elephant plush with a trunk (CENTER, the single sibling)
4. にゃぽ — cream/pale-lavender cat plush with a yellow ribbon (couple with 5)
5. うるる — gray/pale-lavender cloud-like dreamy plush (rightmost, paired with 4)
The pair structure should read visually: [pair]  [single-center]  [pair]. The color sequence reads as a soft pastel rainbow left-to-right.
All 5 have the visible tubular-yarn crochet stitch texture — clearly hand-made, not industrial plush.
A VERY light sprinkling of tiny gold paper-confetti pieces gently falling in the air around them (subtle, celebratory but not busy).
Lighting: soft diffused window light from front-left, no harsh shadow, everything clearly readable.
Camera: horizontal, slightly eye-level, centered composition, symmetrical.
Depth of field: medium — all 5 plushes in focus.
Mood: "they're all here — completion". Quiet triumph, collector's joy.
No burned-in copy in the image. Leave the top 25% relatively clean for headline overlay.
""",
    },
    "P3/gemini_2.png": {
        "title": "P3-3 1組目カップル完成（すもっぴ×ぴょんちー寄り添い）",
        "prompt": """CONCEPT P3 / ANGLE: First couple completion — tender dyad macro.
HEADCOPY reference (not burned in): 「すもっぴから、ぴょんちーへ。」

VISUAL DESCRIPTION:
A gentle macro photograph of two hand-crocheted amigurumi plush characters leaning softly against each other:
- すもっぴ — sky-blue and white bear-like amigurumi
- ぴょんちー — pink rabbit amigurumi with long soft ears draped slightly to one side
They are sitting close, ぴょんちー's ear gently brushing すもっぴ's head, as if in a quiet moment of friendship. Both show detailed tubular-yarn crochet texture, tiny black bead eyes.
Background: very soft out-of-focus pink-beige + ivory gradient (#F4E5DC + #FBF5EC). A few small sprigs of dried かすみ草 (baby's breath) in soft bokeh behind them.
Lighting: warm afternoon window light from the right, soft rim light catching the yarn fibers.
Depth of field: shallow, focus on the two plush faces nearly touching.
Camera: horizontal, slightly lower-than-eye-level, giving them quiet dignity.
Mood: "they found each other" — the first pair completion milestone. Tender, hopeful.
No multiple-character crowd, no confetti (reserve that for the 5-all shot). Just these two.
Leave the bottom edge clean for a thin name-strip overlay.
""",
    },

    # ===== P4: ギフト贈与（橋本なな）=====
    "P4/gemini_1.png": {
        "title": "P4-03 渡す瞬間・受け取る側の表情",
        "prompt": """CONCEPT P4 / ANGLE: The moment of gift-giving — receiver's emotional reaction.
HEADCOPY reference (not burned in): 「完成したにゃぽを、両手で差し出す日まで。」

VISUAL DESCRIPTION:
Photoreal natural-light photograph, soft café or sunlit living-room entrance setting. A 26-year-old Japanese woman (the RECEIVER, center of frame) is holding a small opened gift — a completed hand-crocheted にゃぽ amigurumi plush (cream and pale-lavender cat with a tiny yellow ribbon around its neck) — in her cupped hands. Her face is the emotional center: wide slightly tearful eyes, a hand partially covering her mouth in surprised delight, soft pink blush on cheeks, natural makeup.
In the foreground: the giver's hand (only wrist and fingers visible, slightly out of focus) having just passed over the plush, a soft satin ivory ribbon loosely hanging from the handover.
Background: softly blurred café window with warm afternoon light, creamy bokeh, out-of-focus wooden tabletop and a small ivory-wrapped gift box with a handwritten card peeking (the writing on the card is NOT readable — abstract ink strokes, no English, no specific Japanese readable).
Lighting: warm afternoon window light, soft, no harsh shadow. Slight rim light on the receiver's hair.
Depth of field: shallow (f/1.8-2.0), focus locked on the receiver's eyes and the plush.
Color palette: warm ivory, soft pink-beige, cream yarn tones, natural skin.
Mood: "a private gift between two people" — intimate, surprising, no social-media vibe. Nothing in frame suggests Instagram or SNS.
Camera: slightly lower-than-eye-level, close-medium shot (chest-up of receiver).
No burned-in text. The image itself is the story.
""",
    },
    "P4/gemini_2.png": {
        "title": "P4-04 過去挫折→今度こそ（編みかけ→完成にゃぽ）",
        "prompt": """CONCEPT P4 / ANGLE: Past failure → this time completed. Before-after focus shift.
HEADCOPY reference (not burned in): 「手作りのギフト、今度こそ渡せる。」

VISUAL DESCRIPTION:
Photoreal still-life with a strong foreground-to-background focus shift.
FOREGROUND (lower-left, soft out-of-focus, slightly desaturated): a small tangled messy pile of old gray half-finished yarn with a dusty hook — representing a past unfinished attempt. It sits on a faded piece of paper.
BACKGROUND / MIDGROUND (in focus, upper-right, bathed in soft warm light): a beautifully completed hand-crocheted にゃぽ amigurumi (cream and pale-lavender cat with a yellow neck ribbon) sitting neatly inside a clean ivory gift box, with a soft satin pink-beige ribbon loosely tied. Next to the box, a tiny folded ivory card (no readable text — abstract).
The composition creates a visual bridge: from gray dusty failure (foreground) → warm hopeful completion (background), left-low to right-high diagonal.
Background wall: creamy ivory #FBF5EC wallpaper with very soft morning sunlight streaming from the upper-right window, gentle warm bokeh.
Lighting: directional morning light from upper-right, warm, hopeful.
Depth of field: very shallow — foreground is ~15% in focus (intentionally slightly blurry/faded), background is crisp and bright.
Color palette: foreground is muted gray with low saturation; background is full-saturation warm ivory, cream, pink-beige.
Mood: "the past didn't complete, but this time it did". Redemption, quiet triumph, gift-ready.
No burned-in text. Leave space in the upper-left for potential headline overlay.
""",
    },
}

# ----------------------------------------------------------------------------
# Generator with key rotation
# ----------------------------------------------------------------------------
_key_lock = None  # not needed; ThreadPool uses per-thread state
_key_idx = {"i": 0}
_key_history = []  # (relative_path, key_index)


def _get_client_for_attempt(attempt_idx: int):
    """Rotate key based on attempt index."""
    k = attempt_idx % len(API_KEYS)
    return genai.Client(api_key=API_KEYS[k]), k


def generate_one(rel_path: str, spec: dict, out_path: Path, max_retries: int = 3):
    print(f"\n[START] {rel_path} — {spec['title']}")
    prompt_full = STYLE + "\n\n=== THIS BANNER ===\n" + spec["prompt"]

    last_err = None
    for attempt in range(max_retries):
        cli, key_idx = _get_client_for_attempt(attempt)
        _key_history.append((rel_path, key_idx + 1, attempt + 1))
        try:
            t0 = time.time()
            resp = cli.models.generate_content(
                model=MODEL,
                contents=[
                    types.Content(
                        parts=[types.Part(text=prompt_full)],
                        role="user",
                    )
                ],
            )
            # extract image
            for cand in resp.candidates or []:
                for part in (cand.content.parts if cand.content else []):
                    if getattr(part, "inline_data", None) and part.inline_data.data:
                        out_path.write_bytes(part.inline_data.data)
                        dt = time.time() - t0
                        kb = len(part.inline_data.data) // 1024
                        print(f"[OK]    {rel_path} — key#{key_idx+1} attempt#{attempt+1} — {kb}KB / {dt:.1f}s")
                        return {"path": str(out_path), "status": "ok", "key": key_idx + 1, "attempt": attempt + 1, "seconds": dt, "size_kb": kb}
            # no image — possibly refusal / text-only
            tx = (resp.text or "")[:300] if hasattr(resp, "text") else ""
            print(f"[NOIMG] {rel_path} — key#{key_idx+1} attempt#{attempt+1} — no inline image. text={tx!r}")
            last_err = f"no inline image (text={tx!r})"
        except Exception as e:
            last_err = f"{type(e).__name__}: {str(e)[:300]}"
            print(f"[ERR]   {rel_path} — key#{key_idx+1} attempt#{attempt+1} — {last_err}")
            # backoff on rate limit
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e).upper() or "rate" in str(e).lower():
                time.sleep(2 + attempt * 2)
            else:
                time.sleep(1)

    return {"path": str(out_path), "status": "fail", "error": last_err}


def main():
    t_start = time.time()
    print(f"=== banner16 Gemini gen START ({len(BANNERS)} banners) ===")
    results = []

    # concurrency: 2 parallel to avoid hammering a single key too hard
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {}
        for rel, spec in BANNERS.items():
            out = OUT_ROOT / rel
            if out.exists() and out.stat().st_size > 30000:
                print(f"[SKIP]  {rel} — exists ({out.stat().st_size//1024}KB)")
                results.append({"path": str(out), "status": "skipped"})
                continue
            futs[ex.submit(generate_one, rel, spec, out)] = rel

        for fu in as_completed(futs):
            results.append(fu.result())

    total = time.time() - t_start
    print(f"\n=== DONE in {total:.1f}s ===")
    ok = [r for r in results if r.get("status") == "ok"]
    sk = [r for r in results if r.get("status") == "skipped"]
    ng = [r for r in results if r.get("status") == "fail"]
    print(f"  OK: {len(ok)} / SKIP: {len(sk)} / FAIL: {len(ng)}")
    for r in ng:
        print(f"    FAIL: {r['path']} — {r.get('error')}")

    # dump key history
    print("\n=== API key usage history ===")
    for (rp, k, at) in _key_history:
        print(f"  {rp}  key#{k}  attempt#{at}")

    # write prompts log
    log = OUT_ROOT.parent.parent.parent.parent / "reports" / "projects" / "ameru" / "banner16" / "prompts_gemini.md"
    # safer: absolute
    log = Path("/Users/ca01224/Desktop/一進VOYAGE号/reports/projects/ameru/banner16/prompts_gemini.md")
    lines = ["# ameru banner16 — Gemini プロンプト記録\n",
             f"生成モデル: `{MODEL}`\n",
             f"生成時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
             f"合計: {len(BANNERS)}枚 / OK: {len(ok)} / FAIL: {len(ng)}\n",
             "\n## 共通スタイル前文（STYLE）\n",
             "```\n" + STYLE + "\n```\n",
             "\n## 各バナー\n"]
    for rel, spec in BANNERS.items():
        lines.append(f"\n### {rel}\n**角度**: {spec['title']}\n\n```\n{spec['prompt']}\n```\n")
    log.write_text("".join(lines))
    print(f"\nPrompts log: {log}")


if __name__ == "__main__":
    main()
