"""
プルーストクリーム2 — 好調台本エンベディング
勝ちDNAとしてベクトル化し all_vectors.json に格納
登録日: 2026-04-24
"""
import subprocess, os, json, time, re
from pathlib import Path
import numpy as np

def _load_env(var):
    if os.environ.get(var):
        return
    for rc in [Path.home() / ".zshrc", Path.home() / ".zshenv"]:
        if not rc.exists():
            continue
        try:
            for line in rc.read_text().splitlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                m = re.match(rf'export\s+{var}=["\']?([^"\'#\s]+)["\']?', line)
                if m:
                    os.environ[var] = m.group(1)
                    return
        except Exception:
            pass

_load_env('GEMINI_API_KEY_1')

from google import genai
client = genai.Client(api_key=os.environ['GEMINI_API_KEY_1'])

def embed(text):
    time.sleep(0.3)
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

slug = 'proust'
script_id = 'cream2_001'
out = f'research-park/output/{slug}'

# ============================================================
# 好調台本データ
# ============================================================

full_script = """【衝撃】ワキガの人がこの季節喜ぶ理由。実はワキガの原因はワキに10億個も潜む菌。この菌が汗と結びつくことでツーンと臭くなる。しかもワキガは立派な病気のため、簡単に克服できない。だから今対策しないと永遠に先延ばししているだけ。そこで、ワキガ手術医と共同開発。本気を出して開発したのがワキガへの徹底防臭が可能な「切らないワキガ対策」。原因菌に注目して殺菌成分を2種類配合することに成功。朝のひと塗りでワキガを徹底防臭。だからワキガに悩む30万人に選ばれてる。そんなクリニック専売品の「切らないワキガ対策」がこの動画から初回97%OFFの210円でGETできる。少しでも多くの人に使って欲しいから、送料無料お届け回数の約束もナシ！ワキガ悩み卒業したい人は今すぐ詳細をクリック"""

sections = [
    {
        "section": "hook",
        "text": "【衝撃】ワキガの人がこの季節喜ぶ理由",
        "appeal_angle": "季節×逆説（喜ぶ理由）で認知不協和を起こすフック",
        "seconds": "0-3s",
    },
    {
        "section": "problem",
        "text": "実はワキガの原因はワキに10億個も潜む菌。この菌が汗と結びつくことでツーンと臭くなる",
        "appeal_angle": "数字（10億個）×原因特定で納得感を作る問題提起",
        "seconds": "3-8s",
    },
    {
        "section": "urgency",
        "text": "しかもワキガは立派な病気のため、簡単に克服できない。だから今対策しないと永遠に先延ばししているだけ",
        "appeal_angle": "病気フレームで自責感を解除、先延ばしの罪悪感で緊急性醸成",
        "seconds": "8-14s",
    },
    {
        "section": "solution_origin",
        "text": "そこで、ワキガ手術医と共同開発。本気を出して開発したのがワキガへの徹底防臭が可能な「切らないワキガ対策」",
        "appeal_angle": "専門家権威（ワキガ手術医）×共同開発の真剣さ",
        "seconds": "14-20s",
    },
    {
        "section": "mechanism",
        "text": "原因菌に注目して殺菌成分を2種類配合することに成功。朝のひと塗りでワキガを徹底防臭",
        "appeal_angle": "成分根拠（殺菌成分2種類）×使い方の簡便性（朝ひと塗り）",
        "seconds": "20-26s",
    },
    {
        "section": "social_proof",
        "text": "だからワキガに悩む30万人に選ばれてる",
        "appeal_angle": "量の社会的証明（30万人）",
        "seconds": "26-29s",
    },
    {
        "section": "offer",
        "text": "そんなクリニック専売品の「切らないワキガ対策」がこの動画から初回97%OFFの210円でGETできる",
        "appeal_angle": "クリニック専売品フレーム×割引率97%×絶対額210円の三重訴求",
        "seconds": "29-36s",
    },
    {
        "section": "risk_reversal",
        "text": "少しでも多くの人に使って欲しいから、送料無料お届け回数の約束もナシ！",
        "appeal_angle": "定期縛りストレスの先回り解除（お届け回数の約束ナシ）",
        "seconds": "36-41s",
    },
    {
        "section": "cta",
        "text": "ワキガ悩み卒業したい人は今すぐ詳細をクリック",
        "appeal_angle": "感情ゴール（卒業したい）×視覚誘導（↓矢印）",
        "seconds": "41-45s",
    },
]

