#!/usr/bin/env python3
"""
apply_scores.py — スコアJSONを chunks_skeleton.json に注入して chunks.json を生成する。

使い方:
    python3 apply_scores.py <chunks_skeleton.json> <scores.json> <chunks.json>

scores.json の形式:
{
  "article_id": "...",
  "scorer": "claude-opus-4-7 manual",
  "scored_at": "ISO8601",
  "rubric_version": "sales_elements.md v1.0",
  "scores": [
    {"chunk_order": 1, "funnel_position": "opening",
     "context_hint": "FVヒーロー画像", "elements": {"B1_authority": 0.6, ...}},
    ...
  ]
}

明示されなかった要素は自動で 0.0 埋め。
layer_scores / dominant_layer / dominant_elements / total_intensity は自動計算。
"""
import json
import sys
from pathlib import Path


ELEMENT_KEYS = [
    "A1_pain_empathy", "A2_fear_appeal", "A3_regret_avoidance", "A4_anxiety_trigger",
    "B1_authority", "B2_social_proof", "B3_data_evidence", "B4_transparency",
    "C1_causality", "C2_unique_mechanism", "C3_differentiation", "C4_objection_handling",
    "D1_transformation", "D2_aspiration", "D3_scenario", "D4_scarcity",
    "E1_urgency", "E2_offer_appeal", "E3_risk_reversal", "E4_cta_clarity",
]

LAYER_KEYS = {"A": [], "B": [], "C": [], "D": [], "E": []}
for k in ELEMENT_KEYS:
    LAYER_KEYS[k[0]].append(k)


def calc_layer_scores(elements):
    return {
        L: round(sum(elements[k] for k in ks) / len(ks), 3)
        for L, ks in LAYER_KEYS.items()
    }


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    skel_path = Path(sys.argv[1])
    scores_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    skel = json.loads(skel_path.read_text(encoding="utf-8"))
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    score_map = {s["chunk_order"]: s for s in scores["scores"]}

    for chunk in skel["chunks"]:
        sc = score_map.get(chunk["chunk_order"], {})
        elements = {k: 0.0 for k in ELEMENT_KEYS}
        for k, v in sc.get("elements", {}).items():
            if k in elements:
                elements[k] = float(v)
        chunk["elements"] = elements
        chunk["funnel_position"] = sc.get("funnel_position")
        chunk["context_hint"] = sc.get("context_hint", "")

        ls = calc_layer_scores(elements)
        chunk["layer_scores"] = ls
        max_layer_score = max(ls.values())
        chunk["dominant_layer"] = max(ls, key=ls.get) if max_layer_score > 0 else None

        top_sorted = sorted(elements.items(), key=lambda x: x[1], reverse=True)
        chunk["dominant_elements"] = [k for k, v in top_sorted[:3] if v > 0]
        chunk["total_intensity"] = round(sum(elements.values()) / len(ELEMENT_KEYS), 3)

    out = {
        "article_id": skel["article_id"],
        "schema_version": skel["schema_version"],
        "scored_at": scores.get("scored_at"),
        "scorer": scores.get("scorer"),
        "rubric_version": scores.get("rubric_version"),
        "total_chunks": len(skel["chunks"]),
        "layer_summary": {},
        "chunks": skel["chunks"],
    }
    # article-level layer summary (平均 × dominant_layer分布)
    from collections import Counter
    dom_counter = Counter(c["dominant_layer"] for c in skel["chunks"] if c["dominant_layer"])
    layer_avg = {L: 0.0 for L in LAYER_KEYS}
    for c in skel["chunks"]:
        for L, v in c["layer_scores"].items():
            layer_avg[L] += v
    n = len(skel["chunks"])
    layer_avg = {L: round(v / n, 3) for L, v in layer_avg.items()}
    out["layer_summary"] = {
        "layer_avg_across_chunks": layer_avg,
        "dominant_layer_distribution": dict(dom_counter),
    }

    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scored {n} chunks -> {out_path}")
    print(f"  dominant_layer distribution: {dict(dom_counter)}")
    print(f"  layer avg: {layer_avg}")


if __name__ == "__main__":
    main()
