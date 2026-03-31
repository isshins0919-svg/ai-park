"""Step 7: Cut Proposal - word timestampベースの無音圧縮 + フィラー/リテイク除去。

STTのword-level timestampを使い、単語間のgapが閾値を超える箇所でセグメント分割。
VADの arbitrary threshold (2000ms) は使わず、実際の発話タイミングだけで判断する。

Usage:
    python step07_cut_proposal.py \
        --stt ../runs/{run}/step02_stt/stt_result.json \
        --fillers ../runs/{run}/step04_filler_detect/fillers.json \
        --retakes ../runs/{run}/step05_retake_detect/retakes.json \
        --scenes ../runs/{run}/step06_scene_structure/scenes.json \
        --output ../runs/{run}/step07_cut_proposal
"""

import argparse
import json
import os


def run_step(
    stt_result_path: str,
    fillers_path: str,
    retakes_path: str,
    scenes_path: str,
    output_dir: str,
    config: dict = None,
) -> dict:
    """STTのword timestampベースで無音圧縮 + フィラー/リテイク除去。"""
    os.makedirs(output_dir, exist_ok=True)

    print(f"[Step 7] Cut Proposal (word-timestamp based)")

    stt_result = _load_json(stt_result_path)
    fillers = _load_json(fillers_path)
    retakes = _load_json(retakes_path)
    scenes = _load_json(scenes_path)

    words = stt_result.get("words", [])
    sentences = stt_result.get("sentences", [])
    sentence_map = {s["id"]: s for s in sentences}
    word_map = {w["id"]: w for w in words}

    cfg = config or {}
    max_gap_ms = cfg.get("max_gap_ms", 600)
    segment_padding_ms = cfg.get("segment_padding_ms", 50)
    filler_confidence_threshold = cfg.get("filler_confidence_threshold", 0.6)

    # --- Phase 1: 除去するword_idを特定 ---
    remove_word_ids = set()
    remove_reasons = {}

    # 1a. フィラー (confidence threshold以上のみ)
    filler_removed = 0
    for filler in fillers.get("fillers", []):
        if filler.get("confidence", 0) >= filler_confidence_threshold:
            wid = filler.get("word_id")
            if wid:
                remove_word_ids.add(wid)
                remove_reasons[wid] = f"filler:{filler.get('type', 'unknown')}"
                filler_removed += 1

    # 1b. リテイク (step05で検出済み)
    retake_removed_words = 0
    for retake in retakes.get("retakes", []):
        keep = retake.get("keep", "retry")
        if keep == "retry":
            ids_to_remove = retake.get("original_sentence_ids", [])
        else:
            ids_to_remove = retake.get("retry_sentence_ids", [])
        for sid in ids_to_remove:
            if sid in sentence_map:
                for wid in sentence_map[sid]["word_ids"]:
                    remove_word_ids.add(wid)
                    remove_reasons[wid] = "retake:step05"
                    retake_removed_words += 1

    # 1c. インラインリテイク ("--" パターン検出)
    inline_retake_count = 0
    for sent in sentences:
        text = sent.get("text", "")
        if "--" not in text:
            continue
        # "--" の前の部分が false start (言い直し前)
        dash_pos = text.index("--")
        chars_before = dash_pos
        word_ids = sent["word_ids"]
        # wordのテキストを積算して、dash_posまでのword群を特定
        char_count = 0
        split_idx = 0
        for i, wid in enumerate(word_ids):
            w = word_map.get(wid)
            if w:
                char_count += len(w["text"])
            if char_count >= chars_before:
                split_idx = i + 1
                break
        # split_idx までのwordが false start
        if split_idx > 0:
            for j in range(split_idx):
                wid = word_ids[j]
                if wid not in remove_word_ids:
                    remove_word_ids.add(wid)
                    remove_reasons[wid] = "retake:inline"
            inline_retake_count += 1
            print(f"  inline retake: {sent['id']} \"{text[:dash_pos]}\" (removed {split_idx} words)")

    # 1d. "--" マーカーword除去 (STTが "--" を独立wordとして出力する場合)
    dash_removed = 0
    for w in words:
        if w["text"].strip() in ("--", "-") and w["id"] not in remove_word_ids:
            remove_word_ids.add(w["id"])
            remove_reasons[w["id"]] = "marker:dash"
            dash_removed += 1

    print(f"  fillers removed: {filler_removed}")
    print(f"  retake words removed (step05): {retake_removed_words}")
    print(f"  inline retakes detected: {inline_retake_count}")
    print(f"  total words removed: {len(remove_word_ids)}")

    # --- Phase 2: 残りのword list ---
    remaining_words = [w for w in words if w["id"] not in remove_word_ids]
    print(f"  remaining words: {len(remaining_words)} / {len(words)}")

    # --- Phase 3: gapでクラスタリング + scene境界分割 ---
    # word_id → sentence_id → scene_id のマッピングを構築
    word_to_scene = _build_word_to_scene_map(words, sentences, sentence_map, scenes)
    clusters = _build_clusters(remaining_words, max_gap_ms, word_to_scene)
    print(f"  clusters: {len(clusters)}")

    # --- Phase 4: keep_segments構築 ---
    audio_duration_ms = _estimate_audio_duration(words, sentences)
    scene_list = scenes.get("scenes", [])

    keep_segments = []
    for i, cluster in enumerate(clusters):
        start_ms = max(0, cluster[0]["start_ms"] - segment_padding_ms)
        end_ms = min(audio_duration_ms, cluster[-1]["end_ms"] + segment_padding_ms)
        text = "".join(w["text"] for w in cluster)
        # クラスタの代表scene_idを先に付与
        cluster_scene = word_to_scene.get(cluster[0]["id"])
        keep_segments.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "text": text,
            "scene_id": cluster_scene,
        })

    # 隣接するsegmentが重なっていたらマージ（同一scene内のみ）
    keep_segments = _merge_adjacent_segments(keep_segments)

    # 短すぎるセグメントを隣接セグメントに統合
    # 動画編集の品質制約: 1秒未満 or 5文字以下のカットは視聴体験が悪い
    min_duration_ms = cfg.get("min_segment_duration_ms", 1000)
    min_chars = cfg.get("min_segment_chars", 5)
    keep_segments = _merge_short_segments(keep_segments, min_duration_ms, min_chars)

    # 末尾segmentのトリム（STT末尾word duration肥大化対策）
    keep_segments = _trim_trailing_silence(keep_segments, remaining_words)

    # scene_id 再計算（マージ後の中点ベース）
    for seg in keep_segments:
        seg["scene_id"] = _find_scene(seg, scene_list)

    # --- Stats ---
    kept_ms = sum(s["end_ms"] - s["start_ms"] for s in keep_segments)
    removed_ms = audio_duration_ms - kept_ms

    # remove_ranges (デバッグ用)
    remove_ranges = _build_remove_ranges(keep_segments, audio_duration_ms)

    result = {
        "keep_segments": keep_segments,
        "remove_ranges": remove_ranges,
        "stats": {
            "total_keep_segments": len(keep_segments),
            "total_remove_ranges": len(remove_ranges),
            "kept_duration_ms": kept_ms,
            "removed_duration_ms": removed_ms,
            "original_duration_ms": audio_duration_ms,
            "reduction_ratio": round(removed_ms / max(audio_duration_ms, 1), 3),
            "words_total": len(words),
            "words_removed": len(remove_word_ids),
            "words_kept": len(remaining_words),
            "config": {
                "max_gap_ms": max_gap_ms,
                "segment_padding_ms": segment_padding_ms,
                "filler_confidence_threshold": filler_confidence_threshold,
            },
        },
    }

    print(f"  keep segments: {len(keep_segments)}")
    print(f"  remove ranges: {len(remove_ranges)}")
    print(f"  kept: {kept_ms}ms / {audio_duration_ms}ms (removed {result['stats']['reduction_ratio']:.1%})")

    output_path = os.path.join(output_dir, "cut_proposal.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[Step 7] Done: {output_path}")
    return result


