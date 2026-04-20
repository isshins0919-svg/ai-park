#!/usr/bin/env python3
"""
⚓ ヨミテ VOYAGE 航路図ジェネレーター
history/*.json から 1商品1枚のシェア推移チャートを生成する。
デザインテーマ: 一進VOYAGE号（深海×ゴールド×各商品カラー）
"""
import json
import glob
import os
import sys
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # GUI不要
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from matplotlib.patheffects import withStroke
import matplotlib.patheffects as pe
import numpy as np

# フォント
plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False

# パス
ROOT = Path("/Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite")
HIST_DIR = ROOT / "history"
OUT_DIR = ROOT / "charts"
CONFIG_PATH = ROOT / "daily_news_config.json"

# VOYAGE カラーパレット
BG_DARK = "#0B1E3F"       # 深海の夜
BG_MID = "#12305A"         # 中間
GOLD = "#D4AF37"           # 真鍮
GOLD_LIGHT = "#F0D27A"
CREAM = "#F5E9C5"
INK = "#E8EFF7"            # 白文字
COMP1 = "#7A92B5"          # 競合1
COMP2 = "#556680"          # 競合2
GRID = "#24446A"

# 象限アイコン（matplotlibのフォント対応のため日本語＋記号に統一）
QUADRANT = {
    "own_up_market_up":   ("▲",  "追い風",       "#3AB0F5"),
    "own_up_market_down": ("★",  "独走",          "#F1A53A"),
    "own_down_market_up": ("！", "波に乗れてない","#E25860"),
    "own_down_market_down":("▼", "市場縮小",     "#9080B0"),
    "unknown":            ("◇",  "初回",          GOLD),
}

# 商品アイコン（matplotlib フォント対応の記号）
PRODUCT_ICON = {
    "on:myskin": "✦",
    "プルーストクリーム2": "✧",
    "伸長ぐんぐん習慣": "✩",
    "RKL": "✬",
}


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_history():
    out = {}
    for f in sorted(HIST_DIR.glob("*.json")):
        try:
            with open(f) as fp:
                d = json.load(fp)
            out[d["date"]] = d
        except Exception as e:
            print(f"skip {f}: {e}")
    return out


def compute_quadrant(shares):
    """直近2点を比較して象限判定。shares = [(date, own, market, share)] 日付昇順"""
    if len(shares) < 2:
        return "unknown"
    (_, own_p, market_p, _), (_, own_n, market_n, _) = shares[-2], shares[-1]
    market_up = market_n > market_p * 1.05
    market_down = market_n < market_p * 0.95
    own_up = own_n > own_p * 1.05
    own_down = own_n < own_p * 0.95

    if own_up and market_up: return "own_up_market_up"
    if own_up and market_down: return "own_up_market_down"
    if own_down and market_up: return "own_down_market_up"
    if own_down and market_down: return "own_down_market_down"
    if own_up: return "own_up_market_up"
    if own_down: return "own_down_market_down"
    return "own_up_market_up"


def extract_top_competitors(history, product_key, top_n=2):
    """過去全日のcompetitors_top2から最も頻出する競合を抽出"""
    counter = {}
    for date, h in history.items():
        comps = h.get("products", {}).get(product_key, {}).get("competitors_top2", [])
        for c in comps:
            name = c.get("name","?")
            counter[name] = counter.get(name, 0) + 1
    ranked = sorted(counter.items(), key=lambda x:(-x[1], x[0]))
    return [n for n,_ in ranked[:top_n]]


def shorten(name, n=20):
    if len(name) <= n: return name
    return name[:n-1] + "…"


