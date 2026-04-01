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


# ─── Fish Audio: 声カタログ読み込み ──────────────────────────
def load_voice_catalog() -> dict:
    catalog_path = Path(__file__).parent / "voice_catalog.json"
    if catalog_path.exists():
        with open(catalog_path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def resolve_voice(category: str | None, catalog: dict) -> tuple[str | None, float]:
    """
    声カテゴリー名 → (reference_id, speed) を返す。
    IDが未設定("FILL_FROM_FISH_AUDIO")の場合は None を返し、Fish Audioデフォルトにフォールバック。
    """
    voices = catalog.get("voices", {})
    defaults = catalog.get("defaults", {})

    # カテゴリー未指定 → デフォルトカテゴリーを使う
    if not category:
        category = defaults.get("fallback_category", "女性・クール")

    voice = voices.get(category)
    if not voice:
        print(f"  ⚠️  声カテゴリー '{category}' が voice_catalog.json に見つかりません。デフォルト音声を使用。")
        return None, 1.0

    ref_id = voice.get("reference_id", "")
    if not ref_id or ref_id == "FILL_FROM_FISH_AUDIO":
        print(f"  ⚠️  '{category}' の reference_id が未設定です。voice_catalog.json を更新してください。")
        print(f"      → fish.audio でモデルを探してIDを設定: https://fish.audio/models")
        return None, voice.get("speed", 1.0)

    print(f"  🎙  声: {category} (reference_id: {ref_id[:8]}...)")
    return ref_id, voice.get("speed", 1.0)


# ─── Fish Audio: ナレーション生成 ────────────────────────────
def generate_narration(
    scenes: list,
    fish_key: str,
    output_path: str,
    voice_category: str | None = None,
) -> str | None:
    """
    全シーンのテキストを結合してFish AudioでMP3生成。
    voice_category: voice_catalog.json のキー名（例: "女性・クール"）
    返値: 生成したmp3パス（失敗時None）
    """
    full_text = "。".join(s.text for s in scenes if s.text).strip()
    if not full_text:
        return None

    catalog = load_voice_catalog()
    reference_id, speed = resolve_voice(voice_category, catalog)

    payload: dict = {"text": full_text, "format": "mp3", "latency": "normal"}
    if reference_id:
        payload["reference_id"] = reference_id
    if speed != 1.0:
        payload["prosody"] = {"speed": speed}

    try:
        resp = requests.post(
            "https://api.fish.audio/v1/tts",
            headers={"Authorization": f"Bearer {fish_key}", "Content-Type": "application/json"},
            json=payload,
            stream=True,
            timeout=60
        )
        if resp.status_code != 200:
            print(f"  ⚠️  Fish Audio エラー: {resp.status_code} / {resp.text[:100]}")
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
    note: str = ""                # このカット専用の注釈（上部に小さく表示）
    emphasis: bool = False        # 強調テロップ（感情ワード検知）

EMPHASIS_WORDS = ["臭い", "臭く", "ツーン", "病気", "悩む", "97%OFF", "無料", "卒業"]


# ── 台本パーサ ─────────────────────────────────────────────
def parse_script(html_path: str) -> tuple[list[Scene], str]:
    """
    返値: (scenes, global_annotation)
    - scenes: 全シーンリスト（NO空白の続き行も含む）
    - global_annotation: 全カット共通の上部注釈テキスト
    """
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    rows = soup.find_all("tr")
    scenes: list[Scene] = []
    global_annotation = ""

    # ① 列インデックスを自動検出（テキスト列=2, 注釈列=3, 素材列を探す）
    clip_col  = 6   # デフォルト（ver1）
    notes_col = 3   # デフォルト
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 7:
            continue
        for i, c in enumerate(cells):
            if "差し込み" in c or ("画像" in c and "動画" in c):
                clip_col = i
                print(f"  [台本] 素材列: 列{clip_col}（{c}）")
                break
        else:
            continue
        break

    # ② 全行スキャン前に global_annotation を取得（NO=空 かつ cells[2]に「注釈」指示）
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 4:
            continue
        # "右の注釈は常に" のような指示行 → cells[3] が通し注釈テキスト
        if "注釈" in cells[2] and "常に" in cells[2]:
            raw = cells[3].strip()
            # 括弧内の説明部分（指示文）を除去
            raw = re.sub(r'（[^）]*提示[^）]*）', '', raw).strip()
            global_annotation = raw
            print(f"  [台本] 通し注釈を検出: {global_annotation[:40]}...")
            break

    # ③ シーン行をパース（NO=空白の続き行も全て取得）
    last_no = 0
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < clip_col + 1:
            continue

        # ヘッダ行・空行スキップ
        no_cell = cells[1].strip()
        if no_cell in ("NO", "A"):
            continue

        # テキストが空なら無視
        text = cells[2].strip()
        if not text:
            continue

        # NO列が数字なら更新、空白なら前のNOを継続（続き行）
        if no_cell.isdigit():
            last_no = int(no_cell)
        elif last_no == 0:
            continue  # 最初のNO確定前の行はスキップ

        clip_ref_raw = cells[clip_col].strip() if clip_col < len(cells) else ""
        note = cells[notes_col].strip() if notes_col < len(cells) else ""

        # クリップ参照を分割（"1-11-2" は "1-1" + "1-2"）
        clip_refs = _parse_clip_refs(clip_ref_raw)

        emphasis = any(w in text for w in EMPHASIS_WORDS)
        scenes.append(Scene(no=last_no, text=text, clip_refs=clip_refs,
                            note=note, emphasis=emphasis))

    print(f"台本パース完了: {len(scenes)} シーン（通し注釈: {'あり' if global_annotation else 'なし'}）")
    return scenes, global_annotation


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


# ── 注釈オーバーレイ生成（上部小テキスト） ──────────────────────
ANNOT_FONT_SIZE  = 26
ANNOT_CHARS_LINE = 28

def make_annotation_overlay(text: str, size: tuple, y_start: int = 30) -> np.ndarray:
    """上部に小さく注釈テキストを描画したRGBAオーバーレイを返す。"""
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(ANNOT_FONT_SIZE)
    lines: list[str] = []
    for raw in text.split("\n"):
        lines.extend(textwrap.wrap(raw, width=ANNOT_CHARS_LINE, break_long_words=True) or [raw])
    line_h = ANNOT_FONT_SIZE + 6
    for i, line in enumerate(lines):
        y = y_start + i * line_h
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            draw.text((20+dx, y+dy), line, font=font, fill=(0, 0, 0, 200))
        draw.text((20, y), line, font=font, fill=(255, 255, 255, 220))
    return np.array(img)


# ── テロップ画像生成 ──────────────────────────────────────
def make_telop(text: str, size: tuple, emphasis: bool = False) -> np.ndarray:
    """
    テキスト → RGBA numpy配列。
    「※」以降は自動的に小フォントで描画。
    """
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ※ でメインテキストと注釈テキストに分割
    if "※" in text:
        idx       = text.index("※")
        main_text = text[:idx].strip()
        sub_text  = text[idx:].strip()
    else:
        main_text = text
        sub_text  = ""

    fs       = FONT_EMPH_SIZE if emphasis else FONT_SIZE
    cpl      = CHARS_PER_LINE_EMPH if emphasis else CHARS_PER_LINE
    font     = load_font(fs)
    sub_fs   = max(32, fs // 2)
    sub_font = load_font(sub_fs)

    def _wrap(t, width):
        lines: list[str] = []
        for raw in (t or "").split("\n"):
            lines.extend(textwrap.wrap(raw, width=width, break_long_words=True) or [raw])
        return lines

    main_lines = _wrap(main_text or text, cpl)
    sub_lines  = _wrap(sub_text, cpl + 4) if sub_text else []

    line_h     = fs + 10
    sub_line_h = sub_fs + 6
    total_h    = line_h * len(main_lines) + (sub_line_h * len(sub_lines) + 4 if sub_lines else 0)
    pad_x, pad_y = 24, 14
    base_y = int(h * TELOP_Y_RATIO) - total_h // 2

    def _draw_line(line, fnt, fsize, y, emph):
        bbox = fnt.getbbox(line)
        tw   = bbox[2] - bbox[0]
        x    = max(pad_x, (w - tw) // 2)
        if emph:
            draw.rectangle(
                [x - pad_x, y - pad_y, x + tw + pad_x, y + fsize + pad_y],
                fill=(255, 215, 0, 230)
            )
            draw.text((x, y), line, font=fnt, fill=(0, 0, 0, 255))
        else:
            for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)]:
                draw.text((x+dx, y+dy), line, font=fnt, fill=(0, 0, 0, 200))
            draw.text((x, y), line, font=fnt, fill=(255, 255, 255, 255))

    cur_y = base_y
    for line in main_lines:
        _draw_line(line, font, fs, cur_y, emphasis)
        cur_y += line_h
    if sub_lines:
        cur_y += 4
        for line in sub_lines:
            _draw_line(line, sub_font, sub_fs, cur_y, False)
            cur_y += sub_line_h

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
                     gemini_key: str | None = None,
                     global_annotation: str = "") -> CompositeVideoClip | None:
    # 尺計算（mainでスケール済みの値を優先）
    text_len = len(scene.text)
    duration = override_duration if override_duration else \
               max(MIN_DURATION, min(MAX_DURATION, text_len / CHARS_PER_SEC))

    print(f"  シーン{scene.no}: 「{scene.text[:20]}...」 → {duration:.1f}s refs={scene.clip_refs}")

    found_clips: list[str] = []
    for ref in scene.clip_refs:
        p = find_clip(clips_dir, ref)
        if p:
            found_clips.append(p)

    if not found_clips:
        print(f"    ⚠️  シーン{scene.no}: クリップが見つかりません（refs={scene.clip_refs}）→ 黒フレームで代替")
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        base: VideoFileClip | ImageClip | CompositeVideoClip = ImageClip(black, duration=duration)
    elif len(found_clips) == 1:
        print(f"    ✅ {Path(found_clips[0]).name}")
        base = _load_single_clip(found_clips[0], duration, gemini_key)
        duration = base.duration
    else:
        per_dur = duration / len(found_clips)
        print(f"    ✅ {len(found_clips)}クリップを等分 ({per_dur:.1f}s×{len(found_clips)})")
        sub_clips = []
        for cp in found_clips:
            print(f"      • {Path(cp).name}")
            sc = _load_single_clip(cp, per_dur, gemini_key)
            sub_clips.append(sc)
        base = concatenate_videoclips(sub_clips, method="compose")
        duration = base.duration

    layers = [base]

    # テロップ（テキストありのみ）
    if scene.text:
        telop_arr  = make_telop(scene.text, OUTPUT_SIZE, emphasis=scene.emphasis)
        layers.append(ImageClip(telop_arr, duration=base.duration).set_opacity(1.0))

    # 通し注釈（全カット共通）
    if global_annotation:
        ann_arr = make_annotation_overlay(global_annotation, OUTPUT_SIZE, y_start=24)
        layers.append(ImageClip(ann_arr, duration=base.duration).set_opacity(1.0))

    # カット専用注釈（注釈欄あり）
    if scene.note:
        note_y = 24 + (ANNOT_FONT_SIZE + 6) * (global_annotation.count("\n") + 1) + 10
        note_arr = make_annotation_overlay(scene.note, OUTPUT_SIZE, y_start=note_y)
        layers.append(ImageClip(note_arr, duration=base.duration).set_opacity(1.0))

    return CompositeVideoClip(layers, size=OUTPUT_SIZE)


