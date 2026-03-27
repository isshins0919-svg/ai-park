#!/usr/bin/env python3
"""
記事内バナーメーカー v7
- 構図固定: 画像そのまま + テキストを下部に配置
- 3候補 = テキスト装飾スタイルのみ変える（帯/アウトライン/カラー帯）
- 記事LP好調データから学習した文字デザイン3パターン
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
from PIL import Image


# ─── 環境変数取得 ───────────────────────────────────────────────────────
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


# ─── Gemini クライアント初期化 ──────────────────────────────────────────
def init_gemini(api_key_override: str = ""):
    from google import genai
    if api_key_override:
        keys = [api_key_override]
    else:
        keys = [get_env(f"GEMINI_API_KEY_{i}") for i in range(1, 4)]
        keys = [k for k in keys if k]
    if not keys:
        return None, []
    clients = [genai.Client(api_key=k) for k in keys]
    return genai, clients


# ─── テキストスタイル 3パターン（記事LP好調データから） ────────────────
#
# 好調記事LP解析（三ツ星クリアナチュラル等）から抽出:
# - 文字は常に下部に水平配置
# - 1枚1メッセージ
# - 構図は変えない、文字装飾だけ変える
#
TEXT_STYLES = {
    "A: ダーク帯（最も汎用）": {
        "label": "A",
        "desc": "画像下部に半透明〜不透明の黒グラデーション帯 + 白太ゴシック。読みやすさ最強。",
        "prompt": """TEXT STYLE: Dark band
