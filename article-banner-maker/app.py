#!/usr/bin/env python3
"""
記事内バナーメーカー v8
- 素材モード: 「そのまま」or「AI生成（テキストから）」
- 参考テイスト画像: スタイル・雰囲気を参考画像で伝える
- テキスト下部固定 × 3文字スタイル比較
- session_state でダウンロード後も結果が消えない
- resize_cover でアスペクト比を保ちながら正確にクロップ
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


# ─── リサイズ（アスペクト比保持クロップ / CSS object-fit:cover 相当） ──
def resize_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


# ─── テキストスタイル 3パターン ────────────────────────────────────────
TEXT_STYLES = {
    "A: ダーク帯": {
        "label": "A",
        "desc": "半透明〜不透明の黒グラデ帯 + 白太字。最も汎用。",
        "prompt": """TEXT STYLE A — Dark gradient band:
- Semi-transparent to opaque dark gradient band at the bottom 25-30% of image
- Transparent at top of band → 85% black at bottom edge
- Japanese text centered horizontally on this band
- Text: pure white, ultra bold sans-serif
- Text size: large — fills 65% of band width
- Subtle drop shadow (2px dark)
- Image above the band: UNCHANGED""",
    },
    "B: アウトライン": {
        "label": "B",
        "desc": "帯なし。黄色テキスト + 極太黒縁取り。衝撃系定番。",
        "prompt": """TEXT STYLE B — Outline / stroke text:
- NO background band — text floats directly over image
- Text at the bottom 20% of image, centered horizontally
- Text color: bright yellow (#FFE600) or white
- Ultra bold / black-weight sans-serif font
- THICK black stroke outline around each character (4-5px)
- Strong drop shadow (5px pure black, 60% opacity)
- Text size: very large, commanding attention
- Image: completely preserved behind text""",
    },
    "C: カラー帯": {
        "label": "C",
        "desc": "べた塗りカラー帯 + 白字。ブランドカラーで感情直表現。",
        "prompt": """TEXT STYLE C — Solid color band:
- Fully opaque solid color band at the very bottom (22-28% of image height)
- Band color: pick the most emotionally resonant color for the content
  (e.g. red #E82222 for urgency, orange #FF6B35 for warmth, navy #0A1628 for authority)
- Sharp clean edge between image and band (no gradient)
- Text: pure white, bold sans-serif, centered in band
- Text size: fills 65-75% of band width
- Image above the band: completely unchanged""",
    },
}


# ─── Gemini モデル優先順 ───────────────────────────────────────────────
MODELS = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
]


# ─── 画像 → bytes ───────────────────────────────────────────────────────
def img_to_bytes(img: Image.Image, quality: int = 90) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


# ─── プロンプト生成 ────────────────────────────────────────────────────
def build_prompt(text: str, style_key: str, emotion_hint: str,
                 size_label: str, has_reference: bool) -> str:
    style = TEXT_STYLES[style_key]
    ref_line = (
        "STYLE REFERENCE: A reference image has been provided. "
        "Match its visual mood, color palette, and atmosphere closely."
        if has_reference else ""
    )
    return f"""You are a professional Japanese article LP banner designer.

TASK: Create a banner with Japanese text added at the bottom.

## MANDATORY TEXT:
「{text}」

## TEXT PLACEMENT (NON-NEGOTIABLE):
- Position: BOTTOM of image, horizontal (straight)
- Alignment: centered
- Do NOT alter the main image composition

## TEXT DESIGN:
{style['prompt']}

## CONTEXT:
Output size: {size_label}
Emotional direction: {emotion_hint or 'professional and impactful'}
{ref_line}

## QUALITY CHECK:
□ 「{text}」 clearly readable in 1 second? (if no → bigger/more contrast)
□ Main image subject preserved?
□ Text horizontal at bottom?"""


def build_ai_gen_prompt(description: str, text: str, style_key: str,
                         emotion_hint: str, size_label: str, has_reference: bool) -> str:
    style = TEXT_STYLES[style_key]
    ref_line = (
        "STYLE REFERENCE: Match the visual mood and color palette of the provided reference image."
        if has_reference else ""
    )
    return f"""You are a professional Japanese article LP banner designer.

TASK: Generate a complete banner image from scratch.

## IMAGE TO GENERATE:
{description}

## MANDATORY TEXT (add at the bottom of the generated image):
「{text}」

## TEXT DESIGN:
{style['prompt']}

## CONTEXT:
Output size: {size_label}
Emotional direction: {emotion_hint or 'professional and impactful'}
{ref_line}

## REQUIREMENTS:
- Generate a high-quality photographic or illustrated background
- Add 「{text}」 clearly at the bottom using the text style above
- Professional article LP banner quality"""


# ─── バナー生成（素材画像あり）──────────────────────────────────────────
def generate_from_image(
    base_img: Image.Image,
    ref_img,           # Image or None
    text: str,
    style_key: str,
    emotion_hint: str,
    target_size,
    size_label: str,
    clients: list,
) -> Image.Image:
    from google.genai import types
    from math import gcd

    if target_size:
        tw, th = target_size
        img = resize_cover(base_img, tw, th)
    else:
        img = base_img
        tw, th = img.size

    g = gcd(tw, th)
    aspect_map = {"1:1":"1:1","4:5":"4:5","3:4":"3:4","9:16":"9:16","16:9":"16:9","4:3":"4:3"}
    aspect = aspect_map.get(f"{tw//g}:{th//g}", "1:1")

    prompt = build_prompt(text, style_key, emotion_hint, size_label, ref_img is not None)

    # コンテンツリスト（素材 → 参考 → プロンプト）
    contents = [types.Part.from_bytes(data=img_to_bytes(img), mime_type="image/jpeg")]
    if ref_img:
        ref_resized = ref_img.resize((400, 400), Image.LANCZOS)
        contents.append(types.Part.from_bytes(data=img_to_bytes(ref_resized), mime_type="image/jpeg"))
        contents.append("The second image above is a STYLE REFERENCE only — match its mood/color palette.")
    contents.append(prompt)

    return _call_gemini(contents, aspect, tw, th, target_size, clients)


# ─── バナー生成（AI生成モード）──────────────────────────────────────────
def generate_from_prompt(
    description: str,
    ref_img,
    text: str,
    style_key: str,
    emotion_hint: str,
    target_size,
    size_label: str,
    clients: list,
) -> Image.Image:
    from google.genai import types
    from math import gcd

    tw, th = target_size if target_size else (680, 450)
    g = gcd(tw, th)
    aspect_map = {"1:1":"1:1","4:5":"4:5","3:4":"3:4","9:16":"9:16","16:9":"16:9","4:3":"4:3"}
    aspect = aspect_map.get(f"{tw//g}:{th//g}", "1:1")

    prompt = build_ai_gen_prompt(description, text, style_key, emotion_hint, size_label, ref_img is not None)

    contents = []
    if ref_img:
        ref_resized = ref_img.resize((400, 400), Image.LANCZOS)
        contents.append(types.Part.from_bytes(data=img_to_bytes(ref_resized), mime_type="image/jpeg"))
        contents.append("The image above is a STYLE REFERENCE — match its visual mood and color palette.")
    contents.append(prompt)

    return _call_gemini(contents, aspect, tw, th, target_size, clients)


# ─── Gemini 呼び出し共通処理 ──────────────────────────────────────────
def _call_gemini(contents, aspect, tw, th, target_size, clients):
    from google.genai import types

    last_error = None
    for model in MODELS:
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
                    if target_size:
                        result = resize_cover(result, tw, th)
                    return result
            except Exception as e:
                last_error = e
                time.sleep(2)

    raise RuntimeError(f"生成失敗（全モデル試行済み）: {last_error}")


# ─── 動画生成 ──────────────────────────────────────────────────────────
ANIMATIONS = {"なし（静止）": "none", "ゆっくりズームイン": "zoom",
               "フェードイン": "fade", "左からスライド": "slide"}

def image_to_video(img: Image.Image, duration: int, animation: str, output_path: str):
    w, h = img.size
    fps, total = 30, 30 * duration
    base_arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(total):
        t = i / max(total - 1, 1)
        if animation == "zoom":
            s = 1.0 + 0.08 * t
            nw, nh = int(w*s), int(h*s)
            z = cv2.resize(base_arr, (nw, nh))
            frame = z[(nh-h)//2:(nh-h)//2+h, (nw-w)//2:(nw-w)//2+w]
        elif animation == "fade":
            frame = (base_arr * min(t*2, 1.0)).astype(np.uint8)
        elif animation == "slide":
            off = int((1-min(t*3,1.0))*w*0.3)
            frame = np.zeros_like(base_arr)
            if off < w:
                frame[:, off:] = base_arr[:, :w-off]
        else:
            frame = base_arr.copy()
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


# ─── サイズプリセット（実LP解析ベース） ────────────────────────────────
SIZE_PRESETS = {
    "680 × 450 ★おすすめ（記事スタンダード）": ((680, 450), "680×450"),
    "680 × 350（商品KV・ワイド横長）":          ((680, 350), "680×350"),
    "680 × 300（情報帯・CTA）":                 ((680, 300), "680×300"),
    "1080 × 1080（正方形・権威KV・SNS兼用）":   ((1080, 1080), "1080×1080"),
    "素材のまま":                               (None, "素材のまま"),
}
SIZE_TIPS = {
    "680 × 450 ★おすすめ（記事スタンダード）": "モバイル表示 570×377。記事内で最多使用。冒頭・中盤どちらでも◎",
    "680 × 350（商品KV・ワイド横長）":          "モバイル表示 570×293。商品紹介・成分解説に◎",
    "680 × 300（情報帯・CTA）":                 "モバイル表示 570×251。帯スタイル。CTA・緊急性に◎",
    "1080 × 1080（正方形・権威KV・SNS兼用）":   "正方形。ブランドKV・SNS転用に◎",
    "素材のまま":                               "素材の元サイズをそのまま使用",
}


# ─── Streamlit UI ──────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="記事内バナーメーカー", page_icon="🎨", layout="centered")
    st.title("🎨 記事内バナーメーカー v8")
    st.caption("テキスト下部固定 × 3文字スタイル比較 × 参考テイスト画像対応")

    # session_state 初期化
    if "results" not in st.session_state:
        st.session_state.results = {}   # {style_key: bytes}

    # ── APIキー ──────────────────────────────────────────────────────
    _, clients = init_gemini()
    if not clients:
        st.warning("⚠️ GEMINI_API_KEY が未設定。直接入力してください。")
        key_input = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        if key_input:
            _, clients = init_gemini(key_input)
        if not clients:
            st.stop()
    st.success(f"✅ Gemini 接続済み（{len(clients)}キー）")
    st.divider()

    # ── ① 素材モード ─────────────────────────────────────────────────
    st.subheader("① 素材モード")
    input_mode = st.radio(
        "",
        ["📁 画像をそのまま使う", "✨ AIで画像を生成する（テキスト説明から）"],
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
    else:
        is_video = st.checkbox("動画素材（フレームを抽出して使用）", value=False)
        if is_video:
            base_uploaded = st.file_uploader("動画をアップロード", type=["mp4","mov"])
        else:
            base_uploaded = st.file_uploader("画像をアップロード", type=["jpg","jpeg","png"])
        if base_uploaded and not is_video:
            st.image(Image.open(base_uploaded), caption="素材プレビュー", use_container_width=True)
            base_uploaded.seek(0)
        ai_description = ""

    # ── ② 参考テイスト画像（任意） ───────────────────────────────────
    st.subheader("② 参考テイスト画像（任意）")
    st.caption("「このバナーのような雰囲気で」と伝えたい場合にアップロード。可愛い系・高齢者向け・高級感など。")
    ref_uploaded = st.file_uploader("参考バナー・画像", type=["jpg","jpeg","png"], key="ref")
    ref_img = None
    if ref_uploaded:
        ref_img = Image.open(ref_uploaded).convert("RGB")
        st.image(ref_img, caption="参考テイスト", use_container_width=True)

    # ── ③ テキスト ────────────────────────────────────────────────────
    st.subheader("③ テキスト（バナー下部に入れる文言）")
    text = st.text_input("キャッチコピー", placeholder="例：ボロボロ爪まわりの原因菌をごっそり殺菌破壊！")

    # ── ④ 感情ヒント ──────────────────────────────────────────────────
    st.subheader("④ 感情・雰囲気（任意）")
    emotion_hint = st.text_input("", placeholder="例：驚き・緊急・安心・可愛い・権威・高齢者向け温かみ",
                                  label_visibility="collapsed")

    # ── ⑤ 出力サイズ ──────────────────────────────────────────────────
    st.subheader("⑤ 出力サイズ")
    size_name = st.selectbox("", list(SIZE_PRESETS.keys()), index=0, label_visibility="collapsed")
    output_size, size_label = SIZE_PRESETS[size_name]
    st.caption(SIZE_TIPS.get(size_name, ""))

    # ── ⑥ 動画オプション ──────────────────────────────────────────────
    is_video_output = st.checkbox("動画出力（アニメーション付き）", value=False)
    duration, animation_key = 3, "none"
    if is_video_output:
        duration = st.select_slider("尺（秒）", options=[1, 3, 5, 7], value=3)
        animation_key = ANIMATIONS[st.selectbox("アニメーション", list(ANIMATIONS.keys()))]

    st.divider()

    # ── 3スタイル説明 ─────────────────────────────────────────────────
    st.subheader("生成される3パターン（文字スタイルのみ違う）")
    for key, s in TEXT_STYLES.items():
        st.markdown(f"**{key}** — {s['desc']}")
    st.divider()

    # ── 生成ボタン ────────────────────────────────────────────────────
    if st.button("🚀 3スタイル同時生成", type="primary", use_container_width=True):
        # バリデーション
        if use_ai_gen and not ai_description.strip():
            st.error("① 生成したい画像の説明を入力してください")
            return
        if not use_ai_gen and not base_uploaded:
            st.error("① 素材をアップロードしてください")
            return
        if not text.strip():
            st.error("③ テキストを入力してください")
            return

        # ベース画像準備
        if use_ai_gen:
            base_img = None
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

        # 3スタイル生成
        st.session_state.results = {}
        for style_key in TEXT_STYLES:
            label = TEXT_STYLES[style_key]["label"]
            with st.spinner(f"スタイル {label} 生成中..."):
                try:
                    if use_ai_gen:
                        img = generate_from_prompt(
                            ai_description.strip(), ref_img, text.strip(),
                            style_key, emotion_hint, output_size, size_label, clients,
                        )
                    else:
                        img = generate_from_image(
                            base_img, ref_img, text.strip(),
                            style_key, emotion_hint, output_size, size_label, clients,
                        )
                    # JPEGバイトで保存（session_stateにImage直置きは重い）
                    buf = io.BytesIO()
                    img.save(buf, "JPEG", quality=93)
                    st.session_state.results[style_key] = buf.getvalue()
                except Exception as e:
                    st.warning(f"スタイル {label} 失敗: {e}")

        if not st.session_state.results:
            st.error("全スタイルの生成に失敗しました。しばらく待ってから再試行してください。")

    # ── 結果表示（session_stateから → ダウンロードしても消えない） ────
    if st.session_state.results:
        st.success(f"✅ {len(st.session_state.results)}パターン 生成完了！")
        st.divider()

        cols = st.columns(len(st.session_state.results))
        for col, (style_key, img_bytes) in zip(cols, st.session_state.results.items()):
            s = TEXT_STYLES[style_key]
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
