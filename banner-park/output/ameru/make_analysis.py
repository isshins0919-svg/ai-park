#!/usr/bin/env python3
"""Phase 3.3: クラスタごと勝ちパターン抽出 → reference_analysis.md 生成"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent
VIS_JSON = ROOT / "reference" / "vision_elements.json"
OUT_MD = ROOT / "reference_analysis.md"

refs = json.loads(VIS_JSON.read_text())

# ツール関数
def tone_dist(items):
    return Counter(r['vision']['emotional_tone'] for r in items if r.get('vision'))

def style_dist(items):
    return Counter(r['vision']['visual_style'] for r in items if r.get('vision'))

def palette_list(items):
    pal = []
    for r in items:
        if r.get('vision'):
            pal.extend(r['vision']['palette'])
    return Counter(pal)

# マルチモーダルクラスタでグルーピング
clusters = {}
for r in refs:
    c = r.get('cluster_multi', 0)
    clusters.setdefault(c, []).append(r)

lines = []
lines.append("# ameru バナーPOC: リファレンス構成分析C レポート\n")
lines.append(f"**対象**: 10本 (DPro実績ありバナー)  ")
lines.append(f"**分析手法**: embedding-2-preview マルチモーダル × 階層クラスタリング(3) × Gemini Vision要素分解  ")
lines.append(f"**目的**: ameru用バナー10本生成時の勝ちパターン参照マップ\n")

# エグゼクティブサマリー
lines.append("---\n")
lines.append("## 🎯 エグゼクティブサマリー\n")
lines.append("### 全10本の感情トーン分布")
all_tones = tone_dist(refs)
for t, n in all_tones.most_common():
    lines.append(f"- **{t}**: {n}件")
lines.append("\n### 全10本のビジュアルスタイル分布")
all_styles = style_dist(refs)
for s, n in all_styles.most_common():
    lines.append(f"- {s}: {n}件")

# ameru への転用キー示唆
lines.append("\n### ameru への転用キー示唆")
lines.append("""
- **感情トーン**: ameru は売る前の第一想起では「可愛らしさ × 発見のワクワク」が刺さる。
  **癒し系（購入後価値訴求）をバナーFVに持ち込むのはNG**。癒しはLP中〜後段で効かせる。
