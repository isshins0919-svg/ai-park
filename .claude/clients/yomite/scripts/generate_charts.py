#!/usr/bin/env python3
"""
ヨミテ デイリー 市場占有率チャート（日本語フル版）
history/*.json から 1商品1枚のシェア推移+媒体別ブレイクダウンPNGを生成。
白背景・太字見出し・数字主張強め。日本語ラベル徹底、意味の明確化。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 重要: グラフのX軸ラベルは「観測日(前日=to_date_api)」基準。
   発行日(history JSONの date フィールド)ではない！

   各データ点:
   - X軸ラベル = その点の「最新観測日」（APIのto_date）
   - 値 = その日を末尾とする過去2日間の差分（interval=2）

   例: history/2026-04-20.json は to_date_api=2026-04-19 なので
       グラフ上は「4/19」ラベル（4/18-4/19の2日間差分）で描画される。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

# ⚠️ 日本語統一（serif系は文字化けの原因なので全面的にHiragino Sansに固定）
plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False

# 曜日の日本語化
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]

def ja_weekday(dt):
    return WEEKDAY_JA[dt.weekday()]

def date_ja(dt, fmt="short"):
    """日本語付き日付。fmt='short'→'4/20(月)' / fmt='long'→'2026-04-21 (火)'"""
    if fmt == "short":
        return f"{dt.month}/{dt.day}({ja_weekday(dt)})"
    return f"{dt.strftime('%Y-%m-%d')} ({ja_weekday(dt)})"


ROOT = Path("/Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite")
HIST_DIR = ROOT / "history"
OUT_DIR = ROOT / "charts"
CONFIG_PATH = ROOT / "daily_news_config.json"

# カラーパレット
BG = "#FFFFFF"
INK = "#1B1F26"
INK_SUB = "#6E7682"
INK_SUB_LIGHT = "#9CA3AE"
LINE_LIGHT = "#E5E8EC"
GRID = "#F0F2F5"
COMP1 = "#B5BCC6"
COMP2 = "#D4D8DE"
VIDEO_COLOR = "#6C63FF"     # 動画 = パープル
BANNER_COLOR = "#FF8A3D"    # バナー = オレンジ
CAROUSEL_COLOR = "#3AC29A"  # カルーセル = グリーン

# 商品名 → slug
PKEY_TO_SLUG = {
    "on:myskin": "onmyskin",
    "プルーストクリーム2": "proust",
    "伸長ぐんぐん習慣": "gungun",
    "RKL": "rkl",
    "アポバスターF": "apobusterf",
}

# 状態（象限）定義 — 日本語名＋1行説明
QUADRANT = {
    "own_up_market_up":   ("追い風",      "市場も自社も拡大",        "#3AA6E8"),
    "own_up_market_down": ("自社独走",     "市場縮小の中で自社は伸長", "#F1A53A"),
    "own_down_market_up": ("乗り遅れ",     "市場拡大なのに自社後退",   "#E25860"),
    "own_down_market_down":("全体縮小",   "市場も自社も縮小",        "#9080B0"),
    "unknown":            ("データ蓄積中", "判定に必要な履歴が不足",   INK_SUB),
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


def compute_quadrant(raw):
    """絶対値ベースで象限判定。raw = [(date, own_cost, market_cost, share), ...]
    直近2日の自社¥と市場¥の変動を±5%しきい値で比較。
    """
    if len(raw) < 2:
        return "unknown"
    (_, own_p, market_p, _), (_, own_n, market_n, _) = raw[-2], raw[-1]
    market_up = market_p > 0 and market_n > market_p * 1.05
    market_down = market_p > 0 and market_n < market_p * 0.95
    own_up = own_p > 0 and own_n > own_p * 1.05
    own_down = own_p > 0 and own_n < own_p * 0.95
    if own_up and market_up: return "own_up_market_up"
    if own_up and market_down: return "own_up_market_down"
    if own_down and market_up: return "own_down_market_up"
    if own_down and market_down: return "own_down_market_down"
    if own_up: return "own_up_market_up"
    if own_down: return "own_down_market_down"
    return "own_up_market_up"


def extract_top_competitors(history, product_key, top_n=2):
    total_days = len(history)
    counter = {}
    total_cost = {}
    for date, h in history.items():
        p = h.get("products", {}).get(product_key, {})
        comps = p.get("competitors_top5") or p.get("competitors_top3") or p.get("competitors_top2") or []
        for c in comps:
            name = c.get("name","?")
            counter[name] = counter.get(name, 0) + 1
            total_cost[name] = total_cost.get(name, 0) + c.get("cost_diff", 0)
    ranked = sorted(counter.keys(), key=lambda n: (-counter[n], -total_cost.get(n,0), n))
    return ranked[:top_n]


def shorten(name, n=26):
    if len(name) <= n: return name
    return name[:n-1] + "…"


def fmt_yen(v):
    """¥1.23M / ¥456K / ¥789 形式"""
    if v >= 10**6: return f"¥{v/10**6:.2f}M"
    if v >= 10**3: return f"¥{v/10**3:.0f}K"
    return f"¥{int(v)}"


def fmt_delta(latest, prev, threshold=100000):
    """前日比の文字列・色・記号を返す。
    前日値が threshold (default: ¥100K) 未満の場合は「低水準→¥XXX」で%は出さない。
    戻り値: (text, color, is_meaningful)
    """
    if prev is None:
        return ("前日データなし", INK_SUB_LIGHT, False)
    if prev < threshold and latest > prev:
        # 低水準からの立ち上がり → %表示は紛らわしいので金額差で出す
        diff = latest - prev
        return (f"急増中 +{fmt_yen(diff)}", "#1F9D55", True)
    if prev == 0:
        return ("新規計上", "#1F9D55", False)
    pct = (latest - prev) / prev * 100
    if pct > 5:
        return (f"▲ +{pct:.0f}%", "#1F9D55", True)
    if pct < -5:
        return (f"▼ {pct:.0f}%", "#C4362C", True)
    return (f"→ ほぼ横ばい", INK_SUB, True)


def make_headline(quadrant_key, own_delta_pct=None):
    """象限と絶対値変動率から、分かりやすい日本語見出しを作る"""
    q_label, q_desc, _ = QUADRANT[quadrant_key]
    dstr = ""
    if own_delta_pct is not None:
        if own_delta_pct > 0:
            dstr = f"（自社 +{own_delta_pct:.0f}%）"
        else:
            dstr = f"（自社 {own_delta_pct:.0f}%）"
    if quadrant_key == "own_up_market_up":
        return f"追い風｜市場と一緒に自社も伸びている {dstr}"
    if quadrant_key == "own_up_market_down":
        return f"自社独走｜市場は縮小しているが自社は伸びている {dstr}"
    if quadrant_key == "own_down_market_up":
        return f"乗り遅れ｜市場は伸びているのに自社は後退 {dstr}"
    if quadrant_key == "own_down_market_down":
        return f"全体縮小｜市場も自社も縮小フェーズ {dstr}"
    return "データ蓄積中｜判定には2日以上の履歴が必要"


# ════════════════════════════════════════════════════════════════
# 商品個別チャート
# ════════════════════════════════════════════════════════════════
def draw_chart(product_cfg, history, out_path):
    pkey = product_cfg["name"]
    pkey_norm = PKEY_TO_SLUG[pkey]
    color = product_cfg["color"]
    display_name = product_cfg["display_name"]
    market_label = product_cfg["market"]["genre_label"]

    dates_sorted = sorted(history.keys())
    # X軸は「観測日(前日=to_date_api)」基準
    observed_dates = []
    for d in dates_sorted:
        obs = history[d].get("to_date_api")
        if obs:
            observed_dates.append(obs)
        else:
            obs_dt = datetime.strptime(d, "%Y-%m-%d") - timedelta(days=1)
            observed_dates.append(obs_dt.strftime("%Y-%m-%d"))

    # 時系列データ
    series_own = []
    series_own_abs = []
    series_own_raw = []
    comp_series = {}
    top_comps = extract_top_competitors(history, pkey_norm, top_n=2)

    for d in dates_sorted:
        h = history[d]["products"].get(pkey_norm, {})
        own = h.get("own", 0)
        market = h.get("market", 0)
        share = h.get("share_pct", 0)
        series_own.append((d, share))
        series_own_abs.append((d, own))
        series_own_raw.append((d, own, market, share))
        comps_full = h.get("competitors_top5") or h.get("competitors_top3") or h.get("competitors_top2") or []
        for c in comps_full:
            cname = c.get("name","")
            if cname in top_comps:
                comp_series.setdefault(cname, []).append((d, c.get("cost_diff", 0)))

    quadrant_key = compute_quadrant(series_own_raw)
    q_label, q_desc, q_color = QUADRANT[quadrant_key]

    last_share = series_own[-1][1] if series_own else 0
    today_own = series_own_raw[-1][1] if series_own_raw else 0
    today_market = series_own_raw[-1][2] if series_own_raw else 0
    prev_own = series_own_abs[-2][1] if len(series_own_abs) >= 2 else None
    prev_share = series_own[-2][1] if len(series_own) >= 2 else None

    own_delta_pct = None
    if prev_own and prev_own > 100000:  # 低水準はHEADLINE表記から除外
        own_delta_pct = (today_own - prev_own) / prev_own * 100

    latest = history[dates_sorted[-1]]["products"].get(pkey_norm, {})
    media_breakdown = latest.get("media_breakdown", {})
    mb_total = sum(media_breakdown.values()) if media_breakdown else 0

    # === Figure (1400x1300) ===
    fig = plt.figure(figsize=(14, 13), dpi=100)
    fig.patch.set_facecolor(BG)

    # ======= 上段ヘッダー =======
    header_h = 0.23
    ax_head = fig.add_axes([0, 1-header_h, 1, header_h], zorder=1)
    ax_head.set_facecolor(BG)
    ax_head.set_xlim(0,1); ax_head.set_ylim(0,1)
    ax_head.axis("off")

    # 左端カラーアクセントバー
    ax_head.add_patch(Rectangle((0, 0), 0.008, 1, facecolor=color, transform=ax_head.transAxes))

    # 左: 本日のサマリー見出し
    headline_text = make_headline(quadrant_key, own_delta_pct)
    ax_head.text(0.035, 0.82, "◆ 本日のサマリー", fontsize=11, color=INK_SUB, weight="bold",
                 transform=ax_head.transAxes)
    ax_head.text(0.035, 0.58, headline_text, fontsize=19, color=INK, weight="bold",
                 transform=ax_head.transAxes)
    # 商品名
    ax_head.text(0.035, 0.32, display_name, fontsize=17, color=INK, weight="bold",
                 transform=ax_head.transAxes)
    ax_head.text(0.035, 0.1, f"市場カテゴリ: {market_label}", fontsize=10, color=INK_SUB,
                 transform=ax_head.transAxes)

    # 右: 市場占有率（シェア）
    latest_obs_dt = datetime.strptime(observed_dates[-1], "%Y-%m-%d")
    latest_obs_short = date_ja(latest_obs_dt, "short")
    ax_head.text(0.97, 0.82, f"◆ ジャンル内の市場占有率  ({latest_obs_short}時点)",
                 fontsize=11, color=INK_SUB, ha="right", weight="bold",
                 transform=ax_head.transAxes)
    ax_head.text(0.97, 0.44, f"{last_share:.2f}%", fontsize=58, color=color, ha="right", weight="bold",
                 transform=ax_head.transAxes)

    # 前日比（シェアポイント差）
    if prev_share is not None:
        delta = last_share - prev_share
        if delta > 0.01:
            delta_txt = f"前日比 ▲ +{delta:.2f}pt"
            delta_color = "#1F9D55"
        elif delta < -0.01:
            delta_txt = f"前日比 ▼ {delta:.2f}pt"
            delta_color = "#C4362C"
        else:
            delta_txt = "前日比 → ほぼ横ばい"
            delta_color = INK_SUB
        ax_head.text(0.97, 0.16, delta_txt, fontsize=11, color=delta_color, ha="right",
                     weight="bold", transform=ax_head.transAxes)
    ax_head.text(0.97, 0.02, f"市場全体の広告消化額: {fmt_yen(today_market)}",
                 fontsize=10, color=INK_SUB, ha="right", transform=ax_head.transAxes)

    # 下ボーダーライン
    ax_head.plot([0.02, 0.98], [0.0, 0.0], color=LINE_LIGHT, lw=1.5, transform=ax_head.transAxes)

    # ======= 日付帯 =======
    date_y = 1 - header_h - 0.028
    date_h = 0.028
    ax_date = fig.add_axes([0, date_y, 1, date_h], zorder=2)
    ax_date.axis("off")
    ax_date.set_facecolor(BG)
    today_dt = datetime.strptime(dates_sorted[-1], "%Y-%m-%d")
    today_str = date_ja(today_dt, "long")
    latest_obs_str = date_ja(latest_obs_dt, "long")
    ax_date.text(0.035, 0.5,
                 f"発行日: {today_str}  ／  最新観測日: {latest_obs_str}  ／  各データ点は直近2日間の変動",
                 fontsize=10, color=INK_SUB, va="center", transform=ax_date.transAxes)

    # ======= 中段: 折れ線 =======
    chart_top = date_y - 0.025
    chart_bottom = 0.32
    ax = fig.add_axes([0.08, chart_bottom, 0.85, chart_top - chart_bottom], zorder=2)
    ax.set_facecolor(BG)

    dates_dt = [datetime.strptime(d, "%Y-%m-%d") for d in observed_dates]
    x_pos = list(range(len(dates_dt)))
    date_idx = {d:i_ for i_,d in enumerate(dates_sorted)}

    # 競合線
    comp_colors = [COMP1, COMP2]
    for i, cname in enumerate(top_comps):
        pts = comp_series.get(cname, [])
        if not pts: continue
        px = [date_idx[d] for d,_ in pts if d in date_idx]
        py = [v for d,v in pts if d in date_idx]
        ax.plot(px, py, color=comp_colors[i], lw=2.3, marker="o", markersize=8,
                markerfacecolor="white", markeredgecolor=comp_colors[i], markeredgewidth=1.8,
                linestyle="-", alpha=0.92, label=f"競合: {shorten(cname, 22)}", zorder=3)
        if py and px:
            ax.annotate(fmt_yen(py[-1]),
                        xy=(px[-1], py[-1]),
                        xytext=(12, 0), textcoords="offset points",
                        fontsize=11, color=INK_SUB, va="center", zorder=4)

    # 自社線
    own_y = [v for _,v in series_own_abs]
    ax.plot(x_pos, own_y, color=color, lw=4.5, marker="o", markersize=13,
            markerfacecolor=color, markeredgecolor="white", markeredgewidth=3,
            label=f"自社（ヨミテ）", zorder=6, solid_capstyle="round")

    for i, (xi, yi) in enumerate(zip(x_pos, own_y)):
        is_last = (i == len(own_y) - 1)
        ax.annotate(fmt_yen(yi),
                    xy=(xi, yi),
                    xytext=(0, 18 if is_last else 13),
                    textcoords="offset points",
                    fontsize=15 if is_last else 11,
                    color=color if is_last else INK,
                    weight="bold" if is_last else "normal",
                    ha="center", zorder=10)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{d.month}/{d.day}\n({ja_weekday(d)})" for d in dates_dt],
                       fontsize=12, color=INK_SUB)
    ax.tick_params(axis="y", colors=INK_SUB, labelsize=11)

    def yaxis_yen_fmt(x, _):
        if x >= 10**6: return f"¥{x/10**6:.1f}M"
        if x >= 10**3: return f"¥{x/10**3:.0f}K"
        return f"¥{int(x)}"
    ax.yaxis.set_major_formatter(plt.FuncFormatter(yaxis_yen_fmt))

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

    ax.set_ylabel("広告消化額（円）", fontsize=12, color=INK_SUB, labelpad=10)

    leg = ax.legend(loc="upper left", fontsize=11, frameon=False, labelcolor=INK,
                    handlelength=2.5, handletextpad=0.6, borderaxespad=0.3)

    ax.set_title("直近の広告消化額推移（自社 vs 主要競合 上位2社）",
                 fontsize=13, color=INK, pad=12, weight="bold", loc="left")

    # ======= 下段: 媒体別ブレイクダウン =======
    ax_mb = fig.add_axes([0.08, 0.04, 0.85, 0.24], zorder=2)
    ax_mb.set_facecolor(BG)
    ax_mb.set_xlim(0,1); ax_mb.set_ylim(0,1)
    ax_mb.axis("off")

    ax_mb.text(0, 0.92, "今日の自社クリエイティブ 媒体別の本数内訳",
               fontsize=13, color=INK, weight="bold", transform=ax_mb.transAxes)
    ax_mb.text(0, 0.78, "※ 上位3本の広告クリエイティブを媒体タイプで分類",
               fontsize=10, color=INK_SUB, transform=ax_mb.transAxes)

    if mb_total > 0:
        bar_y = 0.35
        bar_h = 0.22
        cur_x = 0.0
        labels = [
            ("動画", "video", VIDEO_COLOR),
            ("バナー（静止画）", "banner", BANNER_COLOR),
            ("カルーセル", "carousel", CAROUSEL_COLOR),
        ]
        for label, key, col in labels:
            v = media_breakdown.get(key, 0)
            if v == 0: continue
            pct = v / mb_total
            ax_mb.add_patch(Rectangle((cur_x, bar_y), pct, bar_h, facecolor=col,
                                       edgecolor="white", lw=2, transform=ax_mb.transAxes))
            if pct > 0.08:
                ax_mb.text(cur_x + pct/2, bar_y + bar_h/2, f"{pct*100:.0f}%",
                          fontsize=14, color="white", weight="bold",
                          ha="center", va="center", transform=ax_mb.transAxes)
            cur_x += pct

        # 凡例
        leg_y = 0.05
        col_x = [0.0, 0.37, 0.74]
        for (label, key, col), cx in zip(labels, col_x):
            v = media_breakdown.get(key, 0)
            pct = (v / mb_total * 100) if mb_total else 0
            ax_mb.add_patch(Rectangle((cx, leg_y + 0.12), 0.02, 0.1, facecolor=col,
                                       transform=ax_mb.transAxes))
            ax_mb.text(cx + 0.028, leg_y + 0.22, label, fontsize=12, color=INK,
                      weight="bold", va="top", transform=ax_mb.transAxes)
            ax_mb.text(cx + 0.028, leg_y + 0.08, f"{v}本 ({pct:.0f}%)",
                      fontsize=11, color=INK_SUB, va="top", transform=ax_mb.transAxes)

        # 主戦場バッジ
        max_key = max(media_breakdown, key=lambda k: media_breakdown[k])
        max_pct = media_breakdown[max_key] / mb_total * 100
        if max_pct >= 60:
            label_name = {"video": "動画", "banner": "バナー（静止画）",
                         "carousel": "カルーセル"}[max_key]
            ax_mb.text(0.99, 0.92, f"主戦場: {label_name} {max_pct:.0f}%",
                       fontsize=12, color=INK, ha="right", weight="bold",
                       bbox=dict(facecolor="#FFF3E0", edgecolor="#FF8A3D",
                                 boxstyle="round,pad=0.4"),
                       transform=ax_mb.transAxes)
    else:
        ax_mb.text(0.5, 0.5, "媒体別データなし（明日以降蓄積）",
                  fontsize=12, color=INK_SUB,
                  ha="center", va="center", transform=ax_mb.transAxes)

    fig.savefig(out_path, facecolor=BG, dpi=110, bbox_inches=None)
    plt.close(fig)
    print(f"✅ {out_path}")


# ════════════════════════════════════════════════════════════════
# サマリ（全5商品）ダッシュボード画像
# ════════════════════════════════════════════════════════════════
def draw_summary(cfg, history, out_path):
    """5商品を1枚に集約した全体ダッシュボード。
    各商品: 商品名, 自社広告消化額, 前日比, ジャンル占有率, 状態, 主な媒体 を横一列で並べる。
    各カラムに明確なヘッダー行と下段の凡例を入れて、誰が見ても分かるようにする。
    """
    dates_sorted = sorted(history.keys())
    today_date = dates_sorted[-1]
    observed_date = history[today_date].get("to_date_api")
    if not observed_date:
        observed_date = (datetime.strptime(today_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    today_dt = datetime.strptime(today_date, "%Y-%m-%d")
    obs_dt = datetime.strptime(observed_date, "%Y-%m-%d")
    today_str = date_ja(today_dt, "long")
    obs_str = date_ja(obs_dt, "short")

    n = len(cfg["products"])
    fig = plt.figure(figsize=(16, 10), dpi=100)
    fig.patch.set_facecolor(BG)

    # ヘッダー (高め)
    header_h = 0.16
    ax_head = fig.add_axes([0, 1-header_h, 1, header_h])
    ax_head.set_facecolor(BG); ax_head.axis("off")
    ax_head.set_xlim(0,1); ax_head.set_ylim(0,1)

    ax_head.text(0.035, 0.72, "ヨミテ 5商品デイリー・ダッシュボード",
                 fontsize=26, color=INK, weight="bold", transform=ax_head.transAxes)
    ax_head.text(0.035, 0.42,
                 f"発行日: {today_str}｜最新観測日: {obs_str}｜直近2日間の広告配信の変動をレポート",
                 fontsize=12, color=INK_SUB, transform=ax_head.transAxes)
    ax_head.text(0.035, 0.18,
                 "※ 数字の意味は各カラムヘッダーと最下段の凡例を参照ください",
                 fontsize=10, color=INK_SUB_LIGHT, transform=ax_head.transAxes)
    ax_head.plot([0.02, 0.98], [0.02, 0.02], color=LINE_LIGHT, lw=1.5, transform=ax_head.transAxes)

    # ======= テーブルヘッダー行 =======
    # カラム位置（x座標）
    COL_X = {
        "product": 0.035,
        "own":     0.40,
        "delta":   0.54,
        "share":   0.70,
        "state":   0.82,
        "channel": 0.965,
    }

    thead_h = 0.05
    thead_y = 1 - header_h - thead_h - 0.01
    ax_th = fig.add_axes([0, thead_y, 1, thead_h])
    ax_th.set_facecolor("#F8FAFC"); ax_th.axis("off")
    ax_th.set_xlim(0,1); ax_th.set_ylim(0,1)

    # ヘッダーラベル
    ax_th.text(COL_X["product"], 0.5, "商品名／所属ジャンル",
               fontsize=11, color=INK, weight="bold", va="center", transform=ax_th.transAxes)
    ax_th.text(COL_X["own"], 0.5, "自社の広告消化額",
               fontsize=11, color=INK, weight="bold", va="center", ha="right", transform=ax_th.transAxes)
    ax_th.text(COL_X["delta"], 0.5, "前日比",
               fontsize=11, color=INK, weight="bold", va="center", ha="right", transform=ax_th.transAxes)
    ax_th.text(COL_X["share"], 0.5, "ジャンル内の市場占有率",
               fontsize=11, color=INK, weight="bold", va="center", ha="right", transform=ax_th.transAxes)
    ax_th.text(COL_X["state"], 0.5, "状態",
               fontsize=11, color=INK, weight="bold", va="center", ha="center", transform=ax_th.transAxes)
    ax_th.text(COL_X["channel"], 0.5, "主な媒体",
               fontsize=11, color=INK, weight="bold", va="center", ha="right", transform=ax_th.transAxes)

    ax_th.plot([0.02, 0.98], [0.0, 0.0], color=LINE_LIGHT, lw=1, transform=ax_th.transAxes)

    # ======= 各商品行 =======
    footer_h = 0.16   # 凡例用スペース
    rows_top = thead_y - 0.005
    rows_bottom = footer_h + 0.01
    row_h = (rows_top - rows_bottom) / n

    for idx, product in enumerate(cfg["products"]):
        pkey = product["name"]
        pkey_norm = PKEY_TO_SLUG.get(pkey, pkey.lower())
        color = product["color"]
        display_name = product["display_name"]
        market_label = product["market"].get("genre_label", "")

        # データ集約
        series_own_abs = []
        series_own_raw = []
        shares = []
        for d in dates_sorted:
            h = history[d]["products"].get(pkey_norm, {})
            own = h.get("own", 0)
            market = h.get("market", 0)
            share = h.get("share_pct", 0)
            series_own_abs.append(own)
            series_own_raw.append((d, own, market, share))
            shares.append(share)

        latest_own = series_own_abs[-1] if series_own_abs else 0
        prev_own = series_own_abs[-2] if len(series_own_abs) >= 2 else None
        latest_share = shares[-1] if shares else 0
        latest_market = series_own_raw[-1][2] if series_own_raw else 0

        quadrant_key = compute_quadrant(series_own_raw)
        q_label, q_desc, q_color = QUADRANT[quadrant_key]

        # 媒体別主戦場
        latest_mb = history[today_date]["products"].get(pkey_norm, {}).get("media_breakdown", {})
        mb_total = sum(latest_mb.values()) if latest_mb else 0
        main_channel_txt = "データなし"
        if mb_total > 0:
            mx = max(latest_mb, key=lambda k: latest_mb[k])
            mx_pct = latest_mb[mx] / mb_total * 100
            ch_label = {"video":"動画", "banner":"バナー", "carousel":"カルーセル"}.get(mx, mx)
            main_channel_txt = f"{ch_label} {mx_pct:.0f}%"

        # 前日比（低水準対策済み）
        delta_txt, delta_color, _ = fmt_delta(latest_own, prev_own)

        y_top = rows_top - idx * row_h
        ax = fig.add_axes([0, y_top - row_h, 1, row_h])
        ax.set_facecolor(BG); ax.axis("off")
        ax.set_xlim(0,1); ax.set_ylim(0,1)

        # 左カラーバー
        ax.add_patch(Rectangle((0.02, 0.15), 0.005, 0.7, facecolor=color, transform=ax.transAxes))

        # 商品名 + ジャンル
        ax.text(COL_X["product"], 0.68, display_name, fontsize=15, color=INK,
                weight="bold", va="center", transform=ax.transAxes)
        ax.text(COL_X["product"], 0.30, f"市場全体: {fmt_yen(latest_market)}",
                fontsize=10, color=INK_SUB, va="center", transform=ax.transAxes)

        # 自社広告消化額
        ax.text(COL_X["own"], 0.5, fmt_yen(latest_own),
                fontsize=22, color=color, weight="bold",
                va="center", ha="right", transform=ax.transAxes)

        # 前日比
        ax.text(COL_X["delta"], 0.5, delta_txt,
                fontsize=14, color=delta_color, weight="bold",
                va="center", ha="right", transform=ax.transAxes)

        # ジャンル内占有率
        ax.text(COL_X["share"], 0.5, f"{latest_share:.2f}%",
                fontsize=22, color=color, weight="bold",
                va="center", ha="right", transform=ax.transAxes)

        # 状態バッジ
        ax.add_patch(FancyBboxPatch((0.775, 0.26), 0.10, 0.48,
                                    boxstyle="round,pad=0.02",
                                    facecolor=q_color, edgecolor="none", alpha=0.95,
                                    transform=ax.transAxes))
        ax.text(COL_X["state"], 0.58, q_label, fontsize=12, color="white",
                weight="bold", ha="center", va="center", transform=ax.transAxes)
        ax.text(COL_X["state"], 0.38, q_desc, fontsize=8, color="white",
                ha="center", va="center", transform=ax.transAxes)

        # 主な媒体
        ax.text(COL_X["channel"], 0.5, main_channel_txt,
                fontsize=13, color=INK, weight="bold",
                va="center", ha="right", transform=ax.transAxes)

        # 下ボーダー
        ax.plot([0.02, 0.98], [0.02, 0.02], color=LINE_LIGHT, lw=0.8, transform=ax.transAxes)

    # ======= 最下段: 凡例（数字の意味） =======
    ax_fg = fig.add_axes([0, 0, 1, footer_h])
    ax_fg.set_facecolor("#FAFBFC"); ax_fg.axis("off")
    ax_fg.set_xlim(0,1); ax_fg.set_ylim(0,1)
    ax_fg.plot([0.02, 0.98], [1.0, 1.0], color=LINE_LIGHT, lw=1.5, transform=ax_fg.transAxes)

    ax_fg.text(0.035, 0.82, "◆ 用語の説明（この表の読み方）",
               fontsize=11, color=INK, weight="bold", transform=ax_fg.transAxes)

    legend_items = [
        ("自社の広告消化額",
         "ヨミテが直近2日間で配信した広告の総消化金額"),
        ("前日比",
         "昨日との比較。低水準（¥100K未満）からの増加は金額差で表記"),
        ("ジャンル内の市場占有率",
         "所属ジャンルの全広告消化額のうち自社が占める割合（自社／市場 × 100）"),
        ("状態",
         "自社 vs 市場 の変動パターン。追い風／自社独走／乗り遅れ／全体縮小の4区分"),
        ("主な媒体",
         "自社クリエイティブ上位3本のうち最も本数の多い媒体タイプとその割合"),
    ]
    # 2列で配置
    for i, (term, desc) in enumerate(legend_items):
        col = i % 2
        row = i // 2
        x = 0.035 + col * 0.49
        y = 0.62 - row * 0.2
        ax_fg.text(x, y, f"・{term}:", fontsize=10, color=INK,
                   weight="bold", va="center", transform=ax_fg.transAxes)
        ax_fg.text(x + 0.12, y, desc, fontsize=10, color=INK_SUB,
                   va="center", transform=ax_fg.transAxes)

    fig.savefig(out_path, facecolor=BG, dpi=110, bbox_inches=None)
    plt.close(fig)
    print(f"✅ {out_path} (summary)")


def main():
    cfg = load_config()
    history = load_history()
    if not history:
        print("❌ history empty")
        sys.exit(1)

    today = sorted(history.keys())[-1]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # サマリ画像を最初に生成
    summary_path = OUT_DIR / f"{today}_voyage_00summary.png"
    try:
        draw_summary(cfg, history, summary_path)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ summary: {e}")

    # 各商品
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
