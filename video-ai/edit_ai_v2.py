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
import json
import base64
import argparse
import subprocess
import tempfile
import textwrap
from pathlib import Path
from dataclasses import dataclass, field

import cv2
import numpy as np
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips,
)

# ── 定数 ──────────────────────────────────────────────────
OUTPUT_SIZE    = (1080, 1920)   # 縦型 9:16
TARGET_DURATION = 60.0          # 目標動画尺（秒）
CHARS_PER_SEC  = 4.0            # テロップ読速（文字/秒）
MIN_DURATION   = 1.5            # シーン最短秒
MAX_DURATION   = 10.0           # シーン最長秒（長すぎ防止）
FONT_SIZE           = 76         # 通常テロップ（68→76に拡大）
FONT_EMPH_SIZE      = 84         # 強調テロップ
CHARS_PER_LINE      = 14         # 通常テロップ 1行最大文字数
CHARS_PER_LINE_EMPH = 11         # 強調テロップ 1行最大文字数（大きいフォント対応）
TELOP_Y_RATIO       = 0.72       # 画面の何%の高さにテロップを置くか
FFMPEG = "/opt/homebrew/bin/ffmpeg"

# 横長素材のレターボックス閾値（この比率より横長ならletterbox）
LETTERBOX_THRESHOLD = 1.2       # w/h がこれ以上なら黒枠追加

# ─── ffmpegで向き正規化（回転メタデータを焼き込み） ────────────
_FFPROBE = "/opt/homebrew/bin/ffprobe"
_NORMALIZED_CACHE: dict[str, str] = {}   # path → normalized tmp path

def normalize_video_orientation(clip_path: str) -> str:
    """
    ffmpegでクリップを再エンコードして回転メタデータを消去・焼き込む。
    ffmpegはデフォルトで回転タグを適用するので、出力は常に正しい向き。
    キャッシュ済みなら再利用。
    """
    if clip_path in _NORMALIZED_CACHE:
        return _NORMALIZED_CACHE[clip_path]

    # 回転メタデータがなければそのまま返す
    has_rotation = False
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream_side_data=rotation",
             "-of", "default=noprint_wrappers=1", clip_path],
            capture_output=True, text=True
        )
        has_rotation = "rotation" in r.stdout
    except Exception:
        pass

    if not has_rotation:
        _NORMALIZED_CACHE[clip_path] = clip_path
        return clip_path

    # ffmpegで回転を焼き込んだtmpファイルを生成
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp.close()
    try:
        subprocess.run(
            [FFMPEG, "-y", "-i", clip_path,
             "-c:v", "libx264", "-preset", "fast", "-crf", "23",
             "-an",                  # 音声なし
             "-metadata:s:v", "rotate=0",   # メタデータのrotateをリセット
             tmp.name],
            capture_output=True, check=True
        )
        print(f"      🔄 向き正規化: {Path(clip_path).name}")
        _NORMALIZED_CACHE[clip_path] = tmp.name
        return tmp.name
    except Exception as e:
        print(f"      ⚠️  向き正規化失敗 ({e})、元ファイルを使用")
        _NORMALIZED_CACHE[clip_path] = clip_path
        return clip_path


# OpenCV 顔検出モデル
_FACE_CASCADE = None
def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        xml = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(xml)
    return _FACE_CASCADE


# ─── Gemini Vision: クリップ内容分析 ──────────────────────────
def analyze_clip_with_gemini(clip_path: str, gemini_key: str) -> dict:
    """
    クリップの先頭フレームをGemini 2.0 Flashに送り、
    被写体と最適クロップ方向を返す。
    返値例: {"subject":"白衣の医師が話している", "crop_hint":"center", "reason":"..."}
    """
    try:
        frame_tmp = tempfile.mktemp(suffix=".jpg")
        subprocess.run(
            [FFMPEG, "-y", "-i", clip_path, "-vframes", "1", "-ss", "0.5", frame_tmp],
            capture_output=True, check=True
        )
        with open(frame_tmp, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        os.unlink(frame_tmp)

        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}",
            json={"contents": [{"parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                {"text": (
                    "この動画フレームについてJSONのみで答えて。\n"
                    "fields:\n"
                    "  subject: 何が映っているか（日本語・具体的に）\n"
                    "  crop_hint: 縦型9:16クロップ時に被写体が見切れないよう\n"
                    "             左右どちらに寄せるべきか（left/center/right）\n"
                    "  reason: 理由（日本語・1文）\n"
                    "JSON only。余計な説明不要。"
                )}
            ]}]},
            timeout=15
        )
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r"```json|```", "", raw).strip()
        # 閉じ括弧が欠けることがあるので補完
        if not raw.endswith("}"):
            raw += "}"
        return json.loads(raw)
    except Exception as e:
        return {"subject": "不明", "crop_hint": "center", "reason": f"分析失敗: {e}"}


