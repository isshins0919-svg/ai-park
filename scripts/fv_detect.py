#!/usr/bin/env python3
"""fv_detect.py — FV切り替わり検出（セマンティック + ピクセル差分ハイブリッド）

連結されたFV動画から、各FVの切り替わりポイントを自動検出する。

手法:
  1. 0.2秒間隔でフレーム抽出
  2. 隣接フレーム間のピクセル差分（高速・粗い検出）
  3. 差分が大きいポイント周辺をGeminiで意味解析（精密判定）
  4. カットポイントを出力
"""

import base64, json, os, re, subprocess, sys, tempfile, time
from pathlib import Path

import numpy as np

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

# === Env ===
def _load_env(var):
    if os.environ.get(var):
        return
    for rc in [Path.home() / ".zshrc", Path.home() / ".zshenv"]:
        if not rc.exists():
            continue
        for line in rc.read_text().splitlines():
            line = line.strip()
            if line.startswith("#"):
                continue
            m = re.match(rf'export\s+{var}=["\']?([^"\'#\s]+)["\']?', line)
            if m:
                os.environ[var] = m.group(1)
                return

# === Frame Extraction ===
def extract_frames(video_path, interval=0.2):
    """指定間隔でフレームを抽出。[(timestamp, image_path), ...]"""
    # 尺取得
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    duration = float(r.stdout.strip())

    tmpdir = tempfile.mkdtemp(prefix="fv_detect_")
    frames = []
    t = 0.0
    while t < duration:
        out_path = os.path.join(tmpdir, f"frame_{t:.2f}.jpg")
        subprocess.run(
            [FFMPEG, "-y", "-ss", str(t), "-i", video_path,
             "-vframes", "1", "-q:v", "3", out_path],
            capture_output=True
        )
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            frames.append((t, out_path))
        t += interval

    return frames, tmpdir

# === Pixel Difference ===
def pixel_diff(img_path_a, img_path_b):
    """2枚の画像のピクセル差分スコア（0-1）"""
    from PIL import Image
    a = np.array(Image.open(img_path_a).resize((270, 480)))
    b = np.array(Image.open(img_path_b).resize((270, 480)))
    diff = np.abs(a.astype(float) - b.astype(float))
    return float(np.mean(diff) / 255.0)

# === Gemini Verification ===
def gemini_verify_cut(frame_before, frame_after, gemini_key):
    """2フレームがFV切り替わりかGeminiで判定"""
    import requests
    parts = []
    for img_path in [frame_before, frame_after]:
        with open(img_path, "rb") as f:
            parts.append({"inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(f.read()).decode()
            }})

    parts.append({"text": (
        "この2枚の画像は連続する動画の隣接フレームです。\n"
        "1枚目が「直前」、2枚目が「直後」です。\n\n"
        "この動画は複数の「ファーストビュー（FV）」広告パターンが連結されたものです。\n"
        "各FVは2〜4秒程度の短い動画で、それぞれ異なる訴求パターンです。\n\n"
        "質問: この2枚の間でFVパターンが切り替わっていますか？\n\n"
        "切り替わりの判断基準（いずれかに当てはまればCUT）:\n"
        "- テロップの内容・デザイン・色・フォントが大きく変わった\n"
        "- 画面の構図やレイアウトが変わった（同じ人物でも構図変化があればCUT）\n"
        "- 背景色や画面の色調が変わった\n"
        "- 商品・人物が変わった\n\n"
        "切り替わりではない場合:\n"
        "- 同じ構図・同じテロップで人物の表情や口の動きだけが変わった\n"
        "- 同じシーンの微妙なカメラの揺れ\n\n"
        "JSONのみで回答:\n"
        '{"is_cut": true/false, "confidence": 0.0-1.0, "reason": "理由（日本語・1文）"}'
    )})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    resp = requests.post(url, json={"contents": [{"parts": parts}]}, timeout=20)
    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    raw = re.sub(r"```json|```", "", raw).strip()
    raw = re.sub(r",\s*}", "}", raw)
    return json.loads(raw)

