# schema — kiji-rag データスキーマ

---

## meta.json スキーマ

```json
{
  "article_id": "20260424_aurelie_megumi_kakusen",
  "source_url": "https://sb.aurelie.tokyo/ab/nOQKdjZYqRPZ-Qetiwg",
  "squad_beyond_slug": "nOQKdjZYqRPZ-Qetiwg",
  "article_title": "MEGUMIさんの角栓溶解法が話題！毛穴年齢19歳の秘密",
  "brand_name": "Aurelie.",
  "product_category": "クレンジング・スキンケア",
  "target_persona": "30-40代・毛穴悩み・美容感度中〜高",
  "fetched_at": "2026-04-24T17:03:00+09:00",
  "fetched_by": "WebFetch",
  "total_blocks_raw": 169,
  "total_chunks": 0,
  "cta_count": 4,
  "cta_orders": [155, 156, 165, 167, 168],
  "performance": {
    "mCVR": null,
    "landing_CVR": null,
    "CTR": null,
    "test_period": null,
    "note": "成果データ未取得（2026-04-24時点）。将来 Squad Beyond API or 手入力で補完予定。"
  },
  "quality_flags": {
    "images_resolved": false,
    "images_resolved_note": "WebFetch時点で全画像がlazy.png placeholder。実URLは後工程で再取得要。",
    "videos_present": false,
    "anonymization_needed": false,
    "anonymization_note": "口コミはファーストネーム1文字のみで匿名性確保済。"
  },
  "notes": ""
}
```

---

## chunks.json スキーマ

```json
{
  "article_id": "20260424_aurelie_megumi_kakusen",
  "schema_version": "1.0",
  "chunks": [
    {
      "chunk_id": "20260424_aurelie_megumi_kakusen__c001",
      "chunk_order": 1,
      "block_type": "image",
      "source_block_orders": [1, 2, 3],
      "content_text": "",
      "content_media_urls": [
        "https://file.mysquadbeyond.com/lazy.png",
        "https://file.mysquadbeyond.com/lazy.png",
        "https://file.mysquadbeyond.com/lazy.png"
      ],
      "content_captions": ["", "", ""],
      "content_alt": ["", "", ""],
      "context_hint": "ヒーローエリア（FV）画像群",
      "funnel_position": "opening",
      "elements": {
        "A1_pain_empathy": 0.2,
        "A2_fear_appeal": 0.0,
        "A3_regret_avoidance": 0.0,
        "A4_anxiety_trigger": 0.0,
        "B1_authority": 0.7,
        "B2_social_proof": 0.3,
        "B3_data_evidence": 0.4,
        "B4_transparency": 0.0,
        "C1_causality": 0.0,
        "C2_unique_mechanism": 0.0,
        "C3_differentiation": 0.0,
        "C4_objection_handling": 0.0,
        "D1_transformation": 0.0,
        "D2_aspiration": 0.6,
        "D3_scenario": 0.0,
        "D4_scarcity": 0.0,
        "E1_urgency": 0.0,
        "E2_offer_appeal": 0.0,
        "E3_risk_reversal": 0.0,
        "E4_cta_clarity": 0.0
      },
      "layer_scores": {
        "A": 0.05, "B": 0.35, "C": 0.00, "D": 0.15, "E": 0.00
      },
      "dominant_layer": "B",
      "dominant_elements": ["B1_authority", "D2_aspiration", "B3_data_evidence"],
      "total_intensity": 0.11,
      "has_cta": false,
      "embedding": null,
      "embedding_model": null,
      "embedding_generated_at": null
    }
  ]
}
```

---

## 各フィールド説明

### チャンク識別
- `chunk_id`: `<article_id>__c<3桁連番>` 形式
- `chunk_order`: 記事内の順序（1-indexed）
- `source_block_orders`: 統合前の元ブロック番号の配列（遡りトレース用）

### コンテンツ
- `block_type`: `text` / `image` / `video` のいずれか
- `content_text`: テキストチャンクの場合は本文（image/videoでは空文字）
- `content_media_urls`: image/video時のURL配列
- `content_captions`: 各メディアの説明文
- `content_alt`: 画像alt属性
- `context_hint`: そのチャンクが記事上で果たす役割のメモ（手動・LLM付与どちらでも）

### ファネル位置
- `funnel_position`: `opening` / `empathy` / `concept` / `mechanism` / `proof` / `offer` / `cta` / `closing` のいずれか
  - 20要素スコアから自動推定も可能だが、明示フィールドとして保持

### 20要素スコア
- `elements`: 20要素のスコア（0.0〜1.0）
- `layer_scores`: 5層それぞれの平均
- `dominant_layer`: 最高層
- `dominant_elements`: スコア上位3要素
- `total_intensity`: 20要素の単純平均（訴求密度）

### CTA
- `has_cta`: このチャンク内に購入導線があるか

### Embedding（後工程で埋める）
- `embedding`: ベクトル（3072次元、embedding-2）
- `embedding_model`: 使用モデル名（例: `gemini-embedding-2-preview`）
- `embedding_generated_at`: 生成日時

---

## INDEX.md 行フォーマット

```markdown
| article_id | brand | title | fetched | chunks | mCVR | CVR | status |
|---|---|---|---|---|---|---|---|
| 20260424_aurelie_megumi_kakusen | Aurelie. | MEGUMIの角栓溶解法 | 2026-04-24 | 48 | - | - | scored, embedding待 |
```

statusの値:
- `scored, embedding待`: 20要素付与済・ベクトル未生成
- `embedded`: ベクトル生成済・検索可能
- `with_performance`: 成果データ紐付け済
- `raw`: 取得直後・スコアリング未
