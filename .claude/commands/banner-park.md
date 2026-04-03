# Banner Park ver.7.0

strategy.json + Concept Park 完了前提。3つの魂 — **キービジュアルそのもの × キラーキャッチコピー × 別の仮説**。DPro KV哲学フィルター × ベクトル品質ゲート × Nano Banana Pro × PDFマーケティングインテリジェンスレポート。

`/banner-park` で起動。

---

## 起動時表示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BANNER PARK ver.7.0
  戦略翻訳型 × 仮説駆動 × ベクトル品質保証 × PDFレポート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  前提: /research-park + /concept-park 完了済み
  3つの魂:
    1. キービジュアルそのもの
    2. キラーキャッチコピー
    3. 別の仮説
  Nano Banana Pro × DPro KV哲学フィルター × PDFレポート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

ランダム1行:
- 「戦略を弾丸に変換する。装填開始。」
- 「1枚1枚がキービジュアル。1行1行がキラーコピー。」
- 「仮説の数だけ、勝ち筋がある。」
- 「N1の脳内に1番乗りするバナー、作るぞ。」

---

## 3つの魂（哲学）

Banner Park v7.0 が生み出す全てのバナーは、この3つの魂を宿す。

### 魂1: キービジュアルそのもの

> **1つ1つのバナーが、この商品コンセプトを引き立たせるキービジュアルそのものであろうとする。**

バナーは「広告枠を埋める画像」ではない。その商品の世界観を1枚で体現する作品。
Concept Park で確定した keyVisual の方向性が、全バナーのビジュアルの核になる。
DPro リサーチでも「数字 × 美しさ」の2段階で選ぶ。売れてるだけじゃダメ。美しくないと学ばない。

### 魂2: キラーキャッチコピー

> **各バナーの文言は、その商品を代表するキラーキャッチコピーであろうとする。**

ヘッドラインは「説明文」ではない。その1行で商品の全てを語れるレベルの言葉。
Concept Park で確定した salesCopy + hookVectors が起点。
「この1行だけ見て、買いたくなるか？」が基準。

### 魂3: 別の仮説

> **5枚、10枚、20枚 — 数ではなく仮説の数。各バナーが異なる検証仮説を持つ。**

同じコピーの色違いを量産しない。各バナーが「このN1に、このフック角度で、この視線誘導で刺したら？」という固有の仮説を持つ。
配信後に「どの仮説が当たったか」が分かる設計。

---

## Phase 0: 選択肢ヒアリング

### 0-A: strategy.json 読み込み

`research-park/output/{PRODUCT_SLUG}/strategy.json` を Read。
なければ → 「先に `/research-park` + `/concept-park` を実行してね」と案内して終了。

strategy.json から以下を取得:
- `productIntel` → 商品情報・USP
- `primaryN1` → ターゲットN1（層・ペルソナ・新認知戦略）
- `concept` → コンセプト・Only1ポジション・コンセプトベクトル
- `keyVisual` → ビジュアル方向性（mood/色/構図/商品見せ方）
- `salesCopy` → セールスコピーA/B・ベクトル
- `messageSystem` → メッセージ体系・トーン・NG表現
- `formatStrategy.banner` → バナー固有の役割・メッセージ・ベクトル基準値
- `hookVectors` → フック角度バリエーション + ベクトル
- `layerCommunication` → 3層別コミュニケーション方針
- `assets` → ブランドアセット（ロゴ・カラー・ビジュアルトーン）

`all_vectors.json` も Read → 品質ゲートで使う。

**keyVisual / salesCopy / formatStrategy / hookVectors が空の場合** → 「先に `/concept-park` を完了してね」と案内。

### 0-B: 選択肢ヒアリング

パクに以下を**選択肢形式**で質問:

```
━━━ バナー設定 ━━━

1. 広告媒体は？
   a) Meta（Instagram / Facebook）
   b) TikTok
   c) Google（GDN / YouTube）
   d) LINE
   e) その他（入力）

2. バナーサイズは？
   a) 1080×1080（1:1 — SNSフィード）
   b) 1080×1350（4:5 — Instagram推奨）
   c) 1200×628（1.91:1 — GDN / Facebook）
   d) 1080×1920（9:16 — ストーリーズ / TikTok）
   e) その他（入力）

3. 獲得タイプは？
   a) EC購入
   b) リード獲得（LP→フォーム）
   c) アプリインストール
   d) その他（入力）

4. 生成枚数は？
   a) 5枚（最小仮説セット — 高速テスト向き）
   b) 10枚（標準仮説セット — バランス型）
   c) 20枚（最大仮説セット — 大規模テスト向き）
━━━━━━━━━━━━━━━━━━━━
```

