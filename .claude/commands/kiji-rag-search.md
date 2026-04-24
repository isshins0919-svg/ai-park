---
name: kiji-rag-search
description: 記事LP Vector RAG から意味検索。自然言語クエリ × 20要素フィルタの二段構え。「権威性の強い信頼ブロック」「CTA直前のリスクリバーサル」「緊急性訴求の強いオファー」等を記事横断で引ける。
---

# /kiji-rag-search — 記事LP RAG 意味検索

`.claude/knowledge/kiji-rag/articles/*/` に蓄積された記事LPチャンクを、**ベクトル類似度（embedding-2 / 3072次元）× 20要素スコアフィルタ** の二段構えで横断検索する。

## 対象データ

- チャンク単位（ブロック切り替わりで区切り）
- 各チャンクに20要素スコア（`.claude/knowledge/kiji-rag/sales_elements.md`）
- メタ: block_type / dominant_layer / dominant_elements / funnel_position / brand

## 使い方

```
/kiji-rag-search <クエリ> [オプション…]
```

### オプション

| 指定 | 効果 |
|---|---|
| `layer=<A\|B\|C\|D\|E>` | dominant_layer でフィルタ（A=共感/B=信頼/C=論理/D=欲求/E=行動）|
| `element=<ID>>=<閾値>` | 20要素スコア閾値。例: `element=E1_urgency>=0.8` |
| `article=<article_id>` | 特定記事に絞る |
| `block=<text\|image\|video>` | ブロック種別フィルタ |
| `k=<N>` | 上位N件（デフォルト5）|
| `per_article=<N>` | 同一記事からの最大ヒット数（記事多様性確保） |

### 例

```
/kiji-rag-search 40代いちご鼻の強い共感フック
/kiji-rag-search CTA直前のリスクリバーサル layer=E
/kiji-rag-search 緊急性訴求 element=E1_urgency>=0.8 k=3
/kiji-rag-search 独自メカニズムの説明 block=text
/kiji-rag-search 権威性 article=20260424_aurelie_megumi_kakusen
```

## 20要素キー一覧

| 層 | 要素キー |
|---|---|
| **A. 共感** | `A1_pain_empathy` `A2_fear_appeal` `A3_regret_avoidance` `A4_anxiety_trigger` |
| **B. 信頼** | `B1_authority` `B2_social_proof` `B3_data_evidence` `B4_transparency` |
| **C. 論理** | `C1_causality` `C2_unique_mechanism` `C3_differentiation` `C4_objection_handling` |
| **D. 欲求** | `D1_transformation` `D2_aspiration` `D3_scenario` `D4_scarcity` |
| **E. 行動** | `E1_urgency` `E2_offer_appeal` `E3_risk_reversal` `E4_cta_clarity` |

## 実装手順（Claude へのインストラクション）

ユーザー入力からクエリとオプションを抽出し、以下を Bash で実行：

```bash
python3 .claude/knowledge/kiji-rag/tools/search.py "<QUERY>" [OPTIONS]
```

### オプションマッピング

| ユーザー入力 | search.py引数 |
|---|---|
| `layer=X` | `--layer X` |
| `element=KEY>=THR` | `--element KEY:THR` |
| `article=ID` | `--article ID` |
| `block=TYPE` | `--block-type TYPE` |
| `k=N` | `-k N` |
| `per_article=N` | `--per-article-limit N` |

### 結果整形ルール

- search.py は整形済みで出力する。そのまま表示してOK。
- ヒットが0件なら、フィルタ緩和（閾値下げ・layer外し）の再試行を提案する。
- 同じ記事から似たチャンク複数ヒットした場合、何の訴求軸が強いか解説コメントを1-2行添える。

## 関連

- `.claude/knowledge/kiji-rag/README.md` — RAG基盤の目的・使い方
- `.claude/knowledge/kiji-rag/sales_elements.md` — 20要素定義
- `.claude/knowledge/kiji-rag/schema.md` — データスキーマ
- `.claude/knowledge/kiji-rag/INDEX.md` — 格納済み記事一覧
