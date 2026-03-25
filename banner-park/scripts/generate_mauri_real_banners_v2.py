#!/usr/bin/env python3
"""
Banner Park v7.0 — mauri MANUKA HONEY
実写素材ベース × Pillow合成 × 5仮説バナー
AI生成ではなく公式LP素材を使った本番品質
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import textwrap, math, os

# ─── パス設定 ────────────────────────────────────────────────
LP_DIR = Path("/Users/ca01224/Desktop/mauriのデータ/LPフォルダ/『mauri MANUKA HONEY』公式ページ｜ヨミテ_files/")
OUT_DIR = Path("/Users/ca01224/Desktop/AI一進-Claude-Code/banner-park/output/mauri/banners_v2")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── フォント設定 ────────────────────────────────────────────
FONT_W9 = "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc"
FONT_W8 = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_W7 = "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc"

def font(path, size):
    return ImageFont.truetype(path, size)

# ─── バナーサイズ ─────────────────────────────────────────────
W = H = 1080

# ─── ユーティリティ ──────────────────────────────────────────

def smart_crop(img: Image.Image, target_w: int, target_h: int, anchor: str = "top",
               blur_radius: float = 0) -> Image.Image:
    """アスペクト比を保ちながらクロップ。元画像のテキストを消すためblurも可"""
    orig_w, orig_h = img.size
    ratio = max(target_w / orig_w, target_h / orig_h)
    new_w = int(orig_w * ratio)
    new_h = int(orig_h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    if anchor == "top":
        top = 0
    elif anchor == "center":
        top = (new_h - target_h) // 2
    else:  # bottom
        top = new_h - target_h

    left = (new_w - target_w) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    # ブラーで元テキストをつぶす
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return img


def rgba(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        return img.convert("RGBA")
    return img


def draw_multiline_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy,
    font_obj,
    fill,
    shadow_color=(0, 0, 0, 180),
    shadow_offset=4,
    align="left",
    line_spacing=1.2,
):
    """影付きテキスト描画"""
    x, y = xy
    lines = text.split("\n")
    line_h = int(font_obj.size * line_spacing)

    for line in lines:
        # 影
        draw.text((x + shadow_offset, y + shadow_offset), line, font=font_obj, fill=shadow_color)
        # 本体
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += line_h


def draw_centered_multiline(
    draw: ImageDraw.ImageDraw,
    img_w: int,
    text: str,
    y: int,
    font_obj,
    fill,
    shadow=True,
    shadow_color=(0, 0, 0, 200),
    line_spacing=1.25,
):
    """中央寄せ影付きテキスト"""
    lines = text.split("\n")
    line_h = int(font_obj.size * line_spacing)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_obj)
        tw = bbox[2] - bbox[0]
        x = (img_w - tw) // 2
        cur_y = y + i * line_h
        if shadow:
            draw.text((x + 3, cur_y + 3), line, font=font_obj, fill=shadow_color)
        draw.text((x, cur_y), line, font=font_obj, fill=fill)


def gradient_overlay(img: Image.Image, direction: str, opacity_start: int, opacity_end: int, color=(0, 0, 0)) -> Image.Image:
    """グラデーションオーバーレイ"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size

    if direction == "bottom":
        for y in range(h):
            ratio = y / h
            alpha = int(opacity_start + (opacity_end - opacity_start) * ratio)
            draw.line([(0, y), (w, y)], fill=(*color, alpha))
    elif direction == "top":
        for y in range(h):
            ratio = 1 - y / h
            alpha = int(opacity_start + (opacity_end - opacity_start) * ratio)
            draw.line([(0, y), (w, y)], fill=(*color, alpha))
    elif direction == "full":
        overlay = Image.new("RGBA", img.size, (*color, opacity_start))

    img_rgba = rgba(img)
    return Image.alpha_composite(img_rgba, overlay)


