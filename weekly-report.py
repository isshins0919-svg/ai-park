#!/usr/bin/env python3
"""
週次 Claude Code 使用レポート
使い方: python3 weekly-report.py [YYYY-MM-DD] [--html]
"""
import subprocess
import sys
import re
import os
from datetime import date, timedelta

HTML_MODE = "--html" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]

# ---- 設定 ----
END_DATE   = date.fromisoformat(args[0]) if args else date.today()
START_DATE = END_DATE - timedelta(days=6)
PREV_END   = END_DATE - timedelta(days=7)
PREV_START = END_DATE - timedelta(days=13)

# ---- 色 ----
BOLD="\033[1m"; CYAN="\033[0;36m"; GREEN="\033[0;32m"
YELLOW="\033[0;33m"; RED="\033[0;31m"; DIM="\033[2m"; RESET="\033[0m"

# ---- ヘルパー ----
def git(since: date, until: date, *args):
    cmd = ["git","log",
           f"--since={since}T00:00:00",
           f"--until={until}T23:59:59",
           *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

def new_files(s, u, pattern):
    out = git(s, u, "--diff-filter=A", "--name-only", "--format=")
    return sum(1 for l in out.splitlines() if re.search(pattern, l, re.I))

def match_commits(s, u, pattern):
    out = git(s, u, "--oneline")
    return sum(1 for l in out.splitlines() if re.search(pattern, l, re.I))

def all_commits(s, u):
    out = git(s, u, "--oneline")
    return len([l for l in out.splitlines() if l.strip()])

def feat_commits(s, u):
    return match_commits(s, u, r"feat")

def delta(curr, prev):
    if prev == 0: return "new", GREEN
    d = curr - prev
    if d > 0:   return f"+{d}", GREEN
    if d < 0:   return str(d), RED
    return "±0", DIM

def row(icon, label, curr, prev):
    d, col = delta(curr, prev)
    print(f"  {icon}  {label:<10}  {BOLD}{curr:>3}{RESET}   {col}{d}{RESET} vs 先週")

def bar_str(cnt, max_cnt, width=22):
    if max_cnt == 0: return "·"
    n = round(cnt / max_cnt * width)
    return "█" * n if n > 0 else "·"

# ---- 今週 ----
IMG_PATTERN = r"\.(png|jpg|jpeg|webp|gif)$"
VID_PATTERN = r"\.(mp4|mov|webm)$"
REP_PATTERN = r"\.(html|pdf)$"
MOR_PATTERN = r"morning|モーニング"
REV_PATTERN = r"weekly.review|週次|振り返り"
RES_PATTERN = r"research|リサーチ|strategy"

tw = {
    "tot": all_commits(START_DATE, END_DATE),
    "ft":  feat_commits(START_DATE, END_DATE),
    "img": new_files(START_DATE, END_DATE, IMG_PATTERN),
    "vid": new_files(START_DATE, END_DATE, VID_PATTERN),
    "rep": new_files(START_DATE, END_DATE, REP_PATTERN),
    "mor": match_commits(START_DATE, END_DATE, MOR_PATTERN),
    "rev": match_commits(START_DATE, END_DATE, REV_PATTERN),
    "res": match_commits(START_DATE, END_DATE, RES_PATTERN),
}

pw = {
    "tot": all_commits(PREV_START, PREV_END),
    "ft":  feat_commits(PREV_START, PREV_END),
    "img": new_files(PREV_START, PREV_END, IMG_PATTERN),
    "vid": new_files(PREV_START, PREV_END, VID_PATTERN),
    "rep": new_files(PREV_START, PREV_END, REP_PATTERN),
    "mor": match_commits(PREV_START, PREV_END, MOR_PATTERN),
    "rev": match_commits(PREV_START, PREV_END, REV_PATTERN),
    "res": match_commits(PREV_START, PREV_END, RES_PATTERN),
}

# ---- 日別 ----
days = []
for i in range(7):
    d = START_DATE + timedelta(days=i)
    days.append((d, all_commits(d, d)))

max_cnt = max(c for _, c in days) if days else 1

# ---- 表示 ----
print()
print(f"{BOLD}╔══════════════════════════════════════════════╗{RESET}")
print(f"{BOLD}║   📊  週次 Claude Code レポート              ║{RESET}")
print(f"{BOLD}║   {CYAN}{START_DATE} 〜 {END_DATE}{RESET}{BOLD}              ║{RESET}")
print(f"{BOLD}╚══════════════════════════════════════════════╝{RESET}")

print()
print(f"{BOLD}▌ 成果物{RESET}")
row("🖼 ", "画像",      tw["img"], pw["img"])
row("🎬", "動画",      tw["vid"], pw["vid"])
row("📄", "レポート",  tw["rep"], pw["rep"])

print()
print(f"{BOLD}▌ アクティビティ{RESET}")
row("📦", "総コミット",  tw["tot"], pw["tot"])
row("✨", "feat件数",    tw["ft"],  pw["ft"])
row("🔍", "リサーチ",    tw["res"], pw["res"])

print()
print(f"{BOLD}▌ 習慣・振り返り{RESET}")
row("🌅", "Morning",     tw["mor"], pw["mor"])
row("🔄", "週次レビュー", tw["rev"], pw["rev"])

print()
print(f"{BOLD}▌ 日別アクティビティ{RESET}")
DAYS_JP = ["月","火","水","木","金","土","日"]
for d, cnt in days:
    dow = DAYS_JP[d.weekday()]
    label = f"{d.strftime('%m/%d')} ({dow})"
    b = bar_str(cnt, max_cnt)
    if cnt == max_cnt and max_cnt > 0:
        print(f"  {YELLOW}{label:<11}{RESET}  {YELLOW}{b:<22}{RESET}  {BOLD}{cnt:>2}件{RESET}")
    else:
        print(f"  {DIM}{label:<11}{RESET}  {CYAN}{b:<22}{RESET}  {cnt:>2}件")

print()
print(f"{DIM}先週: {PREV_START} 〜 {PREV_END}{RESET}")
print()

# ---- HTML出力 ----
if HTML_MODE:
    DAYS_JP2 = ["月","火","水","木","金","土","日"]

    def d_html(curr, prev):
        if prev == 0: return '<span class="new">new</span>'
        d = curr - prev
        if d > 0: return f'<span class="up">+{d}</span>'
        if d < 0: return f'<span class="down">{d}</span>'
        return '<span class="flat">±0</span>'

    def bar_html(cnt, max_cnt, width=120):
        if max_cnt == 0: return 0
        return round(cnt / max_cnt * width)

    rows_output = ""
    items = [
        ("🖼", "画像", tw["img"], pw["img"]),
        ("🎬", "動画", tw["vid"], pw["vid"]),
        ("📄", "レポート", tw["rep"], pw["rep"]),
        ("📦", "総コミット", tw["tot"], pw["tot"]),
        ("✨", "feat件数", tw["ft"], pw["ft"]),
        ("🔍", "リサーチ", tw["res"], pw["res"]),
        ("🌅", "Morning", tw["mor"], pw["mor"]),
        ("🔄", "週次レビュー", tw["rev"], pw["rev"]),
    ]
    sections = [
        ("成果物", items[:3]),
        ("アクティビティ", items[3:6]),
        ("習慣・振り返り", items[6:]),
    ]

    table_html = ""
    for sec_title, sec_items in sections:
        table_html += f'<tr><td colspan="4" class="section-head">{sec_title}</td></tr>\n'
        for icon, label, curr, prev in sec_items:
            table_html += f"""<tr>
  <td class="icon">{icon}</td>
  <td class="label">{label}</td>
  <td class="value">{curr}</td>
  <td class="delta">{d_html(curr, prev)} vs 先週</td>
</tr>\n"""

    max_bar = max(c for _, c in days) if days else 1
    bar_html_rows = ""
    for d, cnt in days:
        dow = DAYS_JP2[d.weekday()]
        label = f"{d.strftime('%m/%d')} ({dow})"
        w = bar_html(cnt, max_bar)
        is_best = cnt == max_bar and max_bar > 0
        cls = "best" if is_best else ""
        bar_html_rows += f"""<tr class="{cls}">
  <td class="day-label">{label}</td>
  <td class="bar-cell"><div class="bar" style="width:{w}px"></div></td>
  <td class="day-count">{cnt}件</td>
</tr>\n"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>週次 Claude Code レポート {START_DATE} 〜 {END_DATE}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, "Hiragino Sans", sans-serif; background: #0f1117; color: #e2e8f0; padding: 32px; }}
  h1 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
  .period {{ color: #64748b; font-size: 13px; margin-bottom: 32px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  .card {{ background: #1e2130; border-radius: 12px; padding: 20px; }}
  .card h2 {{ font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 14px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  .section-head {{ font-size: 11px; color: #475569; text-transform: uppercase; letter-spacing: .1em; padding: 14px 0 6px; }}
  td {{ padding: 7px 4px; vertical-align: middle; }}
  .icon {{ width: 28px; font-size: 16px; }}
  .label {{ color: #94a3b8; font-size: 14px; width: 110px; }}
  .value {{ font-size: 22px; font-weight: 700; text-align: right; width: 50px; color: #f1f5f9; }}
  .delta {{ font-size: 12px; padding-left: 10px; color: #64748b; white-space: nowrap; }}
  .up   {{ color: #34d399; font-weight: 600; }}
  .down {{ color: #f87171; font-weight: 600; }}
  .new  {{ color: #60a5fa; font-weight: 600; }}
  .flat {{ color: #64748b; }}
  .bar-table {{ width: 100%; border-collapse: collapse; }}
  .day-label {{ font-size: 13px; color: #94a3b8; width: 90px; padding: 5px 0; }}
  .bar-cell {{ padding: 5px 8px; }}
  .bar {{ height: 16px; background: #3b82f6; border-radius: 4px; min-width: 3px; transition: width .3s; }}
  .best .bar {{ background: #f59e0b; }}
  .best .day-label, .best .day-count {{ color: #f59e0b; font-weight: 700; }}
  .day-count {{ font-size: 13px; color: #64748b; white-space: nowrap; text-align: right; width: 40px; }}
  .prev-note {{ font-size: 12px; color: #334155; margin-top: 16px; }}
</style>
</head>
<body>
<h1>📊 週次 Claude Code レポート</h1>
<p class="period">{START_DATE} 〜 {END_DATE}</p>

<div class="grid">
  <div class="card">
    <h2>成果物 &amp; アクティビティ</h2>
    <table>{table_html}</table>
  </div>
  <div class="card">
    <h2>日別アクティビティ</h2>
    <table class="bar-table">{bar_html_rows}</table>
  </div>
</div>

<p class="prev-note">先週比較期間: {PREV_START} 〜 {PREV_END}</p>
</body>
</html>"""

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"reports/weekly-report-{END_DATE}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML保存 → {out_path}")
    subprocess.run(["open", out_path])
