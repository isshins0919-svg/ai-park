#!/usr/bin/env python3
"""
edit_ai_sakura.py — さくらASMR特化 AI自動編集パイプライン

edit_ai_v2.py をベースに、ASMR特化カスタマイズ:
- TTS削除（オリジナル音声使用）
- BGM mixing 無効化
- 壺ポイント（2-3秒無音）を絶対に保持
- ラウドネス正規化 -16 LUFS
- ノイズ除去 afftdn -25（軽め）
- テロップ色分け（プロ声=白 / 素の声=ピンク / 選挙=オレンジ）

使い方:
    python3 edit_ai_sakura.py \\
        --script-html reports/sakura-scripts-v3.html \\
        --materials video-ai/sakura/sessions/2026-04-11/best_takes.json \\
        --script-id 1 \\
        --output video-ai/sakura/output/

依存:
    - ffmpeg (/opt/homebrew/bin/ffmpeg)
    - Python packages: beautifulsoup4 (HTMLパース)
"""

import os, sys, json, re, subprocess, argparse, shutil, tempfile
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════
# 定数
# ═══════════════════════════════════════
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

OUTPUT_W = 1080
OUTPUT_H = 1920
FPS = 30

# 音声処理
NOISE_REDUCTION = "afftdn=nf=-25"
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"
AUDIO_CHAIN = f"{NOISE_REDUCTION},{LOUDNORM}"

# テロップ
FONT_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_FALLBACK = "/System/Library/Fonts/ヒラギノ角ゴ ProN W6.otf"
FONT_SIZE = 76
CHARS_PER_LINE = 12
TELOP_Y_RATIO = 0.72

TELOP_COLORS = {
    "pro": "white",
    "raw": "#E89BB0",       # ピンク（素の声）
    "election": "#E8A855",  # オレンジ（選挙プロ）
    "silence": None,         # テロップなし
}


