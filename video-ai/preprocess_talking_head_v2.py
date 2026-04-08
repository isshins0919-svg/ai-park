#!/usr/bin/env python3
"""
preprocess_talking_head_v2.py — トーキングヘッド動画 前処理パイプライン v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【v1からの根本的な変更点】
  v1: Geminiに「このセリフは何秒？」→ 曖昧なタイムスタンプ → 失敗
  v2: Whisperで全音声を単語レベルで完全書き起こし
      → 台本テキストと照合して【最後の一致区間】を選択
      → 最後 = 演者がOKを出したテイク（前テイクはNG or 言い直し）

【素材の構造（Q&A回答より）】
  [女性] 「○○と言ってください」（プロンプト）
  [男性] NG1「○○（言い間違い）」
  [女性] 「もう一度」
  [男性] NG2「○○（言い直し）」
  [女性] 「OKです」
  [男性] OK「○○」 ← 最後の一致区間 = これを使う
  → 次のシーンへ

【音声処理】
  - 全シーンをloudnorm -18LUFSに正規化（声の音量を統一）
  - BGMは後工程で固定10%でミックス

使い方:
  python3 preprocess_talking_head_v2.py \\
    --csv "台本.csv" \\
    --clips "/path/to/素材フォルダ" \\
    --output-dir "/path/to/prepped"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

# ──────────────────────────────────────────
# 設定
# ──────────────────────────────────────────
FFMPEG  = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

# Whisperモデル: large-v3が最高精度、turboが速度重視
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# テキストマッチング閾値（0〜1、高いほど厳格）
MATCH_THRESHOLD = 0.60  # 日本語の口語は表記ゆれが多いので少し緩め

# シーン末尾パディング（秒）
SCENE_PAD_END = 0.25

# 明るさ補正フィルタ
BRIGHTNESS_FILTER = "eq=brightness=0.06:gamma=1.15:saturation=1.08"

# 音声正規化: loudnorm (-18 LUFS) でシーン間の声の音量を統一
LOUDNORM_FILTER = "loudnorm=I=-18:LRA=11:TP=-1.5"


# ──────────────────────────────────────────
# ユーティリティ
# ──────────────────────────────────────────
def run_cmd(cmd: list, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def ffmpeg_run(*args, check: bool = True):
    cmd = [FFMPEG, "-y"] + list(args)
    r = run_cmd(cmd)
    if check and r.returncode != 0:
        raise RuntimeError(f"FFmpeg失敗:\n{r.stderr[-800:]}")
    return r


def get_duration(path: str) -> float:
    r = run_cmd([FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", path])
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def normalize_text(text: str) -> str:
    """
    テキストを正規化して比較しやすくする。
    - 全角→半角
    - 句読点・記号を除去
    - スペース除去
    - ひらがな/カタカナはそのまま（変換しない）
    """
    text = unicodedata.normalize("NFKC", text)
    # 記号・句読点除去（日本語・英数字以外）
    text = re.sub(r'[^\w\u3040-\u30FF\u4E00-\u9FFF]', '', text)
    return text.strip()


def text_similarity(a: str, b: str) -> float:
    """2つの正規化済みテキストの類似度（0〜1）を返す。"""
    return SequenceMatcher(None, a, b).ratio()


# ──────────────────────────────────────────
# Step 1: CSV パース
# ──────────────────────────────────────────
def parse_script_csv(csv_path: str) -> list[dict]:
    scenes = []
    mode = None
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            col0 = unicodedata.normalize("NFKC", row[0].strip())
            if "■ 台本" in col0:
                mode = "script"
                continue
            if "■ 素材リスト" in col0:
                break
            if mode != "script":
                continue
            if "No." in (col0 or "") or (len(row) > 1 and "No." in row[1]):
                continue

            # 5列形式
            if col0 == "" and len(row) > 1 and row[1].strip().isdigit():
                no_str = row[1].strip()
                text   = row[2].strip() if len(row) > 2 else ""
                clip   = row[3].strip() if len(row) > 3 else ""
                note   = row[4].strip() if len(row) > 4 else ""
            elif col0.isdigit():
                no_str = col0
                text   = row[1].strip() if len(row) > 1 else ""
                clip   = row[2].strip() if len(row) > 2 else ""
                note   = row[3].strip() if len(row) > 3 else ""
            else:
                continue

            if not text:
                continue
            # 複数行テキストを1行に結合
            text_oneline = text.replace("\n", " ").strip()
            scenes.append({
                "no":        int(no_str),
                "text":      text_oneline,
                "text_raw":  text,      # 元の改行あり（CSV出力用）
                "clip_file": clip,
                "note":      note,
            })

    print(f"✅ CSV: {len(scenes)} シーン読み込み完了")
    return scenes


# ──────────────────────────────────────────
# Step 2: Whisper で単語レベル書き起こし
# ──────────────────────────────────────────
def transcribe_audio(video_path: str, cache_dir: Path) -> list[dict]:
    """
    動画ファイルを Whisper で書き起こし、単語レベルのタイムスタンプリストを返す。
    キャッシュがあれば再利用（再実行高速化）。

    返値: [{"word": "制汗剤", "start": 0.24, "end": 0.81}, ...]
    """
    cache_path = cache_dir / f"{Path(video_path).stem}_words.json"
    if cache_path.exists():
        print(f"  📂 キャッシュ読み込み: {cache_path.name}")
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    print(f"  🎙  Whisper 書き起こし開始: {Path(video_path).name}")
    print(f"      モデル: {WHISPER_MODEL} （初回はダウンロードあり）")
    start_t = time.time()

    import mlx_whisper
    result = mlx_whisper.transcribe(
        video_path,
        path_or_hf_repo=WHISPER_MODEL,
        language="ja",
        word_timestamps=True,
        verbose=False,
    )

    # 全セグメントから単語を抽出してフラット化
    words = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            word_text = w.get("word", "").strip()
            if word_text:
                words.append({
                    "word":  word_text,
                    "start": round(float(w["start"]), 3),
                    "end":   round(float(w["end"]),   3),
                })

    elapsed = time.time() - start_t
    print(f"  ✅ 書き起こし完了: {len(words)} 単語 / {elapsed:.0f}s")

    # セグメント全文も表示（確認用）
    full_text = "".join(w["word"] for w in words)
    print(f"  📝 全文（先頭100字）: {full_text[:100]}...")

    # キャッシュ保存
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    return words


# ──────────────────────────────────────────
# Step 3: 台本テキストとのマッチング → 最後の一致区間を選択
# ──────────────────────────────────────────
def find_best_take(words: list[dict], target_text: str) -> dict | None:
    """
    単語リスト(words)の中でtarget_textに最も一致する区間を全部抽出し、
    【最後の一致区間】を返す。最後 = 演者が最終的にOKを出したテイク。

    返値: {"start": float, "end": float, "score": float, "matched_text": str}
          一致なしの場合: None
    """
    target_clean = normalize_text(target_text)
    if not target_clean:
        return None

    # 対象テキストの長さから窓サイズの目安を決める（文字数→概算単語数）
    # 日本語は1単語≒2〜4文字なので、文字数÷3 を基準に
    target_char_len = len(target_clean)
    min_words = max(1, target_char_len // 6)
    max_words = max(5, target_char_len // 2)

    all_matches = []  # (start_word_idx, end_word_idx, score, text)

    for start_idx in range(len(words)):
        best_score = 0.0
        best_end   = start_idx

        for end_idx in range(start_idx + min_words, min(start_idx + max_words + 1, len(words) + 1)):
            window_text  = "".join(w["word"] for w in words[start_idx:end_idx])
            window_clean = normalize_text(window_text)

            score = text_similarity(target_clean, window_clean)

            if score > best_score:
                best_score = score
                best_end   = end_idx

        if best_score >= MATCH_THRESHOLD:
            matched_text = "".join(w["word"] for w in words[start_idx:best_end])
            all_matches.append({
                "start_idx":    start_idx,
                "end_idx":      best_end,
                "start":        words[start_idx]["start"],
                "end":          words[best_end - 1]["end"] if best_end > start_idx else words[start_idx]["end"],
                "score":        best_score,
                "matched_text": matched_text,
            })

    if not all_matches:
        return None

    # 同じ時間帯に複数マッチが重なる場合は最高スコアのみ残す（重複除去）
    deduped = []
    for m in all_matches:
        if not deduped or m["start"] > deduped[-1]["end"] + 0.5:
            deduped.append(m)
        elif m["score"] > deduped[-1]["score"]:
            deduped[-1] = m

    print(f"      一致区間 {len(deduped)} 個発見 → 最後のテイクを選択")
    for i, m in enumerate(deduped):
        label = "← ✅ 採用（OKテイク）" if i == len(deduped) - 1 else "   (NG or 言い直し)"
        print(f"      [{i+1}] {m['start']:.1f}s〜{m['end']:.1f}s score={m['score']:.2f} 「{m['matched_text'][:25]}」{label}")

    # 最後の一致区間 = OKテイク
    return deduped[-1]


# ──────────────────────────────────────────
# Step 4: FFmpeg 精密カット + 明るさ補正 + 音量正規化
# ──────────────────────────────────────────
def cut_and_normalize(
    source_path: str,
    start:       float,
    end:         float,
    output_path: str,
    brightness:  str = BRIGHTNESS_FILTER,
    loudnorm:    str = LOUDNORM_FILTER,
):
    """
    source_pathのstart〜endを切り出し:
      - 明るさ補正
      - 音量正規化（loudnorm -18 LUFS）
    音声はそのまま保持（元音声使用モード）。
    """
    duration = max(0.1, (end - start) + SCENE_PAD_END)
    start_use = max(0.0, start)

    vf = brightness
    af = loudnorm

    ffmpeg_run(
        "-ss", f"{start_use:.3f}",
        "-i", source_path,
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-af", af,
        "-acodec", "aac",
        "-vcodec", "libx264",
        "-preset", "fast",
        "-crf", "18",
        output_path,
    )
    actual = get_duration(output_path)
    print(f"  ✂️  {Path(output_path).name}: {start:.2f}s〜{end:.2f}s → {actual:.2f}s")


# ──────────────────────────────────────────
# Step 5: 前処理済みCSV生成
# ──────────────────────────────────────────
def write_preprocessed_csv(original_csv: str, scenes: list[dict],
                            prepped_dir: str, output_csv: str):
    scene_map = {
        s["no"]: f"scene_{s['no']:02d}.mov"
        for s in scenes
        if (Path(prepped_dir) / f"scene_{s['no']:02d}.mov").exists()
    }

    output_rows = []
    mode = None
    with open(original_csv, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                output_rows.append(row)
                continue
            col0 = unicodedata.normalize("NFKC", row[0].strip())

            if "■ 台本" in col0:
                mode = "script"
                output_rows.append(row)
                continue
            if "■ 素材リスト" in col0:
                mode = None
                output_rows.append(row)
                continue

            if mode == "script":
                if "No." in (col0 or "") or (len(row) > 1 and "No." in row[1]):
                    output_rows.append(row)
                    continue
                if col0 == "" and len(row) > 1 and row[1].strip().isdigit():
                    no = int(row[1].strip())
                    if no in scene_map and len(row) > 3:
                        row = list(row)
                        row[3] = scene_map[no]
                elif col0.isdigit() and len(row) > 2:
                    no = int(col0)
                    if no in scene_map:
                        row = list(row)
                        row[2] = scene_map[no]

            output_rows.append(row)

    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(output_rows)
    print(f"  📄 前処理済みCSV: {Path(output_csv).name}")


# ──────────────────────────────────────────
# メインパイプライン
# ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="トーキングヘッド前処理 v2.0 (Whisper)")
    parser.add_argument("--csv",        required=True)
    parser.add_argument("--clips",      required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--threshold",  type=float, default=MATCH_THRESHOLD,
                        help=f"テキストマッチ閾値 (デフォルト: {MATCH_THRESHOLD})")
    parser.add_argument("--no-cache",   action="store_true",
                        help="書き起こしキャッシュを使わない（再書き起こし）")
    args = parser.parse_args()

    clips_dir  = Path(args.clips)
    output_dir = Path(args.output_dir)
    cache_dir  = output_dir / "_cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    threshold  = args.threshold

    print("\n" + "━" * 60)
    print("  🎬 トーキングヘッド前処理 v2.0 — Whisper × OKテイク選別")
    print("━" * 60)

    # STEP 1: CSV読み込み
    print("\n📄 STEP 1: CSV読み込み")
    scenes = parse_script_csv(args.csv)

    # STEP 2: ファイルごとにシーンをグループ化
    print("\n🗂️  STEP 2: 素材ファイルごとにグループ化")
    file_groups: dict[str, list[dict]] = defaultdict(list)
    for s in scenes:
        if s["clip_file"]:
            file_groups[s["clip_file"]].append(s)

    for fname, slist in file_groups.items():
        nos = [s["no"] for s in slist]
        print(f"  {fname}: S{nos[0]:02d}〜S{nos[-1]:02d} ({len(slist)}シーン)")

    # キャッシュクリア指定
    if args.no_cache:
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        print("  🗑️  書き起こしキャッシュを削除しました")

    # STEP 3: 各素材ファイルを書き起こし → マッチング → カット
    print("\n🎙  STEP 3: Whisper書き起こし → OKテイク選別 → 精密カット")

    cut_ok   = 0
    cut_fail = 0
    fail_list = []

    for clip_filename, clip_scenes in file_groups.items():
        source_path = clips_dir / clip_filename
        if not source_path.exists():
            print(f"\n  ⚠️  素材ファイルが見つかりません: {clip_filename}")
            for s in clip_scenes:
                fail_list.append(s["no"])
            cut_fail += len(clip_scenes)
            continue

        print(f"\n  ─── {clip_filename} ({len(clip_scenes)}シーン) ───")
        print(f"  📹 尺: {get_duration(str(source_path)):.1f}s")

        # Whisper書き起こし
        try:
            words = transcribe_audio(str(source_path), cache_dir)
        except Exception as e:
            print(f"  ❌ 書き起こし失敗: {e}")
            for s in clip_scenes:
                fail_list.append(s["no"])
            cut_fail += len(clip_scenes)
            continue

        # 各シーンのOKテイクを検出してカット
        for scene in clip_scenes:
            sid = f"S{scene['no']:02d}"
            print(f"\n  ── {sid}: 「{scene['text'][:30]}」")

            match = find_best_take(words, scene["text"])

            if match is None:
                print(f"      ⚠️  一致区間なし（threshold={threshold}）")
                print(f"           → 素材全体をフォールバック使用")
                # フォールバック: 素材全体の先頭 or 前シーンの直後
                src_dur = get_duration(str(source_path))
                match = {
                    "start": 0.0,
                    "end":   min(5.0, src_dur),
                    "score": 0.0,
                    "matched_text": "(フォールバック)",
                }

            out_path = output_dir / f"scene_{scene['no']:02d}.mov"
            try:
                cut_and_normalize(
                    source_path = str(source_path),
                    start       = match["start"],
                    end         = match["end"],
                    output_path = str(out_path),
                )
                cut_ok += 1
            except Exception as e:
                print(f"      ❌ カット失敗: {e}")
                fail_list.append(scene["no"])
                cut_fail += 1

    # STEP 4: 前処理済みCSV生成
    print(f"\n📄 STEP 4: 前処理済みCSV生成")
    prepped_csv = output_dir / f"台本_v2_{Path(args.csv).stem}.csv"
    write_preprocessed_csv(args.csv, scenes, str(output_dir), str(prepped_csv))

    # 完了サマリ
    print("\n" + "━" * 60)
    print(f"  🎬 前処理完了！  ✅ {cut_ok}シーン / ⚠️  {cut_fail}シーン失敗")
    if fail_list:
        print(f"  失敗シーン: {fail_list}")
    print("━" * 60)

    output_mp4 = output_dir.parent / "output" / f"apobuster_{time.strftime('%m%d')}_v2.mp4"
    ref_video  = clips_dir / "参考動画.mov"
    ref_arg    = f"\\\n    --ref-video \"{ref_video}\"" if ref_video.exists() else ""

    print(f"""
  次のコマンド（edit_ai_v2.py 実行）:
  python3 /Users/ca01224/Desktop/一進VOYAGE号/video-ai/edit_ai_v2.py \\
    --script  "{prepped_csv}" \\
    --clips   "{output_dir}" \\
    --output  "{output_mp4}"{ref_arg}
""")
    print("━" * 60)


if __name__ == "__main__":
    main()
