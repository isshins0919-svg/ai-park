#!/usr/bin/env python3
"""ameru LP 2系統並列生成：
- E版（ハイブリッド）: ameru世界観 + DR要素埋め込み
- D版（DR全開）: 誘目色・太極太・緊迫感・DR骨格フル
出力: screens_E/01-10.png / screens_D/01-10.png
"""
import os, json, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)
MODEL = "nano-banana-pro-preview"

ROOT = Path(__file__).parent
CORPUS_AMERU = ROOT / "corpus"
CORPUS_DR = ROOT / "corpus" / "dr"
OUT_E = ROOT / "screens_E"; OUT_E.mkdir(exist_ok=True)
OUT_D = ROOT / "screens_D"; OUT_D.mkdir(exist_ok=True)

MATCH_AMERU = json.loads((ROOT / "matches_v2.json").read_text())    # ameru world refs
MATCH_DR    = json.loads((ROOT / "matches_dr.json").read_text())    # DR refs

# ----- 共通のameru商品情報 -----
PRODUCT_BASE = """ameru × らぶいーず® 公式あみぐるみキット（D2Cサブスク）
  通常価格: ¥4,200 → 初回 ¥1,980（53%OFF）
  5回総額: ¥18,780 ／ いつでも解約OK ／ 送料込み ／ 返金保証 ／ 限定300セット
  公式5キャラ: すもっぴ・ぴょんちー・にゃぽ・うるる・ぱおぱお
  差別化: 編み始め完成済みで届く（挫折ゼロ設計）
  ターゲット: らぶいーず®を集めている20-30代女性コレクター
  ブランドルール: 英語「Love is...」等は絶対NG、ひらがな「らぶいーず®」固定
"""

# ----- E版：ハイブリッド（世界観保ちつつDR要素追加） -----
STYLE_E = f"""Create a vertical 9:16 smartphone direct-response LP section for "ameru".
{PRODUCT_BASE}
STYLE (hybrid — ameru world × DR elements):
- Base palette: dusty sky-blue #BCD8E8, ivory #F7F1E6, pink-beige #F0D8D0, gold #C9A36A
- BUT add DR accent color: soft red #E25C4A (for price/%OFF/urgency badges) — use sparingly
- Photorealistic premium but with DR-LP energy (bold numbers, badges, arrows)
- Typography: 丸ゴシック bold + 数字は極太sans-serif・赤/金ハイライト可
- DR elements to incorporate: 価格アンカー (¥4,200→¥1,980), %OFF表示, 限定300セット, 返金保証, 縛りなし
- Overall feeling: "品の良いDR" — FUJIMIサプリLPやキミエ・ユリイロを参考に、ameruのくすみトーンで翻訳
- Include visible Japanese text baked into the image (headlines, badges, price table, CTA button)
USE THE PROVIDED REFERENCE IMAGES as composition/element guides, but RECOLOR to ameru's palette.
"""

# ----- D版：DR全開（世界観一旦置いて誘目色・太極太・緊迫感フル） -----
STYLE_D = f"""Create a vertical 9:16 smartphone direct-response LP section for "ameru".
{PRODUCT_BASE}
STYLE (full DR — 勝ちDR-LP直輸入):
- HIGH-CONTRAST palette: white + black + strong red #E25C4A + yellow #FFD93D + sky-blue accent
- Bold DR typography: 超極太ゴシック / huge %OFF numbers / red boxes with white text / yellow highlights
- Photorealistic but with AGGRESSIVE DR visual language
- DR MUST-HAVES baked in:
  * Big price comparison: ¥4,200 (striked) → ¥1,980 (huge red)
  * Big %OFF badge (「53%OFF」or「初回特別価格」in red circle)
  * Urgency elements: 「限定300セット」「本日締切間近」等は避けて「数量限定」「初回特別」でOK
  * Trust stamps: 「返金保証」「いつでも解約OK」「送料無料」のシールベタ貼り
  * User voice stamps (実名・年齢付きの顔写真風): 「32歳 / ◯◯さん」スタイル
  * Red CTA button with white text, always huge
- Reference style: reginaclinic.jp / laric_scalp / kimie_placenta / meimoku / yuriiro LPs
- Include all Japanese text baked into image
- ameru's brand "らぶいーず®" hiragana still strict. Official characters allowed but NOT the focus — price/proof/offer IS the focus.
USE THE PROVIDED REFERENCE IMAGES as the visual language bible. Match their DR aesthetic.
"""