アスペクト比変換:

| サイズ | アスペクト比 |
|--------|------------|
| 1080×1080 | 1:1 |
| 1080×1350 | 4:5 |
| 1200×628 | 1.91:1 |
| 1080×1920 | 9:16 |
| 上記以外 | 最も近いものに丸め |

---

## ナレッジ読み込み

以下を **Read tool で必ず読む**:
- `.claude/knowledge/banner-dna-templates.md` — 勝ちDNA BN-A〜F
- `.claude/knowledge/hook-db.md` — フックDB BH1〜BH8
- `.claude/knowledge/cta-db.md` — CTADB BC1〜BC8

※ マーケティング哲学はResearch Parkで反映済み。コンセプト・KV・セールスコピー・フォーマット戦略はConcept Parkで確定済み。全てstrategy.jsonに入っている。

---

## Phase 1: DPro KV哲学フィルターリサーチ

**メインエージェントが DPro MCP を直接実行。**

### 哲学: 「数字 × 美しさ」の2段階選定

普通のリサーチ = 売れてるバナーを集める。
KV哲学フィルター = **売れてる × 美しいバナーだけ学ぶ**。

- **Stage 1（数字フィルター）**: DPro MCP で cost_difference 上位を取得
- **Stage 2（KV哲学フィルター）**: 取得したバナーの ad_all_sentence を読み、「このバナーは商品のキービジュアルとして成立するか？」で選別

### Step 1: ジャンル特定

`search_genres` で関連ジャンル1-3個特定。
strategy.json の `dproIntel.genreId` があればそれを使用。

### Step 2: DPro データ取得

#### 勝ちバナー候補 20本取得
`get_items` で以下2回取得:

| 条件 | パラメータ |
|------|-----------|
| 月間安定勝ち | interval=30, sort=cost_difference-desc, limit=100 |
| 直近急上昇 | interval=7, sort=cost_difference-desc, limit=100 |

両方のTOP30に入るバナーを優先。同一advertiser最大2本。

### Step 3: KV哲学フィルター（2段階評価）

取得した20本の ad_all_sentence + production_url を確認し、**2軸で評価**:

```
各バナーに対して:

■ 数字スコア（DProデータから自動）
  cost_difference / play_count / digg_rate

■ KV哲学スコア（AIが判定）
  「このバナーは、その商品のキービジュアルとして美しく成立しているか？」
  5段階: ★1（広告感丸出し）〜 ★5（ブランドKVレベル）

  判定基準:
  - ビジュアルの統一感と世界観
  - 商品の見せ方が魅力的か
  - タイポグラフィの品質
  - 色彩設計の美しさ
  - 「広告」を超えて「作品」に見えるか

合格ライン: 数字TOP20 かつ KV哲学 ★3以上 → 学習対象
```

### Step 4: 合格バナーの構造分析

KV哲学フィルター通過バナー（5-10本）を分析:

各バナーについて:
1. **composition**: layout, zones, colorScheme, typography, imageRole, ctaDesign
2. **eyeFlow**: pattern（Z/F/中央集中/対角線）, step1-3, anchors
3. **copyStructure**: hook, hookText, benefit, proof, cta
4. **matchedTemplate**: templateId（BN-A〜F or OTHER）, matchConfidence
5. **kvQuality**: なぜこのバナーがKVとして美しいのか — 学ぶべきポイント

### DPro件数不足時フォールバック

interval 30→7→2、ジャンルなしで再検索。最低3本確保。
DPro非掲載の場合 → Phase 1 スキップ、Phase 2 はstrategy.json のみで設計。

---

## Phase 2: N枚のバナー設計（仮説ベース）

### 設計の原則

**N枚 = N個の仮説。** 各バナーが固有の検証仮説を持つ。

