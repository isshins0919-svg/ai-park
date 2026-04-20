#!/usr/bin/env python3
"""
ヨミテ デイリー 市場占有率チャート（報道系ミニマル × 媒体別ブレイクダウン）
history/*.json から 1商品1枚のシェア推移+媒体別ブレイクダウンPNGを生成。
白背景・太字見出し・数字主張強め。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 重要: グラフのX軸ラベルは「観測日(前日=to_date_api)」基準。
   発行日(history JSONの date フィールド)ではない！

   各データ点:
   - X軸ラベル = その点の「最新観測日」（APIのto_date）
   - 値 = その日を末尾とする過去2日間の差分（interval=2）

   例: history/2026-04-20.json は to_date_api=2026-04-19 なので
       グラフ上は「4/19」ラベル（4/18-4/19の2日間差分）で描画される。

   ⚠️ このルールを破ると「今日4/20に何が起きたか？」と誤読される。
   どんな理由があっても、X軸ラベルに発行日を出すのは絶対NG！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path("/Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite")
HIST_DIR = ROOT / "history"
OUT_DIR = ROOT / "charts"
CONFIG_PATH = ROOT / "daily_news_config.json"

# カラー
BG = "#FFFFFF"
INK = "#1B1F26"
INK_SUB = "#6E7682"
LINE_LIGHT = "#E5E8EC"
GRID = "#F0F2F5"
COMP1 = "#B5BCC6"
COMP2 = "#D4D8DE"
VIDEO_COLOR = "#6C63FF"    # 動画 = パープル
BANNER_COLOR = "#FF8A3D"   # バナー = オレンジ
CAROUSEL_COLOR = "#3AC29A"  # カルーセル = グリーン

# 商品名 → slug
PKEY_TO_SLUG = {
    "on:myskin": "onmyskin",
    "プルーストクリーム2": "proust",
    "伸長ぐんぐん習慣": "gungun",
    "RKL": "rkl",
    "アポバスターF": "apobusterf",
}

# 象限
QUADRANT = {
    "own_up_market_up":   ("🌊", "追い風",         "#3AA6E8"),
    "own_up_market_down": ("🚀", "独走",            "#F1A53A"),
    "own_down_market_up": ("⚠",  "波に乗れてない",  "#E25860"),
    "own_down_market_down":("📉","市場縮小",        "#9080B0"),
    "unknown":            ("◇",  "初回",            INK_SUB),
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
    counter = {}
    for date, h in history.items():
        comps = h.get("products", {}).get(product_key, {}).get("competitors_top2", [])
        for c in comps:
            name = c.get("name","?")
            counter[name] = counter.get(name, 0) + 1
    ranked = sorted(counter.items(), key=lambda x:(-x[1], x[0]))
    return [n for n,_ in ranked[:top_n]]


def shorten(name, n=26):
    if len(name) <= n: return name
    return name[:n-1] + "…"


def fmt_yen(v):
    if v >= 10**6: return f"¥{v/10**6:.2f}M"
    if v >= 10**3: return f"¥{v/10**3:.0f}K"
    return f"¥{int(v)}"


def make_headline(quadrant_key, delta_share, rank_change=None):
    """象限と変動から、報道系の見出しを作る"""
    q_emoji, q_label, _ = QUADRANT[quadrant_key]
    if quadrant_key == "own_up_market_up":
        return f"{q_emoji} 追い風 / 市場とともに伸長"
    if quadrant_key == "own_up_market_down":
        return f"{q_emoji} 独走 / 市場縮小下で逆行上昇"
    if quadrant_key == "own_down_market_up":
        return f"{q_emoji} 要警戒 / 市場は伸びているのに取り残され"
    if quadrant_key == "own_down_market_down":
        return f"{q_emoji} 静観フェーズ / 市場全体が縮小"
    return "◇ データ蓄積中"


def draw_chart(product_cfg, history, out_path):
    pkey = product_cfg["name"]
    pkey_norm = PKEY_TO_SLUG[pkey]
    color = product_cfg["color"]
    display_name = product_cfg["display_name"]
    market_label = product_cfg["market"]["genre_label"]

    dates_sorted = sorted(history.keys())
    # グラフX軸は「観測日(前日=to_date_api)」でラベル付け。無ければ発行日-1日で計算。
    observed_dates = []
    for d in dates_sorted:
        obs = history[d].get("to_date_api")
        if obs:
            observed_dates.append(obs)
        else:
            # to_date_api 無い場合はdateから1日引いて推定
            from datetime import timedelta
            obs_dt = datetime.strptime(d, "%Y-%m-%d") - timedelta(days=1)
            observed_dates.append(obs_dt.strftime("%Y-%m-%d"))

    series_own = []
    series_own_raw = []
    comp_series = {}
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

    quadrant_key = compute_quadrant(series_own_raw)
    q_emoji, q_label, q_color = QUADRANT[quadrant_key]

    last_y = series_own[-1][1] if series_own else 0
    today_own = series_own_raw[-1][1] if series_own_raw else 0
    today_market = series_own_raw[-1][2] if series_own_raw else 0
    prev_share = series_own[-2][1] if len(series_own) >= 2 else None

    # media_breakdown（最新日のみ）
    latest = history[dates_sorted[-1]]["products"].get(pkey_norm, {})
    media_breakdown = latest.get("media_breakdown", {})
    mb_total = sum(media_breakdown.values()) if media_breakdown else 0

    delta_txt = ""
    delta_color = INK_SUB
    if prev_share is not None:
        delta = last_y - prev_share
        if delta > 0.01:
            delta_txt = f"▲ +{delta:.2f}pt"
            delta_color = "#1F9D55"
        elif delta < -0.01:
            delta_txt = f"▼ {delta:.2f}pt"
            delta_color = "#C4362C"
        else:
            delta_txt = "→ 変化なし"

    # === Figure (1400x1300) ===
    fig = plt.figure(figsize=(14, 13), dpi=100)
    fig.patch.set_facecolor(BG)

    # ======= 上段ヘッダー =======
    header_h = 0.22
    ax_head = fig.add_axes([0, 1-header_h, 1, header_h], zorder=1)
    ax_head.set_facecolor(BG)
    ax_head.set_xlim(0,1); ax_head.set_ylim(0,1)
    ax_head.axis("off")

    # カラーアクセントバー（左端、商品カラー）
    ax_head.add_patch(Rectangle((0, 0), 0.008, 1, facecolor=color, transform=ax_head.transAxes))

    # 見出し（報道系の太字デカ文字）
    headline_text = make_headline(quadrant_key, prev_share is not None and last_y - prev_share)
    ax_head.text(0.035, 0.8, "TODAY'S HEADLINE", fontsize=10, color=INK_SUB, weight="bold",
                 family="serif", transform=ax_head.transAxes)
    ax_head.text(0.035, 0.58, headline_text, fontsize=22, color=INK, weight="bold",
                 transform=ax_head.transAxes)

    # 商品名（小さめで下）
    ax_head.text(0.035, 0.3, display_name, fontsize=17, color=INK, weight="bold",
                 transform=ax_head.transAxes)
    ax_head.text(0.035, 0.1, f"市場 / {market_label}", fontsize=11, color=INK_SUB,
                 transform=ax_head.transAxes)

    # 右: TODAY SHARE（特大）
    ax_head.text(0.97, 0.78, "TODAY  SHARE", fontsize=10, color=INK_SUB, ha="right",
                 family="serif", weight="bold", transform=ax_head.transAxes)
    ax_head.text(0.97, 0.4, f"{last_y:.2f}%", fontsize=60, color=color, ha="right", weight="bold",
                 transform=ax_head.transAxes)
    if delta_txt:
        ax_head.text(0.97, 0.1, delta_txt, fontsize=13, color=delta_color, ha="right",
                     weight="bold", transform=ax_head.transAxes)

    # 下ボーダーライン
    ax_head.plot([0.02, 0.98], [0.0, 0.0], color=LINE_LIGHT, lw=1.5, transform=ax_head.transAxes)

    # ======= 日付帯 =======
    date_y = 1 - header_h - 0.025
    date_h = 0.025
    ax_date = fig.add_axes([0, date_y, 1, date_h], zorder=2)
    ax_date.axis("off")
    ax_date.set_facecolor(BG)
    today_str = datetime.strptime(dates_sorted[-1], "%Y-%m-%d").strftime("%Y-%m-%d (%a)")
    latest_obs = observed_dates[-1]
    latest_obs_str = datetime.strptime(latest_obs, "%Y-%m-%d").strftime("%Y-%m-%d (%a)")
    ax_date.text(0.035, 0.5, f"発行: {today_str}  ／  最新観測日: {latest_obs_str}  ／  各点は2日間差分",
                 fontsize=10, color=INK_SUB, va="center", family="serif",
                 transform=ax_date.transAxes, style="italic")

    # ======= 中段: 折れ線 =======
    chart_top = date_y - 0.02
    chart_bottom = 0.32
    ax = fig.add_axes([0.08, chart_bottom, 0.85, chart_top - chart_bottom], zorder=2)
    ax.set_facecolor(BG)

    # ⚠️ X軸は「観測日(前日=to_date_api)」ラベル基準。発行日(dates_sorted)ではない。
    dates_dt = [datetime.strptime(d, "%Y-%m-%d") for d in observed_dates]
    x_pos = list(range(len(dates_dt)))

    # 競合線
    comp_colors = [COMP1, COMP2]
    for i, cname in enumerate(top_comps):
        pts = comp_series.get(cname, [])
        if not pts: continue
        # 競合も observed_date ベースでx位置決定
        date_idx = {d:i_ for i_,d in enumerate(dates_sorted)}
        px = [date_idx[d] for d,_ in pts if d in date_idx]
        py = [v for d,v in pts if d in date_idx]
        ax.plot(px, py, color=comp_colors[i], lw=2.3, marker="o", markersize=8,
                markerfacecolor="white", markeredgecolor=comp_colors[i], markeredgewidth=1.8,
                linestyle="-", alpha=0.92, label=shorten(cname, 26), zorder=3)
        if py and px:
            ax.annotate(f"{py[-1]:.1f}%",
                        xy=(px[-1], py[-1]),
                        xytext=(12, 0), textcoords="offset points",
                        fontsize=11, color=INK_SUB, va="center", zorder=4)

    # 自社線
    own_y = [v for _,v in series_own]
    ax.plot(x_pos, own_y, color=color, lw=4.5, marker="o", markersize=13,
            markerfacecolor=color, markeredgecolor="white", markeredgewidth=3,
            label=f"自社", zorder=6, solid_capstyle="round")

    for i, (xi, yi) in enumerate(zip(x_pos, own_y)):
        is_last = (i == len(own_y) - 1)
        ax.annotate(f"{yi:.2f}%",
                    xy=(xi, yi),
                    xytext=(0, 18 if is_last else 13),
                    textcoords="offset points",
                    fontsize=15 if is_last else 11,
                    color=color if is_last else INK,
                    weight="bold" if is_last else "normal",
                    ha="center", zorder=10)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.strftime("%-m/%-d\n(%a)") for d in dates_dt], fontsize=12, color=INK_SUB)
    ax.tick_params(axis="y", colors=INK_SUB, labelsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))

    all_y = own_y[:]
    for cname in top_comps:
        all_y += [v for _,v in comp_series.get(cname, [])]
    ymax = max(all_y) if all_y else 1
    ax.set_ylim(0, ymax * 1.3)

    ax.grid(True, axis="y", color=GRID, linestyle="-", alpha=1, zorder=1, lw=1)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(LINE_LIGHT)
    ax.spines["left"].set_linewidth(1)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(LINE_LIGHT)
    ax.spines["bottom"].set_linewidth(1)

    ax.set_ylabel("市場占有率", fontsize=12, color=INK_SUB, labelpad=10)

    leg = ax.legend(loc="upper left", fontsize=11, frameon=False, labelcolor=INK,
                    handlelength=2.5, handletextpad=0.6, borderaxespad=0.3)

    # セクションタイトル
    ax.set_title("直近4日の市場占有率推移", fontsize=13, color=INK, pad=12, weight="bold", loc="left")

    # ======= 下段: 媒体別ブレイクダウン =======
    mb_top = chart_bottom - 0.04
    mb_h = 0.26
    ax_mb = fig.add_axes([0.08, 0.04, 0.85, 0.24], zorder=2)
    ax_mb.set_facecolor(BG)
    ax_mb.set_xlim(0,1); ax_mb.set_ylim(0,1)
    ax_mb.axis("off")

    # セクションタイトル
    ax_mb.text(0, 0.92, "今日の媒体別 内訳（どこで稼いでる？）", fontsize=13, color=INK,
               weight="bold", transform=ax_mb.transAxes)

    if mb_total > 0:
        # 横棒 stacked bar
        bar_y = 0.35
        bar_h = 0.26
        cur_x = 0.0
        labels = [
            ("動画", "video", VIDEO_COLOR),
            ("バナー(静止画)", "banner", BANNER_COLOR),
            ("カルーセル", "carousel", CAROUSEL_COLOR),
        ]
        for label, key, col in labels:
            v = media_breakdown.get(key, 0)
            if v == 0: continue
            pct = v / mb_total
            ax_mb.add_patch(Rectangle((cur_x, bar_y), pct, bar_h, facecolor=col,
                                       edgecolor="white", lw=2, transform=ax_mb.transAxes))
            # パーセント文字（バー内、幅が十分ある場合）
            if pct > 0.08:
                ax_mb.text(cur_x + pct/2, bar_y + bar_h/2, f"{pct*100:.0f}%",
                          fontsize=14, color="white", weight="bold",
                          ha="center", va="center", transform=ax_mb.transAxes)
            cur_x += pct

        # 凡例（バー下、3項目並列）
        leg_y = 0.05
        col_x = [0.0, 0.37, 0.74]
        for (label, key, col), cx in zip(labels, col_x):
            v = media_breakdown.get(key, 0)
            pct = (v / mb_total * 100) if mb_total else 0
            # カラー四角
            ax_mb.add_patch(Rectangle((cx, leg_y + 0.12), 0.02, 0.1, facecolor=col,
                                       transform=ax_mb.transAxes))
            # ラベル + 金額/%
            ax_mb.text(cx + 0.028, leg_y + 0.22, label, fontsize=12, color=INK,
                      weight="bold", va="top", transform=ax_mb.transAxes)
            ax_mb.text(cx + 0.028, leg_y + 0.08, f"{fmt_yen(v)}  ({pct:.1f}%)",
                      fontsize=11, color=INK_SUB, va="top", transform=ax_mb.transAxes)

        # 最大カテゴリに小バッジ
        max_key = max(media_breakdown, key=lambda k: media_breakdown[k])
        max_pct = media_breakdown[max_key] / mb_total * 100
        if max_pct >= 60:
            label_name = {"video": "動画", "banner": "バナー(静止画)", "carousel": "カルーセル"}[max_key]
            ax_mb.text(0.99, 0.92, f"🎯 主戦場: {label_name} {max_pct:.0f}%",
                       fontsize=12, color=INK, ha="right", weight="bold",
                       bbox=dict(facecolor="#FFF3E0", edgecolor="#FF8A3D", boxstyle="round,pad=0.4"),
                       transform=ax_mb.transAxes)
    else:
        ax_mb.text(0.5, 0.5, "媒体別データなし（明日以降蓄積）", fontsize=12, color=INK_SUB,
                  ha="center", va="center", transform=ax_mb.transAxes)

    fig.savefig(out_path, facecolor=BG, dpi=110, bbox_inches=None)
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
        slug = PKEY_TO_SLUG.get(pkey, pkey.lower())
        out = OUT_DIR / f"{today}_voyage_{slug}.png"
        try:
            draw_chart(product, history, out)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ {slug}: {e}")


if __name__ == "__main__":
    main()
