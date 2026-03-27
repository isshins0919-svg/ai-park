#!/usr/bin/env python3
"""
記事内バナーメーカー v9 — Hybrid構成
- Gemini: 背景画像の生成のみ（AI生成モード時・1回）
- PIL: テキスト3スタイルをプログラムで乗せる（速い・安定・完全制御）

素材モード: API呼び出しゼロ → 数秒で完了
AI生成モード: Gemini 1回（30〜60秒）→ PILで3スタイル即時
"""

import io
import os
import subprocess
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ─── 環境変数取得 ──────────────────────────────────────────────────────
def get_env(key: str) -> str:
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    v = os.environ.get(key, "").strip()
    if v:
        return v
    try:
        r = subprocess.run(["zsh", "-i", "-c", f"echo ${key}"],
                           capture_output=True, text=True, timeout=5)
        v = r.stdout.strip()
        if v:
            return v
    except Exception:
        pass
    return ""


# ─── Gemini クライアント初期化 ─────────────────────────────────────────
def init_gemini(api_key_override: str = ""):
    from google import genai
    keys = [api_key_override] if api_key_override else [
        get_env(f"GEMINI_API_KEY_{i}") for i in range(1, 4)
    ]
    keys = [k for k in keys if k]
    if not keys:
        return None, []
    return genai, [genai.Client(api_key=k) for k in keys]


# ─── リサイズ（アスペクト比保持クロップ） ─────────────────────────────
def resize_cover(img: Image.Image, tw: int, th: int) -> Image.Image:
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top  = (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))


# ─── フォント読み込み ──────────────────────────────────────────────────
FONT_PATHS = [
    # Streamlit Cloud / Linux (packages.txt でインストール済み)
    "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
    "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/fonts-ipafont-gothic/ipagp.ttf",
    # Mac
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Arial Unicode.ttf",
    "/Library/Fonts/NotoSansCJK-Bold.ttc",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def fit_font(text: str, img_w: int, target_ratio: float = 0.72,
             max_size: int = 130, min_size: int = 20) -> ImageFont.FreeTypeFont:
    """テキストが画像幅の target_ratio に収まる最大フォントサイズを返す"""
    target_w = img_w * target_ratio
    font_path = next((p for p in FONT_PATHS if os.path.exists(p)), None)
    if not font_path:
        return load_font(max_size)
    lo, hi = min_size, max_size
    while lo < hi - 1:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(font_path, mid)
        bb = f.getbbox(text)
        if (bb[2] - bb[0]) < target_w:
            lo = mid
        else:
            hi = mid
    return ImageFont.truetype(font_path, lo)


def text_size(text: str, font: ImageFont.FreeTypeFont):
    bb = font.getbbox(text)
    return bb[2] - bb[0], bb[3] - bb[1]


# ─── PIL テキストスタイル 3パターン ────────────────────────────────────
def style_a_dark_band(img: Image.Image, text: str) -> Image.Image:
    """A: 半透明黒グラデーション帯 + 白太字 + ドロップシャドウ"""
    w, h = img.size
    band_h = int(h * 0.30)
    font = fit_font(text, w)

    # グラデーション帯（RGBA）
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_o = ImageDraw.Draw(overlay)
    for i in range(band_h):
        alpha = int(200 * (i / band_h))
        y0 = h - band_h + i
        draw_o.rectangle([(0, y0), (w, y0 + 1)], fill=(0, 0, 0, alpha))

    result = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(result)

    tw, th = text_size(text, font)
    x = (w - tw) // 2
    y = h - int(band_h * 0.60) - th // 2

    # ドロップシャドウ
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 160))
    # 本文（白）
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    return result


