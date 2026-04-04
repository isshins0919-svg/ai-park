#!/usr/bin/env python3
"""
update_crew_map.py — 一進VOYAGE号クルーマップ自動更新スクリプト

.claude/agents/ と .claude/commands/ の frontmatter を読み込み、
docs/voyage-crew-map.html の以下を自動更新する:
  - STATS (TOTAL CREW / AGENTS / SKILLS)
  - 新入りクルー（HTMLに未登場のファイルを自動検出して追記）

使い方:
  python3 scripts/update_crew_map.py
"""

import os
import re
from pathlib import Path

BASE = Path(__file__).parent.parent
AGENTS_DIR   = BASE / ".claude/agents"
COMMANDS_DIR = BASE / ".claude/commands"
HTML_PATH    = BASE / "docs/voyage-crew-map.html"

# スキップするファイル（特殊用途）
SKIP_FILES = {"pak-sensei.md"}

# commandsのfrontmatterがない場合のフォールバック（ファイル名→表示名）
SKILL_DISPLAY = {
    "amazon-captain": ("🏴‍☠️", "Amazonキャプテン"),
    "amazon-park":    ("📦", "Amazon Park"),
    "anonymize":      ("🛡️", "匿名化"),
    "banner-park":    ("🖼️", "Banner Park"),
    "client-context": ("👤", "Client Context"),
    "coach":          ("🎓", "Coach Park"),
    "concept-park":   ("💡", "Concept Park"),
    "handoff":        ("📋", "ハンドオフ"),
    "kiji-arc":       ("🌊", "記事アーク"),
    "kiji-cko":       ("🧭", "CKOクルー"),
    "kiji-compass":   ("🧭", "記事コンパス"),
    "kiji-cta":       ("🔔", "記事CTA"),
    "kiji-flow":      ("🔄", "記事フロー"),
    "kiji-hook":      ("🎣", "記事フック"),
    "kiji-offer":     ("💎", "記事オファー"),
    "kiji-rewriter":  ("✍️", "記事ライター"),
    "kiji-tester":    ("🧪", "記事テスト"),
    "kiji-trust":     ("⚓", "記事トラスト"),
    "kiji-validator": ("✅", "記事バリデーター"),
    "lp-speed":       ("⚡", "LP Speed"),
    "meeting-prep":   ("📞", "Meeting Prep"),
    "morning":        ("🌅", "Morning Routine"),
    "movie-arc":      ("🎢", "動画アーク"),
    "movie-bridge":   ("🌉", "動画ブリッジ"),
    "movie-cta":      ("📣", "動画CTA"),
    "movie-hook":     ("⚡", "動画フック"),
    "movie-judge":    ("⚖️", "動画ジャッジ"),
    "movie-kantoku":  ("🎬", "動画カントク"),
    "movie-match":    ("🧩", "動画マッチ"),
    "movie-retention":("📉", "動画リテンション"),
    "movie-style":    ("🎨", "動画スタイル"),
    "movie-tempo":    ("🥁", "動画テンポ"),
    "nice-dive":      ("🌊", "Nice Dive"),
    "park-kaizen":    ("🪞", "Park Kaizen"),
    "park-patrol":    ("🔍", "Park Patrol"),
    "proposal-park":  ("📄", "Proposal Park"),
    "research-park":  ("🔬", "Research Park"),
    "secretary-crew": ("📋", "秘書クルー"),
    "shortad-park":   ("📱", "ShortAd Park"),
    "weekly-review":  ("📅", "Weekly Review"),
    "work-mentor":    ("🧑‍💼", "Work Mentor"),
    "youtube-research":("📺", "YouTube Research"),
    "記事LP-park":    ("📝", "記事LP Park"),
}


# ──────────────────────────────────────────
# frontmatter パーサー
# ──────────────────────────────────────────
def parse_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            data[key.strip()] = val.strip()
    return data


# ──────────────────────────────────────────
# descriptionの先頭絵文字を抽出
# ──────────────────────────────────────────
def extract_emoji(text: str) -> str:
    if not text:
        return "🤖"
    for i in range(1, 4):
        c = text[:i]
        if len(c) and ord(c[-1]) > 0x2000:
            return c
    return "🤖"


def short_role(desc: str, emoji: str) -> str:
    """descriptionから短い役割テキストを抽出（20文字以内）"""
    s = desc.lstrip(emoji).strip().lstrip(" ").strip()
    s = re.split(r"[。．—\-｜×]", s)[0].strip()
    return s[:20]


