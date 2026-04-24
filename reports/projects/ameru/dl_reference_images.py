#!/usr/bin/env python3
"""ameru既存43画像をai-parkからDL。
ローカル: reports/projects/ameru/refs/
"""
import urllib.request
from pathlib import Path

BASE = "https://isshins0919-svg.github.io/ai-park/clients/ameru_new/"
OUT = Path(__file__).parent / "refs"
OUT.mkdir(exist_ok=True)

# 公式5キャラ (loveeez.com)
OFFICIAL = [
    ("official_smoppi.webp", "https://loveeez.com/assets/imgs/home/friends_smoppi_info.webp"),
    ("official_pyonchi.webp", "https://loveeez.com/assets/imgs/home/friends_pyonchi_info.webp"),
    ("official_nyapo.webp", "https://loveeez.com/assets/imgs/home/friends_nyapo_info.webp"),
    ("official_ururu.webp", "https://loveeez.com/assets/imgs/home/friends_ururu_info.webp"),
    ("official_paopao.webp", "https://loveeez.com/assets/imgs/home/friends_paopao_info.webp"),
]

# ai-park既存画像
PATHS = [
    "images/logos/ameru_logo_main.png",
    "images/logos/ameru_logo_pink.png",
    "images/01_zumoppi_hero.png",
    "images/02_package_lifestyle.png",
    "images/03_unboxing_flatlay.png",
    "images/04_hands_crafting.png",
    "images/05_lifestyle_finished.png",
    "images/06_shelf_display.png",
    "images/07_collection_preview.png",
    "images/phase1/H01_hero_cloud_blanket.png",
    "images/phase1/H02_hero_pinkbeige_square.png",
    "images/phase1/H03_hero_wood_table.png",
    "images/phase1/H04_hero_with_package.png",
    "images/phase1/H05_hero_face_macro.png",
    "images/phase1/H06_hero_hands_holding.png",
    "images/phase1/K01_kit_flatlay_woobles.png",
    "images/phase1/K02_yarn_macro_easy_peasy.png",
    "images/phase1/K03_phone_hands_learning.png",
    "images/phase1/K04_unboxing_moment.png",
    "images/phase1/L01_lineup_remaster.png",
    "images/phase1/L02_lineup_shelf.png",
    "images/phase1/L03_lineup_focus_foreground.png",
    "images/phase1/L04_lineup_with_charspace.png",
    "images/phase1/T01_bg_pinkbeige_gradient.png",
    "images/phase1/T02_bg_yarn_negative.png",
    "images/phase1/T03_bg_pastel_confetti.png",
    "images/phase2/P01_timeline_start.png",
    "images/phase2/P02_timeline_half_head.png",
    "images/phase2/P03_timeline_before_face.png",
    "images/phase2/P04_timeline_palms.png",
    "images/phase2/P05_timeline_before_after.png",
    "images/phase2/E01_emotion_hug.png",
    "images/phase2/E02_emotion_crafting.png",
    "images/phase2/E03_emotion_parent_child.png",
    "images/phase2/E04_emotion_windowsill.png",
    "images/phase2/G01_gift_ribbon_card.png",
    "images/phase2/G02_gift_handover.png",
    "images/phase2/G03_gift_child_hands.png",
]

def dl(url: str, out: Path) -> bool:
    if out.exists() and out.stat().st_size > 1000:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            out.write_bytes(r.read())
        print(f"  ✅ {out.name} ({out.stat().st_size//1024}KB)")
        return True
    except Exception as e:
        print(f"  ❌ {out.name}: {e}")
        return False

if __name__ == "__main__":
    print(f"=== DL 43 ameru reference images ===")
    ok = 0
    for name, url in OFFICIAL:
        if dl(url, OUT / name): ok += 1
    for p in PATHS:
        name = p.replace("/", "_").replace("images_", "")
        if dl(BASE + p, OUT / name): ok += 1
    print(f"\n=== {ok}/{len(OFFICIAL)+len(PATHS)} DL完了 ===")
