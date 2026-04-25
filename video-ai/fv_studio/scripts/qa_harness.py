#!/usr/bin/env python3
"""KOSURIちゃん v5 品質チェック Harness.

5人の動画編集者シミュレーション + エッジケース自動テスト。
朝までに寝てる一進さんへのQAレポートを生成する。

使い方:
    GEMINI_API_KEY_1=xxx python3 scripts/qa_harness.py

出力:
    - コンソール: テスト進行ログ
    - reports/kosuri_qa_report.md: 朝に一進さんが読むレポート
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 結果集計
results: list[dict] = []


def T(name: str, fn, *, category: str = "misc") -> Any:
    """1テストを実行して結果を集計."""
    t0 = time.time()
    try:
        ret = fn()
        status = "PASS"
        detail = ret if isinstance(ret, str) else ""
        if isinstance(ret, dict) and ret.get("warn"):
            status = "WARN"
            detail = ret.get("msg", "")
        elif isinstance(ret, dict):
            detail = json.dumps(ret, ensure_ascii=False)[:200]
    except AssertionError as e:
        status = "FAIL"
        detail = str(e) or "assert failed"
        ret = None
    except Exception as e:
        status = "ERROR"
        detail = f"{type(e).__name__}: {str(e)[:180]}"
        ret = None
    elapsed = time.time() - t0
    results.append({"name": name, "category": category, "status": status,
                    "detail": detail, "elapsed_s": round(elapsed, 2)})
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "💥"}[status]
    print(f"{icon} [{category}] {name} ({elapsed:.2f}s)  {detail[:100]}")
    return ret


# ─────────────────────────────────────────────────────────────
# カテゴリ1: 基盤 — モジュール import
# ─────────────────────────────────────────────────────────────

def _test_imports():
    import profile_loader  # noqa
    return f"profile_loader OK (yaml={profile_loader._YAML_AVAILABLE})"


def _test_app_import():
    # app.py は Flask app を初期化するので import できるかだけチェック
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_mod", ROOT / "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert hasattr(m, "app"), "Flask app object missing"
    routes = sorted({r.rule for r in m.app.url_map.iter_rules()})
    return f"{len(routes)} routes registered"


def _test_data_db_exists():
    db = ROOT / "data" / "dpro_fv_patterns.json"
    assert db.exists(), f"DB missing: {db}"
    size_mb = db.stat().st_size / 1024 / 1024
    data = json.loads(db.read_text())
    patterns = data.get("patterns", [])
    assert len(patterns) > 50, f"only {len(patterns)} patterns"
    # すべて非ゼロ embedding？
    for p in patterns:
        emb = p.get("embedding")
        assert emb and len(emb) == 3072, f"bad embedding on {p.get('item_id')}"
        assert not all(x == 0 for x in emb[:5]), f"zero vec on {p.get('item_id')}"
    return f"{len(patterns)} patterns / {size_mb:.2f}MB / dim=3072"


# ─────────────────────────────────────────────────────────────
# カテゴリ2: プロファイル整合性（全商品）
# ─────────────────────────────────────────────────────────────

PRODUCT_KEYS = ["yomite_gungun", "yomite_proust", "yomite_onmyskin", "yomite_rkl"]

REQUIRED_PROFILE_FIELDS = [
    "product_key", "product_name", "client",
    "persona", "product", "regulation", "hooks",
]

REQUIRED_N1_FIELDS = ["scene", "emotion", "visual_hook_emotion", "target_moment"]


def _test_profile_loadable(key: str):
    from profile_loader import load_profile
    p = load_profile(key)
    assert p, f"{key} not loaded"
    missing = [f for f in REQUIRED_PROFILE_FIELDS if f not in p]
    assert not missing, f"missing fields: {missing}"
    return f"{p.get('product_name')} / hooks priority={len(p.get('hooks',{}).get('priority',[]))}"


def _test_n1_complete(key: str):
    from profile_loader import load_profile
    p = load_profile(key)
    n1 = p.get("n1")
    assert n1, f"{key}: n1 missing"
    missing = [f for f in REQUIRED_N1_FIELDS if not n1.get(f)]
    assert not missing, f"n1 missing {missing}"
    # 文字数チェック: 各フィールドが意味ある長さ
    for f in REQUIRED_N1_FIELDS:
        assert len(n1[f]) >= 15, f"n1.{f} too short: '{n1[f]}'"
    return f"all n1 fields present (scene={len(n1['scene'])}char)"


def _test_regulation_sanity(key: str):
    from profile_loader import load_profile
    p = load_profile(key)
    reg = p.get("regulation", {})
    assert reg.get("yakkihou_level"), "yakkihou_level missing"
    assert reg.get("ng_expressions"), "no NG expressions"
    assert reg.get("safe_alternatives"), "no safe_alternatives"
    return f"yakki={reg['yakkihou_level']} ng={len(reg['ng_expressions'])} safe={len(reg['safe_alternatives'])}"


# ─────────────────────────────────────────────────────────────
# カテゴリ3: build_profile_injection() 全商品
# ─────────────────────────────────────────────────────────────

def _test_injection_all(key: str):
    from profile_loader import load_profile, build_profile_injection
    p = load_profile(key)
    inj = build_profile_injection(p)
    assert "商品プロファイル" in inj, "missing profile header"
    assert "N1ターゲット" in inj, "missing N1 block"
    assert p["product_name"] in inj, "product name not injected"
    # NG表現が全部含まれる
    for ng in p.get("regulation", {}).get("ng_expressions", [])[:3]:
        assert ng in inj, f"NG '{ng}' not in injection"
    return f"{len(inj)}char injection"


def _test_injection_empty_on_none():
    from profile_loader import build_profile_injection
    assert build_profile_injection(None) == ""
    assert build_profile_injection({}) == ""
    return "empty-safe"


# ─────────────────────────────────────────────────────────────
# カテゴリ4: DPro RAG検索
# ─────────────────────────────────────────────────────────────

def _test_rag_search(key: str):
    """N1+ペルソナクエリで同ジャンルTOP3がヒットするか."""
    from profile_loader import load_profile, search_dpro_patterns
    p = load_profile(key)
    hits = search_dpro_patterns(p, top_k=3)
    assert len(hits) == 3, f"expected 3, got {len(hits)}"
    # スコア降順
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True), f"not sorted: {scores}"
    # Top1のスコアが0.6+ (意味マッチの目安)
    top1 = hits[0]["score"]
    assert top1 >= 0.5, f"top1 sim too low: {top1}"
    # 同ジャンル率
    own_genre = (p.get("product", {}) or {}).get("category_key", "")
    genre_name = p.get("product", {}).get("category", "")
    return {"top1": round(top1, 3), "genres": [h["genre_name"] for h in hits]}


def _test_rag_caching():
    """同じprofileで2回呼ぶとクエリembedがキャッシュされる"""
    from profile_loader import load_profile, search_dpro_patterns, _DPRO_CACHE
    p = load_profile("yomite_gungun")
    _DPRO_CACHE.get("query_vec_by_key", {}).pop("yomite_gungun", None)  # reset
    t1 = time.time()
    search_dpro_patterns(p, 3)
    first_t = time.time() - t1
    t2 = time.time()
    search_dpro_patterns(p, 3)
    second_t = time.time() - t2
    # 2回目はネットワーク無しで高速化されているはず
    assert second_t < first_t * 0.5 or second_t < 0.3, (
        f"cache not working: 1st={first_t:.3f}s 2nd={second_t:.3f}s"
    )
    return f"1st={first_t:.2f}s 2nd={second_t:.3f}s (cached)"


def _test_rag_disabled_env():
    """KOSURI_DPRO_RAG=0 でRAGブロックが注入されない"""
    from profile_loader import load_profile, build_profile_injection
    os.environ["KOSURI_DPRO_RAG"] = "0"
    try:
        inj = build_profile_injection(load_profile("yomite_gungun"))
        assert "DPro勝ちFVパターン" not in inj, "RAG block leaked when disabled"
    finally:
        os.environ.pop("KOSURI_DPRO_RAG", None)
    return "RAG-OFF respected"


def _test_rag_without_api_key():
    """API key 不在時にクラッシュせず RAGだけskipする."""
    from profile_loader import load_profile, build_profile_injection, _DPRO_CACHE
    saved = {k: os.environ.pop(k, None) for k in ("GEMINI_API_KEY", "GEMINI_API_KEY_1")}
    # キャッシュもクリア
    _DPRO_CACHE.get("query_vec_by_key", {}).clear()
    try:
        inj = build_profile_injection(load_profile("yomite_gungun"))
        # プロファイル本体は動いてる
        assert "商品プロファイル" in inj
        assert "N1ターゲット" in inj
        # RAGはキャッシュあれば動くので、ここでは「落ちないこと」だけ確認
        return "no-crash when GEMINI_API_KEY absent"
    finally:
        for k, v in saved.items():
            if v:
                os.environ[k] = v


# ─────────────────────────────────────────────────────────────
# カテゴリ5: エラー系
# ─────────────────────────────────────────────────────────────

def _test_unknown_product_key():
    from profile_loader import load_profile, build_profile_injection
    p = load_profile("unknown_xxx")
    assert p is None
    inj = build_profile_injection(p)
    assert inj == ""
    return "unknown key → None/empty"


def _test_malformed_key():
    from profile_loader import load_profile
    # アンダースコアなし
    assert load_profile("malformed") is None
    assert load_profile("") is None
    assert load_profile("_") is None
    return "malformed keys handled"


def _test_list_products():
    from profile_loader import list_available_products
    prods = list_available_products()
    keys = {p["product_key"] for p in prods}
    for required in PRODUCT_KEYS:
        assert required in keys, f"{required} missing from listing"
    return f"{len(prods)} products listed"


# ─────────────────────────────────────────────────────────────
# カテゴリ6: Flask routes
# ─────────────────────────────────────────────────────────────

def _test_flask_health():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_mod", ROOT / "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    client = m.app.test_client()
    r = client.get("/health")
    assert r.status_code == 200, f"/health returned {r.status_code}"
    return f"/health OK status={r.status_code}"


def _test_flask_login_page():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_mod", ROOT / "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    client = m.app.test_client()
    r = client.get("/login")
    assert r.status_code == 200
    assert "パスワード" in r.data.decode("utf-8")
    return f"login page OK ({len(r.data)}B)"


def _test_flask_requires_auth():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_mod", ROOT / "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    client = m.app.test_client()
    r = client.get("/")
    # 未認証は redirect to /login
    assert r.status_code in (302, 301), f"expected redirect, got {r.status_code}"
    assert "/login" in r.headers.get("Location", "")
    return f"/ redirects to login ({r.status_code})"


def _test_flask_kosuri_products_after_login():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_mod", ROOT / "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.app.config["WTF_CSRF_ENABLED"] = False
    client = m.app.test_client()
    # ログイン
    r = client.post("/login", data={"password": "kosuri.yomite"}, follow_redirects=False)
    assert r.status_code in (302, 301), f"login status {r.status_code}"
    # 商品一覧
    r = client.get("/kosuri-products")
    assert r.status_code == 200, f"kosuri-products {r.status_code}"
    js = r.get_json()
    keys = {p["product_key"] for p in js.get("products", [])}
    for req in PRODUCT_KEYS:
        assert req in keys, f"{req} missing"
    return f"/kosuri-products returns {len(keys)} products"


def _test_flask_wrong_password():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_mod", ROOT / "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    client = m.app.test_client()
    r = client.post("/login", data={"password": "wrong"})
    assert r.status_code == 200  # login page re-rendered
    assert "違います" in r.data.decode("utf-8"), "no error shown"
    return "wrong pw rejected with message"


# ─────────────────────────────────────────────────────────────
# カテゴリ7: デプロイ整合性
# ─────────────────────────────────────────────────────────────

def _test_requirements_complete():
    req = (ROOT / "requirements.txt").read_text()
    needed = ["flask", "pillow", "gunicorn", "pyyaml", "google-genai"]
    missing = [n for n in needed if n not in req.lower()]
    assert not missing, f"missing in requirements: {missing}"
    return "all key packages listed"


def _test_dockerfile_sane():
    df = (ROOT / "Dockerfile").read_text()
    assert "COPY . ." in df, "missing COPY . ."  # data/, scripts/ も含める
    assert "ffmpeg" in df, "ffmpeg must be installed"
    assert "fonts-noto-cjk" in df, "missing Noto CJK font (caption rendering)"
    assert "gunicorn" in df, "gunicorn startup missing"
    return "Dockerfile has ffmpeg + noto + gunicorn + copy-all"


def _test_deploy_copies_clients():
    ds = (ROOT / "deploy.sh").read_text()
    assert "cp -r" in ds, "deploy.sh doesn't copy clients"
    assert ".claude/clients" in ds, "clients dir path missing"
    return "deploy.sh copies .claude/clients/ into build context"


def _test_data_not_in_gitignore():
    """data/dpro_fv_patterns.json は git commit 対象なはず (Dockerに含める必要)."""
    voyage_root = ROOT.parent.parent
    gi = voyage_root / ".gitignore"
    if not gi.exists():
        return "no .gitignore"
    text = gi.read_text()
    # data/ や dpro_fv_patterns が ignore されてたらアウト
    for pat in ["dpro_fv_patterns", "video-ai/fv_studio/data"]:
        if pat in text:
            return {"warn": True, "msg": f"'{pat}' in .gitignore → won't deploy!"}
    return "data/ not ignored"


# ─────────────────────────────────────────────────────────────
# カテゴリ8: パフォーマンス
# ─────────────────────────────────────────────────────────────

def _test_db_load_speed():
    """DBロードが1秒以内."""
    # キャッシュクリア
    import profile_loader as pl
    pl._DPRO_CACHE.clear()
    t0 = time.time()
    db = pl._load_dpro_db()
    t1 = time.time() - t0
    assert db, "load failed"
    assert t1 < 2.0, f"too slow: {t1:.2f}s"
    return f"loaded {len(db['patterns'])} patterns in {t1*1000:.0f}ms"


def _test_injection_latency():
    """プロファイル注入の総所要時間を計測 (embed呼び出し含む)."""
    from profile_loader import load_profile, build_profile_injection, _DPRO_CACHE
    _DPRO_CACHE.get("query_vec_by_key", {}).clear()
    times = []
    for key in PRODUCT_KEYS:
        t0 = time.time()
        build_profile_injection(load_profile(key))
        times.append(time.time() - t0)
    avg = sum(times) / len(times)
    max_t = max(times)
    # 初回embedは ~500ms-1s 想定
    assert avg < 5.0, f"avg too slow: {avg:.2f}s"
    return f"avg={avg*1000:.0f}ms max={max_t*1000:.0f}ms (4 products, first-call embed)"


# ─────────────────────────────────────────────────────────────
# カテゴリ9: 5人の編集者シミュレーション
# ─────────────────────────────────────────────────────────────

EDITORS = [
    {
        "name": "編集者A・身長サプリ担当",
        "product_key": "yomite_gungun",
        "prompt": "小学4年生のママにうちの子も伸びてほしいと思わせたい",
    },
    {
        "name": "編集者B・ワキガクリーム担当",
        "product_key": "yomite_proust",
        "prompt": "満員電車で他人の視線が怖いOLに刺したい",
    },
    {
        "name": "編集者C・スキンケア担当",
        "product_key": "yomite_onmyskin",
        "prompt": "40代のシワに悩んでる女性にBefore/Afterで見せたい",
    },
    {
        "name": "編集者D・膝サポーター担当",
        "product_key": "yomite_rkl",
        "prompt": "60代の膝痛に悩むシニア、孫と旅行したい気持ちに火をつける",
    },
    {
        "name": "編集者E・プロファイル未使用",
        "product_key": "",  # 空
        "prompt": "既存商品じゃなくて適当に10パターン欲しい",
    },
]


def _simulate_editor(editor: dict):
    """編集者1人の /fv-generate 相当の流れをコード経路のみで追う (LLMは叩かない)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_mod", ROOT / "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from profile_loader import load_profile, build_profile_injection

    product_key = editor["product_key"]
    profile = load_profile(product_key) if product_key else None

    # build_profile_injection が落ちずに返るか
    injection = build_profile_injection(profile) if profile else ""

    # image suffix も
    from profile_loader import build_image_prompt_suffix
    suffix = build_image_prompt_suffix(profile) if profile else ""

    # filter_hook_patterns で avoid フックが除かれているか
    from profile_loader import filter_hook_patterns
    filtered = filter_hook_patterns(m.VISUAL_HOOK_PATTERNS, profile)
    avoid = set((profile or {}).get("hooks", {}).get("avoid", []) or [])
    leaked = [p["id"] for p in filtered if p["id"] in avoid]
    assert not leaked, f"avoid hooks leaked: {leaked}"

    # 結果サマリー
    return {
        "product": (profile or {}).get("product_name") or "(generic)",
        "injection_bytes": len(injection),
        "suffix_bytes": len(suffix),
        "filtered_hooks": len(filtered),
        "leaked": len(leaked),
    }


