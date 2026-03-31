"""
編集AI — 素材 + 台本テキスト → 縦型動画を自動生成
勝ちパターン（プルースト2解析）に基づくテンプレート実装

使い方:
  python3 video-ai/edit_ai.py

入力:
  - 動画クリップ（FV / ボディ / CTA）
  - 各クリップのテロップテキスト
  - 使用区間（秒数）

出力:
  - 結合 + テロップ済み縦型動画（mp4）
"""

import os
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, concatenate_videoclips, CompositeVideoClip,
    ImageClip, AudioFileClip, afx
)

# ===== 設定（勝ちパターンから導出） =====
OUTPUT_SIZE = (1080, 1920)   # 縦型 9:16
FONT_SIZE_MAIN = 72          # 通常テロップ
FONT_SIZE_EMPHASIS = 96      # 強調テロップ（感情ワード）
CHARS_PER_LINE = 13          # 1行あたり最大文字数（解析結果: 12-15）
TEXT_COLOR = (255, 255, 255)
EMPHASIS_BG = (255, 215, 0)  # 黄色背景（解析結果: 最多）
EMPHASIS_TEXT = (0, 0, 0)    # 黒文字
OUTPUT_DIR = "video-ai/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ===== テロップ画像生成 =====
def make_telop_image(
    text: str,
    size: tuple,
    emphasis: bool = False,
    font_size: int = None,
):
    """テキスト → RGBA画像"""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    fs = font_size or (FONT_SIZE_EMPHASIS if emphasis else FONT_SIZE_MAIN)

    # フォント（システムフォントを使用）
    font_candidates = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode MS.ttf",
    ]
    font = None
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, fs)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    # テキスト折り返し
    lines = []
    for raw_line in text.split("\n"):
        if len(raw_line) <= CHARS_PER_LINE:
            lines.append(raw_line)
        else:
            wrapped = textwrap.wrap(raw_line, width=CHARS_PER_LINE, break_long_words=True)
            lines.extend(wrapped)

    line_height = fs + 12
    total_text_h = line_height * len(lines)
    y_start = h - total_text_h - 80  # 下から80px

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2

        if emphasis:
            pad = 16
            draw.rectangle(
                [x - pad, y_start - pad // 2, x + text_w + pad, y_start + fs + pad // 2],
                fill=EMPHASIS_BG
            )
            draw.text((x, y_start), line, font=font, fill=EMPHASIS_TEXT)
        else:
            # 縁取り（白文字 + 黒縁）
            for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)]:
                draw.text((x + dx, y_start + dy), line, font=font, fill=(0, 0, 0, 220))
            draw.text((x, y_start), line, font=font, fill=TEXT_COLOR)

        y_start += line_height

    return img


def add_telop(clip, text: str, start: float, duration: float, emphasis: bool = False):
    """クリップにテロップを追加"""
    if not text.strip():
        return clip

    img = make_telop_image(text, OUTPUT_SIZE, emphasis=emphasis)
    arr = np.array(img)
    telop_clip = (
        ImageClip(arr, ismask=False)
        .set_start(start)
        .set_duration(duration)
    )
    return CompositeVideoClip([clip, telop_clip])


def resize_to_vertical(clip):
    """クリップを縦型(1080x1920)にリサイズ・クロップ"""
    target_w, target_h = OUTPUT_SIZE
    clip_ratio = clip.w / clip.h
    target_ratio = target_w / target_h

    if clip_ratio > target_ratio:
        new_h = target_h
        new_w = int(clip_ratio * new_h)
        resized = clip.resize(height=new_h)
        x_center = resized.w // 2
        cropped = resized.crop(
            x1=x_center - target_w // 2,
            x2=x_center + target_w // 2,
        )
    else:
        new_w = target_w
        new_h = int(new_w / clip_ratio)
        resized = clip.resize(width=new_w)
        y_center = resized.h // 2
        cropped = resized.crop(
            y1=y_center - target_h // 2,
            y2=y_center + target_h // 2,
        )
    return cropped


