#!/usr/bin/env python3
"""FV Mixer Studio — FV差し替え + BGM + 注釈 Webアプリ

起動: python3 video-ai/fv_studio/app.py
URL:  http://localhost:5050
"""

import io
import json
import os
import subprocess
import tempfile
import textwrap
import threading
import time
import uuid
import zipfile
from pathlib import Path

from typing import Optional

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

# ─── KOSURI 商品プロファイル・ローダー ─────────────────────
# `.claude/clients/{client}/{product}/kosuri-profile.yaml` を読み込み、
# FV自動生成のシステムプロンプト・画像プロンプト・履歴ログを差分注入する。
try:
    from profile_loader import (
        append_history as _append_kosuri_history,
        build_image_prompt_suffix as _build_kosuri_image_suffix,
        build_profile_injection as _build_kosuri_injection,
        filter_hook_patterns as _filter_kosuri_hooks,
        list_available_products as _list_kosuri_products,
        load_profile as _load_kosuri_profile,
    )
    _PROFILE_LOADER_AVAILABLE = True
except Exception as _e:
    print(f"[KOSURI profile_loader] unavailable — fallback to generic mode: {_e}")
    _PROFILE_LOADER_AVAILABLE = False

    def _list_kosuri_products():  # type: ignore[no-redef]
        return []

    def _load_kosuri_profile(*_a, **_k):  # type: ignore[no-redef]
        return None

    def _build_kosuri_injection(*_a, **_k):  # type: ignore[no-redef]
        return ""

    def _filter_kosuri_hooks(patterns, *_a, **_k):  # type: ignore[no-redef]
        return patterns

    def _build_kosuri_image_suffix(*_a, **_k):  # type: ignore[no-redef]
        return ""

    def _append_kosuri_history(*_a, **_k):  # type: ignore[no-redef]
        return

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

# ─── GCS Integration ───────────────────────────────────────
GCS_BUCKET = os.environ.get("GCS_BUCKET", "kosuri-studio-uploads")

try:
    from google.cloud import storage as _gcs_storage
    from google.oauth2.service_account import Credentials as _SACredsFull
    _GCS_AVAILABLE = True
except ImportError:
    _GCS_AVAILABLE = False

def _get_gcs_client():
    """Service AccountでGCSクライアントを返す。未設定ならNone。"""
    if not _GCS_AVAILABLE:
        return None
    try:
        sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        if not sa_json:
            sa_b64 = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "")
            if sa_b64:
                import base64
                sa_json = base64.b64decode(sa_b64).decode("utf-8")
        if sa_json:
            info = json.loads(sa_json)
            creds = _SACredsFull.from_service_account_info(info)
            return _gcs_storage.Client(credentials=creds, project=info.get("project_id"))
        return _gcs_storage.Client()  # ADC fallback
    except Exception as e:
        print(f"[GCS] client error: {e}")
        return None

def gcs_signed_url(filename: str, content_type: str, expires_minutes: int = 15):
    """署名付きアップロードURLを生成。失敗したらNone。"""
    client = _get_gcs_client()
    if not client:
        return None
    try:
        import datetime
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(filename)
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=expires_minutes),
            method="PUT",
            content_type=content_type,
        )
        return {"url": url, "gcs_path": f"gs://{GCS_BUCKET}/{filename}"}
    except Exception as e:
        print(f"[GCS] signed url error: {e}")
        return None

def gcs_download_to_local(gcs_path: str, local_path: Path) -> bool:
    """GCSからローカルにダウンロード。成功したらTrue。"""
    client = _get_gcs_client()
    if not client:
        return False
    try:
        blob_name = gcs_path.replace(f"gs://{GCS_BUCKET}/", "")
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(str(local_path))
        return True
    except Exception as e:
        print(f"[GCS] download error: {e}")
        return False

def gcs_delete(gcs_path: str):
    """GCSファイルを削除（コスト節約）。失敗しても無視。"""
    client = _get_gcs_client()
    if not client:
        return
    try:
        blob_name = gcs_path.replace(f"gs://{GCS_BUCKET}/", "")
        bucket = client.bucket(GCS_BUCKET)
        bucket.blob(blob_name).delete()
        print(f"[GCS] deleted: {gcs_path}")
    except Exception as e:
        print(f"[GCS] delete error: {e}")

def _get_sheets_client():
    """Service AccountでGoogleスプレッドシートクライアントを返す。未設定ならNone。"""
    if not _SHEETS_AVAILABLE:
        return None
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sa_json:
        # base64エンコード版にも対応
        sa_b64 = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "")
        if sa_b64:
            import base64
            sa_json = base64.b64decode(sa_b64).decode("utf-8")
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

# ─── フォント解決: 「BODY動画より弱くならない」極太優先 ─────
# W3/Regular は広告として細すぎる。Black/Boldを優先探索し、なければRegularにフォールバック。
_FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc",               # macOS 最重
    "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",               # macOS 極太
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",               # macOS 太
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",           # Docker (fonts-noto-cjk)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",            # Docker 太
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]
_FONT_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",               # macOS fallback
    "/System/Library/Fonts/Hiragino Sans GB.ttc",                     # macOS sub
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",         # Linux (Debian/Ubuntu)
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
FONT_PATH_BOLD = next((f for f in _FONT_CANDIDATES_BOLD if Path(f).exists()), "")
FONT_PATH = next((f for f in _FONT_CANDIDATES if Path(f).exists()), "") or FONT_PATH_BOLD
# Boldが無ければRegularで代用、Regularすら無ければBoldに戻る
if not FONT_PATH_BOLD:
    FONT_PATH_BOLD = FONT_PATH

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXT = {".mp3", ".wav", ".aac", ".m4a", ".ogg"}

BGM_VOLUMES = {"small": 0.20, "medium": 0.40, "large": 0.65}

# Job tracking
jobs: dict[str, dict] = {}


# ─── Cancel機構（全モード共通） ────────────────────────────────
class _JobCancelled(Exception):
    """ジョブがユーザーによりキャンセルされた時に投げる内部例外。"""
    pass


def _is_cancelled(job_id: Optional[str]) -> bool:
    if not job_id:
        return False
    return bool(jobs.get(job_id, {}).get("cancelled"))


def _check_cancel(job_id: Optional[str]) -> None:
    """cancelled なら _JobCancelled を raise。各 run_*_job の step 境界で呼ぶ。"""
    if _is_cancelled(job_id):
        raise _JobCancelled(f"job {job_id} cancelled by user")


def _run_cancellable(cmd, job_id: Optional[str] = None, timeout: Optional[float] = None,
                     poll_interval: float = 0.3, **kwargs):
    """subprocess.run 互換の cancel-aware wrapper。

    ジョブがcancelledになったら Popen.terminate() → _JobCancelled raise。
    capture_output / text / check は透過サポート。
    """
    import time as _time
    capture = kwargs.pop("capture_output", False)
    text_mode = kwargs.pop("text", False)
    check_mode = kwargs.pop("check", False)
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    proc = subprocess.Popen(cmd, **kwargs)
    start = _time.monotonic()
    try:
        while proc.poll() is None:
            if _is_cancelled(job_id):
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                raise _JobCancelled(f"job {job_id} cancelled during subprocess")
            if timeout and (_time.monotonic() - start) > timeout:
                proc.kill(); proc.wait()
                raise subprocess.TimeoutExpired(cmd, timeout)
            _time.sleep(poll_interval)
        stdout, stderr = proc.communicate()
    except _JobCancelled:
        raise
    except Exception:
        try:
            proc.kill(); proc.wait()
        except Exception:
            pass
        raise

    if text_mode:
        if isinstance(stdout, (bytes, bytearray)):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, (bytes, bytearray)):
            stderr = stderr.decode("utf-8", errors="replace")

    class _Result:
        pass
    r = _Result()
    r.returncode = proc.returncode
    r.stdout = stdout
    r.stderr = stderr
    if check_mode and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, stdout, stderr)
    return r


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


