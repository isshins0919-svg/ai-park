#!/usr/bin/env python3
"""
記事LP バナー解析スクリプト
Playwright でJSレンダリング → スクリーンショット + HTML抽出 + 画像URL収集
"""
import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://foot.cosmedia.online/ab/ejgSPLGDwTRRPkjlZXvUg"
OUT_DIR = Path("/Users/ca01224/Desktop/AI一進-Claude-Code/.claude/scripts/lp_analysis")
OUT_DIR.mkdir(exist_ok=True)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 750, "height": 1200})

        print(f"Loading {URL} ...")
        page.goto(URL, wait_until="networkidle", timeout=30000)
        time.sleep(3)  # lazy-load待機

        # ── フルページスクリーンショット ──────────────────────────
        full_path = OUT_DIR / "full_page.png"
        page.screenshot(path=str(full_path), full_page=True)
        print(f"[OK] フルページ screenshot: {full_path}")

        # ── ページ高さ取得 ────────────────────────────────────────
        total_height = page.evaluate("() => document.body.scrollHeight")
        print(f"[INFO] ページ高さ: {total_height}px")

        # ── セクション別スクリーンショット（3分割）─────────────────
        viewport_h = 1200
        for i, scroll_y in enumerate([0, total_height // 3, 2 * total_height // 3]):
            page.evaluate(f"window.scrollTo(0, {scroll_y})")
            time.sleep(1)
            section_path = OUT_DIR / f"section_{i+1}.png"
            page.screenshot(path=str(section_path))
            print(f"[OK] section_{i+1}: scroll_y={scroll_y} → {section_path}")

        # ── 画像URL収集 ───────────────────────────────────────────
        images = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img')).map(img => ({
                src: img.src,
                alt: img.alt,
                width: img.naturalWidth,
                height: img.naturalHeight,
                rect: img.getBoundingClientRect().toJSON(),
            }));
        }""")

        # ── テキストブロック収集（h1〜h3, p, .catch 等）──────────
        texts = page.evaluate("""() => {
            const sel = 'h1, h2, h3, h4, p, .catch, .lead, .caption, [class*="copy"], [class*="text"], [class*="title"]';
            return Array.from(document.querySelectorAll(sel)).map(el => ({
                tag: el.tagName,
                className: el.className,
                text: el.innerText.trim().slice(0, 200),
                rect: el.getBoundingClientRect().toJSON(),
            })).filter(e => e.text.length > 3);
        }""")

        # ── section / div 構造 ───────────────────────────────────
        structure = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('section, article, .section, [class*="block"], [class*="banner"], [class*="cta"]')).map(el => ({
                tag: el.tagName,
                className: el.className,
                id: el.id,
                innerText: el.innerText.trim().slice(0, 100),
            }));
        }""")

        browser.close()

    # 結果保存
    result = {
        "url": URL,
        "total_height": total_height,
        "images": images,
        "texts": texts[:80],  # 上位80件
        "structure": structure[:40],
    }
    out_json = OUT_DIR / "result.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 解析結果: {out_json}")
    print(f"[OK] 画像数: {len(images)}")
    print(f"[OK] テキスト数: {len(texts)}")

    # 主要テキスト表示
    print("\n=== 主要テキスト（上位30件）===")
    for t in texts[:30]:
        print(f"  [{t['tag']}] {t['text'][:80]}")

    # 画像URL表示（幅200px以上のみ）
    print("\n=== バナー候補画像（幅200px以上）===")
    for img in images:
        if img.get("width", 0) >= 200:
            print(f"  {img['width']}x{img['height']} | {img['src'][:100]}")

    print("\n=== スクリーンショット保存先 ===")
    print(f"  フル: {full_path}")
    print(f"  冒頭: {OUT_DIR}/section_1.png")
    print(f"  中盤: {OUT_DIR}/section_2.png")
    print(f"  末尾: {OUT_DIR}/section_3.png")


if __name__ == "__main__":
    run()