# ===== メイン: 動画生成 =====
def build_video(project: dict, output_filename: str = "output.mp4"):
    """
    project = {
        "segments": [
            {
                "clip_path": "path/to/clip.mp4",
                "type": "fv" | "body" | "cta",
                "start_sec": 0.0,    # クリップ内の使用開始秒
                "end_sec": 8.0,      # クリップ内の使用終了秒
                "telop": [
                    {"text": "テロップ文言", "offset": 0.0, "duration": 2.5, "emphasis": True},
                    {"text": "次のテロップ", "offset": 2.5, "duration": 3.0, "emphasis": False},
                ]
            },
            ...
        ],
        "bgm_path": "path/to/bgm.mp3",  # optional
    }
    """
    clips = []
    current_time = 0.0

    for seg in project["segments"]:
        path = seg["clip_path"]
        if not os.path.exists(path):
            print(f"  ⚠️  ファイルが見つかりません: {path}")
            continue

        print(f"  📹 {seg['type'].upper()}: {os.path.basename(path)}")

        raw = VideoFileClip(path)
        start = seg.get("start_sec", 0)
        end = seg.get("end_sec", raw.duration)
        end = min(end, raw.duration)

        segment = raw.subclip(start, end)
        segment = resize_to_vertical(segment)

        # テロップ追加
        telops = seg.get("telop", [])
        composite_clips = [segment]

        for t in telops:
            t_start = t.get("offset", 0)
            t_dur = t.get("duration", 2.0)
            t_text = t.get("text", "")
            t_emph = t.get("emphasis", False)

            if not t_text.strip():
                continue

            img = make_telop_image(t_text, OUTPUT_SIZE, emphasis=t_emph)
            arr = np.array(img)
            telop_clip = (
                ImageClip(arr, ismask=False)
                .set_start(t_start)
                .set_duration(min(t_dur, segment.duration - t_start))
            )
            composite_clips.append(telop_clip)

        final_seg = CompositeVideoClip(composite_clips).set_duration(segment.duration)
        clips.append(final_seg)
        current_time += segment.duration

    if not clips:
        print("❌ 有効なクリップがありません")
        return None

    # 結合
    final = concatenate_videoclips(clips, method="compose")

    # BGM
    if project.get("bgm_path") and os.path.exists(project["bgm_path"]):
        bgm = AudioFileClip(project["bgm_path"]).subclip(0, final.duration)
        bgm = bgm.volumex(0.15)  # BGMは小さめ
        if final.audio:
            from moviepy.editor import CompositeAudioClip
            final = final.set_audio(
                CompositeAudioClip([final.audio, bgm])
            )
        else:
            final = final.set_audio(bgm)

    output_path = os.path.join(OUTPUT_DIR, output_filename)
    print(f"\n  書き出し中 → {output_path}")
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="/tmp/temp_audio.m4a",
        remove_temp=True,
        verbose=False,
        logger=None,
    )
    print(f"  ✅ 完成: {output_path}")
    return output_path


# ===== サンプルプロジェクト（テスト用） =====
if __name__ == "__main__":
    print("=" * 60)
    print("編集AI — プルースト2 勝ちテンプレート")
    print("=" * 60)

    # --- ここを変えるだけで動画が変わる ---
    PROJECT = {
        "segments": [
            {
                "clip_path": "/tmp/proust2_0.mp4",   # FV素材
                "type": "fv",
                "start_sec": 0,
                "end_sec": 8,
                "telop": [
                    {
                        "text": "インナーにワキガ臭\n残ってる人",
                        "offset": 0.0,
                        "duration": 3.0,
                        "emphasis": True,   # 黄色背景 × 黒文字
                    },
                    {
                        "text": "絶対見て",
                        "offset": 3.0,
                        "duration": 2.5,
                        "emphasis": True,
                    },
                ],
            },
            {
                "clip_path": "/tmp/proust2_1.mp4",   # ボディ素材
                "type": "body",
                "start_sec": 8,
                "end_sec": 50,
                "telop": [
                    {
                        "text": "夏よりも冬の方が\nワキガが悪化してた母が",
                        "offset": 0.0,
                        "duration": 3.5,
                        "emphasis": False,
                    },
                    {
                        "text": "感動した",
                        "offset": 3.5,
                        "duration": 2.0,
                        "emphasis": True,
                    },
                    {
                        "text": "ワキガの特攻ケアがヤバイ",
                        "offset": 5.5,
                        "duration": 3.0,
                        "emphasis": True,
                    },
                    {
                        "text": "史上最強の\nワキガ特攻クリーム",
                        "offset": 18.0,
                        "duration": 4.0,
                        "emphasis": False,
                    },
                ],
            },
            {
                "clip_path": "/tmp/proust2_0.mp4",   # CTA素材（同じ素材でも可）
                "type": "cta",
                "start_sec": 50,
                "end_sec": 60,
                "telop": [
                    {
                        "text": "ワキガ悩みに終止符を打ちたい人",
                        "offset": 0.0,
                        "duration": 3.0,
                        "emphasis": False,
                    },
                    {
                        "text": "絶対使ってみて",
                        "offset": 3.0,
                        "duration": 4.0,
                        "emphasis": True,
                    },
                ],
            },
        ],
        "bgm_path": None,
    }

    # ダウンロード済みか確認
    missing = [
        s["clip_path"] for s in PROJECT["segments"]
        if not os.path.exists(s["clip_path"])
    ]
    if missing:
        print("\n⚠️  以下のファイルがありません:")
        for m in missing:
            print(f"  {m}")
        print("\n先に drive_explorer.py でDLしてください")
        print("または clip_path を実際のファイルパスに変更してください")
    else:
        result = build_video(PROJECT, output_filename="proust2_test.mp4")
        if result:
            os.system(f"open {result}")