仮説の変数:
- **フック角度**: hookVectors から選択（常識否定/共感/結果提示/権威/好奇心）
- **視線誘導**: 4パターンから選択（Z型/F型/中央集中型/対角線型）
- **ヘッドライン**: salesCopy を軸に、フック角度に合わせたバリエーション
- **ビジュアル表現**: keyVisual を軸に、フック角度に合わせた微調整

### Step 1: hookVector 選択アルゴリズム（ベクトル多様性最大化）

N枚分のフック角度を、ベクトル空間上で最大限バラけるように自動選択。

**実装コード → `.claude/knowledge/vector-utils.md`「hookVector 選択アルゴリズム」セクションを参照。**

- 閾値: N1需要 sim >= 0.45 / hookVector間 sim <= 0.70
- `target_count = banner_count` として実行

### Step 2: 視線誘導パターンの割り当て

→ `.claude/knowledge/creative-reference.md`「視線誘導パターン」セクション参照。
4パターン（Z型/F型/中央集中型/対角線型）をN枚に均等分配。

### Step 3: bannerSpec 生成（N枚分の設計書）

Claude が strategy.json の全データを読み解き、N枚分の bannerSpec（JSON設計書）を生成する。

```json
{
  "bannerIndex": 1,
  "hypothesis": "常識否定型フック × Z型視線 — 準顕在層の既存常識を壊し、新基準を提示",
  "hookAngle": "常識否定型",
  "hookSource": "hookVectors[0]",
  "gazeFlow": "Z型",
  "gazeDescription": "左上: ヘッドライン → 右上: サブコピー → 左下: 商品画像 → 右下: CTA",

  "headline": "○○は逆効果だった",
  "subHeadline": "△△△△△△△△△",
  "ctaText": "詳しく見る",
  "offerBadge": null,

  "visualDirection": {
    "mood": "keyVisual.mood を継承",
    "productPresentation": "keyVisual.productPresentation を継承",
    "humanElement": "keyVisual.humanElement を継承",
    "colorDirection": {
      "primary": "keyVisual.colorDirection.primary",
      "accent": "keyVisual.colorDirection.accent",
      "background": "keyVisual.colorDirection.background"
    },
    "composition": "Z型に最適化した具体的構図",
    "typography": "keyVisual.typography を継承",
    "differentiator": "keyVisual.differentiator — 競合バナーとの視覚的差別化"
  },

  "kvPhilosophy": "このバナーがKVとして成立する理由 — keyVisualの世界観をどう体現するか",
  "killerCopyPhilosophy": "このヘッドラインが商品を代表するキラーコピーとして成立する理由",
  "testHypothesis": "配信後に検証したい仮説 — 例: 常識否定フックは準顕在層のCTR向上に効くか"
}
```

### Step 4: コピーライティング詳細ルール

各バナーのヘッドライン生成時に適用:

1. **salesCopy が起点**: strategy.json の salesCopy.primary / primaryB をベースに、hookAngle に合わせて変換
2. **15文字以内**: バナーヘッドラインは15文字以内（パクの基準）
3. **数字ファースト**: 数値が入る場合は冒頭に
4. **フックDB照合**: BH1-BH8 の該当パターンを参考
5. **CTADB照合**: BC1-BC8 から獲得タイプに合わせて選定
6. **NG表現チェック**: messageSystem.ngExpressions に該当しないか確認
7. **新認知戦略の反映**: primaryN1.newCognitionStrategy をコピーに織り込む
8. **KV哲学連動**: Phase 1 で学んだ勝ちバナーのコピーパターンを参考

### Step 5: fullBannerPrompt 変換（Claude → Gemini）

bannerSpec を自然言語プロンプトに変換。Gemini が最も良く理解する形式。

