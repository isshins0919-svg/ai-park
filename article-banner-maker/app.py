#!/usr/bin/env python3
"""
記事内バナーメーカー v3 — Gemini (Nano Banana Pro) × パク哲学フル注入
PIL文字貼りを廃止。Geminiがデザインを丸ごと生成。
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

# ─── 環境変数取得（Streamlit Secrets → 環境変数 → zshrc） ───────────
def get_env(key: str) -> str:
    # Streamlit Cloud Secrets（辞書アクセス）
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    # 環境変数
    v = os.environ.get(key, "").strip()
    if v:
        return v
    # ローカル Mac zshrc
    try:
        r = subprocess.run(["zsh", "-i", "-c", f"echo ${key}"],
                           capture_output=True, text=True, timeout=5)
        v = r.stdout.strip()
        if v:
            return v
    except Exception:
        pass
    return ""

# ─── Gemini クライアント初期化（キャッシュなし） ──────────────────────
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

# ─── パク哲学 × デザイン知識 ─────────────────────────────────────────
DESIGN_KNOWLEDGE = """
## パク哲学 — クリエイティブの3つの魂
1. キービジュアルそのもの：1枚が商品の世界観を体現する作品。「広告」を超えて「作品」に見えるか。
2. キラーキャッチコピー：1行で商品の全てを語れるレベルの言葉。「この1行だけ見て、買いたくなるか？」
3. 別の仮説：固有の検証仮説を持つ。同じコピーの色違いを量産しない。

## 設計原則
- 人は感情で買う。論理は後付け。まず感情を動かす。
- N1の脳内に1番乗りする。Only1のポジション。
- 「真に偉大か？」「1秒で止まるか？」が基準。
- 小さな嘘をつかない。本物の体験だけを見せる。

## バナー設計ルール（必須）
- テキストは必ず「3秒で読める」大きさ（画像高さの10%以上のフォントサイズ）
- コントラスト比 4.5:1 以上（白文字なら暗い背景、黒文字なら明るい背景）
- テキストにはドロップシャドウ または アウトライン で可読性を確保
- フォントは最大2種類まで
- 余白を活かした美しいレイアウト
- 構図はシンプル。ゴチャゴチャ禁止

## 禁止事項
- テキストを小さくする
- テキストが背景に埋もれる（読めない）
- 3種類以上のフォントを使う
- ごちゃごちゃした構図
- 日本語テキストが読みにくい位置・サイズ

