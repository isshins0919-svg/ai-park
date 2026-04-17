#!/usr/bin/env python3
"""fv_detect_v4.py — FV自動分割（全素材使い切り・グルーピング方式）

前提:
  - 動画の全クリップが必ずどこかのFVに属する（空白なし）
  - 1つのFVは1〜複数のカットで構成される
  - expected_count 個のFVに最適分割する

手法:
  1. ffmpeg scene filter で全フレームのシーン変化スコアを取得
  2. 高スコアフレームを「カットポイント候補」として全列挙
  3. 候補からN-1個を選んでN個のFVに分割
  4. 最適選択: 各FVの尺の分散が最小になる組み合わせを動的計画法で求める

精度目標: ±0.033秒（1フレーム at 30fps）
"""

import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


def get_duration(video_path):
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def get_scene_scores(video_path):
    """全フレームのsceneスコアを取得"""
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


def find_cut_candidates(frames, min_score=0.15):
    """scene scoreが閾値以上のフレームを「カット候補」として抽出。
    近接フレーム（0.2秒以内）はスコア最大のものだけ残す。"""
    raw = [(t, s) for t, s in frames if s >= min_score]

    # 近接マージ
    merged = []
    for t, s in raw:
        if merged and abs(t - merged[-1][0]) < 0.2:
            if s > merged[-1][1]:
                merged[-1] = (t, s)
        else:
            merged.append((t, s))

    return merged


def optimal_split(candidates, expected_count, duration):
    """N-1個のカットポイントを選んでN個のFVに分割。
    各FVの尺が均等に近くなる組み合わせを動的計画法で求める。

    方針: 理想尺 = total_duration / expected_count からの偏差二乗和を最小化
    """
    n_cuts_needed = expected_count - 1
    cut_times = [c[0] for c in candidates]
    n_candidates = len(cut_times)

    if n_candidates < n_cuts_needed:
        print(f"  ⚠️ 候補{n_candidates}個 < 必要{n_cuts_needed}カット。候補を全て採用。")
        return cut_times

    ideal_dur = duration / expected_count

    # DP: dp[i][j] = cut_times[:i+1] からj個選んだ時の最小コスト
    # コスト = 各セグメントの (実際の尺 - ideal_dur)^2 の合計
    INF = float('inf')

    # カット候補のインデックスからn_cuts_needed個を選ぶ
    # 選んだカットで区切られるセグメントの尺の分散を最小化

    # dp[j][k] = 候補0..jのうちk個をカットとして選んだ時の、
    #            最初〜最後に選んだカットまでのセグメントの最小コスト
    # ※最初のセグメント（0 → 最初のカット）と最後のセグメント（最後のカット → duration）も含む

    # 全組み合わせは C(n, k) で大きすぎるかもしれないが、
    # n_candidates <= 30 程度、n_cuts_needed <= 20 程度なので DP で解ける

    # dp[k] = {last_idx: min_cost} として前から構築
    # ただし状態数が大きいので、コスト関数ベースの貪欲法で十分な場合もある

    # まずシンプルに: 全C(n,k)を列挙（n<=30, k<=15 なら C(30,15)=155M で大きすぎる）
    # → DP で O(n^2 * k) に落とす

    # dp[i][j] = candidates[0..i-1]からj個選んだ時の、選んだカットで区切った
    #            セグメントの偏差二乗和の最小値
    # 遷移: dp[i][j] = min over prev < i of:
    #   dp[prev][j-1] + cost(prev_cut_time → cut_times[i])

    # cut_times にインデックスを付ける
    ct = [0.0] + cut_times + [duration]  # 両端を追加

    # segment_cost(a, b) = (ct[b] - ct[a] - ideal_dur)^2
    def seg_cost(a_time, b_time):
        return (b_time - a_time - ideal_dur) ** 2

    # dp[j][i] = i番目の候補（1-indexed in ct）をj番目のカットとして選んだ時の最小コスト
    # j = 1..n_cuts_needed, i = 1..n_candidates
    dp = [[INF] * (n_candidates + 2) for _ in range(n_cuts_needed + 1)]
    parent = [[(-1, -1)] * (n_candidates + 2) for _ in range(n_cuts_needed + 1)]

    # j=1: 1番目のカットを候補iに置く → セグメント = [0, ct[i]]
    for i in range(1, n_candidates + 1):
        dp[1][i] = seg_cost(0.0, ct[i])
        parent[1][i] = (0, 0)

    # j=2..n_cuts_needed
    for j in range(2, n_cuts_needed + 1):
        for i in range(j, n_candidates + 1):
            for prev in range(j - 1, i):
                cost = dp[j-1][prev] + seg_cost(ct[prev], ct[i])
                if cost < dp[j][i]:
                    dp[j][i] = cost
                    parent[j][i] = (j-1, prev)

    # 最後のセグメント（最後のカット → duration）のコストを加算して最小を見つける
    best_cost = INF
    best_last = -1
    for i in range(n_cuts_needed, n_candidates + 1):
        total = dp[n_cuts_needed][i] + seg_cost(ct[i], duration)
        if total < best_cost:
            best_cost = total
            best_last = i

    # バックトラックで選んだカットを復元
    selected_indices = []
    j, i = n_cuts_needed, best_last
    while j > 0:
        selected_indices.append(i)
        j_prev, i_prev = parent[j][i]
        j, i = j_prev, i_prev
    selected_indices.reverse()

    selected_times = [ct[idx] for idx in selected_indices]
    return selected_times