def _gemini_verify_cuts(clips: list[dict], packed_path: str, expected_count: int) -> list[dict]:
    """Gemini Flash でカット点を検証・修正する。

    各カット境界の前後フレームを画像化してGeminiに送り、
    「ここは本当に異なるFV動画の境界か」を判定。
    NOと判断されたカット点は隣接候補に差し替えるか除外する。
    expected_countに合わせて最終調整。
    """
    import base64, urllib.request

    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY_1")
        or ""
    )
    if not api_key:
        print("[Gemini] APIキー未設定 → スキップ")
        return clips

    try:
        # 各カット境界（クリップの末尾フレーム）を画像化
        with tempfile.TemporaryDirectory() as tmpdir:
            boundary_images = []  # [(clip_index, image_b64), ...]

            for clip in clips[:-1]:  # 最後のクリップ以外（末尾に境界がある）
                frame_time = clip["end"] - 0.1  # 境界直前フレーム
                img_path = Path(tmpdir) / f"boundary_{clip['index']:03d}.jpg"
                r = subprocess.run(
                    [FFMPEG, "-y", "-ss", str(max(0, frame_time)),
                     "-i", packed_path, "-vframes", "1",
                     "-q:v", "5", "-vf", "scale=320:-1", str(img_path)],
                    capture_output=True,
                )
                if img_path.exists():
                    b64 = base64.b64encode(img_path.read_bytes()).decode()
                    boundary_images.append((clip["index"], b64))

            if not boundary_images:
                return clips

            # Geminiにバッチで送信
            parts = [{
                "text": (
                    f"あなたは動画広告のFV（ファーストビュー）素材の専門家です。\n"
                    f"以下は「まとめ素材」動画の各カット候補点（境界直前フレーム）の画像です。\n"
                    f"FVは通常、全く異なる場面・商品・人物が登場する独立した短い動画です。\n\n"
                    f"各画像について、「次の場面との境界として妥当か」を判定してください。\n"
                    f"応答はJSON形式で: {{\"results\": [{{\"index\": 番号, \"valid\": true/false, \"reason\": \"一言\"}}]}}\n"
                    f"画像の枚数: {len(boundary_images)}枚\n"
                    f"期待するFV本数: {expected_count}本（境界数は{expected_count - 1}箇所）"
                )
            }]
            for idx, b64 in boundary_images:
                parts.append({"text": f"[境界候補 #{idx} — クリップ{idx}の末尾]"})
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64,
                    }
                })

            payload = json.dumps({
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
            }).encode()

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            res = urllib.request.urlopen(req, timeout=30)
            resp_data = json.loads(res.read())
            text = resp_data["candidates"][0]["content"]["parts"][0]["text"]

            # JSONを抽出
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0:
                gemini_result = json.loads(text[json_start:json_end])
                results = {r["index"]: r["valid"] for r in gemini_result.get("results", [])}

                # NOと判定されたクリップを隣接クリップと結合
                merged = []
                skip_next = False
                for i, clip in enumerate(clips):
                    if skip_next:
                        skip_next = False
                        continue
                    if results.get(clip["index"]) is False and i + 1 < len(clips):
                        # 隣と結合
                        next_clip = clips[i + 1]
                        merged.append({
                            "index": clip["index"],
                            "start": clip["start"],
                            "end": next_clip["end"],
                            "duration": round(next_clip["end"] - clip["start"], 3),
                        })
                        skip_next = True
                        print(f"[Gemini] 境界#{clip['index']} → 無効と判定、隣と結合")
                    else:
                        merged.append(clip)

                # インデックス振り直し
                for i, c in enumerate(merged):
                    c["index"] = i + 1

                print(f"[Gemini] 検証完了: {len(clips)}本 → {len(merged)}本")
                return merged

    except Exception as e:
        print(f"[Gemini] 検証エラー（スキップして続行）: {e}")

    return clips  # エラー時は元のclipsをそのまま返す


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

    try:
        for clip in clips:
            _check_cancel(job_id)
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
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                str(output_path),
            ]
            try:
                _run_cancellable(cmd, job_id=job_id, capture_output=True, text=True, check=True)
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
    except _JobCancelled:
        print(f"[Cut] job {job_id} cancelled by user")
        job["status"] = "cancelled"
        job["current_name"] = "キャンセルされました"
        job["results"] = results


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

    # Step 4: BGM trim + volume + fade-out（末尾2秒でフェード）
    fade_start = max(0, base_dur - 2.0)
    fc += (
        f"[2:a]atrim=0:{base_dur:.6f},asetpts=PTS-STARTPTS,"
        f"volume={bgm_volume},"
        f"afade=t=out:st={fade_start:.3f}:d=2[bgm];"
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
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
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

    try:
        for i, fv in enumerate(fv_paths):
            _check_cancel(job_id)
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
    except _JobCancelled:
        print(f"[Overlay] job {job_id} cancelled by user")
        job["status"] = "cancelled"
        job["current_name"] = "キャンセルされました"
        job["results"] = results


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

    fade_start2 = max(0, total_dur - 2.0)
    fc += (
        f"[2:a]atrim=0:{total_dur:.6f},asetpts=PTS-STARTPTS,"
        f"volume={bgm_volume},"
        f"afade=t=out:st={fade_start2:.3f}:d=2[bgm];"
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
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
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

    try:
        for i, fv in enumerate(fv_paths):
            _check_cancel(job_id)
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
    except _JobCancelled:
        print(f"[Concat] job {job_id} cancelled by user")
        job["status"] = "cancelled"
        job["current_name"] = "キャンセルされました"
        job["results"] = results


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

    expected_count = int(data.get("expected_count", 0))
    if expected_count < 1:
        return jsonify({"error": "FV本数は必須です（1以上を入力してください）"}), 400
    clips = detect_fv_clips(str(packed_path), expected_count=expected_count)
    # Gemini Flash で境界の妥当性を検証・修正
    clips = _gemini_verify_cuts(clips, str(packed_path), expected_count)
    clips_with_thumbs = generate_thumbnails(clips, str(packed_path), sess_dir)
    return jsonify({"clips": clips_with_thumbs, "session_id": session_id})


@app.route("/thumbnail/<session_id>/<filename>")
def thumbnail(session_id, filename):
    """サムネイル画像を配信。"""
    fpath = UPLOAD_DIR / session_id / "thumbnails" / filename
    if not fpath.exists():
        return "not found", 404
    return send_file(str(fpath), mimetype="image/jpeg")


@app.route("/presign-url", methods=["POST"])
def presign_url():
    """GCS署名付きアップロードURLを発行する。"""
    data = request.json or {}
    session_id = data.get("session_id", str(uuid.uuid4()))
    filename = data.get("filename", "upload.mp4")
    content_type = data.get("content_type", "video/mp4")
    upload_type = data.get("type", "base")

    # GCSパス: sessions/{session_id}/{type}/{filename}
    gcs_filename = f"sessions/{session_id}/{upload_type}/{filename}"
    result = gcs_signed_url(gcs_filename, content_type)
    if not result:
        # GCS未設定時はローカル直接アップロードにフォールバック
        return jsonify({
            "session_id": session_id,
            "upload_url": f"/upload-local/{session_id}/{upload_type}/{filename}",
            "gcs_path": f"local://{session_id}/{upload_type}/{filename}",
            "filename": filename,
            "local_mode": True,
        })
    return jsonify({
        "session_id": session_id,
        "upload_url": result["url"],
        "gcs_path": result["gcs_path"],
        "filename": filename,
    })

@app.route("/upload-local/<session_id>/<upload_type>/<filename>", methods=["PUT"])
def upload_local(session_id, upload_type, filename):
    """GCS未設定時のローカル直接アップロード用エンドポイント。"""
    sess_dir = get_session_dir(session_id)
    if upload_type in ("fv",):
        dest_dir = sess_dir / "fv"
    elif upload_type == "body":
        dest_dir = sess_dir / "body"
    elif upload_type == "packed":
        dest_dir = sess_dir / "packed"
    elif upload_type == "base":
        dest_dir = sess_dir / "base"
    else:
        dest_dir = sess_dir
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / filename
    dest.write_bytes(request.data)
    print(f"[LocalUpload] saved {dest} ({dest.stat().st_size//1024}KB)")
    return jsonify({"ok": True})


@app.route("/register-gcs", methods=["POST"])
def register_gcs():
    """GCSアップロード完了後、セッションにファイルを登録する。
    GCSからローカルにDLし、処理後にGCSを削除（コスト最小化）。
    """
    data = request.json or {}
    session_id = data.get("session_id", "")
    gcs_path = data.get("gcs_path", "")
    filename = data.get("filename", "upload.mp4")
    upload_type = data.get("type", "base")

    if not session_id or not gcs_path:
        return jsonify({"error": "session_id / gcs_path が必要"}), 400

    sess_dir = get_session_dir(session_id)

    if upload_type == "fv":
        dest_dir = sess_dir / "fv"
    elif upload_type == "body":
        dest_dir = sess_dir / "body"
    elif upload_type == "packed":
        dest_dir = sess_dir / "packed"
    else:
        dest_dir = sess_dir
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / filename

    # ローカルモード（GCS未設定時）: /upload-local で既にファイル保存済み
    if gcs_path.startswith("local://"):
        if not dest.exists():
            return jsonify({"error": "ローカルアップロードが見つかりません"}), 500
        ok = True
    else:
        ok = gcs_download_to_local(gcs_path, dest)
    if not ok:
        return jsonify({"error": "GCSからのダウンロードに失敗"}), 500

    # GCSから即削除（コスト節約）
    gcs_delete(gcs_path)

    return jsonify({"session_id": session_id, "saved": [filename]})

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
        "cancelled": False,
        "mode": mode,
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


@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    """ジョブをキャンセル。全モード共通（cut/generation/concat/fv-generate）。"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    if job.get("status") in ("done", "error", "cancelled"):
        return jsonify({"status": job.get("status"), "message": "already finished"})
    job["cancelled"] = True
    job["status"] = "cancelling"
    job["current_name"] = "キャンセル処理中..."
    return jsonify({"status": "cancelling", "job_id": job_id})


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


@app.route("/download_zip/<job_id>")
def download_zip(job_id):
    """ジョブの全結果ファイルをZIPで返す。"""
    job = jobs.get(job_id)
    if not job:
        return "not found", 404
    sess_dir = get_session_dir(job["session_id"])
    output_dir = sess_dir / "output"
    if not output_dir.exists():
        return "no output", 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(output_dir.iterdir()):
            if f.suffix.lower() in {".mp4", ".mov", ".webm"}:
                zf.write(f, f.name)
    buf.seek(0)
    zip_name = f"KOSURIchan_{job_id}.zip"
    return send_file(buf, as_attachment=True, download_name=zip_name, mimetype="application/zip")


@app.route("/preview/<job_id>/<filename>")
def preview(job_id, filename):
    """ブラウザ内プレビュー用（inline）。"""
    job = jobs.get(job_id)
    if not job:
        return "not found", 404
    sess_dir = get_session_dir(job["session_id"])
    filepath = sess_dir / "output" / filename
    if not filepath.exists():
        # fv_generated フォルダも確認
        filepath = sess_dir / "fv_generated" / filename
    if not filepath.exists():
        return "not found", 404
    return send_file(str(filepath), mimetype="video/mp4")


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
    rating_label = {"good": "OK", "no_issue": "問題なし", "bad": "要改善"}.get(entry["rating"], entry["rating"])
    log_to_sheet("ユーザーの声", [
        entry["timestamp"],
        "form",
        entry["creator"],
        rating_label,
        entry["category"],
        entry["comment"],
        entry["job_id"],
        "",
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
            "ユーザーの声",
            ["日時", "ソース", "担当者名", "評価", "カテゴリ", "コメント/メッセージ", "ジョブID", "BOT返答"],
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


# ═══════════════════════════════════════════════════════════════
# FV自動生成モード — ビジュアルフック × 表情設計 × Gemini画像生成
# ═══════════════════════════════════════════════════════════════

# ─── ビジュアルフック10パターン固定DB ─────────────────────────
VISUAL_HOOK_PATTERNS = [
    {
        "id": "V1", "name": "部位極限クローズアップ",
        "psychology": "身体の一部を極端に拡大→無意識に見てしまう（生存本能）",
        "has_face": False,
        "motion": "ultra_slow_zoom_in",
        "image_prompt_template": (
            "Extreme macro close-up of {body_part} skin texture, pores clearly visible, "
            "natural lighting, hyper-realistic, clean and clinical, 9:16 vertical, "
            "subject fills 80% of frame, no text, no people"
        ),
        "face_type": None,
    },
    {
        "id": "V2", "name": "不可視の可視化",
        "psychology": "見えないものが見えた恐怖と好奇心で止まる",
        "has_face": False,
        "motion": "static_then_zoom",
        "image_prompt_template": (
            "Scientific microscope visualization of {invisible_subject}, blue-purple bioluminescent lighting, "
            "CGI render, beautiful yet unsettling, 9:16 vertical, fills entire frame, no text"
        ),
        "face_type": None,
    },
    {
        "id": "V3", "name": "完璧な美・理想形",
        "psychology": "こうなりたいという憧れで吸い寄せられる（繁殖本能）",
        "has_face": True,
        "motion": "slow_pan_left_right",
        "image_prompt_template": (
            "Beautiful {gender} person, arms raised in liberation, radiant clean skin, "
            "white background, natural authentic smile, face fills 60% of frame, "
            "9:16 vertical, UGC style, not overly commercial"
        ),
        "face_type": "F2",
    },
    {
        "id": "V4", "name": "違和感・文脈破壊",
        "psychology": "これ何？と脳が処理しようとして止まる",
        "has_face": True,
        "motion": "static_no_motion",
        "image_prompt_template": (
            "Elderly woman in her 60s with white hair, surprisingly youthful clean {body_part}, "
            "stylish modern outfit, looking directly at camera, strong contrast, "
            "face fills 65% of frame, 9:16 vertical, natural light"
        ),
        "face_type": "F4",
    },
    {
        "id": "V5", "name": "Before状態の直視",
        "psychology": "自分の悩みを見ると止まる（自己関連付け）",
        "has_face": True,
        "motion": "handheld_shake_to_static",
        "image_prompt_template": (
            "{gender} person showing discomfort about {problem_area}, "
            "realistic imperfect skin, redness, unfiltered, "
            "eyebrows furrowed, mouth slightly open in discomfort, "
            "face fills 60% of frame, 9:16 vertical, authentic SNS style"
        ),
        "face_type": "F6",
    },
    {
        "id": "V6", "name": "感情表情・本能反応",
        "psychology": "人の顔には0.05秒で脳が反応する（社会本能）",
        "has_face": True,
        "motion": "slow_zoom_to_face",
        "image_prompt_template": (
            "Close-up of {gender} person's face reacting to noticing {problem}, "
            "eyebrows raised slightly upward in center making八character shape, "
            "eyes glistening, lips barely parted, genuine micro-expression, "
            "face fills 70% of frame, 9:16 vertical, cinematic lighting"
        ),
        "face_type": "F1",
    },
    {
        "id": "V7", "name": "スケール・質感の衝撃",
        "psychology": "これ何のアップ？という好奇心で止まる",
        "has_face": False,
        "motion": "pan_bottom_to_top",
        "image_prompt_template": (
            "Extreme close-up of {product_texture} texture melting onto skin, "
            "macro photography, white and skin tone colors, "
            "hyper-realistic material quality, fills entire frame, 9:16 vertical, no text"
        ),
        "face_type": None,
    },
    {
        "id": "V8", "name": "本能的不快→好奇心",
        "psychology": "見たくない＋でも見てしまう（嫌悪と好奇の共存）",
        "has_face": True,
        "motion": "slight_rotation",
        "image_prompt_template": (
            "{gender} person with exaggerated disgusted expression, eyes squeezed shut, "
            "deep wrinkle between brows, nose scrunched, mouth in extreme frown, "
            "meme-level reaction face, authentic and funny, "
            "face fills 75% of frame, 9:16 vertical, bright even lighting"
        ),
        "face_type": "F10",
    },
    {
        "id": "V9", "name": "対比衝撃（Before/After同時）",
        "psychology": "映像だけで差の大きさが伝わる→見ずにいられない",
        "has_face": True,
        "motion": "dual_zoom_to_center",
        "image_prompt_template": (
            "Split screen image, left side: {gender} person with sad suppressed expression "
            "eyebrows in八shape eyes slightly wet, dark muted tone; "
            "right side: same person beaming with liberation, arms open, bright warm tone; "
            "sharp white dividing line in center, 9:16 vertical"
        ),
        "face_type": "F5_F2",
    },
    {
        "id": "V10", "name": "権威の視覚的証明",
        "psychology": "専門家が見ているという信頼感で止まる",
        "has_face": True,
        "motion": "slow_zoom_to_face",
        "image_prompt_template": (
            "Professional in white coat looking directly and confidently into camera, "
            "clinic background, strong direct gaze, chin slightly down, "
            "subtle confident smile, authoritative but approachable, "
            "face fills 70% of frame, 9:16 vertical, clean white lighting"
        ),
        "face_type": "F9",
    },
    # ─── DPro勝ち広告学習 V11-V14 (2026-04-19 追加) ──────────────
    # 上位6本の勝ち広告を分析: split-screen/医療画像/開発者ポートレート/商品単品
    {
        "id": "V11", "name": "Split-Screen対比衝撃",
        "psychology": "画面2分割で左右の違いを探す本能が働き目が離せなくなる（勝ち広告6本中4本採用）",
        "has_face": True,
        "motion": "dual_zoom_to_center",
        "image_prompt_template": (
            "Vertical 9:16 split-screen composition with sharp white vertical divider line down the center, "
            "left half shows {gender} person with {problem} visible discomfort expression realistic skin texture, "
            "right half shows the same person beaming liberated natural smile, "
            "stark lighting contrast between halves, cinematic documentary style, "
            "no text no logos, faces clearly visible on both sides"
        ),
        "face_type": "F5_F2",
    },
    {
        "id": "V12", "name": "医療科学ビジュアライゼーション",
        "psychology": "MRI・レントゲン・顕微鏡画像の権威+黒背景の恐怖感が思考を止める（ヒザこし守護神cost+15M型）",
        "has_face": False,
        "motion": "static_then_zoom",
        "image_prompt_template": (
            "Vertical 9:16 medical scientific visualization of {body_part}, "
            "x-ray or MRI style imaging on pure black background, "
            "detailed anatomical rendering with subtle millimeter scale markers on side, "
            "white and cyan accent colors, cinematic clinical atmosphere, "
            "highly detailed medical grade CGI, no text no labels no logos"
        ),
        "face_type": None,
    },
    {
        "id": "V13", "name": "専門家・開発者ポートレート",
        "psychology": "白衣/研究室の専門家が直接視線で信頼と権威を即発動（LADDER NMN / オレリー型）",
        "has_face": True,
        "motion": "talking_head_subtle",
        "image_prompt_template": (
            "Vertical 9:16 portrait of Japanese expert specialist in white lab coat or professional attire, "
            "clean research laboratory or clinic interior background with blurred medical equipment, "
            "direct confident eye contact to camera, slight concerned professional expression about {problem}, "
            "handheld documentary camera feel, natural window light, "
            "upper body composition fills 70% of frame, no text no logos no brand names"
        ),
        "face_type": "F9",
    },
    {
        "id": "V14", "name": "商品単品ヒーローショット",
        "psychology": "手が商品を持つ所有感・触感・実生活シーンの使用イメージ（毎日骨ケアMBP型）",
        "has_face": False,
        "motion": "zoom_punch_hold",
        "image_prompt_template": (
            "Vertical 9:16 hero product shot, a woman's hand gracefully holding a sleek {category} product bottle, "
            "clean minimalist background in white or soft pastel color, natural soft daylight casting gentle shadow, "
            "product label should be blank without any text or logo, "
            "premium e-commerce photography style, product fills 50% of frame centered, "
            "hand and forearm visible showing intimate ownership feel"
        ),
        "face_type": None,
    },
]

# ─── 表情ルールDB ──────────────────────────────────────────────
FACE_EXPRESSION_RULES = {
    "F1": "eyebrows raised slightly in center forming八shape, eyes glistening with awareness, nose slightly wrinkled, lips barely parted — the exact moment of noticing something unpleasant",
    "F2": "eyes naturally crinkled at corners (Duchenne smile), cheeks lifted, mouth open showing teeth, chin slightly up, genuine liberation — not posed",
    "F4": "completely neutral expression, direct unwavering eye contact with camera, lips closed, no readable emotion — ambiguity that demands interpretation",
    "F5": "eyebrows in八shape pulling inward, eyes slightly wet but not crying, jaw tight, holding back emotion — the verge without release",
    "F6": "eyes closed, deep furrow between brows, mouth slightly open, nose wrinkled — genuine discomfort, not theatrical",
    "F9": "chin slightly tucked, eyes steady and direct at camera, micro-smile at corner of lips, relaxed jaw — quiet authority and certainty",
    "F10": "eyes squeezed shut, nose deeply wrinkled, mouth pulled hard into downward curve, entire face engaged — exaggerated meme-level disgust that reads as authentic",
    "F5_F2": "left person: eyebrows in八shape, eyes slightly wet, mouth pressed together; right person: wide open smile, eyes crinkled, head tilted back",
}

# ─── カメラモーション定義（ffmpegコマンド） ────────────────────
def _build_motion_filter(motion_type: str, duration: float, w: int = 1080, h: int = 1920) -> str:
    """カメラモーションタイプからffmpeg zoompanフィルター文字列を生成。"""
    d = int(duration * 30)  # 30fps換算フレーム数
    motion_map = {
        "ultra_slow_zoom_in": (
            f"zoompan=z='min(zoom+0.0015,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={d}:s={w}x{h}:fps=30"
        ),
        "static_then_zoom": (
            f"zoompan=z='if(lte(on,{d//2}),1.0,min(zoom+0.008,1.5))'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps=30"
        ),
        "slow_pan_left_right": (
            f"zoompan=z=1.1:x='if(lte(on,{d}), iw*0.05*(on/{d}), iw*0.05)'"
            f":y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps=30"
        ),
        "static_no_motion": (
            f"zoompan=z=1.0:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={d}:s={w}x{h}:fps=30"
        ),
        "handheld_shake_to_static": (
            f"zoompan=z=1.05:x='iw/2-(iw/zoom/2)+if(lte(on,{d//3}),sin(on)*8,0)'"
            f":y='ih/2-(ih/zoom/2)+if(lte(on,{d//3}),cos(on*1.3)*8,0)':d={d}:s={w}x{h}:fps=30"
        ),
        "slow_zoom_to_face": (
            f"zoompan=z='min(zoom+0.003,1.25)':x='iw/2-(iw/zoom/2)':y='ih*0.3-(ih/zoom*0.3)'"
            f":d={d}:s={w}x{h}:fps=30"
        ),
        "pan_bottom_to_top": (
            f"zoompan=z=1.1:x='iw/2-(iw/zoom/2)'"
            f":y='ih*0.9-(ih/zoom/2) - (ih*0.4*(on/{d}))':d={d}:s={w}x{h}:fps=30"
        ),
        "slight_rotation": (
            # rotateフィルターを別途使うのでzoompanは静止
            f"zoompan=z=1.05:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps=30"
        ),
        "dual_zoom_to_center": (
            f"zoompan=z='min(zoom+0.002,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={d}:s={w}x{h}:fps=30"
        ),
        # ─── DPro学習モーション (M10-M13) ─────────────────────────
        # M10: flash_cut_zoom — RKL系Quick Cut (0.3s静止→瞬間1.4倍→0.5s静止)
        # 前半 d/3 は静止、中盤 d/3 で急激ズーム、後半 d/3 は保持
        "flash_cut_zoom": (
            f"zoompan=z='if(lte(on,{d//3}),1.0,if(lte(on,{d*2//3}),"
            f"min(1.0 + 0.4*((on-{d//3})/{d//3}),1.4),1.4))'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps=30"
        ),
        # M11: talking_head_subtle — gungun系 ほぼ静止+呼吸ズーム (1.0-1.03の微動)
        "talking_head_subtle": (
            f"zoompan=z='1.0 + 0.03*sin(on/30)':x='iw/2-(iw/zoom/2)'"
            f":y='ih/2-(ih/zoom/2) + 4*sin(on/25)':d={d}:s={w}x{h}:fps=30"
        ),
        # M12: macro_asmr_glide — proust系 超スロー斜めパン+微ズーム (メタファー訴求向け)
        "macro_asmr_glide": (
            f"zoompan=z='1.05 + 0.03*(on/{d})'"
            f":x='iw/2-(iw/zoom/2) + iw*0.05*(on/{d})'"
            f":y='ih/2-(ih/zoom/2) + ih*0.03*(on/{d})'"
            f":d={d}:s={w}x{h}:fps=30"
        ),
        # M13: native_feed_scroll — onmyskin系 SNS擬態 (最初下に180px、上へスライド→静止)
        # 前半 d/4 でスクロール、後半は静止に見せる
        "native_feed_scroll": (
            f"zoompan=z=1.02"
            f":x='iw/2-(iw/zoom/2)'"
            f":y='ih/2-(ih/zoom/2) + if(lte(on,{d//4}),180*(1-on/{d//4}),0)'"
            f":d={d}:s={w}x{h}:fps=30"
        ),
        # ─── 補助モーション ───────────────────────────────────────
        # zoom_punch_hold — ガッとズーム+静止 (RKLカット点模倣・パンチライン用)
        "zoom_punch_hold": (
            f"zoompan=z='if(lte(on,{d//6}),1.0 + 0.3*(on/{d//6}),1.3)'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps=30"
        ),
        # snap_focus_reveal — 全体からズームアウト+上下揺れ (V9対比アクセント)
        "snap_focus_reveal": (
            f"zoompan=z='1.3 - 0.2*(on/{d})'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2) + 6*sin(on/8)'"
            f":d={d}:s={w}x{h}:fps=30"
        ),
    }
    return motion_map.get(motion_type, motion_map["static_no_motion"])


def _normalize_to_9_16(image_path: Path, target_w: int = 1080, target_h: int = 1920) -> bool:
    """生成画像を強制的に9:16 (1080x1920) に正規化する。

    Gemini 2.5 Flash Image は出力サイズが可変で、1:1 や 16:9 など他アスペクト比で
    返してくることがある。縦長9:16の広告FV以外は絶対NGなので、PIL でcenter-cropして
    1080x1920にresizeする。アスペクト比バグの再発を根本遮断する保険処理。
    """
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        src_w, src_h = img.size
        target_ratio = target_w / target_h  # 0.5625
        src_ratio = src_w / src_h

        if abs(src_ratio - target_ratio) > 0.01:
            # アスペクト比が違う → center crop
            if src_ratio > target_ratio:
                # 横長すぎ → 左右をcropして縦長に
                new_w = int(src_h * target_ratio)
                left = (src_w - new_w) // 2
                img = img.crop((left, 0, left + new_w, src_h))
            else:
                # 縦長すぎ → 上下をcrop
                new_h = int(src_w / target_ratio)
                top = (src_h - new_h) // 2
                img = img.crop((0, top, src_w, top + new_h))

        # 1080x1920に統一リサイズ
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        img.save(str(image_path), quality=92)
        return True
    except Exception as e:
        print(f"[Normalize 9:16] error: {e}")
        return False


def _gemini_generate_image(prompt: str, api_key: str, out_path: Path) -> bool:
    """Gemini Imagen APIで画像生成。成功したら9:16に強制正規化してTrue。

    重要: Gemini 2.5 Flash Image は aspectRatio を直接指定できないモデル。
    プロンプトで誘導 + 生成後 _normalize_to_9_16 で強制crop+resize の二段構えで
    縦横比バグをゼロにする。
    """
    import base64, urllib.request
    # プロンプトの先頭と末尾に9:16要件を強く入れる（モデルがスキップしないよう繰り返す）
    nine_sixteen_prefix = (
        "STRICT VERTICAL 9:16 PORTRAIT ORIENTATION (1080x1920 pixels, tall not wide). "
    )
    nine_sixteen_suffix = (
        " | REQUIRED: 9:16 vertical portrait format only, NOT square, NOT landscape, "
        "subject framed tall like smartphone screen."
    )
    full_prompt = nine_sixteen_prefix + prompt + nine_sixteen_suffix
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=60)
        data = json.loads(res.read())
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                img_bytes = base64.b64decode(part["inlineData"]["data"])
                out_path.write_bytes(img_bytes)
                # 強制的に9:16に正規化（Geminiが正方形や横長を返しても安全）
                _normalize_to_9_16(out_path)
                return True
        return False
    except Exception as e:
        print(f"[Gemini Image] error: {e}")
        return False


def _analyze_video_for_fv(video_path: str, api_key: str) -> dict:
    """Geminiで動画冒頭を解析してFV情報を返す。"""
    import base64, urllib.request
    try:
        # 冒頭6秒を4fps でフレーム抽出（0.25秒精度・タイミング精度向上）
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                [FFMPEG, "-y", "-i", video_path, "-vf", "fps=4,scale=360:-1",
                 "-t", "6", f"{tmpdir}/frame_%04d.jpg", "-loglevel", "quiet"],
                capture_output=True,
            )
            frames = sorted(Path(tmpdir).glob("*.jpg"))[:24]
            if not frames:
                return {}

            parts = [{"text": (
                "この動画広告の冒頭フレームを時系列で解析してください。\n"
                "各フレームには [X.XX秒] のタイムスタンプが付いています（0.25秒精度）。\n"
                "\n"
                "【最重要: テロップの切替タイミングと画面位置】\n"
                "フレーム間でテロップ(画面内に映る文字)が切り替わる瞬間を0.25秒精度で捉え、\n"
                "caption_segments を順に記録してください。各セグメントに以下を含める:\n"
                "  - start, end (秒、小数点2桁)\n"
                "  - text (そのセグメントで画面に出ている実テロップ文字列)\n"
                "  - screen_position: テロップの画面内縦位置\n"
                "    ('top'=上部20%以内 / 'upper_mid'=上部40%付近 / 'center'=中央付近 /\n"
                "     'lower_mid'=下部60%付近 / 'bottom'=下部80%以下)\n"
                "  - importance: 'primary'(主フック) / 'secondary'(補足) / 'kicker'(オチ・CTA)\n"
                "例: 0〜2.3秒に『遺伝型ワキガ10年以上放置してる人』が center/primary、\n"
                "2.3〜4.8秒に『絶対見て』が center/kicker のように。\n"
                "画面に全く文字が出ていない区間はセグメントに含めません。\n"
                "\n"
                "以下のJSON形式で返してください:\n"
                "{\n"
                "  \"fv_end_sec\": FV終点の秒数,\n"
                "  \"captions\": [\"後方互換用・主要テロップ文字列のリスト\"],\n"
                "  \"caption_segments\": [\n"
                "    {\"start\": 開始秒, \"end\": 終了秒, \"text\": \"実テロップ\",\n"
                "     \"screen_position\": \"top|upper_mid|center|lower_mid|bottom\",\n"
                "     \"importance\": \"primary|secondary|kicker\"}\n"
                "  ],\n"
                "  \"target\": \"ターゲット層\",\n"
                "  \"product\": \"商品・サービス名\",\n"
                "  \"category\": \"カテゴリ（健康/美容/食品等）\",\n"
                "  \"body_part\": \"関連する体の部位\",\n"
                "  \"problem\": \"悩み・問題\",\n"
                "  \"gender\": \"登場人物の性別\",\n"
                "  \"main_colors\": [\"メインカラー3色\"]\n"
                "}"
            )}]
            for i, f in enumerate(frames):
                # fps=4 なので 0.25秒刻み
                parts.append({"text": f"[{i*0.25:.2f}秒]"})
                parts.append({"inline_data": {"mime_type": "image/jpeg",
                              "data": base64.b64encode(f.read_bytes()).decode()}})

            payload = json.dumps({
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": 0.1},
            }).encode()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            res = urllib.request.urlopen(req, timeout=30)
            text = json.loads(res.read())["candidates"][0]["content"]["parts"][0]["text"]
            s = text.find("{"); e = text.rfind("}") + 1
            return json.loads(text[s:e]) if s >= 0 else {}
    except Exception as ex:
        print(f"[Video Analysis] error: {ex}")
        return {}


def _design_10_patterns(video_info: dict, user_prompt: str, api_key: str,
                        profile: Optional[dict] = None) -> list[dict]:
    """Geminiがビジュアルフック法則 × 動画情報 × プロンプト × 商品プロファイルから10パターンを設計。

    profile を渡すと VISUAL_HOOK_PATTERNS から avoid されたフックを除外し、
    システムプロンプトにペルソナ・NG表現・優先フック・勝ちコピーを差し込む。
    """
    import urllib.request

    # プロファイルで使用禁止フックを除外した後のリストで LLM に提示
    available_patterns = _filter_kosuri_hooks(VISUAL_HOOK_PATTERNS, profile)
    if not available_patterns:
        available_patterns = VISUAL_HOOK_PATTERNS

    patterns_desc = "\n".join([
        f"{p['id']}: {p['name']} — {p['psychology']}"
        for p in available_patterns
    ])
    face_rules = "\n".join([f"{k}: {v}" for k, v in FACE_EXPRESSION_RULES.items()])

    profile_block = _build_kosuri_injection(profile) if profile else ""

    system_prompt = f"""あなたは動画広告のFV（ファーストビュー）映像の専門クリエイティブディレクターです。

【動画情報】
ターゲット: {video_info.get('target', '不明')}
商品: {video_info.get('product', '不明')}
テロップ: {', '.join(video_info.get('captions', []))}
悩み: {video_info.get('problem', '不明')}
体の部位: {video_info.get('body_part', 'skin')}
性別: {video_info.get('gender', 'female')}
{profile_block}

【ユーザーの意図】
{user_prompt}

【使用可能なビジュアルフック法則（この中から選べ。他は存在しないものと扱え）】
{patterns_desc}

【表情ルール（顔ありパターンに必ず適用）】
{face_rules}

【画像生成の絶対ルール】
- 縦型9:16、被写体が画面の60%以上
- 広告っぽい完璧さを避ける（SNS投稿風・ドキュメンタリー感）
- 人物は1人か0人
- 画像内にテキスト・ロゴ・UI要素・ウォーターマークを一切入れない（最重要）
- コントラストを強く
- 「瞬間」を切り取る（状態でなくモーメント）
- 偽物感のある化学式・英字ブランド名・架空UIを描写しない

【重要な制約（v4ユーザー指示: 変数は1つだけ）】
- テロップの文字列は一切「新規生成するな」。元動画から抽出される文字列をそのまま使う。
- テロップの「見せ方」もあなたは決めない（システム側で全10パターン完全統一する）
- モーションもあなたは決めない（システム側で全10パターン同じモーションに固定する）
- **あなたの唯一の仕事は「画像の中身」を10パターン変えること**。それが唯一の検証変数。

以下のJSON形式で最大10パターンを返してください。各パターンは「使用可能なビジュアルフック」を1つずつ使うこと。
テロップ・モーション・見せ方は一切返さず、画像方針のみに集中すること:
{{
  "patterns": [
    {{
      "hook_id": "V1",
      "concept": "このパターンのコンセプト1行（画像が何を見せるか）",
      "why_stop": "なぜ視聴者の目が止まるか（心理的根拠）",
      "image_prompt": "Gemini画像生成用の英語プロンプト。NO text, NO logos, NO Japanese characters, NO watermarks を必ず含める。SNS投稿風・ドキュメンタリー感を推奨、広告っぽい完璧さは避ける。インパクト強く",
      "face_expression": "使う表情ルールのID（顔なしならnull）"
    }}
  ]
}}"""

    try:
        payload = json.dumps({
            "contents": [{"parts": [{"text": system_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3000},
        }).encode()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=30)
        text = json.loads(res.read())["candidates"][0]["content"]["parts"][0]["text"]
        s = text.find("{"); e = text.rfind("}") + 1
        result = json.loads(text[s:e])
        return result.get("patterns", [])
    except Exception as ex:
        print(f"[Pattern Design] error: {ex}")
        return []


# ─── テロップ描画: 極太フォント + セーフエリア準拠 ─────
# Meta Reels / TikTok の両方でUIに被らないY配置:
#   上14%はハンドル・広告ラベル、下22%はCTAボタンで隠れる → 中央約64%が安全圏
_CAPTION_Y_MAP = {
    "note_top":    0.08,   # 広告ラベルより下、だがhookより上
    "hook_top":    0.20,   # セーフエリア内の上寄り（SNS共通で安全）
    "mid":         0.45,   # 真ん中
    "kick_bottom": 0.72,   # CTAボタンより上の安全下部
    "footer":      0.85,   # TikTok投稿者名の上、ギリギリ見える
}
_CAPTION_SIZE_MAP = {"xl": 140, "l": 108, "m": 80, "s": 52}


def _draw_caption_layers_on_canvas(canvas, caption_layers: list[dict]) -> None:
    """指定キャンバス(RGBA)にテロップレイヤーを描画する共通ロジック。

    caption_layers の各要素:
      {text, placement, size, style, emphasis_words}
    """
    from PIL import Image, ImageDraw, ImageFont
    w, h = canvas.size
    scale = w / 1080.0
    draw = ImageDraw.Draw(canvas, "RGBA")

    for layer in caption_layers or []:
        text = (layer.get("text") or "").strip()
        if not text:
            continue
        size_key = layer.get("size", "m")
        font_size = int(_CAPTION_SIZE_MAP.get(size_key, 80) * scale)
        placement = layer.get("placement", "kick_bottom")
        y_ratio = _CAPTION_Y_MAP.get(placement, 0.72)
        style = layer.get("style", "bold")
        emphasis_words = [w_ for w_ in (layer.get("emphasis_words") or []) if w_]

        # フォント: 極太優先、なければRegularにフォールバック
        font_path = FONT_PATH_BOLD or FONT_PATH
        try:
            font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        lines = text.split("\n")

        # Auto-fit v2: 長いテキストは縮小、短いテキストは拡大して画面幅を最大活用
        # ユーザー要望: 「絶対見て」のような短い文字は1つ目テロップと同サイズではなく、より大きく
        MAX_WIDTH_RATIO = 0.88   # 画面幅の88%以内に収める（上限）
        TARGET_MIN_RATIO = 0.75  # 画面幅の75%以上は使う（下限・短文を大きく）
        max_width_px = int(w * MAX_WIDTH_RATIO)
        target_min_px = int(w * TARGET_MIN_RATIO)
        min_font_size = 36
        max_font_size = int(280 * scale)  # xxl扱いの上限（1080px幅なら280px）

        def _measure_lines(_font):
            _md = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
            _mx = 0
            for _ln in lines:
                _bb = _md.textbbox((0, 0), _ln, font=_font)
                _mx = max(_mx, _bb[2] - _bb[0])
            return _mx

        if font_path:
            # Step1: 超過時は縮小
            for _iter in range(25):
                max_line_w = _measure_lines(font)
                if max_line_w <= max_width_px or font_size <= min_font_size:
                    break
                font_size = max(min_font_size, int(font_size * 0.93))
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except Exception:
                    break
            # Step2: 不足時は拡大（短いテキストを大きく）
            for _iter in range(20):
                max_line_w = _measure_lines(font)
                if max_line_w >= target_min_px or font_size >= max_font_size:
                    break
                new_size = min(max_font_size, int(font_size * 1.1))
                if new_size <= font_size:
                    break
                try:
                    new_font = ImageFont.truetype(font_path, new_size)
                    new_w = _measure_lines(new_font)
                    if new_w > max_width_px:
                        break  # 次のステップで超過する → ここで止める
                    font_size = new_size
                    font = new_font
                except Exception:
                    break

        line_h = int(font_size * 1.25)
        total_h = line_h * len(lines)
        y_start = int(h * y_ratio) - total_h // 2

        # スタイル別パラメータ
        if style == "highlight":
            fill = (30, 20, 0, 255)          # 濃い黒字
            bg = (255, 230, 0, 245)          # 黄色看板
            border_mode = None
        elif style == "double_stroke":
            fill = (255, 255, 255, 255)      # 白字
            bg = None
            border_mode = "double"
        else:  # "bold" 標準
            fill = (255, 255, 255, 255)
            bg = None
            border_mode = "thick"

        inner_stroke = max(6, font_size // 12)   # 黒縁厚（xl=140なら~11px）
        outer_stroke = max(3, font_size // 28)   # 外側白縁

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = (w - tw) // 2
            y = y_start + i * line_h

            # 背景ハイライト（highlight スタイル）
            if bg is not None:
                pad_x = int(font_size * 0.30)
                pad_y = int(font_size * 0.18)
                draw.rectangle(
                    [x - pad_x, y - pad_y, x + tw + pad_x, y + th + pad_y],
                    fill=bg,
                )

            # 縁取り描画
            if border_mode == "double":
                # 外側白縁（極太）
                ring = inner_stroke + outer_stroke
                for dx in range(-ring, ring + 1, 2):
                    for dy in range(-ring, ring + 1, 2):
                        draw.text((x + dx, y + dy), line, font=font, fill=(255, 255, 255, 255))
                # 内側黒縁
                for dx in range(-inner_stroke, inner_stroke + 1, 2):
                    for dy in range(-inner_stroke, inner_stroke + 1, 2):
                        draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
            elif border_mode == "thick":
                for dx in range(-inner_stroke, inner_stroke + 1, 2):
                    for dy in range(-inner_stroke, inner_stroke + 1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))

            # 本体描画
            draw.text((x, y), line, font=font, fill=fill)

            # emphasis_words: 元テロップ内の単語を黄色で上書き（テキスト新規生成ではなく強調のみ）
            for ew in emphasis_words:
                if ew not in line:
                    continue
                idx = line.find(ew)
                if idx < 0:
                    continue
                pre = line[:idx]
                pre_bbox = draw.textbbox((0, 0), pre, font=font)
                pre_w = pre_bbox[2] - pre_bbox[0]
                ex = x + pre_w
                if border_mode in ("thick", "double"):
                    # 強調語の縁も厚めに引き直し
                    for dx in range(-inner_stroke, inner_stroke + 1, 2):
                        for dy in range(-inner_stroke, inner_stroke + 1, 2):
                            draw.text((ex + dx, y + dy), ew, font=font, fill=(0, 0, 0, 255))
                draw.text((ex, y), ew, font=font, fill=(255, 230, 0, 255))


def _render_caption_layers_png(caption_layers: list[dict], w: int = 1080, h: int = 1920,
                                out_path: Optional[Path] = None) -> Optional[Path]:
    """透明背景にテロップだけ描画したPNGを生成して返す。

    ffmpeg overlayで動画に時間指定で重ねるための素材として使う。
    動画の zoompan とは独立しているので、画像が動いてもテロップはピクセル固定される。
    """
    if not caption_layers:
        return None
    from PIL import Image
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))  # 完全透明背景
    _draw_caption_layers_on_canvas(canvas, caption_layers)

    if out_path is None:
        import tempfile, uuid as _uuid
        out_path = Path(tempfile.gettempdir()) / f"kosuri_cap_{_uuid.uuid4().hex[:10]}.png"
    canvas.save(str(out_path))
    return out_path


def _burn_captions_to_image(image_path: Path, caption_layers: list[dict]) -> Path:
    """[レガシー互換] 画像そのものにテロップを焼き込む。

    新しい実装では overlay 方式を推奨（_render_caption_layers_png + ffmpeg overlay）。
    この関数は旧呼び出し経路のために保持している。
    """
    from PIL import Image
    img = Image.open(image_path).convert("RGBA")
    _draw_caption_layers_on_canvas(img, caption_layers)
    out_img = img.convert("RGB")
    tmp_path = image_path.parent / (image_path.stem + "_captioned.jpg")
    out_img.save(str(tmp_path), quality=92)
    return tmp_path


def _detect_caption_placement_from_segments(base_segments: list[dict]) -> str:
    """元動画のcaption_segmentsからテロップの支配的な縦位置を検出し、
    _CAPTION_Y_MAP のキーに変換して返す。

    screen_position の多数決で決定:
      top / upper_mid → "hook_top"
      center          → "mid"
      lower_mid / bottom → "kick_bottom"
    """
    # Gemini が返す screen_position → _CAPTION_Y_MAP キーのマッピング
    POS_TO_PLACEMENT = {
        "top":       "hook_top",
        "upper_mid": "hook_top",
        "center":    "mid",
        "lower_mid": "kick_bottom",
        "bottom":    "kick_bottom",
    }
    votes: dict[str, int] = {}
    for seg in base_segments:
        pos = seg.get("screen_position", "")
        placement = POS_TO_PLACEMENT.get(pos)
        if placement:
            votes[placement] = votes.get(placement, 0) + 1

    if not votes:
        return "hook_top"  # フォールバック

    dominant = max(votes, key=lambda k: votes[k])
    print(f"[Caption Placement] body解析結果: {votes} → '{dominant}' に統一")
    return dominant


def _build_caption_timeline_from_pattern(
    base_segments: list[dict],
    pattern: dict,
    fv_duration: float,
    profile: Optional[dict] = None,
) -> list[dict]:
    """元動画のテロップタイムライン × 統一見せ方 → 時間軸レイヤー配列（v5）。

    v4での決定（ユーザー指示「変数は画像の中身だけ」）:
    - 全10パターンで見せ方を完全に統一する（placement/size/style全て固定）
    - pattern引数は無視する（LLMからのcaption系指定は受け取らない）
    - 全セグメントを auto-detected placement / `xl` / `double_stroke` で統一
    - 短い文字（≤6文字）は render側の auto-fit で自動拡大される

    v5追加:
    - bodyのcaption_segmentsのscreen_positionを多数決で検出し、
      テロップY位置を自動決定（top/upper_mid→hook_top, center→mid,
      lower_mid/bottom→kick_bottom）

    これにより、検証時に差分要因が「画像の中身」のみに絞れる実験設計になる。

    戻り値: [{"start", "end", "layers": [layer_dict]}]
    """
    timeline: list[dict] = []
    if not base_segments:
        return timeline

    # body動画のテロップ位置から自動検出（全パターン・全セグメント共通）
    FIXED_PLACEMENT = _detect_caption_placement_from_segments(base_segments)
    FIXED_SIZE = "xl"
    FIXED_STYLE = "double_stroke"

    for seg in base_segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", fv_duration))
        if start >= fv_duration:
            continue
        end = min(end, fv_duration)

        layer = {
            "text": text,
            "placement": FIXED_PLACEMENT,
            "size": FIXED_SIZE,
            "style": FIXED_STYLE,
            "emphasis_words": [],  # 強調語も統一廃止（差別化要因から除外）
        }
        timeline.append({
            "start": start,
            "end": end,
            "layers": [layer],
        })

    return timeline


def _build_caption_layers_from_pattern(
    base_captions: list[str],
    pattern: dict,
    profile: Optional[dict] = None,
) -> list[dict]:
    """[レガシー互換] 単一フレーム向けのレイヤー配列（時間軸なし）。

    注釈自動追加は廃止。タイムライン対応は _build_caption_timeline_from_pattern を使う。
    """
    layers: list[dict] = []
    if base_captions:
        main_text = base_captions[0]
        emphasis_words = [w_ for w_ in (pattern.get("emphasis_words") or []) if w_ and w_ in main_text]
        layers.append({
            "text": main_text,
            "placement": pattern.get("caption_placement", "hook_top"),
            "size": pattern.get("caption_size", "xl"),
            "style": pattern.get("caption_style", "double_stroke"),
            "emphasis_words": emphasis_words,
        })
    if len(base_captions) > 1 and base_captions[1]:
        kick_text = base_captions[1]
        kick_emph = [w_ for w_ in (pattern.get("emphasis_words") or []) if w_ and w_ in kick_text]
        layers.append({
            "text": kick_text,
            "placement": pattern.get("caption_kick_placement", "kick_bottom"),
            "size": pattern.get("caption_kick_size", "l"),
            "style": pattern.get("caption_kick_style", "bold"),
            "emphasis_words": kick_emph,
        })
    return layers


def _build_fv_video(image_path: Path, audio_path: Path,
                    caption_timeline: list[dict],
                    fv_duration: float, motion_type: str,
                    output_path: Path) -> bool:
    """画像にzoompanで動きを付与、テロップは透明PNGをoverlay時間指定で固定配置。

    caption_timeline = [{"start": float, "end": float, "layers": [layer, ...]}]
    各セグメントは透明背景PNGに焼いて、ffmpeg overlayで `enable='between(t, start, end)'`
    によって指定時刻のみ表示する。これで画像が動いてもテロップはピクセル固定される。
    """
    try:
        w, h = 1080, 1920
        motion_filter = _build_motion_filter(motion_type, fv_duration, w, h)

        # 1) 各セグメントのテロップを透明背景PNGに焼き出し
        import tempfile as _tempfile
        tmp_caption_dir = Path(_tempfile.mkdtemp(prefix="kosuri_captions_"))
        segment_pngs: list[tuple[float, float, Path]] = []
        for idx, seg in enumerate(caption_timeline or []):
            layers = seg.get("layers") or []
            if not layers:
                continue
            png_path = tmp_caption_dir / f"seg_{idx:02d}.png"
            out = _render_caption_layers_png(layers, w, h, png_path)
            if out and out.exists():
                segment_pngs.append((float(seg["start"]), float(seg["end"]), out))

        # 2) ffmpeg filter_complex を構築
        # [0:v]zoompan=...[bg]
        # [bg][1:v]overlay=0:0:enable='between(t,s1,e1)'[v1]
        # [v1][2:v]overlay=0:0:enable='between(t,s2,e2)'[v]
        if segment_pngs:
            filter_parts = [f"[0:v]{motion_filter}[bg]"]
            current_label = "bg"
            for i, (start, end, _png) in enumerate(segment_pngs):
                input_idx = i + 1  # 画像が0、PNG群が1..N、音声は最後
                next_label = f"v{i}" if i < len(segment_pngs) - 1 else "vout"
                filter_parts.append(
                    f"[{current_label}][{input_idx}:v]overlay=0:0:enable='between(t\\,{start:.3f}\\,{end:.3f})'[{next_label}]"
                )
                current_label = next_label
            filter_complex = ";".join(filter_parts)
            map_video = f"[{current_label}]"
            audio_input_idx = len(segment_pngs) + 1
        else:
            # テロップ無しの場合は画像に motion だけ
            filter_complex = f"[0:v]{motion_filter}[vout]"
            map_video = "[vout]"
            audio_input_idx = 1

        # 3) ffmpegコマンド組み立て
        cmd = [FFMPEG, "-y", "-loop", "1", "-i", str(image_path)]
        for _, _, png in segment_pngs:
            cmd.extend(["-i", str(png)])
        cmd.extend([
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", f"{audio_input_idx}:a",
            "-t", str(fv_duration),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path),
        ])

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FV Build] ffmpeg error: {r.stderr[-800:]}")

        # 一時PNGディレクトリは残しておく（ジョブ終了時にセッションごと削除される）
        return r.returncode == 0
    except Exception as ex:
        print(f"[FV Build] error: {ex}")
        import traceback
        traceback.print_exc()
        return False


# 旧シグネチャ(caption_layers)の fallback を_deprecatedルートで提供
def _build_fv_video_legacy(image_path: Path, audio_path: Path,
                            caption_layers: list[dict],
                            fv_duration: float, motion_type: str,
                            output_path: Path) -> bool:
    """[レガシー] テロップ焼き込み→zoompan方式（画像と一緒に動くため非推奨）。"""
    try:
        w, h = 1080, 1920
        motion_filter = _build_motion_filter(motion_type, fv_duration, w, h)
        src_image = image_path
        if caption_layers:
            src_image = _burn_captions_to_image(image_path, caption_layers)

        cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-i", str(src_image),
            "-i", str(audio_path),
            "-vf", motion_filter,
            "-t", str(fv_duration),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FV Build] ffmpeg error: {r.stderr[-500:]}")
        return r.returncode == 0
    except Exception as ex:
        print(f"[FV Build] error: {ex}")
        return False


def run_fv_generate_job(job_id: str, session_id: str, video_path: str,
                        fv_end_sec: float, user_prompt: str,
                        product_key: str = ""):
    """バックグラウンドでFV生成ジョブを実行。

    product_key='yomite_rkl' のように渡すと、該当商品プロファイルを
    `.claude/clients/{client}/{product}/kosuri-profile.yaml` から読み込み、
    ペルソナ・NG表現・優先フック・画像トーンを反映する。
    未指定・読込失敗時は従来の汎用モードで動作する。
    """
    job = jobs[job_id]
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_1", "")
    sess_dir = get_session_dir(session_id)
    fv_gen_dir = sess_dir / "fv_generated"
    fv_gen_dir.mkdir(exist_ok=True)

    # 商品プロファイル読み込み（失敗してもジョブは続行）
    profile = _load_kosuri_profile(product_key) if product_key else None
    if product_key and not profile:
        print(f"[FV Gen] profile not found for product_key={product_key} — generic mode")
    elif profile:
        print(f"[FV Gen] profile loaded: {profile.get('product_name', product_key)}")
    job["product_key"] = product_key
    job["product_name"] = (profile or {}).get("product_name", "")

    try:
        _check_cancel(job_id)
        # Step1: 動画解析
        job["current_name"] = "動画を解析中..."
        video_info = _analyze_video_for_fv(video_path, api_key)
        if not video_info:
            job["status"] = "error"; job["error"] = "動画解析失敗"
            return
        # FV終点を上書き可能
        video_info["fv_end_sec"] = fv_end_sec
        print(f"[FV Gen] 解析完了: {video_info}")

        _check_cancel(job_id)
        # Step2: 10パターン設計（プロファイル注入）
        job["current_name"] = "10パターンをAIが設計中..."
        patterns = _design_10_patterns(video_info, user_prompt, api_key, profile=profile)
        if not patterns:
            job["status"] = "error"; job["error"] = "パターン設計失敗"
            return
        job["total"] = len(patterns)

        # Step3: FV音声を切り出し（元動画から）
        audio_path = fv_gen_dir / "fv_audio.aac"
        subprocess.run(
            [FFMPEG, "-y", "-i", video_path, "-t", str(fv_end_sec),
             "-vn", "-c:a", "aac", "-b:a", "192k", str(audio_path)],
            capture_output=True,
        )

        # Step4: ボディ部分を切り出し（1080x1920 @ 30fps に正規化、xfade継ぎ目合わせのため）
        body_path = fv_gen_dir / "body.mp4"
        subprocess.run(
            [FFMPEG, "-y", "-i", video_path,
             "-ss", str(fv_end_sec),
             "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                    "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
             "-r", "30",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
             "-c:a", "aac", "-b:a", "192k",
             "-pix_fmt", "yuv420p",
             str(body_path)],
            capture_output=True,
        )

        results = []
        captions = video_info.get("captions", [])

        # ─── モーション選択（v4: 10パターン全部同じモーションに固定） ───
        # ユーザー指示: 「変数は1つ = 画像の中身だけ」
        # モーションが10パターンで変わると検証時のノイズになるので、ジョブ単位で1つに固定。
        # 優先順位:
        #   1. プロファイルの primary_motion（新フィールド）
        #   2. プロファイルの motion_priority[0]（既存、先頭のみ使用）
        #   3. 汎用最強フォールバック: slow_zoom_to_face（どんな画像でも自然に動く）
        FIXED_MOTION = "slow_zoom_to_face"
        if profile:
            hooks_cfg = profile.get("hooks", {}) or {}
            FIXED_MOTION = (
                hooks_cfg.get("primary_motion")
                or (hooks_cfg.get("motion_priority") or [None])[0]
                or "slow_zoom_to_face"
            )
        print(f"[FV Gen] 固定モーション: {FIXED_MOTION} (全10パターンで使用)")

        for i, pattern in enumerate(patterns):
            _check_cancel(job_id)  # 各パターン生成前にキャンセル確認
            hook_id = pattern.get("hook_id", f"V{i+1}")
            job["current"] = i + 1
            job["current_name"] = f"{hook_id} — 画像生成中..."

            # Step5: 画像生成
            img_path = fv_gen_dir / f"img_{i+1:02d}.jpg"
            img_prompt = pattern.get("image_prompt", "")

            # 表情ルールを追加
            face_id = pattern.get("face_expression")
            if face_id and face_id in FACE_EXPRESSION_RULES:
                img_prompt += f" Expression detail: {FACE_EXPRESSION_RULES[face_id]}"

            # 商品プロファイルのサフィックス（年齢・世界観）で上書き優先
            profile_img_suffix = _build_kosuri_image_suffix(profile) if profile else ""
            if profile_img_suffix:
                img_prompt += ", " + profile_img_suffix
            elif "Asian" not in img_prompt and "Japanese" not in img_prompt:
                # プロファイル未指定時のフォールバック: 日本向け広告の既定
                img_prompt += (
                    " Japanese or Asian woman model, "
                    "natural Japanese beauty standard, "
                    "suitable for Japanese beauty/health advertisement"
                )

            # 【重要】no-text強制語彙: 画像内に文字/ロゴ/UI要素/透かしを入れさせない
            # Imagenは日本語を正しく描画できないため、テロップはffmpeg焼き込みで別途付与する
            img_prompt += (
                ", plain documentary photo with ABSOLUTELY NO text, NO writing, "
                "NO Japanese characters, NO kanji, NO hiragana, NO katakana, "
                "NO logos, NO watermarks, NO brand names, NO product labels with text, "
                "NO UI elements, NO social media icons, NO like buttons, NO share buttons, "
                "NO subtitles, NO captions, NO signatures, "
                "clean image only with subject and background"
            )

            ok = _gemini_generate_image(img_prompt, api_key, img_path)
            if not ok:
                # フォールバック: 黒背景
                subprocess.run(
                    [FFMPEG, "-y", "-f", "lavfi", "-i", "color=black:s=1080x1920:r=1",
                     "-vframes", "1", str(img_path)],
                    capture_output=True,
                )

            # Step6: FV動画生成
            job["current_name"] = f"{hook_id} — 動画合成中..."
            fv_hook_path = fv_gen_dir / f"fv_{i+1:02d}.mp4"
            hook_pattern = next((p for p in VISUAL_HOOK_PATTERNS if p["id"] == hook_id), VISUAL_HOOK_PATTERNS[i % 10])

            # モーションは全パターンで固定（ループ外で決定済み）
            motion_type = FIXED_MOTION

            # テロップタイムラインを構築:
            # - テキスト・出現タイミングは元動画(video_info.caption_segments)に完全固定
            # - パターン間で変わるのは「見せ方」のみ（placement / size / style / emphasis_words）
            # - 注釈(legal_notes)は自動追加しない（ユーザーが後工程で付与）
            base_segments = video_info.get("caption_segments") or []
            if not base_segments:
                # 後方互換: caption_segments が無ければ captions から等分割セグメントを構築
                base_segments = []
                caps_list = [c for c in (captions or []) if c]
                if caps_list:
                    n = len(caps_list)
                    per = max(1.0, fv_end_sec / n)
                    for k, t in enumerate(caps_list):
                        base_segments.append({
                            "start": k * per,
                            "end": min(fv_end_sec, (k + 1) * per),
                            "text": t,
                        })
            caption_timeline = _build_caption_timeline_from_pattern(
                base_segments=base_segments,
                pattern=pattern,
                fv_duration=fv_end_sec,
                profile=profile,
            )

            _build_fv_video(
                image_path=img_path,
                audio_path=audio_path,
                caption_timeline=caption_timeline,
                fv_duration=fv_end_sec,
                motion_type=motion_type,
                output_path=fv_hook_path,
            )

            # Step7: FV + ボディ を単純concat（音声固定・継ぎ目フェードは不要というユーザー指示）
            # 機能本質: FVの「映像のみ」を複数検証する。音声/テロップ/タイミングは固定。
            job["current_name"] = f"{hook_id} — ボディと結合中..."
            final_path = fv_gen_dir / f"final_{i+1:02d}_{hook_id}.mp4"
            concat_list = fv_gen_dir / f"concat_{i+1:02d}.txt"
            concat_list.write_text(
                f"file '{fv_hook_path.resolve()}'\nfile '{body_path.resolve()}'\n"
            )
            subprocess.run(
                [FFMPEG, "-y", "-f", "concat", "-safe", "0",
                 "-i", str(concat_list),
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                 "-c:a", "aac", "-b:a", "192k",
                 "-pix_fmt", "yuv420p",
                 str(final_path)],
                capture_output=True,
            )

            if final_path.exists():
                dur = get_duration(str(final_path))
                size_mb = final_path.stat().st_size / 1024 / 1024
                results.append({
                    "name": final_path.name,
                    "hook_id": hook_id,
                    "concept": pattern.get("concept", ""),
                    "why_stop": pattern.get("why_stop", ""),
                    "duration": round(dur, 1),
                    "size_mb": round(size_mb, 1),
                })
                print(f"[FV Gen] ✅ {final_path.name} 完成")

        job["status"] = "done"
        job["results"] = results
        log_to_sheet("生成ログ", [
            time.strftime("%Y-%m-%d %H:%M"), "FV自動生成",
            len(results), user_prompt, "", "", session_id[:8],
        ])

        # プロファイル連動: ジョブ履歴を .claude/clients/{client}/{product}/kosuri-history.md に追記。
        # 次回のジョブ時に同loaderから参照可能（将来的な学習材料）。
        if product_key and profile:
            try:
                _append_kosuri_history(product_key, {
                    "job_id": job_id,
                    "product_name": profile.get("product_name", product_key),
                    "user_prompt": user_prompt,
                    "target": video_info.get("target", ""),
                    "problem": video_info.get("problem", ""),
                    "count": len(results),
                    "hook_ids": [r.get("hook_id", "") for r in results],
                })
            except Exception as _he:
                print(f"[FV Gen] history append failed: {_he}")

    except _JobCancelled:
        print(f"[FV Gen] job {job_id} cancelled by user")
        job["status"] = "cancelled"
        job["current_name"] = "キャンセルされました"
        # 途中まで生成した results は保持（UIに表示される）
    except Exception as ex:
        print(f"[FV Gen] job error: {ex}")
        job["status"] = "error"
        job["error"] = str(ex)


@app.route("/fv-generate", methods=["POST"])
def fv_generate():
    """FV自動生成モード エントリーポイント。"""
    data = request.json or {}
    session_id = data.get("session_id", str(uuid.uuid4()))
    user_prompt = data.get("prompt", "").strip()
    fv_end_sec = float(data.get("fv_end_sec", 5.0))
    video_filename = data.get("video_filename", "")
    product_key = (data.get("product_key") or "").strip()

    if not user_prompt:
        return jsonify({"error": "プロンプトは必須です"}), 400

    # 動画パスを解決
    sess_dir = get_session_dir(session_id)
    video_path = None
    for d in [sess_dir, sess_dir / "base", sess_dir / "packed"]:
        if d.exists():
            for f in sorted(d.iterdir()):
                if f.suffix.lower() in VIDEO_EXT:
                    if not video_filename or f.name == video_filename:
                        video_path = str(f)
                        break
        if video_path:
            break

    if not video_path:
        return jsonify({"error": "動画が見つかりません。先にアップロードしてください"}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "running", "total": 10, "current": 0,
        "current_name": "起動中...", "results": [], "session_id": session_id,
        "cancelled": False, "mode": "fvgen",
    }
    threading.Thread(
        target=run_fv_generate_job,
        args=(job_id, session_id, video_path, fv_end_sec, user_prompt, product_key),
        daemon=True,
    ).start()

    return jsonify({
        "job_id": job_id,
        "session_id": session_id,
        "product_key": product_key,
    })


@app.route("/kosuri-products", methods=["GET"])
def kosuri_products():
    """利用可能な KOSURI 商品プロファイル一覧を返す（フロントの商品セレクタ用）。

    返却例:
      [{"product_key": "yomite_rkl", "client": "yomite", "product_name": "RKL 膝サポーター"}, ...]
    """
    try:
        products = _list_kosuri_products()
    except Exception as e:
        print(f"[kosuri-products] error: {e}")
        products = []
    return jsonify({"products": products})


@app.route("/fv-generated/<session_id>/<filename>")
def serve_fv_generated(session_id, filename):
    """生成済みFV動画を配信。"""
    p = get_session_dir(session_id) / "fv_generated" / filename
    if not p.exists():
        return "not found", 404
    return send_file(str(p), mimetype="video/mp4")


@app.route("/kosuri-chat", methods=["POST"])
def kosuri_chat():
    """KOSURIちゃんAIチャット endpoint。Gemini + ギャル人格。"""
    data = request.get_json(force=True)
    user_msg = data.get("message", "").strip()
    msg_type = data.get("type", "question")   # question / feedback / feature
    current_mode = data.get("mode", "")       # overlay / concat / cut / fvgen

    if not user_msg:
        return jsonify({"error": "メッセージが空だよ〜"}), 400

    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY_1", "")
    )

    # ─── モード別注意点 ────────────────────────────────────────
    MODE_TIPS = {
        "overlay": """
【FVオーバーレイ モードの注意点】（今このモードを使っている）
- ⚠️ FV動画の長さを本編動画のFV部分と同じ長さに合わせること！短すぎると黒画面が出る、長すぎると本編が隠れる
- FVと本編のアスペクト比（縦横比）を合わせること。違うとサイズがズレて見た目が崩れる
- BGMボリュームはデフォルト0.3（30%）。本編の声が埋もれないか確認して
- FVは「本編の最初に重ねる」だから、FV動画は本編の最初のシーンに合わせたものを使うと自然になる
- アップロードするFV動画は複数でもOK。複数の場合は全部まとめて選択して
""",
        "concat": """
【FV結合 モードの注意点】（今このモードを使っている）
- ⚠️ 入れる動画は「FVだけ」にすること！ボディ（本編）が始まる部分から先は切り取って入れないように
- 複数のFVをつなぐモードなので、各クリップが「FVとして完結している」ことを確認して
- クリップの長さを統一するとテンポよく仕上がる（バラバラだと視聴者が気になる）
- 各クリップが同じアスペクト比かチェック。違う場合は黒帯が入る場合がある
- BGMは結合した全体にかかる。FVのBGMが元々入っている場合はボリュームを下げて
- 結合順はアップロードしたファイル名の順番になるので、番号付きで管理するのがおすすめ
""",
        "cut": """
【FVカット モードの注意点】（今このモードを使っている）
- ⚠️ 注釈（薬機法テキストなど）が入っているかどうか必ず確認して！FVカットで切り出した動画には注釈が含まれない場合がある。このAI上でも注釈テキストを追加できるから、必要なら使って
- 「FV本数」を入力すると検出精度がめちゃ上がる！わかってるなら必ず入れて
- 長い動画（30分以上など）は処理時間が長くなる。余裕を持って実行して
- 100MB超えの素材もアップロードOK。GCS経由で直接送るから安心して
- カット点はAI（Gemini）が検証してるけど、出力後に確認することをおすすめ
- 素材動画の中にFVじゃないシーン（インタビューや商品紹介など）が混在してると検出精度が下がる
""",
        "fvgen": """
【FV自動生成 モードの注意点】（今このモードを使っている）
- ⚠️ ベータ版だけど「商品」を選ぶと精度が段違いに上がる！ヨミテ4商品（gungun / proust / onmyskin / RKL）はプロファイル搭載済み
- 商品を選ぶと → その商品のペルソナ・薬機法NG表現・勝ちコピー・モデル年齢を自動反映してくれる
- RKLはシニア女性モデル・権威（デューク更家さん）を自動で盛り込む。gungunは薬機法strictで「身長が伸びる」等のNG表現を自動回避
- 商品未選択でも動くけど汎用モードになる。最大精度で使うなら商品セレクタを使って
- プロンプトはそれに追加する具体指示（今回の狙い・訴求軸など）を書いて。「今回はギフト需要狙い」みたいに
- 「FV終了時刻」は動画のFVパートが終わる秒数。わからなければ目安で入れてOK
- 生成された画像FVは静止画ベースになってる（現在仕様）。動画化は今後対応予定
- 処理時間は5〜10分かかる。タブは閉じないで別タブで作業してて
""",
    }

    mode_context = MODE_TIPS.get(current_mode, "")

    KOSURI_SYSTEM = f"""あなたは「KOSURIちゃん」、FV量産Studioのサポートキャラクターです。

【キャラクター設定】
- 20歳、韓国系ギャル、明るくてフレンドリー
- 語尾に「〜だよ！」「〜じゃん？」「〜だよね〜」を自然に使う
- 絵文字を適度に使う（1〜2個/文が上限）
- 専門知識は正確に答える。わからないことは「ちょっとわかんないけど〜」と素直に言う
- 丁寧語と若者言葉を混ぜたくだけたトーン

{mode_context}

【全モード共通の注意点】
- 処理中はタブ閉じないで。別タブはOK
- サーバーはGoogle Cloud Runで動いてるから個人PCに影響なし
- ファイルサイズ制限なし（100MB超OK）
- 処理時間目安：オーバーレイ30秒〜2分 / 結合1〜3分 / カット3〜6分 / 自動生成5〜10分

【FV量産Studioの全機能】
1. FVオーバーレイ：本編動画にFV動画を重ねてオープニングを作る
2. FV結合：複数のFV動画をつなげて1本にまとめる
3. FVカット（β）：長い動画素材からFVシーンを自動検出して切り出す（Gemini AIで検証）
4. FV自動生成（β）：商品の説明文を入力するとAIが10パターンの画像FVを作る

【回答スタイル】
- 短く簡潔に（3〜5文以内）
- 現在のモードに関連する注意点・アドバイスを自然に混ぜて答える
- フィードバック・要望を受け取ったら「ちゃんと記録しとく！」と答える
- 答えた後は「他に聞きたいことある？😊」で締める
- メッセージタイプが feedback/feature の場合は特に丁寧に受け取る
"""

    payload = {
        "system_instruction": {"parts": [{"text": KOSURI_SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 450,
        },
    }

    reply_text = "ごめん、いまちょっとうまく答えられなかった〜💦 もう一回聞いてみて！"
    try:
        import urllib.request as _urllib_req
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        req = _urllib_req.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
        reply_text = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", reply_text)
        ).strip()
    except Exception as e:
        print(f"[KOSURIchat] Gemini error: {e}")

    # Sheets logging — 「ユーザーの声」シートに統合
    from datetime import datetime
    source_label = "bot-question" if msg_type == "question" else "bot-feature"
    log_to_sheet("ユーザーの声", [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        source_label,
        "",           # creator（botチャットは匿名）
        "",           # rating
        "",           # category
        user_msg[:500],
        "",           # job_id
        reply_text[:500],
    ])

    return jsonify({"reply": reply_text})


if __name__ == "__main__":
    print("\n  FV Mixer Studio")
    print("  http://localhost:5050\n")
    app.run(host="0.0.0.0", port=5050, debug=True)