# ── メイン ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="編集AI v2")
    parser.add_argument("--script",  required=True, help="台本HTMLファイルパス")
    parser.add_argument("--clips",   required=True, help="素材フォルダパス")
    parser.add_argument("--output",  default="video-ai/output/output_v2.mp4", help="出力mp4パス")
    parser.add_argument("--no-ai",   action="store_true", help="AI API（Gemini/Fish Audio）を使わない")
    parser.add_argument("--remotion", action="store_true", help="Remotion用 composition.json も出力する")
    parser.add_argument("--voice",   default=None,
                        help="声カテゴリー（例: '女性・クール' '男性・権威'）。未指定時はvoice_catalog.jsonのデフォルトを使用")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # APIキー取得
    def _get_env(key):
        return subprocess.run(["zsh", "-i", "-c", f"echo ${key}"],
                              capture_output=True, text=True).stdout.strip()
    gemini_key = _get_env("GEMINI_API_KEY_1") if not args.no_ai else None
    fish_key   = _get_env("FISH_AUDIO_API_KEY") if not args.no_ai else None

    print("\n📄 台本パース中...")
    scenes, global_annotation = parse_script(args.script)

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
            str(Path(args.output).parent / "narration.mp3"),
            voice_category=args.voice,
        )

    print(f"\n🎬 シーンクリップ生成中（{len(valid_scenes)}シーン）...")
    clips = []
    for scene, base_dur in zip(valid_scenes, raw_durations):
        adjusted_dur = max(MIN_DURATION, base_dur * scale)
        c = build_scene_clip(scene, args.clips,
                             override_duration=adjusted_dur,
                             gemini_key=gemini_key,
                             global_annotation=global_annotation)
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
