#!/usr/bin/env python3
"""fv_detect_v5.py — 汎用FVカット検出（グループ化方式）

v3のペアパターン方式を廃止。
近接ピークをグループ化し、グループ内最高スコアをカットポイントとする汎用アルゴリズム。

手法:
  1. 全フレームのsceneスコアを取得
  2. 局所ピーク検出（adaptive threshold対応）
  3. 近接ピーク（merge_window秒以内）をグループ化 → 最高スコアを代表に
  4. expected_count ベースでスコア上位を選択
"""

import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


def get_scene_scores(video_path):
    """ffmpegで全フレームのsceneスコアを取得"""
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


def find_peaks(frames, window=10, min_prominence=0.03):
    """局所ピーク検出: 周囲windowフレーム内で最大かつ突出度がmin_prominence以上"""
    times = np.array([f[0] for f in frames])
    scores = np.array([f[1] for f in frames])
    n = len(scores)
    peaks = []
    for i in range(n):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        local = scores[lo:hi]
        if scores[i] >= np.max(local) and (scores[i] - np.median(local)) >= min_prominence:
            peaks.append({"time": times[i], "score": float(scores[i])})
    return peaks


def identify_cut_points(peaks, expected_cuts):
    """ハイブリッド方式: ペアパターン + スマートスコア選択

    v3のペアパターン（0.3-0.8秒間隔の隣接ピーク）を検出しつつ、
    ペア内のスコア比でカットポイント選択を切り替える:
    - スコア比 > 3:1 → 高スコア側を選択（cut + noise パターン）
    - スコア比 <= 3:1 → 後方ピークを選択（v3互換、true pair パターン）
    """
    if not peaks:
        return []

    # Step 1: ペア候補を列挙
    pair_candidates = []
    for i in range(len(peaks) - 1):
        gap = peaks[i + 1]["time"] - peaks[i]["time"]
        if 0.3 <= gap <= 0.8:
            s1, s2 = peaks[i]["score"], peaks[i + 1]["score"]
            ratio = max(s1, s2) / max(min(s1, s2), 1e-9)
            # スコア比が大きい → 高スコア側がカット
            # スコア比が小さい → 後方がカット（v3互換）
            if ratio > 3:
                cut_idx = i if s1 > s2 else i + 1
            else:
                cut_idx = i + 1
            pair_candidates.append({
                "i": i, "j": i + 1,
                "cut_time": peaks[cut_idx]["time"],
                "score": peaks[cut_idx]["score"],
                "pair_score": s1 + s2,
                "type": "pair",
                "ratio": ratio,
            })

    # 貪欲法でペアをマッチング（pair_score降順）
    pair_candidates.sort(key=lambda x: -x["pair_score"])
    used = set()
    pairs = []
    for pc in pair_candidates:
        if pc["i"] not in used and pc["j"] not in used:
            pairs.append(pc)
            used.add(pc["i"])
            used.add(pc["j"])

    # Step 2: 単独ピーク
    singles = []
    for i, p in enumerate(peaks):
        if i not in used:
            singles.append({
                "cut_time": p["time"],
                "score": p["score"],
                "pair_score": p["score"],
                "type": "single",
            })

    # Step 3: 全候補をまとめてソート
    all_candidates = pairs + singles
    all_candidates.sort(key=lambda x: x["cut_time"])

    # Step 4: 近接マージ（1.0秒以内は高pair_score側を採用）
    merged = []
    for c in all_candidates:
        if merged and abs(c["cut_time"] - merged[-1]["cut_time"]) < 1.0:
            if c["pair_score"] > merged[-1]["pair_score"]:
                merged[-1] = c
        else:
            merged.append(c)

    # Step 5: expected_cuts 個を選ぶ（pair_score降順）
    if len(merged) > expected_cuts:
        sorted_by_score = sorted(merged, key=lambda x: -x["pair_score"])
        selected = sorted_by_score[:expected_cuts]
        selected.sort(key=lambda x: x["cut_time"])
    else:
        selected = merged

    return [{"cut_time": c["cut_time"], "score": c["score"],
             "group_size": 1, "type": c["type"]} for c in selected]