# ═══════════════════════════════════════
# HTMLパース: 台本v3 → タイムラインJSON
# ═══════════════════════════════════════
def parse_script_html(html_path: Path, script_id: int) -> dict:
    """
    sakura-scripts-v3.html から指定台本のタイムラインを抽出

    v3のフォーマット:
    <div class="page script-page">
      <span class="page-num">01</span>  ← script_id
      <h2>深夜のスタメン発表</h2>        ← title
      <div class="tl-item">
        <span class="tl-time">0:00-0:04</span>
        <span class="tl-voice voice-pro">プロ</span>
        <div class="tl-content">
          <p class="tl-line">「1番、センターフィールダー...」</p>
          <p class="tl-direction">画: ...</p>
        </div>
      </div>
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("⚠️  beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
        sys.exit(1)

    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # script_id でページを特定
    target_page = None
    for page in soup.find_all("div", class_="script-page"):
        page_num_span = page.find("span", class_="page-num")
        if not page_num_span:
            continue
        page_num = page_num_span.get_text(strip=True)
        # "01" や "SCRIPT 01" などの形式に対応
        m = re.search(r"(\d+)", page_num)
        if m and int(m.group(1)) == script_id:
            target_page = page
            break

    if not target_page:
        raise ValueError(f"Script #{script_id} not found in {html_path}")

    # タイトル
    h2 = target_page.find("h2")
    title = h2.get_text(strip=True) if h2 else f"Script #{script_id}"

    # タイムライン抽出
    timeline = []
    for item in target_page.find_all("div", class_="tl-item"):
        time_span = item.find("span", class_="tl-time")
        voice_span = item.find("span", class_="tl-voice")
        line_p = item.find("p", class_="tl-line")
        direction_p = item.find("p", class_="tl-direction")

        if not (time_span and voice_span and line_p):
            continue

        time_text = time_span.get_text(strip=True)
        # "0:00-0:04" → start=0.0, end=4.0
        m = re.match(r"(\d+):(\d+)-(\d+):(\d+)", time_text)
        if not m:
            continue
        start = int(m.group(1)) * 60 + int(m.group(2))
        end = int(m.group(3)) * 60 + int(m.group(4))

        # voice判定
        voice_classes = voice_span.get("class", [])
        if "voice-pro" in voice_classes:
            voice_type = "pro"
        elif "voice-raw" in voice_classes:
            voice_type = "raw"
        elif "voice-election" in voice_classes:
            voice_type = "election"
        elif "voice-silence" in voice_classes:
            voice_type = "silence"
        else:
            voice_type = "raw"

        line_text = line_p.get_text(separator=" ", strip=True)
        # em タグ（演出指示）を除去
        line_text = re.sub(r"（[^）]*）", "", line_text).strip()

        direction = direction_p.get_text(strip=True) if direction_p else ""

        timeline.append({
            "start": start,
            "end": end,
            "duration": end - start,
            "voice": voice_type,
            "text": line_text,
            "direction": direction,
        })

    return {
        "script_id": script_id,
        "title": title,
        "total_duration": timeline[-1]["end"] if timeline else 0,
        "timeline": timeline,
    }


# ═══════════════════════════════════════
# 素材選択
# ═══════════════════════════════════════
def select_clips(best_takes_json: dict, script_id: int) -> dict:
    """best_takes.jsonから該当scriptのクリップ情報を取得"""
    scripts = best_takes_json.get("scripts", {})
    key = str(script_id)
    if key not in scripts:
        raise ValueError(f"Script #{script_id} not found in best_takes.json")
    return scripts[key]


# ═══════════════════════════════════════
# FFmpeg処理
# ═══════════════════════════════════════
def ffmpeg_trim_audio_normalize(input_path: Path, output_path: Path, start: float, duration: float):
    """
    音声付きでトリム + ノイズ除去 + ラウドネス正規化 + 縦型クロップ
    壺ポイントを保持するため silence trim は行わない
    """
    # 縦型クロップ: 中央から 9:16 を切り出し
    # iPhone縦撮りで既に縦型なら scale のみ
    video_filter = f"scale=-2:{OUTPUT_H},crop={OUTPUT_W}:{OUTPUT_H}"

    cmd = [
        FFMPEG, "-y",
        "-ss", str(start),
        "-i", str(input_path),
        "-t", str(duration),
        "-vf", video_filter,
        "-af", AUDIO_CHAIN,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-movflags", "+faststart",
        "-r", str(FPS),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-2000:]}")
    return output_path


def add_telop(video_path: Path, output_path: Path, text: str, voice_type: str, duration: float):
    """drawtext フィルターでテロップを焼き込む"""
    color = TELOP_COLORS.get(voice_type)
    if not color or not text:
        # テロップなし → コピー
        shutil.copy(video_path, output_path)
        return output_path

    # BudouXを試す（無ければ固定長改行）
    lines = wrap_text(text, CHARS_PER_LINE)
    display_text = "\\n".join(lines)

    # drawtext フィルター構築
    font_file = FONT_PATH if Path(FONT_PATH).exists() else FONT_FALLBACK
    escaped_text = display_text.replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")

    y_pos = int(OUTPUT_H * TELOP_Y_RATIO)

    drawtext = (
        f"drawtext=fontfile='{font_file}':"
        f"text='{escaped_text}':"
        f"fontsize={FONT_SIZE}:"
        f"fontcolor={color}:"
        f"x=(w-text_w)/2:"
        f"y={y_pos}:"
        f"box=1:boxcolor=black@0.5:boxborderw=20:"
        f"shadowcolor=black@0.8:shadowx=2:shadowy=2"
    )

    cmd = [
        FFMPEG, "-y",
        "-i", str(video_path),
        "-vf", drawtext,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"⚠️  Telop overlay failed: {result.stderr[-500:]}")
        shutil.copy(video_path, output_path)
    return output_path


def wrap_text(text: str, max_chars: int) -> list:
    """BudouXが使えれば使う、無ければ単純改行"""
    try:
        from budoux import load_default_japanese_parser
        parser = load_default_japanese_parser()
        chunks = parser.parse(text)
        lines = []
        current = ""
        for chunk in chunks:
            if len(current) + len(chunk) <= max_chars:
                current += chunk
            else:
                if current:
                    lines.append(current)
                current = chunk
        if current:
            lines.append(current)
        return lines
    except ImportError:
        # フォールバック: 固定長改行
        return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]


def concat_clips(clip_paths: list, output_path: Path):
    """複数クリップを concat demuxer で連結"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{p.absolute()}'\n")
        list_file = f.name

    try:
        cmd = [
            FFMPEG, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"Concat failed:\n{result.stderr[-2000:]}")
    finally:
        os.unlink(list_file)

    return output_path


