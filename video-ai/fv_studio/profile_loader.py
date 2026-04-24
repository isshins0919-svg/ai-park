"""KOSURI 商品プロファイル ローダー.

`.claude/clients/{client}/{product}/kosuri-profile.yaml` を読み込んで、
FV自動生成に必要なペルソナ・フック優先度・薬機法NG表現を提供する。

DPro勝ちFVパターンのRAG検索（`data/dpro_fv_patterns.json`）も併設し、
生成時にN1×商品プロファイルに意味的に近い勝ち広告TOP3をプロンプト注入する。
"""
from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:
    yaml = None
    _YAML_AVAILABLE = False

_FV_STUDIO_DIR = Path(__file__).resolve().parent
_VOYAGE_ROOT = _FV_STUDIO_DIR.parent.parent

# Cloud Run: デプロイ時に fv_studio/clients/ に一時コピーされる
# ローカル: 一進VOYAGE号/.claude/clients/ を参照
_LOCAL_CLIENTS_DIR = _FV_STUDIO_DIR / "clients"
_CLIENTS_DIR = _LOCAL_CLIENTS_DIR if _LOCAL_CLIENTS_DIR.exists() else _VOYAGE_ROOT / ".claude" / "clients"


def _split_key(product_key: str) -> Optional[tuple[str, str]]:
    if not product_key or "_" not in product_key:
        return None
    client, _, product = product_key.partition("_")
    if not client or not product:
        return None
    return client, product


def _profile_path(product_key: str) -> Optional[Path]:
    sp = _split_key(product_key)
    if not sp:
        return None
    client, product = sp
    p = _CLIENTS_DIR / client / product / "kosuri-profile.yaml"
    return p if p.exists() else None


def _history_path(product_key: str) -> Optional[Path]:
    sp = _split_key(product_key)
    if not sp:
        return None
    client, product = sp
    d = _CLIENTS_DIR / client / product
    if not d.exists():
        return None
    return d / "kosuri-history.md"


def list_available_products() -> list[dict]:
    """利用可能な商品プロファイル一覧（UIのセレクタ用）。"""
    results: list[dict] = []
    if not _CLIENTS_DIR.exists() or not _YAML_AVAILABLE:
        return results
    for client_dir in sorted(_CLIENTS_DIR.iterdir()):
        if not client_dir.is_dir():
            continue
        for product_dir in sorted(client_dir.iterdir()):
            if not product_dir.is_dir():
                continue
            yml = product_dir / "kosuri-profile.yaml"
            if not yml.exists():
                continue
            data = load_profile(f"{client_dir.name}_{product_dir.name}")
            if not data:
                continue
            results.append({
                "product_key": data.get("product_key"),
                "client": data.get("client"),
                "product_name": data.get("product_name"),
            })
    return results


def load_profile(product_key: str) -> Optional[dict]:
    if not _YAML_AVAILABLE:
        return None
    p = _profile_path(product_key)
    if not p:
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[profile_loader] failed to load {p}: {e}")
        return None


