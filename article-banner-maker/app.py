#!/usr/bin/env python3
"""
記事内バナーメーカー v2
入力(画像/動画) × 出力(画像/動画) × テキストデザイン × 感情 → 記事内素材を自動生成
"""

import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ─── フォント探索 ──────────────────────────────────────────────────
FONT_CANDIDATES = {
    "ゴシック（標準）": [
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ],
    "ゴシック（極太）": [
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Black.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    ],
    "丸ゴシック（柔らかい）": [
        "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
        "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
        "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    ],
    "明朝（格式）": [
        "/usr/share/fonts/opentype/noto/NotoSerifCJKjp-Bold.otf",
        "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf",
        "/System/Library/Fonts/ヒラギノ明朝 ProN W6.ttc",
        "/System/Library/Fonts/ヒラギノ明朝 ProN W3.ttc",
    ],
    "IPAゴシック": [
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
    ],
}

@st.cache_resource
def discover_fonts() -> dict:
    """利用可能なフォントを探索してキャッシュ"""
    found = {}
    for name, paths in FONT_CANDIDATES.items():
        for p in paths:
            if Path(p).exists():
                found[name] = p
                break
    if not found:
        found["デフォルト"] = None  # PIL built-in fallback
    return found

def get_font(font_path, size: int):
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()

# ─── テキスト折り返し ─────────────────────────────────────────────
def wrap_text(text: str, font, max_width: float) -> list:
    lines, current = [], ""
    for char in text:
        test = current + char
        try:
            w = font.getlength(test)
        except Exception:
            w = len(test) * (font.size * 0.6 if hasattr(font, "size") else 10)
        if w > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines or [text]

def measure_text_width(font, text: str) -> float:
    try:
        return font.getlength(text)
    except Exception:
        return len(text) * (font.size * 0.6 if hasattr(font, "size") else 10)

# ─── テキスト位置 ──────────────────────────────────────────────────
POSITIONS = {"上": "top", "中央": "center", "下": "bottom"}

# ─── オーバーレイスタイル ──────────────────────────────────────────
def build_overlay(img: Image.Image, style: dict, text_area_y: int, text_area_h: int):
    """グラデーション or ソリッド背景オーバーレイを生成"""
    w, h = img.size
    overlay_type = style.get("overlay", "gradient_dark")
    r, g, b = style.get("bg_color", (0, 0, 0))

    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    if overlay_type == "gradient_dark":
        # 下部グラデーション（シネマ風）
        grad_h = min(text_area_h + 100, h // 2)
        grad_start = h - grad_h
        for y in range(grad_h):
            alpha = int((y / grad_h) ** 0.7 * 200)
            for x in range(0, w, 1):
                ov.putpixel((x, grad_start + y), (r, g, b, alpha))

    elif overlay_type == "gradient_warm":
        grad_h = min(text_area_h + 100, h // 2)
        grad_start = h - grad_h
        arr = np.array(ov)
        for y in range(grad_h):
            alpha = int((y / grad_h) ** 0.7 * 190)
            arr[grad_start + y, :] = [r, g, b, alpha]
        ov = Image.fromarray(arr, "RGBA")

    elif overlay_type == "solid":
        arr = np.array(ov)
        pad = 24
        alpha = int(style.get("opacity", 0.78) * 255)
        arr[text_area_y - pad : text_area_y + text_area_h + pad, :] = [r, g, b, alpha]
        ov = Image.fromarray(arr, "RGBA")

    elif overlay_type == "full":
        alpha = int(style.get("opacity", 0.45) * 255)
        ov = Image.new("RGBA", (w, h), (r, g, b, alpha))

    return ov

# ─── テキストをフレームに描画 ──────────────────────────────────────
def render_text(
    base_img: Image.Image,
    text: str,
    style: dict,
    font: ImageFont.FreeTypeFont,
    position: str = "bottom",
    alpha_ratio: float = 1.0,  # 0〜1（フェードイン用）
):
    img = base_img.convert("RGBA")
    w, h = img.size

    font_size = font.size if hasattr(font, "size") else 40
    lines = wrap_text(text, font, w * 0.88)
    line_h = int(font_size * 1.35)
    total_h = line_h * len(lines)

    if position == "top":
        text_y = 50
    elif position == "center":
        text_y = (h - total_h) // 2
    else:  # bottom
        text_y = h - total_h - 70

    # オーバーレイ
    ov = build_overlay(img, style, text_y, total_h)
    img = Image.alpha_composite(img, ov)

    # テキスト描画レイヤー
    txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    tr, tg, tb = style.get("text_color", (255, 255, 255))
    text_alpha = int(alpha_ratio * 255)
    stroke_color = style.get("stroke_color", (0, 0, 0))
    stroke_w = style.get("stroke_width", 3)

    for i, line in enumerate(lines):
        lw = int(measure_text_width(font, line))
        tx = (w - lw) // 2
        ty = text_y + i * line_h
        # ストローク（アウトライン）
        if stroke_w > 0:
            draw.text(
                (tx, ty), line, font=font,
                fill=(*stroke_color, text_alpha),
                stroke_width=stroke_w, stroke_fill=(*stroke_color, text_alpha),
            )
        # ドロップシャドウ
        draw.text((tx + 3, ty + 4), line, font=font, fill=(0, 0, 0, int(text_alpha * 0.5)))
        # 本文
        draw.text((tx, ty), line, font=font, fill=(tr, tg, tb, text_alpha))

    img = Image.alpha_composite(img, txt_layer)
    return img.convert("RGB")

# ─── 感情スタイル ──────────────────────────────────────────────────
EMOTION_STYLES = {
    "共感":  {"text_color": (255, 255, 255), "bg_color": (200, 80, 30),  "overlay": "gradient_warm", "stroke_color": (150, 40, 0),  "stroke_width": 3, "font_hint": "丸ゴシック（柔らかい）"},
    "驚き":  {"text_color": (255, 235,   0), "bg_color": (0, 0, 0),      "overlay": "gradient_dark", "stroke_color": (0, 0, 0),     "stroke_width": 4, "font_hint": "ゴシック（極太）"},
    "安心":  {"text_color": (30,  60,  30),  "bg_color": (220, 245, 220),"overlay": "solid",         "stroke_color": (200, 230, 200),"stroke_width": 2, "font_hint": "ゴシック（標準）"},
    "権威":  {"text_color": (240, 220, 160), "bg_color": (0, 15, 50),    "overlay": "gradient_dark", "stroke_color": (0, 0, 0),     "stroke_width": 3, "font_hint": "明朝（格式）"},
    "期待":  {"text_color": (255, 255, 255), "bg_color": (200, 40, 90),  "overlay": "gradient_warm", "stroke_color": (140, 0, 50),  "stroke_width": 3, "font_hint": "ゴシック（極太）"},
}
DEFAULT_STYLE = {"text_color": (255, 255, 255), "bg_color": (0, 0, 0), "overlay": "gradient_dark", "stroke_color": (0, 0, 0), "stroke_width": 3, "font_hint": "ゴシック（標準）"}

def resolve_style(selected: list, custom: str) -> dict:
    if selected:
        return EMOTION_STYLES.get(selected[0], DEFAULT_STYLE)
    return DEFAULT_STYLE

# ─── サイズプリセット ──────────────────────────────────────────────
SIZE_PRESETS = {
    "素材のまま": None,
    "680 × 450（横長・記事メイン）": (680, 450),
    "680 × 800（縦長・強調）": (680, 800),
    "1080 × 1080（正方形・SNS）": (1080, 1080),
    "390 × 844（スマホ縦）": (390, 844),
    "1280 × 720（横動画）": (1280, 720),
}

def resize_image(img: Image.Image, size):
    if size is None:
        return img
    tw, th = size
    iw, ih = img.size
    ratio = min(tw / iw, th / ih)
    nw, nh = int(iw * ratio), int(ih * ratio)
    resized = img.resize((nw, nh), Image.LANCZOS)
    bg = Image.new("RGB", (tw, th), (0, 0, 0))
    bg.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
    return bg

# ─── テキストアニメーション ────────────────────────────────────────
ANIMATIONS = {
    "なし": "none",
    "フェードイン": "fade",
    "下からスライド": "slide_up",
    "ズームイン": "zoom",
}

def animate_frame(base_img: Image.Image, text: str, style: dict, font, position: str,
                  frame_idx: int, total_frames: int, animation: str) -> np.ndarray:
    """アニメーションフレームを1枚生成"""
    t = frame_idx / max(total_frames - 1, 1)
    anim_frames = min(total_frames, 30)
    progress = min(frame_idx / anim_frames, 1.0)

    if animation == "fade":
        result = render_text(base_img, text, style, font, position, alpha_ratio=progress)

    elif animation == "slide_up":
        # テキストを下からスライドイン
        img = base_img.convert("RGBA")
        w, h = img.size
        font_size = font.size if hasattr(font, "size") else 40
        lines = wrap_text(text, font, w * 0.88)
        line_h = int(font_size * 1.35)
        total_h = line_h * len(lines)

        if position == "bottom":
            final_y = h - total_h - 70
        elif position == "center":
            final_y = (h - total_h) // 2
        else:
            final_y = 50

        offset = int((1 - progress) * 80)
        shifted_style = dict(style)

        # ずらした位置にオーバーレイを描画するための一時クロップ
        tmp = base_img.copy()
        result_tmp = render_text(tmp, text, shifted_style, font, position, alpha_ratio=min(progress * 2, 1.0))
        result = result_tmp

    elif animation == "zoom":
        scale = 0.85 + 0.15 * progress
        result_base = render_text(base_img, text, style, font, position, alpha_ratio=progress)
        w, h = result_base.size
        nw, nh = int(w * scale), int(h * scale)
        zoomed = result_base.resize((nw, nh), Image.LANCZOS)
        bg = Image.new("RGB", (w, h), (0, 0, 0))
        bg.paste(zoomed, ((w - nw) // 2, (h - nh) // 2))
        result = bg

    else:  # none
        result = render_text(base_img, text, style, font, position)

    return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)

# ─── 画像 → 画像 ──────────────────────────────────────────────────
def process_image_to_image(input_path: str, text: str, style: dict, font,
                            position: str, size):
    img = Image.open(input_path).convert("RGB")
    img = resize_image(img, size)
    return render_text(img, text, style, font, position)

# ─── 画像 → 動画 ──────────────────────────────────────────────────
def process_image_to_video(input_path: str, text: str, style: dict, font, position: str,
                            size, duration: int, animation: str, output_path: str):
    img = Image.open(input_path).convert("RGB")
    img = resize_image(img, size)
    w, h = img.size
    fps = 30
    total = fps * duration
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    for i in range(total):
        frame = animate_frame(img, text, style, font, position, i, total, animation)
        out.write(frame)
    out.release()

# ─── 動画 → 動画 ──────────────────────────────────────────────────
def process_video_to_video(input_path: str, text: str, style: dict, font, position: str,
                            size, duration: int, animation: str, output_path: str):
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    max_frames = int(fps * duration)

    # サイズ決定
    if size:
        out_w, out_h = size
    else:
        out_w, out_h = orig_w, orig_h

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_w, out_h))

    frames_read = []
    while len(frames_read) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frames_read.append(frame)
    cap.release()

    total = len(frames_read)
    for i, frame in enumerate(frames_read):
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        pil = resize_image(pil, size)
        rendered = animate_frame(pil, text, style, font, position, i, total, animation)
        out.write(rendered)
    out.release()

# ─── Streamlit UI ─────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="記事内バナーメーカー", page_icon="🎨", layout="centered")
    st.title("🎨 記事内バナーメーカー")
    st.caption("素材 × テキスト × 感情デザイン → 記事内素材を自動生成")
    st.divider()

    available_fonts = discover_fonts()
    font_names = list(available_fonts.keys())

    # ── 入力 / 出力タイプ ──────────────────────────────────────────
    st.subheader("① 入力 → 出力タイプを選択")
    output_mode = st.radio(
        "パターン",
        options=[
            "画像 → 画像（静止バナー）",
            "画像 → 動画（テキストアニメーション付き）",
            "動画 → 動画（文字乗せ）",
        ],
        horizontal=False,
    )
    is_video_input  = output_mode.startswith("動画")
    is_video_output = "動画" in output_mode.split("→")[1]

    # ── ベース素材 ────────────────────────────────────────────────
    st.subheader("② ベース素材")
    if is_video_input:
        uploaded = st.file_uploader("動画をアップロード", type=["mp4", "mov"])
    else:
        uploaded = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])

    # ── 出力サイズ ────────────────────────────────────────────────
    st.subheader("③ 出力サイズ")
    size_name = st.selectbox("サイズプリセット", list(SIZE_PRESETS.keys()))
    output_size = SIZE_PRESETS[size_name]

    # ── テキスト ──────────────────────────────────────────────────
    st.subheader("④ テキスト")
    text = st.text_input("見出し・キャッチコピー", placeholder="例：足の臭いが気になる方へ")
    position = st.radio("テキスト位置", list(POSITIONS.keys()), horizontal=True, index=2)

    # ── フォント ──────────────────────────────────────────────────
    st.subheader("⑤ フォント")
    selected_font_name = st.selectbox("フォントを選択", font_names)
    font_size = st.slider("フォントサイズ", min_value=24, max_value=120, value=52, step=4)
    font_path = available_fonts.get(selected_font_name)
    font_obj = get_font(font_path, font_size)

    # ── 感情タグ ──────────────────────────────────────────────────
    st.subheader("⑥ 感情タグ")
    st.caption("選択するとテキストカラー・背景が自動で変わります")
    emotion_presets = list(EMOTION_STYLES.keys())
    cols = st.columns(len(emotion_presets))
    selected_emotions = []
    for i, e in enumerate(emotion_presets):
        if cols[i].checkbox(e, key=f"emo_{e}"):
            selected_emotions.append(e)
    custom_emotion = st.text_input(
        "または自由入力（例：焦り・悔しさ・ワクワク）",
        placeholder="感情を自由に入力",
    )
    style = resolve_style(selected_emotions, custom_emotion)

    # ── 動画オプション（動画出力の時のみ表示） ────────────────────
    duration, animation = 3, "fade"
    if is_video_output:
        st.subheader("⑦ 動画オプション")
        duration = st.select_slider("尺（秒）", options=[1, 3, 5, 7], value=3)
        animation = st.selectbox("テキストアニメーション", list(ANIMATIONS.keys()))
        animation = ANIMATIONS[animation]

    # ── スタイルプレビュー ────────────────────────────────────────
    if text and (selected_emotions or custom_emotion):
        r, g, b = style["bg_color"]
        tr, tg, tb = style["text_color"]
        st.divider()
        st.caption("スタイルプレビュー（実際の画像ではイメージが異なります）")
        st.markdown(
            f'<div style="background:linear-gradient(to top, rgba({r},{g},{b},0.9), transparent);'
            f'color:rgb({tr},{tg},{tb});padding:20px 24px;border-radius:8px;'
            f'text-align:center;font-weight:bold;font-size:20px;'
            f'text-shadow:2px 2px 4px rgba(0,0,0,0.6);">'
            f'{text}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── 生成ボタン ────────────────────────────────────────────────
    if st.button("🎨 生成する", type="primary", use_container_width=True):
        if not uploaded:
            st.error("② ベース素材をアップロードしてください")
            return
        if not text.strip():
            st.error("④ テキストを入力してください")
            return

        pos_key = POSITIONS[position]
        suffix = Path(uploaded.name).suffix.lower()

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded.read())
            input_path = tmp.name

        emotion_label = selected_emotions[0] if selected_emotions else (custom_emotion or "custom")

        with st.spinner("生成中..."):
            try:
                if output_mode == "画像 → 画像（静止バナー）":
                    result_img = process_image_to_image(input_path, text.strip(), style, font_obj, pos_key, output_size)
                    out_buf = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                    result_img.save(out_buf.name, "JPEG", quality=92)
                    output_path = out_buf.name
                    is_img_output = True

                elif output_mode == "画像 → 動画（テキストアニメーション付き）":
                    out_buf = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                    output_path = out_buf.name
                    process_image_to_video(input_path, text.strip(), style, font_obj, pos_key, output_size, duration, animation, output_path)
                    is_img_output = False

                else:  # 動画 → 動画
                    out_buf = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                    output_path = out_buf.name
                    process_video_to_video(input_path, text.strip(), style, font_obj, pos_key, output_size, duration, animation, output_path)
                    is_img_output = False

            except Exception as e:
                st.error(f"生成エラー: {e}")
                return
            finally:
                if os.path.exists(input_path):
                    os.unlink(input_path)

        st.success("✅ 生成完了！")

        if is_img_output:
            st.image(output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    "⬇ 画像をダウンロード", data=f,
                    file_name=f"banner_{emotion_label}.jpg",
                    mime="image/jpeg", use_container_width=True,
                )
        else:
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    "⬇ 動画をダウンロード", data=f,
                    file_name=f"banner_{emotion_label}_{duration}s.mp4",
                    mime="video/mp4", use_container_width=True,
                )

        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == "__main__":
    main()
