#!/usr/bin/env python3
"""FV Mixer Studio — FV差し替え + BGM + 注釈 Webアプリ

起動: python3 video-ai/fv_studio/app.py
URL:  http://localhost:5050
"""

import json
import os
import subprocess
import tempfile
import textwrap
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# ─── Google Sheets Integration (optional) ─────────────────
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID", "1PxCyac4kuPivDo_uby48s-pHtlbv0Eme1bW7BYDUdKA"
)

try:
    import gspread as _gspread
    from google.oauth2.service_account import Credentials as _GSACreds
    _SHEETS_AVAILABLE = True
except ImportError:
    _SHEETS_AVAILABLE = False

def _get_sheets_client():
    """Service AccountでGoogleスプレッドシートクライアントを返す。未設定ならNone。"""
    if not _SHEETS_AVAILABLE:
        return None
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sa_json:
        # ローカル開発用: service_account.json ファイルを探す
        sa_file = Path(__file__).parent / "service_account.json"
        if sa_file.exists():
            sa_json = sa_file.read_text(encoding="utf-8")
        else:
            return None
    try:
        info = json.loads(sa_json)
        creds = _GSACreds.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        return _gspread.authorize(creds)
    except Exception as e:
        print(f"[Sheets] auth error: {e}")
        return None

def log_to_sheet(sheet_name: str, row: list):
    """スプレッドシートに1行追記。失敗してもアプリは止めない。"""
    try:
        gc = _get_sheets_client()
        if not gc:
            return
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
        ws.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[Sheets] log error ({sheet_name}): {e}")

def _bgm_label(vol: float) -> str:
    return {0.20: "小", 0.40: "中(推奨)", 0.65: "大"}.get(vol, f"{vol:.2f}")
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB

def _find_bin(name: str) -> str:
    candidates = [
        f"/opt/homebrew/bin/{name}",   # macOS (Homebrew)
        f"/usr/local/bin/{name}",       # macOS (legacy) / Linux
        f"/usr/bin/{name}",             # Linux (apt)
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return name  # fallback: PATH任せ

FFMPEG  = _find_bin("ffmpeg")
FFPROBE = _find_bin("ffprobe")

_FONT_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",               # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",                     # macOS sub
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",         # Linux (Debian/Ubuntu)
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",              # Linux alt
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",         # Linux alt2
]
FONT_PATH = next((f for f in _FONT_CANDIDATES if Path(f).exists()), "")

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXT = {".mp3", ".wav", ".aac", ".m4a", ".ogg"}

BGM_VOLUMES = {"small": 0.20, "medium": 0.40, "large": 0.65}

# Job tracking
jobs: dict[str, dict] = {}


# ─── Utility ───────────────────────────────────────────────────

def get_duration(path: str) -> float:
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


