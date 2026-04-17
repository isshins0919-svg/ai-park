#!/usr/bin/env python3
"""
index_materials.py — さくら撮影素材のインデックス生成

使い方:
    python3 index_materials.py <raw_dir> [--output <path>]

例:
    python3 index_materials.py ~/Desktop/sakura_raw_2026-04-11
    python3 index_materials.py ./raw --output ./materials.json

命名規則:
    script{N}_take{M}.mov              — 台本N、テイクM
    script{N}_{angle}_take{M}.mov      — 画角バリエーション付き
    例: script1_a_take2.mov (a=後ろ姿)

出力: materials.json
    各ファイルのメタデータ (長さ・解像度・音量・orientation) をJSON化
"""

import os, sys, json, re, subprocess, argparse
from pathlib import Path
from datetime import datetime

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

ANGLE_MAP = {
    "a": "後ろ姿",
    "b": "首下バスト",
    "c": "手元・口元",
    "d": "横顔シルエット",
    "e": "その他",
}

VIDEO_EXTS = (".mov", ".mp4", ".m4v", ".MOV", ".MP4")


def parse_filename(name: str) -> dict:
    """ファイル名から script_id / angle / take をパース"""
    stem = Path(name).stem
    # script1_a_take2 or script1_take2
    m = re.match(r"script(\d+)(?:_([a-z]))?_take(\d+)", stem)
    if not m:
        return {"script_id": None, "angle": None, "take": None, "valid": False}
    script_id = int(m.group(1))
    angle_code = m.group(2)
    take = int(m.group(3))
    return {
        "script_id": script_id,
        "angle_code": angle_code,
        "angle": ANGLE_MAP.get(angle_code, "デフォルト") if angle_code else "デフォルト",
        "take": take,
        "valid": True,
    }


def ffprobe_metadata(path: Path) -> dict:
    """ffprobeで動画メタデータを取得"""
    try:
        cmd = [
            FFPROBE, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)

        duration = float(data.get("format", {}).get("duration", 0))
        size_bytes = int(data.get("format", {}).get("size", 0))

        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)

        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0

        # rotation detection
        rotation = 0
        if video_stream:
            tags = video_stream.get("tags", {})
            if "rotate" in tags:
                rotation = int(tags["rotate"])
            for sd in video_stream.get("side_data_list", []) or []:
                if sd.get("side_data_type") == "Display Matrix":
                    rotation = int(sd.get("rotation", 0))

        # 実際の向き（rotation考慮）
        if abs(rotation) in (90, 270):
            display_w, display_h = height, width
        else:
            display_w, display_h = width, height

        orientation = "vertical" if display_h > display_w else "horizontal"

        return {
            "duration_sec": round(duration, 2),
            "size_mb": round(size_bytes / 1_000_000, 2),
            "resolution": f"{display_w}x{display_h}",
            "width": display_w,
            "height": display_h,
            "rotation": rotation,
            "orientation": orientation,
            "has_audio": audio_stream is not None,
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        }
    except Exception as e:
        return {"error": str(e)}


def measure_volume(path: Path) -> dict:
    """FFmpegで音量レベル測定"""
    try:
        cmd = [
            FFMPEG, "-i", str(path),
            "-af", "volumedetect",
            "-f", "null", "-",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stderr

        mean_db = None
        max_db = None
        for line in output.splitlines():
            if "mean_volume:" in line:
                m = re.search(r"mean_volume:\s*(-?[\d.]+)", line)
                if m:
                    mean_db = float(m.group(1))
            elif "max_volume:" in line:
                m = re.search(r"max_volume:\s*(-?[\d.]+)", line)
                if m:
                    max_db = float(m.group(1))

        return {
            "mean_volume_db": mean_db,
            "max_volume_db": max_db,
        }
    except Exception as e:
        return {"error": str(e)}


def index_directory(raw_dir: Path) -> dict:
    """ディレクトリをスキャンして素材インデックスを作成"""
    if not raw_dir.exists():
        raise FileNotFoundError(f"Directory not found: {raw_dir}")

    materials = []
    invalid = []

    video_files = sorted([f for f in raw_dir.iterdir() if f.suffix in VIDEO_EXTS])
    print(f"Found {len(video_files)} video files in {raw_dir}")

    for i, f in enumerate(video_files, 1):
        print(f"  [{i}/{len(video_files)}] {f.name}...", end=" ", flush=True)

        parsed = parse_filename(f.name)
        if not parsed["valid"]:
            print("INVALID NAME")
            invalid.append({"file": f.name, "reason": "filename does not match script{N}_take{M} pattern"})
            continue

        meta = ffprobe_metadata(f)
        vol = measure_volume(f)

        entry = {
            "file": f.name,
            "path": str(f.absolute()),
            "script_id": parsed["script_id"],
            "angle_code": parsed["angle_code"],
            "angle": parsed["angle"],
            "take": parsed["take"],
            **meta,
            **vol,
        }
        materials.append(entry)
        print(f"OK ({meta.get('duration_sec', '?')}s, {vol.get('mean_volume_db', '?')}dB)")

    # script_id, take でソート
    materials.sort(key=lambda x: (x.get("script_id") or 999, x.get("take") or 999))

    return {
        "session_date": datetime.now().strftime("%Y-%m-%d"),
        "indexed_at": datetime.now().isoformat(),
        "raw_dir": str(raw_dir),
        "total_files": len(video_files),
        "valid_count": len(materials),
        "invalid_count": len(invalid),
        "materials": materials,
        "invalid": invalid,
    }


def main():
    parser = argparse.ArgumentParser(description="さくら撮影素材インデックス生成")
    parser.add_argument("raw_dir", type=str, help="撮影素材が入ってるディレクトリ")
    parser.add_argument("--output", "-o", type=str, default=None, help="出力先JSON (default: <raw_dir>/../materials.json)")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir).expanduser().resolve()

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        # デフォルト: video-ai/sakura/sessions/{date}/materials.json
        session_date = datetime.now().strftime("%Y-%m-%d")
        output_path = Path(__file__).parent.parent / "sessions" / session_date / "materials.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n=== さくら素材インデックス生成 ===")
    print(f"Raw dir: {raw_dir}")
    print(f"Output: {output_path}\n")

    index = index_directory(raw_dir)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"Valid: {index['valid_count']}")
    print(f"Invalid: {index['invalid_count']}")
    print(f"Output: {output_path}")

    # サマリー
    by_script = {}
    for m in index["materials"]:
        sid = m["script_id"]
        by_script.setdefault(sid, []).append(m)

    print(f"\n=== Script別サマリー ===")
    for sid in sorted(by_script.keys()):
        takes = by_script[sid]
        print(f"  Script #{sid}: {len(takes)} takes")


if __name__ == "__main__":
    main()
