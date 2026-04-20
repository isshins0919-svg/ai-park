"""
ameru LP画像 Phase2 13本一括生成
gemini-3-pro-image-preview (Nano Banana Pro)
並列3スレッドで処理
"""

import os, subprocess, time, json
from concurrent.futures import ThreadPoolExecutor, as_completed

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'],
                               capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v:
                os.environ[var] = v
        except Exception:
            pass

for _v in ['GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
    _load_env(_v)

from google import genai
from google.genai import types

API_KEYS = [k for k in [os.environ.get(f'GEMINI_API_KEY_{i}', '').strip() for i in range(1, 4)] if k]
if not API_KEYS:
    raise RuntimeError("GEMINI_API_KEY_1 が設定されていません")
print(f"✅ API Keys: {len(API_KEYS)}本")

clients = [genai.Client(api_key=k) for k in API_KEYS]

OUT_DIR = 'reports/clients/ameru/images/phase2'
SEED_DIR = 'reports/clients/ameru/images'
os.makedirs(OUT_DIR, exist_ok=True)

def load_image(path):
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/png')
    return data, mime

# ==========================================================
# 13本プロンプト定義
# ==========================================================
PROMPTS = [
    # --- カテゴリC タイムライン 5本 ---
    {
        "id": "P01",
        "file": "P01_timeline_start.png",
        "aspect": "1:1 square",
        "seed": None,
        "prompt": """A neatly wound cream-colored yarn ball next to a beginner's first few crochet stitches on a crochet hook, with a printed pattern sheet partially visible at the edge. Warm natural morning light. On a light wood tabletop. 1:1 square. Photo realistic. No text, no logo."""
    },
    {
        "id": "P02",
        "file": "P02_timeline_half_head.png",
        "aspect": "1:1 square",
        "seed": "01_zumoppi_hero.png",
        "prompt": """A half-finished cream-colored crocheted amigurumi (only the round head complete, body not yet started) resting on a linen cloth next to the remaining cream yarn ball and a crochet hook. Warm afternoon window light. Close-up lifestyle composition. 1:1 square. Photo realistic. No text, no logo."""
    },
    {
        "id": "P03",
        "file": "P03_timeline_before_face.png",
        "aspect": "1:1 square",
        "seed": "01_zumoppi_hero.png",
        "prompt": """A nearly-finished cream-colored crocheted amigurumi doll with head and body assembled but no face yet (no eyes, no embroidered mouth). Small black embroidery thread and a sewing needle placed beside it, ready for the final face detailing. Warm natural light. 1:1 square. Photo realistic. No text, no logo."""
    },
    {
        "id": "P04",
        "file": "P04_timeline_palms.png",
        "aspect": "4:5 portrait",
        "seed": "01_zumoppi_hero.png",
        "prompt": """A woman's open palms (only hands visible, no face, no jewelry, plain white long sleeve) gently cradling a just-completed cream crocheted amigurumi doll, viewed from above. Soft warm natural light from a window. 4:5 portrait. Photo realistic, emotional lifestyle photography. No text, no logo."""
    },
    {
        "id": "P05",
        "file": "P05_timeline_before_after.png",
        "aspect": "1:1 square",
        "seed": "01_zumoppi_hero.png",
        "prompt": """A split-screen composition: left half shows a single cream yarn ball on a neutral beige surface; right half shows a completed cream crocheted amigurumi doll in the same position, on the same identical beige background. Warm natural lighting, identical lighting and background in both halves. 1:1 square composition with clean vertical divider in the center. Photo realistic, clear visual contrast. No text, no logo."""
    },

    # --- カテゴリD 人物×感情 4本 ---
    {
        "id": "E01",
        "file": "E01_emotion_hug.png",
        "aspect": "4:5 portrait",
        "seed": "05_lifestyle_finished.png",
        "prompt": """A young Asian woman (late 20s, Japanese) gently cradling a cream crocheted amigurumi doll to her chest, her face partially visible showing a soft content smile. Indoor cozy setting, warm natural window light, beige muted background. 4:5 portrait. Photo realistic, emotional lifestyle photography. No text, no logo."""
    },
    {
        "id": "E02",
        "file": "E02_emotion_crafting.png",
        "aspect": "4:5 portrait",
        "seed": "04_hands_crafting.png",
        "prompt": """A young Asian woman's hands and partial side profile, focused on crocheting a cream amigurumi. Close-up on her hands working with yarn, her face partially visible in shallow focus showing gentle concentration. Warm evening lamp light, cozy living room setting. 4:5 portrait. Photo realistic. No text, no logo."""
    },
    {
        "id": "E03",
        "file": "E03_emotion_parent_child.png",
        "aspect": "16:9",
        "seed": None,
        "prompt": """A mother and her young daughter (around 9 years old, elementary school age, both Asian/Japanese) sitting side by side on a sofa, both holding crochet hooks and working on small amigurumi projects together. Only their hands and lap area visible, warm afternoon living room light. 16:9 horizontal composition. Photo realistic, heartwarming family moment. No text, no logo."""
    },
    {
        "id": "E04",
        "file": "E04_emotion_windowsill.png",
        "aspect": "4:5 portrait",
        "seed": "01_zumoppi_hero.png",
        "prompt": """A cream crocheted amigurumi doll placed on a white window sill with soft afternoon light streaming through. Out of focus in the background: the silhouette of a young woman (from waist up, no face shown) looking at the doll with gentle pride. 4:5 portrait. Photo realistic, cinematic lifestyle. No text, no logo."""
    },

    # --- カテゴリE ギフト 3本 ---
    {
        "id": "G01",
        "file": "G01_gift_ribbon_card.png",
        "aspect": "1:1 square",
        "seed": "02_package_lifestyle.png",
        "prompt": """A light blue kraft paper stand-up pouch with the "ameru" logo on the front, wrapped with a cream satin ribbon, placed next to a plain handwritten greeting card (no visible text on card). Small dried flowers scattered around. Top-down flat lay on a warm wood surface. 1:1 square. Photo realistic, gift-giving warmth. No text beyond the package logo, no additional logo."""
    },
    {
        "id": "G02",
        "file": "G02_gift_handover.png",
        "aspect": "4:5 portrait",
        "seed": "02_package_lifestyle.png",
        "prompt": """Two sets of hands (one person handing, one person receiving) exchanging a wrapped ameru kit package with a cream ribbon. Warm indoor lighting, both sets of hands visible (no faces), soft beige background. 4:5 portrait. Photo realistic, gentle emotional moment. No text, no logo."""
    },
    {
        "id": "G03",
        "file": "G03_gift_child_hands.png",
        "aspect": "4:5 portrait",
        "seed": None,
        "prompt": """A close-up of a young child's hands (about 6 years old, Asian/Japanese, only hands visible, no face) holding a just-received ameru kit package wrapped in cream ribbon, with a small crocheted amigurumi partially visible inside. The child's small fingers gripping the package excitedly. Warm natural living room light. 4:5 portrait. Photo realistic. No text, no logo."""
    },

    # --- カテゴリG 背景素材 T04リトライ 1本 ---
    {
        "id": "T04",
        "file": "T04_bg_kraft_texture.png",
        "aspect": "1:1",
        "seed": None,
        "prompt": """Kraft paper texture background, warm beige-brown color (hex #C9B39A), subtle paper grain and fibers visible at normal viewing distance. Flat uniform texture edge to edge, no objects, no folds, no wrinkles. 1:1 square composition. Pure background texture only. No text, no logo."""
    },
]

# ==========================================================
# 生成関数
# ==========================================================
def generate_one(idx, config):
    client = clients[idx % len(clients)]
    seed_path = f"{SEED_DIR}/{config['seed']}" if config['seed'] else None
    out_path = f"{OUT_DIR}/{config['file']}"

    print(f"🎨 [{config['id']}] 開始 (client #{idx % len(clients) + 1})")
    start = time.time()

    try:
        parts = []
        if seed_path and os.path.exists(seed_path):
            data, mime = load_image(seed_path)
            parts.append(types.Part.from_bytes(data=data, mime_type=mime))
            parts.append(types.Part.from_text(
                text=f"Reference image provided above is the style and product reference. Generate a NEW image based on this description:\n\n{config['prompt']}\n\nAspect ratio: {config['aspect']}."
            ))
        else:
            parts.append(types.Part.from_text(
                text=f"{config['prompt']}\n\nAspect ratio: {config['aspect']}."
            ))

        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=[types.Content(role='user', parts=parts)],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
            )
        )

        saved = False
        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                if part.inline_data:
                    with open(out_path, 'wb') as f:
                        f.write(part.inline_data.data)
                    saved = True
                    break
            if saved:
                break

        elapsed = time.time() - start
        if saved:
            size_kb = os.path.getsize(out_path) / 1024
            print(f"✅ [{config['id']}] 完了 {elapsed:.1f}s ({size_kb:.0f}KB)")
            return {'id': config['id'], 'status': 'ok', 'path': out_path, 'time': elapsed}
        else:
            print(f"⚠️ [{config['id']}] 画像データ取得できず")
            return {'id': config['id'], 'status': 'no_image', 'time': elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ [{config['id']}] エラー: {str(e)[:120]}")
        return {'id': config['id'], 'status': 'error', 'error': str(e)[:200], 'time': elapsed}


# ==========================================================
# 並列実行
# ==========================================================
print(f"\n🚀 Phase2 13本 並列生成開始（3スレッド並列）\n")
t0 = time.time()

results = []
with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(generate_one, i, p): p for i, p in enumerate(PROMPTS)}
    for f in as_completed(futures):
        results.append(f.result())

total = time.time() - t0
ok_count = sum(1 for r in results if r['status'] == 'ok')
err_count = sum(1 for r in results if r['status'] != 'ok')

print(f"\n🎉 完了: {ok_count}/{len(PROMPTS)} 成功 / {err_count} 失敗 / 全体 {total:.1f}s")

summary = {
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'total_time_sec': round(total, 1),
    'success_count': ok_count,
    'error_count': err_count,
    'results': results,
}
with open(f'{OUT_DIR}/_generation_log.json', 'w') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"📄 ログ: {OUT_DIR}/_generation_log.json")
