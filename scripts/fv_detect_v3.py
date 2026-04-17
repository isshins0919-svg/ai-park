#!/usr/bin/env python3
"""fv_detect_v3.py — フレーム精度FVカット検出（ペアパターン方式）

ffmpegのsceneスコアで全フレームを解析。
FV切り替わりは「ペア（前FV最終フレーム＋次FV最初フレーム）」として検出される性質を活用。

手法:
  1. 全フレームのsceneスコアを取得
  2. 高スコアフレーム（局所ピーク）を検出
  3. ペア判定: 0.5-0.8秒間隔で隣接する2ピークを「ペア」として認識
  4. ペアの後半 = FV開始フレーム = カットポイント
  5. 単独ピーク（ペアにならなかった高スコア）もカット候補として採用
  6. expected_count ベースで最終選別
"""

import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


def get_scene_scores(video_path):
    tmpfile = tempfile.mktemp(suffix=".txt")
    subprocess.run(
        [FFMPEG, "-i", video_path,
         "-filter:v", "select='gte(scene,0)',metadata=print:file=" + tmpfile,
         "-vsync", "vfr", "-f", "null", "-"],
        capture_output=True, timeout=120
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


def find_all_peaks(frames, window=10, min_prominence=0.03):
    """周囲windowフレーム内で最大かつ突出度がmin_prominence以上のフレーム"""
    times = np.array([f[0] for f in frames])
    scores = np.array([f[1] for f in frames])
    n = len(scores)
    peaks = []
    for i in range(n):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        local = scores[lo:hi]
        if scores[i] >= np.max(local) and (scores[i] - np.median(local)) >= min_prominence:
            peaks.append((times[i], scores[i]))
    return peaks


def identify_cut_points(peaks, expected_cuts):
    """ペアパターン + 単独ピークからカットポイントを確定"""
    if not peaks:
        return []

    # Step 1: ペア候補を全列挙し、ペアスコア（合計）が高い順にマッチング
    pair_candidates = []
    for i in range(len(peaks) - 1):
        gap = peaks[i + 1][0] - peaks[i][0]
        if 0.3 <= gap <= 0.8:
            pair_candidates.append({
                "i": i, "j": i + 1,
                "cut_time": peaks[i + 1][0],
                "score": peaks[i + 1][1],
                "pair_score": peaks[i][1] + peaks[i + 1][1],
                "type": "pair",
            })

    # ペアスコアが高い順にマッチング（貪欲法）
    pair_candidates.sort(key=lambda x: -x["pair_score"])
    used = set()
    pairs = []
    for pc in pair_candidates:
        if pc["i"] not in used and pc["j"] not in used:
            pairs.append(pc)
            used.add(pc["i"])
            used.add(pc["j"])

    # Step 2: ペアにならなかった単独ピーク
    singles = []
    for i, (t, s) in enumerate(peaks):
        if i not in used:
            singles.append({
                "cut_time": t,
                "score": s,
                "pair_score": s,
                "type": "single",
            })

    # Step 3: 全候補をまとめてソート
    all_candidates = pairs + singles
    all_candidates.sort(key=lambda x: x["cut_time"])

    # Step 4: 近接候補のマージ（1.0秒以内は高スコア側を採用）
    merged = []
    for c in all_candidates:
        if merged and abs(c["cut_time"] - merged[-1]["cut_time"]) < 1.0:
            if c["pair_score"] > merged[-1]["pair_score"]:
                merged[-1] = c
        else:
            merged.append(c)

    # Step 5: expected_cuts 個を選ぶ
    if len(merged) > expected_cuts:
        # pair_score が高い順に選ぶ
        sorted_by_score = sorted(merged, key=lambda x: -x["pair_score"])
        selected = sorted_by_score[:expected_cuts]
        selected.sort(key=lambda x: x["cut_time"])
    else:
        selected = merged

    return selected


def detect_fv_cuts(video_path, expected_count=13):
    print(f"📹 Video: {video_path}")
    print(f"🎯 Expected: {expected_count} FVs ({expected_count - 1} cuts)")
    print()

    # Step 1
    print("Step 1: ffmpeg scene scores (全フレーム)...")
    frames = get_scene_scores(video_path)
    print(f"  → {len(frames)} frames")

    # Step 2
    print("Step 2: 局所ピーク検出...")
    peaks = find_all_peaks(frames, window=10, min_prominence=0.03)
    print(f"  → {len(peaks)} peaks")
    for t, s in peaks:
        print(f"    {t:.3f}s  score={s:.6f}")

    # Step 3
    target_cuts = expected_count - 1
    print(f"\nStep 3: ペアパターン解析 → {target_cuts}カット選択...")
    selected = identify_cut_points(peaks, target_cuts)
    print(f"  → {len(selected)} cuts identified")
    for c in selected:
        print(f"    {c['cut_time']:.3f}s  ({c['type']})  score={c['score']:.4f}")

    cut_points = [c["cut_time"] for c in selected]

    # 結果
    fps = len(frames) / float(subprocess.run(
        [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    ).stdout.strip())

    print(f"\n{'='*60}")
    print(f"検出結果: {len(cut_points)} カットポイント → {len(cut_points) + 1} FVs")
    print(f"{'='*60}")
    for i, t in enumerate(cut_points):
        frame_num = round(t * 30) % 30
        sec = int(t)
        print(f"  FV {i+1:2d} の終わり: {sec}秒{frame_num:02d}フレーム ({t:.3f}s)")

    # 正解照合
    ground_truth = [
        2 + 17/30, 5 + 6/30, 7 + 22/30, 10 + 25/30,
        13 + 25/30, 17 + 17/30, 21 + 7/30, 24 + 1/30,
        26 + 23/30, 28 + 22/30, 31 + 25/30, 35 + 0/30,
    ]

    print(f"\n{'='*60}")
    print("正解との照合 (goal: ±0.02s)")
    print(f"{'='*60}")
    all_pass = True
    max_err = 0
    for i, gt in enumerate(ground_truth):
        if i < len(cut_points):
            det = cut_points[i]
            err = det - gt
            max_err = max(max_err, abs(err))
            status = "✅" if abs(err) <= 0.02 else ("⚠️" if abs(err) <= 0.05 else "❌")
            if abs(err) > 0.02:
                all_pass = False
            print(f"  FV{i+1:2d}: 正解={gt:.3f}s  検出={det:.3f}s  誤差={err:+.4f}s  {status}")
        else:
            print(f"  FV{i+1:2d}: 正解={gt:.3f}s  未検出  ❌")
            all_pass = False

    print(f"\n  Max error: {max_err:.4f}s")
    print(f"  {'✅ ALL PASS' if all_pass else '❌ NEEDS TUNING'}")

    return {"cut_points": cut_points, "fv_count": len(cut_points) + 1}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--expected", "-n", type=int, default=13)
    args = parser.parse_args()
    detect_fv_cuts(args.video, args.expected)
