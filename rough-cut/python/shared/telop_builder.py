"""テロップ生成。

BudouX + DP で自然な改行 + 禁則処理。
句読点は表示テキストから除去する。
text_rules による正規化 (列挙数字変換、誤認識補正) を適用する。

コピー元: omakasekun-worker/pipelines/shared/telop/builder.py
"""

import re
from typing import Any, Dict, List, Optional

from shared.budoux_layout import split_pages


# 表示時に除去する句読点
_PUNCT_TO_REMOVE = re.compile(r"[。、！？!?,.]")

# 漢数字→アラビア数字の列挙パターン
_KANJI_ENUM_PATTERNS = [
    (re.compile(r"一つ目"), "1つ目"),
    (re.compile(r"二つ目"), "2つ目"),
    (re.compile(r"三つ目"), "3つ目"),
    (re.compile(r"四つ目"), "4つ目"),
    (re.compile(r"五つ目"), "5つ目"),
    (re.compile(r"六つ目"), "6つ目"),
    (re.compile(r"七つ目"), "7つ目"),
    (re.compile(r"八つ目"), "8つ目"),
    (re.compile(r"九つ目"), "9つ目"),
    (re.compile(r"十つ目"), "10つ目"),
    (re.compile(r"一個目"), "1個目"),
    (re.compile(r"二個目"), "2個目"),
    (re.compile(r"三個目"), "3個目"),
    (re.compile(r"一番目"), "1番目"),
    (re.compile(r"二番目"), "2番目"),
    (re.compile(r"三番目"), "3番目"),
    # 「一つ」「二つ」(列挙の文脈)
    (re.compile(r"一つの"), "1つの"),
    (re.compile(r"二つの"), "2つの"),
    (re.compile(r"三つの"), "3つの"),
]


