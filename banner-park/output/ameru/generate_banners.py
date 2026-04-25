#!/usr/bin/env python3
"""Phase 4: ameru バナー10本 × 2モデル生成
   - Gemini Imagen 3 (imagen-3.0-generate-001)
   - OpenAI gpt-image-1

出力:
  banners/gemini/ameru_<type>_<n>.png  (10本)
  banners/openai/ameru_<type>_<n>.png  (10本)
"""

import os, json, subprocess, sys, time, base64, requests
from pathlib import Path

ROOT = Path(__file__).parent
GEMINI_OUT = ROOT / "banners" / "gemini"
OPENAI_OUT = ROOT / "banners" / "openai"
GEMINI_OUT.mkdir(parents=True, exist_ok=True)
OPENAI_OUT.mkdir(parents=True, exist_ok=True)

# ── env loader ────────────────────────────────────────────
def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass

_load_env('GEMINI_API_KEY_1')
_load_env('OPENAI_API_KEY')

GEMINI_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

# ── バナー仕様定義 ─────────────────────────────────────────
# 5型10本 × 禁忌ルール適用済み
# copy: 日本語コピー（完成プロンプトの意図）
# prompt_en: OpenAI用英語プロンプト
# prompt_ja: Gemini用（日本語混在OK）

BANNERS = [
    # ── Type A: IP×キャラ集合型 × 3本 ──────────────────────
    {
        "id": "A1",
        "type": "IP_character_collection",
        "copy": "らぶいーず、ぜんぶ、自分の手で。",
        "ref_cluster": "B",
        "prompt_en": (
            "Square 1:1 advertisement banner for Japanese amigurumi crochet kit. "
            "Five adorable handmade crochet stuffed animals arranged together: "
            "light blue bear-rabbit (すもっぴ), pink bunny (ぴょんちー), cream-lavender cat (にゃぽ), "
            "grey-purple seal (うるる), mint green elephant (ぱおぱお). "
            "Pastel pink-beige background (#F4E5DC), soft natural light, cozy warm atmosphere. "
            "Top-right corner: small official badge '日本テレビ公式'. "
            "Bottom-left: brand logo 'ameru' in small soft text. "
            "Center-bottom Japanese copy in bold rounded gothic font: 'らぶいーず、ぜんぶ、自分の手で。' "
            "Style: cute Japanese character goods advertisement, Instagram square format, "
            "pastel illustration style, gold confetti sparkles, celebratory. "
            "High quality, sharp focus."
        ),
        "prompt_ja": (
            "正方形1:1の日本の広告バナー。あみぐるみキットの宣伝。"
            "5体の可愛いあみぐるみキャラクターが集合している: "
            "水色のクマうさぎ（すもっぴ）、ピンクのうさぎ（ぴょんちー）、クリーム薄紫のネコ（にゃぽ）、"
            "グレー薄紫のアザラシ（うるる）、ミントグリーンのゾウ（ぱおぱお）。"
            "背景: ピンクベージュ(#F4E5DC)の柔らかいパステルトーン。"
            "右上に小さく「日本テレビ公式」のバッジ。左下に「ameru」ロゴ。"
            "中央下部に太めの丸ゴシックで「らぶいーず、ぜんぶ、自分の手で。」"
            "金の紙吹雪・サテンリボン装飾あり。Instagramスクエア広告スタイル。高品質。"
        ),
    },
    {
        "id": "A2",
        "type": "IP_character_collection",
        "copy": "公式5キャラ、自分で編める。",
        "ref_cluster": "B",
        "prompt_en": (
            "Square Instagram advertisement banner for Japanese crochet amigurumi kit brand. "
            "Flat lay composition: five small cute crochet amigurumi dolls in pastel colors arranged in a circle, "
            "surrounded by colorful yarn balls, a crochet hook, and the kit packaging box (light blue). "
            "Ivory white background (#FBF5EC), soft overhead lighting, cozy handcraft aesthetic. "
            "Top area: Japanese text '公式5キャラ、自分で編める。' in bold rounded gothic font. "
            "Top-right: small circular badge 'らぶいーず® 日本テレビ公式'. "
            "Bottom-left: 'ameru' logo in small elegant text. "
            "Style: clean lifestyle product photo, pastel craft aesthetic, Instagram square. High detail."
        ),
        "prompt_ja": (
            "正方形Instagramバナー。日本のあみぐるみキット広告。"
            "フラットレイ構成: 5体のパステルカラーのあみぐるみ人形が円形に並び、"
            "カラフルな毛糸玉・かぎ針・水色のキット箱が周囲に散らばっている。"
            "アイボリー白背景(#FBF5EC)、柔らかいオーバーヘッドライティング、手芸の温かみ。"
            "上部に太い丸ゴシックで「公式5キャラ、自分で編める。」"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
            "清潔感あるライフスタイル商品写真スタイル。高品質。"
        ),
    },
    {
        "id": "A3",
        "type": "IP_character_collection",
        "copy": "#らぶいーず を編む",
        "ref_cluster": "B",
        "prompt_en": (
            "Square social media advertisement banner, SNS organic style for Japanese amigurumi crochet kit. "
            "Close-up of two hands holding a small, almost-complete crochet amigurumi character "
            "(light blue bear-rabbit すもっぴ) in progress, with yarn tail still attached. "
            "Soft warm background with pastel pink and cream tones. "
            "Authentic handmade feel, natural indoor lighting. "
            "Top of image: hashtag text '#らぶいーず を編む' in casual playful Japanese font. "
            "Bottom-right: 'ameru' brand logo. "
            "Style: authentic UGC-style photo, warm and personal, Instagram square format."
        ),
        "prompt_ja": (
            "正方形SNS広告バナー、UGCスタイル。日本のあみぐるみキット。"
            "両手がほぼ完成した水色のあみぐるみ（すもっぴ）を持つ接写。毛糸の尻尾がまだついている。"
            "パステルピンクとクリームのソフトな温かい背景。"
            "本物の手作り感、自然な室内ライティング。"
            "上部に遊び心あるフォントで「#らぶいーず を編む」"
            "右下に「ameru」ブランドロゴ。"
            "本物のSNS投稿のような温かみのあるスタイル。"
        ),
    },
    # ── Type B: オーダーメイド差別化型 × 2本 ─────────────────
    {
        "id": "B1",
        "type": "order_made_differentiation",
        "copy": "世界でひとつの、あなたのらぶいーず",
        "ref_cluster": "A",
        "prompt_en": (
            "Premium square advertisement banner for Japanese handmade crochet amigurumi kit. "
            "Center hero: single beautifully completed light blue crochet amigurumi bear-rabbit doll "
            "on a pristine ivory white background (#FBF5EC), soft studio lighting, slight shadow. "
            "The doll looks perfect and unique, like a treasured keepsake. "
            "Delicate gold ribbon bow in corner, subtle gold confetti sparkles. "
            "Top: elegant Japanese text '世界でひとつの、あなたのらぶいーず' in refined rounded gothic. "
            "Small badge top-right: 'らぶいーず® 日本テレビ公式'. "
            "Bottom-left: 'ameru' logo. "
            "Style: premium product photography, luxury handcraft, ownership satisfaction appeal. "
            "Warm ivory tones, high detail, sharp focus."
        ),
        "prompt_ja": (
            "プレミアム正方形広告バナー。日本の手作りあみぐるみキット。"
            "中央ヒーロー: 完成した美しい水色のあみぐるみ（すもっぴ）1体が"
            "アイボリー白背景(#FBF5EC)の上に置かれ、スタジオライティング、繊細な影。"
            "宝物のような唯一無二感。角に金のリボン、微細な金の紙吹雪。"
            "上部に上品な丸ゴシックで「世界でひとつの、あなたのらぶいーず」"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
            "高級感のある商品写真スタイル、所有満足感の訴求。"
        ),
    },
    {
        "id": "B2",
        "type": "order_made_differentiation",
        "copy": "編み始め完成済み、だから必ず完成する",
        "ref_cluster": "A",
        "prompt_en": (
            "Square advertisement banner for Japanese crochet amigurumi kit, focusing on 'starter-ready' unique selling point. "
            "Center: an open light blue kit box revealing inside: a partially-started amigurumi body "
            "(head already shaped in light blue yarn), full yarn kit, crochet hook, instruction card. "
            "The partially-made body signals 'already started = guaranteed completion'. "
            "Pastel background, soft warm lighting. "
            "Bold Japanese headline: '編み始め完成済み、だから必ず完成する' in warm rounded gothic. "
            "Small reassuring sub-copy: 'かぎ針・糸・パーツ全部入り'. "
            "Top-right badge: 'らぶいーず® 日本テレビ公式'. Bottom-left: 'ameru' logo. "
            "Style: clear product explanation, trust-building, clean composition."
        ),
        "prompt_ja": (
            "正方形広告バナー。「編み始め完成済み」というOnly1訴求。"
            "中央: 開いた水色のキット箱の中に、すでに頭部が形作られたあみぐるみ本体と"
            "毛糸・かぎ針・説明書が入っている。"
            "「すでに始まっている=必ず完成できる」を視覚化。"
            "パステル背景、温かい柔らかいライティング。"
            "太い丸ゴシックで「編み始め完成済み、だから必ず完成する」"
            "小さいサブコピー「かぎ針・糸・パーツ全部入り」"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
        ),
    },
    # ── Type C: SNSエモコピー型 × 2本 ────────────────────────
    {
        "id": "C1",
        "type": "sns_emotional_copy",
        "copy": "え、らぶいーずって自分で編めるの？",
        "ref_cluster": "B",
        "prompt_en": (
            "Square SNS advertisement banner with surprise discovery theme for Japanese amigurumi kit. "
            "Vibrant pastel design: a cute surprised reaction face emoji overlaid on pastel pink background, "
            "with a small amigurumi doll appearing as if 'revealed' with sparkle effects. "
            "Bold casual Japanese headline at top: 'え、らぶいーずって自分で編めるの？' "
            "in playful informal font (like a surprised SNS post). "
            "Animated-style sparkles, confetti, discovery moment energy. "
            "Sub-text: '初心者でもOK／編み始め完成済み'. "
            "Top-right badge: 'らぶいーず® 日本テレビ公式'. Bottom-left: 'ameru'. "
            "Style: SNS native ad, pop art energy, thumb-stopping first impression."
        ),
        "prompt_ja": (
            "正方形SNS広告バナー。発見の驚きテーマ。"
            "鮮やかなパステルデザイン: 可愛い驚きのリアクション表情がパステルピンク背景に。"
            "小さなあみぐるみが「お披露目」されるように輝きエフェクトと共に登場。"
            "上部に遊び心ある口語体フォントで「え、らぶいーずって自分で編めるの？」"
            "キラキラ・紙吹雪・発見の瞬間のエネルギー。"
            "サブテキスト「初心者でもOK／編み始め完成済み」"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
            "SNSネイティブ広告スタイル、目を引く第一印象。"
        ),
    },
    {
        "id": "C2",
        "type": "sns_emotional_copy",
        "copy": "8時間で、推しが手元に。",
        "ref_cluster": "B",
        "prompt_en": (
            "Square advertisement banner emphasizing quick completion time for Japanese amigurumi kit. "
            "Split composition: LEFT side shows yarn and crochet needle and kit box (starting point). "
            "RIGHT side shows a beautifully completed light blue amigurumi bear-rabbit (done!). "
            "Center divider area: bold '8H' or hourglass icon. "
            "Japanese headline bold: '8時間で、推しが手元に。' in impactful rounded gothic. "
            "Pastel warm tones: pink-beige to ivory gradient background. "
            "Achievement feeling, wow-factor, fast turnaround surprise. "
            "Top-right: 'らぶいーず® 日本テレビ公式' badge. Bottom-left: 'ameru'. "
            "Style: before/after concept, clean modern composition, high energy."
        ),
        "prompt_ja": (
            "正方形広告バナー。完成の速さを強調。"
            "左半分: 毛糸・かぎ針・キット箱（スタート地点）。"
            "右半分: 完成した水色のあみぐるみ（すもっぴ、完成！）。"
            "中央に「8H」または砂時計アイコン。"
            "太い丸ゴシックで「8時間で、推しが手元に。」"
            "パステル温かいトーン: ピンクベージュからアイボリーのグラデーション背景。"
            "達成感・驚き・スピード感。"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
        ),
    },
    # ── Type D: 実写完成型 × 2本 ──────────────────────────────
    {
        "id": "D1",
        "type": "completed_lifestyle",
        "copy": "できた。",
        "ref_cluster": "B",
        "prompt_en": (
            "Square lifestyle photograph-style advertisement banner. "
            "Five completed handmade crochet amigurumi dolls lined up on a wooden table or white surface: "
            "light blue bear-rabbit, pink bunny, cream-lavender cat, grey-purple seal, mint elephant. "
            "Each doll is about 10-15cm, meticulously crafted, displayed proudly. "
            "Natural soft window light, warm cozy home background, slightly blurred depth of field. "
            "Bottom center: single bold Japanese word 'できた。' in large warm rounded font. "
            "Top-right: small badge 'らぶいーず® 日本テレビ公式'. Bottom-left: 'ameru'. "
            "Style: heartwarming lifestyle photo, pride of creation, UGC-authentic feel. "
            "No CGI - photorealistic warmth."
        ),
        "prompt_ja": (
            "正方形ライフスタイル写真スタイルの広告バナー。"
            "完成した5体のあみぐるみが木製テーブルか白いサーフェスに並んでいる:"
            "水色のクマうさぎ、ピンクのうさぎ、クリーム薄紫のネコ、グレー薄紫のアザラシ、ミントのゾウ。"
            "各10-15cm、丁寧に作られ誇らしげに展示。"
            "柔らかい自然光、温かみのある家の背景、浅い被写界深度。"
            "下中央に大きな太い丸ゴシックで「できた。」"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
            "感動的なライフスタイル写真、創作の誇り、UGC的温かみ。"
        ),
    },
    {
        "id": "D2",
        "type": "completed_lifestyle",
        "copy": "できた。自分の手で。",
        "ref_cluster": "B",
        "prompt_en": (
            "Square close-up lifestyle advertisement banner for Japanese amigurumi crochet kit. "
            "Hands gently cupping a single completed light blue crochet amigurumi bear-rabbit doll (すもっぴ). "
            "The hands look like a woman's hands, warm skin tone, slight smile implied. "
            "Soft blurred background in pastel pink-ivory. "
            "Intimate, proud, tender moment of creation. "
            "Bottom: Japanese text 'できた。自分の手で。' in heartfelt rounded gothic font. "
            "Top-right: small 'らぶいーず® 日本テレビ公式' badge. Bottom-left: 'ameru'. "
            "Style: close-up hands lifestyle, emotional, warm, tactile. Photorealistic."
        ),
        "prompt_ja": (
            "正方形接写ライフスタイル広告バナー。"
            "女性の手が完成した水色のあみぐるみ（すもっぴ）を優しく包んでいる。"
            "暖かい肌色の手、微笑みが伝わる温かさ。"
            "パステルピンクアイボリーのぼかし背景。"
            "創作の誇らしい、親密な、感動的な瞬間。"
            "下部に温かみある丸ゴシックで「できた。自分の手で。」"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
            "接写ライフスタイル、感情的、温かみ、触感的。リアル写真調。"
        ),
    },
    # ── Type E: キットパッケージ単品型 × 1本 ─────────────────
    {
        "id": "E1",
        "type": "package_single",
        "copy": "はじめの1体、¥1,980",
        "ref_cluster": "C",
        "prompt_en": (
            "Clean e-commerce product listing square banner for Japanese amigurumi crochet kit. "
            "Center: single light blue rectangular kit box package on pure white background. "
            "Box has elegant label: 'ameru × らぶいーず あみぐるみキット'. "
            "Simple, minimal, trust-building product shot. "
            "Very slight shadow beneath box for depth. "
            "Text at bottom: 'はじめの1体、¥1,980 (税込)' in clean bold Japanese sans-serif. "
            "Sub-text: 'かぎ針・糸・パーツ全部入り / 送料込み'. "
            "Top-right: 'らぶいーず® 日本テレビ公式' badge. Bottom-left: 'ameru' logo. "
            "Style: clean EC product photography, white background, minimal text, "
            "SmartNews listing compatible format. High detail product shot."
        ),
        "prompt_ja": (
            "清潔なECサイト商品掲載用正方形バナー。"
            "中央: 水色の長方形キット箱が純白背景の上に。"
            "箱のラベル: 「ameru × らぶいーず あみぐるみキット」"
            "シンプル、ミニマル、信頼感のある商品ショット。"
            "箱の下にわずかな影で奥行き感。"
            "下部テキスト: 「はじめの1体、¥1,980（税込）」清潔な太い和文サンセリフ。"
            "サブテキスト: 「かぎ針・糸・パーツ全部入り / 送料込み」"
            "右上に「らぶいーず® 日本テレビ公式」バッジ。左下に「ameru」ロゴ。"
            "清潔なEC商品写真スタイル、白背景、ミニマルなテキスト。"
        ),
    },
]


