#!/usr/bin/env python3
"""
Banner Park v3 — mauri MANUKA HONEY
実写商品画像 × Pillow合成 × ヒラギノ角ゴシック
blur不要の本番クオリティバナー 5枚 (1080×1080)
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

# ── パス設定 ──────────────────────────────────────────
ASSETS_DIR = "/Users/ca01224/Desktop/mauriのデータ/mauri素材フォルダー/mauri-商品画像"
OUTPUT_DIR = "/Users/ca01224/Desktop/AI一進-Claude-Code/banner-park/output/mauri/banners_v3"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── フォント ───────────────────────────────────────────
FONT_W9 = "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc"
FONT_W8 = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_W6 = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_W3 = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"

SIZE = (1080, 1080)


# ── ユーティリティ関数 ────────────────────────────────────

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def smart_crop(img: Image.Image, target_w: int, target_h: int,
               anchor: str = "center") -> Image.Image:
    """アスペクト比を保ちながら中央/上/下クロップ"""
    orig_w, orig_h = img.size
    ratio = max(target_w / orig_w, target_h / orig_h)
    new_w = int(orig_w * ratio)
    new_h = int(orig_h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    if anchor == "top":
        top = 0
    elif anchor == "bottom":
        top = new_h - target_h
    else:
        top = (new_h - target_h) // 2
    left = (new_w - target_w) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def add_gradient_overlay(img: Image.Image, direction: str = "bottom",
                          color: tuple = (0, 0, 0),
                          alpha_start: int = 0, alpha_end: int = 180) -> Image.Image:
    """グラデーションオーバーレイを重ねる"""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steps = h if direction in ("top", "bottom") else w
    for i in range(steps):
        t = i / steps
        if direction == "bottom":
            t = t
        elif direction == "top":
            t = 1 - t
        elif direction == "left":
            t = 1 - (i / steps)
        else:
            t = i / steps
        alpha = int(alpha_start + (alpha_end - alpha_start) * t)
        r, g, b = color
        if direction in ("top", "bottom"):
            draw.line([(0, i), (w, i)], fill=(r, g, b, alpha))
        else:
            draw.line([(i, 0), (i, h)], fill=(r, g, b, alpha))
    result = Image.alpha_composite(img.convert("RGBA"), overlay)
    return result


def add_dark_overlay(img: Image.Image, alpha: int = 100,
                     color: tuple = (0, 0, 0)) -> Image.Image:
    """全面単色オーバーレイ"""
    overlay = Image.new("RGBA", img.size, (*color, alpha))
    result = Image.alpha_composite(img.convert("RGBA"), overlay)
    return result


def draw_text_shadow(draw, pos, text, font, fill, shadow_offset=3, shadow_alpha=160):
    """影付きテキスト描画"""
    x, y = pos
    shadow = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.text((x + shadow_offset, y + shadow_offset), text, font=font,
               fill=(0, 0, 0, shadow_alpha))
    return shadow


def draw_multiline_centered(draw, text, font, y_start, canvas_w,
                              fill, line_spacing=1.15,
                              shadow=True, shadow_img=None, shadow_draw=None):
    """複数行テキストを中央揃えで描画"""
    lines = text.split("\n")
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        line_widths.append(lw)
        line_heights.append(lh)

    single_h = max(line_heights) if line_heights else 40
    step = int(single_h * line_spacing)

    y = y_start
    for i, line in enumerate(lines):
        lw = line_widths[i]
        x = (canvas_w - lw) // 2
        if shadow and shadow_draw is not None:
            shadow_draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), line, font=font, fill=fill)
        y += step
    return y  # 最終行の下端Y


def add_badge(img: Image.Image, text: str, x: int, y: int,
              bg_color: tuple, text_color: tuple, font,
              padding_x: int = 20, padding_y: int = 10,
              radius: int = 8) -> Image.Image:
    """角丸バッジを貼る"""
    draw_tmp = ImageDraw.Draw(img)
    bbox = draw_tmp.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bw = tw + padding_x * 2
    bh = th + padding_y * 2
    overlay = img.copy().convert("RGBA")
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=radius, fill=(*bg_color, 230))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img)
    draw.text((x + padding_x, y + padding_y), text, font=font, fill=text_color)
    return img


def add_cta_button(img: Image.Image, text: str, y: int,
                   bg_color: tuple, text_color: tuple, font,
                   width: int = 680, height: int = 88,
                   radius: int = 44) -> Image.Image:
    """中央揃えCTAボタン"""
    iw, ih = img.size
    x = (iw - width) // 2
    overlay = img.copy().convert("RGBA")
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle([x, y, x + width, y + height], radius=radius,
                         fill=(*bg_color, 245))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (iw - tw) // 2
    ty = y + (height - th) // 2
    draw.text((tx, ty), text, font=font, fill=text_color)
    return img


def add_brand_bar(img: Image.Image, brand_text: str = "mauri MANUKA HONEY",
                  sub_text: str = "NZ直送 | 政府認定ラボ証明書つき") -> Image.Image:
    """上部ブランドバー"""
    bar_h = 72
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # 上部黒バー
    draw.rectangle([0, 0, img.size[0], bar_h], fill=(20, 15, 10, 210))
    # ブランド名（アンバーゴールド）
    font_brand = load_font(FONT_W8, 26)
    font_sub = load_font(FONT_W3, 20)
    draw.text((54, 13), brand_text, font=font_brand, fill=(212, 175, 55, 255))
    draw.text((54, 43), sub_text, font=font_sub, fill=(220, 200, 160, 220))
    result = Image.alpha_composite(img.convert("RGBA"), overlay)
    return result


def finalize(img: Image.Image) -> Image.Image:
    """RGBA→RGB変換（白背景合成）"""
    bg = Image.new("RGB", img.size, (255, 255, 255))
    if img.mode == "RGBA":
        bg.paste(img, mask=img.split()[3])
    else:
        bg.paste(img)
    return bg


# ── Banner 01: 常識否定型 ─────────────────────────────────
# 素材: HG_109335.jpg（アンバー背景×蜂蜜ドリップ×花）
# コピー: 「そのマヌカハニー/本物ですか？」
def build_banner_01():
    print("  Building banner_01_v3.png (常識否定型)...")
    src = Image.open(os.path.join(ASSETS_DIR, "HG_109335.jpg"))
    img = smart_crop(src, 1080, 1080, anchor="center")

    # ボトム側に濃いグラデ → テキスト可読性UP
    img = add_gradient_overlay(img, "bottom", color=(10, 5, 0),
                                alpha_start=0, alpha_end=220)
    # 上部に薄いグラデ
    img = add_gradient_overlay(img, "top", color=(10, 5, 0),
                                alpha_start=80, alpha_end=0)

    # シャドウ用レイヤー
    shadow_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    img_rgba = img.convert("RGBA")
    draw = ImageDraw.Draw(img_rgba)

    # ── ブランドバー
    img_rgba = add_brand_bar(img_rgba, "mauri MANUKA HONEY", "NZ産 政府認定ラボ証明書つき")

    # ── バッジ「衝撃の事実」
    font_badge = load_font(FONT_W8, 24)
    img_rgba = add_badge(img_rgba, "衝撃の事実", 50, 100,
                         bg_color=(180, 30, 30), text_color=(255, 255, 255),
                         font=font_badge, padding_x=18, padding_y=10, radius=6)

    # ── メインコピー（2行）
    font_main = load_font(FONT_W9, 88)
    draw = ImageDraw.Draw(img_rgba)
    text_main = "そのマヌカハニー\n本物ですか？"
    shadow_draw.text((50 + 4, 580 + 4), "そのマヌカハニー", font=font_main, fill=(0, 0, 0, 200))
    shadow_draw.text((50 + 4, 680 + 4), "本物ですか？", font=font_main, fill=(0, 0, 0, 200))
    img_rgba = Image.alpha_composite(img_rgba, shadow_layer)
    draw = ImageDraw.Draw(img_rgba)
    draw.text((50, 580), "そのマヌカハニー", font=font_main, fill=(255, 255, 255))
    draw.text((50, 680), "本物ですか？", font=font_main, fill=(212, 175, 55))  # ゴールド

    # ── サブコピー
    font_sub = load_font(FONT_W6, 34)
    draw.text((50, 790), "市販品の多くは表示MGO値と実測値が違う", font=font_sub,
              fill=(220, 200, 160))

    # ── CTAボタン
    font_cta = load_font(FONT_W8, 34)
    img_rgba = add_cta_button(img_rgba, "本物を確認する  →", 960,
                               bg_color=(212, 175, 55), text_color=(20, 10, 0),
                               font=font_cta, width=700, height=80, radius=40)

    img_final = finalize(img_rgba)
    img_final.save(os.path.join(OUTPUT_DIR, "banner_01_v3.png"), quality=95)
    print("    ✅ banner_01_v3.png")


# ── Banner 02: 恐怖訴求型（MGO実測値） ──────────────────────
# 素材: HG_109147.jpg（ウッド×蜂蜜×白花）
# コピー: 「MGO263+の実力/本当にある？」
def build_banner_02():
    print("  Building banner_02_v3.png (恐怖訴求型)...")
    src = Image.open(os.path.join(ASSETS_DIR, "HG_109147.jpg"))
    img = smart_crop(src, 1080, 1080, anchor="center")

    # 全体に薄い暗め + 左側グラデ（テキストエリア確保）
    img = add_dark_overlay(img, alpha=40, color=(0, 0, 0))
    img = add_gradient_overlay(img, "top", color=(5, 10, 5),
                                alpha_start=200, alpha_end=0)

    shadow_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    img_rgba = img.convert("RGBA")

    # ── ブランドバー
    img_rgba = add_brand_bar(img_rgba, "mauri MANUKA HONEY", "MGO実測値345 | 農薬不検出")

    # ── バッジ「要注意」
    font_badge = load_font(FONT_W8, 24)
    img_rgba = add_badge(img_rgba, "⚠ 要注意", 50, 100,
                         bg_color=(200, 100, 0), text_color=(255, 255, 255),
                         font=font_badge, padding_x=18, padding_y=10, radius=6)

    # ── メインコピー
    font_main = load_font(FONT_W9, 80)
    shadow_draw.text((54, 570), "MGO263+の実力", font=font_main, fill=(0, 0, 0, 200))
    shadow_draw.text((54, 662), "本当にある？", font=font_main, fill=(0, 0, 0, 200))
    img_rgba = Image.alpha_composite(img_rgba, shadow_layer)
    draw = ImageDraw.Draw(img_rgba)
    draw.text((54, 570), "MGO263+の実力", font=font_main, fill=(255, 255, 255))
    draw.text((54, 662), "本当にある？", font=font_main, fill=(255, 220, 60))

    # ── 数値バッジ（権威）
    font_num = load_font(FONT_W9, 54)
    font_label = load_font(FONT_W3, 26)
    draw.text((54, 780), "実測MGO  345", font=font_num, fill=(212, 175, 55))
    draw.text((54, 846), "政府認定ラボ検査済み｜農薬不検出証明", font=font_label,
              fill=(200, 185, 140))

    # ── CTA
    font_cta = load_font(FONT_W8, 34)
    img_rgba = add_cta_button(img_rgba, "証明書を確認する  →", 960,
                               bg_color=(255, 255, 255), text_color=(20, 20, 20),
                               font=font_cta, width=700, height=80, radius=40)

    img_final = finalize(img_rgba)
    img_final.save(os.path.join(OUTPUT_DIR, "banner_02_v3.png"), quality=95)
    print("    ✅ banner_02_v3.png")


# ── Banner 03: 共感型（毎朝ライフスタイル） ──────────────────
# 素材: 250130_mauri_撮影-1.jpg（フルーツ×パン×植物）
# コピー: 「毎朝1杯/本物が体を守る」
def build_banner_03():
    print("  Building banner_03_v3.png (共感型)...")
    src = Image.open(os.path.join(ASSETS_DIR, "250130_mauri_撮影-1.jpg"))
    img = smart_crop(src, 1080, 1080, anchor="center")

    # 上部グラデ（ブランドバー下まで） + ボトムグラデ（CTAエリア）
    img = add_gradient_overlay(img, "top", color=(10, 8, 5),
                                alpha_start=180, alpha_end=0)
    img = add_gradient_overlay(img, "bottom", color=(10, 8, 5),
                                alpha_start=0, alpha_end=200)

    shadow_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    img_rgba = img.convert("RGBA")

    # ── ブランドバー
    img_rgba = add_brand_bar(img_rgba, "mauri MANUKA HONEY", "毎日の習慣に。NZから直送")

    # ── ハート的バッジ
    font_badge = load_font(FONT_W8, 24)
    img_rgba = add_badge(img_rgba, "60代女性に選ばれてます", 50, 100,
                         bg_color=(30, 100, 60), text_color=(255, 255, 255),
                         font=font_badge, padding_x=18, padding_y=10, radius=6)

    # ── メインコピー
    font_main = load_font(FONT_W9, 88)
    shadow_draw.text((54, 580), "毎朝1杯", font=font_main, fill=(0, 0, 0, 200))
    shadow_draw.text((54, 678), "本物が体を守る", font=font_main, fill=(0, 0, 0, 200))
    img_rgba = Image.alpha_composite(img_rgba, shadow_layer)
    draw = ImageDraw.Draw(img_rgba)
    draw.text((54, 580), "毎朝1杯", font=font_main, fill=(255, 255, 255))
    draw.text((54, 678), "本物が体を守る", font=font_main, fill=(180, 230, 160))

    # ── サブコピー
    font_sub = load_font(FONT_W6, 32)
    draw.text((54, 800), "運動・野菜・サプリ…それでも不安なあなたへ", font=font_sub,
              fill=(220, 210, 190))

    # ── CTA
    font_cta = load_font(FONT_W8, 34)
    img_rgba = add_cta_button(img_rgba, "はじめてみる  →", 960,
                               bg_color=(212, 175, 55), text_color=(10, 10, 10),
                               font=font_cta, width=680, height=80, radius=40)

    img_final = finalize(img_rgba)
    img_final.save(os.path.join(OUTPUT_DIR, "banner_03_v3.png"), quality=95)
    print("    ✅ banner_03_v3.png")


# ── Banner 04: 権威証明型（ブランドKV） ─────────────────────
# 素材: mauri_KV_logo.png（2瓶×ディッパー×アンバー背景）
# コピー: 「現役薬剤師も/毎日食べるマヌカハニー」
def build_banner_04():
    print("  Building banner_04_v3.png (権威証明型)...")
    src = Image.open(os.path.join(ASSETS_DIR, "mauri_KV_logo.png"))
    img = smart_crop(src, 1080, 1080, anchor="center")

    img = add_gradient_overlay(img, "top", color=(10, 6, 2),
                                alpha_start=240, alpha_end=0)
    img = add_gradient_overlay(img, "bottom", color=(10, 6, 2),
                                alpha_start=0, alpha_end=220)

    shadow_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    img_rgba = img.convert("RGBA")

    # ── ブランドバー
    img_rgba = add_brand_bar(img_rgba, "mauri MANUKA HONEY", "NZ産 MGO実測345 農薬不検出")

    # ── 権威バッジ
    font_badge = load_font(FONT_W8, 24)
    img_rgba = add_badge(img_rgba, "現役薬剤師推薦", 54, 100,
                         bg_color=(20, 60, 120), text_color=(255, 255, 255),
                         font=font_badge, padding_x=18, padding_y=10, radius=6)

    # ── メインコピー
    font_main = load_font(FONT_W9, 78)
    shadow_draw.text((54, 600), "現役薬剤師も", font=font_main, fill=(0, 0, 0, 200))
    shadow_draw.text((54, 690), "毎日食べる", font=font_main, fill=(0, 0, 0, 200))
    shadow_draw.text((54, 780), "マヌカハニー", font=font_main, fill=(0, 0, 0, 200))
    img_rgba = Image.alpha_composite(img_rgba, shadow_layer)
    draw = ImageDraw.Draw(img_rgba)
    draw.text((54, 600), "現役薬剤師も", font=font_main, fill=(255, 255, 255))
    draw.text((54, 690), "毎日食べる", font=font_main, fill=(212, 175, 55))
    draw.text((54, 780), "マヌカハニー", font=font_main, fill=(255, 255, 255))

    # ── CTA
    font_cta = load_font(FONT_W8, 34)
    img_rgba = add_cta_button(img_rgba, "品質を確認する  →", 975,
                               bg_color=(212, 175, 55), text_color=(10, 10, 10),
                               font=font_cta, width=700, height=80, radius=40)

    img_final = finalize(img_rgba)
    img_final.save(os.path.join(OUTPUT_DIR, "banner_04_v3.png"), quality=95)
    print("    ✅ banner_04_v3.png")


# ── Banner 05: 価格オファー型 ─────────────────────────────
# 素材: HG_109397.jpg（手×スプーン×ライフスタイル）
# コピー: 「初回2,980円/今だけ特別価格」
def build_banner_05():
    print("  Building banner_05_v3.png (価格オファー型)...")
    src = Image.open(os.path.join(ASSETS_DIR, "HG_109397.jpg"))
    img = smart_crop(src, 1080, 1080, anchor="top")

    img = add_gradient_overlay(img, "top", color=(5, 5, 5),
                                alpha_start=160, alpha_end=0)
    img = add_gradient_overlay(img, "bottom", color=(5, 5, 5),
                                alpha_start=0, alpha_end=230)

    shadow_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    img_rgba = img.convert("RGBA")

    # ── ブランドバー
    img_rgba = add_brand_bar(img_rgba, "mauri MANUKA HONEY", "定期縛りなし｜いつでも解約OK")

    # ── 価格バッジ
    font_badge = load_font(FONT_W8, 24)
    img_rgba = add_badge(img_rgba, "初回限定オファー", 54, 100,
                         bg_color=(160, 30, 30), text_color=(255, 255, 255),
                         font=font_badge, padding_x=18, padding_y=10, radius=6)

    # ── 通常価格（打ち消し線）
    font_cross = load_font(FONT_W3, 38)
    font_main = load_font(FONT_W9, 96)
    font_sub = load_font(FONT_W6, 36)

    shadow_draw.text((54, 600), "通常 7,200円", font=font_cross, fill=(0, 0, 0, 160))
    shadow_draw.text((54, 660), "初回 2,980円", font=font_main, fill=(0, 0, 0, 200))
    img_rgba = Image.alpha_composite(img_rgba, shadow_layer)
    draw = ImageDraw.Draw(img_rgba)

    # 通常価格（白・打ち消し線）
    draw.text((54, 600), "通常 7,200円", font=font_cross, fill=(200, 200, 200))
    # 打ち消し線
    bbox = draw.textbbox((54, 600), "通常 7,200円", font=font_cross)
    mid_y = (bbox[1] + bbox[3]) // 2
    draw.line([(54, mid_y), (bbox[2], mid_y)], fill=(200, 200, 200), width=3)

    # メイン価格（ゴールド）
    draw.text((54, 660), "初回", font=font_sub, fill=(220, 200, 160))
    draw.text((54 + 120, 645), "2,980円", font=font_main, fill=(212, 175, 55))

    # ── サブコピー
    font_note = load_font(FONT_W3, 28)
    draw.text((54, 810), "定期縛りなし・いつでも解約OK", font=font_note, fill=(200, 190, 170))
    draw.text((54, 848), "NZ産 木製スプーン同梱", font=font_note, fill=(200, 190, 170))

    # ── CTAボタン
    font_cta = load_font(FONT_W8, 36)
    img_rgba = add_cta_button(img_rgba, "今すぐ試してみる  →", 955,
                               bg_color=(200, 40, 40), text_color=(255, 255, 255),
                               font=font_cta, width=720, height=90, radius=45)

    img_final = finalize(img_rgba)
    img_final.save(os.path.join(OUTPUT_DIR, "banner_05_v3.png"), quality=95)
    print("    ✅ banner_05_v3.png")


# ── メイン実行 ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  Banner Park v3 — mauri MANUKA HONEY")
    print("  実写商品画像 × Pillow合成 (1080×1080)")
    print("=" * 50)

    build_banner_01()
    build_banner_02()
    build_banner_03()
    build_banner_04()
    build_banner_05()

    print()
    print("=" * 50)
    print("  完了! → banner-park/output/mauri/banners_v3/")
    print("=" * 50)