def _build_word_to_scene_map(
    words: list, sentences: list, sentence_map: dict, scenes: dict,
) -> dict:
    """word_id → scene_id のマッピングを構築。"""
    # sentence_id → scene_id
    sent_to_scene = {}
    for scene in scenes.get("scenes", []):
        for sid in scene.get("sentence_ids", []):
            sent_to_scene[sid] = scene["id"]

    # word_id → sentence_id → scene_id
    word_to_scene = {}
    for sent in sentences:
        scene_id = sent_to_scene.get(sent["id"])
        for wid in sent.get("word_ids", []):
            word_to_scene[wid] = scene_id

    return word_to_scene


def _build_clusters(words: list, max_gap_ms: int, word_to_scene: dict = None) -> list:
    """wordをgap閾値 + scene境界でクラスタリング。

    分割条件:
    1. 連続するword間のgapがmax_gap_ms超
    2. scene_idが変わった（話題の切れ目）
    """
    if not words:
        return []

    clusters = []
    current = [words[0]]

    for w in words[1:]:
        prev_end = current[-1]["end_ms"]
        gap = w["start_ms"] - prev_end

        # scene境界チェック
        scene_changed = False
        if word_to_scene:
            prev_scene = word_to_scene.get(current[-1]["id"])
            curr_scene = word_to_scene.get(w["id"])
            if prev_scene and curr_scene and prev_scene != curr_scene:
                scene_changed = True

        if gap > max_gap_ms or scene_changed:
            clusters.append(current)
            current = [w]
        else:
            current.append(w)

    if current:
        clusters.append(current)

    return clusters