def build_profile_injection(profile: Optional[dict]) -> str:
    if not profile:
        return ""
    persona = profile.get("persona", {}) or {}
    product = profile.get("product", {}) or {}
    reg = profile.get("regulation", {}) or {}
    hooks = profile.get("hooks", {}) or {}
    winning = profile.get("winning_copies", []) or []
    n1 = profile.get("n1", {}) or {}

    parts = ["", "━━━━━━━━━━━━━━━━━━━━━━━━━", "【商品プロファイル（最優先で従え）】"]
    parts.append(f"商品名: {profile.get('product_name', '不明')}")
    parts.append(
        f"ペルソナ: {persona.get('age_range', '')} {persona.get('gender', '')} — "
        f"{persona.get('role', '')}"
    )
    if persona.get("pain_points"):
        parts.append("悩み軸: " + " / ".join(persona["pain_points"]))

    if n1:
        parts.append("")
        parts.append("【N1ターゲット（1カット目で刺せ）】")
        if n1.get("scene"):
            parts.append(f"  ▸ シーン: {n1['scene']}")
        if n1.get("emotion"):
            parts.append(f"  ▸ 感情軸: {n1['emotion']}")
        if n1.get("visual_hook_emotion"):
            parts.append(f"  ▸ ビジュアルフック: {n1['visual_hook_emotion']}")
        if n1.get("target_moment"):
            parts.append(f"  ▸ ターゲットモーメント: {n1['target_moment']}")

    if product.get("visual_subjects"):
        parts.append("")
        parts.append("視覚要素候補: " + " / ".join(product["visual_subjects"]))
    if product.get("key_authorities"):
        parts.append("権威要素（V10/V13で使え）: " + " / ".join(product["key_authorities"]))

    if reg.get("yakkihou_level"):
        parts.append("")
        parts.append(f"【薬機法レベル: {reg['yakkihou_level']}】")
    if reg.get("ng_expressions"):
        parts.append("NG表現（テロップ/コピーで絶対使うな）:")
        for ng in reg["ng_expressions"]:
            parts.append(f"  ✗ {ng}")
    if reg.get("safe_alternatives"):
        parts.append("安全な言い換え: " + " / ".join(reg["safe_alternatives"]))

    if hooks.get("priority"):
        parts.append("")
        parts.append(
            f"【最優先使用フック】{', '.join(hooks['priority'])} を10パターンのうち最低4つ採用"
        )
    if hooks.get("avoid"):
        parts.append(
            f"【使用禁止フック】{', '.join(hooks['avoid'])} はこの商品で1つも使うな"
        )

    if winning:
        parts.append("")
        parts.append("【過去勝ちコピー（トーン参考）】")
        for c in winning[:5]:
            parts.append(f"  ✓ {c}")
    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━")

    base = "\n".join(parts)

    # DPro勝ちFVパターンRAG（環境変数 KOSURI_DPRO_RAG=0 で無効化可）
    if os.environ.get("KOSURI_DPRO_RAG", "1") != "0":
        rag = build_dpro_rag_injection(profile, top_k=3)
        if rag:
            base += "\n" + rag
    return base


def filter_hook_patterns(hook_patterns: list[dict], profile: Optional[dict]) -> list[dict]:
    if not profile:
        return hook_patterns
    avoid = set((profile.get("hooks", {}) or {}).get("avoid", []) or [])
    if not avoid:
        return hook_patterns
    return [p for p in hook_patterns if p.get("id") not in avoid]


def build_image_prompt_suffix(profile: Optional[dict]) -> str:
    if not profile:
        return ""
    parts: list[str] = []
    persona = profile.get("persona", {}) or {}
    hooks_cfg = profile.get("hooks", {}) or {}

    if hooks_cfg.get("model_age_override") == "senior":
        parts.append("model MUST be senior woman aged 55-65, grey or natural hair, NOT young")
    elif persona.get("age_range"):
        parts.append(f"model age range: {persona['age_range']}")

    suffix = profile.get("image_prompt_suffix", "")
    if suffix:
        parts.append(suffix)
    return ", ".join(parts)


def append_history(product_key: str, entry: dict) -> None:
    p = _history_path(product_key)
    if not p:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    hook_ids = entry.get("hook_ids") or []
    lines = [
        f"## {ts} (job={entry.get('job_id', '')})",
        f"- user_prompt: {str(entry.get('user_prompt', ''))[:200]}",
        f"- video_info: target={entry.get('target', '')} / problem={entry.get('problem', '')}",
        f"- generated: {entry.get('count', 0)}本",
        f"- hooks_used: {', '.join(hook_ids) if hook_ids else '(なし)'}",
        "",
    ]
    try:
        if p.exists():
            existing = p.read_text(encoding="utf-8")
        else:
            existing = f"# KOSURI生成履歴 — {entry.get('product_name', product_key)}\n\n"
        p.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"[profile_loader] append_history error: {e}")


# ─────────────────────────────────────────────────────────────
# DPro勝ちFVパターン RAG
# ─────────────────────────────────────────────────────────────

_DPRO_RAG_PATH = _FV_STUDIO_DIR / "data" / "dpro_fv_patterns.json"
_DPRO_CACHE: dict[str, Any] = {}  # { patterns: list, meta: dict, query_vec_by_key: {} }


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def _load_dpro_db() -> Optional[dict[str, Any]]:
    if "patterns" in _DPRO_CACHE:
        return _DPRO_CACHE
    if not _DPRO_RAG_PATH.exists():
        return None
    try:
        data = json.loads(_DPRO_RAG_PATH.read_text(encoding="utf-8"))
        _DPRO_CACHE["patterns"] = data.get("patterns", [])
        _DPRO_CACHE["model"] = data.get("model")
        _DPRO_CACHE["dim"] = data.get("dim")
        _DPRO_CACHE["query_vec_by_key"] = {}
        return _DPRO_CACHE
    except Exception as e:
        print(f"[profile_loader] dpro db load failed: {e}")
        return None


