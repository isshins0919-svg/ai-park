#!/usr/bin/env python3
"""Phase A — ameru 視覚RAGコーパス構築
- 既存ameru 43枚 + camicks(craft-D2C) + 外部参考LPを統合
- メタデータ付き corpus/ に集約
- metadata.json を生成
"""
import json, shutil, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus"
CORPUS.mkdir(exist_ok=True)
META_PATH = ROOT / "corpus_metadata.json"

VOYAGE = Path("/Users/ca01224/Desktop/一進VOYAGE号")

# --- 1) ameru refs 43枚（既にDL済み） ---
AMERU_REFS = ROOT / "refs"

AMERU_META = {
    "official_smoppi.webp": {"brand":"loveeez","section":"character","genre":"ip_plush","tags":["character","official_ip","sky_blue","cute"]},
    "official_pyonchi.webp": {"brand":"loveeez","section":"character","genre":"ip_plush","tags":["character","official_ip","pink","rabbit"]},
    "official_nyapo.webp": {"brand":"loveeez","section":"character","genre":"ip_plush","tags":["character","official_ip","cream","cat"]},
    "official_ururu.webp": {"brand":"loveeez","section":"character","genre":"ip_plush","tags":["character","official_ip","purple"]},
    "official_paopao.webp": {"brand":"loveeez","section":"character","genre":"ip_plush","tags":["character","official_ip","mint","elephant"]},
    "logos_ameru_logo_main.png": {"brand":"ameru","section":"logo","genre":"d2c_craft","tags":["logo","brand"]},
    "logos_ameru_logo_pink.png": {"brand":"ameru","section":"logo","genre":"d2c_craft","tags":["logo","pink"]},
    "01_zumoppi_hero.png": {"brand":"ameru","section":"hero","genre":"d2c_craft","tags":["amigurumi","sky_blue","sky_background","hero"]},
    "02_package_lifestyle.png": {"brand":"ameru","section":"lifestyle","genre":"d2c_craft","tags":["package","sakura","lifestyle"]},
    "03_unboxing_flatlay.png": {"brand":"ameru","section":"kit","genre":"d2c_craft","tags":["flatlay","kit","unboxing","topdown"]},
    "04_hands_crafting.png": {"brand":"ameru","section":"process","genre":"d2c_craft","tags":["hands","crafting","warm"]},
    "05_lifestyle_finished.png": {"brand":"ameru","section":"lifestyle","genre":"d2c_craft","tags":["finished","hug","emotion"]},
    "06_shelf_display.png": {"brand":"ameru","section":"lifestyle","genre":"d2c_craft","tags":["shelf","display","interior"]},
    "07_collection_preview.png": {"brand":"ameru","section":"lineup","genre":"d2c_craft","tags":["collection","5characters"]},
    "phase1_H01_hero_cloud_blanket.png": {"brand":"ameru","section":"hero","genre":"d2c_craft","tags":["hero","cloud_blanket","morning_light","4:5"]},
    "phase1_H02_hero_pinkbeige_square.png": {"brand":"ameru","section":"hero","genre":"d2c_craft","tags":["hero","pinkbeige","square"]},
    "phase1_H03_hero_wood_table.png": {"brand":"ameru","section":"hero","genre":"d2c_craft","tags":["hero","wood_table","16:9"]},
    "phase1_H04_hero_with_package.png": {"brand":"ameru","section":"hero","genre":"d2c_craft","tags":["hero","package","4:5"]},
    "phase1_H05_hero_face_macro.png": {"brand":"ameru","section":"hero","genre":"d2c_craft","tags":["hero","macro","face"]},
    "phase1_H06_hero_hands_holding.png": {"brand":"ameru","section":"hero","genre":"d2c_craft","tags":["hero","hands","holding"]},
    "phase1_K01_kit_flatlay_woobles.png": {"brand":"ameru","section":"kit","genre":"d2c_craft","tags":["kit","flatlay","woobles_style"]},
    "phase1_K02_yarn_macro_easy_peasy.png": {"brand":"ameru","section":"kit","genre":"d2c_craft","tags":["yarn","macro","easy_peasy"]},
    "phase1_K03_phone_hands_learning.png": {"brand":"ameru","section":"video_tutorial","genre":"d2c_craft","tags":["phone","hands","video","learning"]},
    "phase1_K04_unboxing_moment.png": {"brand":"ameru","section":"kit","genre":"d2c_craft","tags":["unboxing","moment","16:9"]},
    "phase1_L01_lineup_remaster.png": {"brand":"ameru","section":"lineup","genre":"d2c_craft","tags":["lineup","5chars","confetti","16:9"]},
    "phase1_L02_lineup_shelf.png": {"brand":"ameru","section":"lineup","genre":"d2c_craft","tags":["lineup","5chars","shelf","interior"]},
    "phase1_L03_lineup_focus_foreground.png": {"brand":"ameru","section":"lineup","genre":"d2c_craft","tags":["lineup","focus","foreground"]},
    "phase1_L04_lineup_with_charspace.png": {"brand":"ameru","section":"lineup","genre":"d2c_craft","tags":["lineup","5chars","charspace","16:9"]},
    "phase1_T01_bg_pinkbeige_gradient.png": {"brand":"ameru","section":"background","genre":"d2c_craft","tags":["background","pinkbeige","gradient"]},
    "phase1_T02_bg_yarn_negative.png": {"brand":"ameru","section":"background","genre":"d2c_craft","tags":["background","yarn","negative_space"]},
    "phase1_T03_bg_pastel_confetti.png": {"brand":"ameru","section":"background","genre":"d2c_craft","tags":["background","pastel","confetti"]},
    "phase2_P01_timeline_start.png": {"brand":"ameru","section":"process","genre":"d2c_craft","tags":["timeline","start","yarn_ball"]},
    "phase2_P02_timeline_half_head.png": {"brand":"ameru","section":"process","genre":"d2c_craft","tags":["timeline","half","head"]},
    "phase2_P03_timeline_before_face.png": {"brand":"ameru","section":"process","genre":"d2c_craft","tags":["timeline","before_face"]},
    "phase2_P04_timeline_palms.png": {"brand":"ameru","section":"process","genre":"d2c_craft","tags":["timeline","palms","handheld"]},
    "phase2_P05_timeline_before_after.png": {"brand":"ameru","section":"only1_proof","genre":"d2c_craft","tags":["before_after","split","timeline"]},
    "phase2_E01_emotion_hug.png": {"brand":"ameru","section":"emotion","genre":"d2c_craft","tags":["hug","emotion","4:5"]},
    "phase2_E02_emotion_crafting.png": {"brand":"ameru","section":"emotion","genre":"d2c_craft","tags":["crafting","emotion","in_progress"]},
    "phase2_E03_emotion_parent_child.png": {"brand":"ameru","section":"emotion","genre":"d2c_craft","tags":["parent_child","emotion","16:9"]},
    "phase2_E04_emotion_windowsill.png": {"brand":"ameru","section":"lifestyle","genre":"d2c_craft","tags":["windowsill","lifestyle","emotion","4:5"]},
    "phase2_G01_gift_ribbon_card.png": {"brand":"ameru","section":"offer_gift","genre":"d2c_craft","tags":["gift","ribbon","card","package"]},
    "phase2_G02_gift_handover.png": {"brand":"ameru","section":"cta","genre":"d2c_craft","tags":["handover","gift","hands","4:5"]},
    "phase2_G03_gift_child_hands.png": {"brand":"ameru","section":"cta","genre":"d2c_craft","tags":["child_hands","gift","receive","4:5"]},
}