```
[1. ビジュアル指示（英語）]
Create a professional {aspect_ratio} Japanese advertisement banner for {product_name}.
Visual style: {mood}, {productPresentation}. {humanElement}.
Color palette: primary {primary}, accent {accent}, background {background}.
Overall feel: {kvPhilosophy — KVとしての世界観}.

[2. 構図・視線誘導（英語）]
Layout: {gazeFlow} eye flow pattern.
{gazeDescription — 具体的なゾーン配置}
Composition: {composition — 具体的構図}

[3. 日本語テキスト配置]
Place the following Japanese text directly in the image:
- HEADLINE: '{headline}' — bold {typography}, {headline_position}, high contrast, clearly legible
- SUB: '{subHeadline}' — semi-bold, positioned below headline
- CTA: '{ctaText}' — {ctaColor} rounded button, {cta_position}
{offerBadge指示 — null時省略}

[4. テキスト品質指示]
CRITICAL: All Japanese text must be perfectly rendered and legible.
- Sufficient contrast ratio between text and background
- No text cut off at edges (maintain 5% safe margin on all sides)
- Clean, modern sans-serif font for Japanese characters
- Text hierarchy: headline largest, sub smaller, CTA button text medium

[5. ネガティブ指示]
Do NOT include: watermarks, blurry text, overlapping text elements, English translations of Japanese text, stock photo watermarks, excessive visual clutter.

[6. ブランド差別化]
{brand_directive — ロゴ配置等}
Differentiation: {differentiator — 競合バナーとの視覚的差別化}
```

各バナーの fullBannerPrompt を `bannerSpecs[]` に保持。

---

## Phase 3: ベクトル品質ゲート（生成前検証）

**Gemini に画像生成を投げる前に、プロンプトの品質をベクトルで検証する。**
ダメなプロンプトを事前に弾く = APIコスト削減 + 品質保証。

### ベクトル品質ゲート

**実装コード → `.claude/knowledge/vector-utils.md`「4段階ベクトル品質ゲート」セクションを参照。**

バナー固有の準備:
```python
# 各バナーのヘッドラインをベクトル化して item_vecs を作成
item_vecs = []
for spec in bannerSpecs:
    vec = embed(spec['headline'] + ' ' + spec['subHeadline'])
    spec['headlineVector'] = vec
    item_vecs.append({'index': spec['bannerIndex'], 'vector': vec, 'label': spec['headline']})
```

ゲート不通過時の自動修正（3回トライしてFAILなら停止して報告）:
- コンセプト一貫性 FAIL → ヘッドラインをコンセプトに寄せて再生成
- 競合差別化 FAIL → フック角度変更 or 表現差別化
- 多様性 FAIL → 類似ペアの片方のフック角度変更

---

## Phase 4: Nano Banana Pro 画像生成

N枚を `gemini-3-pro-image-preview` で生成。

```python
import subprocess, os, time
from google import genai
from google.genai import types

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass
for _v in ['GEMINI_API_KEY_1','GEMINI_API_KEY_2','GEMINI_API_KEY_3']:
    _load_env(_v)

API_KEYS = [k for k in [os.environ.get(f'GEMINI_API_KEY_{i}','').strip() for i in range(1,4)] if k]
clients = [genai.Client(api_key=k) for k in API_KEYS]

slug = '{slug}'
out_dir = f'banner-park/output/{slug}'
banner_dir = f'{out_dir}/banners'
spec_dir = f'{out_dir}/specs'
os.makedirs(banner_dir, exist_ok=True)
os.makedirs(spec_dir, exist_ok=True)

# ロゴ参照画像（あれば Gemini マルチモーダル入力で渡す）
logo = None
logo_path = f'assets/{slug}/logo.png'
if os.path.exists(logo_path):
    with open(logo_path, 'rb') as f:
        logo = f.read()

ok = ng = 0

for i, spec in enumerate(bannerSpecs):
    fn = f"banner_{spec['bannerIndex']:02d}.png"
    fp = os.path.join(banner_dir, fn)
    if os.path.exists(fp):
        ok += 1
        continue

    prompt = spec['fullBannerPrompt']
    contents = ([types.Part.from_bytes(data=logo, mime_type='image/png'),
                 prompt + ' Include the provided logo at top-right corner, small size.'] if logo else prompt)

    for attempt in range(3):
        c = clients[(i + attempt) % len(clients)]
        try:
            resp = c.models.generate_content(
                model='gemini-3-pro-image-preview',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(aspect_ratio=spec['aspectRatio'])))
            img = next((p.inline_data.data for p in resp.parts if p.inline_data), None)
            if not img or len(img) < 10240:
                if attempt < 2:
                    time.sleep(3)
                    continue
                ng += 1
                break
            with open(fp, 'wb') as f:
                f.write(img)
            ok += 1
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                ng += 1
    time.sleep(2)

    # bannerSpec を JSON として保存
    spec_path = os.path.join(spec_dir, f"banner_{spec['bannerIndex']:02d}_spec.json")
    with open(spec_path, 'w', encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

print(f'\\n=== 生成結果: {ok}/{len(bannerSpecs)} OK, {ng}/{len(bannerSpecs)} NG ===')
```