def detect_fv_cuts(video_path, expected_count, verbose=True):
    """FVカットを検出して結果を返す"""
    if verbose:
        print(f"📹 Video: {video_path}")
        print(f"🎯 Expected: {expected_count} FVs ({expected_count - 1} cuts)")
        print()

    # Step 1: scene scores
    if verbose:
        print("Step 1: ffmpeg scene scores...")
    frames = get_scene_scores(video_path)
    if verbose:
        print(f"  → {len(frames)} frames")

    # Step 2: peak detection
    if verbose:
        print("Step 2: 局所ピーク検出...")
    peaks = find_peaks(frames, window=10, min_prominence=0.03)
    if verbose:
        print(f"  → {len(peaks)} peaks")
        for p in peaks:
            marker = " ★" if p["score"] > 0.3 else ""
            print(f"    {p['time']:.3f}s  score={p['score']:.6f}{marker}")

    # Step 3: group and select
    target_cuts = expected_count - 1
    if verbose:
        print(f"\nStep 3: グループ化 + 上位{target_cuts}選択...")
    selected = identify_cut_points(peaks, target_cuts)
    if verbose:
        print(f"  → {len(selected)} cuts")
        for c in selected:
            print(f"    {c['cut_time']:.3f}s  score={c['score']:.4f}  (group={c['group_size']})")

    cut_points = [c["cut_time"] for c in selected]

    if verbose:
        print(f"\n{'='*60}")
        print(f"検出結果: {len(cut_points)} カットポイント → {len(cut_points) + 1} FVs")
        print(f"{'='*60}")
        for i, t in enumerate(cut_points):
            print(f"  Cut {i+1:2d}: {t:.3f}s")

    return {"cut_points": cut_points, "fv_count": len(cut_points) + 1}


def evaluate(cut_points, ground_truth, tolerance=0.1, verbose=True):
    """検出結果をground truthと照合"""
    if verbose:
        print(f"\n{'='*60}")
        print(f"正解との照合 (tolerance: ±{tolerance}s)")
        print(f"{'='*60}")

    correct = 0
    max_err = 0
    errors = []
    for i, gt in enumerate(ground_truth):
        if i < len(cut_points):
            det = cut_points[i]
            err = det - gt
            abs_err = abs(err)
            max_err = max(max_err, abs_err)
            errors.append(abs_err)
            if abs_err <= tolerance:
                correct += 1
                status = "✅"
            elif abs_err <= tolerance * 3:
                status = "⚠️"
            else:
                status = "❌"
            if verbose:
                print(f"  Cut{i+1:2d}: GT={gt:.3f}s  Det={det:.3f}s  err={err:+.4f}s  {status}")
        else:
            if verbose:
                print(f"  Cut{i+1:2d}: GT={gt:.3f}s  未検出  ❌")

    total = len(ground_truth)
    accuracy = correct / total * 100 if total > 0 else 0
    avg_err = np.mean(errors) if errors else 0

    if verbose:
        print(f"\n  Accuracy: {correct}/{total} ({accuracy:.0f}%)")
        print(f"  Max error: {max_err:.4f}s")
        print(f"  Avg error: {avg_err:.4f}s")
        print(f"  {'✅ PASS' if correct == total else '❌ NEEDS WORK'}")

    return {
        "correct": correct,
        "total": total,
        "accuracy": accuracy,
        "max_error": max_err,
        "avg_error": avg_err,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FV cut detection v5 (group-based)")
    parser.add_argument("video", help="Path to packed FV video")
    parser.add_argument("--expected", "-n", type=int, required=True, help="Expected number of FVs")
    parser.add_argument("--ground-truth", "-gt", help="Comma-separated ground truth cut times")
    parser.add_argument("--tolerance", "-t", type=float, default=0.1, help="Tolerance in seconds (default: 0.1)")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    result = detect_fv_cuts(args.video, args.expected, verbose=not args.quiet)

    if args.ground_truth:
        gt = [float(x) for x in args.ground_truth.split(",")]
        evaluate(result["cut_points"], gt, tolerance=args.tolerance, verbose=True)