def draw_chart(product_cfg, history, out_path):
    """1商品1枚のVOYAGE航路図"""
    pkey = product_cfg["name"]
    pkey_norm = {
        "on:myskin": "onmyskin",
        "プルーストクリーム2": "proust",
        "伸長ぐんぐん習慣": "gungun",
        "RKL": "rkl",
    }[pkey]
    icon = PRODUCT_ICON[pkey]
    color = product_cfg["color"]
    display_name = product_cfg["display_name"]
    market_label = product_cfg["market"]["genre_label"]

    # 時系列データ抽出
    dates_sorted = sorted(history.keys())
    series_own = []   # [(date, share_pct)]
    series_own_raw = []  # own/market
    comp_series = {}  # name -> [(date, share_pct)]

    top_comps = extract_top_competitors(history, pkey_norm, top_n=2)

    for d in dates_sorted:
        h = history[d]["products"].get(pkey_norm, {})
        own = h.get("own", 0)
        market = h.get("market", 0)
        share = h.get("share_pct", 0)
        series_own.append((d, share))
        series_own_raw.append((d, own, market, share))

        if market > 0:
            for c in h.get("competitors_top2", []):
                cname = c.get("name","")
                if cname in top_comps:
                    csh = (c.get("cost_diff",0) / market) * 100
                    comp_series.setdefault(cname, []).append((d, csh))

    # 象限判定
    quadrant_key = compute_quadrant(series_own_raw)
    q_icon, q_label, q_color = QUADRANT[quadrant_key]

    # 今日の値（直近）
    today_share = series_own[-1][1] if series_own else 0
    today_own = series_own_raw[-1][1] if series_own_raw else 0
    today_market = series_own_raw[-1][2] if series_own_raw else 0
    prev_share = series_own[-2][1] if len(series_own) >= 2 else None

    # === Figure (Slack最適 1200x1500) ===
    fig = plt.figure(figsize=(13, 15), dpi=100)
    fig.patch.set_facecolor(BG_DARK)

    # 背景星空ドット
    np.random.seed(hash(pkey) % 2**32)
    ax_bg = fig.add_axes([0,0,1,1], zorder=0)
    ax_bg.set_facecolor(BG_DARK)
    ax_bg.set_xlim(0,1); ax_bg.set_ylim(0,1)
    ax_bg.axis("off")
    stars_x = np.random.rand(80)
    stars_y = np.random.rand(80)
    stars_s = np.random.rand(80) * 8 + 1
    ax_bg.scatter(stars_x, stars_y, s=stars_s, c=GOLD_LIGHT, alpha=0.25, zorder=0)

    # 上部グラデ帯（ヘッダー）
    header_h = 0.18
    ax_head = fig.add_axes([0,1-header_h,1,header_h], zorder=1)
    ax_head.set_facecolor(BG_MID)
    ax_head.set_xlim(0,1); ax_head.set_ylim(0,1)
    ax_head.axis("off")

    # 装飾: 錨マーク（左、大きく）
    import matplotlib.patches as mp
    def draw_anchor(ax, cx, cy, size=0.16, color=GOLD, lw=3.2):
        # リング（上の輪）
        ring = Circle((cx, cy + size*0.85), size*0.18, fill=False, edgecolor=color, lw=lw, transform=ax.transAxes)
        ax.add_patch(ring)
        # 縦棒
        ax.plot([cx, cx], [cy + size*0.67, cy - size*0.85], color=color, lw=lw+0.5, transform=ax.transAxes)
        # 水平バー
        ax.plot([cx - size*0.55, cx + size*0.55], [cy + size*0.45, cy + size*0.45], color=color, lw=lw, transform=ax.transAxes)
        # 下の三日月フック（弧）
        arc = mp.Arc((cx, cy - size*0.4), size*1.55, size*1.0, angle=0, theta1=200, theta2=340,
                     edgecolor=color, lw=lw, transform=ax.transAxes)
        ax.add_patch(arc)
        # フック先端
        ax.plot([cx - size*0.77, cx - size*0.63], [cy - size*0.3, cy - size*0.05], color=color, lw=lw, transform=ax.transAxes)
        ax.plot([cx + size*0.77, cx + size*0.63], [cy - size*0.3, cy - size*0.05], color=color, lw=lw, transform=ax.transAxes)

    draw_anchor(ax_head, 0.065, 0.5, size=0.35, color=GOLD, lw=3.0)

    # コンパス風装飾（右、大きく）
    compass_x, compass_y, compass_r = 0.92, 0.5, 0.38
    circle = Circle((compass_x, compass_y), compass_r, fill=False, edgecolor=GOLD, lw=2.5, alpha=0.55, transform=ax_head.transAxes)
    ax_head.add_patch(circle)
    circle2 = Circle((compass_x, compass_y), compass_r*0.6, fill=False, edgecolor=GOLD, lw=1.2, alpha=0.35, transform=ax_head.transAxes)
    ax_head.add_patch(circle2)
    for angle_deg in range(0, 360, 45):
        a = np.deg2rad(angle_deg - 90)
        x1, y1 = compass_x + compass_r*0.6*np.cos(a), compass_y + compass_r*0.6*np.sin(a)
        x2, y2 = compass_x + compass_r*np.cos(a), compass_y + compass_r*np.sin(a)
        is_cardinal = angle_deg % 90 == 0
        lw_c = 2.2 if is_cardinal else 1
        ax_head.plot([x1,x2],[y1,y2], color=GOLD, alpha=0.7 if is_cardinal else 0.4, lw=lw_c, transform=ax_head.transAxes)
    # N針
    ax_head.plot([compass_x, compass_x], [compass_y, compass_y + compass_r*0.5], color="#E25860", lw=3, transform=ax_head.transAxes, solid_capstyle="round")
    ax_head.plot([compass_x, compass_x], [compass_y, compass_y - compass_r*0.5], color=CREAM, lw=3, transform=ax_head.transAxes, solid_capstyle="round")
    ax_head.text(compass_x, compass_y + compass_r*0.72, "N", fontsize=11, color=GOLD_LIGHT, ha="center", va="center", weight="bold", family="serif", transform=ax_head.transAxes)

    # タイトル
    ax_head.text(0.13, 0.74, "V O Y A G E   R E P O R T", fontsize=13, color=GOLD_LIGHT, weight="bold", family="serif", transform=ax_head.transAxes)
    ax_head.text(0.13, 0.44, display_name, fontsize=28, color=INK, weight="bold", transform=ax_head.transAxes)
    ax_head.text(0.13, 0.18, f"市場  ／  {market_label}", fontsize=12, color=CREAM, transform=ax_head.transAxes, style="italic")

    # 右：今日日付
    today_str = datetime.strptime(dates_sorted[-1], "%Y-%m-%d").strftime("%Y.%m.%d")
    day_str = datetime.strptime(dates_sorted[-1], "%Y-%m-%d").strftime("%A").upper()
    ax_head.text(0.8, 0.82, today_str, fontsize=12, color=GOLD_LIGHT, ha="right", va="center", family="serif", transform=ax_head.transAxes)
    ax_head.text(0.8, 0.72, day_str, fontsize=10, color=CREAM, ha="right", va="center", family="serif", alpha=0.7, transform=ax_head.transAxes)

    # 下装飾ライン（金）
    ax_head.plot([0.02, 0.98], [0.02, 0.02], color=GOLD, lw=1.2, alpha=0.7, transform=ax_head.transAxes)

    # メインチャート領域
    chart_top = 1 - header_h - 0.03
    chart_bottom = 0.27
    ax = fig.add_axes([0.09, chart_bottom, 0.85, chart_top - chart_bottom], zorder=2)
    ax.set_facecolor(BG_DARK)

    # X軸
    dates_dt = [datetime.strptime(d, "%Y-%m-%d") for d in dates_sorted]
    x_pos = list(range(len(dates_dt)))

    # 自社折れ線（太、グロー効果）
    own_y = [v for _,v in series_own]
    # グロー3層
    ax.plot(x_pos, own_y, color=color, lw=14, alpha=0.12, zorder=3, solid_capstyle="round")
    ax.plot(x_pos, own_y, color=color, lw=9, alpha=0.22, zorder=4, solid_capstyle="round")
    ax.plot(x_pos, own_y, color=color, lw=4.5, marker="o", markersize=15,
            markerfacecolor=color, markeredgecolor="white", markeredgewidth=3,
            label=f"自社 ヨミテ", zorder=6, solid_capstyle="round")

    # 自社: 塗り潰し（航路っぽい効果）
    ax.fill_between(x_pos, 0, own_y, color=color, alpha=0.13, zorder=2)

    # 競合線
    comp_colors = [COMP1, COMP2]
    for i, cname in enumerate(top_comps):
        pts = comp_series.get(cname, [])
        if not pts: continue
        date_idx = {d:i_ for i_,d in enumerate(dates_sorted)}
        px = [date_idx[d] for d,_ in pts if d in date_idx]
        py = [v for d,v in pts if d in date_idx]
        ax.plot(px, py, color=comp_colors[i], lw=2, marker="s", markersize=8,
                markerfacecolor=comp_colors[i], markeredgecolor=CREAM, markeredgewidth=1,
                linestyle="--", alpha=0.85, label=f"競合: {shorten(cname, 22)}", zorder=5)

    # 軸
    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.strftime("%m/%d\n(%a)") for d in dates_dt], fontsize=10, color=INK)
    ax.tick_params(axis="y", colors=INK, labelsize=10)
    ax.set_ylabel("市場占有率 (%)", fontsize=12, color=GOLD_LIGHT, fontweight="bold", labelpad=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))

    # グリッド
    ax.grid(True, axis="y", color=GRID, linestyle="--", alpha=0.5, zorder=1)
    ax.set_axisbelow(True)

    # 枠
    for spine in ax.spines.values():
        spine.set_color(GOLD)
        spine.set_linewidth(1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # タイトル（市場ラベル）
    ax.set_title(f"市場: {market_label}", fontsize=12, color=CREAM, pad=12, weight="bold", loc="left")

    # 凡例
    leg = ax.legend(loc="upper left", fontsize=10.5, frameon=True, facecolor=BG_MID, edgecolor=GOLD, labelcolor=INK)
    leg.get_frame().set_alpha(0.8)

    # 最新点にシェア%バッジ
    last_y = own_y[-1]
    ax.annotate(f"{last_y:.2f}%",
                xy=(x_pos[-1], last_y),
                xytext=(12, 12), textcoords="offset points",
                fontsize=16, color="white", weight="bold",
                bbox=dict(boxstyle="round,pad=0.45", facecolor=color, edgecolor=GOLD, lw=1.5),
                zorder=10)

    # === 下部パネル（ステータスバー） ===
    status_h = 0.24
    ax_status = fig.add_axes([0, 0, 1, status_h], zorder=2)
    ax_status.set_facecolor(BG_MID)
    ax_status.set_xlim(0,1); ax_status.set_ylim(0,1)
    ax_status.axis("off")

    # 区切り金ライン上部
    ax_status.plot([0.02, 0.98], [0.96, 0.96], color=GOLD, lw=1, alpha=0.7, transform=ax_status.transAxes)

    # 左: 象限バッジ
    ax_status.add_patch(FancyBboxPatch((0.035, 0.46), 0.27, 0.44, boxstyle="round,pad=0.02",
                                       facecolor=q_color, edgecolor=GOLD, lw=1.5, alpha=0.92,
                                       transform=ax_status.transAxes))
    ax_status.text(0.17, 0.76, q_icon, fontsize=34, ha="center", va="center", color="white",
                   weight="bold", transform=ax_status.transAxes)
    ax_status.text(0.17, 0.54, q_label, fontsize=14, color="white", ha="center", va="center",
                   weight="bold", transform=ax_status.transAxes)

    # 中央: 今日のシェア（特大）
    delta_txt = ""
    if prev_share is not None:
        delta = last_y - prev_share
        if delta > 0.01:
            delta_txt = f"▲ +{delta:.2f}pt"
            delta_color = "#3AF58B"
        elif delta < -0.01:
            delta_txt = f"▼ {delta:.2f}pt"
            delta_color = "#F56A6A"
        else:
            delta_txt = "→ 変化なし"
            delta_color = GOLD_LIGHT
    else:
        delta_color = GOLD_LIGHT

    ax_status.text(0.5, 0.85, "TODAY SHARE", fontsize=10, color=GOLD_LIGHT, ha="center", weight="bold",
                   family="serif", transform=ax_status.transAxes)
    ax_status.text(0.5, 0.55, f"{last_y:.2f}%", fontsize=46, color="white", ha="center",
                   weight="bold", transform=ax_status.transAxes)
    if delta_txt:
        ax_status.text(0.5, 0.3, delta_txt, fontsize=13, color=delta_color, ha="center",
                       weight="bold", transform=ax_status.transAxes)

    # 右: 自社/市場金額
    def fmt_yen(v):
        if v >= 10**6: return f"¥{v/10**6:.1f}M"
        if v >= 10**3: return f"¥{v/10**3:.0f}K"
        return f"¥{v:.0f}"

    ax_status.text(0.83, 0.85, "VS MARKET", fontsize=10, color=GOLD_LIGHT, ha="center", weight="bold",
                   family="serif", transform=ax_status.transAxes)
    ax_status.text(0.83, 0.62, f"自社 {fmt_yen(today_own)}", fontsize=13, color=color, ha="center",
                   weight="bold", transform=ax_status.transAxes)
    ax_status.text(0.83, 0.42, f"市場 {fmt_yen(today_market)}", fontsize=13, color=INK, ha="center",
                   transform=ax_status.transAxes)

    # 下段装飾バー + Brand
    ax_status.plot([0.02, 0.98], [0.1, 0.1], color=GOLD, lw=0.5, alpha=0.5, transform=ax_status.transAxes)
    ax_status.text(0.5, 0.04, "一進 VOYAGE 号   YOMITE DAILY MARKET POSITION   ~ Navigate the tides ~",
                   fontsize=9, color=GOLD_LIGHT, ha="center", alpha=0.75, family="serif",
                   style="italic", transform=ax_status.transAxes)

    # 保存
    fig.savefig(out_path, facecolor=BG_DARK, dpi=110, bbox_inches=None)
    plt.close(fig)
    print(f"✅ {out_path}")


def main():
    cfg = load_config()
    history = load_history()
    if not history:
        print("❌ history empty")
        sys.exit(1)

    today = sorted(history.keys())[-1]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for product in cfg["products"]:
        pkey = product["name"]
        slug = {"on:myskin":"onmyskin","プルーストクリーム2":"proust","伸長ぐんぐん習慣":"gungun","RKL":"rkl"}[pkey]
        out = OUT_DIR / f"{today}_voyage_{slug}.png"
        try:
            draw_chart(product, history, out)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ {slug}: {e}")

if __name__ == "__main__":
    main()