# ─── Fish Audio: ナレーション生成 ────────────────────────────
def generate_narration(scenes: list, fish_key: str, output_path: str) -> str | None:
    """
    全シーンのテキストを結合してFish AudioでMP3生成。
    返値: 生成したmp3パス（失敗時None）
    """
    full_text = "。".join(s.text for s in scenes if s.text).strip()
    if not full_text:
        return None
    try:
        resp = requests.post(
            "https://api.fish.audio/v1/tts",
            headers={"Authorization": f"Bearer {fish_key}", "Content-Type": "application/json"},
            json={"text": full_text, "format": "mp3", "latency": "normal"},
            stream=True,
            timeout=60
        )
        if resp.status_code != 200:
            print(f"  ⚠️  Fish Audio エラー: {resp.status_code}")
            return None
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        size_kb = os.path.getsize(output_path) // 1024
        print(f"  ✅ ナレーション生成完了: {output_path} ({size_kb}KB)")
        return output_path
    except Exception as e:
        print(f"  ⚠️  Fish Audio 失敗: {e}")
        return None

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

    # ヘッダ行から「差し込み画像/動画」列インデックスを自動検出
    clip_col = 6  # デフォルト（ver1）
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 7:
            continue
        for i, c in enumerate(cells):
            if "差し込み" in c or "画像" in c:
                clip_col = i
                print(f"  [台本] 素材列を自動検出: 列{clip_col}（{c}）")
                break
        else:
            continue
        break

    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < clip_col + 1:
            continue
        # ヘッダ行スキップ
        if cells[1] in ("NO", "A", "") or not cells[1].isdigit():
            continue

        no   = int(cells[1])
        text = cells[2].strip()
        clip_ref_raw = cells[clip_col].strip()
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