# --- 2) camicks 追加（D2C textile, similar premium craft aesthetic） ---
CAMICKS_SRC = VOYAGE / "banner-park/output/camicks"
CAMICKS_PICKS = [
    ("main_images/main_02_offwhite_pair.png", {"brand":"camicks","section":"hero","genre":"d2c_textile","tags":["offwhite","pair","product","premium"]}),
    ("main_images/main_03_darkgray_top_angle.png", {"brand":"camicks","section":"hero","genre":"d2c_textile","tags":["topangle","darkgray","moody"]}),
    ("main_images/main_04_multicolor_lineup.png", {"brand":"camicks","section":"lineup","genre":"d2c_textile","tags":["lineup","multicolor","colorpalette"]}),
    ("main_images/main_05_lifestyle_foot.png", {"brand":"camicks","section":"lifestyle","genre":"d2c_textile","tags":["lifestyle","foot","natural"]}),
    ("amazon_c_final/amazon_main_v1.png", {"brand":"camicks","section":"hero","genre":"d2c_textile","tags":["amazon","main","hero","clean"]}),
    ("amazon_c_final/amazon_01_c_secret.png", {"brand":"camicks","section":"feature","genre":"d2c_textile","tags":["feature","secret","japanese_craft"]}),
    ("amazon_c_final/amazon_02_c_craft.png", {"brand":"camicks","section":"feature","genre":"d2c_textile","tags":["craft","process","premium"]}),
    ("amazon_c_final/amazon_03_c_washi.png", {"brand":"camicks","section":"feature","genre":"d2c_textile","tags":["washi","texture","macro"]}),
    ("amazon_c_final/amazon_05_c_aesthetic.png", {"brand":"camicks","section":"feature","genre":"d2c_textile","tags":["aesthetic","mood","lifestyle"]}),
    ("amazon_c_final/amazon_06_c_legacy.png", {"brand":"camicks","section":"brand","genre":"d2c_textile","tags":["legacy","heritage","brand_story"]}),
    ("amazon_c_final/amazon_sub03_washi_v2.png", {"brand":"camicks","section":"feature","genre":"d2c_textile","tags":["washi","detail","sub"]}),
    ("amazon_c_final/amazon_sub04_easycare_v2.png", {"brand":"camicks","section":"feature","genre":"d2c_textile","tags":["easycare","function","sub"]}),
    ("amazon_c_final/amazon_sub05_lifestyle_v2.png", {"brand":"camicks","section":"lifestyle","genre":"d2c_textile","tags":["lifestyle","wearing","sub"]}),
]