# DNA特徴（勝ちパターンの構造）
dna_features = [
    {"feature": "hook_pattern", "text": "季節文脈×逆説フック: 本来ネガティブな状態を「喜ぶ」と反転させる認知不協和フック"},
    {"feature": "problem_pattern", "text": "物理量の数字で原因特定: 10億個の菌のような具体数で抽象悩みを物質化"},
    {"feature": "urgency_pattern", "text": "病気フレーム×先延ばし罪悪感: 自己責任を解除しつつ緊急性を醸成"},
    {"feature": "authority_pattern", "text": "専門医共同開発: ワキガ手術医という悩みの頂点専門家との共同開発"},
    {"feature": "mechanism_pattern", "text": "成分数で根拠提示: 殺菌成分2種類のような数値化された機能根拠"},
    {"feature": "social_proof_pattern", "text": "量の権威: 30万人選ばれている規模訴求"},
    {"feature": "offer_pattern", "text": "三重訴求オファー: クリニック専売品×割引率97%×絶対額210円"},
    {"feature": "risk_reversal_pattern", "text": "定期縛り解除の先回り: お届け回数の約束ナシで購入抵抗を下げる"},
    {"feature": "cta_pattern", "text": "感情ゴール×視覚誘導CTA: 卒業したい気持ち×矢印クリック誘導"},
]

print(f"=== プルーストクリーム2 好調台本エンベディング ===")
print(f"  台本ID: {script_id}")
print(f"  セクション数: {len(sections)}")
print(f"  DNA特徴: {len(dna_features)}")

# ============================================================
# ベクトル化
# ============================================================

print(f"\n  全文ベクトル化中...")
full_vector = embed(full_script)
print(f"    ✅ full_script (dim={len(full_vector)})")

print(f"\n  セクション別ベクトル化中...")
for s in sections:
    s['vector'] = embed(s['text'])
    s['category'] = 'winner_script_section'
    s['script_id'] = script_id
    s['brand'] = 'proust_cream2'
    print(f"    ✅ {s['section']:18}: {s['text'][:30]}...")

print(f"\n  DNA特徴ベクトル化中...")
for d in dna_features:
    d['vector'] = embed(d['text'])
    d['category'] = 'winner_dna_feature'
    d['script_id'] = script_id
    d['brand'] = 'proust_cream2'
    print(f"    ✅ {d['feature']}")

# 全文ベクトル（全体代表）
full_entry = {
    "script_id": script_id,
    "brand": "proust_cream2",
    "category": "winner_script_full",
    "text": full_script,
    "vector": full_vector,
    "status": "winner",
    "registered_at": "2026-04-24",
    "ad_format": "short_video",
    "section_count": len(sections),
}

# ============================================================
# all_vectors.json に保存
# ============================================================

vectors_path = f'{out}/all_vectors.json'
existing = []
if os.path.exists(vectors_path):
    existing = json.load(open(vectors_path))
    # 同じscript_idの古いエントリを除去（再実行対応）
    existing = [v for v in existing if v.get('script_id') != script_id]

all_new = [full_entry] + sections + dna_features
merged = existing + all_new

with open(vectors_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, default=lambda x: x if not hasattr(x,'tolist') else x.tolist())

print(f"\n  ✅ all_vectors.json 保存完了（合計{len(merged)}件 / 今回{len(all_new)}件追加）")

# ============================================================
# セクション間コサイン類似度マトリクス（構造診断）
# ============================================================

print(f"\n=== セクション間類似度マトリクス ===")
print(f"  (類似度が全部高い = セクション分化が甘い / 0.5付近 = 適度な多様性)")
print()

headers = [s['section'][:8] for s in sections]
print("  " + " ".join([f"{h:>10}" for h in ["section"] + headers]))
for i, si in enumerate(sections):
    row = [f"{si['section'][:8]:>10}"]
    for j, sj in enumerate(sections):
        if i == j:
            row.append(f"{'--':>10}")
        else:
            sim = cosine_sim(si['vector'], sj['vector'])
            row.append(f"{sim:>10.3f}")
    print("  " + " ".join(row))

# ============================================================
# 全文 vs セクション類似度
# ============================================================

print(f"\n=== 全文 × 各セクション 類似度（全体代表性）===")
for s in sections:
    sim = cosine_sim(full_vector, s['vector'])
    marker = "★" if sim >= 0.75 else ("✓" if sim >= 0.60 else " ")
    print(f"  {marker} {s['section']:18}: {sim:.3f}  {s['text'][:30]}...")

print(f"\n=== 完了 ===")
print(f"  登録場所: {vectors_path}")
print(f"  台本詳細: {out}/winners/{script_id}.md")
print(f"\n  使い方:")
print(f"    新規台本のベクトル vs このベクトルで winner_proximity 計算")
print(f"    類似度 0.55〜0.75 = 勝ちDNA継承しつつ被らない最適ゾーン")