- **ビジュアル型**: 清原推しぬい（IP×キャラ3体×公式バッジ×淡いドット）が最強リファ。ameru KV（5キャラ集合 + 公式バッジ）と完全同型。
- **コピー型**: じぶんぐるみ「334億通り」のような**数値差別化** × moin「泣きそうになる」のような**SNS口語コピー**の2軸。
- **禁忌**: あつお型（キャラ自身の疲労感訴求）は転用しない。可愛らしさとネガが混線する。
""")

# クラスタ別詳細
lines.append("---\n")
lines.append("## 📊 マルチモーダル・クラスタ詳細\n")

CLUSTER_LABELS = {
    1: "クラスタA: オーダーメイド×差別化訴求（3件）",
    2: "クラスタB: キャラクター×感情訴求（6件）",
    3: "クラスタC: シンプルパッケージ単品（1件）",
}

for c in sorted(clusters.keys()):
    members = clusters[c]
    label = CLUSTER_LABELS.get(c, f"クラスタ{c}")
    lines.append(f"### {label}\n")
    lines.append(f"**構成**: {len(members)}件")
    # 感情トーン
    tones = tone_dist(members)
    lines.append(f"\n**感情トーン分布**: {', '.join(f'{t}×{n}' for t,n in tones.most_common())}")
    # ビジュアルスタイル
    styles = style_dist(members)
    lines.append(f"**ビジュアルスタイル**: {', '.join(f'{s}×{n}' for s,n in styles.most_common())}")
    # 主要配色 TOP5
    pal = palette_list(members)
    lines.append(f"**主要配色 TOP5**: {', '.join(f'{c_}×{n}' for c_,n in pal.most_common(5))}")

    # 訴求軸を並べる
    lines.append("\n**訴求軸一覧**:")
    for m in members:
        v = m.get('vision', {}) or {}
        lines.append(f"- [{m['src']}] {v.get('appeal_axis', '?')}")

    # 勝ちパターン抽出
    lines.append("\n**このクラスタの勝ちパターン（共通要素）**:")
    common = []
    if c == 1:
        common = [
            "一点の商品（ぬいぐるみ/セール商品）を大きく主役化",
            "コピーは**数値差別化**（「334億通り」「一生もの」「-30%」）または**人物共演**",
            "背景は柔らかいトーン（アイボリー/ベージュ/白）",
            "訴求軸は『自分だけの◯◯』『一生もの』等の**所有満足**",
        ]
    elif c == 2:
        common = [
            "**キャラクターや製品が複数**画面に登場（清原3体/moin複数カット/おもぬい複数ぬい）",
            "感情トーンは**癒し/可愛らしさ**が主軸",
            "SNS口語コピー（「泣きそうになる」「エモすぎて」等）で感情温度を上げる",
            "配色は**パステル/淡色**寄り",
            "訴求軸は**体験と感情**（癒される・エモい・推し）",
        ]
    elif c == 3:
        common = [
            "商品単体のパッケージ写真1枚で完結",
            "白背景・商品名＋商品特徴の最小情報",
            "EC商品リスト向け（SmartNews等のリスティング媒体）",
        ]
    for cc in common:
        lines.append(f"- {cc}")

    lines.append("")

# 個別バナー要素テーブル
lines.append("---\n")
lines.append("## 📋 個別バナー要素テーブル\n")
lines.append("| # | src | main_copy | tone | visual_style | appeal_axis |")
lines.append("|---|---|---|---|---|---|")
for i, r in enumerate(refs, 1):
    v = r.get('vision', {}) or {}
    mc = (v.get('main_copy','') or '')[:40].replace('|','/')
    aa = (v.get('appeal_axis','') or '')[:40].replace('|','/')
    lines.append(f"| {i} | {r['src']} | {mc} | {v.get('emotional_tone','')} | {v.get('visual_style','')} | {aa} |")

# ameru用バナー10本生成への提言
lines.append("\n---\n")
lines.append("## 🎨 ameru用バナー10本 生成方針（Phase 4 への引き継ぎ）\n")
lines.append("### 推奨クラスタ割当")
lines.append("""
| 型 | 本数 | 参考クラスタ | ameru コピー例（暫定） |
|---|---|---|---|
| **IP×キャラ集合型** (清原推しぬい系) | 3本 | クラスタB | 「らぶいーず、ぜんぶ、自分の手で。」/「公式5キャラ、自分で編める。」/「#らぶいーず を編む」 |
| **オーダーメイド差別化型** (じぶんぐるみ系) | 2本 | クラスタA | 「世界でひとつの、あなたのらぶいーず」/「編み始め完成済み、だから必ず完成する」 |
| **SNSエモコピー型** (moin系) | 2本 | クラスタB | 「え、らぶいーずって自分で編めるの？」/「8時間で、推しが手元に。」 |
| **実写癒し・完成型** (おもぬい風) | 2本 | クラスタB | 完成した5キャラを並べて「できた。」 |
| **キットパッケージ単品型** (ユザワヤ風) | 1本 | クラスタC | 水色パッケージ単品＋「はじめの1体、¥1,980」|

### 禁忌クロスチェック（Phase 4 ゲート）
- [ ] 「らぶいーず」は完全ひらがな。英語表記NG。
- [ ] 公式5キャラ名: すもっぴ/ぴょんちー/にゃぽ/うるる/ぱおぱお 以外使用NG。
- [ ] 誕生月訴求NG。
- [ ] 商品ラインナップは5回定期便 + 単品のみ。カップルセット等NG。
- [ ] 時間依存コピーNG（「本日より」等）。数量限定（「限定300セット」）はOK。
- [ ] 「買う」系ネガアンカーNG（「買うより編む」等）。
- [ ] 助数詞「1体」で統一（「1匹」「1個」NG）。
- [ ] 売る前に「失敗したら悲しい」「挫折不安」等のネガ前提を先出ししない。**発見 → 欲しい** の順。

### 感情トーン戦略（N1修正を反映）
バナーFV = **「可愛らしさ × 発見のワクワク」**を最前面に。
癒し・フィエロ（達成感）は**LPの中〜後段**の役割であって、バナーでは前面に出さない。
""")

lines.append("\n---\n")
lines.append(f"## 🔗 関連ファイル\n")
lines.append("- `strategy.json` — ameru戦略定義")
lines.append("- `reference/final_10.json` — 10本のメタデータ")
lines.append("- `reference/all_vectors.json` — embedding-2 ベクトル (image/text/multi × 10)")
lines.append("- `reference/clusters.json` — クラスタ割当結果")
lines.append("- `reference/vision_elements.json` — Vision要素分解結果")
lines.append("- `reference/refs/*.webp|.jpg` — 参考画像10枚\n")

OUT_MD.write_text("\n".join(lines))
print(f"saved: {OUT_MD}")
print(f"lines: {len(lines)}")