# ── Gemini Imagen 3 生成 ──────────────────────────────────
def generate_gemini(banner: dict, out_dir: Path):
    from google import genai
    from google.genai import types as gtypes

    assert GEMINI_KEY, "GEMINI_API_KEY_1 未設定"
    client = genai.Client(api_key=GEMINI_KEY)

    out_path = out_dir / f"ameru_{banner['id']}.png"
    if out_path.exists():
        print(f"  [skip] {out_path.name} already exists")
        return str(out_path)

    resp = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=banner["prompt_ja"],
        config=gtypes.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
            output_mime_type="image/png",
        ),
    )
    if not resp.generated_images:
        raise RuntimeError("Gemini: 画像が返らなかった")
    img_bytes = resp.generated_images[0].image.image_bytes
    out_path.write_bytes(img_bytes)
    return str(out_path)


# ── OpenAI gpt-image-1 生成 ───────────────────────────────
def generate_openai(banner: dict, out_dir: Path):
    assert OPENAI_KEY, "OPENAI_API_KEY 未設定"
    out_path = out_dir / f"ameru_{banner['id']}.png"
    if out_path.exists():
        print(f"  [skip] {out_path.name} already exists")
        return str(out_path)

    payload = {
        "model": "gpt-image-2",
        "prompt": banner["prompt_en"],
        "n": 1,
        "size": "1024x1024",
        "quality": "medium",
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers=headers,
        json=payload,
        timeout=180,
    )
    data = resp.json()
    if resp.status_code != 200 or "error" in data:
        err = data.get("error", {})
        raise RuntimeError(f"OpenAI error: {err.get('message', data)}")
    b64 = data["data"][0].get("b64_json")
    if not b64:
        raise RuntimeError("OpenAI: b64_json が返らなかった")
    out_path.write_bytes(base64.b64decode(b64))
    return str(out_path)


