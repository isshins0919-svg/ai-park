"""Step 2: STT - ElevenLabs word-level 文字起こし。

Usage:
    python step02_stt.py --audio ../runs/{run}/step01_preprocess/audio.wav --output ../runs/{run}/step02_stt
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from shared.stt_elevenlabs import transcribe_audio, stt_result_to_words


def run_step(audio_path: str, output_dir: str) -> dict:
    """STT実行 + sentence構築。"""
    os.makedirs(output_dir, exist_ok=True)

    print(f"[Step 2] STT: {audio_path}")

    # STT実行
    raw_result = transcribe_audio(audio_path)

    # words変換
    words = stt_result_to_words(raw_result)
    print(f"  words: {len(words)}")

    # sentence構築
    sentences = _build_sentences(raw_result, words)
    print(f"  sentences: {len(sentences)}")

    result = {
        "words": words,
        "sentences": sentences,
        "raw_text": raw_result.get("text", ""),
    }

    output_path = os.path.join(output_dir, "stt_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[Step 2] Done: {output_path}")
    return result


def _build_sentences(raw_result: dict, words: list) -> list:
    """utterancesまたは句読点からsentencesを構築。"""
    sentences = []

    # utterancesがある場合はそれを使用
    utterances = raw_result.get("utterances", [])
    if utterances:
        for i, utt in enumerate(utterances):
            utt_text = utt.get("text", "").strip()
            if not utt_text:
                continue

            # utterance内のwordsを特定
            utt_words = _find_words_in_range(
                words,
                int(utt.get("start", 0) * 1000),
                int(utt.get("end", 0) * 1000),
            )

            sentences.append({
                "id": f"sent_{i:04d}",
                "text": utt_text,
                "start_ms": utt_words[0]["start_ms"] if utt_words else 0,
                "end_ms": utt_words[-1]["end_ms"] if utt_words else 0,
                "word_ids": [w["id"] for w in utt_words],
            })
    else:
        # フォールバック: 句読点で分割
        sentences = _split_by_punctuation(words)

    return sentences


def _find_words_in_range(words: list, start_ms: int, end_ms: int) -> list:
    """指定範囲内のwordsを抽出。"""
    return [w for w in words if w["end_ms"] > start_ms and w["start_ms"] < end_ms]


def _split_by_punctuation(words: list) -> list:
    """句読点でsentencesに分割 (フォールバック)。"""
    if not words:
        return []

    punct_pattern = re.compile(r"[。！？\.!\?]$")
    sentences = []
    current_words = []

    for w in words:
        current_words.append(w)

        if punct_pattern.search(w["text"]) or len(current_words) >= 30:
            text = "".join(cw["text"] for cw in current_words)
            sentences.append({
                "id": f"sent_{len(sentences):04d}",
                "text": text,
                "start_ms": current_words[0]["start_ms"],
                "end_ms": current_words[-1]["end_ms"],
                "word_ids": [cw["id"] for cw in current_words],
            })
            current_words = []

    # 残り
    if current_words:
        text = "".join(cw["text"] for cw in current_words)
        sentences.append({
            "id": f"sent_{len(sentences):04d}",
            "text": text,
            "start_ms": current_words[0]["start_ms"],
            "end_ms": current_words[-1]["end_ms"],
            "word_ids": [cw["id"] for cw in current_words],
        })

    return sentences


def main():
    parser = argparse.ArgumentParser(description="Step 2: STT")
    parser.add_argument("--audio", required=True, help="Input audio path (WAV)")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    run_step(args.audio, args.output)


if __name__ == "__main__":
    main()
