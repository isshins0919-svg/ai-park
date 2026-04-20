"""
ameru LP画像 Phase1B — カテゴリB キット内容物 4本生成 (Woobles参照)
gemini-3-pro-image-preview / 並列3
"""
import os, time, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

API_KEYS = [k for k in [os.environ.get(f'GEMINI_API_KEY_{i}', '').strip() for i in range(1, 4)] if k]
if not API_KEYS:
    raise RuntimeError("GEMINI_API_KEY_1 が設定されていません")
print(f"✅ API Keys: {len(API_KEYS)}本")

clients = [genai.Client(api_key=k) for k in API_KEYS]

OUT_DIR = 'reports/clients/ameru/images/phase1'
SEED_DIR = 'reports/clients/ameru/images'
os.makedirs(OUT_DIR, exist_ok=True)

def load_image(path):
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/png')
    return data, mime

PROMPTS = [
    {
        "id": "K01",
        "file": "K01_kit_flatlay_woobles.png",
        "aspect": "1:1 square",
        "seed": "03_unboxing_flatlay.png",
        "prompt": """Top-down flat lay photograph of a complete crochet amigurumi kit on a clean white background, styled like The Woobles brand kit presentation. Arranged neatly in a grid pattern with equal spacing:
- 3 balls of smooth tube-style pastel yarn (soft cream, sky blue, dusty pink), chunky and clean-looking with no fraying
- 1 metal crochet hook with pastel mint green grip
- 1 pair of small black bead eyes on a small white card
- 1 embroidery needle
- 1 small cluster of white stuffing cotton
- 1 A5 instruction booklet with a cute cream amigurumi image on the cover
- 1 small pre-started crochet piece (a few rows already completed, as a beginner-friendly feature)
Style: bright minimal product photography, Japanese brand "ameru" variant of The Woobles kit aesthetic, clean studio lighting with slight shadows. 1:1 square. No text overlay, no logos beyond packaging."""
    },
    {
        "id": "K02",
        "file": "K02_yarn_macro_easy_peasy.png",
        "aspect": "1:1 square",
        "seed": None,
        "prompt": """Extreme macro close-up product photograph of a cream-colored smooth tube-style crochet yarn (similar to The Woobles' Easy Peasy Yarn). The yarn is noticeably thicker than regular cotton yarn, looks perfectly round and even like a soft tube, no frayed fibers visible, clean and beginner-friendly appearance. Coiled loosely on a white linen surface. One metal crochet hook with pastel grip resting diagonally next to it. Soft natural light from the left, sharp focus on the yarn texture showing the weave structure clearly. 1:1 square. No text, no logo. Professional macro product photography."""
    },
    {
        "id": "K03",
        "file": "K03_phone_hands_learning.png",
        "aspect": "4:5 portrait",
        "seed": "04_hands_crafting.png",
        "prompt": """A smartphone propped up vertically on a light wooden table, screen showing a crochet tutorial video (close-up shot of hands demonstrating a crochet stitch in the video). In front of the phone at a slight angle: two hands of a young woman (only hands and forearms visible, no face), mid-crocheting with cream-colored yarn and a pastel metal crochet hook, a small partially-completed amigurumi in progress. Cozy warm window light, light wooden table, one ball of white yarn next to the scene. The entire setup shows a clear "learning together" vibe: video+hands+in-progress craft all in one frame. 4:5 portrait composition. No text overlay."""
    },
    {
        "id": "K04",
        "file": "K04_unboxing_moment.png",
        "aspect": "4:5 portrait",
        "seed": "02_package_lifestyle.png",
        "prompt": """Overhead shot of hands opening a light blue kraft paper stand-up pouch labeled "ameru" (Japanese text), mid-action of revealing the contents: pastel yarn balls spilling out, crochet hook, instruction booklet partially visible. The opened package sits on a white linen surface with a few dried flower sprigs. Style inspired by The Woobles unboxing moments — excitement captured at the moment of opening. Top-down 3/4 angle, soft morning light, warm lifestyle tones. 4:5 portrait. No additional text overlay beyond the package logo."""
    },
]

def generate_one(idx, config):
    client = clients[idx % len(clients)]
    seed_path = f"{SEED_DIR}/{config['seed']}" if config['seed'] else None
    out_path = f"{OUT_DIR}/{config['file']}"
    print(f"🎨 [{config['id']}] 開始")
    start = time.time()
    try:
        parts = []
        if seed_path and os.path.exists(seed_path):
            data, mime = load_image(seed_path)
            parts.append(types.Part.from_bytes(data=data, mime_type=mime))
            parts.append(types.Part.from_text(
                text=f"Reference image provided above is the style reference. Generate a NEW image based on this description:\n\n{config['prompt']}\n\nAspect ratio: {config['aspect']}."
            ))
        else:
            parts.append(types.Part.from_text(text=f"{config['prompt']}\n\nAspect ratio: {config['aspect']}."))
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=[types.Content(role='user', parts=parts)],
            config=types.GenerateContentConfig(response_modalities=['IMAGE'])
        )
        saved = False
        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                if part.inline_data:
                    with open(out_path, 'wb') as f:
                        f.write(part.inline_data.data)
                    saved = True; break
            if saved: break
        elapsed = time.time() - start
        if saved:
            size_kb = os.path.getsize(out_path) / 1024
            print(f"✅ [{config['id']}] 完了 {elapsed:.1f}s ({size_kb:.0f}KB)")
            return {'id': config['id'], 'status': 'ok', 'path': out_path, 'time': elapsed}
        else:
            print(f"⚠️ [{config['id']}] no_image")
            return {'id': config['id'], 'status': 'no_image', 'time': elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ [{config['id']}] {str(e)[:120]}")
        return {'id': config['id'], 'status': 'error', 'error': str(e)[:200], 'time': elapsed}

print(f"\n🚀 Phase1B 4本 並列生成開始\n")
t0 = time.time()
results = []
with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(generate_one, i, p): p for i, p in enumerate(PROMPTS)}
    for f in as_completed(futures):
        results.append(f.result())
total = time.time() - t0
ok = sum(1 for r in results if r['status'] == 'ok')
print(f"\n🎉 完了: {ok}/{len(PROMPTS)} 成功 / 全体 {total:.1f}s")
