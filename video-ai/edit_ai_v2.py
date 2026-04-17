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
import csv
import json
import base64
import argparse
import subprocess
import tempfile
import textwrap
import unicodedata
import time
import random
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import requests
try:
    import mediapipe as mp
    _MP_FACE_MESH = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1,
        refine_landmarks=True, min_detection_confidence=0.5
    )
    _MEDIAPIPE_AVAILABLE = True
except Exception:
    _MP_FACE_MESH = None
    _MEDIAPIPE_AVAILABLE = False
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips,
)
import moviepy.video.fx.all as vfx

# ── 定数 ──────────────────────────────────────────────────
OUTPUT_SIZE    = (1080, 1920)   # 縦型 9:16
TARGET_DURATION = 60.0          # 目標動画尺（秒）
CHARS_PER_SEC  = 4.0            # テロップ読速（文字/秒）
MIN_DURATION   = 0.9            # シーン最短秒（1.5→0.9: テンポ改善）
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


# ─── Gemini APIキー管理 ─────────────────────────────────────
class GeminiKeyManager:
    """
    複数のGemini APIキーをラウンドロビンで管理。
    429 (rate limit) エラー時に自動で次のキーに切り替える。
    """
    def __init__(self, keys: list[str]):
        self._keys = [k for k in keys if k]
        self._idx = 0

    def __bool__(self) -> bool:
        return bool(self._keys)

    def current(self) -> str | None:
        return self._keys[self._idx % len(self._keys)] if self._keys else None

    def rotate(self) -> str | None:
        if len(self._keys) <= 1:
            return self.current()
        self._idx = (self._idx + 1) % len(self._keys)
        print(f"  🔄 Gemini APIキー切り替え → KEY_{self._idx + 1}")
        return self.current()

_GEMINI_KEY_MGR: GeminiKeyManager | None = None


def _gemini_post(payload: dict, timeout: int = 20,
                 model: str = "gemini-2.5-flash") -> requests.Response:
    """
    Gemini APIへのPOST。
    _GEMINI_KEY_MGR が設定されていれば 429 時にキーローテーションしてリトライ。
    """
    mgr = _GEMINI_KEY_MGR
    max_attempts = len(mgr._keys) if mgr else 1
    last_resp = None
    for attempt in range(max(1, max_attempts)):
        key = mgr.current() if mgr else None
        if not key:
            raise RuntimeError("Gemini APIキーが設定されていません")
        url = (f"https://generativelanguage.googleapis.com/v1beta/models"
               f"/{model}:generateContent?key={key}")
        last_resp = requests.post(url, json=payload, timeout=timeout)
        if last_resp.status_code == 429 and mgr and len(mgr._keys) > 1 and attempt < max_attempts - 1:
            print(f"  ⚠️  Gemini rate limit (429)。キーローテーション中...")
            mgr.rotate()
            continue
        return last_resp
    return last_resp


# ─── Gemini Vision: クリップ内容分析 ──────────────────────────
def analyze_clip_with_gemini(clip_path: str, gemini_key: str,
                             scene_text: str = "") -> dict:
    """
    クリップの複数フレームをGemini 2.0 Flashに送り、
    被写体・最適クロップ方向・ベスト開始秒を返す。
    返値例: {"subject":"白衣の医師が話している", "crop_x_percent":35,
             "best_start_sec": 1.5, "reason":"..."}
    """
    try:
        # クリップ尺を取得
        probe = subprocess.run(
            [_FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", clip_path],
            capture_output=True, text=True
        )
        try:
            clip_dur = float(probe.stdout.strip())
        except Exception:
            clip_dur = 3.0

        # 複数フレームを抽出（素材全体から均等に3枚）
        sample_times = []
        if clip_dur <= 2.0:
            sample_times = [clip_dur * 0.3]
        else:
            sample_times = [clip_dur * p for p in [0.15, 0.5, 0.85]]

        parts = []
        for i, st in enumerate(sample_times):
            frame_tmp = tempfile.mktemp(suffix=".jpg")
            subprocess.run(
                [FFMPEG, "-y", "-i", clip_path, "-ss", str(st), "-vframes", "1", frame_tmp],
                capture_output=True, check=True
            )
            if os.path.exists(frame_tmp):
                with open(frame_tmp, "rb") as f:
                    parts.append({"inline_data": {"mime_type": "image/jpeg",
                                                  "data": base64.b64encode(f.read()).decode()}})
                os.unlink(frame_tmp)

        if not parts:
            return {"subject": "不明", "crop_x_percent": 50, "best_start_sec": 0}

        scene_hint = f"\nこの素材に合わせるテロップ: 「{scene_text[:30]}」" if scene_text else ""
        parts.append({"text": (
            f"この動画素材の{len(parts)}枚のフレーム（前半・中間・後半）を見て、JSONのみで答えて。\n"
            f"素材の総尺: {clip_dur:.1f}秒{scene_hint}\n\n"
            "fields:\n"
            "  subject: 何が映っているか（日本語・具体的に）\n"
            "  crop_x_percent: 縦型9:16にクロップする際、最も重要な被写体の中心が\n"
            "                  画像横幅の何%の位置にあるか（0=左端 50=中央 100=右端）整数\n"
            "  best_start_sec: この素材の中で視聴者の感情を最も動かす瞬間は何秒目から始まるか。\n"
            "                  判断基準: 表情の変化、動きの開始、商品が見える瞬間、インパクトのある構図。\n"
            "                  0.0〜素材尺の範囲で小数点1桁で返す。\n"
            "  reason: なぜその瞬間がベストか（日本語・1文）\n"
            "JSON only。余計な説明不要。"
        )})

        resp = _gemini_post({"contents": [{"parts": parts}]}, timeout=20)
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r"```json|```", "", raw).strip()
        # Geminiが複数JSONオブジェクトやトレイリングカンマを返すことがあるので堅牢にパース
        # Step1: 最初の{}ブロックだけ抽出
        brace_depth = 0
        json_end = 0
        for i, ch in enumerate(raw):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    json_end = i + 1
                    break
        if json_end > 0:
            raw = raw[:json_end]
        elif not raw.endswith("}"):
            raw += "}"
        # Step2: トレイリングカンマ除去（JSON非準拠だがGeminiが頻繁に出す）
        raw = re.sub(r",\s*}", "}", raw)
        raw = re.sub(r",\s*]", "]", raw)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            # Step3: 正規表現で各フィールドを個別抽出（最終フォールバック）
            result = {}
            m = re.search(r'"subject"\s*:\s*"([^"]*)"', raw)
            result["subject"] = m.group(1) if m else "不明"
            m = re.search(r'"crop_x_percent"\s*:\s*(\d+)', raw)
            result["crop_x_percent"] = int(m.group(1)) if m else 50
            m = re.search(r'"best_start_sec"\s*:\s*([\d.]+)', raw)
            result["best_start_sec"] = float(m.group(1)) if m else 0
            m = re.search(r'"reason"\s*:\s*"([^"]*)"', raw)
            result["reason"] = m.group(1) if m else ""
        # best_start_sec を安全クリップ
        best_start = float(result.get("best_start_sec", 0))
        result["best_start_sec"] = round(max(0, min(clip_dur - 0.5, best_start)), 1)
        return result
    except Exception as e:
        return {"subject": "不明", "crop_x_percent": 50, "best_start_sec": 0,
                "reason": f"分析失敗: {e}"}


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


def resolve_voice_full(category: str | None, catalog: dict) -> dict:
    """
    声カテゴリー名 → voice dictをそのまま返す（engine / reference_id / speaker_id 等を含む）。
    engine未設定の場合は "fish_audio" を補完して返す。
    """
    voices = catalog.get("voices", {})
    defaults = catalog.get("defaults", {})
    if not category:
        category = defaults.get("fallback_category", "女性・クール")
    voice = voices.get(category)
    if not voice:
        print(f"  ⚠️  声カテゴリー '{category}' が voice_catalog.json に見つかりません。fish_audioデフォルトで続行。")
        return {"engine": "fish_audio", "reference_id": None, "speed": 1.0}
    result = dict(voice)
    result.setdefault("engine", "fish_audio")  # engineフィールド後付け補完
    print(f"  🎙  声: {category} (engine={result['engine']})")
    return result


# ─── Fish Audio: 音声時間取得 ─────────────────────────────────
def get_audio_duration(path: str) -> float:
    """ffprobeで音声ファイルの長さ（秒）を取得"""
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True
        )
        return float(r.stdout.strip())
    except Exception:
        try:
            return AudioFileClip(path).duration
        except Exception:
            return 0.0


