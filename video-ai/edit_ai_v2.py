#!/usr/bin/env python3
"""
編集AI v2 — 台本HTML + 素材フォルダ → 縦型1分動画を自動生成

使い方:
  python3 video-ai/edit_ai_v2.py \
    --script  ~/Desktop/編集フォルダ/nabe_雑学_台本20（台本4アップデート）.html \
    --clips   ~/Desktop/編集フォルダ/素材 \
    --output  video-ai/output/nabe_test.mp4

仕組み:
  1. 台本HTMLをパース → シーンリスト（テキスト + クリップ参照）
  2. クリップ参照からファイルを自動検索
  3. 各シーン: クリップ切り出し → 縦型クロップ → テロップ描画
  4. 全シーン結合 → mp4出力
"""

from __future__ import annotations
import os
import re
import sys
import argparse
import subprocess
import tempfile
import textwrap
from pathlib import Path
from dataclasses import dataclass, field

import cv2
import numpy as np
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip,
    concatenate_videoclips,
)

# ── 定数 ──────────────────────────────────────────────────
OUTPUT_SIZE    = (1080, 1920)   # 縦型 9:16
TARGET_DURATION = 60.0          # 目標動画尺（秒）
CHARS_PER_SEC  = 4.0            # テロップ読速（文字/秒）
MIN_DURATION   = 1.5            # シーン最短秒
MAX_DURATION   = 10.0           # シーン最長秒（長すぎ防止）
FONT_SIZE      = 68             # 通常テロップ
FONT_EMPH_SIZE = 88             # 強調テロップ
CHARS_PER_LINE = 14             # 1行最大文字数
TELOP_Y_RATIO  = 0.72           # 画面の何%の高さにテロップを置くか
FFMPEG = "/opt/homebrew/bin/ffmpeg"

# 横長素材のレターボックス閾値（この比率より横長ならletterbox）
LETTERBOX_THRESHOLD = 1.2       # w/h がこれ以上なら黒枠追加

# OpenCV 顔検出モデル
_FACE_CASCADE = None
def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        xml = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(xml)
    return _FACE_CASCADE

FONT_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/Library/Fonts/Arial Unicode MS.ttf",
]

# ── データ構造 ────────────────────────────────────────────
@dataclass
class Scene:
    no: int
    text: str
    clip_refs: list[str]          # ["1-1", "1-2"] など
    notes: str = ""
    emphasis: bool = False        # 強調テロップ（感情ワード検知）

EMPHASIS_WORDS = ["臭い", "臭く", "ツーン", "病気", "悩む", "97%OFF", "無料", "卒業"]


# ── 台本パーサ ─────────────────────────────────────────────
def parse_script(html_path: str) -> list[Scene]:
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    rows = soup.find_all("tr")
    scenes: list[Scene] = []

    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 7:
            continue
        # ヘッダ行スキップ
        if cells[1] in ("NO", "A", "") or not cells[1].isdigit():
            continue

        no   = int(cells[1])
        text = cells[2].strip()
        clip_ref_raw = cells[6].strip()   # "1-11-2" → ["1-1","1-2"]
        notes = cells[3].strip()

        # クリップ参照を分割（"1-11-2" は "1-1" + "1-2"）
        clip_refs = _parse_clip_refs(clip_ref_raw)

        emphasis = any(w in text for w in EMPHASIS_WORDS)
        scenes.append(Scene(no=no, text=text, clip_refs=clip_refs,
                            notes=notes, emphasis=emphasis))

    print(f"台本パース完了: {len(scenes)} シーン")
    return scenes


def _parse_clip_refs(raw: str) -> list[str]:
    """
    "1-11-2"   → ["1-1", "1-2"]   ← シーン1の素材1と2
    "12-112-2" → ["12-1", "12-2"] ← シーン12の素材1と2
    "10-1"     → ["10-1"]
    "3"        → ["3"]
    """
    if not raw:
        return []
    # バリアント番号は常に1桁 → \d{1,2}-\d でマッチ
    refs = re.findall(r'\d{1,2}-\d', raw)
    if refs:
        return refs
    # ハイフンなし単体番号（"3", "11", "15"など）
    return re.findall(r'\d+', raw)


