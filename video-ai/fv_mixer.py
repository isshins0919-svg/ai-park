#!/usr/bin/env python3
"""FV差し替え + BGMミキサー + FV自動分割

フォルダに素材を入れて実行 → FVバリエーション × BGM音量パターンの動画を一括生成。
連結されたFV動画は --split-fv オプションで自動分割可能。

使い方:
  # 通常モード（FV個別ファイル）
  python3 video-ai/fv_mixer.py --input-dir "/path/to/FV+BODY+MP3"

  # FV自動分割モード（連結FV → 自動カット → ミックス）
  python3 video-ai/fv_mixer.py --input-dir "/path/to/FV+BODY+MP3" --split-fv 13

フォルダ構成:
  input-dir/
    ├── FV映像/          ← FV動画を複数本 or 連結FV動画1本
    │   ├── fv_01.mp4    （個別モード）
    │   └── fv_02.mp4
    │   -- or --
    │   └── FV複数パターン.mp4  （連結モード: --split-fv N で自動分割）
    ├── ベースの映像.mp4  ← ベース動画1本
    └── 背景音楽.MP3      ← BGM 1本
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import numpy as np

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

BGM_VOLUMES = {"low": 0.20, "mid": 0.40}

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".ogg"}


# ═══════════════════════════════════════════════════════════
#  FV自動分割（ペアパターン方式 — フレーム精度）
# ═══════════════════════════════════════════════════════════

def _get_scene_scores(video_path: str) -> list[tuple[float, float]]:
    """ffmpeg scene filterで全フレームのシーン変化スコアを取得"""
    tmpfile = tempfile.mktemp(suffix=".txt")
    subprocess.run(
        [FFMPEG, "-i", video_path,
         "-filter:v", "select='gte(scene,0)',metadata=print:file=" + tmpfile,
         "-vsync", "vfr", "-f", "null", "-"],
        capture_output=True, timeout=300
    )
    frames = []
    current_pts = None
    for line in open(tmpfile).readlines():
        pts_match = re.search(r'pts_time:([\d.]+)', line)
        score_match = re.search(r'scene_score=([\d.]+)', line)
        if pts_match:
            current_pts = float(pts_match.group(1))
        if score_match and current_pts is not None:
            frames.append((current_pts, float(score_match.group(1))))
            current_pts = None
    os.unlink(tmpfile)
    return frames


def _find_peaks(frames: list, window: int = 10, min_prominence: float = 0.03):
    """局所ピーク検出"""
    scores = np.array([f[1] for f in frames])
    n = len(scores)
    peaks = []
    for i in range(n):
        lo, hi = max(0, i - window), min(n, i + window + 1)
        local = scores[lo:hi]
        if scores[i] >= np.max(local) and (scores[i] - np.median(local)) >= min_prominence:
            peaks.append((frames[i][0], scores[i]))
    return peaks


def _identify_cuts(peaks: list, expected_cuts: int) -> list[float]:
    """ハイブリッド方式: ペアパターン + スマートスコア選択 (v5)

    ペア内スコア比でカットポイント選択を切り替える:
    - スコア比 > 3:1 → 高スコア側を選択（cut + noise パターン）
    - スコア比 <= 3:1 → 後方ピークを選択（true pair パターン）
    """
    if not peaks:
        return []

    # ペア候補を全列挙（0.3-0.8秒間隔の隣接ピーク）
    pair_candidates = []
    for i in range(len(peaks) - 1):
        gap = peaks[i + 1][0] - peaks[i][0]
        if 0.3 <= gap <= 0.8:
            s1, s2 = peaks[i][1], peaks[i + 1][1]
            ratio = max(s1, s2) / max(min(s1, s2), 1e-9)
            if ratio > 3:
                cut_idx = i if s1 > s2 else i + 1
            else:
                cut_idx = i + 1
            pair_candidates.append({
                "i": i, "j": i + 1,
                "cut_time": peaks[cut_idx][0],
                "pair_score": s1 + s2,
                "type": "pair",
            })

    # 貪欲法: ペアスコアが高い順にマッチング
    pair_candidates.sort(key=lambda x: -x["pair_score"])
    used = set()
    cuts = []
    for pc in pair_candidates:
        if pc["i"] not in used and pc["j"] not in used:
            cuts.append(pc)
            used.add(pc["i"])
            used.add(pc["j"])

    # 単独ピーク（ペアにならなかったもの）
    for i, (t, s) in enumerate(peaks):
        if i not in used:
            cuts.append({"cut_time": t, "pair_score": s, "type": "single"})

    # 時系列でソート → 近接マージ
    cuts.sort(key=lambda x: x["cut_time"])
    merged = []
    for c in cuts:
        if merged and abs(c["cut_time"] - merged[-1]["cut_time"]) < 1.0:
            if c["pair_score"] > merged[-1]["pair_score"]:
                merged[-1] = c
        else:
            merged.append(c)

    # expected_cuts 個を選択
    if len(merged) > expected_cuts:
        top = sorted(merged, key=lambda x: -x["pair_score"])[:expected_cuts]
        top.sort(key=lambda x: x["cut_time"])
        return [c["cut_time"] for c in top]
    return [c["cut_time"] for c in merged]


def split_fv_video(combined_video: str, output_dir: str, expected_count: int) -> list[Path]:
    """連結FV動画を自動分割して個別ファイルに出力。
    Returns: 分割されたFVファイルパスのリスト
    """
    print(f"  🔪 FV自動分割: {Path(combined_video).name} → {expected_count}本")

    # Step 1: sceneスコア取得
    frames = _get_scene_scores(combined_video)
    print(f"    → {len(frames)} frames analyzed")

    # Step 2: ピーク検出
    peaks = _find_peaks(frames)
    print(f"    → {len(peaks)} peaks detected")

    # Step 3: カットポイント特定
    cut_points = _identify_cuts(peaks, expected_count - 1)
    print(f"    → {len(cut_points)} cut points identified")

    if len(cut_points) != expected_count - 1:
        print(f"    ⚠️ 期待{expected_count - 1}カットに対し{len(cut_points)}カット検出")

    # Step 4: ffmpegで分割
    duration = get_duration(combined_video)
    segments = []
    starts = [0.0] + cut_points
    ends = cut_points + [duration]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_files = []

    for i, (start, end) in enumerate(zip(starts, ends)):
        out_path = out_dir / f"fv_{i+1:02d}.mp4"
        dur = end - start
        # 再エンコード方式: フレーム精度で分割（-c copy だとキーフレームのずれが発生する）
        ffmpeg_run(
            "-ss", f"{start:.6f}",
            "-i", combined_video,
            "-t", f"{dur:.6f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            str(out_path),
            check=False,
        )
        if out_path.exists():
            actual_dur = get_duration(str(out_path))
            print(f"    FV{i+1:2d}: {start:.3f}s → {end:.3f}s ({actual_dur:.2f}s) ✅")
            output_files.append(out_path)
        else:
            print(f"    FV{i+1:2d}: FAILED ❌")

    print(f"  → {len(output_files)}/{expected_count} FVs extracted")
    return output_files


# ═══════════════════════════════════════════════════════════
#  FV Mixer コア機能
# ═══════════════════════════════════════════════════════════

def ffmpeg_run(*args, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [FFMPEG, "-y"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_duration(path: str) -> float:
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def detect_materials(input_dir: Path) -> tuple[Path, list[Path], Path]:
    """素材を自動検出。(ベース動画, FV映像リスト, BGMパス) を返す。"""
    base_video = None
    fv_clips = []
    bgm_file = None

    # FV映像: サブフォルダ内の動画
    fv_dirs = [d for d in input_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    for fv_dir in fv_dirs:
        for f in sorted(fv_dir.iterdir()):
            if f.suffix.lower() in VIDEO_EXTENSIONS and not f.name.startswith("."):
                fv_clips.append(f)

    # ベース動画: input_dir直下の動画ファイル
    # BGM: input_dir直下の音声ファイル
    for f in sorted(input_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            if f.suffix.lower() in VIDEO_EXTENSIONS:
                base_video = f
            elif f.suffix.lower() in AUDIO_EXTENSIONS:
                bgm_file = f

    if not base_video:
        sys.exit("  ベース動画が見つかりません。input-dir直下に動画ファイルを置いてください。")
    if not fv_clips:
        sys.exit("  FV映像が見つかりません。サブフォルダに動画ファイルを置いてください。")
    if not bgm_file:
        sys.exit("  BGMが見つかりません。input-dir直下に音声ファイルを置いてください。")

    return base_video, fv_clips, bgm_file


def mix_fv(
    base_path: Path,
    fv_path: Path,
    bgm_path: Path,
    output_path: Path,
    bgm_volume: float,
    base_dur: float,
    fv_dur: float,
) -> bool:
    """1本のFV + ベース + BGM → 1本の完成動画を生成。"""
    filter_complex = (
        # FV映像をベースと同じ解像度にスケール
        f"[1:v]setpts=PTS-STARTPTS,"
        f"scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2[fv];"
        # FV映像をベースの上にoverlay（FV終了後は自然にベースが見える）
        f"[0:v][fv]overlay=0:0:eof_action=pass[vout];"
        # BGMをベース動画の長さにカット + 音量調整
        f"[2:a]atrim=0:{base_dur:.6f},asetpts=PTS-STARTPTS,volume={bgm_volume}[bgm];"
        # ベース音声 + BGM をミックス
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]"
    )

    try:
        ffmpeg_run(
            "-i", str(base_path),
            "-i", str(fv_path),
            "-i", str(bgm_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ffmpeg error: {e.stderr[-500:]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="FV差し替え + BGMミキサー + FV自動分割")
    parser.add_argument(
        "--input-dir", type=str, required=True,
        help="素材フォルダのパス（ベース動画/FV映像/BGMを含む）",
    )
    parser.add_argument(
        "--split-fv", type=int, default=0,
        help="連結FV動画を自動分割するFV本数（例: --split-fv 13）",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        sys.exit(f"  フォルダが見つかりません: {input_dir}")

    print(f"\n  FV Mixer v2.0 {'+ FV Auto-Split' if args.split_fv else ''}")
    print(f"  {'=' * 40}")

    # --split-fv: 連結FV動画を自動分割
    if args.split_fv > 0:
        fv_dirs = [d for d in input_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        combined_fv = None
        for fv_dir in fv_dirs:
            videos = [f for f in sorted(fv_dir.iterdir())
                      if f.suffix.lower() in VIDEO_EXTENSIONS and not f.name.startswith(".")]
            if len(videos) == 1:
                combined_fv = videos[0]
                split_output_dir = fv_dir
                break

        if combined_fv:
            split_files = split_fv_video(
                str(combined_fv), str(split_output_dir), args.split_fv
            )
            if not split_files:
                sys.exit("  FV自動分割に失敗しました")
            print()

    # 素材検出
    base_video, fv_clips, bgm_file = detect_materials(input_dir)

    base_dur = get_duration(str(base_video))
    print(f"  ベース動画: {base_video.name} ({base_dur:.1f}s)")
    print(f"  FV映像: {len(fv_clips)}本")
    print(f"  BGM: {bgm_file.name}")

    # FV秒数を事前取得
    fv_durations = {}
    for fv in fv_clips:
        fv_durations[fv] = get_duration(str(fv))
        print(f"    {fv.name}: {fv_durations[fv]:.2f}s")

    # 出力先
    output_dir = input_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成ループ
    total = len(fv_clips) * len(BGM_VOLUMES)
    success = 0
    start_time = time.time()

    print(f"\n  {total}本の動画を生成します...")
    print(f"  {'=' * 40}")

    for i, fv in enumerate(fv_clips, 1):
        fv_dur = fv_durations[fv]
        fv_label = f"FV{i}"

        for vol_name, vol_value in BGM_VOLUMES.items():
            output_name = f"{fv_label}_bgm-{vol_name}.mp4"
            output_path = output_dir / output_name

            print(f"  [{success + 1}/{total}] {output_name} ...", end=" ", flush=True)

            ok = mix_fv(
                base_path=base_video,
                fv_path=fv,
                bgm_path=bgm_file,
                output_path=output_path,
                bgm_volume=vol_value,
                base_dur=base_dur,
                fv_dur=fv_dur,
            )

            if ok:
                success += 1
                out_dur = get_duration(str(output_path))
                print(f"done ({out_dur:.1f}s)")
            else:
                print("FAILED")

    elapsed = time.time() - start_time
    print(f"\n  {'=' * 40}")
    print(f"  {success}/{total} 完了 ({elapsed:.0f}秒)")
    print(f"  出力先: {output_dir}")


if __name__ == "__main__":
    main()
