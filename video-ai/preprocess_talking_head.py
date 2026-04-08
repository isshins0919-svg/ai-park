#!/usr/bin/env python3
"""
preprocess_talking_head.py — トーキングヘッド動画 前処理パイプライン v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
概要:
  長尺のトーキングヘッド動画（16:9横）から、台本の各シーンに対応する
  区間をGemini音声解析 + FFmpegで正確に切り出す。

処理フロー:
  1. CSVを読んで「どのファイルにどのシーンが入っているか」をマップ化
  2. 各動画から音声を抽出（FFmpeg → mp3）
  3. Gemini Files APIに音声をアップロード
  4. 「この台本テキストは音声の何秒〜何秒か」をGeminiに問い合わせ
  5. FFmpegで各シーンを切り出し + 明るさ補正（音声はそのまま保持）
  6. prepped/ フォルダに scene_01.mov〜scene_NN.mov を出力
  7. edit_ai_v2.py に渡す「前処理済みCSV」を自動生成

使い方:
  python3 preprocess_talking_head.py \\
    --csv "台本.csv" \\
    --clips "/path/to/素材フォルダ" \\
    --output-dir "/path/to/prepped"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

# ──────────────────────────────────────────
# 設定
# ──────────────────────────────────────────
FFMPEG  = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY_1")
GEMINI_MODEL   = "gemini-2.0-flash"

# 明るさ補正（顔が暗い素材向け）
BRIGHTNESS_FILTER = "eq=brightness=0.06:gamma=1.15:saturation=1.08"

# シーン末尾パディング（秒）：次のセリフが始まる直前まで使えるよう少し余裕
SCENE_PAD_END = 0.12

# 単独ファイルのシーン（FV.movなど）で使う区間の最大秒数
# Geminiがタイムスタンプを返せなかった場合のフォールバック
FALLBACK_SINGLE_DURATION = 5.0


# ──────────────────────────────────────────
# ユーティリティ
# ──────────────────────────────────────────
def run_cmd(cmd: list, timeout: int = 300) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result


def ffmpeg(*args, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [FFMPEG, "-y"] + list(args)
    r = run_cmd(cmd)
    if check and r.returncode != 0:
        raise RuntimeError(f"FFmpeg失敗:\n{r.stderr[-600:]}")
    return r


def get_duration(path: str) -> float:
    r = run_cmd([FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", path])
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


# ──────────────────────────────────────────
# Step 1: CSVパース
# ──────────────────────────────────────────
def parse_script_csv(csv_path: str) -> list[dict]:
    """
    台本CSVからシーンリストを返す。
    Returns: [{"no": 1, "text": "...", "clip_file": "xxx.mov", "note": "..."}, ...]
    """
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
            # ヘッダ行スキップ
            if "No." in (col0 or "") or (len(row) > 1 and "No." in row[1]):
                continue

            # 5列形式: col0="", col1=No., col2=text, col3=clip, col4=note
            if col0 == "" and len(row) > 1 and row[1].strip().isdigit():
                no_str    = row[1].strip()
                text      = row[2].strip() if len(row) > 2 else ""
                clip_file = row[3].strip() if len(row) > 3 else ""
                note      = row[4].strip() if len(row) > 4 else ""
            elif col0.isdigit():
                no_str    = col0
                text      = row[1].strip() if len(row) > 1 else ""
                clip_file = row[2].strip() if len(row) > 2 else ""
                note      = row[3].strip() if len(row) > 3 else ""
            else:
                continue

            if not text:
                continue

            scenes.append({
                "no":        int(no_str),
                "text":      text,
                "clip_file": clip_file,  # 元CSV記載のファイル名
                "note":      note,
            })
    print(f"✅ CSV読み込み完了: {len(scenes)} シーン")
    return scenes


# ──────────────────────────────────────────
# Step 2: 素材グループ化
# ──────────────────────────────────────────
def group_scenes_by_clip(scenes: list[dict]) -> dict[str, list[dict]]:
    """
    clip_fileをキーに、シーンをグループ化。
    同じファイルを使う連続シーンをまとめて1回のGemini解析で処理できるようにする。
    """
    groups = defaultdict(list)
    for s in scenes:
        groups[s["clip_file"]].append(s)
    return dict(groups)


# ──────────────────────────────────────────
# Step 3: 音声抽出
# ──────────────────────────────────────────
def extract_audio(video_path: str, out_mp3: str):
    """動画から音声をmp3に抽出（128kbps）。"""
    ffmpeg("-i", video_path, "-vn", "-acodec", "libmp3lame", "-ab", "128k",
           "-ac", "1",  # モノラルにして容量削減
           out_mp3)
    size_kb = Path(out_mp3).stat().st_size // 1024
    print(f"  🔊 音声抽出: {Path(video_path).name} → {Path(out_mp3).name} ({size_kb}KB)")


# ──────────────────────────────────────────
# Step 4: Gemini Files API アップロード
# ──────────────────────────────────────────
def upload_audio_to_gemini(audio_path: str, api_key: str) -> str:
    """
    Gemini Files APIに音声ファイルをアップロードし、file_uriを返す。
    multipart uploadをrequestsで実装。
    """
    import requests

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    display_name = Path(audio_path).name
    boundary     = "==gemini_boundary=="

    # multipart/related ボディ構築
    meta_part = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f'{{"file": {{"display_name": "{display_name}"}}}}\r\n'
        f"--{boundary}\r\n"
        f"Content-Type: audio/mpeg\r\n\r\n"
    ).encode("utf-8")
    end_part = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = meta_part + audio_data + end_part

    upload_url = (
        f"https://generativelanguage.googleapis.com/upload/v1beta/files"
        f"?key={api_key}&uploadType=multipart"
    )
    resp = requests.post(
        upload_url,
        headers={
            "Content-Type":   f"multipart/related; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
        data=body,
        timeout=180,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Gemini Filesアップロード失敗 ({resp.status_code}): {resp.text[:300]}"
        )

    file_info = resp.json()["file"]
    file_uri  = file_info["uri"]
    file_name = file_info["name"]
    print(f"  📤 アップロード完了: {display_name} → {file_name.split('/')[-1]}")

    # ファイルがACTIVEになるまでポーリング（最大60秒）
    for i in range(30):
        st = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={api_key}",
            timeout=30,
        ).json()
        state = st.get("state", "")
        if state == "ACTIVE":
            print(f"  ✅ ファイル ACTIVE")
            break
        print(f"    ⏳ 処理中 ({state})... {i+1}/30")
        time.sleep(2)
    else:
        raise RuntimeError("Gemini Filesファイルがタイムアウト前にACTIVEになりませんでした")

    return file_uri


# ──────────────────────────────────────────
# Step 5: Geminiでタイムスタンプ取得
# ──────────────────────────────────────────
def get_timestamps_gemini(file_uri: str, scenes: list[dict], api_key: str) -> dict:
    """
    Geminiに音声ファイルと台本テキストを渡し、各シーンのタイムスタンプを取得。

    Returns: {"S02": {"start": 0.5, "end": 3.2, "confidence": "high"}, ...}
    """
    import requests

    script_lines = "\n".join(
        f"S{s['no']:02d}: {s['text'].replace(chr(10), ' ')}"
        for s in scenes
    )

    prompt = f"""添付の音声ファイルを注意深く聞いてください。