# ── クリップ検索 ──────────────────────────────────────────
EXTS = [".mp4", ".MP4", ".mov", ".MOV", ".HEIC", ".heic", ".jpeg", ".jpg", ".JPG", ".PNG"]

def find_clip(clips_dir: str, ref: str) -> str | None:
    """
    ref="1-1"  → 1-1.mp4 or 1-1.mov など
    ref="3"    → 3.HEIC など（全角数字も対応）
    """
    d = Path(clips_dir)

    # 半角→全角、全角→半角の両方で試す
    ref_full = ref.translate(str.maketrans("0123456789", "０１２３４５６７８９"))
    ref_half = ref.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    candidates = [ref, ref_full, ref_half]

    for c in candidates:
        for ext in EXTS:
            p = d / f"{c}{ext}"
            if p.exists():
                return str(p)
    return None


# ── フォント読み込み ────────────────────────────────────────
def load_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in FONT_CANDIDATES:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── テロップ画像生成 ──────────────────────────────────────
def make_telop(text: str, size: tuple, emphasis: bool = False) -> np.ndarray:
    """テキスト → RGBA numpy配列"""
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    fs   = FONT_EMPH_SIZE if emphasis else FONT_SIZE
    font = load_font(fs)

    # テキスト折り返し
    lines = []
    for raw_line in text.split("\n"):
        if len(raw_line) <= CHARS_PER_LINE:
            lines.append(raw_line)
        else:
            lines.extend(textwrap.wrap(raw_line, width=CHARS_PER_LINE, break_long_words=True))

    line_h = fs + 10
    total_h = line_h * len(lines)
    pad_x, pad_y = 24, 14

    # Y位置（画面の TELOP_Y_RATIO 位置を基準に上揃え）
    base_y = int(h * TELOP_Y_RATIO) - total_h // 2

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = base_y + i * line_h

        if emphasis:
            # 黄色背景 × 黒文字
            draw.rectangle(
                [x - pad_x, y - pad_y, x + tw + pad_x, y + fs + pad_y],
                fill=(255, 215, 0, 230)
            )
            draw.text((x, y), line, font=font, fill=(0, 0, 0, 255))
        else:
            # 白縁取り × 白文字
            for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)]:
                draw.text((x+dx, y+dy), line, font=font, fill=(0, 0, 0, 200))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    return np.array(img)


# ── 静止画をVideoクリップ化 ─────────────────────────────────
def image_to_clip(path: str, duration: float) -> VideoFileClip | ImageClip:
    """HEIC/JPG → ImageClip（縦型にクロップ済み）"""
    try:
        # HEICはffmpegでJPGに変換
        if path.lower().endswith(".heic"):
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.close()
            subprocess.run(
                [FFMPEG, "-y", "-i", path, tmp.name],
                capture_output=True, check=True
            )
            path = tmp.name

        img = Image.open(path).convert("RGB")
        img = fit_to_vertical(img)
        arr = np.array(img)
        clip = ImageClip(arr, duration=duration)
        return clip
    except Exception as e:
        print(f"  ⚠️  画像読み込みエラー {Path(path).name}: {e}")
        # 黒フレームで代替
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        return ImageClip(black, duration=duration)