def build_telop_pages(
    transcript: str,
    cut_id: str,
    max_chars_per_line: int = 12,
    max_lines_per_page: int = 2,
    text_rules: Optional[Dict[str, Any]] = None,
    dp_overrides: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """transcript を TelopPage[] に変換。

    Args:
        transcript: カットのトランスクリプト
        cut_id: カットID（ページIDのプレフィックスに使用）
        max_chars_per_line: 1行の最大文字数
        max_lines_per_page: 1ページの最大行数
        text_rules: テキスト正規化ルール (project config の text_rules セクション)
        dp_overrides: BudouX DPペナルティのオーバーライド (templates/*.yaml の dp セクション)

    Returns:
        TelopPage[] 互換の dict リスト
    """
    if not transcript.strip():
        return []

    raw_pages = split_pages(
        text=transcript,
        max_chars_per_line=max_chars_per_line,
        max_lines_per_page=max_lines_per_page,
        dp_overrides=dp_overrides,
    )

    pages = []
    for i, raw in enumerate(raw_pages):
        # 句読点を除去した表示用テキスト
        cleaned_lines = [_remove_punctuation(line) for line in raw["lines"]]
        # text_rules による正規化
        if text_rules:
            cleaned_lines = [_normalize_text(line, text_rules) for line in cleaned_lines]
        # 空行を除外
        cleaned_lines = [line for line in cleaned_lines if line.strip()]
        if not cleaned_lines:
            continue

        page = {
            "id": f"{cut_id}_p{i:02d}",
            "lines": cleaned_lines,
        }
        pages.append(page)

    return pages


def _remove_punctuation(text: str) -> str:
    """表示用テキストから句読点を除去。"""
    return _PUNCT_TO_REMOVE.sub("", text).strip()


def _normalize_text(text: str, text_rules: Dict[str, Any]) -> str:
    """text_rules に基づいてテキストを正規化。

    適用順序:
    1. 共通正規化 (normalize_numbers=true 時)
       - 漢数字→算用数字
       - 固有名詞の正式表記
    2. corrections (誤認識補正) - 個別の修正
    3. enumeration_style (列挙数字変換) - 漢数字→アラビア数字 (旧互換)
    """
    # 1. 共通正規化
    if text_rules.get("normalize_numbers", True):
        text = _normalize_kanji_numbers(text)
    if text_rules.get("normalize_proper_nouns", True):
        text = _normalize_proper_nouns(text)

    # 2. corrections: STT 誤認識の自動置換
    corrections = text_rules.get("corrections", {})
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    # 3. enumeration_style: 列挙数字の変換 (旧互換)
    style = text_rules.get("enumeration_style", "as_is")
    if style == "arabic":
        for pattern, replacement in _KANJI_ENUM_PATTERNS:
            text = pattern.sub(replacement, text)

    return text


# ── 漢数字→算用数字 変換 ──────────────────────────────────

try:
    from kanjize import kanji2number as _kanji2number
    _HAS_KANJIZE = True
except ImportError:
    _HAS_KANJIZE = False

# 漢数字の文字セット
_KANJI_NUM_CHARS = "〇零一二三四五六七八九十百千万億兆"

# 助数詞リスト (漢数字の直後に来る文字列)
_COUNTER_SUFFIXES_STR = (
    "円|個|本|人|回|件|枚|台|匹|頭|冊|杯|"
    "度|時|分|秒|時間|日|週間|ヶ月|か月|カ月|年|"
    "パーセント|%|倍|"
    "フォロワー|名|社|店|"
    "ぐらい|くらい|以上|以下|以内|未満"
)

# 正規表現: 漢数字列 + 助数詞 を一括マッチ
_KANJI_NUM_PATTERN = re.compile(
    rf"([{_KANJI_NUM_CHARS}]+)({_COUNTER_SUFFIXES_STR})"
)


def _normalize_kanji_numbers(text: str) -> str:
    """テキスト中の漢数字+助数詞パターンを算用数字に変換。

    「三十八度」→「38度」、「千九百円」→「1,900円」、「百個」→「100個」
    「一万フォロワー」→「1万フォロワー」、「十六万フォロワー」→「16万フォロワー」
    助数詞が後続しない漢数字は変換しない (「一般」「三角」等の誤変換を防ぐ)。
    kanjize ライブラリを使用して正確にパース。
    """
    if not _HAS_KANJIZE:
        return text

    def _replace(m: re.Match) -> str:
        kanji_str = m.group(1)
        suffix = m.group(2)
        try:
            num = _kanji2number(kanji_str)
        except (ValueError, KeyError):
            return m.group(0)  # パース失敗→そのまま

        num_str = _format_number(num)
        return num_str + suffix

    return _KANJI_NUM_PATTERN.sub(_replace, text)


def _format_number(num: int) -> str:
    """数値を日本語表記に適したフォーマットにする。

    万/億/兆の単位は漢字で残す (「10000」ではなく「1万」)。
    1万未満はそのまま数字。1万以上はN万/N億表記。
    """
    if num >= 1_0000_0000_0000:  # 兆
        cho = num // 1_0000_0000_0000
        remainder = num % 1_0000_0000_0000
        if remainder == 0:
            return f"{cho}兆"
        oku = remainder // 1_0000_0000
        return f"{cho}兆{oku}億" if oku else f"{cho}兆"

    if num >= 1_0000_0000:  # 億
        oku = num // 1_0000_0000
        remainder = num % 1_0000_0000
        if remainder == 0:
            return f"{oku}億"
        man = remainder // 1_0000
        return f"{oku}億{man}万" if man else f"{oku}億"

    if num >= 1_0000:  # 万
        man = num // 1_0000
        remainder = num % 1_0000
        if remainder == 0:
            return f"{man}万"
        return f"{man}万{remainder}"

    return str(num)


# ── 固有名詞の正式表記 ──────────────────────────────────

_PROPER_NOUN_MAP = {
    "YOUTUBE": "YouTube",
    "Youtube": "YouTube",
    "youtube": "YouTube",
    "INSTAGRAM": "Instagram",
    "instagram": "Instagram",
    "TIKTOK": "TikTok",
    "Tiktok": "TikTok",
    "tiktok": "TikTok",
    "TWITTER": "X",
    "twitter": "X",
    "Twitter": "X",
    "LINE": "LINE",  # そのまま (正式)
}


def _normalize_proper_nouns(text: str) -> str:
    """固有名詞を正式表記に変換。"""
    for wrong, correct in _PROPER_NOUN_MAP.items():
        if wrong in text:
            text = text.replace(wrong, correct)
    return text


def build_voice_data(
    keep_segments: list,
    words: list,
    telop_pages_by_cut: dict,
) -> Dict[str, Any]:
    """VoiceData を構築。word timingは秒単位 (Remotion Telop互換)。"""
    cuts = []

    for i, seg in enumerate(keep_segments):
        cut_id = f"cut_{i + 1:03d}"

        # この区間のwordsを抽出
        words_in_range = [
            w for w in words
            if w["end_ms"] > seg["start_ms"] and w["start_ms"] < seg["end_ms"]
        ]

        # word timingをカット相対時間に変換（秒単位）
        voice_words = []
        for w in words_in_range:
            voice_words.append({
                "text": w["text"],
                "start": max(0, (w["start_ms"] - seg["start_ms"])) / 1000.0,
                "end": max(0, (w["end_ms"] - seg["start_ms"])) / 1000.0,
            })

        # telopマッピング（句読点除去後のテキストでマッチング）
        pages = telop_pages_by_cut.get(cut_id, [])
        telops = _map_pages_to_telops(pages, voice_words, words_in_range)

        cuts.append({
            "id": cut_id,
            "narration": seg.get("text", ""),
            "voice": {
                "duration_ms": seg["end_ms"] - seg["start_ms"],
                "words": voice_words,
            },
            "telops": telops,
        })

    return {"version": "1.0", "cuts": cuts}


def _map_pages_to_telops(
    pages: list,
    voice_words: list,
    words_in_range: list,
) -> list:
    """TelopPage[] を VoiceTelop[] にマッピング。

    句読点除去後のテロップテキストと、元テキスト（句読点あり）の
    word indices を対応付ける。
    """
    if not pages or not words_in_range:
        return []

    telops = []

    # 句読点除去した元テキストでマッチング
    full_text_raw = "".join(w["text"] for w in words_in_range)
    full_text_clean = _remove_punctuation(full_text_raw)

    # 元テキストの文字位置 → word index マッピング
    char_to_word_idx: Dict[int, int] = {}
    char_pos = 0
    for wi, w in enumerate(words_in_range):
        for _ in w["text"]:
            char_to_word_idx[char_pos] = wi
            char_pos += 1

    # クリーンテキストの文字位置 → 元テキストの文字位置マッピング
    clean_to_raw: Dict[int, int] = {}
    clean_pos = 0
    for raw_pos, ch in enumerate(full_text_raw):
        if not _PUNCT_TO_REMOVE.match(ch):
            clean_to_raw[clean_pos] = raw_pos
            clean_pos += 1

    page_clean_offset = 0
    for page in pages:
        page_text = "".join(page["lines"])
        page_len = len(page_text)

        # クリーンテキスト内での位置を探す
        match_pos = full_text_clean.find(page_text, page_clean_offset)
        if match_pos == -1:
            match_pos = page_clean_offset

        # word indices を特定（クリーン → raw → word_idx）
        word_indices = set()
        for ci in range(match_pos, min(match_pos + page_len, len(full_text_clean))):
            raw_pos = clean_to_raw.get(ci)
            if raw_pos is not None and raw_pos in char_to_word_idx:
                word_indices.add(char_to_word_idx[raw_pos])

        sorted_indices = sorted(word_indices)

        # segments（行単位）
        segments = []
        line_clean_offset = match_pos
        for line_text in page["lines"]:
            line_len = len(line_text)
            line_word_indices = set()
            for ci in range(line_clean_offset, min(line_clean_offset + line_len, len(full_text_clean))):
                raw_pos = clean_to_raw.get(ci)
                if raw_pos is not None and raw_pos in char_to_word_idx:
                    line_word_indices.add(char_to_word_idx[raw_pos])
            segments.append({
                "text": line_text,
                "word_indices": sorted(line_word_indices),
            })
            line_clean_offset += line_len

        telops.append({
            "id": page["id"],
            "text": page_text,
            "word_indices": sorted_indices,
            "segments": segments,
        })

        page_clean_offset = match_pos + page_len

    return telops
