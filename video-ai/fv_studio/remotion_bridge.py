"""
こすりちゃん FV を Remotion でレンダリングするブリッジ。

既存 _build_fv_video (ffmpeg) と同じ I/F で呼べる _build_fv_video_remotion を提供する。
入力の caption_timeline は _build_caption_timeline_from_pattern の出力をそのまま受ける。

使い方:
    from fv_studio.remotion_bridge import build_fv_video_remotion
    build_fv_video_remotion(
        image_path=..., audio_path=..., caption_timeline=[...],
        fv_duration=6.0, motion_type="ultra_slow_zoom_in",
        output_path=Path("out.mp4"),
    )

MVP対応モーション (それ以外は static_no_motion にフォールバック):
  - ultra_slow_zoom_in / static_no_motion / flash_cut_zoom
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"
PUBLIC_DIR = REMOTION_DIR / "public"
SUPPORTED_MOTIONS = {"ultra_slow_zoom_in", "static_no_motion", "flash_cut_zoom"}


def _stage_asset(src: Path, prefix: str) -> str:
    """src を remotion/public/<uuid>.<ext> にコピーし、public内相対名を返す。"""
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    ext = src.suffix or ""
    staged_name = f"{prefix}_{uuid.uuid4().hex[:10]}{ext}"
    dst = PUBLIC_DIR / staged_name
    shutil.copyfile(src, dst)
    return staged_name


def _normalize_motion(motion_type: str) -> str:
    return motion_type if motion_type in SUPPORTED_MOTIONS else "static_no_motion"


def _build_composition_spec(
    image_path: Path,
    audio_path: Path,
    caption_timeline: list[dict[str, Any]],
    fv_duration: float,
    motion_type: str,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
) -> dict[str, Any]:
    """caption_timeline (app.py の schema) → composition.json の schema へ変換。

    caption_timeline は既に { start, end, layers: [{ text, placement, size, style, emphasis_words }] } 形。
    そのまま captions として渡せる。
    """
    captions = []
    for seg in caption_timeline:
        layers = []
        for layer in seg.get("layers", []):
            layers.append({
                "text": layer.get("text", ""),
                "placement": layer.get("placement", "kick_bottom"),
                "size": layer.get("size", "xl"),
                "style": layer.get("style", "double_stroke"),
                "emphasis_words": layer.get("emphasis_words", []) or [],
            })
        captions.append({
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "layers": layers,
        })

    # 画像/音声を remotion/public/ にstaging (Remotionの staticFile で参照する)
    staged_image = _stage_asset(Path(image_path), "img")
    staged_audio = _stage_asset(Path(audio_path), "aud") if audio_path else None

    return {
        "fps": fps,
        "width": width,
        "height": height,
        "image": staged_image,
        "audio": staged_audio,
        "duration_sec": float(fv_duration),
        "motion": _normalize_motion(motion_type),
        "captions": captions,
    }


def _write_composition_json(spec: dict[str, Any], target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "composition.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_fv_video_remotion(
    image_path: Path,
    audio_path: Path,
    caption_timeline: list[dict[str, Any]],
    fv_duration: float,
    motion_type: str,
    output_path: Path,
    *,
    keep_composition_json: bool = True,
) -> bool:
    """_build_fv_video の Remotion 版。成功で True を返す。

    composition.json は output_path と同じディレクトリに書き出す (デバッグ容易化)。
    npx remotion render を COMPOSITION_JSON env 経由で呼ぶ。
    """
    image_path = Path(image_path)
    audio_path = Path(audio_path) if audio_path else None
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spec = _build_composition_spec(
        image_path=image_path,
        audio_path=audio_path,
        caption_timeline=caption_timeline,
        fv_duration=fv_duration,
        motion_type=motion_type,
    )

    comp_json = _write_composition_json(spec, output_path.parent)

    env = os.environ.copy()

    cmd = [
        "npx", "remotion", "render",
        "src/index.ts",
        "KosuriFV",
        str(output_path.resolve()),
        f"--props={comp_json.resolve()}",
        "--codec=h264",
        "--overwrite",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print(f"[remotion_bridge] timeout rendering {output_path}")
        return False
    except FileNotFoundError:
        print("[remotion_bridge] npx not found. Install Node.js first.")
        return False

    if result.returncode != 0:
        print("[remotion_bridge] render failed:")
        print("STDOUT:", result.stdout[-2000:])
        print("STDERR:", result.stderr[-2000:])
        return False

    # staged assetsは public/ に残しておく (デバッグ用)。
    # 必要ならここでクリーンアップ可能。

    if not keep_composition_json:
        try:
            comp_json.unlink()
        except OSError:
            pass

    return output_path.exists() and output_path.stat().st_size > 0


# 既存 _build_fv_video と同じ snake_case でもエクスポート
_build_fv_video_remotion = build_fv_video_remotion
