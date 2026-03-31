"""Step 4: Filler Detection - フィラー検出。

Usage:
    python step04_filler_detect.py \
        --stt ../runs/{run}/step02_stt/stt_result.json \
        --vad ../runs/{run}/step03_vad/vad_result.json \
        --output ../runs/{run}/step04_filler_detect
"""

import argparse
import json
import os
import re
import sys


# フィラーパターン定義 (rough_edit 28パターン + talk-to-edit 補完)
FILLER_PATTERNS = {
    # 典型的なフィラー (hesitation)
    "えー": {"type": "hesitation", "confidence": 0.9},
    "えーと": {"type": "hesitation", "confidence": 0.95},
    "えーっと": {"type": "hesitation", "confidence": 0.95},
    "えっと": {"type": "hesitation", "confidence": 0.95},
    "あー": {"type": "hesitation", "confidence": 0.85},
    "あのー": {"type": "hedging", "confidence": 0.9},
    "あの": {"type": "hedging", "confidence": 0.7},
    "うーん": {"type": "thinking", "confidence": 0.9},
    "うん": {"type": "backchannel", "confidence": 0.6},
    # ぼかし表現 (hedging)
    "まあ": {"type": "hedging", "confidence": 0.7},
    "まー": {"type": "hedging", "confidence": 0.8},
    "そのー": {"type": "hedging", "confidence": 0.85},
    "その": {"type": "hedging", "confidence": 0.5},
    "なんか": {"type": "hedging", "confidence": 0.65},
    "やっぱ": {"type": "hedging", "confidence": 0.5},
    "ちょっと": {"type": "hedging", "confidence": 0.4},
    "こう": {"type": "hedging", "confidence": 0.5},
    # 対話的アーティファクト (backchannel / turn_taking)
    "どうぞ": {"type": "turn_taking", "confidence": 0.5},
    "はいはい": {"type": "backchannel", "confidence": 0.7},
    "そうそう": {"type": "backchannel", "confidence": 0.6},
    "そうそうそう": {"type": "backchannel", "confidence": 0.75},
    "ね": {"type": "backchannel", "confidence": 0.4},
    "ねー": {"type": "backchannel", "confidence": 0.5},
    "はい": {"type": "backchannel", "confidence": 0.3},
    # 英語系フィラー
    "um": {"type": "hesitation", "confidence": 0.9},
    "uh": {"type": "hesitation", "confidence": 0.9},
    "ah": {"type": "hesitation", "confidence": 0.85},
    "well": {"type": "hedging", "confidence": 0.5},
}

FILLER_REGEX_PATTERNS = [
    (r"^[えエ][ーェ]+[とト]?$", "hesitation", 0.9),
    (r"^[あア][ーァ]+$", "hesitation", 0.85),
    (r"^[うウ][ーゥ]+[んン]?$", "thinking", 0.85),
    (r"^[そソ][のノ][ーォ]+$", "hedging", 0.85),
    (r"^[まマ][ーァ]+$", "hedging", 0.8),
]


def run_step(stt_result_path: str, vad_result_path: str, output_dir: str, config: dict = None) -> dict:
    """フィラー検出。"""
    os.makedirs(output_dir, exist_ok=True)

    print(f"[Step 4] Filler Detection")

    with open(stt_result_path, "r", encoding="utf-8") as f:
        stt_result = json.load(f)
    with open(vad_result_path, "r", encoding="utf-8") as f:
        vad_result = json.load(f)

    words = stt_result.get("words", [])
    sentences = stt_result.get("sentences", [])

    fillers = []

    for i, word in enumerate(words):
        text = word["text"].strip()
        if not text:
            continue

        filler_info = _detect_filler(text)
        if not filler_info:
            continue

        confidence = filler_info["confidence"]

        # 文脈調整: 文頭のフィラーは信頼度UP
        if _is_sentence_initial(word, sentences):
            confidence = min(1.0, confidence + 0.1)

        # 文脈調整: 前のwordとのギャップが大きい場合は信頼度UP
        if i > 0:
            gap_ms = word["start_ms"] - words[i - 1]["end_ms"]
            if gap_ms > 300:
                confidence = min(1.0, confidence + 0.05)

        fillers.append({
            "text": text,
            "type": filler_info["type"],
            "start_ms": word["start_ms"],
            "end_ms": word["end_ms"],
            "confidence": round(confidence, 3),
            "source": filler_info["source"],
            "word_id": word["id"],
        })

    # 連続フィラーをマージ (200ms以内)
    fillers = _merge_consecutive_fillers(fillers, max_gap_ms=200)

    # 統計
    type_counts = {}
    for f in fillers:
        t = f["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    result = {
        "fillers": fillers,
        "stats": {
            "total_fillers": len(fillers),
            "type_distribution": type_counts,
            "high_confidence": sum(1 for f in fillers if f["confidence"] >= 0.7),
        },
    }

    print(f"  fillers: {len(fillers)}")
    print(f"  types: {type_counts}")
    print(f"  high confidence (>=0.7): {result['stats']['high_confidence']}")

    output_path = os.path.join(output_dir, "fillers.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[Step 4] Done: {output_path}")
    return result


def _detect_filler(text: str) -> dict | None:
    """テキストがフィラーかどうか判定。"""
    # 完全一致
    if text in FILLER_PATTERNS:
        info = FILLER_PATTERNS[text]
        return {**info, "source": "pattern"}

    # 正規表現マッチ
    for pattern, ftype, conf in FILLER_REGEX_PATTERNS:
        if re.match(pattern, text):
            return {"type": ftype, "confidence": conf, "source": "regex"}

    return None


def _is_sentence_initial(word: dict, sentences: list) -> bool:
    """wordがsentenceの先頭かどうか。"""
    for s in sentences:
        word_ids = s.get("word_ids", [])
        if word_ids and word_ids[0] == word["id"]:
            return True
    return False


def _merge_consecutive_fillers(fillers: list, max_gap_ms: int = 200) -> list:
    """連続するフィラーをマージ。"""
    if len(fillers) <= 1:
        return fillers

    merged = [fillers[0].copy()]

    for f in fillers[1:]:
        last = merged[-1]
        gap = f["start_ms"] - last["end_ms"]

        if gap <= max_gap_ms and f["type"] == last["type"]:
            # マージ
            last["end_ms"] = f["end_ms"]
            last["text"] = f"{last['text']}{f['text']}"
            last["confidence"] = max(last["confidence"], f["confidence"])
        else:
            merged.append(f.copy())

    return merged


def main():
    parser = argparse.ArgumentParser(description="Step 4: Filler Detection")
    parser.add_argument("--stt", required=True, help="STT result JSON path")
    parser.add_argument("--vad", required=True, help="VAD result JSON path")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    run_step(args.stt, args.vad, args.output)


if __name__ == "__main__":
    main()