# ──────────────────────────────────────────
# クルー一覧収集
# ──────────────────────────────────────────
def collect_crew():
    agents, skills = [], []

    for f in sorted(AGENTS_DIR.glob("*.md")):
        if f.name in SKIP_FILES:
            continue
        fm = parse_frontmatter(f)
        if not fm.get("name"):
            continue
        desc  = fm.get("description", "")
        emoji = extract_emoji(desc)
        agents.append({
            "file":  f.name,
            "stem":  f.stem,
            "name":  fm["name"],
            "emoji": emoji,
            "role":  short_role(desc, emoji),
            "tier":  "AGENT",
        })

    for f in sorted(COMMANDS_DIR.glob("*.md")):
        if f.name in SKIP_FILES:
            continue
        stem = f.stem
        fm   = parse_frontmatter(f)
        # フォールバックテーブル優先
        if stem in SKILL_DISPLAY:
            emoji, display_name = SKILL_DISPLAY[stem]
            role = ""
        else:
            desc  = fm.get("description", "")
            emoji = extract_emoji(desc)
            display_name = fm.get("name") or stem
            role  = short_role(desc, emoji)

        skills.append({
            "file":  f.name,
            "stem":  stem,
            "name":  display_name,
            "emoji": emoji,
            "role":  role,
            "tier":  "SKILL",
        })

    return agents, skills


# ──────────────────────────────────────────
# HTMLに既登録のファイル名を収集
# ──────────────────────────────────────────
def find_registered_files(html: str) -> set:
    """data-file属性 + HTMLに登場するファイル名(stem)を収集"""
    registered = set(re.findall(r'data-file="([^"]+)"', html))
    return registered


# ──────────────────────────────────────────
# 新入りクルーのHTML生成
# ──────────────────────────────────────────
def build_new_crew_html(new_crew: list) -> str:
    if not new_crew:
        return ""

    cards = ""
    for c in new_crew:
        name  = c["name"][:14]
        role  = c["role"][:20]
        cards += (
            f'          <div class="crew-card" data-file="{c["file"]}">'
            f'<span class="tier">{c["tier"]}</span>'
            f'<div class="icon">{c["emoji"]}</div>'
            f'<div class="name">{name}</div>'
            f'<div class="role">{role}</div>'
            f'</div>\n'
        )

    return f"""
      <div class="deck deck-util" style="border-color: rgba(100,200,100,0.2);">
        <div class="deck-header">
          <span class="deck-icon">🆕</span>
          <span class="deck-name">新入りクルー（自動検出）</span>
          <span class="deck-desc">最新セッションで追加されたクルー</span>
        </div>
        <div class="crew-grid">
{cards}        </div>
      </div>"""


# ──────────────────────────────────────────
# メイン
# ──────────────────────────────────────────
def main():
    html = HTML_PATH.read_text(encoding="utf-8")
    agents, skills = collect_crew()
    all_crew = agents + skills

    total    = len(all_crew)
    n_agents = len(agents)
    n_skills = len(skills)

    print(f"📊 クルー集計: TOTAL={total} / AGENTS={n_agents} / SKILLS={n_skills}")

    # ── 1. STATS 更新 ──────────────────────────────
    def replace_stat(h, sid, val):
        return re.sub(
            rf'(<div class="stat-num" id="{sid}">)\d+(</div>)',
            rf'\g<1>{val}\2', h
        )
    html = replace_stat(html, "stat-total",  total)
    html = replace_stat(html, "stat-agents", n_agents)
    html = replace_stat(html, "stat-skills", n_skills)

    # ── 2. 新入りクルー 更新 ──────────────────────
    registered = find_registered_files(html)
    new_crew   = [c for c in all_crew if c["file"] not in registered]

    if new_crew:
        print(f"🆕 新入りクルー検出: {len(new_crew)}体")
        for c in new_crew:
            print(f"   → {c['name']} ({c['file']})")
    else:
        print("✅ 新入りクルーなし（全員登録済み）")

    new_html = build_new_crew_html(new_crew)
    html = re.sub(
        r"<!-- AUTO:NEW-CREW -->.*?<!-- /AUTO:NEW-CREW -->",
        f"<!-- AUTO:NEW-CREW -->{new_html}\n      <!-- /AUTO:NEW-CREW -->",
        html, flags=re.DOTALL,
    )

    # ── 3. 保存 ──────────────────────────────────
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"✅ 更新完了: {HTML_PATH}")


if __name__ == "__main__":
    main()