def _merge_adjacent_segments(segments: list) -> list:
    """重なりのあるsegmentをマージ（同一scene内のみ）。

    scene境界で分割されたセグメントは、paddingで時間的に重なっていても
    マージしない。異なる話題を1カットにまとめないため。
    """
    if len(segments) <= 1:
        return segments

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        last = merged[-1]
        same_scene = (
            last.get("scene_id") is not None
            and seg.get("scene_id") is not None
            and last["scene_id"] == seg["scene_id"]
        )
        overlapping = seg["start_ms"] <= last["end_ms"]

        if overlapping and same_scene:
            # 同一scene内の重複 → マージ
            last["end_ms"] = max(last["end_ms"], seg["end_ms"])
            last["text"] = last["text"] + seg["text"]
        else:
            # 異なるsceneまたは離れている → 分離
            new_seg = seg.copy()
            if overlapping:
                # padding重複を解消: 中点で分割
                mid = (last["end_ms"] + new_seg["start_ms"]) // 2
                last["end_ms"] = mid
                new_seg["start_ms"] = mid
            merged.append(new_seg)

    return merged


def _merge_short_segments(
    segments: list,
    min_duration_ms: int = 1000,
    min_chars: int = 5,
) -> list:
    """短すぎるセグメントを隣接セグメントに統合する。

    動画編集の品質制約:
    - 1秒未満のカットは視聴体験が悪い (映像として不自然)
    - 5文字以下のテロップは情報量が少なく孤立して見える

    短いセグメントは前のセグメントに統合する。先頭セグメントが短い場合は
    後ろのセグメントに統合する。統合時はgapを埋めて連続させる。
    """
    if len(segments) <= 1:
        return segments

    # 複数パスで処理 (1回のマージで新たに短くなることはないが、安全のため)
    changed = True
    while changed:
        changed = False
        result = []
        i = 0
        while i < len(segments):
            seg = segments[i]
            duration_ms = seg["end_ms"] - seg["start_ms"]
            text_len = len(seg.get("text", ""))
            is_short = duration_ms < min_duration_ms or text_len < min_chars

            if is_short and result:
                # 前のセグメントに統合
                prev = result[-1]
                prev["end_ms"] = seg["end_ms"]
                prev["text"] = prev["text"] + seg["text"]
                changed = True
                print(f"  short merge: \"{seg['text']}\" ({duration_ms}ms/{text_len}字) -> merged into prev")
            elif is_short and not result and i + 1 < len(segments):
                # 先頭セグメントが短い場合、後ろに統合
                next_seg = segments[i + 1]
                next_seg["start_ms"] = seg["start_ms"]
                next_seg["text"] = seg["text"] + next_seg["text"]
                changed = True
                print(f"  short merge: \"{seg['text']}\" ({duration_ms}ms/{text_len}字) -> merged into next")
            else:
                result.append(seg.copy())
            i += 1
        segments = result

    return segments


