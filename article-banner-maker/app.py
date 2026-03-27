#!/usr/bin/env python3
"""
記事内バナー動画メーカー
画像 or 動画 × テキスト × 感情 → 記事内バナー動画（MP4）を自動生成
"""

import os
import tempfile
import urllib.request
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ─── フォント設定 ──────────────────────────────────────────────
FONT_PATH = Path(__file__).parent / "NotoSansJP-Bold.ttf"
FONT_URL = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"

def ensure_font():
    if not FONT_PATH.exists():
        with st.spinner("日本語フォントを準備中..."):
            try:
                urllib.request.urlretrieve(FONT_URL, FONT_PATH)
            except Exception:
                pass  # フォールバックでシステムフォントを使う

def get_font(size: int):
    candidates = [
        str(FONT_PATH),
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

# ─── 感情スタイル定義 ───────────────────────────────────────────
EMOTION_STYLES = {
    "共感":  {"text_color": (255, 255, 255), "bg_color": (255, 107,  53), "opacity": 0.78},
    "驚き":  {"text_color": (255, 235,   0), "bg_color": (  0,   0,   0), "opacity": 0.80},
    "安心":  {"text_color": ( 20,  20,  20), "bg_color": (240, 255, 240), "opacity": 0.82},
    "権威":  {"text_color": (255, 255, 255), "bg_color": (  0,  20,  60), "opacity": 0.88},
    "期待":  {"text_color": (255, 255, 255), "bg_color": (220,  50, 100), "opacity": 0.75},
}
DEFAULT_STYLE = {"text_color": (255, 255, 255), "bg_color": (0, 0, 0), "opacity": 0.70}

def resolve_style(selected: list, custom: str) -> dict:
    if selected:
        return EMOTION_STYLES.get(selected[0], DEFAULT_STYLE)
    return DEFAULT_STYLE

# ─── テキスト折り返し ───────────────────────────────────────────
def wrap_text(text: str, font, max_width: float) -> list:
    lines, current = [], ""
    for char in text:
        test = current + char
        try:
            w = font.getlength(test)
        except AttributeError:
            w = len(test) * 14  # fallback
        if w > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines or [text]

# ─── フレームにテキストをオーバーレイ ─────────────────────────────
def render_text_on_frame(
    frame_bgr: np.ndarray,
    text: str,
    style: dict,
    font_size: int = 52,
) -> np.ndarray:
    img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    w, h = img.size
    font = get_font(font_size)

    lines = wrap_text(text, font, w * 0.82)
    line_h = font_size + 12
    box_h = line_h * len(lines) + 48
    try:
        box_w = int(max(font.getlength(l) for l in lines)) + 64
    except AttributeError:
        box_w = int(max(len(l) for l in lines) * (font_size * 0.6)) + 64
    box_w = min(box_w, w - 40)

    box_x = (w - box_w) // 2
    box_y = h - box_h - 60

    # 半透明背景
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    r, g, b = style["bg_color"]
    alpha = int(style["opacity"] * 255)
    draw_ov.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=12,
        fill=(r, g, b, alpha),
    )
    img = Image.alpha_composite(img, overlay)

    # テキスト描画
    draw = ImageDraw.Draw(img)
    tr, tg, tb = style["text_color"]
    for i, line in enumerate(lines):
        try:
            lw = int(font.getlength(line))
        except AttributeError:
            lw = len(line) * int(font_size * 0.6)
        tx = (w - lw) // 2
        ty = box_y + 24 + i * line_h
        # 影
        draw.text((tx + 2, ty + 2), line, font=font, fill=(0, 0, 0, 160))
        draw.text((tx, ty), line, font=font, fill=(tr, tg, tb, 255))

    result = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    return result

# ─── 動画生成 ────────────────────────────────────────────────────
def image_to_video(image_path: str, text: str, style: dict, duration: int, output_path: str):
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError("画像を読み込めませんでした")
    h, w = img_bgr.shape[:2]
    fps = 30
    frame = render_text_on_frame(img_bgr, text, style)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    for _ in range(fps * duration):
        out.write(frame)
    out.release()