---

## Phase 5: テキスト品質 + KV品質検証

### 5-A: テキスト品質検証

Gemini Flash で全画像の日本語テキスト読み取り検証。

```python
client_flash = genai.Client(api_key=os.environ['GEMINI_API_KEY_1'])
import glob

files = sorted(glob.glob(f'{banner_dir}/*.png'))
text_issues = []

for fp in files:
    with open(fp, 'rb') as f:
        img = f.read()
    r = client_flash.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
            types.Part.from_bytes(data=img, mime_type='image/png'),
            'このバナー画像内の日本語テキストを全て読み取れ。以下を判定:\n'
            '1. テキストが切れていないか\n'
            '2. 文字化け・誤字がないか\n'
            '3. テキストの視認性（コントラスト十分か）\n'
            '問題なければ「OK」のみ。問題あれば「ISSUE: {具体的な問題}」で報告。'
        ])
    has_issue = 'ISSUE' in r.text.upper()
    print(f"{'⚠️' if has_issue else '✅'} {os.path.basename(fp)}: {r.text.strip()[:100]}")
    if has_issue:
        text_issues.append(os.path.basename(fp))
```

テキスト問題あり → 該当バナーを再生成（最大3回リトライ）。

### 5-B: KV品質検証

各バナーが「キービジュアルとして成立しているか」をAIが判定:

```python
for fp in files:
    with open(fp, 'rb') as f:
        img = f.read()
    kv_check = client_flash.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
            types.Part.from_bytes(data=img, mime_type='image/png'),
            f'このバナーを、商品「{product_name}」のキービジュアルとして評価してください。\n'
            f'コンセプト: 「{concept}」\n'
            f'ビジュアル方向性: {visual_concept}\n\n'
            '5段階評価:\n'
            '★5: ブランドKVレベル — そのまま公式サイトのメインビジュアルに使える\n'
            '★4: 高品質広告 — プロが作った広告クリエイティブとして十分\n'
            '★3: 標準品質 — 広告として機能するが特筆すべき点なし\n'
            '★2: 品質不足 — 素人感がある、またはコンセプトとズレ\n'
            '★1: 使用不可 — 品質問題あり\n\n'
            '回答形式: ★X — 理由（1行）'
        ])
    print(f"  {os.path.basename(fp)}: {kv_check.text.strip()[:100]}")
```

★2以下 → 再生成。★3 → パクに報告（使うか判断）。★4以上 → 合格。

### 5-C: 生成テキストのベクトル事後検証

画像から抽出したテキストをベクトル化し、コンセプトとの乖離をチェック:

```python
for fp, spec in zip(files, bannerSpecs):
    with open(fp, 'rb') as f:
        img = f.read()
    # テキスト抽出
    r = client_flash.models.generate_content(
        model='gemini-2.0-flash',
        contents=[types.Part.from_bytes(data=img, mime_type='image/png'),
                  'この画像内の日本語テキストを全て抽出して、1行で連結して返してください。'])
    actual_text = r.text.strip()
    if actual_text:
        actual_vec = embed(actual_text)
        sim = cosine_sim(actual_vec, concept_vec)
        print(f"  Banner {spec['bannerIndex']:02d} 実テキスト×コンセプト: sim={sim:.3f} {'✅' if sim >= 0.40 else '⚠️乖離'}")
```

---

## Phase 6: マーケティングインテリジェンスレポート

### 6-A: レポートデータ収集

Phase 0〜5 の全データを集約:

```python
report_data = {
    'product': strategy['productIntel'],
    'n1': strategy['primaryN1'],
    'concept': strategy['concept'],
    'keyVisual': strategy['keyVisual'],
    'salesCopy': strategy['salesCopy'],
    'formatStrategy': strategy['formatStrategy']['banner'],
    'hookVectors': strategy['hookVectors'],
    'bannerSpecs': bannerSpecs,
    'gateResults': gate_results,
    'kvScores': kv_scores,
    'textVerification': text_results,
    'dproResearch': dpro_research_summary,
    'generatedAt': datetime.now().isoformat(),
    'bannerCount': len(bannerSpecs)
}
```