# ── メイン実行 ────────────────────────────────────────────
def run(model: str = "both"):
    results = {"gemini": [], "openai": []}
    errors = []

    for i, banner in enumerate(BANNERS, 1):
        print(f"\n[{i:2}/{len(BANNERS)}] {banner['id']} — {banner['copy']}")

        if model in ("both", "gemini"):
            print(f"  Gemini Imagen 3 ...", end=" ", flush=True)
            try:
                p = generate_gemini(banner, GEMINI_OUT)
                print(f"✅ {Path(p).name}")
                results["gemini"].append({"id": banner["id"], "copy": banner["copy"], "path": p, "type": banner["type"]})
            except Exception as e:
                print(f"❌ {type(e).__name__}: {str(e)[:100]}")
                errors.append({"model": "gemini", "id": banner["id"], "error": str(e)})

        if model in ("both", "openai"):
            print(f"  OpenAI gpt-image-1 ...", end=" ", flush=True)
            try:
                p = generate_openai(banner, OPENAI_OUT)
                print(f"✅ {Path(p).name}")
                results["openai"].append({"id": banner["id"], "copy": banner["copy"], "path": p, "type": banner["type"]})
            except Exception as e:
                print(f"❌ {type(e).__name__}: {str(e)[:100]}")
                errors.append({"model": "openai", "id": banner["id"], "error": str(e)})

        # レートリミット考慮
        if i < len(BANNERS):
            time.sleep(2)

    # サマリー保存
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_banners": len(BANNERS),
        "results": results,
        "errors": errors,
    }
    summary_path = ROOT / "banners" / "generation_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print(f"\n{'='*50}")
    print(f"Gemini: {len(results['gemini'])}/{len(BANNERS)} ✅")
    print(f"OpenAI: {len(results['openai'])}/{len(BANNERS)} ✅")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  [{e['model']}] {e['id']}: {e['error'][:80]}")
    print(f"Summary: {summary_path}")
    return results, errors


if __name__ == "__main__":
    model_arg = sys.argv[1] if len(sys.argv) > 1 else "both"
    if model_arg not in ("both", "gemini", "openai"):
        print(f"Usage: python3 generate_banners.py [both|gemini|openai]")
        sys.exit(1)
    print(f"=== ameru Phase 4: バナー生成 ({model_arg}) ===")
    print(f"Gemini out: {GEMINI_OUT}")
    print(f"OpenAI out: {OPENAI_OUT}")
    print(f"Banners: {len(BANNERS)}本")
    run(model=model_arg)