def style_b_outline(img: Image.Image, text: str) -> Image.Image:
    """B: 背景なし + 黄色テキスト + 極太黒縁取り"""
    w, h = img.size
    font = fit_font(text, w)

    result = img.copy()
    draw = ImageDraw.Draw(result)

    tw, th = text_size(text, font)
    x = (w - tw) // 2
    y = h - int(h * 0.25) - th // 2

    stroke_w = max(4, int(font.size * 0.10))
    # アウトライン（黒）
    draw.text((x, y), text, font=font,
              fill=(255, 230, 0), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    return result


def style_c_color_band(img: Image.Image, text: str,
                        band_color: tuple = (220, 40, 40)) -> Image.Image:
    """C: べた塗りカラー帯 + 白テキスト"""
    w, h = img.size
    band_h = int(h * 0.26)
    font = fit_font(text, w)

    result = img.copy()
    draw = ImageDraw.Draw(result)

    # べた塗り帯
    draw.rectangle([(0, h - band_h), (w, h)], fill=band_color)

    tw, th = text_size(text, font)
    x = (w - tw) // 2
    y = h - band_h // 2 - th // 2

    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    return result


STYLES = {
    "A: ダーク帯": {
        "label": "A", "fn": style_a_dark_band,
        "desc": "半透明黒グラデーション帯 + 白太字 + シャドウ。最も汎用。",
    },
    "B: アウトライン": {
        "label": "B", "fn": style_b_outline,
        "desc": "帯なし・黄色文字 + 極太黒縁取り。インパクト系定番。",
    },
    "C: カラー帯": {
        "label": "C", "fn": lambda img, text: style_c_color_band(img, text),
        "desc": "べた塗りカラー帯（赤）+ 白文字。ブランドカラー直表現。",
    },
}


def apply_all_styles(base_img: Image.Image, text: str, target_size) -> dict:
    """base_img に3スタイルを適用して辞書で返す（全部PIL・即時）"""
    if target_size:
        tw, th = target_size
        img = resize_cover(base_img, tw, th)
    else:
        img = base_img.copy()

    results = {}
    for key, s in STYLES.items():
        try:
            results[key] = s["fn"](img.copy(), text)
        except Exception as e:
            st.warning(f"スタイル {s['label']} 失敗: {e}")
    return results


# ─── Gemini: 背景画像のみ生成（AI生成モード用）─────────────────────────
GEMINI_MODELS = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
]


def get_aspect_ratio(tw: int, th: int) -> str:
    ratio = tw / th
    candidates = {"1:1": 1.0, "4:3": 4/3, "3:4": 3/4,
                  "16:9": 16/9, "9:16": 9/16, "4:5": 4/5}
    return min(candidates, key=lambda k: abs(candidates[k] - ratio))


def img_to_bytes(img: Image.Image, quality: int = 90) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def generate_background(
    description: str,
    ref_img,          # Image or None
    emotion_hint: str,
    target_size,
    size_label: str,
    clients: list,
) -> Image.Image:
    """Gemini でテキストなしの背景画像を1枚だけ生成する"""
    from google.genai import types

    tw, th = target_size if target_size else (680, 450)
    aspect = get_aspect_ratio(tw, th)

    ref_line = (
        "A style reference image is provided. Match its mood/atmosphere/color palette ONLY. "
        "Do NOT copy its subject."
        if ref_img else ""
    )
    prompt = f"""Generate a high-quality photographic background image for a Japanese article LP banner.

Scene: {description}
Output size: {size_label}
Mood: {emotion_hint or 'warm and professional'}
{ref_line}

IMPORTANT:
- Leave the bottom 25% relatively uncluttered (text will be added later)
- NO text, no watermarks, no overlays
- Photorealistic, professional photography quality"""

    contents = []
    if ref_img:
        ref_r = ref_img.resize((400, 400), Image.LANCZOS)
        contents.append(types.Part.from_bytes(data=img_to_bytes(ref_r), mime_type="image/jpeg"))
        contents.append("Style reference image above — match mood/color only.")
    contents.append(prompt)

    last_error = None
    for model in GEMINI_MODELS:
        for client in clients:
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=aspect),
                    ),
                )
                img_data = next(
                    (p.inline_data.data for p in resp.parts
                     if hasattr(p, "inline_data") and p.inline_data),
                    None,
                )
                if img_data and len(img_data) > 10240:
                    result = Image.open(io.BytesIO(img_data)).convert("RGB")
                    return resize_cover(result, tw, th)
            except Exception as e:
                last_error = e
                time.sleep(2)

    raise RuntimeError(f"背景生成失敗: {last_error}")


# ─── 動画生成 ──────────────────────────────────────────────────────────
ANIMATIONS = {"なし（静止）": "none", "ゆっくりズームイン": "zoom",
               "フェードイン": "fade", "左からスライド": "slide"}


