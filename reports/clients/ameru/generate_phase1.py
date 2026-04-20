"""
ameru LP画像 Phase1 14本一括生成
gemini-3-pro-image-preview (Nano Banana Pro)
並列3スレッドで処理
"""

import os, subprocess, time, base64, json
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

OUT_DIR = 'reports/clients/ameru/images/phase1'
SEED_DIR = 'reports/clients/ameru/images'
os.makedirs(OUT_DIR, exist_ok=True)

def load_image(path):
    """画像バイトを返す"""
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/png')
    return data, mime

# ==========================================================
# 14本プロンプト定義
# ==========================================================
PROMPTS = [
    {
        "id": "H01",
        "file": "H01_hero_cloud_blanket.png",
        "aspect": "4:5 portrait",
        "seed": "01_zumoppi_hero.png",
        "prompt": """A handmade cream-colored crocheted amigurumi doll (plump body, tiny dot eyes, small embroidered smile, two small ears on top) sitting on a soft white fleece blanket. Soft warm morning natural light coming from the side creating gentle shadows. Beige-cream bokeh background. Cozy minimal lifestyle photography, 4:5 portrait aspect ratio. No text, no logo, no watermark. Photo realistic, professional product photography."""
    },
    {
        "id": "H02",
        "file": "H02_hero_pinkbeige_square.png",
        "aspect": "1:1 square",
        "seed": "01_zumoppi_hero.png",
        "prompt": """Cream-colored handmade crocheted amigurumi doll centered on a smooth pink-beige seamless paper backdrop (color hex #F4C6BD). Clean product photography like Japanese beauty brand meeth. Soft diffused studio lighting from top, gentle shadow under the doll, high key warm tone. 1:1 square composition. No text, no logo, no watermark. Photo realistic."""
    },
    {
        "id": "H03",
        "file": "H03_hero_wood_table.png",
        "aspect": "16:9",
        "seed": "01_zumoppi_hero.png",
        "prompt": """Cream crocheted amigurumi on a light oak wooden tabletop. Next to it: one small beige ceramic coffee cup, one white yarn ball. Top-down slight 3/4 angle, low saturation muted earth tones, warm natural window light, negative space on the right side. 16:9 cinematic aspect ratio. No text, no logo, no watermark. Photo realistic lifestyle."""
    },
    {
        "id": "H04",
        "file": "H04_hero_with_package.png",
        "aspect": "4:5 portrait",
        "seed": "02_package_lifestyle.png",
        "prompt": """Cream crocheted amigurumi doll next to a light blue kraft paper stand-up pouch with Japanese text "ameru" logo on the front, both placed on a natural linen cloth. Dried gypsophila sprigs scattered around. Top-down 3/4 angle, soft morning light, warm lifestyle tones. 4:5 portrait. No additional text overlay beyond the package logo. Photo realistic."""
    },
    {
        "id": "H05",
        "file": "H05_hero_face_macro.png",
        "aspect": "1:1 square",
        "seed": "01_zumoppi_hero.png",
        "prompt": """Extreme close-up macro shot of the face of a cream-colored crocheted amigurumi doll. Clearly visible crochet stitch texture, two tiny black bead eyes, small embroidered smile curve. Shallow depth of field blurring ears and body edges. Warm soft natural light. 1:1 square composition centered on the face. No text, no logo. Ultra detailed macro product photography."""
    },
    {
        "id": "H06",
        "file": "H06_hero_hands_holding.png",
        "aspect": "4:5 portrait",
        "seed": "01_zumoppi_hero.png",
        "prompt": """Two hands of a young woman gently cradling a cream crocheted amigurumi doll. Only hands and forearms visible (no face shown), pale skin, no jewelry, plain white long sleeve. Indoor soft window light behind, muted beige wall. The amigurumi facing forward with visible face. 4:5 portrait. No text, no logo. Photo realistic emotional lifestyle photography."""
    },
    {
        "id": "L01",
        "file": "L01_lineup_remaster.png",
        "aspect": "16:9",
        "seed": "07_collection_preview.png",
        "prompt": """Five handmade crocheted amigurumi dolls in a row (colors left-to-right: cream white, sky blue, dusty pink, mint green, lavender purple). Each has small ears, simple bead eyes and embroidered smile, similar body shape. Arranged in a slight curve on a clean pure white background. Pastel confetti (light pink, blue, yellow dots) scattered around the floor. Soft studio lighting from top, crisp clean product photography. 16:9 aspect ratio. No text, no logo, no watermark."""
    },
    {
        "id": "L02",
        "file": "L02_lineup_shelf.png",
        "aspect": "16:9",
        "seed": "07_collection_preview.png",
        "prompt": """Five crocheted amigurumi dolls (cream, blue, pink, mint, purple) neatly displayed on a light oak wooden shelf in a cozy Japanese living room. Behind the shelf: a few small potted plants slightly out of focus, a framed minimalist poster. Warm natural window light from the left. 16:9 cinematic horizontal composition. No text, no logo, no watermark. Photo realistic interior photography."""
    },
    {
        "id": "L03",
        "file": "L03_lineup_focus_foreground.png",
        "aspect": "4:5 portrait",
        "seed": "07_collection_preview.png",
        "prompt": """One cream-white crocheted amigurumi in sharp focus in the foreground, four other amigurumi (blue, pink, mint, purple) slightly out of focus in the background on a soft pink-beige fabric. Shallow depth of field f/2.8 look. Warm natural light. 4:5 portrait composition. No text, no logo. Professional product photography."""
    },
    {
        "id": "L04",
        "file": "L04_lineup_with_charspace.png",
        "aspect": "16:9",
        "seed": "07_collection_preview.png",
        "prompt": """Top portion of frame: five crocheted amigurumi dolls (cream, blue, pink, mint, purple) in a row on a neutral beige surface. Bottom portion of frame: blank clean space (for adding cartoon character illustrations later in post). 16:9 horizontal composition with generous bottom area. Soft studio lighting. No text, no logo."""
    },
    {
        "id": "T01",
        "file": "T01_bg_pinkbeige_gradient.png",
        "aspect": "1:1",
        "seed": None,
        "prompt": """Smooth pink-beige gradient background transitioning from light cream (#FBF4EC) at the top to soft dusty pink (#F4C6BD) at the bottom. Very subtle paper texture, minimalist, no objects. For use as product photography backdrop. 1:1 square. Pure background texture only. No text, no logo."""
    },
    {
        "id": "T02",
        "file": "T02_bg_yarn_negative.png",
        "aspect": "16:9",
        "seed": None,
        "prompt": """Close-up of a single white yarn ball placed on the left third of the frame on a neutral linen surface. Generous empty negative space on the right two-thirds of the frame suitable for future text overlay. Soft natural light, warm tones. 16:9 horizontal composition. No text, no logo."""
    },
    {
        "id": "T03",
        "file": "T03_bg_pastel_confetti.png",
        "aspect": "1:1",
        "seed": None,
        "prompt": """Pastel confetti dots scattered on a pure white background. Colors: light pink, mint, sky blue, soft yellow, lavender. Flat lay top-down view. Confetti scattered around the edges of the frame with empty white space in the center. 1:1 square composition. No text, no objects beyond confetti."""
    },
    {
        "id": "T04",
        "file": "T04_bg_kraft_texture.png",
        "aspect": "1:1",
        "seed": None,
        "prompt": """Kraft paper texture background, warm beige-brown color (#C9B39A), subtle grain and paper fibers visible at normal viewing. Flat uniform texture edge to edge, no objects, no logo. 1:1 square. Pure background texture only."""
    },
]

# ==========================================================
# 生成関数
# ==========================================================
def generate_one(idx, config):
    """1枚生成"""
    client = clients[idx % len(clients)]
    seed_path = f"{SEED_DIR}/{config['seed']}" if config['seed'] else None
    out_path = f"{OUT_DIR}/{config['file']}"

    print(f"🎨 [{config['id']}] 開始 (client #{idx % len(clients) + 1})")
    start = time.time()

    try:
        # プロンプト構築（シード画像がある場合は参照）
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

        # 画像データ抽出して保存
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
print(f"\n🚀 Phase1 14本 並列生成開始（3スレッド並列）\n")
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

# サマリ保存
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