# --- 3) 外部 prime benchmark ---
# The Woobles 公式画像 (CDN pattern) + Craftie / Fujimi 相当
EXTERNAL = [
    ("woobles_hero1.png", "https://thewoobles.com/cdn/shop/files/BopBearBetaThumbnail_1080x.png?v=1699399131",
     {"brand":"the_woobles","section":"hero","genre":"d2c_craft_bench","tags":["hero","beginner","crochet_kit","usa"]}),
    ("woobles_hero2.png", "https://thewoobles.com/cdn/shop/files/Octopus_Thumbnail_c10ee7eb-fc34-4bb7-a1a5-5691a2aba9b1_1080x.png?v=1699399145",
     {"brand":"the_woobles","section":"hero","genre":"d2c_craft_bench","tags":["hero","octopus","pink","beginner"]}),
]

def copy_all():
    meta = {}
    # 1) ameru refs
    n1 = 0
    for fname, m in AMERU_META.items():
        src = AMERU_REFS / fname
        if src.exists():
            shutil.copy(src, CORPUS / fname)
            meta[fname] = m
            n1 += 1
    print(f"✅ ameru: {n1} copied")

    # 2) camicks
    n2 = 0
    for rel, m in CAMICKS_PICKS:
        src = CAMICKS_SRC / rel
        if src.exists():
            dst_name = f"camicks_{Path(rel).name}"
            shutil.copy(src, CORPUS / dst_name)
            meta[dst_name] = m
            n2 += 1
        else:
            print(f"  ⚠️  skip {rel}")
    print(f"✅ camicks: {n2} copied")

    # 3) external DL
    n3 = 0
    for fname, url, m in EXTERNAL:
        dst = CORPUS / fname
        if dst.exists() and dst.stat().st_size > 1000:
            meta[fname] = m
            n3 += 1
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                dst.write_bytes(r.read())
            meta[fname] = m
            n3 += 1
            print(f"  ✅ {fname}")
        except Exception as e:
            print(f"  ❌ {fname}: {e}")
    print(f"✅ external: {n3}")

    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"\n=== total {len(meta)} in corpus/ → {META_PATH.name} ===")

if __name__ == "__main__":
    copy_all()