def image_to_video(img: Image.Image, duration: int, animation: str, output_path: str):
    w, h = img.size
    fps, total = 30, 30 * duration
    base = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(total):
        t = i / max(total - 1, 1)
        if animation == "zoom":
            s = 1.0 + 0.08 * t
            nw, nh = int(w * s), int(h * s)
            z = cv2.resize(base, (nw, nh))
            frame = z[(nh-h)//2:(nh-h)//2+h, (nw-w)//2:(nw-w)//2+w]
        elif animation == "fade":
            frame = (base * min(t * 2, 1.0)).astype(np.uint8)
        elif animation == "slide":
            off = int((1 - min(t * 3, 1.0)) * w * 0.3)
            frame = np.zeros_like(base)
            if off < w:
                frame[:, off:] = base[:, :w - off]
        else:
            frame = base.copy()
        out.write(frame)
    out.release()


def extract_frame(video_path: str) -> Image.Image:
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_FRAME_COUNT) // 2)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    raise ValueError("動画からフレームを取得できませんでした")


# ─── サイズプリセット ──────────────────────────────────────────────────
SIZE_PRESETS = {
    "680 × 450 ★（記事スタンダード）":        ((680, 450), "680×450"),
    "680 × 350（商品KV・ワイド横長）":         ((680, 350), "680×350"),
    "680 × 300（情報帯・CTA）":               ((680, 300), "680×300"),
    "1080 × 1080（正方形・権威KV・SNS兼用）": ((1080, 1080), "1080×1080"),
    "素材のまま":                             (None, "素材のまま"),
}
SIZE_TIPS = {
    "680 × 450 ★（記事スタンダード）":        "モバイル表示 570×377。記事内で最多使用。",
    "680 × 350（商品KV・ワイド横長）":         "モバイル表示 570×293。商品紹介・成分解説に◎",
    "680 × 300（情報帯・CTA）":               "モバイル表示 570×251。帯スタイル。CTAに◎",
    "1080 × 1080（正方形・権威KV・SNS兼用）": "正方形。ブランドKV・SNS転用に◎",
    "素材のまま":                             "素材の元サイズをそのまま使用",
}