def video_to_video(video_path: str, text: str, style: dict, duration: int, output_path: str):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    max_frames = int(fps * duration)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    count = 0
    while count < max_frames:
        ret, frame = cap.read()
        if not ret:
            # 動画が短い場合は最後のフレームを繰り返す
            if count == 0:
                break
            # 最後のフレームを使い回す
            out.write(frame_prev)
        else:
            frame = render_text_on_frame(frame, text, style)
            out.write(frame)
            frame_prev = frame
        count += 1
    cap.release()
    out.release()


# ─── Streamlit UI ────────────────────────────────────────────────
def main():
    ensure_font()

    st.set_page_config(
        page_title="記事内バナー動画メーカー",
        page_icon="🎬",
        layout="centered",
    )

    st.title("🎬 記事内バナー動画メーカー")
    st.caption("画像・動画 × テキスト × 感情 → 記事内バナー動画を自動生成")
    st.divider()

    # ① ベース素材
    st.subheader("① ベース素材")
    uploaded = st.file_uploader(
        "画像 または 動画をアップロード",
        type=["jpg", "jpeg", "png", "mp4", "mov"],
        help="記事内に使いたいベース画像 or 動画をアップロードしてください",
    )

    # ② テキスト
    st.subheader("② テキスト")
    text = st.text_input(
        "見出し・キャッチコピー",
        placeholder="例：足の臭いが気になる方へ",
    )

    # ③ 感情タグ
    st.subheader("③ 感情タグ")
    st.caption("当てはまるものを選択 or 自由入力（テキストカラー・背景色が変わります）")
    emotion_presets = ["共感", "驚き", "安心", "権威", "期待"]
    cols = st.columns(len(emotion_presets))
    selected_emotions = []
    for i, emotion in enumerate(emotion_presets):
        if cols[i].checkbox(emotion, key=f"emo_{emotion}"):
            selected_emotions.append(emotion)
    custom_emotion = st.text_input(
        "または自由入力（例：焦り・期待感・悔しさ）",
        placeholder="感情を自由に入力",
    )

    # ④ 動画の尺
    st.subheader("④ 動画の尺")
    duration = st.select_slider("秒数を選択", options=[1, 3, 5, 7], value=3)

    st.divider()

    # スタイルプレビュー
    if selected_emotions or custom_emotion:
        style = resolve_style(selected_emotions, custom_emotion)
        r, g, b = style["bg_color"]
        tr, tg, tb = style["text_color"]
        st.markdown(
            f'<div style="background:rgba({r},{g},{b},{style["opacity"]});'
            f'color:rgb({tr},{tg},{tb});padding:12px 20px;border-radius:8px;'
            f'text-align:center;font-weight:bold;font-size:18px;">'
            f'{text or "テキストプレビュー"}</div>',
            unsafe_allow_html=True,
        )
        st.caption("↑ テキストスタイルのプレビュー")

    # 生成ボタン
    generate = st.button("🎬 生成する", type="primary", use_container_width=True)

    if generate:
        if not uploaded:
            st.error("① ベース素材をアップロードしてください")
            return
        if not text.strip():
            st.error("② テキストを入力してください")
            return

        style = resolve_style(selected_emotions, custom_emotion)
        emotion_label = selected_emotions[0] if selected_emotions else (custom_emotion or "custom")
        suffix = Path(uploaded.name).suffix.lower()
        is_video = suffix in [".mp4", ".mov"]

        with st.spinner("生成中..."):
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
                tmp_in.write(uploaded.read())
                input_path = tmp_in.name

            output_path = input_path.replace(suffix, "_output.mp4")

            try:
                if is_video:
                    video_to_video(input_path, text.strip(), style, duration, output_path)
                else:
                    image_to_video(input_path, text.strip(), style, duration, output_path)
            except Exception as e:
                st.error(f"生成エラー: {e}")
                return
            finally:
                if os.path.exists(input_path):
                    os.unlink(input_path)

        st.success("✅ 生成完了！")

        # プレビュー
        st.video(output_path)

        # ダウンロード
        with open(output_path, "rb") as f:
            st.download_button(
                label="⬇ ダウンロード",
                data=f,
                file_name=f"banner_{emotion_label}_{duration}s.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == "__main__":
    main()