def trim_silence(audio_path: str, threshold_db: float = -32.0,
                 min_silence_ms: int = 30) -> str:
    """ナレーションmp3の先頭・末尾の無音をトリムしたファイルを返す。
    ffmpegのsilenceremoveフィルタで先頭・末尾を処理。元ファイルを上書き。
    """
    import shutil
    trimmed = audio_path + ".trimmed.mp3"
    try:
        # ffmpeg silenceremove: start_periods=1で先頭無音除去、stop_periods=1で末尾無音除去
        threshold_amp = 10 ** (threshold_db / 20)  # dB → 振幅比
        cmd = [
            _FFMPEG, "-y", "-i", audio_path,
            "-af", (
                f"silenceremove=start_periods=1:start_threshold={threshold_amp}"
                f",areverse"
                f",silenceremove=start_periods=1:start_threshold={threshold_amp}"
                f",areverse"
            ),
            "-q:a", "2", trimmed
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and Path(trimmed).exists() and Path(trimmed).stat().st_size > 0:
            shutil.move(trimmed, audio_path)
        else:
            # トリム失敗 → 元ファイルのまま
            if Path(trimmed).exists():
                Path(trimmed).unlink()
    except Exception:
        if Path(trimmed).exists():
            Path(trimmed).unlink()
    return audio_path


# ─── Fish Audio: シーン単位TTS（同期方式の核心） ──────────────
def _fish_tts_single(text: str, fish_key: str, output_path: str,
                     reference_id: str | None, speed: float,
                     max_retries: int = 4) -> bool:
    """1シーン分のテキストをFish AudioでTTS生成。成功でTrue。
    429 (Rate Limit) の場合はエクスポネンシャルバックオフ+ジッターでリトライ。
    """
    payload: dict = {"text": text, "format": "mp3", "latency": "normal"}
    if reference_id:
        payload["reference_id"] = reference_id
    if speed != 1.0:
        payload["prosody"] = {"speed": speed}

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                "https://api.fish.audio/v1/tts",
                headers={"Authorization": f"Bearer {fish_key}", "Content-Type": "application/json"},
                json=payload,
                stream=True,
                timeout=60
            )
            if resp.status_code == 429:
                wait = (2 ** attempt) + random.uniform(0.5, 2.0)
                print(f"      ⏳ Fish Audio 429 rate limit → {wait:.1f}s待機後リトライ ({attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            if resp.status_code != 200:
                print(f"      ⚠️  Fish Audio エラー: {resp.status_code}")
                return False
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2.0)
                continue
            print(f"      ⚠️  Fish Audio 失敗: {e}")
            return False
    print(f"      ⚠️  Fish Audio: {max_retries}回リトライ後もエラー")
    return False


# ─── VOICEVOX TTS (su-shiki.com 非公式Web API) ────────────────
def _voicevox_tts_single(text: str, api_key: str, output_path: str,
                          speaker_id: int = 13, speed: float = 1.0) -> bool:
    """
    VOICEVOX TTSをsu-shiki.com非公式Web API経由で呼び出す。
    APIキー取得先（無料）: https://voicevox.su-shiki.com/su-shikiapis/
    speaker_id=13 → 青山龍星 (VOICEVOX Nemo)  ← クレジット: "VOICEVOX Nemo" 必須
    商用利用無料。ただし出力動画にクレジット表記を入れること。
    """
    if not api_key:
        print("      ⚠️  VOICEVOX_API_KEY が未設定。su-shiki.com でAPIキーを取得してください。")
        return False
    url = "https://api.su-shiki.com/v2/voicevox/audio/"
    params = {
        "text": text,
        "speaker": speaker_id,
        "key": api_key,
        "speed": round(speed, 2),
    }
    try:
        resp = requests.get(url, params=params, timeout=60)
        if resp.status_code != 200:
            print(f"      ⚠️  VOICEVOX エラー: {resp.status_code} {resp.text[:80]}")
            return False
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        print(f"      ⚠️  VOICEVOX 失敗: {e}")
        return False


# ─── Coefont TTS API ─────────────────────────────────────────
def _coefont_tts_single(text: str, api_key: str, output_path: str,
                         voice_id: str = "", speed: float = 1.0) -> bool:
    """
    Coefont REST APIでTTSを生成する（Standardプラン ¥4,400/月 が必要）。
    voice_id: Coefontダッシュボードで確認 → voice_catalog.json の coefont_voice_id に設定。
    ⚠️ ひろゆき等の実在人物モデルは商用広告使用前にCoefontの正式ライセンス契約を必ず確認すること。
    API仕様: https://coefont.cloud/developers
    """
    if not api_key:
        print("      ⚠️  COEFONT_API_KEY が未設定。~/.zshrc に COEFONT_API_KEY を追加してください。")
        return False
    if not voice_id or voice_id == "FILL_AFTER_CONFIRM":
        print("      ⚠️  Coefont voice_id が未設定。voice_catalog.json の coefont_voice_id を設定してください。")
        return False
    url = "https://api.coefont.cloud/v2/speech"
    payload = {
        "coefont": voice_id,
        "text": text,
        "speed": round(speed, 2),
    }
    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        if resp.status_code != 200:
            print(f"      ⚠️  Coefont エラー: {resp.status_code} {resp.text[:100]}")
            return False
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        print(f"      ⚠️  Coefont 失敗: {e}")
        return False


def generate_scene_narrations(
    scenes: list,
    fish_key: str,
    output_dir: str,
    voice_category: str | None = None,
    tts_speed: float = 1.0,
) -> list[tuple[str | None, float]]:
    """
    【コアロジック】シーンごとに個別TTSを生成し、音声の実尺を返す。
    返値: [(mp3_path_or_None, duration_sec), ...]  ← scenesと同順

    v14: ThreadPoolExecutor で全シーン並列生成（最大15並列）。
    Fish Audioは並列リクエストを受け付けるため、20シーン分が3〜5秒に短縮される。
    音声尺が映像尺を決定する。映像を音声に合わせる（逆は不可）。
    """
    catalog = load_voice_catalog()
    voice_info = resolve_voice_full(voice_category, catalog)
    engine = voice_info.get("engine", "fish_audio")
    voice_speed = voice_info.get("speed", 1.0)
    # voice_catalog の speed は音質調整用。tts_speed は全体テンポ調整用。
    # 両方掛け合わせてTTSエンジンに渡す（上限2.0、下限0.5でクリップ）
    effective_speed = max(0.5, min(2.0, voice_speed * tts_speed))
    if effective_speed != 1.0:
        print(f"  🎚  TTS速度: {effective_speed:.2f}x（voice={voice_speed}, target={tts_speed:.2f}）")

    # ─── エンジン別パラメータ解決 ────────────────────────────
    if engine == "voicevox":
        _voicevox_speaker_id = voice_info.get("speaker_id", 13)
        _voicevox_key = os.environ.get(voice_info.get("api_key_env", "VOICEVOX_API_KEY"), "")
        if not _voicevox_key:
            print(f"  ⚠️  VOICEVOX_API_KEY が未設定 → fish_audioにフォールバック")
            engine = "fish_audio"
    if engine == "coefont":
        _coefont_voice_id = voice_info.get("coefont_voice_id", "FILL_AFTER_CONFIRM")
        _coefont_key = os.environ.get(voice_info.get("api_key_env", "COEFONT_API_KEY"), "")
        if not _coefont_key or _coefont_voice_id == "FILL_AFTER_CONFIRM":
            print(f"  ⚠️  Coefont APIキーまたはvoice_idが未設定 → fish_audioにフォールバック")
            engine = "fish_audio"
    if engine == "fish_audio":
        reference_id = voice_info.get("reference_id")
        if not reference_id or reference_id == "FILL_FROM_FISH_AUDIO":
            reference_id = None

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 結果リストをシーン数で初期化（順序保持のためインデックスで管理）
    results: list[tuple[str | None, float]] = [(None, MIN_DURATION)] * len(scenes)

    # テキストありシーンのみタスクリストに追加
    tts_tasks: list[tuple[int, object, str, str]] = []
    for i, scene in enumerate(scenes):
        if scene.text:
            mp3_path = str(Path(output_dir) / f"scene_{scene.no:02d}.mp3")
            tts_text = normalize_text_for_tts(scene.text)
            tts_tasks.append((i, scene, mp3_path, tts_text))

    if not tts_tasks:
        return results

    engine_label = {"fish_audio": "Fish Audio", "voicevox": "VOICEVOX", "coefont": "Coefont"}.get(engine, engine)
    print(f"  🚀 TTS並列生成: {len(tts_tasks)}シーン（最大4並列・engine={engine_label}）")

    def _do_tts(task: tuple) -> tuple:
        idx, scene, mp3_path, tts_text = task
        if engine == "voicevox":
            ok = _voicevox_tts_single(tts_text, _voicevox_key, mp3_path, _voicevox_speaker_id, effective_speed)
        elif engine == "coefont":
            ok = _coefont_tts_single(tts_text, _coefont_key, mp3_path, _coefont_voice_id, effective_speed)
        else:  # fish_audio（デフォルト）
            ok = _fish_tts_single(tts_text, fish_key, mp3_path, reference_id, effective_speed)
        return idx, scene, mp3_path, ok

    with ThreadPoolExecutor(max_workers=min(4, len(tts_tasks))) as executor:
        for idx, scene, mp3_path, ok in executor.map(_do_tts, tts_tasks):
            if ok:
                trim_silence(mp3_path)  # 先頭・末尾の無音をカット
                dur = get_audio_duration(mp3_path)
                print(f"      🎙  S{scene.no:02d} → {dur:.2f}s")
                results[idx] = (mp3_path, max(dur, MIN_DURATION))
            else:
                results[idx] = (None, max(MIN_DURATION, len(scene.text) / CHARS_PER_SEC))

    total = sum(d for _, d in results)
    print(f"  ✅ シーン別TTS完了 合計: {total:.1f}s ({len(results)}シーン)")
    return results


def estimate_tts_speed(scenes: list, target_sec: float = TARGET_DURATION * 0.72) -> float:
    """
    テキスト文字数から自然な読み上げ時間を推定し、
    target_secに収まる最小速度（1.25以上）を返す。
    目標尺を72%に設定（60s×0.72≒43s）で無言間を最小化。
    最低でも1.25x（速め）を保証してテンポを維持。
    """
    total_chars = sum(len(normalize_text_for_tts(s.text)) for s in scenes if s.text)
    natural_sec = total_chars / CHARS_PER_SEC
    speed = natural_sec / target_sec if natural_sec > target_sec else 1.0
    speed = round(min(speed, 2.0), 2)
    # テンポ維持のため最低速度フロアを1.25xに設定
    speed = max(speed, 1.25)
    print(f"  📊 推定読み上げ時間: {natural_sec:.1f}s → 目標{target_sec:.0f}s → TTS速度: {speed}x（フロア1.25x）")
    return speed