# ─── Streamlit UI ──────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="記事内バナーメーカー", page_icon="🎨", layout="centered")
    st.title("🎨 記事内バナーメーカー v9")
    st.caption("Gemini（背景生成のみ）× PIL（テキスト即時・完全制御）— 速い・安定・3スタイル比較")

    if "results" not in st.session_state:
        st.session_state.results = {}

    # ── APIキー ──────────────────────────────────────────────────────
    _, clients = init_gemini()
    if not clients:
        st.warning("⚠️ GEMINI_API_KEY が未設定（AI生成モードに必要）。直接入力してください。")
        key_input = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        if key_input:
            _, clients = init_gemini(key_input)
    if clients:
        st.success(f"✅ Gemini 接続済み（{len(clients)}キー）")
    else:
        st.info("ℹ️ 素材モードはAPIキー不要で使えます")
    st.divider()

    # ── ① 素材モード ─────────────────────────────────────────────────
    st.subheader("① 素材モード")
    input_mode = st.radio(
        "",
        ["📁 画像をそのまま使う（API不要・即時）",
         "✨ AIで画像を生成する（Gemini・30〜60秒）"],
        label_visibility="collapsed",
    )
    use_ai_gen = input_mode.startswith("✨")

    if use_ai_gen:
        ai_description = st.text_area(
            "生成したい画像の説明",
            placeholder="例：白髪の60代女性が笑顔で座っている。明るい自然光。清潔感のある室内。",
            height=80,
        )
        base_uploaded = None
        is_video = False
    else:
        is_video = st.checkbox("動画素材（フレームを抽出して使用）", value=False)
        if is_video:
            base_uploaded = st.file_uploader("動画をアップロード", type=["mp4", "mov"])
        else:
            base_uploaded = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])
        if base_uploaded and not is_video:
            st.image(Image.open(base_uploaded), caption="素材プレビュー", use_container_width=True)
            base_uploaded.seek(0)
        ai_description = ""

    # ── ② 参考テイスト画像（任意） ───────────────────────────────────
    st.subheader("② 参考テイスト画像（任意）")
    st.caption("「このバナーのような雰囲気で」という場合にアップロード。可愛い系・高齢者向け・高級感など。")
    ref_uploaded = st.file_uploader("参考バナー・画像", type=["jpg", "jpeg", "png"], key="ref")
    ref_img = None
    if ref_uploaded:
        ref_img = Image.open(ref_uploaded).convert("RGB")
        st.image(ref_img, caption="参考テイスト（雰囲気・色のみ参考）", use_container_width=True)

    # ── ③ テキスト ────────────────────────────────────────────────────
    st.subheader("③ テキスト（バナー下部に入れる文言）")
    text = st.text_input("キャッチコピー", placeholder="例：こんなにも笑顔に！！")

    # ── ④ 感情ヒント（AI生成モードのみ使用） ──────────────────────────
    emotion_hint = ""
    if use_ai_gen:
        st.subheader("④ 感情・雰囲気（AI生成の指示）")
        emotion_hint = st.text_input(
            "", placeholder="例：温かみ・活発・清潔感・高齢者向け・可愛い系",
            label_visibility="collapsed",
        )

    # ── ⑤ 出力サイズ ──────────────────────────────────────────────────
    st.subheader("⑤ 出力サイズ" if use_ai_gen else "④ 出力サイズ")
    size_name = st.selectbox("", list(SIZE_PRESETS.keys()), index=0, label_visibility="collapsed")
    output_size, size_label = SIZE_PRESETS[size_name]
    st.caption(SIZE_TIPS.get(size_name, ""))

    # ── 動画オプション ────────────────────────────────────────────────
    is_video_output = st.checkbox("動画出力（アニメーション付き）", value=False)
    duration, animation_key = 3, "none"
    if is_video_output:
        duration = st.select_slider("尺（秒）", options=[1, 3, 5, 7], value=3)
        animation_key = ANIMATIONS[st.selectbox("アニメーション", list(ANIMATIONS.keys()))]

    st.divider()
    st.subheader("生成される3パターン（テキスト装飾のみ違う）")
    for key, s in STYLES.items():
        st.markdown(f"**{key}** — {s['desc']}")
    st.divider()

    # ── 生成ボタン ────────────────────────────────────────────────────
    if st.button("🚀 3スタイル同時生成", type="primary", use_container_width=True):
        if use_ai_gen and not ai_description.strip():
            st.error("① 生成したい画像の説明を入力してください")
            return
        if not use_ai_gen and not base_uploaded:
            st.error("① 素材をアップロードしてください")
            return
        if not text.strip():
            st.error("③ テキストを入力してください")
            return

        # ── ベース画像準備 ─────────────────────────────────────────
        if use_ai_gen:
            if not clients:
                st.error("AI生成モードにはGemini APIキーが必要です")
                return
            with st.spinner("Gemini で背景を生成中... (30〜60秒)"):
                try:
                    base_img = generate_background(
                        ai_description.strip(), ref_img,
                        emotion_hint, output_size, size_label, clients,
                    )
                    st.image(base_img, caption="生成された背景", use_container_width=True)
                except Exception as e:
                    st.error(f"背景生成失敗: {e}")
                    return
        else:
            suffix = Path(base_uploaded.name).suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(base_uploaded.read())
                tmp_path = tmp.name
            try:
                base_img = (extract_frame(tmp_path) if is_video
                            else Image.open(tmp_path).convert("RGB"))
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        # ── PIL で3スタイル即時適用 ───────────────────────────────
        with st.spinner("3スタイル生成中..."):
            result_imgs = apply_all_styles(base_img, text.strip(), output_size)

        st.session_state.results = {}
        for key, img in result_imgs.items():
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=93)
            st.session_state.results[key] = buf.getvalue()

        if not st.session_state.results:
            st.error("生成に失敗しました")

    # ── 結果表示（session_stateから・ダウンロードしても消えない） ───
    if st.session_state.results:
        st.success(f"✅ {len(st.session_state.results)}パターン 生成完了！")
        st.divider()

        cols = st.columns(len(st.session_state.results))
        for col, (style_key, img_bytes) in zip(cols, st.session_state.results.items()):
            s = STYLES[style_key]
            img = Image.open(io.BytesIO(img_bytes))
            with col:
                st.image(img, caption=style_key, use_container_width=True)
                if is_video_output:
                    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vf:
                        image_to_video(img, duration, animation_key, vf.name)
                        with open(vf.name, "rb") as f:
                            st.download_button(
                                f"⬇ {s['label']} 動画",
                                data=f.read(),
                                file_name=f"banner_{s['label']}_{duration}s.mp4",
                                mime="video/mp4",
                                key=f"dl_v_{s['label']}",
                            )
                    os.unlink(vf.name)
                else:
                    st.download_button(
                        f"⬇ {s['label']} 画像DL",
                        data=img_bytes,
                        file_name=f"banner_style{s['label']}.jpg",
                        mime="image/jpeg",
                        key=f"dl_i_{s['label']}",
                    )


if __name__ == "__main__":
    main()