def detect_face_center(img_arr: np.ndarray) -> tuple[int, int] | None:
    """BGRのnumpy配列から顔の中心座標(cx, cy)を返す。見つからなければNone"""
    gray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY)
    cascade = _get_face_cascade()
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
    if len(faces) == 0:
        return None
    # 最大の顔を採用
    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    return (x + fw // 2, y + fh // 2)


def fit_to_vertical(img: Image.Image) -> Image.Image:
    """
    PIL画像を OUTPUT_SIZE(1080×1920) に収める。
    - ほぼ縦型(9:16): そのままリサイズ
    - 横長: レターボックス（黒枠上下）で幅1080に収める
    - 顔検出可能: 顔中心でクロップ
    """
    w, h = img.size
    ratio = w / h
    target_ratio = OUTPUT_SIZE[0] / OUTPUT_SIZE[1]   # 0.5625

    # ほぼ縦型
    if abs(ratio - target_ratio) < 0.1:
        return img.resize(OUTPUT_SIZE, Image.LANCZOS)

    # 横長 → レターボックス or 顔中心クロップ
    if ratio > LETTERBOX_THRESHOLD:
        # まず顔検出でクロップできるか試みる
        arr = np.array(img.convert("RGB"))
        arr_bgr = arr[:, :, ::-1]
        face_c = detect_face_center(arr_bgr)

        if face_c:
            # 顔中心でクロップ
            cx, cy = face_c
            new_w = int(h * target_ratio)
            x = max(0, min(cx - new_w // 2, w - new_w))
            img = img.crop((x, 0, x + new_w, h))
            return img.resize(OUTPUT_SIZE, Image.LANCZOS)
        else:
            # 顔なし → レターボックス（幅1080に合わせ、上下黒帯）
            ow, oh = OUTPUT_SIZE
            scale = ow / w
            new_h = int(h * scale)
            resized = img.resize((ow, new_h), Image.LANCZOS)
            canvas = Image.new("RGB", (ow, oh), (0, 0, 0))
            y_offset = (oh - new_h) // 2
            canvas.paste(resized, (0, y_offset))
            return canvas

    # 縦長すぎ → センタークロップ
    new_h = int(w / target_ratio)
    y = (h - new_h) // 2
    img = img.crop((0, y, w, y + new_h))
    return img.resize(OUTPUT_SIZE, Image.LANCZOS)


def crop_clip_to_vertical(clip: VideoFileClip) -> VideoFileClip:
    """
    動画クリップを OUTPUT_SIZE に変換。
    - 横長: 先頭フレームで顔検出 → 顔中心クロップ or レターボックス
    - 縦型: そのままリサイズ
    """
    w, h = clip.size
    ratio = w / h
    target_ratio = OUTPUT_SIZE[0] / OUTPUT_SIZE[1]

    # ほぼ縦型
    if abs(ratio - target_ratio) < 0.1:
        return clip.resize(OUTPUT_SIZE)

    if ratio > LETTERBOX_THRESHOLD:
        # 先頭フレームで顔検出
        try:
            frame = clip.get_frame(min(0.5, clip.duration * 0.1))
            frame_bgr = frame[:, :, ::-1].astype(np.uint8)
            face_c = detect_face_center(frame_bgr)
        except Exception:
            face_c = None

        if face_c:
            # 顔中心クロップ
            cx, _ = face_c
            new_w = int(h * target_ratio)
            x1 = max(0, min(cx - new_w // 2, w - new_w))
            clip = clip.crop(x1=x1, y1=0, x2=x1+new_w, y2=h)
            return clip.resize(OUTPUT_SIZE)
        else:
            # レターボックス: 幅1080にスケールし上下黒帯
            ow, oh = OUTPUT_SIZE
            scale = ow / w
            new_h = int(h * scale)
            y_offset = (oh - new_h) // 2

            def add_letterbox(frame):
                resized = cv2.resize(frame, (ow, new_h))
                canvas = np.zeros((oh, ow, 3), dtype=np.uint8)
                canvas[y_offset:y_offset+new_h] = resized
                return canvas

            return clip.fl_image(add_letterbox).set_duration(clip.duration)

    # 縦長すぎ → センタークロップ
    new_h = int(w / target_ratio)
    y1 = (h - new_h) // 2
    clip = clip.crop(x1=0, y1=y1, x2=w, y2=y1+new_h)
    return clip.resize(OUTPUT_SIZE)


# ── シーン1本分のVideoClipを生成 ──────────────────────────────
def build_scene_clip(scene: Scene, clips_dir: str,
                     override_duration: float | None = None) -> CompositeVideoClip | None:
    # 尺計算（mainでスケール済みの値を優先）
    text_len = len(scene.text)
    duration = override_duration if override_duration else \
               max(MIN_DURATION, min(MAX_DURATION, text_len / CHARS_PER_SEC))

    print(f"  シーン{scene.no}: 「{scene.text[:20]}...」 → {duration:.1f}s refs={scene.clip_refs}")

    # クリップ検索（-1優先、なければ-2、なければ番号のみ）
    clip_path = None
    for ref in scene.clip_refs:
        found = find_clip(clips_dir, ref)
        if found:
            clip_path = found
            break

    if not clip_path:
        print(f"    ⚠️  シーン{scene.no}: クリップが見つかりません（refs={scene.clip_refs}）→ 黒フレームで代替")
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        base = ImageClip(black, duration=duration)
    else:
        ext = Path(clip_path).suffix.lower()
        print(f"    ✅ {Path(clip_path).name}")

        if ext in (".heic", ".jpeg", ".jpg", ".png"):
            base = image_to_clip(clip_path, duration)
        else:
            try:
                raw = VideoFileClip(clip_path)
                raw = raw.set_audio(None)          # ① 音声削除
                raw = crop_clip_to_vertical(raw)   # ② 顔検出クロップ or レターボックス
                if raw.duration > duration:
                    raw = raw.subclip(0, duration)
                else:
                    duration = raw.duration
                base = raw
            except Exception as e:
                print(f"    ⚠️  動画読み込みエラー: {e}")
                black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
                base = ImageClip(black, duration=duration)

    # テキストなしシーン（CTAなど）はテロップなし
    if not scene.text:
        return base if hasattr(base, 'duration') else None

    # テロップ画像 → ImageClip
    telop_arr  = make_telop(scene.text, OUTPUT_SIZE, emphasis=scene.emphasis)
    telop_clip = ImageClip(telop_arr, duration=base.duration).set_opacity(1.0)

    return CompositeVideoClip([base, telop_clip], size=OUTPUT_SIZE)


# ── メイン ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="編集AI v2")
    parser.add_argument("--script",  required=True, help="台本HTMLファイルパス")
    parser.add_argument("--clips",   required=True, help="素材フォルダパス")
    parser.add_argument("--output",  default="video-ai/output/output_v2.mp4", help="出力mp4パス")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    print("\n📄 台本パース中...")
    scenes = parse_script(args.script)

    # ③ 60秒に収まるようにシーン尺をスケール
    valid_scenes = [s for s in scenes if s.text or s.clip_refs]
    raw_durations = []
    for s in valid_scenes:
        tl = len(s.text)
        raw_durations.append(max(MIN_DURATION, min(MAX_DURATION, tl / CHARS_PER_SEC)))
    total_raw = sum(raw_durations)
    scale = min(1.0, TARGET_DURATION / total_raw) if total_raw > TARGET_DURATION else 1.0
    if scale < 1.0:
        print(f"  ⏱  尺スケール: {total_raw:.1f}s → {TARGET_DURATION}s（×{scale:.2f}）")

    print(f"\n🎬 シーンクリップ生成中（{len(valid_scenes)}シーン）...")
    clips = []
    for scene, base_dur in zip(valid_scenes, raw_durations):
        adjusted_dur = max(MIN_DURATION, base_dur * scale)
        c = build_scene_clip(scene, args.clips, override_duration=adjusted_dur)
        if c is not None:
            clips.append(c)

    if not clips:
        print("❌ 有効なシーンがありません")
        sys.exit(1)

    print(f"\n✂️  {len(clips)}シーンを結合中...")
    final = concatenate_videoclips(clips, method="compose")
    total_sec = final.duration

    print(f"\n💾 出力中: {args.output} （{total_sec:.1f}秒）")
    final.write_videofile(
        args.output,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-crf", "23"],
        logger=None,
    )

    print(f"\n✅ 完成！ {args.output}")
    print(f"   総尺: {total_sec:.1f}秒 / {len(clips)}シーン")


if __name__ == "__main__":
    main()