def _trim_trailing_silence(keep_segments: list, remaining_words: list) -> list:
    """最後のsegmentの末尾トリム（STT末尾word duration肥大化対策）。

    ElevenLabsのSTTは録音末尾の無音を最後のwordに含めることがある。
    wordデータは触らず、segmentレベルで末尾をカットする。
    """
    if not keep_segments or not remaining_words:
        return keep_segments

    last_seg = keep_segments[-1]
    # このsegment内の最後のwordを探す
    words_in_seg = [
        w for w in remaining_words
        if w["start_ms"] < last_seg["end_ms"] and w["end_ms"] > last_seg["start_ms"]
    ]
    if len(words_in_seg) < 2:
        return keep_segments

    last_word = words_in_seg[-1]
    second_last = words_in_seg[-2]

    # 最後のwordのdurationが前のwordの3倍以上なら異常とみなす
    last_dur = last_word["end_ms"] - last_word["start_ms"]
    prev_dur = second_last["end_ms"] - second_last["start_ms"]
    if prev_dur > 0 and last_dur > prev_dur * 3 and last_dur > 500:
        # 最後のwordのstart_ms + 妥当なduration でカット
        trimmed_end = last_word["start_ms"] + min(prev_dur * 2, 400) + 50
        if trimmed_end < last_seg["end_ms"]:
            trimmed_ms = last_seg["end_ms"] - trimmed_end
            last_seg["end_ms"] = trimmed_end
            print(f"  trailing trim: -{trimmed_ms}ms (last word dur {last_dur}ms -> capped)")

    return keep_segments


def _build_remove_ranges(keep_segments: list, audio_duration_ms: int) -> list:
    """keep_segmentsの間をremove_rangesとして構築（デバッグ・ログ用）。"""
    ranges = []
    prev_end = 0
    for seg in keep_segments:
        if seg["start_ms"] > prev_end:
            ranges.append({
                "start_ms": prev_end,
                "end_ms": seg["start_ms"],
                "duration_ms": seg["start_ms"] - prev_end,
                "reason": "gap",
            })
        prev_end = seg["end_ms"]

    if prev_end < audio_duration_ms:
        ranges.append({
            "start_ms": prev_end,
            "end_ms": audio_duration_ms,
            "duration_ms": audio_duration_ms - prev_end,
            "reason": "trailing_silence",
        })

    return ranges


def _estimate_audio_duration(words: list, sentences: list) -> int:
    """音声の総尺をword/sentenceから推定。"""
    candidates = []
    if words:
        candidates.append(words[-1]["end_ms"])
    if sentences:
        candidates.append(sentences[-1]["end_ms"])
    if candidates:
        return max(candidates) + 500  # 末尾に余白
    return 0


def _find_scene(segment: dict, scenes: list) -> str | None:
    """segmentが属するscene_idを特定。"""
    mid_ms = (segment["start_ms"] + segment["end_ms"]) // 2
    for scene in scenes:
        s_start = scene.get("start_ms", 0)
        s_end = scene.get("end_ms", 0)
        if s_start <= mid_ms <= s_end:
            return scene["id"]
    return None


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Step 7: Cut Proposal")
    parser.add_argument("--stt", required=True, help="STT result JSON path")
    parser.add_argument("--fillers", required=True, help="Fillers JSON path")
    parser.add_argument("--retakes", required=True, help="Retakes JSON path")
    parser.add_argument("--scenes", required=True, help="Scenes JSON path")
    parser.add_argument("--output", required=True, help="Output directory")
    # VADは不要だが互換性のため受け付ける
    parser.add_argument("--vad", help="(unused) VAD result JSON path")
    args = parser.parse_args()

    run_step(args.stt, args.fillers, args.retakes, args.scenes, args.output)


if __name__ == "__main__":
    main()