音声には男性（メイン話者）と女性（進行役）の声が含まれています。

【やること】
以下の台本テキストを**男性が話している区間**を秒単位で特定してください。
女性の声・返答・相槌は完全に無視してください。

【台本（男性の発言）】
{script_lines}

【出力形式】
必ず以下のJSONのみを返してください（説明文・マークダウン不要）:
{{
  "segments": [
    {{"id": "S01", "start": 1.2, "end": 4.5, "confidence": "high"}},
    {{"id": "S02", "start": 5.0, "end": 7.8, "confidence": "high"}}
  ]
}}

【補足】
- confidence: high（確実）/ medium（ほぼ確実）/ low（不明瞭）
- 台本テキストが聞き取れない場合はそのIDを省略してください
- start/endは0.1秒単位で答えてください
- 男性が話し終わった瞬間をendとしてください（余白を含めないこと）"""

    payload = {
        "contents": [{
            "parts": [
                {
                    "fileData": {
                        "mimeType": "audio/mpeg",
                        "fileUri":  file_uri,
                    }
                },
                {"text": prompt},
            ]
        }],
        "generationConfig": {
            "temperature":    0.05,
            "maxOutputTokens": 2048,
        },
    }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models"
        f"/{GEMINI_MODEL}:generateContent?key={api_key}"
    )

    for attempt in range(3):
        resp = requests.post(url, json=payload, timeout=120)
        if resp.status_code == 429:
            wait = (attempt + 1) * 10
            print(f"    ⏳ 429 rate limit → {wait}s待機")
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini APIエラー ({resp.status_code}): {resp.text[:300]}")
        break

    raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    print(f"  🤖 Gemini タイムスタンプ取得完了")

    # JSON部分を抽出
    m = re.search(r'\{[\s\S]*\}', raw_text)
    if not m:
        raise RuntimeError(f"GeminiレスポンスにJSONが見つかりません:\n{raw_text[:300]}")

    data   = json.loads(m.group(0))
    result = {}
    for seg in data.get("segments", []):
        sid = seg["id"]
        result[sid] = {
            "start":      float(seg["start"]),
            "end":        float(seg["end"]),
            "confidence": seg.get("confidence", "medium"),
        }
        icon = "✅" if seg.get("confidence") == "high" else "⚠️ "
        print(f"    {icon} {sid}: {seg['start']:.1f}s〜{seg['end']:.1f}s [{seg.get('confidence','?')}]")

    return result


# ──────────────────────────────────────────
# Step 6: FFmpegでシーン切り出し + 明るさ補正
# ──────────────────────────────────────────
def cut_scene(
    source_path: str,
    start:       float,
    end:         float,
    output_path: str,
    brightness:  str = BRIGHTNESS_FILTER,
):
    """
    source_pathのstart〜endを切り出し、明るさ補正をかけてoutput_pathに保存。
    音声はAACでそのまま保持。
    """
    clip_dur  = max(0.1, (end - start) + SCENE_PAD_END)
    start_use = max(0.0, start)

    ffmpeg(
        "-ss", f"{start_use:.3f}",
        "-i", source_path,
        "-t", f"{clip_dur:.3f}",
        "-vf", brightness,
        "-acodec", "aac",
        "-vcodec", "libx264",
        "-preset", "fast",
        "-crf", "18",
        output_path,
    )
    actual = get_duration(output_path)
    conf_mark = ""
    print(
        f"  ✂️  scene_{Path(output_path).stem[-2:]}.mov: "
        f"{start:.1f}s〜{end:.1f}s → {actual:.2f}s"
    )


# ──────────────────────────────────────────
# Step 7: 前処理済みCSVを生成
# ──────────────────────────────────────────
def write_preprocessed_csv(
    original_csv: str,
    scenes:       list[dict],  # no/text/clip_file/note
    prepped_dir:  str,
    output_csv:   str,
):
    """
    元CSVをベースに、clip_file列だけ prepped/scene_NN.mov に差し替えたCSVを生成。
    edit_ai_v2.py に直接渡せる。
    """
    # シーン番号 → 前処理済みファイル名のマップ
    scene_map = {}
    for s in scenes:
        no = s["no"]
        prepped_name = f"scene_{no:02d}.mov"
        prepped_path = Path(prepped_dir) / prepped_name
        if prepped_path.exists():
            scene_map[no] = prepped_name  # CSVにはファイル名だけ（拡張子付き）

    # 元CSVを読んでclip_file列を差し替え
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
            if "ナレーション" in col0 and mode != "script":
                # ナレーション設定の「なし（テロップのみ）」はそのまま維持
                output_rows.append(row)
                continue

            if mode == "script":
                # ヘッダ行はそのまま
                if "No." in (col0 or "") or (len(row) > 1 and "No." in row[1]):
                    output_rows.append(row)
                    continue
                # シーン行: clip_file列を差し替え
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

    print(f"  📄 前処理済みCSV出力: {Path(output_csv).name}")
    print(f"     → edit_ai_v2.py に渡してください")


# ──────────────────────────────────────────
# メインパイプライン
# ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="トーキングヘッド動画 前処理パイプライン"
    )
    parser.add_argument("--csv",        required=True, help="台本CSVパス")
    parser.add_argument("--clips",      required=True, help="素材フォルダパス")
    parser.add_argument("--output-dir", required=True, help="前処理済みクリップの出力先")
    parser.add_argument("--api-key",    default=GEMINI_API_KEY, help="Gemini APIキー")
    parser.add_argument("--skip-upload", action="store_true",
                        help="Geminiアップロードをスキップ（タイムスタンプJSONを手動指定）")
    parser.add_argument("--timestamps-json", default=None,
                        help="既存タイムスタンプJSONファイルパス（--skip-upload時）")
    args = parser.parse_args()

    clips_dir  = Path(args.clips)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    api_key    = args.api_key

    print("\n" + "━" * 55)
    print("  🎬 トーキングヘッド 前処理パイプライン v1.0")
    print("━" * 55)

    # ── STEP 1: CSV読み込み ──────────────────────────
    print("\n📄 STEP 1: CSV読み込み")
    scenes = parse_script_csv(args.csv)

    # ── STEP 2: ファイルごとにシーンをグループ化 ─────
    print("\n🗂️  STEP 2: 素材グループ化")
    groups = group_scenes_by_clip(scenes)
    for fname, slist in groups.items():
        nos = [s["no"] for s in slist]
        print(f"  {fname}: S{nos[0]:02d}〜S{nos[-1]:02d} ({len(slist)}シーン)")

    # ── STEP 3〜5: 各素材ファイルを処理 ─────────────
    print("\n🎙  STEP 3〜5: 音声抽出 → Gemini解析 → シーン切り出し")

    # 全タイムスタンプを格納（ファイル名ではなくシーン番号キー）
    all_timestamps: dict[str, dict] = {}  # "S01" -> {start, end, confidence}

    if args.timestamps_json and Path(args.timestamps_json).exists():
        print(f"  📂 既存タイムスタンプJSONを読み込み: {args.timestamps_json}")
        with open(args.timestamps_json) as f:
            all_timestamps = json.load(f)
    else:
        temp_dir = output_dir / "_temp_audio"
        temp_dir.mkdir(exist_ok=True)

        for clip_filename, clip_scenes in groups.items():
            if not clip_filename:
                print(f"  ⚠️  クリップ未指定のシーンをスキップ")
                continue

            source_path = clips_dir / clip_filename
            if not source_path.exists():
                print(f"  ⚠️  素材ファイルが見つかりません: {clip_filename}")
                continue

            print(f"\n  ─── {clip_filename} ({len(clip_scenes)}シーン) ───")
            source_dur = get_duration(str(source_path))
            print(f"  📹 素材尺: {source_dur:.1f}s")

            # 音声抽出
            audio_path = temp_dir / f"{Path(clip_filename).stem}_audio.mp3"
            extract_audio(str(source_path), str(audio_path))

            # 1シーンのみ or 短尺ファイルはGemini解析（タイムスタンプ特定）
            if args.skip_upload:
                print(f"  ⏭️  Geminiアップロードスキップ（フォールバック尺を使用）")
                ts = {}
            else:
                # Gemini Files APIにアップロード
                file_uri = upload_audio_to_gemini(str(audio_path), api_key)
                # タイムスタンプ取得
                ts = get_timestamps_gemini(file_uri, clip_scenes, api_key)

            all_timestamps.update(ts)

            # タイムスタンプが取れなかったシーン用フォールバック: 均等分割
            scene_nos_in_file = [s["no"] for s in clip_scenes]
            missing = [s for s in clip_scenes if f"S{s['no']:02d}" not in ts]
            if missing and len(clip_scenes) > 1:
                print(f"  ⚠️  タイムスタンプ未取得 {len(missing)}シーン → 均等分割で補完")
                per_dur = source_dur / len(clip_scenes)
                for i, s in enumerate(clip_scenes):
                    sid = f"S{s['no']:02d}"
                    if sid not in all_timestamps:
                        fb_start = i * per_dur
                        fb_end   = fb_start + per_dur - 0.3
                        all_timestamps[sid] = {
                            "start": round(fb_start, 2),
                            "end":   round(fb_end, 2),
                            "confidence": "low_fallback",
                        }
                        print(f"    ⚠️  {sid}: フォールバック {fb_start:.1f}s〜{fb_end:.1f}s")
            elif missing and len(clip_scenes) == 1:
                # 単独ファイル
                s = missing[0]
                sid = f"S{s['no']:02d}"
                print(f"  ⚠️  {sid}: タイムスタンプ未取得 → ファイル先頭{FALLBACK_SINGLE_DURATION}s")
                all_timestamps[sid] = {
                    "start": 0.0,
                    "end":   min(FALLBACK_SINGLE_DURATION, source_dur),
                    "confidence": "low_fallback",
                }

        # タイムスタンプをキャッシュ保存（再実行時に再利用可能）
        ts_cache_path = output_dir / "timestamps_cache.json"
        with open(ts_cache_path, "w", encoding="utf-8") as f:
            json.dump(all_timestamps, f, ensure_ascii=False, indent=2)
        print(f"\n  💾 タイムスタンプキャッシュ保存: {ts_cache_path.name}")

    # ── STEP 6: FFmpegで切り出し ─────────────────────
    print("\n✂️  STEP 6: シーン切り出し + 明るさ補正")

    # ファイル名→Pathのマップ（素材フォルダ内の全ファイル）
    clip_path_map: dict[str, Path] = {}
    for p in clips_dir.iterdir():
        clip_path_map[p.name] = p

    cut_ok    = 0
    cut_fail  = 0
    for s in scenes:
        sid = f"S{s['no']:02d}"
        ts  = all_timestamps.get(sid)
        if not ts:
            print(f"  ⚠️  {sid}: タイムスタンプなし → スキップ")
            cut_fail += 1
            continue

        clip_filename = s["clip_file"]
        source_path   = clip_path_map.get(clip_filename)
        if not source_path:
            print(f"  ⚠️  {sid}: 素材ファイル '{clip_filename}' が見つかりません")
            cut_fail += 1
            continue

        out_path = output_dir / f"scene_{s['no']:02d}.mov"
        try:
            cut_scene(
                source_path = str(source_path),
                start       = ts["start"],
                end         = ts["end"],
                output_path = str(out_path),
            )
            cut_ok += 1
        except Exception as e:
            print(f"  ❌ {sid} 切り出し失敗: {e}")
            cut_fail += 1

    print(f"\n  ✅ 切り出し完了: {cut_ok}シーン / ⚠️  失敗: {cut_fail}シーン")

    # ── STEP 7: 前処理済みCSV生成 ────────────────────
    print("\n📄 STEP 7: 前処理済みCSV生成")
    prepped_csv_path = output_dir / f"台本_前処理済み_{Path(args.csv).stem}.csv"
    write_preprocessed_csv(
        original_csv = args.csv,
        scenes       = scenes,
        prepped_dir  = str(output_dir),
        output_csv   = str(prepped_csv_path),
    )

    # ── 完了サマリ ────────────────────────────────────
    print("\n" + "━" * 55)
    print("  🎬 前処理完了！")
    print("━" * 55)
    print(f"  出力フォルダ: {output_dir}")
    print(f"  シーンファイル: {cut_ok}個")
    print(f"  前処理済みCSV: {prepped_csv_path.name}")
    print()
    print("  次のステップ（edit_ai_v2.py実行コマンド）:")
    output_mp4 = Path(args.output_dir).parent / "output" / f"apobuster_{time.strftime('%m%d')}.mp4"
    ref_video  = clips_dir / "参考動画.mov"
    ref_arg    = f"\\\n    --ref-video \"{ref_video}\"" if ref_video.exists() else ""
    print(f"""
  python3 /Users/ca01224/Desktop/一進VOYAGE号/video-ai/edit_ai_v2.py \\
    --script  "{prepped_csv_path}" \\
    --clips   "{output_dir}" \\
    --output  "{output_mp4}"{ref_arg}
""")
    print("━" * 55)


if __name__ == "__main__":
    main()