# ─── TTS用テキスト正規化 ─────────────────────────────────────
def normalize_text_for_tts(text: str) -> str:
    """
    Fish Audio TTS に送る前にテキストを正規化する。
    ・【〇〇】→ 〇〇！ に変換（括弧は読まれないため除去）
    ・「だから」「そこで」「しかし」などの転換ワードの前に間（、）を追加
    ・改行は読点に変換
    """
    # 改行 → 読点（自然な区切り）
    text = text.replace('\n', '、')
    # 【〇〇】 → 〇〇！（STOPフェーズのフックワードを確実に読ませる）
    text = re.sub(r'【([^】]+)】', r'\1！', text)
    # 転換ワードの前に間を追加（先頭にある場合も含む）
    TRANSITION_WORDS = ['だから', 'そこで', 'しかし', 'でも', 'だが', 'だって']
    for word in TRANSITION_WORDS:
        # 文中・先頭を問わず「、」がなければ追加
        text = re.sub(r'(?<!、)(' + word + r')', r'、\1', text)
    # 先頭の余分な読点を除去
    text = text.lstrip('、').strip()
    return text


# ─── Fish Audio: 全文結合方式（後方互換・非推奨） ─────────────
def generate_narration(
    scenes: list,
    fish_key: str,
    output_path: str,
    voice_category: str | None = None,
) -> str | None:
    """非推奨。generate_scene_narrations()を使うこと。後方互換のため残す。"""
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
            json=payload, stream=True, timeout=60
        )
        if resp.status_code != 200:
            return None
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        return output_path
    except Exception:
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


# ── 台本パーサ（CSV） ──────────────────────────────────────
def parse_script_csv(csv_path: str) -> tuple[list[Scene], str, str | None, str | None, int, str]:
    """
    新フォーマットCSV台本をパース。
    返値: (scenes, global_annotation, voice_category, bgm_filename, ref_level, narration_mode)
    narration_mode: "tts"（AI生成）or "original"（元動画の音声をそのまま使う）
    ref_level: 参考動画の反映レベル (1=エッセンス, 2=スタイル踏襲, 3=完全トレース)
    """
    scenes: list[Scene] = []
    global_annotation = ""
    voice_category: str | None = None
    bgm_filename: str | None = None
    ref_level: int = 2  # デフォルト: スタイル踏襲（現状の動作）
    narration_mode: str = "tts"  # デフォルト: TTS生成

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    mode = None
    for row in rows:
        if not row:
            continue
        col0 = row[0].strip()

        # セクション検出
        if "■ 動画の基本情報" in col0:
            mode = "base"
        elif "■ ナレーション設定" in col0:
            mode = "narr"
        elif "■ 固定注釈" in col0:
            mode = "anno"
        elif "■ BGM設定" in col0 or "■ BGM" in col0:
            mode = "bgm"
        elif "■ 参考動画設定" in col0 or "■ 参考動画" in col0:
            mode = "ref"
        elif "■素材フォルダー" in col0 or "■ スタイル" in col0:
            mode = "other"
        elif "■ 台本" in col0:
            mode = "script"
        elif "■ 素材リスト" in col0:
            mode = "end"
            break

        elif mode == "narr":
            # 4列形式: col0=key, col1=val / 5列形式: col0="", col1=key, col2=val
            if col0:
                key, val = col0, (row[1].strip() if len(row) > 1 else "")
            else:
                key, val = (row[1].strip() if len(row) > 1 else ""), (row[2].strip() if len(row) > 2 else "")
            if key == "ナレーション" and val:
                # "なし（テロップのみ）" / "なし" → original モード
                if val.startswith("なし"):
                    narration_mode = "original"
                    print(f"  🔇 ナレーションモード: 元音声をそのまま使用（TTS不使用）")
                else:
                    narration_mode = "tts"
            if key == "声のカテゴリー" and val:
                # "女性・クール（健康食品・サプリ向き" → "女性・クール" に正規化
                voice_category = val.split("（")[0].strip()

        elif mode == "ref":
            if col0:
                key, val = col0, (row[1].strip() if len(row) > 1 else "")
            else:
                key, val = (row[1].strip() if len(row) > 1 else ""), (row[2].strip() if len(row) > 2 else "")
            if "反映レベル" in key and val:
                # "1", "2", "3" or "1（エッセンス）" → 先頭数字を抽出
                m = re.match(r"(\d)", val)
                if m:
                    ref_level = max(1, min(3, int(m.group(1))))

        elif mode == "bgm":
            # 4列形式: col0=key, col1=val / 5列形式: col0="", col1=key, col2=val
            if col0:
                key, val = col0, (row[1].strip() if len(row) > 1 else "")
            else:
                key, val = (row[1].strip() if len(row) > 1 else ""), (row[2].strip() if len(row) > 2 else "")
            # "BGMファイル" / "BGMファイル名" どちらのキー名も受け付ける
            if key in ("BGMファイル", "BGMファイル名") and val:
                bgm_filename = val

        elif mode == "anno":
            # 注釈テキストが入っている行（col0が空 or "固定注釈⇨"でない）
            # 5列形式では col1=key/note, col2=text になる場合があるので両方チェック
            text = ""
            for ci in [1, 2]:
                candidate = row[ci].strip() if len(row) > ci else ""
                if candidate and "【例" not in candidate and "【必要" not in candidate and "注釈テキスト" not in candidate and "注釈内容" not in candidate:
                    text = candidate
                    break
            if text:
                if global_annotation:
                    global_annotation += "　" + text
                else:
                    global_annotation = text

        elif mode == "script":
            # 4列形式: col0=No., col1=text, col2=素材, col3=note
            # 5列形式: col0="",  col1=No., col2=text, col3=素材, col4=note
            if col0 == "" and len(row) > 1 and row[1].strip().isdigit():
                # 5列形式（新テンプレート）
                no_str   = row[1].strip()
                text     = row[2].strip() if len(row) > 2 else ""
                sozai_raw= row[3].strip() if len(row) > 3 else ""
                note     = row[4].strip() if len(row) > 4 else ""
            elif col0.isdigit():
                # 4列形式（旧テンプレート）
                no_str   = col0
                text     = row[1].strip() if len(row) > 1 else ""
                sozai_raw= row[2].strip() if len(row) > 2 else ""
                note     = row[3].strip() if len(row) > 3 else ""
            else:
                continue  # ヘッダ行 or 空行スキップ

            no = int(no_str)

            # テキスト空・テンプレートプレースホルダーはスキップ
            if not text or text in ("【ここに書く】",) or text == "【ここに書く】":
                continue
            # 完全に【...】で囲まれたテンプレート行はスキップ（実コンテンツは除外しない）
            if re.match(r"^【[^】]*】$", text):
                continue

            # 素材IDパース（改行・スペース区切りに対応）
            clip_refs = _parse_clip_refs_csv(sozai_raw)

            emphasis = any(w in text for w in EMPHASIS_WORDS)
            scenes.append(Scene(no=no, text=text, clip_refs=clip_refs,
                                note=note, emphasis=emphasis))

    # ─── 注釈バリデーション（サイレントスルー禁止） ─────────────────
    print(f"\n  📋 注釈チェック:")
    if global_annotation:
        print(f"  ✅ 固定注釈: 「{global_annotation[:30]}...」")
    else:
        print(f"  ⚠️  固定注釈: 未設定 — CSVの「■ 固定注釈」セクションに薬機法テキストを入力してください")
    scene_notes = [(s.no, s.note) for s in scenes if s.note]
    if scene_notes:
        print(f"  ✅ カット注釈: {len(scene_notes)}シーンに設定あり")
        for no, note in scene_notes:
            print(f"     S{no:02d}: {note[:40]}")
    else:
        print(f"  ℹ️  カット注釈: なし（各シーンの注釈欄は空）")

    if bgm_filename:
        print(f"  🎵 BGM: {bgm_filename}")
    narr_label = "元音声（TTS不使用）" if narration_mode == "original" else "TTS生成"
    print(f"\n台本パース完了 (CSV): {len(scenes)} シーン / 声: {voice_category or 'デフォルト'} / ナレーション: {narr_label}")
    return scenes, global_annotation, voice_category, bgm_filename, ref_level, narration_mode


def _parse_clip_refs_csv(raw: str) -> list[str]:
    """CSV素材フィールド: 改行・スペース区切りのIDリストをパース。全角数字→半角変換。"""
    if not raw:
        return []
    # 全角→半角正規化
    raw = unicodedata.normalize("NFKC", raw)
    # 改行・スペースで分割
    tokens = [t.strip() for t in re.split(r"[\s\n]+", raw) if t.strip()]
    refs = []
    for t in tokens:
        # "clip-001", "clip-012" などの clip-NNN 形式（新フォーマット）
        if re.match(r"^clip-\d+$", t, re.IGNORECASE):
            refs.append(t)
        # "scene_01.mov" などの前処理済みファイル名（拡張子付き）
        elif re.match(r".+\.(mov|mp4|avi|mkv|webm|heic|jpeg|jpg|png|webp)$", t, re.IGNORECASE):
            refs.append(t)
        # "1-1", "12-2" などの X-N 形式
        elif re.match(r"^\d{1,2}-\d$", t):
            refs.append(t)
        # 単体番号 "3", "11", "15" など
        elif re.match(r"^\d+$", t):
            refs.append(t)
    return refs