### 6-B: HTML レポート生成

`banner-park/output/{slug}/report.html` を生成。

レポート構成:

6セクション構成:
1. 表紙（商品名・コンセプト・日付・枚数）
2. 戦略サマリー（N1・コンセプト・KV・セールスコピー・フック角度一覧）
3. バナーポートフォリオ（各バナー: 画像 + 仮説カード）
4. ベクトル検証レポート（コンセプト一貫性・競合差別化・多様性・N1刺さり度）
5. テスト戦略（Round 1: フック大分類 → Round 2: バリエーション → Round 3: 視線誘導。判定: CTR×1.5/CVR×1.2/CPA×0.8）
6. Next Action（空白地帯・次回角度・勝ちパターン仮説）

HTMLはダークテーマ。プリント時はライトテーマに自動切替（`@media print`）。

### 6-C: PDF 変換

```python
# weasyprint でHTML → PDF変換
try:
    from weasyprint import HTML
    HTML(filename=f'{out_dir}/report.html').write_pdf(f'{out_dir}/report.pdf')
    print(f"✅ PDF生成完了: {out_dir}/report.pdf")
except ImportError:
    # weasyprint 未インストール時のフォールバック
    print("⚠️ weasyprint未インストール。HTMLレポートのみ生成。")
    print(f"  PDF化するには: pip install weasyprint")
    print(f"  または report.html をブラウザで開いて Cmd+P でPDF化")
```

### 6-D: 出力ディレクトリ構造

```
banner-park/output/{PRODUCT_SLUG}/
├── banners/                    ← バナー画像（PNG）
│   ├── banner_01.png
│   ├── banner_02.png
│   └── ...
├── specs/                      ← 各バナーの設計書（JSON）
│   ├── banner_01_spec.json
│   └── ...
├── report.html                 ← レポート原本（ダークテーマ）
└── report.pdf                  ← マーケティングインテリジェンスレポート
```

### 6-E: 完了プレゼン

```
━━━━━ BANNER PARK v7.0 完了 ━━━━━
商品: {product_name}
コンセプト: 「{concept}」

生成結果:
  バナー: {ok}/{total} 枚 生成成功
  KV品質: 平均 ★{avg_kv_score}
  テキスト品質: {text_ok}/{total} 枚 OK

ベクトル検証:
  コンセプト一貫性: 平均 sim={avg_concept_sim:.3f}
  競合差別化: 平均 sim={avg_comp_sim:.3f}
  バナー間多様性: {diversity_issues}件の類似ペア

納品物:
  📁 banners/ — {N}枚のバナー画像
  📁 specs/ — {N}枚の設計書JSON
  📄 report.html — インタラクティブレポート
  📄 report.pdf — マーケティングインテリジェンスレポート

テスト戦略:
  Round 1: {round1_description}
  Round 2: {round2_description}

Next Action:
  {next_action_summary}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 注意事項

- **前提**: `/research-park` + `/concept-park` 完了済み。strategy.json に concept / keyVisual / salesCopy / formatStrategy / hookVectors が全て入っていること
- **Phase 0**: 選択肢ヒアリングで枚数決定。5/10/20
- **Phase 1**: メインが直列実行（DPro MCP依存）。KV哲学フィルターで「美しい × 売れてる」だけ学ぶ
- **Phase 2**: Claude が strategy.json を読み解いて bannerSpec(JSON) → fullBannerPrompt(自然言語) の2段変換
- **Phase 3**: ベクトル品質ゲートは**生成前**。formatStrategy.banner.vectorCheckpoints の基準値を適用
- **Phase 4**: Nano Banana Pro シングルエンジン。GEMINI_API_KEY 最低1本
- **Phase 5**: テキスト + KV + ベクトルの3重検証
- **Phase 6**: HTMLレポート + PDF（weasyprint）。「人が次に活かせる情報」を全て含む
- **3つの魂**: 全Phaseを通じて、KVそのもの × キラーコピー × 別の仮説 を常に意識
- **ベクトル活用3箇所**: Phase 2（hookVector選択）→ Phase 3（品質ゲート）→ Phase 5-C（事後検証）
