#!/usr/bin/env python3
"""
Short Ad Park v7.0 — mauri MANUKA HONEY
実素材 × デスマス調連続トーク × Fish Audio TTS × moviepy assembly
"""

import os, json, time, subprocess, requests
from pathlib import Path
from PIL import Image
import numpy as np

# ─── 環境変数ロード ───────────────────────────────────────
def load_env(var):
    val = os.environ.get(var, '').strip()
    if not val:
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'],
                               capture_output=True, text=True, timeout=5)
            val = r.stdout.strip()
            if val:
                os.environ[var] = val
        except Exception:
            pass
    return val

for v in ['GEMINI_API_KEY', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3',
          'XAI_API_KEY', 'FISH_AUDIO_API_KEY']:
    load_env(v)

FISH_KEY  = os.environ.get('FISH_AUDIO_API_KEY', '')
XAI_KEY   = os.environ.get('XAI_API_KEY', '')
GEMINI_KEYS = [os.environ.get(k, '') for k in
               ['GEMINI_API_KEY', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

# ─── パス設定 ─────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent
ASSET_BASE = Path('/Users/ca01224/Desktop/mauriのデータ/mauri素材フォルダー')
OUT_DIR    = BASE_DIR / 'output' / 'mauri-v7'
SCRIPT_PATH = BASE_DIR / 'scripts' / 'mauri-v7-script.json'

for d in [OUT_DIR/'audio', OUT_DIR/'clips', OUT_DIR/'images']:
    d.mkdir(parents=True, exist_ok=True)

# ─── 台本ロード ───────────────────────────────────────────
with open(SCRIPT_PATH) as f:
    SCRIPT = json.load(f)

HOOKS   = SCRIPT['hooks']
SCENES  = SCRIPT['scenes']
VOICE_ID = SCRIPT['settings']['voice']['referenceId']
W, H     = SCRIPT['settings']['width'], SCRIPT['settings']['height']
FPS      = SCRIPT['settings']['fps']

# ─── フォント ──────────────────────────────────────────────
FONT = '/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc'
if not Path(FONT).exists():
    FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'

# ══════════════════════════════════════════════════════════
# Phase 1: Fish Audio TTS 生成
# ══════════════════════════════════════════════════════════

def generate_tts(text: str, out_path: Path) -> bool:
    if out_path.exists() and out_path.stat().st_size > 5000:
        print(f"  [SKIP] {out_path.name}")
        return True
    if not text.strip():
        return True  # S15 は無音
    print(f"  [TTS] {text[:30]}...")
    try:
        resp = requests.post(
            'https://api.fish.audio/v1/tts',
            headers={'Authorization': f'Bearer {FISH_KEY}',
                     'Content-Type': 'application/json'},
            json={'text': text,
                  'reference_id': VOICE_ID,
                  'format': 'mp3',
                  'latency': 'normal'},
            timeout=60
        )
        if resp.status_code == 200:
            out_path.write_bytes(resp.content)
            print(f"  [OK] {out_path.name} ({len(resp.content)//1024}KB)")
            return True
        else:
            print(f"  [ERR] TTS HTTP {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"  [ERR] TTS exception: {e}")
        return False

def generate_all_tts():
    print("\n=== Phase 1: TTS生成 ===")
    for hook_key, hook in HOOKS.items():
        path = OUT_DIR / 'audio' / f'hook_{hook_key.lower()}_narration.mp3'
        generate_tts(hook['narration'], path)
        time.sleep(0.5)
    for scene in SCENES:
        if scene['role'] == 'HOOK':
            continue  # hookはフック別で生成済み
        text = scene.get('narration', '')
        path = OUT_DIR / 'audio' / f"{scene['id']}.mp3"
        generate_tts(text, path)
        time.sleep(0.5)

# ══════════════════════════════════════════════════════════
# Phase 2: 素材準備（画像リサイズ + 動画変換）
# ══════════════════════════════════════════════════════════

def prepare_image(src_path: Path, out_path: Path) -> bool:
    """webp/png/jpg → 720x1280 JPG に変換（縦型クロップ）"""
    if out_path.exists():
        return True
    try:
        img = Image.open(src_path).convert('RGB')
        iw, ih = img.size
        # アスペクト比に応じてリサイズ&クロップ
        target_ratio = W / H  # 720/1280 = 0.5625
        src_ratio = iw / ih
        if src_ratio > target_ratio:
            # 横が長い → 高さに合わせてリサイズし横をクロップ
            new_h = H
            new_w = int(iw * (H / ih))
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - W) // 2
            img = img.crop((left, 0, left + W, H))
        else:
            # 縦が長い → 幅に合わせてリサイズし縦をクロップ（上1/3を使用）
            new_w = W
            new_h = int(ih * (W / iw))
            img = img.resize((new_w, new_h), Image.LANCZOS)
            top = min(new_h // 6, new_h - H) if new_h > H else 0
            img = img.crop((0, top, W, top + H))
        img.save(out_path, 'JPEG', quality=92)
        print(f"  [IMG] {out_path.name}")
        return True
    except Exception as e:
        print(f"  [ERR] Image {src_path.name}: {e}")
        return False

def prepare_video(src_path: Path, out_path: Path, duration: float) -> bool:
    """mp4 → 720x1280 × duration秒 に変換"""
    if out_path.exists():
        return True
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        print("  [WARN] ffmpeg not found, falling back to image")
        return False
    try:
        cmd = [ffmpeg, '-y', '-i', str(src_path),
               '-vf', f'scale=-1:{H},crop={W}:{H}',
               '-t', str(duration),
               '-c:v', 'libx264', '-crf', '23',
               '-an', str(out_path)]
        subprocess.run(cmd, capture_output=True, timeout=60)
        if out_path.exists() and out_path.stat().st_size > 10000:
            print(f"  [VID] {out_path.name}")
            return True
        return False
    except Exception as e:
        print(f"  [ERR] Video prep {src_path.name}: {e}")
        return False

def _find_ffmpeg():
    for candidate in [
        '/usr/local/bin/ffmpeg',
        '/opt/homebrew/bin/ffmpeg',
        '/Users/ca01224/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1',
    ]:
        if Path(candidate).exists():
            return candidate
    try:
        r = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        p = r.stdout.strip()
        if p:
            return p
    except Exception:
        pass
    return None

def prepare_all_assets():
    print("\n=== Phase 2: 素材準備 ===")
    # hook assets
    for hook_key, hook in HOOKS.items():
        src = ASSET_BASE / hook['asset']
        if hook['assetType'] == 'image':
            out = OUT_DIR / 'images' / f'hook_{hook_key.lower()}.jpg'
            prepare_image(src, out)
        else:
            out = OUT_DIR / 'clips' / f'hook_{hook_key.lower()}.mp4'
            prepare_video(src, out, 2.0)
    # scene assets
    for scene in SCENES:
        if scene['role'] == 'HOOK':
            continue
        src = ASSET_BASE / scene['asset']
        sid = scene['id']
        if scene['assetType'] == 'image':
            out = OUT_DIR / 'images' / f'{sid}.jpg'
            prepare_image(src, out)
        else:
            out = OUT_DIR / 'clips' / f'{sid}.mp4'
            prepare_video(src, out, scene['duration'])

# ══════════════════════════════════════════════════════════
# Phase 3: moviepy アセンブル
# ══════════════════════════════════════════════════════════

def ken_burns(img_path: Path, duration: float, zoom_start=1.0, zoom_end=1.08):
    """Ken Burnsエフェクト付き VideoClip 生成 (moviepy 2.x対応)"""
    from moviepy import VideoClip
    img = Image.open(img_path).convert('RGB').resize((W, H), Image.LANCZOS)
    arr = np.array(img)
    def make_frame(t):
        progress = t / max(duration, 0.001)
        zoom = zoom_start + (zoom_end - zoom_start) * progress
        zh = int(H * zoom)
        zw = int(W * zoom)
        zoomed = np.array(Image.fromarray(arr).resize((zw, zh), Image.LANCZOS))
        cy = (zh - H) // 2
        cx = (zw - W) // 2
        return zoomed[cy:cy+H, cx:cx+W]
    clip = VideoClip(make_frame, duration=duration)
    clip.fps = FPS
    return clip

def make_telop(text: str, duration: float, y_rel=0.55):
    """テロップ TextClip（白文字・黒縁）"""
    from moviepy import TextClip
    try:
        tc = TextClip(
            text=text,
            font=FONT,
            font_size=52,
            color='white',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(W - 60, None),
            text_align='center'
        ).with_duration(duration)
        return tc.with_position(('center', int(H * y_rel)))
    except Exception as e:
        print(f"  [WARN] TextClip error: {e}")
        return None

def get_audio_duration(audio_path: Path) -> float:
    """音声ファイルの実際の長さを取得"""
    from moviepy import AudioFileClip
    try:
        a = AudioFileClip(str(audio_path))
        d = a.duration
        a.close()
        return d
    except Exception:
        return 2.0

def assemble_hook(hook_key: str):
    """1本のフック動画を生成 — 音声ドリブン（音声長さ＝映像尺）"""
    from moviepy import (VideoFileClip, AudioFileClip,
                         CompositeVideoClip, concatenate_videoclips)
    from moviepy import ColorClip

    print(f"\n=== Phase 3: アセンブル Hook-{hook_key} ===")
    hook = HOOKS[hook_key]
    clips = []          # 映像クリップリスト（順番に並べる）
    audio_segments = [] # (audio_clip, start_time) のリスト

    AUDIO_DIR = OUT_DIR / 'audio_fast'
    current_t = 0.0

    def get_video_clip(scene_id, asset_type, duration):
        """映像クリップを duration 秒で取得"""
        if asset_type == 'video':
            clip_path = OUT_DIR / 'clips' / f'{scene_id}.mp4'
            if clip_path.exists():
                vc = VideoFileClip(str(clip_path))
                # ループが必要な場合はB-roll代わりに同じクリップを繰り返す
                if vc.duration < duration:
                    from moviepy import concatenate_videoclips as cat
                    n = int(duration / vc.duration) + 1
                    vc = cat([vc] * n)
                return vc.subclipped(0, duration).resized((W, H))
        img_path = OUT_DIR / 'images' / f'{scene_id}.jpg'
        if img_path.exists():
            return ken_burns(img_path, duration)
        print(f"  [WARN] No asset for {scene_id}, using color clip")
        return ColorClip((W, H), color=(30, 20, 10), duration=duration)

    # ─── シーン1: HOOK ───────────────────────────────────
    hook_audio_path = AUDIO_DIR / f'hook_{hook_key.lower()}_narration.mp3'
    hook_dur = get_audio_duration(hook_audio_path) if hook_audio_path.exists() else 2.0
    hook_dur = max(hook_dur, 1.0)  # 最低1秒

    if hook['assetType'] == 'video':
        vc = get_video_clip(f'hook_{hook_key.lower()}', 'video', hook_dur)
    else:
        img_path = OUT_DIR / 'images' / f'hook_{hook_key.lower()}.jpg'
        vc = ken_burns(img_path, hook_dur)

    telop = make_telop(hook['overlayText'], hook_dur)
    sc = CompositeVideoClip([vc] + ([telop] if telop else []))
    clips.append(sc)
    if hook_audio_path.exists():
        audio_segments.append((AudioFileClip(str(hook_audio_path)), current_t))
    print(f"  scene_01 [HOOK-{hook_key}] {hook_dur:.2f}s")
    current_t += hook_dur

    # ─── シーン2〜15 ─────────────────────────────────────
    for scene in SCENES:
        if scene['role'] == 'HOOK':
            continue

        sid = scene['id']
        asset_type = scene['assetType']
        has_narration = bool(scene.get('narration', '').strip())

        # 音声の長さで映像尺を決定
        if has_narration:
            audio_path = AUDIO_DIR / f'{sid}.mp3'
            dur = get_audio_duration(audio_path) if audio_path.exists() else scene['duration']
        else:
            dur = scene['duration']  # CTA_FINAL等の無音シーン
        dur = max(dur, 0.5)

        vc = get_video_clip(sid, asset_type, dur)
        telop = make_telop(scene['overlayText'], dur)
        sc = CompositeVideoClip([vc] + ([telop] if telop else []))
        clips.append(sc)

        if has_narration:
            audio_path = AUDIO_DIR / f'{sid}.mp3'
            if audio_path.exists():
                audio_segments.append((AudioFileClip(str(audio_path)), current_t))

        print(f"  {sid} [{scene['role']}] {dur:.2f}s")
        current_t += dur

    print(f"  合計: {current_t:.1f}s")

    # ─── 結合 ────────────────────────────────────────────
    final_video = concatenate_videoclips(clips, method='compose')

    if audio_segments:
        from moviepy import CompositeAudioClip
        mixed = CompositeAudioClip([a.with_start(t) for a, t in audio_segments])
        final_video = final_video.with_audio(mixed)

    out_path = OUT_DIR / f'final-hook{hook_key}-v7.mp4'
    print(f"  [EXPORT] {out_path.name}...")
    final_video.write_videofile(
        str(out_path),
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        logger=None
    )
    # クリーンアップ
    for a, _ in audio_segments:
        try: a.close()
        except Exception: pass

    print(f"  [DONE] {out_path.name} ({out_path.stat().st_size // 1024}KB)")
    return out_path

# ══════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    hooks_to_run = sys.argv[1:] if len(sys.argv) > 1 else ['A', 'B', 'C']

    print("━" * 50)
    print("  SHORT AD PARK v7.0 — mauri MANUKA HONEY")
    print("━" * 50)
    print(f"  生成フック: {hooks_to_run}")
    print(f"  Fish Audio: {'✅' if FISH_KEY else '❌'}")
    print(f"  出力先: {OUT_DIR}")
    print("━" * 50)

    # Phase 1: TTS
    generate_all_tts()

    # Phase 2: 素材準備
    prepare_all_assets()

    # Phase 3: アセンブル
    results = []
    for hk in hooks_to_run:
        if hk not in HOOKS:
            print(f"[SKIP] Hook {hk} not defined")
            continue
        try:
            out = assemble_hook(hk)
            results.append(f"✅ Hook-{hk}: {out}")
        except Exception as e:
            results.append(f"❌ Hook-{hk}: {e}")
            import traceback; traceback.print_exc()

    print("\n" + "━" * 50)
    print("  完了レポート")
    print("━" * 50)
    for r in results:
        print(f"  {r}")
    print(f"\n  出力フォルダ: {OUT_DIR}")
    print("━" * 50)
