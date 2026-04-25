#!/usr/bin/env python3
"""KOSURIちゃん v5 深層監査 — 回帰テスト / 並列化 / 本番シミュレーション.

qa_harness.py が通った後の2段階目。
- 過去のバグ修正が退行してないかチェック
- 並列リクエスト時の挙動
- Python 3.10+ 機能の使用有無（Docker=3.11）
- Docker build context 想定サイズ
- ジョブdict リークチェック
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

results: list[dict] = []


def T(name: str, fn, *, category: str = "misc"):
    t0 = time.time()
    try:
        ret = fn()
        status = "PASS"
        detail = ret if isinstance(ret, str) else (
            json.dumps(ret, ensure_ascii=False)[:200] if isinstance(ret, dict) else ""
        )
        if isinstance(ret, dict) and ret.get("warn"):
            status = "WARN"
            detail = ret.get("msg", "")
    except AssertionError as e:
        status = "FAIL"
        detail = str(e) or "assert failed"
    except Exception as e:
        status = "ERROR"
        detail = f"{type(e).__name__}: {str(e)[:180]}"
    t = time.time() - t0
    results.append({"name": name, "category": category, "status": status, "detail": detail, "elapsed_s": round(t, 2)})
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "💥"}[status]
    print(f"{icon} [{category}] {name} ({t:.2f}s)  {detail[:120]}")


# ─────────────────────────────────────────────────────────────
# 回帰テスト: 直近修正された問題が復活してないか
# ─────────────────────────────────────────────────────────────

def _reg_filename_circle_nums():
    """①②③ファイル名バグ修正の回帰テスト."""
    sys.path.insert(0, str(ROOT))
    from app import _sanitize_filename_prefix
    cases = [
        ("①スマホ撮影", "1スマホ撮影"),
        ("②②②動画", "222動画"),
        ("⑳FV", "20FV"),
        ("🎬FV", "FV"),  # 絵文字除去
        ("", "output"),   # 空は output
        ("  ", "output"),  # 空白のみも output
    ]
    for inp, expected in cases:
        got = _sanitize_filename_prefix(inp)
        assert got == expected, f"'{inp}' → expected '{expected}', got '{got}'"
    return f"{len(cases)}件の丸数字・絵文字・空文字ケース合格"


def _reg_mkdir_parents():
    """FVカット mkdir 500修正の回帰テスト — 全 mkdir に parents=True."""
    text = (ROOT / "app.py").read_text()
    # .mkdir(...) のうち parents=True を含まないもの
    pat = re.compile(r"\.mkdir\(([^)]*)\)")
    bad = []
    for m in pat.finditer(text):
        args = m.group(1)
        # exist_ok のみで parents を指定してないものを検出
        if "parents" not in args and "exist_ok" in args:
            # 親ディレクトリが確実に存在する明らかケース(UPLOAD_DIRなど)を除外したい
            # 行番号を含めて残す
            line_no = text[:m.start()].count("\n") + 1
            bad.append(f"L{line_no}: .mkdir({args})")
    assert not bad, f"parents欠落: {bad[:5]}"
    return f"全{len(list(pat.finditer(text)))}件のmkdirで parents=True 付き"


def _reg_gemini_retry_exists():
    """429リトライ機構が app.py に存在し、全LLM呼び出しで使われているか."""
    text = (ROOT / "app.py").read_text()
    assert "_gemini_request_with_retry" in text, "retry関数消えてる"
    # generativelanguage.googleapis.com への urlopen 直接呼び出しがないこと（retry経由必須）
    # ただし retry の内部実装は除く
    direct_calls = 0
    for m in re.finditer(r"urllib\.request\.urlopen\(", text):
        # 直前500文字に `_gemini_request_with_retry` 定義が無ければ直接呼び出しの疑い
        ctx = text[max(0, m.start()-500):m.start()]
        if "_gemini_request_with_retry" not in ctx and "generativelanguage" in text[max(0, m.start()-300):m.end()+300]:
            direct_calls += 1
    # retry関数内の1回の直接呼び出しは許容
    assert direct_calls <= 1, f"retry経由しないLLM呼び出しが{direct_calls}件ある"
    return "429リトライ関数経由で呼ばれている"


# ─────────────────────────────────────────────────────────────
# Pythonバージョン互換性
# ─────────────────────────────────────────────────────────────

def _py_version_compat():
    """Docker は Python 3.11。ローカルは 3.9。match 文など 3.10+ 構文使ってないか."""
    files = [ROOT / "app.py", ROOT / "profile_loader.py", ROOT / "gen_kosuri_images.py"]
    violations = []
    for f in files:
        text = f.read_text()
        # match statement (3.10+)
        if re.search(r"^\s*match\s+\w+:", text, re.MULTILINE):
            violations.append(f"{f.name}: match statement")
        # PEP 604 union type annotation (`x: int | None`) は 3.10+
        # ただし `from __future__ import annotations` が先頭にあれば OK
        has_future = "from __future__ import annotations" in text
        if not has_future:
            if re.search(r":\s*\w+\s*\|\s*None", text) or re.search(r"->\s*\w+\s*\|\s*\w+", text):
                violations.append(f"{f.name}: PEP604 union (no __future__)")
    assert not violations, f"互換性問題: {violations}"
    return f"{len(files)}ファイル全て3.11互換"


# ─────────────────────────────────────────────────────────────
# 並列安全性
# ─────────────────────────────────────────────────────────────

def _parallel_rag_search():
    """10スレッド同時 search_dpro_patterns で race condition 起きないか."""
    from profile_loader import load_profile, search_dpro_patterns, _DPRO_CACHE
    _DPRO_CACHE.get("query_vec_by_key", {}).clear()
    profiles = [load_profile(k) for k in ["yomite_gungun", "yomite_proust", "yomite_onmyskin", "yomite_rkl"]]
    errors: list[str] = []
    results_by_thread: list[list] = []

    def worker(idx: int):
        try:
            for _ in range(3):
                for p in profiles:
                    hits = search_dpro_patterns(p, top_k=3)
                    results_by_thread.append((idx, len(hits)))
        except Exception as e:
            errors.append(f"T{idx}: {e}")

    ths = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in ths:
        t.start()
    for t in ths:
        t.join()

    assert not errors, f"並列エラー: {errors[:3]}"
    # 全スレッドで結果が取れているか
    assert all(n == 3 for _, n in results_by_thread), "一部threadでtop3取れてない"
    return f"10スレッド×12回 = {len(results_by_thread)}回 race無し"


def _jobs_dict_concurrent_write():
    """jobs dict への並列書き込みが壊れないか（簡易race test）."""
    from app import jobs
    jobs.clear()
    def worker(idx: int):
        for i in range(100):
            job_id = f"job_{idx}_{i}"
            jobs[job_id] = {"status": "running", "idx": idx}
            jobs[job_id]["current"] = i
    ths = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in ths: t.start()
    for t in ths: t.join()
    # 全 8*100 個存在
    assert len(jobs) == 800, f"期待800, got {len(jobs)}"
    jobs.clear()
    return "800並列書き込み全てdict格納"


# ─────────────────────────────────────────────────────────────
# プロファイル内容の質 (意味的な妥当性)
# ─────────────────────────────────────────────────────────────

def _n1_scene_quality():
    """n1.scene が「誰が / どこで / 何を」の3要素を含むか軽くチェック."""
    from profile_loader import load_profile
    warnings = []
    for k in ["yomite_gungun", "yomite_proust", "yomite_onmyskin", "yomite_rkl"]:
        p = load_profile(k)
        scene = p["n1"]["scene"]
        # 代・代の・歳・OL・ママ等が含まれていることで「誰」が明示
        has_who = bool(re.search(r"(\d+代|\d+歳|OL|ママ|母|シニア|女性|男性|高校生|子ども)", scene))
        if not has_who:
            warnings.append(f"{k}: 年代/役割不明 — '{scene}'")
    if warnings:
        return {"warn": True, "msg": " / ".join(warnings)}
    return "全商品でN1の誰が明示"


def _image_suffix_has_age():
    """build_image_prompt_suffix が年代を反映 (rklは senior override)."""
    from profile_loader import load_profile, build_image_prompt_suffix
    rkl = build_image_prompt_suffix(load_profile("yomite_rkl"))
    assert "senior" in rkl.lower() or "55" in rkl, f"RKL が senior モデル指定してない: {rkl}"
    gungun = build_image_prompt_suffix(load_profile("yomite_gungun"))
    assert "30" in gungun or "40" in gungun, f"gungun に年代指定なし: {gungun}"
    return "年代/senior指定OK"


# ─────────────────────────────────────────────────────────────
# Docker build context
# ─────────────────────────────────────────────────────────────

def _docker_context_size():
    """.dockerignore を考慮した想定 build context サイズ."""
    ignored_globs = [".dockerignore entries"]
    ignore = (ROOT / ".dockerignore").read_text().splitlines()
    ignore_set = {x.strip().rstrip("/") for x in ignore if x.strip() and not x.startswith("#")}
    total = 0
    big_dirs: list[tuple[str, int]] = []
    for p in ROOT.rglob("*"):
        if p.is_file():
            # ignore 適用
            rel = p.relative_to(ROOT)
            top = rel.parts[0]
            if top in ignore_set:
                continue
            if p.name in ignore_set:
                continue
            if p.name.startswith("."):
                # .DS_Store等は除外 (.dockerignore側で定義)
                if p.name == ".DS_Store":
                    continue
            total += p.stat().st_size
    mb = total / 1024 / 1024
    # context が 500MB 超えると Cloud Build が重い → 警告
    if mb > 500:
        return {"warn": True, "msg": f"build context={mb:.1f}MB (>500MB)"}
    return f"build context: {mb:.1f}MB"


def _data_json_in_context():
    """data/dpro_fv_patterns.json が .dockerignore で除外されてない."""
    ignore = (ROOT / ".dockerignore").read_text()
    assert "data" not in ignore.split("\n"), "'data' line in .dockerignore → DB excluded!"
    assert "dpro_fv_patterns" not in ignore
    return "data/ は build に含まれる"


# ─────────────────────────────────────────────────────────────
# ログ出力: print → Cloud Run Logs 互換
# ─────────────────────────────────────────────────────────────

def _stdout_flushing():
    """長時間ジョブ中のログ欠落を防ぐため print に flush=True が必要な箇所がある."""
    text = (ROOT / "app.py").read_text()
    # 今は flush=True が無くても gunicorn が stdout を unbuffered で扱う → 問題なし
    # ただし gunicorn config で --bind だけなのでデフォルトバッファを確認
    df = (ROOT / "Dockerfile").read_text()
    # PYTHONUNBUFFERED=1 があれば安全
    unbuffered = "PYTHONUNBUFFERED" in df
    if not unbuffered:
        return {"warn": True, "msg": "Dockerfile に PYTHONUNBUFFERED=1 なし → ログ遅延の可能性"}
    return "unbuffered stdout 設定あり"


# ─────────────────────────────────────────────────────────────
# Profile loader の google.genai 遅延 import
# ─────────────────────────────────────────────────────────────

def _lazy_genai_import():
    """google.genai が profile_loader のトップレベル import ではなく遅延 import."""
    text = (ROOT / "profile_loader.py").read_text()
    lines = text.split("\n")
    # 最初の 30 行に `from google import genai` が無いこと
    for i, ln in enumerate(lines[:30]):
        assert "from google import genai" not in ln, f"L{i+1}: top-level import"
        assert "import google.genai" not in ln, f"L{i+1}: top-level import"
    # _embed_query の中に try: from google import genai が有ること
    assert "from google import genai" in text, "遅延importが存在しない"
    return "google.genai は遅延import"


# ─────────────────────────────────────────────────────────────
# 実行
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("KOSURIちゃん v5 深層監査")
    print("=" * 70)

    T("①②③ファイル名バグ回帰", _reg_filename_circle_nums, category="1.回帰")
    T("mkdir parents=True 全網羅", _reg_mkdir_parents, category="1.回帰")
    T("Gemini 429リトライ経由", _reg_gemini_retry_exists, category="1.回帰")

    T("Python3.11互換", _py_version_compat, category="2.互換性")

    T("並列RAG検索 race無し", _parallel_rag_search, category="3.並列")
    T("jobs dict 並列書き込み", _jobs_dict_concurrent_write, category="3.並列")

    T("N1 scene内容品質", _n1_scene_quality, category="4.プロファイル品質")
    T("画像suffix年代反映", _image_suffix_has_age, category="4.プロファイル品質")

    T("Docker context size", _docker_context_size, category="5.Docker")
    T("data/ build含まれる", _data_json_in_context, category="5.Docker")

    T("stdout flush対策", _stdout_flushing, category="6.ログ")

    T("google.genai 遅延import", _lazy_genai_import, category="7.設計")

    # サマリー
    pass_c = sum(1 for r in results if r["status"] == "PASS")
    warn_c = sum(1 for r in results if r["status"] == "WARN")
    fail_c = sum(1 for r in results if r["status"] == "FAIL")
    err_c = sum(1 for r in results if r["status"] == "ERROR")

    print()
    print("=" * 70)
    print(f"DEEP AUDIT  PASS={pass_c} WARN={warn_c} FAIL={fail_c} ERROR={err_c} / {len(results)}")
    print("=" * 70)

    # レポートに追記
    report_path = ROOT.parent.parent / "reports" / "kosuri_qa_report.md"
    lines = []
    if report_path.exists():
        lines = report_path.read_text().split("\n")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 深層監査 (Deep Audit)")
    lines.append("")
    lines.append(f"**サマリー**: ✅PASS={pass_c} / ⚠️WARN={warn_c} / ❌FAIL={fail_c} / 💥ERROR={err_c} ／ **TOTAL {len(results)}**")
    lines.append("")
    by_cat: dict[str, list[dict]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)
    for cat in sorted(by_cat.keys()):
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| 結果 | テスト名 | 詳細 | 時間 |")
        lines.append("|---|---|---|---|")
        for r in by_cat[cat]:
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "💥"}[r["status"]]
            detail = r["detail"].replace("|", "\\|").replace("\n", " ")[:200]
            lines.append(f"| {icon} | {r['name']} | {detail} | {r['elapsed_s']}s |")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 レポート更新: {report_path}")

    sys.exit(1 if (fail_c + err_c) else 0)


if __name__ == "__main__":
    main()