- Add a semi-transparent to opaque dark gradient band covering the bottom 25-30% of the image
- The band goes from fully transparent at top to 85% black opacity at bottom
- Place the Japanese text centered horizontally on this dark band
- Text color: pure white (#FFFFFF)
- Font: ultra bold sans-serif (like Gothic Bold)
- Text size: LARGE — fills 60-70% of the band width
- Add subtle drop shadow to text (2-3px dark shadow)
- NO changes to the image above the band""",
    },
    "B: アウトライン（インパクト系）": {
        "label": "B",
        "desc": "背景帯なし。黄色テキスト + 極太黒縁取り + ドロップシャドウ。衝撃系バナーの定番。",
        "prompt": """TEXT STYLE: Outline / Stroke
- NO background band — text floats over the image
- Place Japanese text in the bottom 20% of image, centered horizontally
- Text color: bright yellow (#FFE600) or white — high visibility
- Font: ultra bold / black weight sans-serif
- THICK black outline/stroke around each character (3-5px stroke)
- Strong drop shadow (4-6px, pure black, 60% opacity)
- Text size: LARGE — commands attention immediately
- DO NOT add any overlay or band — outline creates readability on its own""",
    },
    "C: カラー帯（ブランドカラー）": {
        "label": "C",
        "desc": "鮮やかなカラー塗り帯 + 白テキスト。ブランドカラーで感情を直接表現。",
        "prompt": """TEXT STYLE: Solid color band
- Add a SOLID (fully opaque) colored band at the very bottom of the image
- Band height: 22-28% of total image height
- Band color: choose a strong, vivid color that fits the mood — red (#E82222), orange (#FF6B35), navy (#0A1628), or green (#2E7D32)
- Text color: pure white (#FFFFFF)
- Font: bold sans-serif
- Text centered horizontally and vertically within the band
- Text size: fills 65-75% of the band width
- Sharp clean edge between image and colored band (no gradient)""",
    },
}


# ─── プロンプト生成 ─────────────────────────────────────────────────────
def build_prompt(text: str, style_key: str, emotion_hint: str, size_label: str) -> str:
    style = TEXT_STYLES[style_key]
    return f"""You are a professional Japanese article LP banner designer.

TASK: Add a text overlay to the provided image. Keep the image composition EXACTLY as-is.

## MANDATORY TEXT TO ADD:
「{text}」

## TEXT PLACEMENT RULE (NON-NEGOTIABLE):
- Text position: BOTTOM of the image, horizontal (straight, not angled)
- Text alignment: centered
- Do NOT move, crop, or alter the main image subject/composition

## TEXT DESIGN STYLE:
{style['prompt']}

## CONTEXT:
- This is for a Japanese article LP (記事LP) banner
- Output size: {size_label}
- Emotional direction: {emotion_hint or 'professional and impactful'}

## QUALITY CHECK:
- Can you read 「{text}」 clearly in 1 second? → If no, increase text size/contrast
- Is the main image subject preserved? → Must be yes
- Is the text horizontal and at the bottom? → Must be yes

Generate the banner with ONLY the text overlay added. Preserve everything else."""


# ─── バナー生成 ─────────────────────────────────────────────────────────
MODELS = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
]


def generate_banner(
    base_image: Image.Image,
    text: str,
    style_key: str,
    emotion_hint: str,
    size,
    size_label: str,
    clients: list,
) -> Image.Image:
    from google.genai import types
    from math import gcd

    if size:
        tw, th = size
        img = base_image.resize((tw, th), Image.LANCZOS)
    else:
        img = base_image
        tw, th = img.size

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    img_bytes = buf.getvalue()

    g = gcd(tw, th)
    aspect_map = {"1:1": "1:1", "4:5": "4:5", "3:4": "3:4",
                  "9:16": "9:16", "16:9": "16:9", "4:3": "4:3"}
    aspect = aspect_map.get(f"{tw//g}:{th//g}", "1:1")

    prompt = build_prompt(text, style_key, emotion_hint, size_label)

    last_error = None
    for model in MODELS:
        for client in clients:
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                        prompt,
                    ],
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
                    if size:
                        result = result.resize((tw, th), Image.LANCZOS)
                    return result
            except Exception as e:
                last_error = e
                time.sleep(2)

    raise RuntimeError(f"生成失敗（全モデル試行済み）: {last_error}")


# ─── 動画生成 ───────────────────────────────────────────────────────────
ANIMATIONS = {
    "なし（静止）": "none",
    "ゆっくりズームイン": "zoom",
    "フェードイン": "fade",
    "左からスライド": "slide",
}


def image_to_video(img: Image.Image, duration: int, animation: str, output_path: str):
    w, h = img.size
    fps = 30
    total = fps * duration
    base_arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    for i in range(total):
        t = i / max(total - 1, 1)
        if animation == "zoom":
            scale = 1.0 + 0.08 * t
            nw, nh = int(w * scale), int(h * scale)
            zoomed = cv2.resize(base_arr, (nw, nh))
            x, y = (nw - w) // 2, (nh - h) // 2
            frame = zoomed[y:y+h, x:x+w]
        elif animation == "fade":
            frame = (base_arr * min(t * 2, 1.0)).astype(np.uint8)
        elif animation == "slide":
            offset = int((1 - min(t * 3, 1.0)) * w * 0.3)
            frame = np.zeros_like(base_arr)
            if offset < w:
                frame[:, offset:] = base_arr[:, :w-offset]
        else:
            frame = base_arr.copy()
        out.write(frame)
    out.release()


def extract_frame(video_path: str) -> Image.Image:
    cap = cv2.VideoCapture(video_path)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    raise ValueError("動画からフレームを取得できませんでした")


# ─── サイズプリセット（実LP解析から記事内で使われる4種類に絞る） ──────
#
# 解析元: foot.cosmedia.online（Cosmos Media CMS）
# モバイル表示幅: 750px viewport → 570px表示（左右90px余白）
# アップロード標準: 横680px（CMSが自動リサイズ）
#
# 記事内で実際に使われているサイズ:
#   680×450 → 最多（表示570×377）比率1.51 … 標準横長・最も見慣れた比率
#   680×350 → 商品KV・成分解説（表示570×293）比率1.94 … 少し横広
#   680×300 → CTA帯・情報バナー（表示570×251）比率2.27 … 帯スタイル
#   1080×1080 → 正方形KV（SNS兼用・権威バナー） 比率1:1
#
SIZE_PRESETS = {
    "680 × 450 ★おすすめ（記事スタンダード・最多使用）": ((680, 450), "680×450"),
    "680 × 350（商品KV・ワイド横長）": ((680, 350), "680×350"),
    "680 × 300（情報帯・CTA）": ((680, 300), "680×300"),
    "1080 × 1080（正方形・権威KV・SNS兼用）": ((1080, 1080), "1080×1080"),
    "素材のまま": (None, "素材のまま"),
}


# ─── Streamlit UI ────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="記事内バナーメーカー", page_icon="🎨", layout="centered")
    st.title("🎨 記事内バナーメーカー v7")
    st.caption("画像そのまま × テキスト下部固定 × 文字デザイン3パターン比較")

    # APIキー
    api_key_override = ""
    genai_module, clients = init_gemini()
    if not clients:
        st.warning("⚠️ GEMINI_API_KEY が未設定。直接入力してください。")
        api_key_override = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        if api_key_override:
            genai_module, clients = init_gemini(api_key_override)
        if not clients:
            st.stop()

    st.success(f"✅ Gemini 接続済み（{len(clients)}キー）")
    st.divider()

    # ── ① 入力タイプ ──────────────────────────────────────────────────
    st.subheader("① 入力素材")
    col1, col2 = st.columns(2)
    with col1:
        is_video_input = st.checkbox("動画素材（フレーム抽出）", value=False)
    with col2:
        is_video_output = st.checkbox("動画出力（アニメーション付き）", value=False)

    if is_video_input:
        uploaded = st.file_uploader("動画をアップロード", type=["mp4", "mov"])
    else:
        uploaded = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])

    if uploaded:
        suffix = Path(uploaded.name).suffix.lower()
        if not is_video_input:
            preview = Image.open(uploaded)
            st.image(preview, caption="素材プレビュー", use_container_width=True)
            uploaded.seek(0)

    # ── ② テキスト ────────────────────────────────────────────────────
    st.subheader("② テキスト（バナー下部に入れる文言）")
    text = st.text_input("キャッチコピー", placeholder="例：ボロボロ爪まわりの原因菌を殺菌破壊！")

    # ── ③ 感情ヒント ──────────────────────────────────────────────────
    st.subheader("③ 感情・訴求方向（任意）")
    emotion_hint = st.text_input(
        "感情・雰囲気を一言で",
        placeholder="例：驚き・緊急・安心・権威・期待・共感",
    )

    # ── ④ 出力サイズ ──────────────────────────────────────────────────
    st.subheader("④ 出力サイズ")
    size_name = st.selectbox("サイズプリセット", list(SIZE_PRESETS.keys()), index=0)
    output_size, size_label = SIZE_PRESETS[size_name]
    size_tips = {
        "680 × 450 ★おすすめ（記事スタンダード・最多使用）": "モバイルで570×377表示。記事内で最も使われる比率。冒頭・中盤どちらにも◎",
        "680 × 350（商品KV・ワイド横長）": "モバイルで570×293表示。横に広く商品が映えるワイド比率。商品紹介・成分解説に◎",
        "680 × 300（情報帯・CTA）": "モバイルで570×251表示。帯スタイル。CTA・緊急性バナー・情報まとめに◎",
        "1080 × 1080（正方形・権威KV・SNS兼用）": "正方形。商品KV・ブランド権威演出・SNS転用に◎",
        "素材のまま": "素材の元サイズをそのまま使用",
    }
    if size_name in size_tips:
        st.caption(size_tips[size_name])

    # ── ⑤ 動画オプション ──────────────────────────────────────────────
    duration, animation_key = 3, "none"
    if is_video_output:
        st.subheader("⑤ 動画オプション")
        duration = st.select_slider("尺（秒）", options=[1, 3, 5, 7], value=3)
        anim_name = st.selectbox("アニメーション", list(ANIMATIONS.keys()))
        animation_key = ANIMATIONS[anim_name]

    st.divider()

    # ── 文字スタイル説明 ──────────────────────────────────────────────
    st.subheader("生成される3パターン")
    for key, s in TEXT_STYLES.items():
        st.markdown(f"**{key}** — {s['desc']}")

    st.divider()

    # ── 生成ボタン ────────────────────────────────────────────────────
    if st.button("🚀 3スタイル同時生成", type="primary", use_container_width=True):
        if not uploaded:
            st.error("① 素材をアップロードしてください")
            return
        if not text.strip():
            st.error("② テキストを入力してください")
            return

        suffix = Path(uploaded.name).suffix.lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded.read())
            input_path = tmp.name

        results = {}  # style_key → Image

        try:
            if is_video_input:
                base_img = extract_frame(input_path)
            else:
                base_img = Image.open(input_path).convert("RGB")
        except Exception as e:
            st.error(f"素材読み込みエラー: {e}")
            os.unlink(input_path)
            return
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

        for style_key in TEXT_STYLES:
            label = TEXT_STYLES[style_key]["label"]
            with st.spinner(f"スタイル {label} 生成中..."):
                try:
                    img = generate_banner(
                        base_img, text.strip(), style_key,
                        emotion_hint, output_size, size_label, clients,
                    )
                    results[style_key] = img
                except Exception as e:
                    st.warning(f"スタイル {label} 失敗: {e}")

        if not results:
            st.error("全スタイルの生成に失敗しました。しばらく待って再試行してください。")
            return

        st.success(f"✅ {len(results)}パターン 生成完了！")
        st.divider()

        cols = st.columns(len(results))
        for col, (style_key, img) in zip(cols, results.items()):
            s = TEXT_STYLES[style_key]
            with col:
                st.image(img, caption=style_key, use_container_width=True)

                if is_video_output:
                    out_buf = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                    image_to_video(img, duration, animation_key, out_buf.name)
                    with open(out_buf.name, "rb") as f:
                        st.download_button(
                            f"⬇ {s['label']} 動画DL",
                            data=f,
                            file_name=f"banner_style{s['label']}_{duration}s.mp4",
                            mime="video/mp4",
                            key=f"dl_v_{s['label']}",
                        )
                    os.unlink(out_buf.name)
                else:
                    buf = io.BytesIO()
                    img.save(buf, "JPEG", quality=93)
                    st.download_button(
                        f"⬇ {s['label']} 画像DL",
                        data=buf.getvalue(),
                        file_name=f"banner_style{s['label']}.jpg",
                        mime="image/jpeg",
                        key=f"dl_i_{s['label']}",
                    )


if __name__ == "__main__":
    main()