def add_pill_button(img: Image.Image, text: str, x: int, y: int, w: int, h: int,
                    bg_color, text_color, font_obj) -> Image.Image:
    """丸角ボタン描画"""
    img = rgba(img)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r = h // 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=(*bg_color, 240))
    img = Image.alpha_composite(img, overlay)
    draw2 = ImageDraw.Draw(img)
    bbox = draw2.textbbox((0, 0), text, font=font_obj)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x + (w - tw) // 2
    ty = y + (h - th) // 2 - 2
    draw2.text((tx + 2, ty + 2), text, font=font_obj, fill=(0, 0, 0, 120))
    draw2.text((tx, ty), text, font=font_obj, fill=text_color)
    return img


def add_badge(img: Image.Image, text: str, x: int, y: int,
              bg_color, text_color, font_obj, padding_x=20, padding_h=12) -> Image.Image:
    """バッジ（小ラベル）描画"""
    img = rgba(img)
    draw_tmp = ImageDraw.Draw(img)
    bbox = draw_tmp.textbbox((0, 0), text, font=font_obj)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bw = tw + padding_x * 2
    bh = th + padding_h * 2
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    draw_ov.rounded_rectangle([x, y, x + bw, y + bh], radius=bh // 2, fill=(*bg_color, 230))
    img = Image.alpha_composite(img, overlay)
    draw2 = ImageDraw.Draw(img)
    draw2.text((x + padding_x, y + padding_h), text, font=font_obj, fill=text_color)
    return img


# ─── Banner 01: 常識否定型 ────────────────────────────────────
def banner_01():
    """「美味しさで選んでた。」— MNK_LP-1の上部（amber product shot）"""
    print("  Banner 01: 常識否定型 生成中...")
    base = Image.open(LP_DIR / "MNK_LP-1.webp")
    # 上部の商品ショット。blur=18で元テキストを完全に背景テクスチャ化
    img = smart_crop(base, W, H, anchor="top", blur_radius=18)
    # 強めのオーバーレイで元テキストを完全に抑制
    img = gradient_overlay(img, "full", 120, 120, color=(30, 15, 0))
    img = gradient_overlay(img, "bottom", 0, 180, color=(20, 10, 0))
    img = gradient_overlay(img, "top", 120, 0, color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ──── テキスト ────
    # サブキャッチ（上部）
    sub_font = font(FONT_W7, 38)
    draw_centered_multiline(draw, W, "そのマヌカハニー、本物ですか？", 60, sub_font,
                            fill=(255, 220, 120), shadow_color=(0,0,0,200))

    # メインヘッドライン
    main_font = font(FONT_W9, 88)
    draw_centered_multiline(draw, W, "美味しさで\n選んでた。", 700, main_font,
                            fill=(255, 255, 255), shadow_color=(0, 0, 0, 220), line_spacing=1.15)

    # サブコピー
    sub2_font = font(FONT_W8, 40)
    draw_centered_multiline(draw, W, "本当に守られていますか？", 920, sub2_font,
                            fill=(255, 240, 180), shadow_color=(0,0,0,200))

    # CTAボタン
    btn_font = font(FONT_W8, 36)
    img = add_pill_button(img, "本物の選び方を見る  →", 140, 1000, 800, 66,
                          bg_color=(212, 160, 23), text_color=(255, 255, 255), font_obj=btn_font)

    img = img.convert("RGB")
    out = OUT_DIR / "banner_01_real.png"
    img.save(out, quality=95)
    print(f"     ✅ {out.name}")
    return str(out)


# ─── Banner 02: 恐怖訴求型 ────────────────────────────────────
def banner_02():
    """「そのMGO263+実測値は？」— MNK_LP-9（選ばれる理由・証明書）"""
    print("  Banner 02: 恐怖訴求型 生成中...")
    base = Image.open(LP_DIR / "MNK_LP-9.webp")
    img = smart_crop(base, W, H, anchor="top", blur_radius=15)
    img = gradient_overlay(img, "full", 150, 150, color=(10, 20, 40))
    img = gradient_overlay(img, "bottom", 0, 180, color=(10, 20, 40))
    draw = ImageDraw.Draw(img)

    # 上部ラベル
    label_font = font(FONT_W8, 34)
    draw_centered_multiline(draw, W, "市販のマヌカハニーの衝撃の真実", 55, label_font,
                            fill=(255, 220, 100), shadow_color=(0,0,0,200))

    # メインヘッドライン
    main_font = font(FONT_W9, 82)
    draw_centered_multiline(draw, W, "そのMGO263+\n実測値は？", 680, main_font,
                            fill=(255, 255, 255), shadow_color=(0,0,0,230), line_spacing=1.2)

    # 証拠テキスト
    proof_font = font(FONT_W8, 38)
    draw_centered_multiline(draw, W, "mauri 実測値MGO345 証明書つき", 900, proof_font,
                            fill=(120, 255, 160), shadow_color=(0,0,0,200))

    # CTAボタン
    btn_font = font(FONT_W8, 34)
    img = add_pill_button(img, "証明書を確認する  →", 165, 1002, 750, 62,
                          bg_color=(45, 80, 22), text_color=(255, 255, 255), font_obj=btn_font)

    img = img.convert("RGB")
    out = OUT_DIR / "banner_02_real.png"
    img.save(out, quality=95)
    print(f"     ✅ {out.name}")
    return str(out)


# ─── Banner 03: 共感型 ────────────────────────────────────────
def banner_03():
    """「毎日摂っているのに...」— MNK_LP_offer-1（ダーク・美しいプロダクト）"""
    print("  Banner 03: 共感型 生成中...")
    base = Image.open(LP_DIR / "MNK_LP_offer-1.webp")
    # centerクロップ: jarがちょうど中央に来る部分
    img = smart_crop(base, W, H, anchor="center", blur_radius=12)
    # 上下にグラデ（元テキストを消す）
    img = gradient_overlay(img, "full", 90, 90, color=(0, 0, 0))
    img = gradient_overlay(img, "top", 200, 10, color=(0, 0, 0))
    img = gradient_overlay(img, "bottom", 0, 220, color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 上部
    top_font = font(FONT_W7, 36)
    draw_centered_multiline(draw, W, "こんな思い、ありませんか？", 52, top_font,
                            fill=(220, 220, 220), shadow_color=(0,0,0,180))

    # メインヘッドライン（少し小さめ / 長文）
    main_font = font(FONT_W9, 68)
    draw_centered_multiline(draw, W, "毎日摂っているのに\n守られてる感じが\nしない", 660, main_font,
                            fill=(255, 255, 255), shadow_color=(0,0,0,230), line_spacing=1.2)

    # サブコピー
    sub_font = font(FONT_W8, 38)
    draw_centered_multiline(draw, W, "選び方が、違うのかもしれない。", 920, sub_font,
                            fill=(255, 220, 120), shadow_color=(0,0,0,200))

    # CTAボタン
    btn_font = font(FONT_W8, 34)
    img = add_pill_button(img, "本物の選び方を見る  →", 165, 1006, 750, 62,
                          bg_color=(212, 160, 23), text_color=(20, 20, 20), font_obj=btn_font)

    img = img.convert("RGB")
    out = OUT_DIR / "banner_03_real.png"
    img.save(out, quality=95)
    print(f"     ✅ {out.name}")
    return str(out)


# ─── Banner 04: NZ直送・本物ストーリー型 ─────────────────────
def banner_04():
    """「NZ養蜂家からの直接取引」— 260309_MNK_LP-2（養蜂家・ハニカム・NZ山岳）"""
    print("  Banner 04: NZ直送ストーリー型 生成中...")
    base = Image.open(LP_DIR / "260309_MNK_LP-2.webp")
    # 上部（養蜂家 + NZ山岳）を使用。ブラーで元テキスト消去
    img = smart_crop(base, W, H, anchor="top", blur_radius=14)
    img = gradient_overlay(img, "full", 130, 130, color=(5, 20, 5))
    img = gradient_overlay(img, "top", 160, 20, color=(5, 20, 5))
    img = gradient_overlay(img, "bottom", 0, 200, color=(5, 20, 5))
    draw = ImageDraw.Draw(img)

    # バッジ
    badge_font = font(FONT_W8, 30)
    img = add_badge(img, "ニュージーランド直送", 100, 55,
                    bg_color=(45, 80, 22), text_color=(255, 255, 255), font_obj=badge_font)

    # メイン
    main_font = font(FONT_W9, 76)
    draw = ImageDraw.Draw(img)
    draw_centered_multiline(draw, W, "奇跡の採蜜。\nNZ養蜂家からの\n直接取引", 680, main_font,
                            fill=(255, 255, 255), shadow_color=(0,0,0,230), line_spacing=1.18)

    # サブ
    sub_font = font(FONT_W8, 36)
    draw_centered_multiline(draw, W, "MGO実測345 × 農薬不検出 × 証明書つき", 930, sub_font,
                            fill=(180, 255, 140), shadow_color=(0,0,0,200))

    # CTAボタン
    btn_font = font(FONT_W8, 34)
    img = add_pill_button(img, "mauriを詳しく見る  →", 165, 1006, 750, 62,
                          bg_color=(212, 160, 23), text_color=(20, 20, 20), font_obj=btn_font)

    img = img.convert("RGB")
    out = OUT_DIR / "banner_04_real.png"
    img.save(out, quality=95)
    print(f"     ✅ {out.name}")
    return str(out)


# ─── Banner 05: 価格オファー型 ────────────────────────────────
def banner_05():
    """「初回58%OFF」— MNK_LP_offer-1（最美product shot）+ 価格強調"""
    print("  Banner 05: 価格オファー型 生成中...")
    base = Image.open(LP_DIR / "MNK_LP_offer-1.webp")
    # topクロップ: jar + 木製スプーン + フィグの美しいショット
    img = smart_crop(base, W, H, anchor="top", blur_radius=16)
    # 全体に暗めオーバーレイ（元テキスト完全消去）
    img = gradient_overlay(img, "full", 130, 130, color=(10, 5, 0))
    img = gradient_overlay(img, "bottom", 0, 200, color=(10, 5, 0))
    img = gradient_overlay(img, "top", 150, 20, color=(10, 5, 0))
    draw = ImageDraw.Draw(img)

    # 上部バッジ: "公式サイト限定"
    badge_font = font(FONT_W8, 32)
    img = add_badge(img, "🍯 公式サイト限定 特別価格", 110, 52,
                    bg_color=(180, 30, 30), text_color=(255, 255, 255), font_obj=badge_font)
    draw = ImageDraw.Draw(img)

    # 58%OFF 大きく
    off_font = font(FONT_W9, 110)
    draw_centered_multiline(draw, W, "初回 58%OFF", 640, off_font,
                            fill=(255, 220, 50), shadow_color=(0,0,0,230), line_spacing=1.1)

    # 価格
    price_font = font(FONT_W8, 52)
    draw_centered_multiline(draw, W, "通常7,200円 → 2,980円", 800, price_font,
                            fill=(255, 255, 255), shadow_color=(0,0,0,220))

    # 条件
    cond_font = font(FONT_W7, 34)
    draw_centered_multiline(draw, W, "NZ直送 ／ 定期縛りなし ／ いつでも解約OK", 890, cond_font,
                            fill=(200, 240, 200), shadow_color=(0,0,0,180))

    # CTAボタン
    btn_font = font(FONT_W8, 38)
    img = add_pill_button(img, "今すぐ試す  →", 210, 1005, 660, 68,
                          bg_color=(212, 160, 23), text_color=(20, 20, 20), font_obj=btn_font)

    img = img.convert("RGB")
    out = OUT_DIR / "banner_05_real.png"
    img.save(out, quality=95)
    print(f"     ✅ {out.name}")
    return str(out)


# ─── メイン ─────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  実写バナー生成 — mauri MANUKA HONEY v2.0")
    print("  Pillow × LP実写素材 × ヒラギノ角ゴシック")
    print("=" * 60)

    results = []
    for fn in [banner_01, banner_02, banner_03, banner_04, banner_05]:
        try:
            out = fn()
            results.append(("✅", out))
        except Exception as e:
            print(f"     ❌ エラー: {e}")
            results.append(("❌", str(e)))

    print("\n" + "=" * 60)
    print(f"  完了: {sum(1 for r in results if r[0]=='✅')}/5 枚")
    print(f"  出力先: {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