def detect_fv_cuts(video_path, expected_count=13):
    duration = get_duration(video_path)
    ideal_dur = duration / expected_count

    print(f"📹 Video: {video_path}")
    print(f"⏱  Duration: {duration:.3f}s")
    print(f"🎯 Expected: {expected_count} FVs (ideal: {ideal_dur:.2f}s each)")
    print()

    # Step 1: 全フレームscoreスコア
    print("Step 1: ffmpeg scene scores...")
    frames = get_scene_scores(video_path)
    print(f"  → {len(frames)} frames")

    # Step 2: カット候補抽出
    print("Step 2: カット候補抽出 (score >= 0.15)...")
    candidates = find_cut_candidates(frames, min_score=0.15)
    print(f"  → {len(candidates)} candidates")
    for t, s in candidates:
        marker = "◆" if s >= 0.5 else "●" if s >= 0.2 else "○"
        print(f"    {marker} {t:.3f}s  score={s:.4f}")

    # Step 3: 最適分割
    target_cuts = expected_count - 1
    print(f"\nStep 3: 最適分割 (DP) → {target_cuts}カット...")
    cut_points = optimal_split(candidates, expected_count, duration)
    print(f"  → {len(cut_points)} cuts selected")

    # 結果出力
    print(f"\n{'='*60}")
    print(f"検出結果: {len(cut_points)} カットポイント → {len(cut_points) + 1} FVs")
    print(f"{'='*60}")

    fv_starts = [0.0] + cut_points
    fv_ends = cut_points + [duration]
    for i in range(len(fv_starts)):
        start, end = fv_starts[i], fv_ends[i]
        dur = end - start
        frame_num = round(start * 30) % 30 if i > 0 else 0
        sec = int(start)
        if i > 0:
            print(f"  FV{i+1:2d}: starts {sec}秒{frame_num:02d} ({start:.3f}s) dur={dur:.2f}s")
        else:
            print(f"  FV 1: starts 0.000s dur={dur:.2f}s")

    # 正解照合
    ground_truth = [
        2 + 17/30, 5 + 6/30, 7 + 22/30, 10 + 25/30,
        13 + 25/30, 17 + 17/30, 21 + 7/30, 24 + 1/30,
        26 + 23/30, 28 + 22/30, 31 + 25/30, 35 + 0/30,
    ]

    print(f"\n{'='*60}")
    print("正解との照合 (goal: ±0.033s = 1フレーム)")
    print(f"{'='*60}")
    all_pass = True
    max_err = 0
    for i, gt in enumerate(ground_truth):
        if i < len(cut_points):
            det = cut_points[i]
            err = det - gt
            max_err = max(max_err, abs(err))
            status = "✅" if abs(err) <= 0.034 else "❌"
            if abs(err) > 0.034:
                all_pass = False
            print(f"  FV{i+1:2d}: 正解={gt:.3f}s  検出={det:.3f}s  誤差={err:+.4f}s  {status}")
        else:
            print(f"  FV{i+1:2d}: 正解={gt:.3f}s  未検出  ❌")
            all_pass = False

    print(f"\n  Max error: {max_err:.4f}s")
    print(f"  {'✅ ALL PASS' if all_pass else '❌ NEEDS TUNING'}")

    return {"cut_points": cut_points, "fv_count": len(cut_points) + 1, "duration": duration}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--expected", "-n", type=int, default=13)
    args = parser.parse_args()
    detect_fv_cuts(args.video, args.expected)
