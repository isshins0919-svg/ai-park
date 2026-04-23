#!/usr/bin/env python3
"""
ヨミテ デイリー 「勝ってるか / 負けてるか」チャート v4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
設計思想:
  - 絶対¥は信用できない（DPro推定誤差あり）→ 絶対値を廃止
  - 本質は「競合との比較・市場内での順位」
  - 一目で「勝ってる／負けてる」が分かることが最優先
  - Meta(FB/Insta) + YouTube(通常/Shorts) に集計対象を限定

生成チャート:
  ① サマリ: 5商品の市場順位・シェア%・前日比を一画面で
  ② 商品別: ①順位バッジ大 ②市場リーダーボードTOP5 ③主要競合との直接対決

データソース:
  history/{YYYY-MM-DD}.json の products[slug]:
    - share_pct          (ジャンル内シェア%)
    - rank               (市場内の順位)
    - rank_total         (TOP何位までの計測か)
    - leaderboard_top5   (市場TOP5の全員)
    - competitors_top3   (自社除く競合TOP3)
    - media_breakdown    (媒体別本数)
    - data_confidence    ("low" など、データ信頼度の注釈)
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

# 日本語フォント統一（serif系は使用禁止・文字化けの原因）
plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]
def ja_weekday(dt): return WEEKDAY_JA[dt.weekday()]
def date_short(dt): return f"{dt.month}/{dt.day}({ja_weekday(dt)})"
def date_long(dt): return f"{dt.strftime('%Y-%m-%d')} ({ja_weekday(dt)})"

ROOT = Path("/Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite")
HIST_DIR = ROOT / "history"
OUT_DIR = ROOT / "charts"
CONFIG_PATH = ROOT / "daily_news_config.json"

# ═══ カラーパレット ═══
BG = "#FFFFFF"
INK = "#1B1F26"
INK_SUB = "#6E7682"
INK_SUB_LIGHT = "#9CA3AE"
LINE_LIGHT = "#E5E8EC"
GRID = "#F2F4F7"

# 順位バッジのカラー（勝ち負けの視覚化）
# ⚠️ matplotlibのHiragino Sansで絵文字が文字化けするので、
#    絵文字ではなく文字記号（◆◇◎●▲▼）で表現
RANK_COLOR = {
    1: "#FFD700",   # 金: 首位
    2: "#3AA6E8",   # 青: 2位（勝ち圏）
    3: "#3AA6E8",   # 青: 3位（勝ち圏）
    4: "#F1A53A",   # オレンジ: 4位（要注意）
    5: "#E25860",   # 赤: 5位以下（負け圏）
}
RANK_LABEL = {
    1: "首位・独走中",
    2: "2位・追撃ポジション",
    3: "3位・勝ち圏維持",
    4: "4位・要注意",
    5: "劣勢・戦略見直し",
}

# 媒体カラー
VIDEO_COLOR = "#6C63FF"
BANNER_COLOR = "#FF8A3D"
CAROUSEL_COLOR = "#3AC29A"

# 商品名 → slug
PKEY_TO_SLUG = {
    "on:myskin": "onmyskin",
    "プルーストクリーム2": "proust",
    "伸長ぐんぐん習慣": "gungun",
    "RKL": "rkl",
    "アポバスターF": "apobusterf",
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


def rank_color(rank, total=5):
    if rank is None: return INK_SUB
    return RANK_COLOR.get(rank, RANK_COLOR[5])


def rank_judgement(rank):
    if rank is None: return "評価不能", INK_SUB
    if rank == 1:    return "首位・独走中", "#C48A00"
    if rank == 2:    return "2位・追撃ポジション", "#3AA6E8"
    if rank == 3:    return "3位・勝ち圏維持", "#3AA6E8"
    if rank == 4:    return "4位・要注意", "#F1A53A"
    return "劣勢・戦略見直し", "#C4362C"


def shorten(name, n=30):
    if len(name) <= n: return name
    return name[:n-1] + "…"


def fmt_pct(v):
    if v is None: return "—"
    return f"{v:.2f}%"


# ════════════════════════════════════════════════════════════
# 商品個別チャート：順位 × リーダーボード × 直接対決
# ════════════════════════════════════════════════════════════
def draw_product_chart(product_cfg, history, out_path):
    pkey = product_cfg["name"]
    pkey_norm = PKEY_TO_SLUG[pkey]
    color = product_cfg["color"]
    display_name = product_cfg["display_name"]
    market_label = product_cfg["market"]["genre_label"]

    dates_sorted = sorted(history.keys())
    today_date = dates_sorted[-1]
    obs_date = history[today_date].get("to_date_api")
    if not obs_date:
        obs_date = (datetime.strptime(today_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    today_dt = datetime.strptime(today_date, "%Y-%m-%d")
    obs_dt = datetime.strptime(obs_date, "%Y-%m-%d")

    p = history[today_date]["products"].get(pkey_norm, {})
    rank = p.get("rank")
    rank_total = p.get("rank_total", 5)
    share = p.get("share_pct", 0)
    leaderboard = p.get("leaderboard_top5", [])
    competitors = p.get("competitors_top3", [])
    confidence = p.get("data_confidence", "high")
    confidence_note = p.get("data_confidence_reason", "")

    # 自社シェアの直近履歴（推移のライトバージョン）
    share_history = []
    for d in dates_sorted[-4:]:
        s = history[d]["products"].get(pkey_norm, {}).get("share_pct")
        if s is not None:
            obs_d = history[d].get("to_date_api", d)
            share_history.append((obs_d, s))

    # 前日比
    prev_share = share_history[-2][1] if len(share_history) >= 2 else None
    delta = share - prev_share if prev_share is not None else None

    r_label, r_color = rank_judgement(rank)
    r_bg = rank_color(rank)

    # ═══ Figure: 14x13 ═══
    fig = plt.figure(figsize=(14, 13), dpi=100)
    fig.patch.set_facecolor(BG)

    # ════════════════════════════════════════════
    # ① ヘッダー
    # ════════════════════════════════════════════
    header_h = 0.24
    ax_h = fig.add_axes([0, 1 - header_h, 1, header_h])
    ax_h.set_facecolor(BG); ax_h.axis("off")
    ax_h.set_xlim(0, 1); ax_h.set_ylim(0, 1)

    # 左端カラーバー
    ax_h.add_patch(Rectangle((0, 0), 0.008, 1, facecolor=color, transform=ax_h.transAxes))

    # 左: 商品名 + 観測日
    ax_h.text(0.035, 0.80, display_name, fontsize=19, color=INK, weight="bold",
              transform=ax_h.transAxes)
    ax_h.text(0.035, 0.65, f"市場カテゴリ: {market_label}",
              fontsize=10, color=INK_SUB, transform=ax_h.transAxes)
    ax_h.text(0.035, 0.52, f"観測日: {date_long(obs_dt)} ／ Meta(FB/Insta) + YouTube(通常/Shorts) 集計",
              fontsize=10, color=INK_SUB_LIGHT, transform=ax_h.transAxes)

    # 大きな順位バッジ（中央）
    if rank:
        badge_x, badge_y = 0.56, 0.20
        badge_w, badge_h = 0.18, 0.62
        ax_h.add_patch(FancyBboxPatch((badge_x, badge_y), badge_w, badge_h,
                                      boxstyle="round,pad=0.02",
                                      facecolor=r_bg, edgecolor="none", alpha=0.95,
                                      transform=ax_h.transAxes))
        ax_h.text(badge_x + badge_w/2, badge_y + badge_h * 0.68,
                  f"{rank}位", fontsize=46, color="white", weight="bold",
                  ha="center", va="center", transform=ax_h.transAxes)
        ax_h.text(badge_x + badge_w/2, badge_y + badge_h * 0.22,
                  f"/ 市場TOP{rank_total}", fontsize=11, color="white",
                  ha="center", va="center", transform=ax_h.transAxes)

    # 右: シェア% + 勝ち負けメッセージ
    ax_h.text(0.97, 0.82, "◆ ジャンル内シェア",
              fontsize=11, color=INK_SUB, ha="right", weight="bold",
              transform=ax_h.transAxes)
    ax_h.text(0.97, 0.48, fmt_pct(share), fontsize=54, color=color, weight="bold",
              ha="right", transform=ax_h.transAxes)

    # 前日比
    if delta is not None:
        if delta > 0.01:
            dtxt, dcol = f"前日比 ▲ +{delta:.2f}pt", "#1F9D55"
        elif delta < -0.01:
            dtxt, dcol = f"前日比 ▼ {delta:.2f}pt", "#C4362C"
        else:
            dtxt, dcol = "前日比 → ほぼ横ばい", INK_SUB
        ax_h.text(0.97, 0.22, dtxt, fontsize=12, color=dcol, weight="bold",
                  ha="right", transform=ax_h.transAxes)
    ax_h.text(0.97, 0.08, r_label, fontsize=13, color=r_color, weight="bold",
              ha="right", transform=ax_h.transAxes)

    # 下ボーダー
    ax_h.plot([0.02, 0.98], [0.0, 0.0], color=LINE_LIGHT, lw=1.5, transform=ax_h.transAxes)

    # データ信頼度警告
    if confidence == "low":
        ax_h.text(0.035, -0.02,
                  f"※ データ信頼度: 低  {confidence_note}",
                  fontsize=10, color="#C4362C", weight="bold",
                  transform=ax_h.transAxes)

    # ════════════════════════════════════════════
    # ② 市場リーダーボード（TOP5 水平バー、全てaxes座標）
    # ════════════════════════════════════════════
    lb_top = 1 - header_h - 0.04
    lb_h = 0.44
    ax_lb = fig.add_axes([0.08, lb_top - lb_h, 0.85, lb_h])
    ax_lb.set_facecolor(BG)
    ax_lb.set_xlim(0, 1); ax_lb.set_ylim(0, 1)
    ax_lb.axis("off")

    ax_lb.text(0, 0.96, "市場リーダーボード TOP5（Meta+YouTube内 シェア%）",
               fontsize=14, color=INK, weight="bold", transform=ax_lb.transAxes)

    # リーダーボード（1位→5位）を上から順に描画
    lb_items = leaderboard[:5] if leaderboard else []
    N = max(len(lb_items), 1)

    # 描画エリア: y=0 〜 y=0.88
    AREA_TOP = 0.88
    AREA_BOTTOM = 0.02
    ROW_H = (AREA_TOP - AREA_BOTTOM) / N  # 各行の高さ

    # バーのx座標（axes 0-1）- 左半分が名前、右半分がバー
    BAR_LEFT = 0.52
    BAR_MAX_W = 0.36   # バー最大幅

    if lb_items:
        max_share = max([x.get("share_pct", 0) for x in lb_items])
        for i, item in enumerate(lb_items):
            rank_in_lb = i + 1  # 1位〜5位
            row_top_y = AREA_TOP - i * ROW_H
            row_center_y = row_top_y - ROW_H / 2

            name = shorten(item.get("name", "?"), 22)
            adv = shorten(item.get("advertiser", ""), 18)
            s = item.get("share_pct", 0)
            is_own = item.get("is_own", False)

            bar_color = color if is_own else INK_SUB_LIGHT
            text_color = color if is_own else INK
            text_weight = "bold" if is_own else "normal"

            # 行の背景（自社はハイライト）
            if is_own:
                ax_lb.add_patch(Rectangle(
                    (0, row_top_y - ROW_H), 1, ROW_H,
                    facecolor=color, alpha=0.06,
                    edgecolor="none",
                    transform=ax_lb.transAxes
                ))

            # 順位ラベル（左端）
            ax_lb.text(0.025, row_center_y, f"{rank_in_lb}位",
                       fontsize=14, color=INK_SUB, ha="left", va="center",
                       weight="bold" if is_own else "normal",
                       transform=ax_lb.transAxes)
            # 商品名 + 広告主（自社は背景色+色文字で自明なので記号なし）
            suffix = "  【自社】" if is_own else ""
            ax_lb.text(0.08, row_center_y + ROW_H * 0.18, f"{name}{suffix}",
                       fontsize=11, color=text_color, va="center",
                       weight=text_weight, transform=ax_lb.transAxes)
            ax_lb.text(0.08, row_center_y - ROW_H * 0.22, f"({adv})",
                       fontsize=9, color=INK_SUB_LIGHT, va="center",
                       transform=ax_lb.transAxes)
            # バー（正規化した幅）
            normalized_w = (s / max_share) * BAR_MAX_W if max_share > 0 else 0
            bar_h = ROW_H * 0.45
            ax_lb.add_patch(Rectangle(
                (BAR_LEFT, row_center_y - bar_h / 2), normalized_w, bar_h,
                facecolor=bar_color, alpha=0.92 if is_own else 0.42,
                edgecolor="white", linewidth=1.2,
                transform=ax_lb.transAxes
            ))
            # シェア%ラベル
            ax_lb.text(BAR_LEFT + normalized_w + 0.008, row_center_y,
                       f"{s:.1f}%",
                       fontsize=13, color=text_color, va="center",
                       weight="bold" if is_own else "normal",
                       transform=ax_lb.transAxes)

    # ════════════════════════════════════════════
    # ③ 直接対決（vs 主要競合2-3社）
    # ════════════════════════════════════════════
    hh_top = lb_top - lb_h - 0.04
    hh_h = 0.22
    ax_hh = fig.add_axes([0.08, 0.04, 0.85, hh_h])
    ax_hh.set_facecolor(BG)
    ax_hh.set_xlim(0, 1); ax_hh.set_ylim(0, 1)
    ax_hh.axis("off")

    ax_hh.text(0, 0.92, "主要競合との直接対決（vs 競合TOP3、自社除く）",
               fontsize=14, color=INK, weight="bold", transform=ax_hh.transAxes)

    if competitors:
        col_w = 0.31
        gap = 0.015
        start_x = 0
        for i, comp in enumerate(competitors[:3]):
            cname = shorten(comp.get("name", "?"), 22)
            cshare = comp.get("share_pct", 0)
            diff = share - cshare  # 正=自社勝ち / 負=負け

            x0 = start_x + i * (col_w + gap)
            # カード背景
            card_col = "#E8F5E9" if diff > 0 else "#FFEBEE"
            border_col = "#1F9D55" if diff > 0 else "#C4362C"
            ax_hh.add_patch(FancyBboxPatch((x0, 0.08), col_w, 0.75,
                                            boxstyle="round,pad=0.015",
                                            facecolor=card_col,
                                            edgecolor=border_col,
                                            linewidth=1.5,
                                            transform=ax_hh.transAxes))

            # 競合名
            ax_hh.text(x0 + col_w/2, 0.72, f"vs {cname}",
                       fontsize=10, color=INK, ha="center", weight="bold",
                       transform=ax_hh.transAxes)
            # 結論ラベル（絵文字使用せず記号で表現）
            if diff > 0:
                verdict, vcol = "◎ 優位", "#1F9D55"
                diff_txt = f"+{diff:.1f}pt"
            elif diff < 0:
                verdict, vcol = "● 劣勢", "#C4362C"
                diff_txt = f"{diff:.1f}pt"
            else:
                verdict, vcol = "＝ 拮抗", INK_SUB
                diff_txt = "±0.0pt"
            ax_hh.text(x0 + col_w/2, 0.56, verdict,
                       fontsize=15, color=vcol, ha="center", weight="bold",
                       transform=ax_hh.transAxes)
            # 差分
            ax_hh.text(x0 + col_w/2, 0.38, diff_txt,
                       fontsize=20, color=vcol, ha="center", weight="bold",
                       transform=ax_hh.transAxes)
            # 自社シェア vs 競合シェア
            ax_hh.text(x0 + col_w/2, 0.18,
                       f"自社 {share:.1f}%  vs  競合 {cshare:.1f}%",
                       fontsize=10, color=INK_SUB, ha="center",
                       transform=ax_hh.transAxes)
    else:
        ax_hh.text(0.5, 0.5, "競合データなし",
                   fontsize=12, color=INK_SUB, ha="center", va="center",
                   transform=ax_hh.transAxes)

    fig.savefig(out_path, facecolor=BG, dpi=110, bbox_inches=None)
    plt.close(fig)
    print(f"✅ {out_path}")


# ════════════════════════════════════════════════════════════
# サマリ：5商品の順位ダッシュボード
# ════════════════════════════════════════════════════════════
def draw_summary(cfg, history, out_path):
    dates_sorted = sorted(history.keys())
    today_date = dates_sorted[-1]
    obs_date = history[today_date].get("to_date_api", today_date)
    today_dt = datetime.strptime(today_date, "%Y-%m-%d")
    obs_dt = datetime.strptime(obs_date, "%Y-%m-%d")

    n = len(cfg["products"])
    fig = plt.figure(figsize=(16, 10), dpi=100)
    fig.patch.set_facecolor(BG)

    # ヘッダー
    header_h = 0.17
    ax_head = fig.add_axes([0, 1 - header_h, 1, header_h])
    ax_head.set_facecolor(BG); ax_head.axis("off")
    ax_head.set_xlim(0, 1); ax_head.set_ylim(0, 1)

    ax_head.text(0.035, 0.72, "ヨミテ 5商品  市場ポジション・ダッシュボード",
                 fontsize=24, color=INK, weight="bold", transform=ax_head.transAxes)
    ax_head.text(0.035, 0.44,
                 f"発行日: {date_long(today_dt)}｜観測日: {date_short(obs_dt)}｜Meta(FB/Insta) + YouTube(通常/Shorts) 集計",
                 fontsize=12, color=INK_SUB, transform=ax_head.transAxes)
    ax_head.text(0.035, 0.22,
                 "勝ってるか / 負けてるか が一目で分かるよう、順位と市場内ポジションで可視化",
                 fontsize=10, color=INK_SUB_LIGHT, transform=ax_head.transAxes)
    ax_head.plot([0.02, 0.98], [0.02, 0.02], color=LINE_LIGHT, lw=1.5, transform=ax_head.transAxes)

    # ヘッダー行
    thead_h = 0.04
    thead_y = 1 - header_h - thead_h - 0.005
    ax_th = fig.add_axes([0, thead_y, 1, thead_h])
    ax_th.set_facecolor("#F8FAFC"); ax_th.axis("off")
    ax_th.set_xlim(0, 1); ax_th.set_ylim(0, 1)

    COL = {
        "product": 0.035,
        "rank":    0.39,
        "share":   0.54,
        "vs_top":  0.68,
        "state":   0.84,
    }
    ax_th.text(COL["product"], 0.5, "商品名 / ジャンル",
               fontsize=10.5, color=INK, weight="bold", va="center", transform=ax_th.transAxes)
    ax_th.text(COL["rank"], 0.5, "市場順位",
               fontsize=10.5, color=INK, weight="bold", va="center", ha="center", transform=ax_th.transAxes)
    ax_th.text(COL["share"], 0.5, "シェア%",
               fontsize=10.5, color=INK, weight="bold", va="center", ha="center", transform=ax_th.transAxes)
    ax_th.text(COL["vs_top"], 0.5, "首位との差",
               fontsize=10.5, color=INK, weight="bold", va="center", ha="center", transform=ax_th.transAxes)
    ax_th.text(COL["state"], 0.5, "状態",
               fontsize=10.5, color=INK, weight="bold", va="center", ha="center", transform=ax_th.transAxes)

    ax_th.plot([0.02, 0.98], [0.0, 0.0], color=LINE_LIGHT, lw=1, transform=ax_th.transAxes)

    # 各商品行
    rows_top = thead_y - 0.005
    rows_bottom = 0.11
    row_h = (rows_top - rows_bottom) / n

    # シェア順にソート
    products_sorted = sorted(cfg["products"],
                             key=lambda p: -(history[today_date]["products"].get(PKEY_TO_SLUG.get(p["name"]), {}).get("share_pct", 0)))

    for idx, product in enumerate(products_sorted):
        pkey = product["name"]
        pkey_norm = PKEY_TO_SLUG.get(pkey, pkey.lower())
        color = product["color"]
        display_name = product["display_name"]
        market_label = product["market"].get("genre_label", "")

        p = history[today_date]["products"].get(pkey_norm, {})
        rank = p.get("rank")
        share = p.get("share_pct", 0)
        leaderboard = p.get("leaderboard_top5", [])
        top_share = leaderboard[0]["share_pct"] if leaderboard else share

        r_label, r_color = rank_judgement(rank)
        r_bg = rank_color(rank)

        y_top = rows_top - idx * row_h
        ax = fig.add_axes([0, y_top - row_h, 1, row_h])
        ax.set_facecolor(BG); ax.axis("off")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

        # 左カラーバー
        ax.add_patch(Rectangle((0.02, 0.15), 0.005, 0.7, facecolor=color, transform=ax.transAxes))

        # 商品名
        ax.text(COL["product"], 0.68, display_name,
                fontsize=14, color=INK, weight="bold", va="center", transform=ax.transAxes)
        ax.text(COL["product"], 0.30, shorten(market_label, 48),
                fontsize=9, color=INK_SUB, va="center", transform=ax.transAxes)

        # 順位バッジ
        if rank:
            bx = COL["rank"] - 0.05
            ax.add_patch(FancyBboxPatch((bx, 0.2), 0.10, 0.6,
                                        boxstyle="round,pad=0.02",
                                        facecolor=r_bg, edgecolor="none", alpha=0.95,
                                        transform=ax.transAxes))
            ax.text(bx + 0.05, 0.5, f"{rank}位",
                    fontsize=22, color="white", weight="bold",
                    ha="center", va="center", transform=ax.transAxes)

        # シェア%
        ax.text(COL["share"], 0.5, f"{share:.2f}%",
                fontsize=22, color=color, weight="bold",
                va="center", ha="center", transform=ax.transAxes)

        # 首位との差
        if rank == 1:
            vs_txt, vs_col = "★ 首位", "#C48A00"
        else:
            diff = share - top_share
            vs_txt = f"{diff:+.1f}pt"
            vs_col = "#1F9D55" if diff >= 0 else "#C4362C"
        ax.text(COL["vs_top"], 0.5, vs_txt,
                fontsize=14, color=vs_col, weight="bold",
                va="center", ha="center", transform=ax.transAxes)

        # 状態ラベル
        ax.text(COL["state"], 0.62, r_label,
                fontsize=11, color=r_color, weight="bold",
                va="center", ha="center", transform=ax.transAxes)
        # 補足 (データ信頼度)
        if p.get("data_confidence") == "low":
            ax.text(COL["state"], 0.30, "※ 要検証",
                    fontsize=9, color=INK_SUB, ha="center", va="center",
                    transform=ax.transAxes)

        # 下ボーダー
        ax.plot([0.02, 0.98], [0.02, 0.02], color=LINE_LIGHT, lw=0.7, transform=ax.transAxes)

    # 凡例（最下段）
    ax_fg = fig.add_axes([0, 0, 1, 0.10])
    ax_fg.set_facecolor("#FAFBFC"); ax_fg.axis("off")
    ax_fg.set_xlim(0, 1); ax_fg.set_ylim(0, 1)
    ax_fg.plot([0.02, 0.98], [1.0, 1.0], color=LINE_LIGHT, lw=1.5, transform=ax_fg.transAxes)

    ax_fg.text(0.035, 0.72, "◆ 表の読み方",
               fontsize=11, color=INK, weight="bold", transform=ax_fg.transAxes)
    ax_fg.text(0.035, 0.42,
               "・市場順位: ジャンル内TOP5中の自社ポジション（金=首位 ／ 青=2-3位（勝ち圏） ／ 橙=4位（要注意） ／ 赤=5位（劣勢））",
               fontsize=9.5, color=INK_SUB, transform=ax_fg.transAxes)
    ax_fg.text(0.035, 0.18,
               "・シェア%: ジャンル広告消化額全体（Meta+YouTube）に対する自社の割合 ／ 首位との差: 1位からの開き（ptポイント）",
               fontsize=9.5, color=INK_SUB, transform=ax_fg.transAxes)

    fig.savefig(out_path, facecolor=BG, dpi=110, bbox_inches=None)
    plt.close(fig)
    print(f"✅ {out_path} (summary)")


def main():
    cfg = load_config()
    history = load_history()
    if not history:
        print("❌ history empty"); sys.exit(1)

    today = sorted(history.keys())[-1]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # サマリ
    summary_path = OUT_DIR / f"{today}_voyage_00summary.png"
    try:
        draw_summary(cfg, history, summary_path)
    except Exception as e:
        import traceback; traceback.print_exc()

    # 各商品
    for product in cfg["products"]:
        slug = PKEY_TO_SLUG.get(product["name"], product["name"].lower())
        out = OUT_DIR / f"{today}_voyage_{slug}.png"
        try:
            draw_product_chart(product, history, out)
        except Exception as e:
            import traceback; traceback.print_exc()


if __name__ == "__main__":
    main()