# 10スクリーン（DR骨格）
SECTION_MAP = {
    "01.png": ("01_FV",
     "FV: 最強オファー訴求FV. Above the fold で「53%OFF」「¥1,980」「限定300セット」を絶対に見せる。すもっぴ水色クマあみぐるみ+パッケージ+金リボン。ヘッドライン『らぶいーず、ぜんぶ、自分の手で。』『はじめての1体 ¥1,980(53%OFF)』。CTAボタン『今すぐはじめる ▶』を画面内に。"),
    "02.png": ("02_empathy",
     "共感セクション: 「こんなお悩み、ありませんか？」見出し＋ペイン3〜4個の箇条書き（チェック風アイコン）：『らぶいーず全部集めたいけど高い』『手作りしたいけど編み物は難しそう』『初心者キットは可愛くない』『途中で挫折したらショック』。背景アイボリー。"),
    "03.png": ("03_solution",
     "解決セクション: 「ameruがぜんぶ解決します」見出し＋3つのこだわり。①『編み始め、完成済み』②『公式らぶいーず®コラボ』③『動画教材つき・LINEでサポート』。各こだわりにアイコンと短い解説。"),
    "04.png": ("04_proof_number",
     "数値証拠セクション: 大きな数字を並べる。『満足度 98.2%』『完成率 94%』『累計すもっぴ編み手 1,500名』的なデータ（仮想値でOK、※印で米国Wooblesベースの仮定値と注記）。グラフ・数字強調。"),
    "05.png": ("05_proof_voice",
     "ユーザーボイスセクション: 実名風ユーザー3人の顔写真＋年齢＋コメント。『田中さとみ/34歳/初めてだけど完成しました！』『佐藤あかり/29歳/すもっぴの次はぴょんちーも欲しい』『鈴木みさき/38歳/娘と一緒に楽しめました』。★5レビュー風。"),
    "06.png": ("06_proof_media",
     "メディア・権威セクション: 掲載メディアロゴ（日本テレビ公式コラボ＋雑誌・ウェブメディア掲載を示唆）。『日本テレビ公式 らぶいーず® × ameru』の金ロゴ＋他3-4メディアロゴ（架空でOK、シルエット程度）。"),
    "07.png": ("07_offer_anchor",
     "オファー価格アンカーセクション: 通常価格¥4,200と初回¥1,980を大きく並べて『53%OFF』を強調。5回分の内訳。2ヶ月に1体ずつお届け。特典リスト（動画教材つき、LINEサポート、送料無料、初回キット無料同梱）。"),
    "08.png": ("08_guarantee",
     "返金・安心保証セクション: 『30日間返金保証』『いつでも解約OK（縛りなし）』『送料込み』『コンビニ後払いOK』の4つの安心要素を大きなシール/バッジ形式で。"),
    "09.png": ("09_faq",
     "よくある質問(FAQ)セクション: Q&A形式4つ。Q1『本当に初心者でも編めますか？』Q2『途中で解約できますか？』Q3『いつ届きますか？』Q4『らぶいーず®公式ですか？』。それぞれに短い回答。"),
    "10.png": ("10_cta",
     "最終CTA: 『今すぐ、はじめての1体を編む』大きな赤（D版）or水色（E版）のCTAボタン。ボタン内『¥1,980で はじめてみる（53%OFF）』。ボタン下にリアシュアランス『30日返金保証／いつでも解約OK／送料込み』。箱画像＋手で開ける瞬間。"),
}

def gen(out_path: Path, style: str, section_detail: str, refs: list[Path]):
    if out_path.exists() and out_path.stat().st_size > 30000:
        print(f"  [skip] {out_path.name}"); return
    parts = [types.Part(text=style + "\n\nSECTION DETAIL:\n" + section_detail)]
    for rp in refs:
        if not rp.exists(): continue
        ext = rp.suffix.lower().lstrip(".")
        mime = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp","gif":"image/gif"}.get(ext,"image/png")
        parts.append(types.Part(inline_data=types.Blob(mime_type=mime, data=rp.read_bytes())))
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=[types.Content(parts=parts, role="user")],
        )
        for cand in resp.candidates:
            for part in cand.content.parts:
                if part.inline_data and part.inline_data.data:
                    out_path.write_bytes(part.inline_data.data)
                    print(f"  ✅ {out_path.name} {len(part.inline_data.data)//1024}KB")
                    return
        print(f"  ❌ no image for {out_path.name}")
    except Exception as e:
        print(f"  ❌ {out_path.name}: {type(e).__name__}: {str(e)[:200]}")

def build_refs_E(section_key: str) -> list[Path]:
    """E版: ameru世界観ref 2枚 + DR要素ref 2枚"""
    # map DR-section key to legacy ameru-matches_v2 keys
    ameru_map = {
        "01_FV":"01_FV","02_empathy":"08_life","03_solution":"04_only1",
        "04_proof_number":"04_only1","05_proof_voice":"08_life","06_proof_media":"01_FV",
        "07_offer_anchor":"09_offer","08_guarantee":"09_offer","09_faq":"05_kit",
        "10_cta":"10_cta",
    }
    ameru_refs = [CORPUS_AMERU / m["file"] for m in MATCH_AMERU.get(ameru_map[section_key], [])[:2]]
    dr_refs = [CORPUS_DR / m["file"] for m in MATCH_DR.get(section_key, [])[:2]]
    return [p for p in (ameru_refs + dr_refs) if p.exists()]

def build_refs_D(section_key: str) -> list[Path]:
    """D版: DR-LP ref 4枚 + ameru world 1枚だけ（参考程度）"""
    dr_refs = [CORPUS_DR / m["file"] for m in MATCH_DR.get(section_key, [])[:4]]
    ameru_map = {"01_FV":"01_FV","10_cta":"10_cta"}
    ameru_key = ameru_map.get(section_key)
    ameru_refs = []
    if ameru_key:
        ameru_refs = [CORPUS_AMERU / m["file"] for m in MATCH_AMERU.get(ameru_key, [])[:1]]
    return [p for p in (dr_refs + ameru_refs) if p.exists()]

if __name__ == "__main__":
    print("=== E版（ハイブリッド） ===")
    for fname, (skey, detail) in SECTION_MAP.items():
        refs = build_refs_E(skey)
        print(f"\n[E/{fname}] {skey}  refs: {[r.name for r in refs]}")
        gen(OUT_E / fname, STYLE_E, detail, refs)

    print("\n=== D版（DR全開） ===")
    for fname, (skey, detail) in SECTION_MAP.items():
        refs = build_refs_D(skey)
        print(f"\n[D/{fname}] {skey}  refs: {[r.name for r in refs]}")
        gen(OUT_D / fname, STYLE_D, detail, refs)

    print("\n=== done ===")
    print(f"E: {len(list(OUT_E.glob('*.png')))} / D: {len(list(OUT_D.glob('*.png')))}")
