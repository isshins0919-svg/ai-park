#!/usr/bin/env python3
"""
gungun_render.py — ぐんぐん習慣 Letterbox動画レンダラー v4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【v4変更点（参考動画に完全準拠）】
  ① テロップタイミング: TIMING_OFFSET=-0.35s（350ms前出し）
  ② 映像比率: 16:9→4:3（VIDEO_H=810px）/ ZOOM_FACTOR=1.15で人物アップ
  ③ テロップ位置: 下黒帯→映像エリア内下部に移動（参考動画同様）
     - 半透明ダークバー＋太縁取り（±4px）で視認性確保
  ④ レイアウト全体を4:3映像に合わせて再計算

【レイアウト（1080×1920出力）】
  ┌─────────────────┐ y=0
  │ ※注釈（小文字）  │ y=10
  │ 18歳が            │ y=230
  │ ラストチャンス    │ y=322  ← 上黒帯 (0-520)
  ├─────────────────┤ y=520
  │  横長映像（4:3）  │        ← 映像 1080×810
  │  ┌テロップBG┐    │ y=1110
  │  │テロップ  │    │ y=1130 ← 映像内下部に配置
  │  └─────────┘    │
  ├─────────────────┤ y=1330
  │  下黒帯           │        ← (1330-1920)
  └─────────────────┘ y=1920
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ─── 定数 ────────────────────────────────────────────────────
FFMPEG  = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

# 出力サイズ
OUT_W, OUT_H = 1080, 1920

# レイアウト（v4: 4:3映像）
VIDEO_Y      = 520    # 映像エリア開始Y（上黒帯 520px）
VIDEO_H      = 810    # 映像エリア高さ（4:3 @ 1080px幅 = 1080*3/4）
VIDEO_BOTTOM = VIDEO_Y + VIDEO_H  # = 1330

# ズーム設定（4:3は既に横クロップ済みなので控えめに）
ZOOM_FACTOR  = 1.15   # ズーム倍率
CROP_Y_SHIFT = 30     # 上方シフトpx（顔が見えるように上寄り）

# テキストレイアウト（上黒帯 520px に合わせて再計算）
ANNO_Y        = 10
ANNO_FONTSIZE = 26
ANNO_LINE_H   = 32
ANNO_MAX_W    = OUT_W - 24

TITLE_Y        = 230   # 上黒帯520pxに収まるよう調整
TITLE_FONTSIZE = 82
TITLE_LINE_GAP = 92

# テロップ（映像エリア内下部に配置 — 参考動画同様）
TELOP_Y         = VIDEO_BOTTOM - 200  # = 1130（映像内下部）
TELOP_FONTSIZE  = 62
TELOP_LINE_H    = 76
TELOP_MAX_CHARS = 13
KOME_SIZE_RATIO = 0.55

# フォント（太い角ゴシックで視認性重視）
FONT_BOLD  = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"   # テロップ・タイトル
FONT_MED   = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"   # 注釈

# Whisperキャッシュ
WHISPER_CACHE_DIR = Path(__file__).parent / "_cache"

# テロップタイミングオフセット（発話開始の350ms前に出す — マジで重要）
TIMING_OFFSET = -0.35

# 日本語助詞（タイトル自動改行）
JP_PARTICLES = "がのにをはもでへとよりから"

# 音量正規化ターゲット（参考動画実測: -14.19 LUFS）
LOUDNORM_TARGET = "loudnorm=I=-14:LRA=11:TP=-1.5"


# ─── フォント ─────────────────────────────────────────────────
def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_MED
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def text_width(draw: ImageDraw.Draw, text: str, font) -> int:
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    except Exception:
        return len(text) * font.size


def text_height(draw: ImageDraw.Draw, text: str, font) -> int:
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]
    except Exception:
        return font.size


# ─── テキスト折り返し（ピクセル幅基準）────────────────────────
def wrap_text_by_width(text: str, font, max_w: int) -> list[str]:
    """ピクセル幅でテキストを折り返す。"""
    dummy_img  = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)

    if text_width(dummy_draw, text, font) <= max_w:
        return [text]

    lines: list[str] = []
    current = ""
    for char in text:
        test = current + char
        if text_width(dummy_draw, test, font) > max_w and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def wrap_telop(text: str, max_chars: int) -> list[str]:
    """テロップを文字数で折り返す。まず意味的分割を試みる。"""
    if "\n" in text:
        return text.split("\n")
    return wrap_telop_smart(text, max_chars)


def wrap_telop_smart(text: str, max_chars: int) -> list[str]:
    """
    テロップを意味的に折り返す。
    全体の長さが max_chars 以下なら1行。
    超える場合、中央付近(±3文字)で助詞・読点・活用終止形を探して分割。
    見つからなければ単純に max_chars で切る。
    """
    if len(text) <= max_chars:
        return [text]

    # 分割候補文字（助詞終わり・読点・句点・活用形終わり）
    SPLIT_CHARS = set("がのにをはもでへとよりからまでついてもがながら、。！？")

    mid = len(text) // 2
    # 中央から±4文字の範囲で分割点を探す（中央に近い方を優先）
    best_pos = None
    best_dist = 999
    for offset in range(0, 5):
        for sign in [1, -1]:
            pos = mid + offset * sign
            if 2 <= pos <= len(text) - 2:
                # pos の直後で分割（pos文字目まで前半）
                if text[pos] in SPLIT_CHARS or text[pos - 1] in SPLIT_CHARS:
                    split_at = pos if text[pos - 1] in SPLIT_CHARS else pos + 1
                    dist = abs(split_at - mid)
                    if dist < best_dist:
                        best_dist = dist
                        best_pos = split_at

    if best_pos and best_pos > 1:
        first  = text[:best_pos]
        second = text[best_pos:]
        # 再帰的に折り返し（どちらかが長い場合）
        result = []
        result.extend(wrap_telop_smart(first, max_chars) if len(first) > max_chars else [first])
        result.extend(wrap_telop_smart(second, max_chars) if len(second) > max_chars else [second])
        return result

    # フォールバック: max_charsで単純分割
    lines = []
    while len(text) > max_chars:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    if text:
        lines.append(text)
    return lines


# ─── タイトル自動改行 ─────────────────────────────────────────
def split_title(title: str) -> list[str]:
    """助詞位置でタイトルを2行分割。"""
    if "\n" in title:
        return title.split("\n")
    if len(title) <= 6:
        return [title]
    for i in range(3, min(8, len(title) - 1)):
        if title[i] in JP_PARTICLES:
            return [title[:i+1], title[i+1:]]
    mid = len(title) // 2
    return [title[:mid], title[mid:]]


# ─── ※含みテロップ描画 ─────────────────────────────────────────
def draw_telop_line_with_kome(
    draw: ImageDraw.Draw,
    text: str,
    y: int,
    font_main: ImageFont.FreeTypeFont,
    font_kome: ImageFont.FreeTypeFont,
    canvas_w: int,
):
    """
    テロップ1行描画。※記号のみ小さく（上付き風）。
    シャドウ装飾のみ（縁取りなし・背景バーなし）。
    右下に複数レイヤーのシャドウを落として映像上でも読める視認性を確保。
    """
    # シャドウ: 右下方向に複数レイヤー（濃さをグラデーションで）
    SHADOW_LAYERS = [
        (5, 5, 200),  # 遠い影（濃い）
        (4, 4, 200),
        (3, 3, 180),
        (2, 2, 150),  # 近い影（少し薄め）
    ]

    def draw_seg(seg: str, font, x: int, y_off: int = 0):
        # シャドウを遠い順に描く
        for sdx, sdy, alpha in SHADOW_LAYERS:
            draw.text((x + sdx, y + y_off + sdy), seg, font=font, fill=(0, 0, 0, alpha))
        # 本文（白・不透明）
        draw.text((x, y + y_off), seg, font=font, fill=(255, 255, 255, 255))
        return x + text_width(draw, seg, font)

    parts = re.split(r'(※)', text)
    segments = []
    total_w = 0
    for part in parts:
        if not part:
            continue
        if part == "※":
            w = text_width(draw, "※", font_kome)
            segments.append(("kome", "※", w))
        else:
            w = text_width(draw, part, font_main)
            segments.append(("main", part, w))
        total_w += segments[-1][2]

    x = (canvas_w - total_w) // 2
    kome_y_off = -int(font_main.size * 0.1)
    for kind, seg_text, w in segments:
        if kind == "kome":
            draw_seg(seg_text, font_kome, x, kome_y_off)
        else:
            draw_seg(seg_text, font_main, x, 0)
        x += w


# ─── オーバーレイ生成ヘルパー ─────────────────────────────────
def _draw_annotation(draw: ImageDraw.Draw, annotation: str, scene_note: str = ""):
    """注釈テキストを上黒帯エリアに描画（overflow自動折り返し）。"""
    if not annotation and not scene_note:
        return
    font = load_font(ANNO_FONTSIZE, bold=False)
    raw_segs = []
    if annotation:
        for seg in re.split(r'[　\n]', annotation):
            seg = seg.strip()
            if seg:
                raw_segs.append(seg)
    if scene_note:
        for seg in re.split(r'[　\n]', scene_note):
            seg = seg.strip()
            if seg:
                raw_segs.append(seg)

    y = ANNO_Y
    for seg in raw_segs:
        for line in wrap_text_by_width(seg, font, ANNO_MAX_W):
            if y + ANNO_LINE_H > VIDEO_Y - 5:
                return  # overflow防止
            draw.text((12, y), line, font=font, fill=(255, 255, 255, 200))
            y += ANNO_LINE_H


def _draw_title(draw: ImageDraw.Draw, title_lines: list[str]):
    """タイトルを上黒帯エリアに描画。"""
    font = load_font(TITLE_FONTSIZE, bold=True)
    STROKE_T = [(dx, dy) for dx in (-4, 0, 4) for dy in (-4, 0, 4) if not (dx == 0 and dy == 0)]
    y = TITLE_Y
    for line in title_lines:
        w = text_width(draw, line, font)
        x = (OUT_W - w) // 2
        for dx, dy in STROKE_T:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 230))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += TITLE_LINE_GAP


def _draw_telop(draw: ImageDraw.Draw, telop_text: str):
    """
    テロップを映像エリア内下部に描画（参考動画同様）。
    - 半透明ダークバーで背景を抑えて視認性UP
    - 太縁取り（±4px）でさらに視認性UP
    """
    if not telop_text:
        return
    font_main = load_font(TELOP_FONTSIZE, bold=True)
    font_kome = load_font(int(TELOP_FONTSIZE * KOME_SIZE_RATIO), bold=False)
    lines = wrap_telop(telop_text, TELOP_MAX_CHARS)
    n_lines = len(lines)

    # ── 背景バー: なし（シャドウのみで視認性確保）─────────────

    # ── テロップテキスト ──────────────────────────────────────
    y = TELOP_Y
    for line in lines:
        if y >= VIDEO_BOTTOM:
            break
        draw_telop_line_with_kome(draw, line, y, font_main, font_kome, OUT_W)
        y += TELOP_LINE_H


# ─── 静的オーバーレイ（黒帯＋タイトルのみ）────────────────────
def make_static_overlay(title_lines: list[str]) -> np.ndarray:
    """
    常時表示オーバーレイ: 上下黒帯 + タイトル。
    注釈・テロップはシーン別オーバーレイに任せる。
    """
    img  = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (OUT_W, VIDEO_Y)], fill=(0, 0, 0, 255))
    draw.rectangle([(0, VIDEO_BOTTOM), (OUT_W, OUT_H)], fill=(0, 0, 0, 255))
    _draw_title(draw, title_lines)
    return np.array(img)


# ─── シーン別オーバーレイ（透明背景＋注釈＋テロップ）──────────
def make_scene_overlay(annotation: str, telop_text: str, scene_note: str = "") -> np.ndarray:
    """
    シーン別オーバーレイ: 透明背景に注釈とテロップのみ。
    静的オーバーレイの上に重ねる。
    """
    img  = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _draw_annotation(draw, annotation, scene_note)
    _draw_telop(draw, telop_text)
    return np.array(img)


# ─── FV用フルオーバーレイ（黒帯＋全テキスト）─────────────────
def make_fv_overlay(title_lines: list[str], annotation: str, telop_text: str, scene_note: str = "") -> np.ndarray:
    """FVシーン用フルオーバーレイ（1枚で全要素を含む）。"""
    img  = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (OUT_W, VIDEO_Y)], fill=(0, 0, 0, 255))
    draw.rectangle([(0, VIDEO_BOTTOM), (OUT_W, OUT_H)], fill=(0, 0, 0, 255))
    _draw_annotation(draw, annotation, scene_note)
    _draw_title(draw, title_lines)
    _draw_telop(draw, telop_text)
    return np.array(img)


# ─── FFmpeg ──────────────────────────────────────────────────
def ffmpeg_run(*args, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [FFMPEG, "-y"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_duration(path: str) -> float:
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def get_video_size(path: str) -> tuple[int, int]:
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    lines = r.stdout.strip().split("\n")
    try:
        return int(lines[0]), int(lines[1])
    except Exception:
        return 1920, 1080


# ─── ズーム込みスケール・クロップフィルタ ────────────────────
def get_scale_crop_filter(src_w: int, src_h: int) -> str:
    """
    ズームインした上でVIDEO_H×OUT_Wに収まるscale+crop+padフィルタを返す。
    ZOOM_FACTOR=1.35 / CROP_Y_SHIFTで上方シフト（顔強調）。
    """
    zoomed_h = round(VIDEO_H * ZOOM_FACTOR)  # 592 * 1.35 ≈ 799
    scaled_w  = round(src_w / src_h * zoomed_h)

    if scaled_w >= OUT_W:
        scale_f = f"scale={scaled_w}:{zoomed_h}"
        crop_x  = (scaled_w - OUT_W) // 2
        crop_y  = max(0, (zoomed_h - VIDEO_H) // 2 - CROP_Y_SHIFT)
        crop_f  = f"crop={OUT_W}:{VIDEO_H}:{crop_x}:{crop_y}"
    else:
        # 幅が足りない場合は幅を基準にスケール（ズーム込み）
        scaled_h = round(src_h / src_w * OUT_W * ZOOM_FACTOR)
        scale_f  = f"scale={OUT_W}:{scaled_h}"
        crop_y   = max(0, (scaled_h - VIDEO_H) // 2 - CROP_Y_SHIFT)
        crop_f   = f"crop={OUT_W}:{VIDEO_H}:0:{crop_y}"

    pad_f = f"pad={OUT_W}:{OUT_H}:0:{VIDEO_Y}:black"
    return f"{scale_f},{crop_f},{pad_f}"


# ─── 黒フレームスキップ ───────────────────────────────────────
def get_first_non_black_time(path: str) -> float:
    """
    冒頭の黒フレーム区間を検出してスキップ時刻を返す。
    - blackdetectで検出した場合はその時刻
    - 検出できない場合でも最低 MIN_SKIP_SEC はスキップ
      （カメラ起動直後のフェードイン対策）
    """
    MIN_SKIP_SEC = 0.15  # 常に最低0.15sスキップ

    r = subprocess.run(
        [FFMPEG, "-i", path,
         "-vf", "blackdetect=d=0.03:pic_th=0.85:pix_th=0.05",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True
    )
    matches = re.findall(r'black_end:([\d.]+)', r.stderr)
    if matches:
        t = max(MIN_SKIP_SEC, float(matches[0]))
        print(f"    🕳  冒頭黒フレーム検出 → {t:.3f}s からスキップ")
        return t

    print(f"    ⏩  冒頭フェードイン対策 → {MIN_SKIP_SEC}s スキップ")
    return MIN_SKIP_SEC


# ─── FVシーン単体レンダリング ─────────────────────────────────
def render_fv_scene(
    clip_path: str,
    overlay_arr: np.ndarray,
    output_path: str,
) -> bool:
    """
    FVクリップ全体をletterbox+ズームでレンダリング。
    - 冒頭黒フレームを自動スキップ
    - テロップは末尾0.3秒前に消す（body S01テロップとの重なり防止）
    """
    overlay_png = Path(output_path).parent / f"_fv_ov_{Path(output_path).stem}.png"
    try:
        Image.fromarray(overlay_arr).save(str(overlay_png), "PNG")
        src_w, src_h = get_video_size(clip_path)
        vf = get_scale_crop_filter(src_w, src_h)

        # 冒頭黒フレームをスキップ
        skip_t = get_first_non_black_time(clip_path)
        fv_full_dur = get_duration(clip_path)
        effective_dur = fv_full_dur - skip_t

        # テロップ表示: 末尾0.3秒前に消す（次シーンのテロップと重ならないよう）
        telop_end = max(0.5, effective_dur - 0.3)

        cmd = [FFMPEG, "-y"]
        if skip_t > 0:
            cmd += ["-ss", f"{skip_t:.3f}"]
        cmd += ["-i", clip_path,
                "-loop", "1", "-i", str(overlay_png),
                "-filter_complex",
                f"[0:v]{vf}[base];[base][1:v]overlay=0:0:enable='between(t,0,{telop_end:.3f})'[out]",
                "-map", "[out]",
                "-map", "0:a",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-ar", "44100", "-ac", "2",
                "-af", LOUDNORM_TARGET,
                "-shortest",
                output_path]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    FFmpegエラー: {result.stderr[-400:]}")
        return result.returncode == 0
    finally:
        overlay_png.unlink(missing_ok=True)


# ─── ボディ連続レンダリング（音声途切れなし）─────────────────
def render_body_continuous(
    body_clip_path: str,
    body_scenes: list[dict],
    adj_ts: list[float],
    raw_ts: list[float],
    title_lines: list[str],
    annotation: str,
    output_path: str,
) -> bool:
    """
    body.movを1本丸ごとFFmpegで処理。音声は完全連続。

    テロップタイミング:
      表示開始 = adj_ts[i]  （発話のTIMING_OFFSET前出し）
      表示終了 = raw_ts[i+1]（次シーンの実際の発話開始 = 前シーンのテロップがちょうど消える）
      → 「これ」が言われている最中に「こっそり〜」テロップが出ない

    filter_complex構成:
      [0:v] scale+crop+pad [base]
      [base][1:v] overlay(static: 黒帯+タイトル) [s0]
      [s0][2:v] overlay(scene0: 注釈+テロップ) enable='between(t,adj0,raw1)' [s1]
      ...
    """
    tmpdir = Path(output_path).parent / "_body_tmp"
    tmpdir.mkdir(parents=True, exist_ok=True)

    try:
        src_w, src_h = get_video_size(body_clip_path)
        vf = get_scale_crop_filter(src_w, src_h)
        body_dur = get_duration(body_clip_path)

        # 静的オーバーレイ（黒帯+タイトル）
        static_arr = make_static_overlay(title_lines)
        static_png = str(tmpdir / "static.png")
        Image.fromarray(static_arr).save(static_png)

        # シーン別オーバーレイ（注釈+テロップ）
        scene_pngs: list[str] = []
        for i, scene in enumerate(body_scenes):
            arr = make_scene_overlay(annotation, scene["text"], scene.get("note", ""))
            p = str(tmpdir / f"scene_{i:02d}.png")
            Image.fromarray(arr).save(p)
            scene_pngs.append(p)
            t_show_start = adj_ts[i]
            t_show_end   = adj_ts[i + 1]  # 次テロップのadj開始まで（重なりゼロ）
            print(f"  ✅ S{i+2:02d} 表示[{t_show_start:.2f}→{t_show_end:.2f}s] 「{scene['text'][:15]}」")

        # FFmpegコマンド組み立て
        cmd = [FFMPEG, "-y"]
        cmd += ["-i", body_clip_path]
        cmd += ["-loop", "1", "-i", static_png]
        for p in scene_pngs:
            cmd += ["-loop", "1", "-i", p]

        # filter_complex
        n = len(body_scenes)
        filters: list[str] = []
        filters.append(f"[0:v]{vf}[base]")
        filters.append(f"[base][1:v]overlay=0:0[s0]")

        for i in range(n):
            t_start = adj_ts[i]        # 先出し開始（発話350ms前）
            t_end   = adj_ts[i + 1]   # 次テロップの先出し開始時刻まで → 重ならない
            in_idx  = i + 2
            s_in    = f"s{i}"
            s_out   = f"s{i+1}"
            enable  = f"between(t,{t_start:.3f},{t_end:.3f})"
            filters.append(f"[{s_in}][{in_idx}:v]overlay=0:0:enable='{enable}'[{s_out}]")

        fc    = ";".join(filters)
        final = f"s{n}"

        cmd += ["-filter_complex", fc]
        cmd += ["-map", f"[{final}]"]
        cmd += ["-map", "0:a"]
        cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "18"]
        cmd += ["-c:a", "aac", "-ar", "44100", "-ac", "2"]
        cmd += ["-af", LOUDNORM_TARGET]
        cmd += ["-t", f"{body_dur:.3f}"]
        cmd += [output_path]

        print(f"\n  🔗 {n}シーンを連続合成中（1本ストリーム）...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ body連続レンダリング失敗:\n{result.stderr[-600:]}")
            return False

        dur = get_duration(output_path)
        print(f"  ✅ 完成！ {Path(output_path).name} ({dur:.1f}秒 / {n}シーン・音声連続)")
        return True

    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Whisperタイミング取得 ────────────────────────────────────
def get_whisper_timestamps(clip_path: str) -> list[dict]:
    """Whisperで単語レベルタイムスタンプ取得（キャッシュあり）。"""
    WHISPER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = WHISPER_CACHE_DIR / f"{Path(clip_path).stem}_whisper.json"

    if cache_file.exists():
        print(f"    📁 Whisperキャッシュ使用: {cache_file.name}")
        return json.loads(cache_file.read_text())

    print(f"    🎙  Whisper書き起こし中: {Path(clip_path).name}...")
    try:
        import mlx_whisper
        result = mlx_whisper.transcribe(
            clip_path,
            path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
            language="ja",
            word_timestamps=True,
            verbose=False,
        )
        words = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                words.append({
                    "word":  w["word"].strip(),
                    "start": round(w["start"], 3),
                    "end":   round(w["end"],   3),
                })
        cache_file.write_text(json.dumps(words, ensure_ascii=False))
        return words
    except Exception as e:
        print(f"    ⚠️  Whisper失敗: {e}")
        return []


def normalize_for_match(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'[^\w\u3040-\u30FF\u4E00-\u9FFF]', '', text)
    return text.strip()


def find_scene_timestamp(words: list[dict], scene_text: str, search_after: float = 0.0) -> float | None:
    """シーンテキストに対応する発話開始タイムスタンプを探す。"""
    if not words:
        return None
    target = normalize_for_match(scene_text)
    if not target:
        return None

    filtered = [w for w in words if w["start"] >= search_after - 0.5]
    if not filtered:
        return None

    best_score = 0.0
    best_start = None
    n = len(target)
    min_words = max(1, n // 8)
    max_words = max(4, n // 2)

    for si in range(len(filtered)):
        if filtered[si]["start"] < search_after - 0.1:
            continue
        for ei in range(si + min_words, min(si + max_words + 1, len(filtered) + 1)):
            window = "".join(w["word"] for w in filtered[si:ei])
            score  = SequenceMatcher(None, target, normalize_for_match(window)).ratio()
            if score > best_score:
                best_score = score
                best_start = filtered[si]["start"]

    if best_score >= 0.45 and best_start is not None:
        return best_start
    return None


def compute_scene_timestamps(
    body_scenes: list[dict], words: list[dict], body_total_dur: float
) -> tuple[list[float], list[float]]:
    """
    各ボディシーンのタイムスタンプを返す。

    Returns:
      adj_ts: テロップ表示開始時刻（発話のTIMING_OFFSET前出し）
      raw_ts: 実際の発話開始時刻（テロップ終了の基準。次シーンのraw開始 = 前シーンのテロップ終了）

    between(adj_ts[i], raw_ts[i+1]) を使うことで:
      - テロップは発話の少し前から先出し
      - テロップ終了は次の発話が実際に始まる瞬間まで（早めに消えない）
    """
    adj_ts: list[float] = []
    raw_ts: list[float] = []
    search_after = 0.0

    for i, scene in enumerate(body_scenes):
        t = find_scene_timestamp(words, scene["text"], search_after)
        if t is not None:
            t_adj = max(0.0, t + TIMING_OFFSET)
            adj_ts.append(t_adj)
            raw_ts.append(t)
            search_after = t + 0.3
            print(f"    ✅ S{i+2:02d} [{t_adj:.2f}s → raw:{t:.2f}s] 「{scene['text'][:15]}」")
        else:
            fallback = search_after
            adj_ts.append(fallback)
            raw_ts.append(fallback)
            search_after = fallback + max(1.0, len(scene["text"]) / 6.0)
            print(f"    ⚠️  S{i+2:02d} [{fallback:.2f}s] 「{scene['text'][:15]}」 (フォールバック)")

    adj_ts.append(body_total_dur)
    raw_ts.append(body_total_dur)
    return adj_ts, raw_ts


# ─── CSV パース ────────────────────────────────────────────────
def parse_gungun_csv(csv_path: str) -> dict:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    annotation  = ""
    title_text  = "18歳がラストチャンス"
    fv_scenes:   dict[str, dict] = {}
    body_scenes: list[dict] = []
    mode = ""

    for row in rows:
        if not row:
            continue
        col0 = row[0].strip()

        if "■ 固定注釈" in col0:
            mode = "anno"
        elif "■ 台本" in col0:
            mode = "script"
        elif "■ 素材リスト" in col0:
            break
        elif col0.startswith("■"):
            mode = "memo" if "依頼メモ" in col0 else "other"
            continue

        if mode == "memo":
            full = " ".join(row)
            m = re.search(r'「([^」]+)」という文字', full)
            if m:
                title_text = m.group(1)

        elif mode == "anno":
            for ci in [1, 2]:
                candidate = row[ci].strip() if len(row) > ci else ""
                if candidate and not any(x in candidate for x in ["【", "注釈テキスト", "注釈内容", "表示位置"]):
                    if annotation:
                        annotation += "　" + candidate
                    else:
                        annotation = candidate
                    break

        elif mode == "script":
            if col0 == "" and len(row) > 1:
                no_str   = row[1].strip()
                text     = row[2].strip() if len(row) > 2 else ""
                clip_raw = row[3].strip() if len(row) > 3 else ""
                note     = row[4].strip() if len(row) > 4 else ""
            elif col0:
                no_str   = col0
                text     = row[1].strip() if len(row) > 1 else ""
                clip_raw = row[2].strip() if len(row) > 2 else ""
                note     = row[3].strip() if len(row) > 3 else ""
            else:
                continue

            if not no_str or "No" in no_str:
                continue
            if not text or text == "【ここに書く】":
                continue

            scene = {"no": no_str, "text": text, "clip": clip_raw, "note": note}
            if re.match(r'^\d+-\d+$', no_str):
                fv_scenes[no_str] = scene
            elif re.match(r'^\d+$', no_str) and int(no_str) >= 2:
                body_scenes.append(scene)

    return {
        "annotation":  annotation,
        "title":       title_text,
        "fv_scenes":   fv_scenes,
        "body_scenes": body_scenes,
    }


# ─── クリップ検索 ─────────────────────────────────────────────
def find_clip(ref: str, clips_dir: str) -> str | None:
    d = Path(clips_dir)
    direct = d / ref
    if direct.exists():
        return str(direct)
    stem = Path(ref).stem
    for ext in [".mov", ".mp4", ".MOV", ".MP4"]:
        for p in list(d.rglob(f"{stem}{ext}")):
            return str(p)
        for p in list(d.rglob(f"{ref}{ext}")):
            return str(p)
    return None


# ─── 1本の動画を生成 ──────────────────────────────────────────
def render_video(
    fv_key: str,
    parsed: dict,
    clips_dir: str,
    output_path: str,
    words: list[dict],
) -> bool:
    annotation  = parsed["annotation"]
    title_text  = parsed["title"]
    fv_scene    = parsed["fv_scenes"][fv_key]
    body_scenes = parsed["body_scenes"]
    title_lines = split_title(title_text)

    print(f"\n{'='*60}")
    print(f"  生成: {fv_key} → {Path(output_path).name}")
    print(f"  タイトル: 「{'／'.join(title_lines)}」")
    print(f"  FVテロップ: 「{fv_scene['text']}」")
    print(f"  ボディシーン: {len(body_scenes)}シーン")
    print(f"{'='*60}")

    tmpdir = Path(tempfile.mkdtemp(prefix="gungun_"))
    scene_files: list[str] = []

    try:
        # ── FVシーン ──────────────────────────────────────────
        fv_clip_path = find_clip(fv_scene["clip"], clips_dir)
        if not fv_clip_path:
            print(f"  ❌ FVクリップなし: {fv_scene['clip']}")
            return False

        fv_dur = get_duration(fv_clip_path)
        print(f"\n  [S01] FV: {fv_scene['text'][:30]} ({fv_dur:.2f}s)")

        fv_overlay = make_fv_overlay(title_lines, annotation, fv_scene["text"], fv_scene.get("note", ""))
        fv_out = str(tmpdir / "s01.mp4")
        ok = render_fv_scene(fv_clip_path, fv_overlay, fv_out)
        if not ok:
            print("  ❌ FVレンダリング失敗")
            return False
        scene_files.append(fv_out)
        print(f"  ✅ FV完了")

        # ── ボディシーン（連続音声方式）─────────────────────────
        if body_scenes:
            body_clip_path = find_clip(body_scenes[0]["clip"], clips_dir)
            if not body_clip_path:
                print(f"  ❌ bodyクリップなし: {body_scenes[0]['clip']}")
                return False

            body_total_dur = get_duration(body_clip_path)
            print(f"\n  body.mov: {body_total_dur:.2f}s / {len(body_scenes)}シーン")
            print(f"  📍 タイムスタンプ計算中...")
            adj_ts, raw_ts = compute_scene_timestamps(body_scenes, words, body_total_dur)

            body_out = str(tmpdir / "body.mp4")
            ok = render_body_continuous(
                body_clip_path, body_scenes, adj_ts, raw_ts,
                title_lines, annotation, body_out
            )
            if not ok:
                return False
            scene_files.append(body_out)

        # ── FV + ボディ結合 ────────────────────────────────────
        if not scene_files:
            print("  ❌ シーンなし")
            return False

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if len(scene_files) == 1:
            # FVのみ（bodyなし）
            import shutil
            shutil.copy(scene_files[0], output_path)
        else:
            concat_list = str(tmpdir / "concat.txt")
            with open(concat_list, "w") as f:
                for p in scene_files:
                    f.write(f"file '{p}'\n")

            result = ffmpeg_run(
                "-f", "concat", "-safe", "0",
                "-i", concat_list,
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-ar", "44100", "-ac", "2",
                output_path,
                check=False
            )
            if result.returncode != 0:
                print(f"  ❌ 結合失敗:\n{result.stderr[-400:]}")
                return False

        total_dur = get_duration(output_path)
        n_scenes = len(scene_files) + len(body_scenes) - 1
        print(f"\n  ✅ 完成！ {Path(output_path).name} ({total_dur:.1f}秒 / {n_scenes}シーン)")
        return True

    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── メイン ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ぐんぐん習慣 Letterbox動画生成 v3")
    parser.add_argument("--csv",          required=True)
    parser.add_argument("--clips",        required=True)
    parser.add_argument("--output-dir",   required=True)
    parser.add_argument("--fv",           default="all",
                        help="生成するFVパターン番号（例: 1）またはall")
    parser.add_argument("--whisper-json", default=None,
                        help="既存のWhisper JSONパス")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📄 CSV解析: {args.csv}")
    parsed = parse_gungun_csv(args.csv)
    print(f"  タイトル: 「{parsed['title']}」 → {split_title(parsed['title'])}")
    print(f"  注釈: 「{parsed['annotation'][:40]}...」")
    print(f"  FVパターン: {sorted(parsed['fv_scenes'].keys())}")
    print(f"  ボディシーン: {len(parsed['body_scenes'])}シーン")

    # Whisperタイムスタンプ
    words: list[dict] = []
    if args.whisper_json and Path(args.whisper_json).exists():
        words = json.loads(Path(args.whisper_json).read_text())
        print(f"  🎙  Whisper読み込み: {len(words)}単語")
    else:
        if parsed["body_scenes"]:
            body_clip = find_clip(parsed["body_scenes"][0]["clip"], args.clips)
            if body_clip:
                words = get_whisper_timestamps(body_clip)
        if not words:
            print("  ⚠️  Whisperタイムスタンプなし → 文字数按分でフォールバック")

    targets = sorted(parsed["fv_scenes"].keys()) if args.fv == "all" else [f"1-{args.fv}"]
    print(f"\n🚀 生成対象: {targets}")

    results = []
    for fv_key in targets:
        output_path = str(output_dir / f"gungun_{fv_key.replace('-', '_')}.mp4")
        ok = render_video(fv_key, parsed, args.clips, output_path, words)
        results.append((fv_key, output_path, ok))

    print(f"\n{'━'*60}")
    print(f"  完了: {sum(1 for _,_,ok in results if ok)}/{len(results)}本")
    for fv_key, path, ok in results:
        print(f"  {'✅' if ok else '❌'} {fv_key}: {Path(path).name}")
    print(f"{'━'*60}\n")


if __name__ == "__main__":
    main()
