---
name: kiji-rag-add
description: 記事LP URLから kiji-rag に1記事追加する半自動パイプライン。WebFetch→ブロック統合→20要素スコアリング(Claude担当)→embedding-2までを1コマンドで実行。Squad Beyondのドラフト/公開URL両対応。
---

# /kiji-rag-add — 記事LP を kiji-rag に追加する半自動パイプライン

記事LP URL を渡すと、kiji-rag Vector RAG に**1記事を格納**するまでの全工程を半自動で実行する。

**半自動の理由**: 20要素スコアリングは現状 Claude（セッション）が手動判定。`/kiji-rag-add` 実行時、このセッション内で Claude が chunks プレビューを見てスコアを付ける。v2.0 で Haiku 自動化予定。

---

## 使い方

```
/kiji-rag-add <URL> [brand=<brand>] [keyword=<keyword>]
```

### 引数

| 引数 | 必須 | 説明 |
|---|---|---|
| `<URL>` | ✅ | 記事LP の URL（Squad Beyond 公開/ドラフト両対応） |
| `brand=<name>` | 任意 | ブランド名（article_id 自動生成に使用。省略時は Claude が推定） |
| `keyword=<word>` | 任意 | 記事テーマ（例: `megumi_kakusen`, `cream2_wakiga`）。省略時は Claude が推定 |

### 例

```
/kiji-rag-add https://sb.aurelie.tokyo/ab/xxxxx
/kiji-rag-add https://sb-draft-preview.squadbeyond.com/articles/yyyyy/draft?token=zzz brand=proust keyword=cream3
```

---

## 実行手順（Claude へのインストラクション）

### Step 1: 引数解析 & article_id 決定

1. URL を受け取る
2. `brand` / `keyword` 指定があれば使う、なければ URL取得後にタイトル・本文から推定
3. article_id 命名規則: `YYYYMMDD_<brand>_<keyword>` （`date '+%Y%m%d'` で生成）
4. 格納先ディレクトリ: `.claude/knowledge/kiji-rag/articles/<article_id>/`

### Step 2: WebFetch で記事取得

```
WebFetch(url=<URL>, prompt="<標準プロンプト（後述）>")
```

**標準プロンプト**（記事構造抽出用）:

```
この記事LPの構造を上から下まで順番通りに全ブロック抽出してください。3種類:
text / image / video

出力JSON:
{
  "article_title": "(タイトル)",
  "brand_name": "(ブランド名)",
  "product_name": "(商品名)",
  "total_blocks": (数),
  "cta_count": (数),
  "cta_positions": [(order配列)],
  "cta_destination_url": "(URL)",
  "blocks": [
    {"order":1, "block_type":"text|image|video",
     "content":"...", "media_url":"...", "alt_text":"...",
     "caption":"...", "heading_level":"...", "tag_hint":"...",
     "is_cta_block":bool, "cta_url":"..."}
  ]
}

重要:
- 省略せず全ブロック。HTMLタグ除去。
- 動画(<video>/iframe)は必ず video 型で識別。
- Squad Beyond の lazy-load 画像はそのまま placeholder URL で構わない。
- 口コミ実名は原文保持（後工程で匿名化判定）。
```

**注意**: Squad BeyondドラフトURLならトークン込みで渡せば取れる。将来 `getArticleHtml` MCP に移行可能。

### Step 3: blocks_raw.json 保存

取得した JSON を以下に保存:
- path: `.claude/knowledge/kiji-rag/articles/<article_id>/blocks_raw.json`
- 先頭に以下のフィールドを追加:
  - `article_id`
  - `source_url`
  - `fetched_at`（ISO8601 now）
  - `fetched_by`: `"WebFetch"`
  - `degraded_mode_notes`: 画像がlazy.pngなら記録

### Step 4: meta.json 骨格作成

同ディレクトリに `meta.json` を作成。スキーマは `.claude/knowledge/kiji-rag/schema.md` 参照。

必須フィールド:
- article_id / source_url / article_title / brand_name / product_name
- company（わかれば）/ product_category / target_persona
- hook_angle（推定）/ concept_type（推定）
- fetched_at / total_blocks_raw
- cta_count_unique_url / cta_orders_in_raw / cta_destination_url
- key_offer（価格・特典・リスクリバーサル）
- performance: すべて null（未取得）
- quality_flags（画像解決状況・匿名化必要性）

### Step 5: チャンク統合

```bash
python3 .claude/knowledge/kiji-rag/tools/merge_blocks.py \
  .claude/knowledge/kiji-rag/articles/<article_id>/blocks_raw.json \
  .claude/knowledge/kiji-rag/articles/<article_id>/chunks_skeleton.json
```

出力で chunk数を確認。text/image/video の内訳も報告。

### Step 6: chunks プレビュー

以下のPythonワンライナーでチャンクの内容をプレビュー:

```bash
python3 << 'EOF'
import json
from pathlib import Path
data = json.loads(Path('.claude/knowledge/kiji-rag/articles/<article_id>/chunks_skeleton.json').read_text())
for c in data['chunks']:
    text = c['content_text'] or ''
    media = f"[image x{len(c['content_media_urls'])}]" if c['block_type'] == 'image' else ''
    cta = '*CTA*' if c.get('has_cta') else ''
    print(f"[{c['chunk_order']:>2}] ({c['block_type']:<5}, src={c['source_block_orders']}) {cta}")
    if text:
        preview = text[:250].replace('\n', ' / ')
        print(f"     TXT: {preview}")
    if media:
        caps = [x for x in c['content_captions'] if x]
        print(f"     IMG: {media}" + (f" caption={caps}" if caps else ""))
EOF
```