# ═══════════════════════════════════════
# 品質チェック
# ═══════════════════════════════════════
def quality_check(video_path: Path) -> dict:
    """最終動画の品質をチェック"""
    try:
        cmd = [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)

        duration = float(data.get("format", {}).get("duration", 0))

        # 音量測定
        vol_cmd = [FFMPEG, "-i", str(video_path), "-af", "volumedetect", "-f", "null", "-"]
        vol_result = subprocess.run(vol_cmd, capture_output=True, text=True, timeout=60)
        mean_db = None
        max_db = None
        for line in vol_result.stderr.splitlines():
            if "mean_volume:" in line:
                m = re.search(r"mean_volume:\s*(-?[\d.]+)", line)
                if m: mean_db = float(m.group(1))
            elif "max_volume:" in line:
                m = re.search(r"max_volume:\s*(-?[\d.]+)", line)
                if m: max_db = float(m.group(1))

        checks = {
            "duration_sec": round(duration, 2),
            "duration_ok": 45 <= duration <= 70,
            "mean_volume_db": mean_db,
            "max_volume_db": max_db,
            "peak_ok": max_db is not None and max_db <= -1.0,
            "loudness_ok": mean_db is not None and -22 <= mean_db <= -12,
        }
        checks["all_ok"] = all([checks["duration_ok"], checks["peak_ok"], checks["loudness_ok"]])
        return checks
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════
# メイン処理
# ═══════════════════════════════════════
def process_script(
    script_html: Path,
    materials_json_path: Path,
    script_id: int,
    output_dir: Path,
    version: str = "v1",
) -> Path:
    """1本の台本をAI編集して最終MP4を出力"""
    print(f"\n=== さくらAI編集 — Script #{script_id} ===")

    # Step 1: 台本パース
    print(f"[1/6] 台本パース中...")
    script_data = parse_script_html(script_html, script_id)
    print(f"  タイトル: {script_data['title']}")
    print(f"  シーン数: {len(script_data['timeline'])}")
    print(f"  総尺: {script_data['total_duration']}秒")

    # Step 2: 素材読み込み
    print(f"[2/6] ベストテイク読み込み中...")
    with open(materials_json_path, encoding="utf-8") as f:
        best_takes = json.load(f)
    clip_info = select_clips(best_takes, script_id)
    best_take_file = clip_info["best_take"]["file"]
    print(f"  ベストテイク: {best_take_file}")

    # パス解決: materials.json から path を取得
    # best_takes.json に path がない場合は、materials.json から取る
    materials_json_parent = materials_json_path.parent
    # best_take に path がない場合は、session dir から raw_dir を推定
    source_video_path = None
    if "path" in clip_info["best_take"]:
        source_video_path = Path(clip_info["best_take"]["path"])
    else:
        # raw_dir を推定
        guesses = [
            materials_json_parent / "raw" / best_take_file,
            materials_json_parent.parent / "raw" / best_take_file,
            Path.home() / "Desktop" / best_take_file,
        ]
        for g in guesses:
            if g.exists():
                source_video_path = g
                break
    if not source_video_path or not source_video_path.exists():
        raise FileNotFoundError(f"Source video not found: {best_take_file}")
    print(f"  Source: {source_video_path}")

    # Step 3: シーンごとに切り出し
    print(f"[3/6] シーン切り出し中...")
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / f"temp_s{script_id}"
    temp_dir.mkdir(exist_ok=True)

    clip_paths = []
    for i, scene in enumerate(script_data["timeline"]):
        if scene["voice"] == "silence":
            continue  # silence シーンはスキップ（素材の自然な無音を使う）

        clip_out = temp_dir / f"scene_{i:02d}_raw.mp4"
        ffmpeg_trim_audio_normalize(
            source_video_path,
            clip_out,
            scene["start"],
            scene["duration"],
        )

        # Step 4: テロップ焼き込み
        clip_with_telop = temp_dir / f"scene_{i:02d}_telop.mp4"
        add_telop(
            clip_out,
            clip_with_telop,
            scene["text"],
            scene["voice"],
            scene["duration"],
        )
        clip_paths.append(clip_with_telop)
        print(f"  {i+1}/{len(script_data['timeline'])}: {scene['voice']:10} [{scene['start']}s-{scene['end']}s]")

    # Step 5: 連結
    print(f"[4/6] クリップ連結中...")
    final_path = output_dir / f"sakura_s{script_id}_{version}.mp4"
    concat_clips(clip_paths, final_path)

    # Step 6: 品質チェック
    print(f"[5/6] 品質チェック中...")
    checks = quality_check(final_path)
    print(f"  尺: {checks.get('duration_sec')}s ({'OK' if checks.get('duration_ok') else 'NG'})")
    print(f"  平均音量: {checks.get('mean_volume_db')}dB ({'OK' if checks.get('loudness_ok') else 'NG'})")
    print(f"  ピーク: {checks.get('max_volume_db')}dB ({'OK' if checks.get('peak_ok') else 'NG'})")

    # 一時ファイル削除
    shutil.rmtree(temp_dir, ignore_errors=True)

    # レポート保存
    report = {
        "script_id": script_id,
        "version": version,
        "output": str(final_path),
        "source": str(source_video_path),
        "script_data": script_data,
        "quality_checks": checks,
        "edited_at": datetime.now().isoformat(),
    }
    report_path = output_dir / f"sakura_s{script_id}_{version}_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[6/6] 完了!")
    print(f"  Output: {final_path}")
    print(f"  Report: {report_path}")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="さくらASMR特化 AI自動編集")
    parser.add_argument("--script-html", type=str, required=True, help="台本HTMLファイル (v3)")
    parser.add_argument("--materials", type=str, required=True, help="best_takes.json パス")
    parser.add_argument("--script-id", type=int, required=True, help="台本ID (1-5)")
    parser.add_argument("--output", type=str, default="video-ai/sakura/output", help="出力ディレクトリ")
    parser.add_argument("--version", type=str, default="v1", help="バージョン識別子")
    args = parser.parse_args()

    script_html = Path(args.script_html).expanduser().resolve()
    materials = Path(args.materials).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()

    if not script_html.exists():
        print(f"❌ Script HTML not found: {script_html}")
        sys.exit(1)
    if not materials.exists():
        print(f"❌ Materials JSON not found: {materials}")
        sys.exit(1)

    try:
        process_script(script_html, materials, args.script_id, output_dir, args.version)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