## フックDB（バナー版 - 参考）
- BH1 数字衝撃: 「-Xkg」「X万人突破」「X%OFF」→ 巨大フォント
- BH2 疑問/問題提起: 「まだXXで悩んでる?」→ 吹き出し風
- BH4 社会的証明: 「XX万人が選んだ」→ バッジ
- BH5 緊急性: 「今だけ」「残りX個」→ 赤背景帯
- BH8 新常識提案: 「XXはもう古い」→ 対比構造
"""

# ─── 感情×デザイン言語 ───────────────────────────────────────────────
EMOTION_DESIGN = {
    "共感": {
        "color": "暖色系。オレンジ(#FF6B35)または温かい赤(#E84545)。背景は白/クリーム系。",
        "font": "丸ゴシック系。太めで親しみやすく。",
        "layout": "温かみのある光。人物中心。テキストは下部に大きく。半透明の暖色オーバーレイ。",
        "mood": "共感・親近感。「あなたのことを分かっている」雰囲気。",
        "text": "オレンジまたは白の太字。暖色の半透明背景上に。読みやすいサイズで大きく。",
    },
    "驚き": {
        "color": "高コントラスト。黒背景×黄(#FFE600)。または白背景×黒極太テキスト。",
        "font": "極太ゴシック。インパクト最大。",
        "layout": "大胆な構図。テキストが全体の35〜45%を占めても良い。衝撃的な配置。",
        "mood": "衝撃・驚き。「え、知らなかった！」の感覚。",
        "text": "黄色または白で超大きく。中央配置。黒いアウトライン太め。",
    },
    "安心": {
        "color": "緑系(#4CAF50, #88C057)または清潔な白×青(#4A90E2)。清潔感・誠実さ。",
        "font": "標準ゴシック。読みやすく落ち着いた印象。",
        "layout": "余白多め。整理されたクリーンなレイアウト。ナチュラルライト。",
        "mood": "安心・信頼。「大丈夫」「これで解決する」感覚。",
        "text": "ダークグリーンまたは白。緑/青のアクセントカラーを背景やバンドに使用。",
    },
    "権威": {
        "color": "ネイビー(#0A1628)×ゴールド(#C9A84C)。または深い紺×白。上品で格式ある配色。",
        "font": "明朝体または太ゴシック。格式と専門性。",
        "layout": "左右バランス・中央構図。落ち着いた高級感。専門家・実績の雰囲気。",
        "mood": "権威・専門性・信頼。「これが本物」「専門家が認めた」感覚。",
        "text": "ゴールドまたは白テキスト。ネイビー背景上に。シャープで読みやすいフォント。",
    },
    "期待": {
        "color": "明るく鮮やか。ピンク(#FF4081)または明るいオレンジ(#FF6E40)。白との組み合わせ。",
        "font": "太ゴシック。エネルギッシュで前向き。",
        "layout": "上向きの構図。躍動感・動き。明るく開放的。",
        "mood": "期待・ワクワク。「これが来る！」「もうすぐ変わる」感覚。",
        "text": "白または明るい黄色。ピンク/オレンジの鮮やかな背景またはグラデーション上に。",
    },
}
DEFAULT_EMOTION = {
    "color": "黒×白。高コントラスト。テキストは白。背景にダークグラデーション。",
    "font": "太ゴシック。インパクトある読みやすいフォント。",
    "layout": "テキスト下部配置。人物・商品は上部〜中央。",
    "mood": "インパクト・訴求力。",
    "text": "白い太字テキスト。黒いドロップシャドウ付き。大きく明確に。",
}

# ─── Imagen-3 用プロンプト生成（英語）──────────────────────────────
def build_imagen_prompt(text: str, emotion: str, custom_emotion: str,
                        image_desc: str, size_label: str, comp_instruction: str) -> str:
    em = EMOTION_DESIGN.get(emotion, DEFAULT_EMOTION)
    emotion_label = emotion or custom_emotion or "impact"

    # 感情→英語スタイル
    style_map = {
        "共感": "warm orange tones, friendly rounded font, soft glowing light, empathetic mood",
        "驚き": "high contrast black and yellow, ultra bold impact font, shocking dramatic composition",
        "安心": "clean green and white, clear readable layout, natural light, trustworthy calm mood",
        "権威": "navy and gold, elegant serif font, prestigious authoritative composition",
        "期待": "vibrant pink and orange gradient, energetic bold font, upward dynamic composition",
    }
    style = style_map.get(emotion, "high contrast, bold typography, professional advertising design")

    return f"""Professional Japanese article LP banner advertisement.

Base image description: {image_desc}

Required Japanese text overlay (MUST be large and clearly readable): 「{text}」

Design style: {style}
Composition: {comp_instruction}
Output size: {size_label}

Design requirements:
- The Japanese text 「{text}」 MUST appear prominently and be clearly readable
- Large bold typography, minimum 10% of image height
- Text contrast ratio 4.5:1 minimum (white text on dark overlay, or dark text on light)
- Text must have drop shadow or outline for readability
- Professional gradient or solid overlay behind text
- Maximum 2 font styles
- Clean, uncluttered layout with proper white space
- Photographic quality, magazine-level production

Quality standard: This banner must stop someone scrolling in 1 second. It should feel like a brand key visual, not just an advertisement.