# === Main Detection ===
def detect_fv_cuts(video_path, expected_count=13):
    print(f"📹 Video: {video_path}")
    print(f"🎯 Expected FV count: {expected_count}")
    print()

    # Step 1: フレーム抽出
    print("Step 1: フレーム抽出 (0.1秒間隔)...")
    frames, tmpdir = extract_frames(video_path, interval=0.1)
    print(f"  → {len(frames)} frames extracted")

    # Step 2: ピクセル差分で候補検出
    print("Step 2: ピクセル差分で切り替わり候補を検出...")
    diffs = []
    for i in range(len(frames) - 1):
        t_a, path_a = frames[i]
        t_b, path_b = frames[i + 1]
        d = pixel_diff(path_a, path_b)
        diffs.append((t_b, d, i + 1))

    # 近接フレームをマージ（0.8秒以内は最大差分のみ残す）
    diffs.sort(key=lambda x: x[0])
    merged_all = []
    for t, d, idx in diffs:
        if merged_all and abs(t - merged_all[-1][0]) < 0.8:
            if d > merged_all[-1][1]:
                merged_all[-1] = (t, d, idx)
        else:
            merged_all.append((t, d, idx))

    # 差分の大きい順にソート → expected_count の 1.5倍を候補に
    merged_all.sort(key=lambda x: -x[1])
    n_candidates = int(expected_count * 1.5)
    candidates = merged_all[:n_candidates]
    candidates.sort(key=lambda x: x[0])  # 時系列順に戻す

    diff_values = [d[1] for d in diffs]
    mean_diff = np.mean(diff_values)
    std_diff = np.std(diff_values)
    print(f"  → Mean diff: {mean_diff:.4f}, Std: {std_diff:.4f}")
    print(f"  → Top {n_candidates} candidates (from {len(merged_all)} merged points):")

    merged = candidates
    for t, d, idx in merged:
        print(f"    {t:.2f}s (diff={d:.4f})")

    # Step 3: Geminiで精密判定
    _load_env("GEMINI_API_KEY_1")
    gemini_key = os.environ.get("GEMINI_API_KEY_1")

    if gemini_key and len(merged) > 0:
        print(f"\nStep 3: Gemini で {len(merged)} 候補を精密判定...")
        confirmed_cuts = []
        for t, d, idx in merged:
            before_path = frames[idx - 1][1]
            after_path = frames[idx][1]
            try:
                result = gemini_verify_cut(before_path, after_path, gemini_key)
                is_cut = result.get("is_cut", False)
                conf = result.get("confidence", 0)
                reason = result.get("reason", "")
                status = "✅ CUT" if is_cut else "❌ skip"
                print(f"  {t:.2f}s: {status} (conf={conf:.2f}) {reason}")
                if is_cut and conf >= 0.5:
                    confirmed_cuts.append(t)
                time.sleep(0.3)
            except Exception as e:
                print(f"  {t:.2f}s: ⚠️ Gemini error: {e}")
                # 差分が十分大きければ採用
                if d >= threshold * 1.2:
                    confirmed_cuts.append(t)
    else:
        print("\nStep 3: Gemini unavailable, using pixel diff only")
        confirmed_cuts = [t for t, d, idx in merged]

    # Step 4: expected_count に近づける最終フィルタ
    target_cuts = expected_count - 1
    if len(confirmed_cuts) > target_cuts:
        # 候補のピクセル差分スコアを使って、差分が大きい順にtarget_cuts個を採用
        cut_with_diff = []
        for ct in confirmed_cuts:
            best_diff = 0
            for t, d, idx in merged:
                if abs(t - ct) < 0.5:
                    best_diff = max(best_diff, d)
            cut_with_diff.append((ct, best_diff))
        cut_with_diff.sort(key=lambda x: -x[1])
        confirmed_cuts = sorted([c for c, _ in cut_with_diff[:target_cuts]])
        print(f"\n  → Filtered to top {target_cuts} by pixel diff strength")

    # Step 5: 結果出力
    print(f"\n{'='*50}")
    print(f"検出結果: {len(confirmed_cuts)} カットポイント ({expected_count - 1} が正解)")
    print(f"{'='*50}")
    for i, t in enumerate(sorted(confirmed_cuts)):
        sec = int(t)
        frame = int((t - sec) * 30)  # 30fps
        print(f"  FV {i+1} の終わり: {sec}秒{frame:02d}フレーム ({t:.2f}s)")

    # JSON出力
    result = {
        "video": str(video_path),
        "cut_points": sorted(confirmed_cuts),
        "fv_count": len(confirmed_cuts) + 1,
        "expected": expected_count,
    }
    print(f"\nJSON: {json.dumps(result, ensure_ascii=False)}")

    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="FV連結動画のパス")
    parser.add_argument("--expected", "-n", type=int, default=13, help="FVの本数")
    args = parser.parse_args()
    detect_fv_cuts(args.video, args.expected)