def _build_query_text(profile: dict) -> str:
    persona = profile.get("persona", {}) or {}
    n1 = profile.get("n1", {}) or {}
    parts = [
        f"商品: {profile.get('product_name', '')}",
        f"ペルソナ: {persona.get('role', '')} {persona.get('age_range', '')}",
    ]
    if n1.get("scene"):
        parts.append(f"シーン: {n1['scene']}")
    if n1.get("emotion"):
        parts.append(f"感情: {n1['emotion']}")
    if n1.get("visual_hook_emotion"):
        parts.append(f"ビジュアルフック: {n1['visual_hook_emotion']}")
    if pp := persona.get("pain_points"):
        parts.append("悩み: " + " / ".join(pp))
    return " / ".join(parts)


def _embed_query(text: str) -> Optional[list[float]]:
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except ImportError:
        return None
    api_key = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        dim = _DPRO_CACHE.get("dim") or 3072
        r = client.models.embed_content(
            model=_DPRO_CACHE.get("model") or "gemini-embedding-2-preview",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=dim),
        )
        return list(r.embeddings[0].values)
    except Exception as e:
        print(f"[profile_loader] query embed failed: {str(e)[:150]}")
        return None


def search_dpro_patterns(profile: Optional[dict], top_k: int = 3) -> list[dict[str, Any]]:
    """商品プロファイル（N1+ペルソナ）と意味的に近いDPro勝ち広告TOP-kを返す."""
    if not profile:
        return []
    db = _load_dpro_db()
    if not db or not db.get("patterns"):
        return []
    product_key = profile.get("product_key", "")

    # クエリembedキャッシュ
    qvec_cache: dict[str, list[float]] = _DPRO_CACHE.setdefault("query_vec_by_key", {})
    qvec = qvec_cache.get(product_key)
    if qvec is None:
        qtext = _build_query_text(profile)
        qvec = _embed_query(qtext)
        if qvec:
            qvec_cache[product_key] = qvec
    if not qvec:
        return []

    # コサイン類似度ランキング（自ジャンルに+10%ブースト=同ジャンル優先）
    own_genre = (profile.get("product", {}) or {}).get("category_key", "")
    scored: list[tuple[float, dict]] = []
    for p in db["patterns"]:
        emb = p.get("embedding")
        if not emb:
            continue
        score = _cosine(qvec, emb)
        # cost_differenceが大きい=勝ちが強いので軽く重みづけ
        cost = p.get("cost_difference", 0) or 0
        cost_boost = min(0.05, math.log10(max(cost, 1)) / 200.0)
        scored.append((score + cost_boost, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [{"score": round(s, 4), **p} for s, p in scored[:top_k]]
    return top


def build_dpro_rag_injection(profile: Optional[dict], top_k: int = 3) -> str:
    """DPro勝ちFVパターン TOP-k をプロンプト注入用テキストに変換."""
    hits = search_dpro_patterns(profile, top_k=top_k)
    if not hits:
        return ""
    lines = ["", "━━━━━━━━━━━━━━━━━━━━━━━━━",
             f"【DPro勝ちFVパターン TOP{len(hits)}（意味的類似・構造参考）】",
             "※ 以下は実在の高パフォーマンス広告の冒頭構造。そのままコピーせず、"
             "「冒頭で何を見せ／何を言うか」の型を参考にする。"]
    for i, h in enumerate(hits, 1):
        cost = h.get("cost_difference", 0) or 0
        cost_m = cost / 1_000_000
        hook = h.get("ad_start_sentence") or (h.get("ad_all_sentence") or "")[:80]
        duration = h.get("duration", "")
        app = h.get("app_name", "")
        genre = h.get("genre_name", "")
        score = h.get("score", 0)
        lines.append(
            f"  {i}. [¥{cost_m:.1f}M / sim={score:.2f} / {genre} / {app} {duration}]"
        )
        lines.append(f"     FV冒頭: 「{hook}」")
        # ナレーション冒頭120字で構成を学ばせる
        narr = (h.get("ad_all_sentence") or "")[:120]
        if narr:
            lines.append(f"     構成: {narr}…")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


def load_recent_history(product_key: str, limit: int = 5) -> list[str]:
    p = _history_path(product_key)
    if not p or not p.exists():
        return []
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return []
    blocks = re.split(r"^## ", text, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if b.strip()]
    return blocks[-limit:]