IMPORTANT: Include the exact Japanese text 「{text}」 visibly in the image."""


# ─── Gemini multimodal 用プロンプト ──────────────────────────────────
VARIANT_HINTS = [
    "Use bold typography with the text centered at the bottom third of the image.",
    "Place the text at the top of the image with a gradient overlay behind it.",
    "Use a strong semi-transparent band across the middle to highlight the text.",
]

def build_prompt(text: str, emotion: str, custom_emotion: str, size_label: str, variant: int = 0) -> str:
    em = EMOTION_DESIGN.get(emotion, DEFAULT_EMOTION) if emotion else DEFAULT_EMOTION
    emotion_label = emotion or custom_emotion or "インパクト訴求"
    variant_hint = VARIANT_HINTS[variant % len(VARIANT_HINTS)]

    # 感情→英語スタイル
    style_map = {
        "共感": "warm orange tones, friendly rounded font, soft glowing light, empathetic mood",
        "驚き": "high contrast black and yellow, ultra bold impact font, shocking dramatic composition",
        "安心": "clean green and white, clear readable layout, natural light, trustworthy calm mood",
        "権威": "navy and gold, elegant serif font, prestigious authoritative composition",
        "期待": "vibrant pink and orange gradient, energetic bold font, upward dynamic composition",
    }
    style_en = style_map.get(emotion, "high contrast, bold typography, professional advertising design")

    return f"""You are a world-class Japanese advertising creative director.

Using the provided image as the base, create a professional article LP banner.

MANDATORY TEXT (MUST appear large and clearly readable in the final image):
「{text}」

Design style: {style_en}
Color scheme: {em['color']}
Font style: {em['font']}
Text treatment: {em['text']}
Layout & mood: {em['layout']} / {em['mood']}
Output size: {size_label}

Text placement rule: {variant_hint}

CRITICAL REQUIREMENTS:
1. The Japanese text 「{text}」 MUST be visible, large (≥10% of image height), and clearly readable
2. Text must have sufficient contrast (white on dark, or dark on light) — add drop shadow or outline
3. Do NOT use more than 2 font styles
4. Keep layout clean — no clutter
5. The banner must stop a viewer in 1 second

QUALITY STANDARD (from パク哲学):
- "Is this truly great?" — it should feel like a brand key visual, not just an ad
- Human emotion first, logic second
- Only ONE message: 「{text}」

