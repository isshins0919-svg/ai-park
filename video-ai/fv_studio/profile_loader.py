"""KOSURI 商品プロファイル ローダー.

`.claude/clients/{client}/{product}/kosuri-profile.yaml` を読み込んで、
FV自動生成に必要なペルソナ・フック優先度・薬機法NG表現を提供する。
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

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

    parts = ["", "━━━━━━━━━━━━━━━━━━━━━━━━━", "【商品プロファイル（最優先で従え）】"]
    parts.append(f"商品名: {profile.get('product_name', '不明')}")
    parts.append(
        f"ペルソナ: {persona.get('age_range', '')} {persona.get('gender', '')} — "
        f"{persona.get('role', '')}"
    )
    if persona.get("pain_points"):
        parts.append("悩み軸: " + " / ".join(persona["pain_points"]))
    if product.get("visual_subjects"):
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

    return "\n".join(parts)


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