# ── 台本パーサ（HTML） ─────────────────────────────────────
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
EXTS = [".mp4", ".MP4", ".mov", ".MOV", ".HEIC", ".heic", ".jpeg", ".jpg", ".JPG", ".PNG", ".webp", ".WEBP"]

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
    ref="1-1"           → 1-1.mp4 or 1-1.mov など
    ref="3"             → 3.HEIC など（全角数字も対応）
    ref="scene_01.mov"  → 拡張子付きファイル名を直接マッチング
    """
    d = Path(clips_dir)

    # 拡張子付きファイル名の直接マッチング（前処理済みファイル対応）
    direct = d / ref
    if direct.exists():
        return str(direct)

    # 半角→全角、全角→半角の両方で試す
    ref_stem = Path(ref).stem  # 拡張子を除いた部分
    ref_full = ref_stem.translate(str.maketrans("0123456789", "０１２３４５６７８９"))
    ref_half = ref_stem.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    candidates = [ref_stem, ref_full, ref_half]

    for c in candidates:
        for ext in EXTS:
            p = d / f"{c}{ext}"
            if p.exists():
                return str(p)

    # サブフォルダ再帰検索（fv/ などのサブディレクトリ対応）
    for c in candidates:
        for ext in EXTS:
            matches = list(d.rglob(f"{c}{ext}"))
            if matches:
                return str(matches[0])
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


# ── 上部固定バナー（動画終始表示テキスト） ───────────────────────
def make_top_banner(text: str, size: tuple) -> np.ndarray:
    """動画上部に全編表示する固定バナーのRGBAオーバーレイを返す。"""
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(54)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    strip_h = text_h + 24
    # 半透明黒帯
    draw.rectangle([(0, 0), (w, strip_h)], fill=(0, 0, 0, 180))
    x = (w - text_w) // 2
    y = 10
    # 縁取り
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2)]:
        draw.text((x+dx, y+dy), text, font=font, fill=(0, 0, 0, 220))
    # 本文（白）
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    return np.array(img)


# ── テロップ テキストクリーニング ──────────────────────────────
def clean_telop_text(text: str) -> str:
    """テロップ用テキストクリーニング。ショート動画に不要な句読点・引用符を除去。
    削除: 、。「」
    残す: …！？※（感情・余韻・注釈の演出意図）
    """
    # ※以降は注釈なので分離して保持
    if "※" in text:
        idx = text.index("※")
        main = text[:idx]
        sub = text[idx:]  # ※以降はそのまま保持
    else:
        main = text
        sub = ""
    # 句読点・引用符を除去
    for ch in "、。「」":
        main = main.replace(ch, "")
    return (main + sub).strip()


# ── テロップ画像生成 ──────────────────────────────────────
def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    """'#RRGGBB' → (R, G, B, A)"""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (255, 255, 255, alpha)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def calc_dynamic_font_size(text: str, emphasis: bool,
                           scene_no: int, total_scenes: int,
                           base_size: int = FONT_SIZE,
                           emph_size: int = FONT_EMPH_SIZE) -> int:
    """
    参考動画のエッセンス: フォントサイズ = 文字数の反比例関数。
    参考動画実測値: 8文字→70px / 10文字→70px / 15文字→50px / 16文字→50px
    → 文字数が少ないほど大きく、多いほど小さく。自由度を最大化する。
    出力範囲: 40px〜100px（参考動画の30〜80pxを9:16全画面用にスケール）
    """
    clean = clean_telop_text(text).split("※")[0].strip().replace("\n", "")
    char_count = len(clean)

    # 文字数→フォントサイズ: 線形補間（参考動画のパターンを再現）
    # 4文字以下 → 100px（最大インパクト）
    # 8文字   → 85px
    # 12文字  → 72px
    # 16文字  → 60px
    # 20文字+ → 48px（読ませるモード）
    if char_count <= 4:
        fs = 100
    elif char_count <= 20:
        # 4→100, 20→48 の線形補間
        fs = int(100 - (char_count - 4) * (100 - 48) / 16)
    else:
        fs = 48

    # emphasis ワード → さらに10%ブースト
    if emphasis:
        fs = int(fs * 1.12)

    # 冒頭フック(S1-2) / ラストCTA(最後3シーン) → 最低でも72px
    if scene_no <= 2 or scene_no >= total_scenes - 2:
        fs = max(fs, 72)

    # 安全クリップ: 40px〜100px
    return max(40, min(100, fs))


def make_telop(text: str, size: tuple, emphasis: bool = False,
               telop_y_ratio: float = TELOP_Y_RATIO,
               font_size: int = FONT_SIZE,
               font_emph_size: int = FONT_EMPH_SIZE,
               text_color: str | None = None,
               stroke_color: str | None = None,
               scene_no: int = 0,
               total_scenes: int = 1) -> np.ndarray:
    """
    テキスト → RGBA numpy配列。
    - 全テロップに半透明背景帯を描画（視認性確保）
    - フォントサイズはシーン役割×テキスト量で動的決定
    - 「※」以降は自動的に小フォントで描画。
    """
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 句読点フィルタ（v13: ショート動画に不要な、。「」を除去）
    text = clean_telop_text(text)

    # ※ でメインテキストと注釈テキストに分割
    if "※" in text:
        idx       = text.index("※")
        main_text = text[:idx].strip()
        sub_text  = text[idx:].strip()
    else:
        main_text = text
        sub_text  = ""

    # 動的フォントサイズ決定
    fs = calc_dynamic_font_size(text, emphasis, scene_no, total_scenes,
                                font_size, font_emph_size)
    cpl    = max(8, int(CHARS_PER_LINE * (FONT_SIZE / fs)))  # フォントに応じて折り返し調整
    font   = load_font(fs)
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

    # 動的Y位置: Meta Reels安全帯（y_ratio 0.55〜0.78）に配置
    # 下部320px（y>0.833）はいいね/コメント/URLバナーUI干渉ゾーンのため禁止
    if fs >= 80:
        dynamic_y = 0.62   # 大きいテロップ → HOOK・強調（安全帯上部）
    elif fs >= 65:
        dynamic_y = 0.67   # 中くらい → 通常説明（安全帯中央）
    else:
        dynamic_y = 0.72   # 小さいテロップ → OFFER・CTA（安全帯下部）

    # Meta安全帯フロア: 0.55以上、0.833未満を保証
    raw_y = dynamic_y if telop_y_ratio == TELOP_Y_RATIO else telop_y_ratio
    effective_y = max(raw_y, 0.55)   # Meta Reels安全帯下限（旧0.75は誤り・UI干渉ゾーン）
    base_y = int(h * effective_y) - total_h // 2
    # 上端・下端はみ出し防止
    base_y = max(20, min(h - total_h - 40, base_y))

    # --- 半透明背景帯（視認性の要） ---
    # 参考動画の本質: 白背景×黒文字 = コントラスト最大化
    # 全テロップに白半透明帯を敷き、黒文字で読ませる
    band_margin = 20  # 帯の上下余白
    band_top = base_y - band_margin
    band_btm = base_y + total_h + band_margin
    # 画面内にクリップ
    band_top = max(0, band_top)
    band_btm = min(h, band_btm)
    if emphasis:
        # 強調: 黄色帯 × 黒文字（目を引く）
        draw.rectangle([0, band_top, w, band_btm], fill=(255, 215, 0, 210))
    else:
        # 通常: 白半透明帯 × 黒文字（参考動画と同じ高コントラスト設計）
        draw.rectangle([0, band_top, w, band_btm], fill=(255, 255, 255, 200))

    # テキスト色: 白帯/黄色帯 → 常に黒文字（コントラスト最大）
    t_rgba  = (0, 0, 0, 255)
    st_rgba = None  # 白帯の上なので縁取り不要

    def _draw_line(line, fnt, fsize, y):
        bbox = fnt.getbbox(line)
        tw   = bbox[2] - bbox[0]
        x_offset = bbox[0]  # フォントの左端オフセット補正
        x    = max(pad_x, (w - tw) // 2 - x_offset)
        if st_rgba:
            for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                draw.text((x+dx, y+dy), line, font=fnt, fill=st_rgba)
        draw.text((x, y), line, font=fnt, fill=t_rgba)

    cur_y = base_y
    for line in main_lines:
        _draw_line(line, font, fs, cur_y)
        cur_y += line_h
    if sub_lines:
        cur_y += 4
        for line in sub_lines:
            _draw_line(line, sub_font, sub_fs, cur_y)
            cur_y += sub_line_h

    return np.array(img)


# ── 静止画をVideoクリップ化 ─────────────────────────────────

def fit_to_vertical_blur_fill(img: Image.Image) -> Image.Image:
    """
    静止画を 1080×1920 に変換する「ブラー背景フィル」方式。

    設計思想:
    - 広告素材・商品画像は「制作者が意図した全体」を見せるべき
    - 横長・正方形画像をクロップすると重要な要素が失われる
    - Instagram/TikTokリール標準: ブラー背景+全体前景でプロ品質

    処理:
    - 背景: 元画像をcover(拡大充填)→ ガウスブラー(r=30)→ 輝度50%で暗化
    - 前景: 元画像をcontain(クロップなし)で中央に配置
    - 結果: 黒帯なし・全体表示・フレーム余白なし
    """
    from PIL import ImageFilter, ImageEnhance

    ow, oh = OUTPUT_SIZE
    w, h = img.size

    # アスペクト比が9:16に近い場合はそのままリサイズ
    if abs(w / h - ow / oh) < 0.08:
        return img.resize((ow, oh), Image.LANCZOS)

    # ── 背景: coverスケール → ブラー → 暗化 ──────────────────
    scale_cover = max(ow / w, oh / h)
    bg_w = int(w * scale_cover)
    bg_h = int(h * scale_cover)
    bg = img.resize((bg_w, bg_h), Image.LANCZOS)
    bx = (bg_w - ow) // 2
    by = (bg_h - oh) // 2
    bg = bg.crop((bx, by, bx + ow, by + oh))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)   # 暗化して前景を引き立てる

    # ── 前景: containスケール（クロップなし）→ 中央配置 ──────
    scale_contain = min(ow / w, oh / h)
    fg_w = int(w * scale_contain)
    fg_h = int(h * scale_contain)
    fg = img.resize((fg_w, fg_h), Image.LANCZOS)

    canvas = bg.copy()
    x_off = (ow - fg_w) // 2
    y_off = (oh - fg_h) // 2
    canvas.paste(fg, (x_off, y_off))

    return canvas


def image_to_clip(path: str, duration: float) -> VideoFileClip | ImageClip:
    """HEIC/JPG → ImageClip（ブラー背景フィル・クロップなし）"""
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
        img = fit_to_vertical_blur_fill(img)   # ← ブラー背景フィル（旧: fit_to_vertical）
        arr = np.array(img)
        clip = ImageClip(arr, duration=duration)
        print(f"    🖼️  画像: ブラー背景フィル適用 ({Path(path).name})")
        return clip
    except Exception as e:
        print(f"  ⚠️  画像読み込みエラー {Path(path).name}: {e}")
        # 黒フレームで代替
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        return ImageClip(black, duration=duration)


def detect_face_center(img_arr: np.ndarray) -> tuple[int, int] | None:
    """
    BGRのnumpy配列から顔の中心座標(cx, cy)を返す。見つからなければNone。
    MediaPipe Face Mesh（468ランドマーク）を優先使用。
    未インストール or 検出失敗時はOpenCV Haar Cascadeにフォールバック。
    """
    h, w = img_arr.shape[:2]

    # ── MediaPipe Face Mesh（優先） ──────────────────────────
    if _MEDIAPIPE_AVAILABLE and _MP_FACE_MESH is not None:
        try:
            rgb = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)
            result = _MP_FACE_MESH.process(rgb)
            if result.multi_face_landmarks:
                lm = result.multi_face_landmarks[0].landmark
                # 全ランドマークの重心を顔中心とする
                cx = int(sum(p.x for p in lm) / len(lm) * w)
                cy = int(sum(p.y for p in lm) / len(lm) * h)
                return (cx, cy)
        except Exception:
            pass  # フォールバックへ

    # ── OpenCV Haar Cascade（フォールバック） ─────────────────
    gray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY)
    cascade = _get_face_cascade()
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
    if len(faces) == 0:
        return None
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


def crop_clip_to_vertical(clip: VideoFileClip, crop_x_percent: int = 50) -> VideoFileClip:
    """
    動画クリップを OUTPUT_SIZE(1080×1920) に変換。全アスペクト比に対応。
    crop_x_percent: Geminiが返す被写体中心のX位置（0=左端 50=中央 100=右端）
    """
    w, h = clip.size
    ratio = w / h
    target_ratio = OUTPUT_SIZE[0] / OUTPUT_SIZE[1]
    ow, oh = OUTPUT_SIZE

    if abs(ratio - target_ratio) < 0.08:
        return clip.resize((ow, oh))

    if ratio > target_ratio:
        # 9:16より横広い
        if ratio > LETTERBOX_THRESHOLD:
            # かなり横長 → 顔検出優先 → Gemini x% クロップ → レターボックス
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

            # Gemini の crop_x_percent で正確なX座標を計算
            new_w = int(h * target_ratio)
            subject_x = int(w * crop_x_percent / 100)  # 被写体の中心X座標
            x1 = max(0, min(subject_x - new_w // 2, w - new_w))
            return clip.crop(x1=x1, y1=0, x2=x1+new_w, y2=h).resize((ow, oh))
        else:
            # やや横広（3:4など）→ Geminiのx%でクロップ
            new_w = int(h * target_ratio)
            subject_x = int(w * crop_x_percent / 100)
            x1 = max(0, min(subject_x - new_w // 2, w - new_w))
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
                      gemini_key: str | None,
                      scene_text: str = "",
                      keep_audio: bool = False) -> VideoFileClip | ImageClip:
    """
    1つのクリップファイルを読み込み、縦型クロップ・ベストモーメント選定して返す。
    keep_audio=True: 元音声を保持（「ナレーションなし=元音声使用」モード用）。
                     Trueの場合はdurationを無視してクリップの自然尺を返す。
    """
    ext = Path(clip_path).suffix.lower()
    if ext in (".heic", ".jpeg", ".jpg", ".png", ".webp"):
        return image_to_clip(clip_path, duration)

    try:
        # ffmpegで向きを正規化してから読み込む（回転メタデータを焼き込み）
        normalized_path = normalize_video_orientation(clip_path)
        raw = VideoFileClip(normalized_path)
        if not keep_audio:
            raw = raw.set_audio(None)  # TTS音声を使う場合は元音声を剥ぎ取る

        crop_x_percent = 50  # デフォルト: 中央
        best_start = 0.0
        if gemini_key:
            analysis = analyze_clip_with_gemini(clip_path, gemini_key,
                                               scene_text=scene_text)
            crop_x_percent = int(analysis.get("crop_x_percent", 50))
            crop_x_percent = max(0, min(100, crop_x_percent))
            best_start = float(analysis.get("best_start_sec", 0))
            reason = analysis.get("reason", '')
            print(f"      🤖 Gemini: {analysis.get('subject','')} → x={crop_x_percent}% "
                  f"| 開始={best_start}s ({reason})")

        raw = crop_clip_to_vertical(raw, crop_x_percent=crop_x_percent)

        # keep_audio=True: 前処理済みの精密カット済みクリップ → 自然尺のまま返す
        if keep_audio:
            return raw  # トリム・ループなし。クリップ尺がそのままシーン尺になる

        # ベストモーメントから切り出し（先頭から使うのではなく感情的に最も訴える瞬間から）
        if best_start > 0 and raw.duration > duration:
            end_t = min(best_start + duration, raw.duration)
            start_t = max(0, end_t - duration)
            raw = raw.subclip(start_t, end_t)
        elif raw.duration > duration:
            raw = raw.subclip(0, duration)
        return raw
    except Exception as e:
        print(f"      ⚠️  動画読み込みエラー {Path(clip_path).name}: {e}")
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        return ImageClip(black, duration=duration)


def _fit_video_to_duration(base, target_duration: float):
    """
    映像クリップを target_duration に合わせる。
    - 映像が長ければ先頭からトリム
    - 映像が短ければループ（音声に映像を合わせる核心処理）
    """
    if base.duration >= target_duration:
        return base.subclip(0, target_duration)
    # 映像が短い → ループして目標尺に合わせる
    return vfx.loop(base, duration=target_duration)


def build_continuous_group_clip(
    group_scenes: list, group_audios: list, clips_dir: str,
    gemini_key: str | None = None,
    global_annotation: str = "",
    style: dict | None = None,
    total_scenes: int = 1,
) -> CompositeVideoClip | None:
    """
    連続同一素材グループを1本のクリップとして生成。
    - 1つの映像を流し続け、テロップだけ各シーンのタイミングで切り替わる
    - 各シーンの音声は時系列順に結合して映像に乗せる
    """
    total_dur = sum(d for _, d in group_audios)
    refs = group_scenes[0].clip_refs  # 先頭シーンの素材を使用（継続シーンは空のため）
    nos = [s.no for s in group_scenes]
    print(f"  🔗 グループ S{nos[0]:02d}〜S{nos[-1]:02d}: {total_dur:.1f}s 継続 refs={refs}")

    # 映像を総尺に合わせて読み込む
    found_clips: list[str] = []
    for ref in refs:
        p = find_clip(clips_dir, ref)
        if p:
            found_clips.append(p)

    if not found_clips:
        print(f"    ⚠️  グループ: クリップなし → 黒フレーム")
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        base = ImageClip(black, duration=total_dur)
    elif len(found_clips) == 1:
        print(f"    ✅ {Path(found_clips[0]).name}")
        group_text = " ".join(s.text for s in group_scenes if s.text)
        raw = _load_single_clip(found_clips[0], total_dur, gemini_key,
                                scene_text=group_text)
        base = _fit_video_to_duration(raw, total_dur)
    else:
        per_dur = total_dur / len(found_clips)
        group_text = " ".join(s.text for s in group_scenes if s.text)
        sub_clips = []
        for cp in found_clips:
            sc = _load_single_clip(cp, per_dur, gemini_key, scene_text=group_text)
            sub_clips.append(_fit_video_to_duration(sc, per_dur))
        base = concatenate_videoclips(sub_clips, method="compose")

    # 音声をシーン順に結合して映像に乗せる
    narration_dir = Path(group_audios[0][0]).parent if group_audios[0][0] else None
    if narration_dir:
        audio_clips = []
        for audio_path, _ in group_audios:
            if audio_path and Path(audio_path).exists():
                audio_clips.append(AudioFileClip(audio_path))
        if audio_clips:
            from moviepy.editor import concatenate_audioclips
            combined_audio = concatenate_audioclips(audio_clips)
            base = base.set_audio(combined_audio)

    s = style or {}
    telop_y      = s.get("telop_y_ratio", TELOP_Y_RATIO)
    font_size    = s.get("font_size", FONT_SIZE)
    font_emph    = s.get("font_emph_size", FONT_EMPH_SIZE)
    text_color   = s.get("telop_color")
    stroke_color = s.get("outline_color")

    layers = [base]

    # テロップを各シーンの開始時刻に合わせてタイムラインに配置
    t_offset = 0.0
    for scene, (_, audio_dur) in zip(group_scenes, group_audios):
        if scene.text:
            telop_arr = make_telop(scene.text, OUTPUT_SIZE, emphasis=scene.emphasis,
                                   telop_y_ratio=telop_y, font_size=font_size,
                                   font_emph_size=font_emph,
                                   text_color=text_color, stroke_color=stroke_color,
                                   scene_no=scene.no, total_scenes=total_scenes)
            telop_clip = (ImageClip(telop_arr, duration=audio_dur)
                         .set_opacity(1.0)
                         .set_start(t_offset))
            layers.append(telop_clip)
        t_offset += audio_dur

    # ① global_annotation を先に追加（全シーン共通・フルデュレーション）
    if global_annotation:
        ann_arr = make_annotation_overlay(global_annotation, OUTPUT_SIZE, y_start=24)
        layers.append(ImageClip(ann_arr, duration=total_dur).set_opacity(1.0))

    # ② scene.note を後から追加（global_annotationより上に描画される）
    t_offset = 0.0
    for scene, (_, audio_dur) in zip(group_scenes, group_audios):
        if scene.note:
            # global_annotationの行数を計算して、その下にnoteを配置
            import textwrap as _tw
            ann_lines = []
            for raw_line in global_annotation.split("\n"):
                ann_lines.extend(_tw.wrap(raw_line, width=ANNOT_CHARS_LINE) or [raw_line])
            note_y = 24 + (ANNOT_FONT_SIZE + 6) * max(len(ann_lines), 1) + 10
            note_arr = make_annotation_overlay(scene.note, OUTPUT_SIZE, y_start=note_y)
            note_clip = (ImageClip(note_arr, duration=audio_dur)
                        .set_opacity(1.0)
                        .set_start(t_offset))
            layers.append(note_clip)
        t_offset += audio_dur

    return CompositeVideoClip(layers, size=OUTPUT_SIZE)


def build_scene_clip(scene: Scene, clips_dir: str,
                     audio_path: str | None = None,
                     audio_duration: float | None = None,
                     override_duration: float | None = None,
                     gemini_key: str | None = None,
                     global_annotation: str = "",
                     style: dict | None = None,
                     total_scenes: int = 1,
                     keep_audio: bool = False) -> CompositeVideoClip | None:
    """
    1シーンのCompositeVideoClipを生成。
    audio_path/audio_duration が渡された場合（シーン単位TTS方式）:
      - 映像尺 = 音声尺（完全同期）
      - 音声をクリップに埋め込む
    keep_audio=True（元音声使用モード）:
      - クリップの自然尺を使用（TTS不使用）
      - 前処理で精密にカットされた音声付きクリップをそのまま使う
    渡されない場合（フォールバック）:
      - 文字数から尺を推定
    """
    # 尺の決定順: 音声実尺 > override_duration > 文字数推定
    # keep_audio=True の場合はクリップ読み込み後に自然尺を取得するため後回し
    if not keep_audio:
        if audio_duration is not None:
            duration = audio_duration
        elif override_duration is not None:
            duration = override_duration
        else:
            duration = max(MIN_DURATION, min(MAX_DURATION, len(scene.text) / CHARS_PER_SEC))
    else:
        duration = override_duration or MIN_DURATION  # 仮置き。後でクリップ実尺に上書き

    print(f"  シーン{scene.no}: 「{scene.text[:20]}...」 → {duration:.1f}s refs={scene.clip_refs}")

    found_clips: list[str] = []
    for ref in scene.clip_refs:
        p = find_clip(clips_dir, ref)
        if p:
            found_clips.append(p)

    if not found_clips:
        print(f"    ⚠️  シーン{scene.no}: クリップなし → 黒フレーム")
        black = np.zeros((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), dtype=np.uint8)
        base = ImageClip(black, duration=duration)
    elif len(found_clips) == 1:
        print(f"    ✅ {Path(found_clips[0]).name}")
        raw = _load_single_clip(found_clips[0], duration, gemini_key,
                                scene_text=scene.text, keep_audio=keep_audio)
        if keep_audio:
            # 元音声モード: クリップの自然尺をシーン尺として確定
            duration = max(MIN_DURATION, raw.duration)
            print(f"      🎙  元音声モード: 尺={duration:.2f}s（クリップ自然尺）")
            base = raw  # トリム不要（前処理で精密カット済み）
        else:
            base = _fit_video_to_duration(raw, duration)
    else:
        per_dur = duration / len(found_clips)
        print(f"    ✅ {len(found_clips)}クリップを等分 ({per_dur:.1f}s×{len(found_clips)})")
        sub_clips = []
        for cp in found_clips:
            print(f"      • {Path(cp).name}")
            sc = _load_single_clip(cp, per_dur, gemini_key, scene_text=scene.text)
            sub_clips.append(_fit_video_to_duration(sc, per_dur))
        base = concatenate_videoclips(sub_clips, method="compose")

    # 音声を映像に直接埋め込む（シーン単位TTS方式）
    if audio_path and Path(audio_path).exists():
        try:
            audio_clip = AudioFileClip(audio_path)
            base = base.set_audio(audio_clip)
        except Exception as e:
            print(f"    ⚠️  音声埋め込み失敗: {e}")

    layers = [base]

    # スタイル設定（参考動画から抽出 or デフォルト）
    s = style or {}
    telop_y      = s.get("telop_y_ratio", TELOP_Y_RATIO)
    font_size    = s.get("font_size", FONT_SIZE)
    font_emph    = s.get("font_emph_size", FONT_EMPH_SIZE)
    text_color   = s.get("telop_color")
    stroke_color = s.get("outline_color")

    if scene.text:
        telop_arr = make_telop(scene.text, OUTPUT_SIZE, emphasis=scene.emphasis,
                               telop_y_ratio=telop_y, font_size=font_size,
                               font_emph_size=font_emph,
                               text_color=text_color, stroke_color=stroke_color,
                               scene_no=scene.no, total_scenes=total_scenes)
        layers.append(ImageClip(telop_arr, duration=base.duration).set_opacity(1.0))

    # ① global_annotation を先に追加（下層）
    if global_annotation:
        ann_arr = make_annotation_overlay(global_annotation, OUTPUT_SIZE, y_start=24)
        layers.append(ImageClip(ann_arr, duration=base.duration).set_opacity(1.0))

    # ② scene.note を後から追加（global_annotationより上に描画）
    if scene.note:
        # global_annotationの実際の行数を計算してnote_yを決定
        import textwrap as _tw
        ann_lines = []
        for raw_line in global_annotation.split("\n"):
            ann_lines.extend(_tw.wrap(raw_line, width=ANNOT_CHARS_LINE) or [raw_line])
        note_y = 24 + (ANNOT_FONT_SIZE + 6) * max(len(ann_lines), 1) + 10
        note_arr = make_annotation_overlay(scene.note, OUTPUT_SIZE, y_start=note_y)
        layers.append(ImageClip(note_arr, duration=base.duration).set_opacity(1.0))

    return CompositeVideoClip(layers, size=OUTPUT_SIZE)


# ── メイン ────────────────────────────────────────────────
def analyze_reference_video(ref_path: str, gemini_key: str, ref_level: int = 2) -> dict:
    """
    参考動画からテロップスタイル + カットテンポを抽出。
    ref_level: 1=エッセンス（テロップ感だけ）, 2=スタイル踏襲（現状）, 3=完全トレース（カット秒数まで）
    返値例: {"font_size": 72, "telop_y_ratio": 0.75, "avg_cut_sec": 1.8, "tempo": "fast"}
    """
    level_names = {1: "エッセンス", 2: "スタイル踏襲", 3: "完全トレース"}
    print(f"\n🎬 参考動画解析中: {Path(ref_path).name} [反映Lv.{ref_level}: {level_names.get(ref_level, '?')}]")
    style = {}

    # === ① カットテンポ（ffmpeg scene detection）===
    try:
        result = subprocess.run(
            [FFMPEG, "-i", ref_path,
             "-vf", "select=gt(scene,0.3),showinfo",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=60
        )
        times = [float(m) for m in re.findall(r"pts_time:([\d.]+)", result.stderr)]
        dur_r = subprocess.run(
            [_FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", ref_path],
            capture_output=True, text=True
        )
        ref_dur = float(dur_r.stdout.strip()) if dur_r.stdout.strip() else None
        if len(times) >= 2 and ref_dur:
            all_points = [0.0] + sorted(times) + [ref_dur]
            intervals  = [all_points[i+1] - all_points[i] for i in range(len(all_points)-1)]
            avg_cut    = sum(intervals) / len(intervals)
            tempo      = "fast" if avg_cut < 2.0 else "medium" if avg_cut < 3.5 else "slow"
            style["avg_cut_sec"]  = round(avg_cut, 2)
            style["cut_count"]    = len(times) + 1
            style["ref_duration"] = round(ref_dur, 1)
            style["tempo"]        = tempo
            print(f"  ✂️  カットテンポ: 平均{avg_cut:.1f}s ({tempo}) / {len(times)+1}カット / 総尺{ref_dur:.1f}s")
        elif ref_dur:
            style["ref_duration"] = round(ref_dur, 1)
            print(f"  ℹ️  カット検出なし / 総尺: {ref_dur:.1f}s")
    except Exception as e:
        print(f"  ⚠️  カットテンポ解析失敗: {e}")

    # === ② 2段階Gemini分析：レイアウト構造 → スタイル変換 ===
    sample_frames = []
    for t in [5, 15, 25]:
        try:
            tmp = tempfile.mktemp(suffix=".jpg")
            subprocess.run(
                [FFMPEG, "-y", "-i", ref_path, "-ss", str(t), "-vframes", "1", tmp],
                capture_output=True, check=True
            )
            if os.path.exists(tmp):
                with open(tmp, "rb") as f:
                    sample_frames.append(base64.b64encode(f.read()).decode())
                os.unlink(tmp)
        except Exception:
            pass

    if not sample_frames:
        print("  ⚠️  参考動画フレーム取得失敗 → デフォルトスタイルを使用")
        return style

    # --- Step A: レイアウト構造 + テロップスタイルを意味的に解釈 ---
    # Geminiにピクセル単位で直接返させ、OUTPUT_SIZEに比例変換する
    layout_info = {}
    try:
        # 参考動画フレームの実寸を取得（比例変換用）
        ref_frame_h = 1920  # デフォルト
        try:
            probe = subprocess.run(
                [_FFPROBE, "-v", "quiet", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height",
                 "-of", "csv=p=0", ref_path],
                capture_output=True, text=True
            )
            parts = probe.stdout.strip().split(",")
            if len(parts) == 2:
                ref_frame_h = int(parts[1])
        except Exception:
            pass

        layout_prompt = (
            "この縦型動画のスクリーンショットを分析して、レイアウト構造とテロップスタイルをJSONで返して。\n\n"
            "===== fields =====\n"
            "layout_type: 以下から1つ選ぶ\n"
            "  'white_bars'      : 上下に白い（または色付きの）バーがあり映像と区切られている\n"
            "  'full_bleed'      : 映像が画面全体を占め、バーなし\n"
            "  'overlay'         : 映像上に半透明オーバーレイがある\n"
            "top_bar_percent     : 上部バーの高さ（全画面高さに対する%）。なしは0\n"
            "bottom_bar_percent  : 下部バーの高さ（%）。なしは0\n"
            "text_zone           : テロップがある領域\n"
            "  'top_bar' / 'bottom_bar' / 'upper_area' / 'center' / 'lower_third'\n\n"
            "telop_font_size_px  : テロップの文字の高さ（ピクセル推定値）。画像全体の高さを基準に推定\n"
            "telop_y_center_px   : テロップ中心のY座標（ピクセル推定値。画像上端=0）\n"
            "telop_color         : テキスト色（'#FFFFFF'形式）。不明はnull\n"
            "outline_color       : 縁取り色（'#000000'形式）。なしはnull\n"
            "has_text_bg         : テロップ背景（半透明帯やボックス）があるか (true/false)\n\n"
            "重要:\n"
            "- telop_font_size_pxとtelop_y_center_pxは、この画像の実ピクセルサイズに基づいて推定すること\n"
            "- white_barsの場合、テロップはバー内にあるので、バーの中でのY位置を返すこと\n"
            "JSON only。"
        )
        resp = _gemini_post({"contents": [{"parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": sample_frames[0]}},
            {"text": layout_prompt}
        ]}]}, timeout=15)
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r"```json|```", "", raw).strip()
        layout_info = json.loads(raw) or {}
        print(f"  🔍 レイアウト解析: {layout_info.get('layout_type','不明')} "
              f"| text_zone={layout_info.get('text_zone','?')} "
              f"| font={layout_info.get('telop_font_size_px','?')}px "
              f"| y={layout_info.get('telop_y_center_px','?')}px")
    except Exception as e:
        print(f"  ⚠️  レイアウト解析失敗: {e}")

    # --- Step B: レイアウト構造を考慮して OUTPUT_SIZE(1080x1920) 用スタイルに変換 ---
    OUT_W, OUT_H = OUTPUT_SIZE  # 1080, 1920
    layout_type = layout_info.get("layout_type", "full_bleed")

    # Geminiから返されたピクセル値を OUTPUT_SIZE に比例変換
    gemini_font_px = layout_info.get("telop_font_size_px")
    gemini_y_px    = layout_info.get("telop_y_center_px")
    scale_factor   = OUT_H / max(ref_frame_h, 1)

    if gemini_font_px and gemini_y_px:
        # 比例変換
        scaled_font = int(gemini_font_px * scale_factor)
        scaled_y    = gemini_y_px * scale_factor

        if layout_type == "white_bars":
            # 参考動画はバー内にテロップ → うちはfull_bleed
            # フォントサイズはそのまま使えるが、Y位置はバー位置を直接転用しない
            fs = max(50, min(90, scaled_font))
            style["font_size"]      = fs
            style["font_emph_size"] = max(60, min(100, int(fs * 1.15)))
            style["telop_y_ratio"]  = TELOP_Y_RATIO  # デフォルト安全域
            style["_layout_note"]   = (f"white_bars→full_bleed: font {gemini_font_px}px"
                                       f"×{scale_factor:.2f}={fs}px, Y=デフォルト{TELOP_Y_RATIO}")
        else:
            # full_bleed / overlay → 比例変換してそのまま使う
            fs = max(50, min(100, scaled_font))
            y_ratio = scaled_y / OUT_H
            style["font_size"]      = fs
            style["font_emph_size"] = max(60, min(120, int(fs * 1.15)))
            style["telop_y_ratio"]  = round(max(0.55, min(0.88, y_ratio)), 2)
            style["_layout_note"]   = (f"{layout_type}: font {gemini_font_px}px"
                                       f"×{scale_factor:.2f}={fs}px, "
                                       f"Y {gemini_y_px}px→{style['telop_y_ratio']}")
    else:
        # Geminiからピクセル値が取れなかった → デフォルト
        style["font_size"]      = FONT_SIZE
        style["font_emph_size"] = FONT_EMPH_SIZE
        style["telop_y_ratio"]  = TELOP_Y_RATIO
        style["_layout_note"]   = "Geminiピクセル値なし→デフォルト"

    # はみ出し安全チェック: テロップが画面外に出ないことを検証
    max_lines = 3  # 最大3行想定
    line_h = style["font_size"] + 10
    total_telop_h = line_h * max_lines
    telop_top = int(OUT_H * style["telop_y_ratio"]) - total_telop_h // 2
    telop_btm = telop_top + total_telop_h
    if telop_top < 20:
        # 上にはみ出る → Y位置を下げる
        style["telop_y_ratio"] = round((total_telop_h // 2 + 40) / OUT_H, 2)
        style["_layout_note"] += " | ⚠上はみ出し補正"
    if telop_btm > OUT_H - 40:
        # 下にはみ出る → Y位置を上げる
        style["telop_y_ratio"] = round((OUT_H - 40 - total_telop_h // 2) / OUT_H, 2)
        style["_layout_note"] += " | ⚠下はみ出し補正"

    # レベル1（エッセンス）: テロップスタイル詳細は使わない。カットテンポ + デフォルトスタイル
    if ref_level == 1:
        style["font_size"]      = FONT_SIZE
        style["font_emph_size"] = FONT_EMPH_SIZE
        style["telop_y_ratio"]  = TELOP_Y_RATIO
        style["_layout_note"]   = "Lv.1 エッセンス: テンポのみ参考、スタイルは独自"
        print(f"  ✅ Lv.1 エッセンス: テンポ情報のみ使用、テロップスタイルは独自デフォルト")
        return style

    # カラーはレイアウトを問わず転用（レベル2以上）
    if layout_info.get("telop_color"):
        style["telop_color"]  = layout_info["telop_color"]
    if layout_info.get("outline_color"):
        style["outline_color"] = layout_info["outline_color"]

    # レベル3（完全トレース）: 各カットの秒数リストを返す
    if ref_level == 3 and "cut_count" in style:
        style["_trace_mode"] = True
        print(f"  🎯 Lv.3 完全トレース: カット秒数まで再現")

    print(f"  ✅ スタイル変換完了: font={style.get('font_size')}px "
          f"y={style.get('telop_y_ratio')} | {style.get('_layout_note','')}")
    return style


def main():
    parser = argparse.ArgumentParser(description="編集AI v2")
    parser.add_argument("--script",   required=True, help="台本CSVまたはHTMLファイルパス")
    parser.add_argument("--clips",    required=True, help="素材フォルダパス")
    parser.add_argument("--output",   default="video-ai/output/output_v2.mp4", help="出力mp4パス")
    parser.add_argument("--no-ai",    action="store_true", help="AI API（Gemini/Fish Audio）を使わない")
    parser.add_argument("--remotion", action="store_true", help="Remotion用 composition.json も出力する")
    parser.add_argument("--voice",    default=None,
                        help="声カテゴリー（例: '女性・クール'）。未指定時はCSVまたはvoice_catalog.jsonのデフォルト")
    parser.add_argument("--ref-video", default=None,
                        help="参考動画パス。テロップスタイル（フォント・位置）を自動抽出して適用")
    parser.add_argument("--keep-audio", action="store_true",
                        help="元動画の音声をそのまま使う（TTS不使用）。"
                             "トーキングヘッド素材など、撮影済み音声を活かす場合に使用。"
                             "CSVのナレーション欄が「なし」の場合は自動適用。")
    parser.add_argument("--top-banner", default=None,
                        help="動画の上部に全編表示する固定テキスト（例: '18歳がラストチャンス'）")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    narration_dir = str(Path(args.output).parent / "narrations")

    # APIキー取得（os.environ優先 → ~/.zshrc 直接パース、シェル不起動）
    def _get_env(key):
        # 1. os.environ に既にあればそれを返す
        val = os.environ.get(key, "")
        if val:
            return val
        # 2. ~/.zshrc を直接テキスト解析（シェルを起動しない）
        try:
            zshrc = Path.home() / ".zshrc"
            if zshrc.exists():
                content = zshrc.read_text(encoding="utf-8", errors="replace")
                m = re.search(
                    rf'export\s+{re.escape(key)}=["\']?([^"\'\n]+)["\']?',
                    content
                )
                if m:
                    return m.group(1).strip()
        except Exception:
            pass
        return ""
    fish_key = _get_env("FISH_AUDIO_API_KEY") if not args.no_ai else None
    if not args.no_ai:
        global _GEMINI_KEY_MGR
        gemini_keys = [_get_env(f"GEMINI_API_KEY_{i}") for i in [1, 2, 3]]
        _GEMINI_KEY_MGR = GeminiKeyManager(gemini_keys)
        gemini_key = _GEMINI_KEY_MGR.current()
        print(f"  🔑 Gemini APIキー: {len(_GEMINI_KEY_MGR._keys)}本 読み込み済み")
    else:
        gemini_key = None

    # 台本パース
    print("\n📄 台本パース中...")
    csv_voice_category = None
    bgm_filename = None
    ref_level = 2  # デフォルト: スタイル踏襲
    narration_mode = "tts"  # デフォルト
    if args.script.lower().endswith(".csv"):
        scenes, global_annotation, csv_voice_category, bgm_filename, ref_level, narration_mode = parse_script_csv(args.script)
    else:
        scenes, global_annotation = parse_script(args.script)

    valid_scenes = [s for s in scenes if s.text or s.clip_refs]

    # 参考動画スタイル抽出
    style = {}
    if args.ref_video and gemini_key:
        style = analyze_reference_video(args.ref_video, gemini_key, ref_level=ref_level)

    # 声カテゴリー決定（CLI > CSV > デフォルト）
    effective_voice = args.voice or csv_voice_category

    # ナレーションモード決定（CLI --keep-audio > CSV ナレーション欄 > デフォルトTTS）
    use_original_audio = args.keep_audio or (narration_mode == "original")
    if use_original_audio:
        print("\n🎙  ナレーションモード: 元音声キープ（TTS不使用）")
        print("    前処理済みクリップの音声をそのまま使用します")

    # ─── シーン単位TTS（音声が映像尺を決定する） ─────────────────
    scene_audio: list[tuple[str | None, float]] = []
    if use_original_audio:
        # 元音声モード: TTSを生成しない。尺はクリップの自然尺を後で取得
        # ここではプレースホルダーとして (None, MIN_DURATION) を入れる
        # 実際の尺は build_scene_clip() 内でクリップ読み込み後に決定される
        scene_audio = [(None, MIN_DURATION)] * len(valid_scenes)
        print(f"  📹 {len(valid_scenes)}シーン分の音声尺はクリップ実尺から取得します")
    elif fish_key:
        print("\n🎙  Fish Audio: シーン別ナレーション生成中...")
        # 速度推定: テキスト文字数から60秒に収まる速度を計算
        tts_speed = estimate_tts_speed(valid_scenes)
        scene_audio = generate_scene_narrations(
            valid_scenes, fish_key, narration_dir,
            voice_category=effective_voice,
            tts_speed=tts_speed,
        )
    else:
        # AI無効時: 文字数から推定尺を使用
        for s in valid_scenes:
            dur = max(MIN_DURATION, min(MAX_DURATION, len(s.text) / CHARS_PER_SEC))
            scene_audio.append((None, dur))

    # ─── 連続同一素材シーンをグループ化 ──────────────────────────
    # 素材なし or 同じ素材IDの連続シーンは「1クリップを流し続ける」
    def group_continuous_scenes(scenes, scene_audio):
        groups = []  # [(scene_list, audio_list)]
        i = 0
        while i < len(scenes):
            group_s = [scenes[i]]
            group_a = [scene_audio[i]]
            j = i + 1
            while j < len(scenes):
                prev_refs = scenes[j-1].clip_refs
                curr_refs = scenes[j].clip_refs
                # 次が素材なし → 前の素材を継続
                # 次が前と同じ素材 → 継続
                if not curr_refs or curr_refs == prev_refs:
                    group_s.append(scenes[j])
                    group_a.append(scene_audio[j])
                    j += 1
                else:
                    break
            groups.append((group_s, group_a))
            i = j
        return groups

    scene_groups = group_continuous_scenes(valid_scenes, scene_audio)
    cont_count = sum(len(g[0]) - 1 for g in scene_groups if len(g[0]) > 1)
    if cont_count:
        print(f"\n  🔗 連続素材グループ: {cont_count}シーンを継続使用に統合")

    # ─── シーンクリップ生成（音声尺に映像を合わせる） ──────────────
    print(f"\n🎬 シーンクリップ生成中（{len(scene_groups)}グループ / {len(valid_scenes)}シーン）...")
    clips = []
    for group_scenes, group_audios in scene_groups:
        if len(group_scenes) == 1:
            # 通常: 1シーン1クリップ
            scene, (audio_path, audio_dur) = group_scenes[0], group_audios[0]
            c = build_scene_clip(
                scene, args.clips,
                audio_path=audio_path if not use_original_audio else None,
                audio_duration=audio_dur if not use_original_audio else None,
                gemini_key=gemini_key,
                global_annotation=global_annotation,
                style=style,
                total_scenes=len(valid_scenes),
                keep_audio=use_original_audio,
            )
        else:
            # 継続グループ: 複数シーンを1クリップで処理
            c = build_continuous_group_clip(
                group_scenes, group_audios, args.clips,
                gemini_key=gemini_key,
                global_annotation=global_annotation,
                style=style,
                total_scenes=len(valid_scenes),
            )
        for scene, (audio_path, audio_dur) in zip([group_scenes[0]], [group_audios[0]]):
            pass  # dummy loop for structure (actual processing above)
        if c is not None:
            clips.append(c)

    if not clips:
        print("❌ 有効なシーンがありません")
        sys.exit(1)

    total_sec = sum(c.duration for c in clips)
    print(f"\n✂️  {len(clips)}シーンを結合中... 総尺: {total_sec:.1f}s")
    final = concatenate_videoclips(clips, method="compose")

    # ─── BGMミックス ─────────────────────────────────────────
    if bgm_filename:
        # BGMファイルを検索（カレントディレクトリ相対 → clips → CSVと同じフォルダの順）
        bgm_path = None
        search_candidates = [
            Path(bgm_filename),                        # カレントディレクトリ相対（shortad-park/bgm/... 等）
            Path(args.clips) / bgm_filename,            # clipsフォルダ内
            Path(args.script).parent / bgm_filename,    # CSVと同じフォルダ
            Path("/Users/ca01224/Desktop/動画編集フォルダ/よく使う音楽素材") / bgm_filename,  # 社内BGMライブラリ
            Path(__file__).parent / bgm_filename,       # video-ai/ ディレクトリ
        ]
        for candidate in search_candidates:
            if candidate.exists():
                bgm_path = str(candidate)
                break
        if bgm_path:
            try:
                bgm_audio = AudioFileClip(bgm_path)
                # BGMを動画尺に合わせてループまたはトリム
                if bgm_audio.duration < total_sec:
                    bgm_audio = vfx.loop(bgm_audio, duration=total_sec)
                else:
                    bgm_audio = bgm_audio.subclip(0, total_sec)
                # BGM音量: 声の邪魔にならないよう10%固定
                bgm_audio = bgm_audio.volumex(0.10)
                # 既存音声（ナレーション）とBGMを合成
                if final.audio:
                    from moviepy.editor import CompositeAudioClip
                    mixed = CompositeAudioClip([final.audio, bgm_audio])
                    final = final.set_audio(mixed)
                else:
                    final = final.set_audio(bgm_audio)
                print(f"  🎵 BGMミックス: {bgm_filename} (vol=10%)")
            except Exception as e:
                print(f"  ⚠️  BGMミックス失敗: {e}")
        else:
            print(f"  ⚠️  BGMファイルが見つかりません: {bgm_filename}")

    # ─── 上部固定バナーオーバーレイ ─────────────────────────────
    if args.top_banner:
        banner_arr = make_top_banner(args.top_banner, OUTPUT_SIZE)
        banner_clip = ImageClip(banner_arr, duration=total_sec).set_opacity(1.0)
        audio_backup = final.audio
        final = CompositeVideoClip([final, banner_clip])
        if audio_backup:
            final = final.set_audio(audio_backup)
        print(f"  🏷  上部バナー: 「{args.top_banner}」")

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
    print(f"   ナレーション: シーン単位TTS同期方式（{narration_dir}/scene_XX.mp3）")
    if bgm_filename:
        print(f"   BGM: {bgm_filename}")

    # Remotion用 composition.json を出力（--remotion オプション時）
    if args.remotion:
        audio_durations = [d for _, d in scene_audio]
        _export_composition_json(valid_scenes, audio_durations, 1.0, None, args)


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