Generate the banner now. Preserve the original image subject while adding the text overlay and design elements."""

# ─── Gemini でバナー生成 ─────────────────────────────────────────────
def analyze_image(base_image: Image.Image, clients: list) -> str:
    """Gemini Flash で画像を分析して説明文を生成"""
    from google.genai import types
    buf = io.BytesIO()
    base_image.save(buf, format="JPEG", quality=85)
    img_bytes = buf.getvalue()
    for client in clients:
        try:
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    "この画像を詳細に説明してください。被写体・人物・商品・背景・色調・雰囲気・構図を具体的に日本語で。",
                ],
            )
            return resp.text.strip()
        except Exception:
            continue
    return "人物または商品の写真"


def generate_banners(
    base_image: Image.Image,
    text: str,
    emotion: str,
    custom_emotion: str,
    composition: str,
    size,
    size_label: str,
    clients: list,
    n: int = 3,
) -> list:
    """
    素材画像を直接Geminiに渡してバナーを生成（画像入力→画像出力）。
    元素材を活かしたまま、テキストとデザインを追加する。
    """
    from google.genai import types
    from math import gcd

    # アスペクト比
    if size:
        tw, th = size
        base_image = base_image.resize((tw, th), Image.LANCZOS)
    else:
        tw, th = base_image.size
    g = gcd(tw, th)
    aspect_map = {"1:1":"1:1","4:5":"4:5","3:4":"3:4","9:16":"9:16","16:9":"16:9","4:3":"4:3"}
    aspect = aspect_map.get(f"{tw//g}:{th//g}", "1:1")

    # 画像→バイト列
    buf = io.BytesIO()
    base_image.save(buf, format="JPEG", quality=90)
    img_bytes = buf.getvalue()

    # 構図指示
    comp_map = {
        "寄り（クローズアップ）": "Crop tighter. Subject fills more of the frame. Emphasize the key element.",
        "引き（ワイドショット）": "Show more environment. Wider framing with context and atmosphere.",
        "バランス（標準）": "Keep original composition. Balanced framing.",
    }
    comp_instruction = comp_map.get(composition, comp_map["バランス（標準）"])

    # 画像入力→画像出力モデル（元素材を保持）
    MODELS = [
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview",
        "gemini-2.5-flash-image",
    ]

    images = []
    last_error = None

    for i in range(n):
        prompt = build_prompt(text, emotion, custom_emotion, size_label, variant=i) + f"\n\nComposition: {comp_instruction}"
        generated = False
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
                        images.append(result)
                        generated = True
                        break
                except Exception as e:
                    last_error = e
                    time.sleep(3)
            if generated:
                break

    if images:
        return images

    raise RuntimeError(
        f"画像生成に失敗しました。数分後に再試行してください。\n詳細: {last_error}"
    )


# ─── 動画生成ユーティリティ ─────────────────────────────────────────
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
            x = (nw - w) // 2
            y = (nh - h) // 2
            frame = zoomed[y:y+h, x:x+w]

        elif animation == "fade":
            alpha = min(t * 2, 1.0)
            frame = (base_arr * alpha).astype(np.uint8)

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

# ─── サイズプリセット ────────────────────────────────────────────────
SIZE_PRESETS = {
    "素材のまま": (None, "素材のまま"),
    "680 × 450（横長・記事メイン）": ((680, 450), "680×450 横長"),
    "680 × 800（縦長・強調）": ((680, 800), "680×800 縦長"),
    "1080 × 1080（正方形・SNS）": ((1080, 1080), "1080×1080 正方形"),
    "1080 × 1920（縦動画・ストーリーズ）": ((1080, 1920), "1080×1920 縦動画"),
    "1280 × 720（横動画）": ((1280, 720), "1280×720 横動画"),
}

# ─── Streamlit UI ────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="記事内バナーメーカー", page_icon="🎨", layout="centered")
    st.title("🎨 記事内バナーメーカー v3")
    st.caption("Nano Banana Pro（Gemini）× パク哲学フル注入 → プロ品質バナーを自動生成")

    # APIキー取得（自動 or 手動入力）
    api_key_override = ""
    genai_module, clients = init_gemini()
    if not clients:
        st.warning("⚠️ GEMINI_API_KEY_1 が自動取得できませんでした。以下に直接入力してください。")
        api_key_override = st.text_input(
            "Gemini API Key", type="password",
            placeholder="AIzaSy...",
            help="Google AI Studio (aistudio.google.com) で取得できます"
        )
        if api_key_override:
            genai_module, clients = init_gemini(api_key_override)
        if not clients:
            st.stop()

    st.success(f"✅ Gemini 接続済み（{len(clients)}キー）")
    st.divider()

    # ── ① 入力 / 出力タイプ ─────────────────────────────────────────
    st.subheader("① 入力 → 出力タイプ")
    output_mode = st.radio(
        "",
        ["画像 → 画像（静止バナー）",
         "画像 → 動画（アニメーション付き）",
         "動画 → 画像（フレーム抽出 → バナー）",
         "動画 → 動画（フレーム抽出 → アニメーション）"],
        label_visibility="collapsed",
    )
    is_video_input = output_mode.startswith("動画 →")
    is_video_output = output_mode.endswith("動画）") or output_mode.endswith("アニメーション付き）")

    # ── ② ベース素材 ────────────────────────────────────────────────
    st.subheader("② ベース素材")
    if is_video_input:
        uploaded = st.file_uploader("動画をアップロード", type=["mp4", "mov"])
    else:
        uploaded = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])

    # ── ③ 出力サイズ ────────────────────────────────────────────────
    st.subheader("③ 出力サイズ")
    size_name = st.selectbox("サイズプリセット", list(SIZE_PRESETS.keys()))
    output_size, size_label = SIZE_PRESETS[size_name]

    # ── ④ テキスト ──────────────────────────────────────────────────
    st.subheader("④ テキスト（バナー内に入れる文言）")
    text = st.text_input("キャッチコピー・見出し", placeholder="例：足の臭いが気になる方へ")

    # ── ⑤ 感情タグ ──────────────────────────────────────────────────
    st.subheader("⑤ 感情タグ")
    st.caption("選択するとデザイン指示（カラー・フォント・構図）が変わります")
    emotion_list = list(EMOTION_DESIGN.keys())
    cols = st.columns(len(emotion_list))
    selected_emotions = []
    for i, e in enumerate(emotion_list):
        if cols[i].checkbox(e, key=f"emo_{e}"):
            selected_emotions.append(e)
    custom_emotion = st.text_input("または自由入力（例：焦り・ワクワク・悔しさ）", placeholder="感情を自由に入力")

    # ── ⑥ 構図（寄り/引き） ────────────────────────────────────────
    st.subheader("⑥ 構図")
    composition = st.radio(
        "",
        ["寄り（クローズアップ）", "バランス（標準）", "引き（ワイドショット）"],
        index=1,
        horizontal=True,
        label_visibility="collapsed",
    )
    comp_desc = {
        "寄り（クローズアップ）": "被写体を大きく・感情の強度を上げる。顔・商品・細部にフォーカス。",
        "バランス（標準）": "被写体と背景のバランス。記事LP標準構図。",
        "引き（ワイドショット）": "環境・シーン全体を見せる。世界観・安心感・権威感に合う。",
    }
    st.caption(comp_desc[composition])

    # ── ⑦ 動画オプション（動画出力のみ） ─────────────────────────────
    duration, animation_key = 3, "none"
    if is_video_output:
        st.subheader("⑦ 動画オプション")
        duration = st.select_slider("尺（秒）", options=[1, 3, 5, 7], value=3)
        anim_name = st.selectbox("アニメーション", list(ANIMATIONS.keys()))
        animation_key = ANIMATIONS[anim_name]

    st.divider()

    # ── 生成ボタン ───────────────────────────────────────────────────
    if st.button("🚀 Gemini で3枚生成する（候補3パターン）", type="primary", use_container_width=True):
        if not uploaded:
            st.error("② ベース素材をアップロードしてください")
            return
        if not text.strip():
            st.error("④ テキストを入力してください")
            return

        emotion = selected_emotions[0] if selected_emotions else ""
        emotion_label = emotion or custom_emotion or "custom"
        suffix = Path(uploaded.name).suffix.lower()

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded.read())
            input_path = tmp.name

        with st.spinner("Gemini で3パターン生成中... （候補ごとにレイアウトを変えています・60〜90秒）"):
            try:
                if is_video_input:
                    base_img = extract_frame(input_path)
                else:
                    base_img = Image.open(input_path).convert("RGB")

                banner_imgs = generate_banners(
                    base_img, text.strip(), emotion, custom_emotion,
                    composition, output_size, size_label, clients,
                    n=3,
                )
            except Exception as e:
                st.error(f"生成エラー: {e}")
                return
            finally:
                if os.path.exists(input_path):
                    os.unlink(input_path)

        st.success(f"✅ {len(banner_imgs)}枚 生成完了！")
        st.divider()

        # ── 候補を並べて表示・ダウンロード ─────────────────────────
        cols_out = st.columns(len(banner_imgs))
        for idx, img in enumerate(banner_imgs):
            with cols_out[idx]:
                st.image(img, caption=f"候補 {idx+1}", use_container_width=True)

                if is_video_output:
                    out_buf = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                    image_to_video(img, duration, animation_key, out_buf.name)
                    with open(out_buf.name, "rb") as f:
                        st.download_button(
                            f"⬇ 候補{idx+1} 動画",
                            data=f,
                            file_name=f"banner_{emotion_label}_{idx+1}_{duration}s.mp4",
                            mime="video/mp4",
                            key=f"dl_video_{idx}",
                        )
                    os.unlink(out_buf.name)
                else:
                    buf = io.BytesIO()
                    img.save(buf, "JPEG", quality=93)
                    st.download_button(
                        f"⬇ 候補{idx+1} 画像",
                        data=buf.getvalue(),
                        file_name=f"banner_{emotion_label}_{idx+1}.jpg",
                        mime="image/jpeg",
                        key=f"dl_img_{idx}",
                    )


if __name__ == "__main__":
    main()