### Step 7: 20要素スコアリング（Claude 担当）

**このセッション内で Claude が chunks プレビューを読み、全チャンクに 20要素スコアを付与する**。

ルーブリック参照: `.claude/knowledge/kiji-rag/sales_elements.md`

20要素:
```
A. 共感層: A1_pain_empathy / A2_fear_appeal / A3_regret_avoidance / A4_anxiety_trigger
B. 信頼層: B1_authority / B2_social_proof / B3_data_evidence / B4_transparency
C. 論理層: C1_causality / C2_unique_mechanism / C3_differentiation / C4_objection_handling
D. 欲求層: D1_transformation / D2_aspiration / D3_scenario / D4_scarcity
E. 行動層: E1_urgency / E2_offer_appeal / E3_risk_reversal / E4_cta_clarity
```

スコア基準:
- 0.0: 要素なし / 0.3: 片鱗のみ / 0.5: 標準 / 0.7: 強い / 1.0: チャンクの核

**出力**: `.claude/knowledge/kiji-rag/articles/<article_id>/scores.json`

フォーマット:
```json
{
  "article_id": "<article_id>",
  "scorer": "claude-opus-4-7[1m] manual",
  "scored_at": "<ISO8601>",
  "rubric_version": "sales_elements.md v1.0 (5層×4要素=20)",
  "scores": [
    {"chunk_order": N, "funnel_position": "<opening|empathy|concept|mechanism|authority|proof|offer|cta|closing>",
     "context_hint": "<そのチャンクの役割を1行>",
     "elements": {"<要素キー>": 0.0-1.0, ...}}
    // 0.0の要素は省略可（apply_scoresで自動埋め）
  ]
}
```

**留意点**:
- 画像チャンクは周辺テキスト＋captionから訴求推定（薄くてOK、「-」で dominant_layer が null になっても問題ない）
- 長大統合テキストチャンクは複数要素ピークが出る → 全部拾う
- context_hint は将来の自分のため丁寧に書く（検索ランキングの説明責任）

### Step 8: スコア注入 → chunks.json 生成

```bash
python3 .claude/knowledge/kiji-rag/tools/apply_scores.py \
  .claude/knowledge/kiji-rag/articles/<article_id>/chunks_skeleton.json \
  .claude/knowledge/kiji-rag/articles/<article_id>/scores.json \
  .claude/knowledge/kiji-rag/articles/<article_id>/chunks.json
```

出力の `dominant_layer distribution` と `layer avg` を報告。

### Step 9: embedding-2 ベクトル化

```bash
python3 .claude/knowledge/kiji-rag/tools/embed_chunks.py \
  .claude/knowledge/kiji-rag/articles/<article_id>/chunks.json
```

`embeddings.npy` (N×3072) と `embedding_index.jsonl` が生成される。所要時間 = チャンク数 × 0.35秒程度。

### Step 10: INDEX.md 更新

`.claude/knowledge/kiji-rag/INDEX.md` に1行追加:

```
| <article_id> | <brand> | <title> | <YYYY-MM-DD> | <N> (text/image/video内訳) | <dom分布> | <strategy_type推定> | - | - | embedded (3072dim) |
```

`strategy_type` は dominant_layer 分布から推定:
- E > B > 他 = 権威×オファー強押し型
- C > B > 他 = 問題再定義×論理メカニズム型
- A > D > 他 = 共感ドラマ型
- B ≫ 他 = 権威頼り型
- (自由に命名、層分布の主軸2つを言語化)

### Step 11: 動作確認

記事特有のテーマでクエリしてトップヒットを確認:

```bash
python3 .claude/knowledge/kiji-rag/tools/search.py "<記事特有のクエリ>" \
  --article <article_id> -k 3
```

期待通り該当チャンクが返るか確認。

### Step 12: 報告

ユーザーに完了報告:
- article_id / chunks数 / dominant_layer 分布 / strategy_type 推定
- 動作確認クエリの結果（top 1-2）
- degraded mode 残事項（画像URL未解決などあれば）

---

## エラーハンドリング

- WebFetch 失敗 → Squad Beyond の場合は `getArticleHtml` MCP を試す提案
- merge_blocks 失敗 → blocks_raw.json の `blocks` 配列確認
- embed API エラー → GEMINI_API_KEY_1 確認
- 既存 article_id 衝突 → suffix `_v2` 等で回避 or 上書き確認

---

## Squad Beyond MCP 対応（v1.1 で移行予定）

現在 WebFetch 経由で lazy.png placeholder 問題あり。Squad Beyond MCP ツール群:
- `getArticleHtml`: 画像URL含む完全HTML
- `listAbTestArticles`: 記事一覧
- `listAbTestDailyReports`: 成果データ（mCVR/CVR）

これらが利用可能なら、Step 2 を MCP 経由に切り替え + meta.json の `performance` フィールドを自動埋め。

---

## 関連

- `.claude/knowledge/kiji-rag/README.md` — 基盤概要
- `.claude/knowledge/kiji-rag/sales_elements.md` — 20要素ルーブリック
- `.claude/knowledge/kiji-rag/schema.md` — データスキーマ
- `.claude/knowledge/kiji-rag/tools/` — merge/apply_scores/embed/search スクリプト
- `/kiji-rag-search` — 記事横断検索スキル