ANNOT_FONT_SIZE = 22
ANNOT_CHARS_LINE = 30


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """日本語フォントを読み込む。"""
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_annotation_png(text: str, width: int = 1080, height: int = 1920) -> str:
    """注釈テキストを透過PNGとして生成し、一時ファイルパスを返す。"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(ANNOT_FONT_SIZE)

    lines: list[str] = []
    for raw in text.strip().split("\n"):
        lines.extend(textwrap.wrap(raw, width=ANNOT_CHARS_LINE, break_long_words=True) or [raw])

    line_h = ANNOT_FONT_SIZE + 8
    for i, line in enumerate(lines):
        x, y = 20, 20 + i * line_h
        # 縁取り（黒）
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 200))
        # 本文（白）
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 220))

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, "PNG")
    tmp.close()
    return tmp.name


def get_session_dir(session_id: str) -> Path:
    d = UPLOAD_DIR / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─── FV Cut: Scene Detection (v5 Hybrid) ────────────────

def _get_scene_scores(video_path: str) -> list[tuple[float, float]]:
    """ffmpeg scene filterで全フレームのシーン変化スコアを取得。"""
    import re as _re
    tmpfile = tempfile.mktemp(suffix=".txt")
    subprocess.run(
        [FFMPEG, "-i", video_path,
         "-filter:v", "select='gte(scene,0)',metadata=print:file=" + tmpfile,
         "-vsync", "vfr", "-f", "null", "-"],
        capture_output=True, timeout=300,
    )
    frames = []
    current_pts = None
    for line in open(tmpfile).readlines():
        pts_match = _re.search(r'pts_time:([\d.]+)', line)
        score_match = _re.search(r'scene_score=([\d.]+)', line)
        if pts_match:
            current_pts = float(pts_match.group(1))
        if score_match and current_pts is not None:
            frames.append((current_pts, float(score_match.group(1))))
            current_pts = None
    os.unlink(tmpfile)
    return frames


def _find_peaks(frames: list, window: int = 10, min_prominence: float = 0.03) -> list[tuple[float, float]]:
    """局所ピーク検出: 周囲windowフレーム内で最大かつ突出度がmin_prominence以上。"""
    import numpy as _np
    scores = _np.array([f[1] for f in frames])
    n = len(scores)
    peaks = []
    for i in range(n):
        lo, hi = max(0, i - window), min(n, i + window + 1)
        local = scores[lo:hi]
        if scores[i] >= _np.max(local) and (scores[i] - _np.median(local)) >= min_prominence:
            peaks.append((frames[i][0], float(scores[i])))
    return peaks


def _identify_cuts(peaks: list, expected_cuts: int) -> list[float]:
    """ハイブリッド方式: ペアパターン + スマートスコア選択 (v5)

    ペア内スコア比でカットポイント選択を切り替える:
    - スコア比 > 3:1 → 高スコア側を選択（cut + noise パターン）
    - スコア比 <= 3:1 → 後方ピークを選択（true pair パターン）
    """
    if not peaks:
        return []

    pair_candidates = []
    for i in range(len(peaks) - 1):
        gap = peaks[i + 1][0] - peaks[i][0]
        if 0.3 <= gap <= 0.8:
            s1, s2 = peaks[i][1], peaks[i + 1][1]
            ratio = max(s1, s2) / max(min(s1, s2), 1e-9)
            cut_idx = (i if s1 > s2 else i + 1) if ratio > 3 else i + 1
            pair_candidates.append({
                "i": i, "j": i + 1,
                "cut_time": peaks[cut_idx][0],
                "pair_score": s1 + s2,
            })

    pair_candidates.sort(key=lambda x: -x["pair_score"])
    used = set()
    cuts = []
    for pc in pair_candidates:
        if pc["i"] not in used and pc["j"] not in used:
            cuts.append(pc)
            used.add(pc["i"])
            used.add(pc["j"])

    for i, (t, s) in enumerate(peaks):
        if i not in used:
            cuts.append({"cut_time": t, "pair_score": s})

    cuts.sort(key=lambda x: x["cut_time"])
    merged = []
    for c in cuts:
        if merged and abs(c["cut_time"] - merged[-1]["cut_time"]) < 1.0:
            if c["pair_score"] > merged[-1]["pair_score"]:
                merged[-1] = c
        else:
            merged.append(c)

    if len(merged) > expected_cuts:
        top = sorted(merged, key=lambda x: -x["pair_score"])[:expected_cuts]
        top.sort(key=lambda x: x["cut_time"])
        return [c["cut_time"] for c in top]
    return [c["cut_time"] for c in merged]


def detect_fv_clips(packed_path: str, expected_count: int = 0) -> list[dict]:
    """まとめ素材からFVクリップの境界を自動検出。

    v5 ハイブリッド方式:
      1. ffmpeg scene filter で全フレームスコアを取得
      2. 局所ピーク検出
      3. ペアパターン + スコア比でカットポイント選択
      4. expected_count > 0 なら指定数に絞り込み

    expected_count=0 の場合は自動検出（全ペアを採用）。
    """
    total_dur = get_duration(packed_path)

    # Step 1: scene scores
    frames = _get_scene_scores(packed_path)
    if not frames:
        return [{"index": 1, "start": 0.0, "end": round(total_dur, 3),
                 "duration": round(total_dur, 3)}]

    # Step 2: peak detection
    peaks = _find_peaks(frames, window=10, min_prominence=0.03)

    # Step 3: カットポイント特定
    if expected_count > 1:
        cut_points = _identify_cuts(peaks, expected_count - 1)
    else:
        # auto mode: 全ペア + 単独ピーク（スコア上位）から推定
        # とりあえず検出されたペア分をすべて使う
        cut_points = _identify_cuts(peaks, max(len(peaks) // 2, 1))

    # クリップ構築
    clips = []
    starts = [0.0] + cut_points
    ends = cut_points + [total_dur]
    for i, (s, e) in enumerate(zip(starts, ends)):
        if e - s > 0.1:
            clips.append({
                "index": len(clips) + 1,
                "start": round(s, 3),
                "end": round(e, 3),
                "duration": round(e - s, 3),
            })

    return clips


def generate_thumbnails(clips: list[dict], packed_path: str, session_dir: Path) -> list[dict]:
    """各クリップの先頭フレームをサムネイル画像として生成。clipsにthumbキーを追加して返す。"""
    thumb_dir = session_dir / "thumbnails"
    thumb_dir.mkdir(exist_ok=True)
    result = []
    for clip in clips:
        fname = f"thumb_{clip['index']:03d}.jpg"
        out = thumb_dir / fname
        subprocess.run(
            [FFMPEG, "-y", "-ss", str(clip["start"]),
             "-i", packed_path, "-vframes", "1", "-q:v", "4",
             "-vf", "scale=180:320", str(out)],
            capture_output=True,
        )
        result.append({**clip, "thumb": fname if out.exists() else None})
    return result


def run_cut_job(job_id: str, session_id: str, clips: list[dict], filename_prefix: str):
    """バックグラウンドでFVクリップを書き出す。"""
    _start = time.time()
    job = jobs[job_id]
    sess_dir = get_session_dir(session_id)
    output_dir = sess_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # まとめ素材を検索
    packed_path = None
    packed_dir = sess_dir / "packed"
    if packed_dir.exists():
        for f in sorted(packed_dir.iterdir()):
            if (f.is_file() or f.is_symlink()) and f.suffix.lower() in VIDEO_EXT:
                packed_path = f.resolve()
                break

    if not packed_path:
        job["status"] = "error"
        job["error"] = "まとめ素材が見つかりません"
        return

    total = len(clips)
    job["total"] = total
    results = []

    for clip in clips:
        i = clip["index"]
        output_name = f"{filename_prefix}_{i:02d}.mp4"
        output_path = output_dir / output_name
        job["current"] = i
        job["current_name"] = output_name

        cmd = [
            FFMPEG, "-y",
            "-ss", str(clip["start"]),
            "-i", str(packed_path),
            "-t", str(clip["duration"]),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            dur = get_duration(str(output_path))
            size_mb = output_path.stat().st_size / 1024 / 1024
            results.append({
                "name": output_name,
                "fv_name": f"clip_{i}",
                "duration": round(dur, 1),
                "size_mb": round(size_mb, 1),
            })
        except subprocess.CalledProcessError as e:
            print(f"  cut error clip{i}: {e.stderr[-300:]}")

    job["status"] = "done"
    job["results"] = results
    log_to_sheet("生成ログ", [
        time.strftime("%Y-%m-%d %H:%M"),
        "FVカット",
        total,
        "",
        "",
        round(time.time() - _start, 1),
        session_id[:8],
    ])


# ─── Audio Helpers ────────────────────────────────────────

def has_audio_stream(path: str) -> bool:
    """動画に音声ストリームがあるか確認。"""
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-select_streams", "a",
         "-show_entries", "stream=codec_type",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    return bool(r.stdout.strip())


def split_packed_video(packed_path: Path, fv_dir: Path, clip_dur: float) -> list[Path]:
    """まとめ素材を固定秒数で分割してfv_dirに保存。クリップパスリストを返す。"""
    fv_dir.mkdir(exist_ok=True)
    output_pattern = str(fv_dir / "clip_%03d.mp4")
    cmd = [
        FFMPEG, "-y",
        "-i", str(packed_path),
        "-c", "copy",
        "-f", "segment",
        "-segment_time", str(clip_dur),
        "-reset_timestamps", "1",
        output_pattern,
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return sorted(
        [f for f in fv_dir.iterdir()
         if (f.is_file() or f.is_symlink()) and f.suffix.lower() in VIDEO_EXT
         and not f.name.startswith(".")],
    )


# ─── Video Generation ─────────────────────────────────────────

def generate_video(
    base_path: Path,
    fv_path: Path,
    bgm_path: Path,
    output_path: Path,
    bgm_volume: float,
    base_dur: float,
    annotation: str = "",
) -> bool:
    """1本のFV + ベース + BGM (+ 注釈) → 完成動画。"""
    has_annotation = bool(annotation and annotation.strip())
    annotation_png = None

    # 注釈PNGを事前生成
    if has_annotation:
        annotation_png = make_annotation_png(annotation)

    # ── filter_complex 構築 ──
    # 入力: [0]=ベース動画, [1]=FV映像, [2]=BGM, [3]=注釈PNG(あれば)
    # Step 1: FVスケール（映像トラックのみ使用。FVの音声は完全に無視）
    fc = (
        "[1:v]setpts=PTS-STARTPTS,"
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2[fv];"
    )
    # Step 2: FV overlay
    vout = "vtmp" if has_annotation else "vout"
    fc += f"[0:v][fv]overlay=0:0:eof_action=pass[{vout}];"

    # Step 3: 注釈PNG overlay (あれば)
    if has_annotation:
        fc += "[vtmp][3:v]overlay=0:0:shortest=1[vout];"

    # Step 4: BGM trim + volume
    fc += (
        f"[2:a]atrim=0:{base_dur:.6f},asetpts=PTS-STARTPTS,"
        f"volume={bgm_volume}[bgm];"
    )
    # Step 5: Audio mix
    fc += "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]"

    inputs = [
        "-i", str(base_path),
        "-i", str(fv_path),
        "-i", str(bgm_path),
    ]
    if annotation_png:
        inputs += ["-loop", "1", "-i", annotation_png]

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ffmpeg error: {e.stderr[-800:]}")
        return False
    finally:
        if annotation_png:
            try:
                os.unlink(annotation_png)
            except OSError:
                pass


def run_generation_job(job_id: str, session_id: str, bgm_volume: float, annotation: str, filename_prefix: str = "FV"):
    """バックグラウンドで全FV動画を生成。"""
    _start = time.time()
    job = jobs[job_id]
    sess_dir = get_session_dir(session_id)
    output_dir = sess_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # 素材検出
    base_path = None
    bgm_path = None
    fv_paths = []

    for f in sorted(sess_dir.iterdir()):
        if (f.is_file() or f.is_symlink()) and not f.name.startswith("."):
            if f.suffix.lower() in VIDEO_EXT:
                base_path = f.resolve()
            elif f.suffix.lower() in AUDIO_EXT:
                bgm_path = f.resolve()

    fv_dir = sess_dir / "fv"
    if fv_dir.exists():
        fv_paths = sorted(
            [f.resolve() for f in fv_dir.iterdir()
             if (f.is_file() or f.is_symlink()) and f.suffix.lower() in VIDEO_EXT
             and not f.name.startswith(".")],
        )

    print(f"  [job] base={base_path}, bgm={bgm_path}, fv={len(fv_paths)}本")
    if not base_path or not bgm_path or not fv_paths:
        job["status"] = "error"
        job["error"] = f"素材が不足しています (base={base_path}, bgm={bgm_path}, fv={len(fv_paths)})"
        print(f"  [job] ERROR: {job['error']}")
        return

    base_dur = get_duration(str(base_path))
    total = len(fv_paths)
    job["total"] = total
    results = []

    for i, fv in enumerate(fv_paths):
        output_name = f"{filename_prefix}_{i + 1}.mp4"
        output_path = output_dir / output_name

        job["current"] = i + 1
        job["current_name"] = output_name

        ok = generate_video(
            base_path=base_path,
            fv_path=fv,
            bgm_path=bgm_path,
            output_path=output_path,
            bgm_volume=bgm_volume,
            base_dur=base_dur,
            annotation=annotation,
        )

        if ok:
            dur = get_duration(str(output_path))
            size_mb = output_path.stat().st_size / 1024 / 1024
            results.append({
                "name": output_name,
                "fv_name": fv.name,
                "duration": round(dur, 1),
                "size_mb": round(size_mb, 1),
            })

    job["status"] = "done"
    job["results"] = results
    log_to_sheet("生成ログ", [
        time.strftime("%Y-%m-%d %H:%M"),
        "FVオーバーレイ",
        total,
        _bgm_label(bgm_volume),
        (annotation[:50] if annotation else ""),
        round(time.time() - _start, 1),
        session_id[:8],
    ])


# ─── Concat Video Generation ──────────────────────────────

def generate_concat_video(
    fv_path: Path,
    body_path: Path,
    bgm_path: Path,
    output_path: Path,
    bgm_volume: float,
    annotation: str = "",
) -> bool:
    """FV + ボディを前後結合 + BGM ミックス。FV音声を保持。"""
    has_annotation = bool(annotation and annotation.strip())
    annotation_png = None

    if has_annotation:
        annotation_png = make_annotation_png(annotation)

    fv_has_audio = has_audio_stream(str(fv_path))
    fv_dur = get_duration(str(fv_path))
    body_dur = get_duration(str(body_path))
    total_dur = fv_dur + body_dur

    # FV・Bodyを同じ解像度にスケール
    fc = (
        "[0:v]setpts=PTS-STARTPTS,"
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2[fv_s];"
        "[1:v]setpts=PTS-STARTPTS,"
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2[body_s];"
    )

    if fv_has_audio:
        fc += "[fv_s][0:a][body_s][1:a]concat=n=2:v=1:a=1[vcat][acat];"
    else:
        # FV音声なし → サイレント音声を生成して結合
        fc += (
            f"anullsrc=channel_layout=stereo:sample_rate=44100[silent];"
            f"[silent]atrim=0:{fv_dur:.6f},asetpts=PTS-STARTPTS[fv_a];"
            "[fv_s][fv_a][body_s][1:a]concat=n=2:v=1:a=1[vcat][acat];"
        )

    if has_annotation:
        fc += "[vcat][3:v]overlay=0:0:shortest=1[vout];"
        video_map = "[vout]"
    else:
        video_map = "[vcat]"

    fc += (
        f"[2:a]atrim=0:{total_dur:.6f},asetpts=PTS-STARTPTS,"
        f"volume={bgm_volume}[bgm];"
        "[acat][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]"
    )

    inputs = [
        "-i", str(fv_path),
        "-i", str(body_path),
        "-i", str(bgm_path),
    ]
    if annotation_png:
        inputs += ["-loop", "1", "-i", annotation_png]

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", fc,
        "-map", video_map, "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ffmpeg error: {e.stderr[-800:]}")
        return False
    finally:
        if annotation_png:
            try:
                os.unlink(annotation_png)
            except OSError:
                pass


def run_concat_job(
    job_id: str,
    session_id: str,
    bgm_volume: float,
    annotation: str,
    filename_prefix: str,
):
    """バックグラウンドでFV結合モードの動画を生成（個別クリップのみ）。"""
    _start = time.time()
    job = jobs[job_id]
    sess_dir = get_session_dir(session_id)
    output_dir = sess_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # BGM検出
    bgm_path = None
    for f in sorted(sess_dir.iterdir()):
        if (f.is_file() or f.is_symlink()) and not f.name.startswith("."):
            if f.suffix.lower() in AUDIO_EXT:
                bgm_path = f.resolve()

    # ボディ動画検出
    body_path = None
    body_dir = sess_dir / "body"
    if body_dir.exists():
        for f in sorted(body_dir.iterdir()):
            if (f.is_file() or f.is_symlink()) and f.suffix.lower() in VIDEO_EXT:
                body_path = f.resolve()
                break

    fv_dir = sess_dir / "fv"

    # FVクリップ収集
    fv_paths = []
    if fv_dir.exists():
        fv_paths = sorted(
            [f.resolve() for f in fv_dir.iterdir()
             if (f.is_file() or f.is_symlink()) and f.suffix.lower() in VIDEO_EXT
             and not f.name.startswith(".")],
        )

    print(f"  [concat] body={body_path}, bgm={bgm_path}, fv={len(fv_paths)}本")
    if not body_path or not bgm_path or not fv_paths:
        job["status"] = "error"
        job["error"] = f"素材不足 (body={body_path}, bgm={bgm_path}, fv={len(fv_paths)})"
        return

    total = len(fv_paths)
    job["total"] = total
    results = []

    for i, fv in enumerate(fv_paths):
        output_name = f"{filename_prefix}_{i + 1}.mp4"
        output_path = output_dir / output_name
        job["current"] = i + 1
        job["current_name"] = output_name

        ok = generate_concat_video(
            fv_path=fv,
            body_path=body_path,
            bgm_path=bgm_path,
            output_path=output_path,
            bgm_volume=bgm_volume,
            annotation=annotation,
        )

        if ok:
            dur = get_duration(str(output_path))
            size_mb = output_path.stat().st_size / 1024 / 1024
            results.append({
                "name": output_name,
                "fv_name": fv.name,
                "duration": round(dur, 1),
                "size_mb": round(size_mb, 1),
            })

    job["status"] = "done"
    job["results"] = results
    log_to_sheet("生成ログ", [
        time.strftime("%Y-%m-%d %H:%M"),
        "FV結合",
        total,
        _bgm_label(bgm_volume),
        (annotation[:50] if annotation else ""),
        round(time.time() - _start, 1),
        session_id[:8],
    ])


# ─── Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.route("/analyze", methods=["POST"])
def analyze():
    """まとめ素材を解析してFVクリップ境界を返す。"""
    data = request.json
    session_id = data.get("session_id", "")
    sess_dir = get_session_dir(session_id)

    packed_path = None
    packed_dir = sess_dir / "packed"
    if packed_dir.exists():
        for f in sorted(packed_dir.iterdir()):
            if (f.is_file() or f.is_symlink()) and f.suffix.lower() in VIDEO_EXT:
                packed_path = f.resolve()
                break

    if not packed_path:
        return jsonify({"error": "まとめ素材が見つかりません"}), 400

    expected_count = data.get("expected_count", 0)
    clips = detect_fv_clips(str(packed_path), expected_count=int(expected_count))
    clips_with_thumbs = generate_thumbnails(clips, str(packed_path), sess_dir)
    return jsonify({"clips": clips_with_thumbs, "session_id": session_id})


@app.route("/thumbnail/<session_id>/<filename>")
def thumbnail(session_id, filename):
    """サムネイル画像を配信。"""
    fpath = UPLOAD_DIR / session_id / "thumbnails" / filename
    if not fpath.exists():
        return "not found", 404
    return send_file(str(fpath), mimetype="image/jpeg")


@app.route("/upload", methods=["POST"])
def upload():
    session_id = request.form.get("session_id", str(uuid.uuid4()))
    upload_type = request.form.get("type", "")  # "base", "fv", "bgm"
    sess_dir = get_session_dir(session_id)

    saved = []
    for f in request.files.getlist("files"):
        if not f.filename:
            continue
        if upload_type == "fv":
            fv_dir = sess_dir / "fv"
            fv_dir.mkdir(exist_ok=True)
            dest = fv_dir / f.filename
        elif upload_type == "body":
            body_dir = sess_dir / "body"
            body_dir.mkdir(exist_ok=True)
            dest = body_dir / f.filename
        elif upload_type == "packed":
            packed_dir = sess_dir / "packed"
            packed_dir.mkdir(exist_ok=True)
            dest = packed_dir / f.filename
        else:
            dest = sess_dir / f.filename
        f.save(str(dest))
        saved.append(f.filename)

    return jsonify({"session_id": session_id, "saved": saved})


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    session_id = data.get("session_id", "")
    bgm_vol_key = data.get("bgm_volume", "medium")
    bgm_volume = BGM_VOLUMES.get(bgm_vol_key, 0.40)
    annotation = data.get("annotation", "")
    filename_prefix = data.get("filename_prefix", "FV")
    mode = data.get("mode", "overlay")          # "overlay" or "concat"
    fv_input_type = data.get("fv_input_type", "individual")  # "individual" or "packed"
    clip_dur = float(data.get("clip_dur", 2.0))

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "running",
        "total": 0,
        "current": 0,
        "current_name": "",
        "results": [],
        "session_id": session_id,
    }

    if mode == "concat":
        t = threading.Thread(
            target=run_concat_job,
            args=(job_id, session_id, bgm_volume, annotation, filename_prefix),
            daemon=True,
        )
    elif mode == "cut":
        clips = data.get("clips", [])
        t = threading.Thread(
            target=run_cut_job,
            args=(job_id, session_id, clips, filename_prefix),
            daemon=True,
        )
    else:
        t = threading.Thread(
            target=run_generation_job,
            args=(job_id, session_id, bgm_volume, annotation, filename_prefix),
            daemon=True,
        )
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    return jsonify(job)


@app.route("/download/<job_id>/<filename>")
def download(job_id, filename):
    job = jobs.get(job_id)
    if not job:
        return "not found", 404
    sess_dir = get_session_dir(job["session_id"])
    filepath = sess_dir / "output" / filename
    if not filepath.exists():
        return "file not found", 404
    return send_file(str(filepath), as_attachment=True, download_name=filename)


@app.route("/clear/<session_id>", methods=["DELETE"])
def clear(session_id):
    import shutil
    sess_dir = UPLOAD_DIR / session_id
    if sess_dir.exists():
        shutil.rmtree(sess_dir)
    return jsonify({"ok": True})


@app.route("/files/<session_id>")
def list_files(session_id):
    """セッション内のアップロード済みファイル一覧。"""
    sess_dir = UPLOAD_DIR / session_id
    result = {"base": None, "bgm": None, "fv": [], "body": None, "packed": None}

    if not sess_dir.exists():
        return jsonify(result)

    for f in sorted(sess_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            if f.suffix.lower() in VIDEO_EXT:
                result["base"] = f.name
            elif f.suffix.lower() in AUDIO_EXT:
                result["bgm"] = f.name

    fv_dir = sess_dir / "fv"
    if fv_dir.exists():
        result["fv"] = sorted(
            [f.name for f in fv_dir.iterdir()
             if f.suffix.lower() in VIDEO_EXT and not f.name.startswith(".")],
        )

    body_dir = sess_dir / "body"
    if body_dir.exists():
        for f in sorted(body_dir.iterdir()):
            if f.suffix.lower() in VIDEO_EXT and not f.name.startswith("."):
                result["body"] = f.name
                break

    packed_dir = sess_dir / "packed"
    if packed_dir.exists():
        for f in sorted(packed_dir.iterdir()):
            if f.suffix.lower() in VIDEO_EXT and not f.name.startswith("."):
                result["packed"] = f.name
                break

    return jsonify(result)


# ─── Feedback System ──────────────────────────────────────────

FEEDBACK_FILE = Path(__file__).parent / "feedback.json"


def _load_feedback() -> list[dict]:
    if FEEDBACK_FILE.exists():
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    return []


def _save_feedback(data: list[dict]):
    FEEDBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@app.route("/feedback", methods=["POST"])
def submit_feedback():
    """フィードバック投稿。"""
    fb = request.json
    all_fb = _load_feedback()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "creator": fb.get("creator", ""),
        "job_id": fb.get("job_id", ""),
        "rating": fb.get("rating", ""),        # good / bad
        "category": fb.get("category", ""),     # bgm / fv_timing / annotation / other
        "comment": fb.get("comment", ""),
        "status": "pending",                    # pending → approved / rejected
    }
    all_fb.append(entry)
    _save_feedback(all_fb)
    log_to_sheet("フィードバック", [
        entry["timestamp"],
        entry["creator"],
        "OK" if entry["rating"] == "good" else "要改善",
        entry["category"],
        entry["comment"],
        entry["job_id"],
    ])
    return jsonify({"ok": True, "id": entry["id"]})


@app.route("/feedback", methods=["GET"])
def list_feedback():
    """フィードバック一覧（管理画面用）。"""
    return jsonify(_load_feedback())


@app.route("/feedback/<fb_id>/review", methods=["POST"])
def review_feedback(fb_id):
    """フィードバックの承認/却下（管理者用）。"""
    data = request.json
    new_status = data.get("status", "")  # approved / rejected
    note = data.get("note", "")

    all_fb = _load_feedback()
    for fb in all_fb:
        if fb["id"] == fb_id:
            fb["status"] = new_status
            fb["review_note"] = note
            fb["reviewed_at"] = time.strftime("%Y-%m-%d %H:%M")
            _save_feedback(all_fb)
            return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


@app.route("/setup-sheets", methods=["POST"])
def setup_sheets():
    """初回セットアップ: スプレッドシートにシートとヘッダーを作成する。"""
    if not _SHEETS_AVAILABLE:
        return jsonify({"error": "gspreadがインストールされていません"}), 400
    try:
        gc = _get_sheets_client()
        if not gc:
            return jsonify({"error": "Service Account未設定 (service_account.json または GOOGLE_SERVICE_ACCOUNT_JSON)"}), 400
        sh = gc.open_by_key(SPREADSHEET_ID)

        def _ensure_sheet(name, headers, static_rows=None):
            try:
                ws = sh.worksheet(name)
            except Exception:
                ws = sh.add_worksheet(title=name, rows=1000, cols=len(headers))
            if not ws.row_values(1):
                ws.insert_row(headers, 1)
                if static_rows:
                    for row in static_rows:
                        ws.append_row(row, value_input_option="USER_ENTERED")
            return ws

        _ensure_sheet(
            "生成ログ",
            ["日時", "モード", "FV本数", "BGM音量", "注釈(50字)", "処理時間(秒)", "セッションID"],
        )
        _ensure_sheet(
            "フィードバック",
            ["日時", "担当者名", "評価", "カテゴリ", "コメント", "ジョブID"],
        )
        _ensure_sheet(
            "スクリプト一覧",
            ["ツール名", "ファイルパス", "説明", "技術スタック"],
            static_rows=[
                ["KOSURIちゃん (メインサーバー)", "video-ai/fv_studio/app.py",
                 "Flask Webサーバー。動画生成・ジョブ管理・API全体", "Python / Flask / ffmpeg"],
                ["フロントエンドUI", "video-ai/fv_studio/templates/index.html",
                 "ブラウザ画面。3モード(FVオーバーレイ/FV結合/FVカット)", "HTML / CSS / Vanilla JS"],
                ["Cloud Runデプロイスクリプト", "video-ai/fv_studio/deploy.sh",
                 "GCP Cloud Runへの自動デプロイ", "gcloud / Cloud Build"],
                ["Dockerコンテナ定義", "video-ai/fv_studio/Dockerfile",
                 "本番環境コンテナ (python3.11-slim + ffmpeg + Noto CJK)", "Docker"],
                ["依存パッケージ", "video-ai/fv_studio/requirements.txt",
                 "flask / pillow / gunicorn / gspread / google-auth", "pip"],
            ],
        )
        return jsonify({"ok": True, "message": "シートのセットアップが完了しました"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n  FV Mixer Studio")
    print("  http://localhost:5050\n")
    app.run(host="0.0.0.0", port=5050, debug=True)