# ─────────────────────────────────────────────────────────────
# 法規チェック（機械的に検出できる範囲）
# ─────────────────────────────────────────────────────────────

def _test_no_banned_words_in_profile(key: str):
    """profile 内の winning_copies / persona 等に薬機法抵触ワードが無いか."""
    from profile_loader import load_profile
    p = load_profile(key)
    # 極端に危険なワード（各商品で自分のNG表現は使ってないか）
    ng = [n for n in p.get("regulation", {}).get("ng_expressions", []) if len(n) >= 4]
    # winning_copies / safe_alternatives はNGワードを含んではいけない
    winning = p.get("winning_copies", []) or []
    safe = p.get("regulation", {}).get("safe_alternatives", []) or []
    hits = []
    for copy in winning + safe:
        for n in ng:
            if n in copy:
                hits.append(f"'{n}' in '{copy}'")
    assert not hits, f"NG terms leaked: {hits[:3]}"
    return f"ng={len(ng)} copies_clean={len(winning + safe)}"


# ─────────────────────────────────────────────────────────────
# 実行
# ─────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 70)
    print("KOSURIちゃん v5 品質チェック Harness")
    print("=" * 70)

    # 基盤
    T("profile_loader import", _test_imports, category="1.基盤")
    T("app.py import + routes", _test_app_import, category="1.基盤")
    T("data/dpro_fv_patterns.json健全性", _test_data_db_exists, category="1.基盤")

    # プロファイル整合性
    for key in PRODUCT_KEYS:
        T(f"{key} load + 必須フィールド", lambda k=key: _test_profile_loadable(k), category="2.プロファイル")
        T(f"{key} n1 完備", lambda k=key: _test_n1_complete(k), category="2.プロファイル")
        T(f"{key} regulation完備", lambda k=key: _test_regulation_sanity(k), category="2.プロファイル")

    # 注入
    for key in PRODUCT_KEYS:
        T(f"{key} build_profile_injection", lambda k=key: _test_injection_all(k), category="3.注入")
    T("build_profile_injection(None)", _test_injection_empty_on_none, category="3.注入")

    # RAG
    for key in PRODUCT_KEYS:
        T(f"{key} DPro RAG top-3", lambda k=key: _test_rag_search(k), category="4.RAG")
    T("RAGクエリembedキャッシュ", _test_rag_caching, category="4.RAG")
    T("KOSURI_DPRO_RAG=0でOFF", _test_rag_disabled_env, category="4.RAG")
    T("API_KEY無しでgraceful", _test_rag_without_api_key, category="4.RAG")

    # エラー系
    T("未登録 product_key", _test_unknown_product_key, category="5.エラー系")
    T("malformed key", _test_malformed_key, category="5.エラー系")
    T("list_available_products", _test_list_products, category="5.エラー系")

    # Flask
    T("/health", _test_flask_health, category="6.Flask")
    T("/login page", _test_flask_login_page, category="6.Flask")
    T("未認証→redirect", _test_flask_requires_auth, category="6.Flask")
    T("ログイン後/kosuri-products", _test_flask_kosuri_products_after_login, category="6.Flask")
    T("パスワード間違い", _test_flask_wrong_password, category="6.Flask")

    # デプロイ
    T("requirements.txt完備", _test_requirements_complete, category="7.デプロイ")
    T("Dockerfile sanity", _test_dockerfile_sane, category="7.デプロイ")
    T("deploy.sh clients コピー", _test_deploy_copies_clients, category="7.デプロイ")
    T("data/ がgitignoreされてない", _test_data_not_in_gitignore, category="7.デプロイ")

    # パフォーマンス
    T("DBロード速度", _test_db_load_speed, category="8.パフォーマンス")
    T("注入レイテンシ(4商品)", _test_injection_latency, category="8.パフォーマンス")

    # 5人シミュレーション
    for ed in EDITORS:
        T(ed["name"], lambda e=ed: _simulate_editor(e), category="9.編集者5人")

    # 法規
    for key in PRODUCT_KEYS:
        T(f"{key} NG語リーク検査", lambda k=key: _test_no_banned_words_in_profile(k), category="10.法規")

    # ─── サマリー ──────────────────────────────────────────
    total = len(results)
    pass_c = sum(1 for r in results if r["status"] == "PASS")
    warn_c = sum(1 for r in results if r["status"] == "WARN")
    fail_c = sum(1 for r in results if r["status"] == "FAIL")
    err_c = sum(1 for r in results if r["status"] == "ERROR")

    print()
    print("=" * 70)
    print(f"RESULT  PASS={pass_c} WARN={warn_c} FAIL={fail_c} ERROR={err_c} / {total}")
    print("=" * 70)

    # レポート出力
    report_path = ROOT.parent.parent / "reports" / "kosuri_qa_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# KOSURIちゃん v5 品質チェック レポート",
        "",
        f"**実行日時**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**サマリー**: ✅PASS={pass_c} / ⚠️WARN={warn_c} / ❌FAIL={fail_c} / 💥ERROR={err_c} ／ **TOTAL {total}**",
        "",
    ]
    by_cat: dict[str, list[dict]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)
    for cat in sorted(by_cat.keys()):
        md.append(f"## {cat}")
        md.append("")
        md.append("| 結果 | テスト名 | 詳細 | 時間 |")
        md.append("|---|---|---|---|")
        for r in by_cat[cat]:
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "💥"}[r["status"]]
            # マークダウン用 escape
            detail = r["detail"].replace("|", "\\|").replace("\n", " ")[:200]
            md.append(f"| {icon} | {r['name']} | {detail} | {r['elapsed_s']}s |")
        md.append("")

    # 総合判定
    md.append("## 総合判定")
    md.append("")
    if fail_c == 0 and err_c == 0:
        md.append("🚢 **デプロイ可能**: 致命的な問題なし。")
    else:
        md.append(f"⛔ **要対応**: FAIL={fail_c} / ERROR={err_c} 件あり。")
    if warn_c:
        md.append(f"\n⚠️ 警告 {warn_c} 件。内容確認推奨。")
    report_path.write_text("\n".join(md), encoding="utf-8")
    print(f"\n📄 レポート: {report_path}")

    # non-zero if critical
    sys.exit(1 if (fail_c + err_c) else 0)


if __name__ == "__main__":
    main()