def expand_clip_refs(refs: list[str], clips_dir: str) -> list[str]:
    """
    台本のrefs=['5-1'] → 5-2, 5-3... も自動発見して ['5-1','5-2'] を返す。
    '5-1' のような X-N 形式のみ展開。単体番号('3'等)は展開しない。
    既に複数指定済み(e.g. ['1-1','1-2'])はそのまま使う。
    """
    expanded: list[str] = []
    seen: set[str] = set()

    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        expanded.append(ref)

        # X-1 形式なら X-2, X-3 ... を自動探索
        m = re.match(r'^(\d{1,2})-(\d)$', ref)
        if m:
            base, variant = m.group(1), int(m.group(2))
            # variantの次から順に見つかる限り追加
            nxt = variant + 1
            while True:
                candidate = f"{base}-{nxt}"
                if candidate in seen:
                    break
                if find_clip(clips_dir, candidate):
                    seen.add(candidate)
                    expanded.append(candidate)
                    nxt += 1
                else:
                    break

    return expanded


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

    fs      = FONT_EMPH_SIZE if emphasis else FONT_SIZE
    cpl     = CHARS_PER_LINE_EMPH if emphasis else CHARS_PER_LINE
    font    = load_font(fs)

    # テキスト折り返し
    lines = []
    for raw_line in text.split("\n"):
        if len(raw_line) <= cpl:
            lines.append(raw_line)
        else:
            lines.extend(textwrap.wrap(raw_line, width=cpl, break_long_words=True))

    line_h = fs + 10
    total_h = line_h * len(lines)
    pad_x, pad_y = 24, 14

    # Y位置（画面の TELOP_Y_RATIO 位置を基準に上揃え）
    base_y = int(h * TELOP_Y_RATIO) - total_h // 2

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0]
        x = max(pad_x, (w - tw) // 2)   # 左端クランプ（はみ出し防止）
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

        img = Image.open(path)
        img = ImageOps.exif_transpose(img)  # EXIF回転情報を適用
        img = img.convert("RGB")
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
    """PIL画像を OUTPUT_SIZE(1080×1920) に変換。全アスペクト比に対応。"""
    w, h = img.size
    ratio = w / h
    target_ratio = OUTPUT_SIZE[0] / OUTPUT_SIZE[1]   # 0.5625
    ow, oh = OUTPUT_SIZE

    if abs(ratio - target_ratio) < 0.08:
        return img.resize((ow, oh), Image.LANCZOS)

    if ratio > target_ratio:
        # 9:16より横広い（3:4〜16:9など）
        if ratio > LETTERBOX_THRESHOLD:
            # かなり横長 → 顔検出 or レターボックス
            arr = np.array(img.convert("RGB"))[:, :, ::-1]
            face_c = detect_face_center(arr)
            if face_c:
                cx, _ = face_c
                new_w = int(h * target_ratio)
                x = max(0, min(cx - new_w // 2, w - new_w))
                img = img.crop((x, 0, x + new_w, h))
            else:
                scale = ow / w
                new_h = int(h * scale)
                resized = img.resize((ow, new_h), Image.LANCZOS)
                canvas = Image.new("RGB", (ow, oh), (0, 0, 0))
                canvas.paste(resized, (0, (oh - new_h) // 2))
                return canvas
        else:
            # やや横広（3:4など）→ 幅を9:16に合わせてセンタークロップ
            new_w = int(h * target_ratio)
            x = (w - new_w) // 2
            img = img.crop((x, 0, x + new_w, h))
    else:
        # 9:16より縦長 → 高さを1920に合わせてスケール、幅が足りなければピラーボックス
        scale = oh / h
        new_w = int(w * scale)
        resized = img.resize((new_w, oh), Image.LANCZOS)
        if new_w >= ow:
            x = (new_w - ow) // 2
            return resized.crop((x, 0, x + ow, oh))
        canvas = Image.new("RGB", (ow, oh), (0, 0, 0))
        canvas.paste(resized, ((ow - new_w) // 2, 0))
        return canvas

    return img.resize((ow, oh), Image.LANCZOS)


def crop_clip_to_vertical(clip: VideoFileClip, crop_hint: str = "center") -> VideoFileClip:
    """動画クリップを OUTPUT_SIZE に変換。全アスペクト比に対応。"""
    w, h = clip.size
    ratio = w / h
    target_ratio = OUTPUT_SIZE[0] / OUTPUT_SIZE[1]
    ow, oh = OUTPUT_SIZE

    if abs(ratio - target_ratio) < 0.08:
        return clip.resize((ow, oh))

    if ratio > target_ratio:
        # 9:16より横広い
        if ratio > LETTERBOX_THRESHOLD:
            # かなり横長 → 顔検出 → Gemini hint → レターボックス の優先順
            try:
                frame = clip.get_frame(min(0.5, clip.duration * 0.1))
                face_c = detect_face_center(frame[:, :, ::-1].astype(np.uint8))
            except Exception:
                face_c = None

            if face_c:
                cx, _ = face_c
                new_w = int(h * target_ratio)
                x1 = max(0, min(cx - new_w // 2, w - new_w))
                return clip.crop(x1=x1, y1=0, x2=x1+new_w, y2=h).resize((ow, oh))

            # Gemini hint でクロップ
            new_w = int(h * target_ratio)
            if crop_hint == "left":   x1 = 0
            elif crop_hint == "right": x1 = w - new_w
            else:                      x1 = (w - new_w) // 2
            x1 = max(0, min(x1, w - new_w))
            return clip.crop(x1=x1, y1=0, x2=x1+new_w, y2=h).resize((ow, oh))
        else:
            # やや横広（3:4など）→ 幅センタークロップ
            new_w = int(h * target_ratio)
            x1 = (w - new_w) // 2
            return clip.crop(x1=x1, y1=0, x2=x1+new_w, y2=h).resize((ow, oh))
    else:
        # 9:16より縦長 → 高さ1920にスケール、幅が足りなければピラーボックス
        scale = oh / h
        new_w = int(w * scale)
        resized = clip.resize((new_w, oh))
        if new_w >= ow:
            x1 = (new_w - ow) // 2
            return resized.crop(x1=x1, y1=0, x2=x1+ow, y2=oh)
        x_off = (ow - new_w) // 2

        def add_pillarbox(frame):
            canvas = np.zeros((oh, ow, 3), dtype=np.uint8)
            canvas[:, x_off:x_off+new_w] = frame
            return canvas

        return resized.fl_image(add_pillarbox).set_duration(clip.duration)


# ── シーン1本分のVideoClipを生成 ──────────────────────────────
def _load_single_clip(clip_path: str, duration: float,
                      gemini_key: str | None) -> VideoFileClip | ImageClip:
    """1つのクリップファイルを読み込み、縦型クロップ・尺カットして返す。"""
    ext = Path(clip_path).suffix.lower()
    if ext in (".heic", ".jpeg", ".jpg", ".png"):
        return image_to_clip(clip_path, duration)

    try:
        # ffmpegで向きを正規化してから読み込む（回転メタデータを焼き込み）
        normalized_path = normalize_video_orientation(clip_path)
        raw = VideoFileClip(normalized_path)
        raw = raw.set_audio(None)

        crop_hint = "center"
        if gemini_key:
            analysis = analyze_clip_with_gemini(clip_path, gemini_key)
            crop_hint = analysis.get("crop_hint", "center")
            print(f"      🤖 Gemini: {analysis.get('subject','')} → {crop_hint}")

        raw = crop_clip_to_vertical(raw, crop_hint=crop_hint)
        if raw.duration > duration:
            raw = raw.subclip(0, duration)
        return raw
    except Exception as e:
        print(f"      ⚠️  動画読み込みエラー {Path(clip_path).name}: {e}")
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        return ImageClip(black, duration=duration)


def build_scene_clip(scene: Scene, clips_dir: str,
                     override_duration: float | None = None,
                     gemini_key: str | None = None) -> CompositeVideoClip | None:
    # 尺計算（mainでスケール済みの値を優先）
    text_len = len(scene.text)
    duration = override_duration if override_duration else \
               max(MIN_DURATION, min(MAX_DURATION, text_len / CHARS_PER_SEC))

    print(f"  シーン{scene.no}: 「{scene.text[:20]}...」 → {duration:.1f}s refs={scene.clip_refs}")

    # 台本のrefs を自動展開（5-1 → 5-1, 5-2 など）してから全クリップ収集
    expanded_refs = expand_clip_refs(scene.clip_refs, clips_dir)
    if expanded_refs != scene.clip_refs:
        print(f"    🔍 自動展開: {scene.clip_refs} → {expanded_refs}")

    found_clips: list[str] = []
    for ref in expanded_refs:
        p = find_clip(clips_dir, ref)
        if p:
            found_clips.append(p)

    if not found_clips:
        print(f"    ⚠️  シーン{scene.no}: クリップが見つかりません（refs={scene.clip_refs}）→ 黒フレームで代替")
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        base: VideoFileClip | ImageClip | CompositeVideoClip = ImageClip(black, duration=duration)
    elif len(found_clips) == 1:
        # 1クリップ: 従来通り
        print(f"    ✅ {Path(found_clips[0]).name}")
        base = _load_single_clip(found_clips[0], duration, gemini_key)
        duration = base.duration
    else:
        # 複数クリップ: 等分して結合
        per_dur = duration / len(found_clips)
        print(f"    ✅ {len(found_clips)}クリップを等分 ({per_dur:.1f}s×{len(found_clips)})")
        sub_clips = []
        for cp in found_clips:
            print(f"      • {Path(cp).name}")
            sc = _load_single_clip(cp, per_dur, gemini_key)
            sub_clips.append(sc)
        base = concatenate_videoclips(sub_clips, method="compose")
        duration = base.duration

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
    parser.add_argument("--no-ai",   action="store_true", help="AI API（Gemini/Fish Audio）を使わない")
    parser.add_argument("--remotion", action="store_true", help="Remotion用 composition.json も出力する")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # APIキー取得
    def _get_env(key):
        return subprocess.run(["zsh", "-i", "-c", f"echo ${key}"],
                              capture_output=True, text=True).stdout.strip()
    gemini_key = _get_env("GEMINI_API_KEY_1") if not args.no_ai else None
    fish_key   = _get_env("FISH_AUDIO_API_KEY") if not args.no_ai else None

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

    # ① Fish Audio: ナレーション先行生成
    narration_path = None
    if fish_key:
        print("\n🎙  Fish Audio: ナレーション生成中...")
        narration_path = generate_narration(
            valid_scenes, fish_key,
            str(Path(args.output).parent / "narration.mp3")
        )

    print(f"\n🎬 シーンクリップ生成中（{len(valid_scenes)}シーン）...")
    clips = []
    for scene, base_dur in zip(valid_scenes, raw_durations):
        adjusted_dur = max(MIN_DURATION, base_dur * scale)
        c = build_scene_clip(scene, args.clips,
                             override_duration=adjusted_dur,
                             gemini_key=gemini_key)   # ② Gemini Vision
        if c is not None:
            clips.append(c)

    if not clips:
        print("❌ 有効なシーンがありません")
        sys.exit(1)

    print(f"\n✂️  {len(clips)}シーンを結合中...")
    final = concatenate_videoclips(clips, method="compose")
    total_sec = final.duration

    # ③ ナレーション合成
    if narration_path and Path(narration_path).exists():
        print(f"\n🎙  ナレーションを動画に合成中...")
        try:
            narr = AudioFileClip(narration_path)
            # ナレーションの尺に合わせて動画全体をスピード調整
            if narr.duration > total_sec * 1.15:
                speed = narr.duration / total_sec
                print(f"  ⏩ ナレーションが長いため動画を×{speed:.2f}倍速に調整")
                final = final.speedx(speed)
                total_sec = final.duration
            # ナレーションが短ければそのまま（動画の余りは無音）
            narr_cut = narr.subclip(0, min(narr.duration, total_sec))
            final = final.set_audio(narr_cut)
        except Exception as e:
            print(f"  ⚠️  ナレーション合成失敗: {e}")

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
    if narration_path:
        print(f"   ナレーション: {narration_path}")

    # Remotion用 composition.json を出力（--remotion オプション時）
    if args.remotion:
        _export_composition_json(valid_scenes, raw_durations, scale, narration_path, args)


def _export_composition_json(scenes, raw_durations, scale, narration_path, args):
    """Remotionが読み込む composition.json を生成"""
    fps = 30
    comp_scenes = []
    clips_dir = args.clips

    for scene, base_dur in zip(scenes, raw_durations):
        adjusted_dur = max(MIN_DURATION, base_dur * scale)
        frames = int(adjusted_dur * fps)

        clip_path = ""
        for ref in scene.clip_refs:
            found = find_clip(clips_dir, ref)
            if found:
                clip_path = str(Path(found).resolve())
                break

        comp_scenes.append({
            "clip": clip_path,
            "text": scene.text,
            "emphasis": scene.emphasis,
            "durationFrames": frames,
        })

    comp = {
        "fps": fps,
        "width": OUTPUT_SIZE[0],
        "height": OUTPUT_SIZE[1],
        "scenes": comp_scenes,
        "narration": str(Path(narration_path).resolve()) if narration_path else None,
    }

    out_path = Path(args.output).parent / "composition.json"
    out_path.write_text(json.dumps(comp, ensure_ascii=False, indent=2))
    print(f"\n📋 Remotion用 composition.json → {out_path}")
    print(f"   レンダリング: cd video-ai/remotion && npx remotion render src/Root.tsx VideoAI ../output/remotion_out.mp4")


if __name__ == "__main__":
    main()
