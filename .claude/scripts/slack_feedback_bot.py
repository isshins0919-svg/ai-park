#!/usr/bin/env python3
"""
Slack 記事フィードバックBot v6
- #yomite_ai-fb を2分おきにポーリング
- 「フィードバック」+ URL を含む投稿を検知
- Playwright でJS実行後にDOM順（テキスト＋画像・動画セット）で解析
- 動画は全本のサムネイルをOpenCV並列取得 → Claude Visionに渡す
- 18パート構造分析＋統計付きフィードバックをSlack Canvasで返信
"""
from __future__ import annotations

import re
import io
import os
import json
import time
import subprocess
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# ── httpx 0.28+ で非ASCII文字がヘッダー値に入るとUnicodeEncodeErrorになる問題を回避 ──
# httpx 0.28 から header値をASCIIでエンコードするようになったが、
# 古いanthropic SDKの内部処理で非ASCII文字が混入するケースがある
import httpx._models as _httpx_models
_orig_normalize = _httpx_models._normalize_header_value
def _patched_normalize_header_value(value, encoding=None):
    if isinstance(value, str):
        try:
            return value.encode(encoding or "ascii")
        except UnicodeEncodeError:
            logging.getLogger(__name__).warning(
                f"Non-ASCII header value detected (len={len(value)}): {repr(value[:50])}... — falling back to UTF-8"
            )
            return value.encode("utf-8")
    return _orig_normalize(value, encoding)
_httpx_models._normalize_header_value = _patched_normalize_header_value

from PIL import Image

import markdown as md_lib
from bs4 import BeautifulSoup
import anthropic
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from playwright.sync_api import sync_playwright
import cv2
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── 設定 ─────────────────────────────────────────────
CHANNEL_ID     = "C0AMYLU2W5D"   # #yomite_ai-kiji_fb
POLL_INTERVAL  = 120              # 2分おきにチェック
MAX_IMAGES     = 10               # Vision に渡す画像の上限
MAX_VIDEOS     = 36               # サムネイル抽出する動画の上限（全本対応）
MAX_VIDEO_WORKERS = 8             # サムネイル並列取得スレッド数
STATE_FILE     = Path(__file__).parent / "slack_feedback_state.json"
LOG_FILE       = Path(__file__).parent / "slack_feedback_bot.log"

TRIGGER_KEYWORDS = ["フィードバック", "feedback", "フィードバックください", "fb"]

# オファーセクション検知キーワード（ここで読み込みを止める）
OFFER_TRIGGERS = [
    "アンケート", "クーポン", "今すぐ購入", "お申込", "ご注文",
    "定期コース", "カートに", "送料無料", "キャンペーン終了",
    "限定クーポン", "特典セット", "円OFF", "割引コード",
]

# ─── ロギング ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─── 環境変数取得 ─────────────────────────────────────
def get_env(key: str) -> str:
    # まず現在のプロセス環境変数を確認（nohup経由で渡された場合）
    val = os.environ.get(key, "")
    if val:
        return val
    # 次に ~/.zshrc を source して取得（zsh -l は ~/.zshrc を読まないため明示的に source）
    val = subprocess.run(
        ["zsh", "-l", "-c", f"source ~/.zshrc 2>/dev/null; echo ${key}"],
        capture_output=True, text=True
    ).stdout.strip()
    if not val:
        raise EnvironmentError(f"環境変数 {key} が未設定です。~/.zshrc を確認してください。")
    return val

# ─── 状態管理 ─────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_ts": None, "processed": []}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ─── URL抽出 ─────────────────────────────────────────
def extract_urls(text: str) -> list[str]:
    return re.findall(r'https?://[^\s\|<>]+', text)

# ─── 記事取得（Playwright版 — JS実行後に画像URL取得）────────
def fetch_article_with_images(url: str) -> dict:
    """
    Playwrightでブラウザを起動してJSを実行し、レンダリング後の画像URLを取得。
    SquadBeyond等のlazyload/JS依存ページに対応。
    """
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )

            page.goto(url, wait_until="networkidle", timeout=30000)

            # lazyload画像を全て展開するためページ末尾までスクロール
            page.evaluate("""
                async () => {
                    await new Promise(resolve => {
                        let total = document.body.scrollHeight;
                        let current = 0;
                        const step = 800;
                        const timer = setInterval(() => {
                            window.scrollBy(0, step);
                            current += step;
                            if (current >= total) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            page.wait_for_timeout(1500)  # lazyload発火待ち

            # レンダリング後のHTMLを取得
            html = page.content()
            browser.close()

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        soup = BeautifulSoup(html, "html.parser")

        # 不要タグ除去
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        body = soup.find("body") or soup
        full_html = str(body)

        # オファー検知：最初に出現する位置でカット
        offer_pos = len(full_html)
        offer_detected = False
        offer_trigger = None
        for trigger in OFFER_TRIGGERS:
            pos = full_html.find(trigger)
            if pos != -1 and pos < offer_pos:
                offer_pos = pos
                offer_detected = True
                offer_trigger = trigger

        pre_offer_soup = BeautifulSoup(full_html[:offer_pos], "html.parser")

        # ── DOM順にテキスト・画像・動画をセクションとして解析 ──
        def normalize_src(src: str) -> str:
            if src.startswith("//"): return "https:" + src
            if src.startswith("/"): return base_url + src
            return src

        def is_valid_img(src: str, tag) -> bool:
            if not src or "lazy.png" in src or "placeholder" in src or src.startswith("data:"):
                return False
            w = tag.get("width", "")
            h = tag.get("height", "")
            if (str(w).isdigit() and int(w) <= 50) or (str(h).isdigit() and int(h) <= 50):
                return False
            return src.startswith("http")

        def iter_dom(node):
            """DOM順にp/h/li/img/videoをyieldするジェネレーター"""
            for child in node.children:
                if not hasattr(child, "name") or child.name is None:
                    continue
                if child.name in ["script", "style", "nav", "footer", "aside", "header"]:
                    continue
                if child.name in ["img", "video", "iframe"]:
                    yield child
                elif child.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "dt", "dd", "blockquote"]:
                    yield child
                else:
                    yield from iter_dom(child)

        sections = []
        text_buf = []
        img_count = 0
        vid_count = 0
        all_video_urls = []

        def flush_text():
            t = "\n".join(text_buf).strip()
            if t and len(t) > 10:
                sections.append({"type": "text", "content": t[:600]})
            text_buf.clear()

        for elem in iter_dom(pre_offer_soup):
            if elem.name == "img":
                src = normalize_src(elem.get("src", ""))
                if is_valid_img(src, elem) and img_count < MAX_IMAGES:
                    flush_text()
                    sections.append({"type": "image", "url": src, "position": img_count + 1})
                    img_count += 1

            elif elem.name == "video":
                src = elem.get("src") or elem.get("data-src")
                if not src:
                    source = elem.find("source")
                    if source: src = source.get("src") or source.get("data-src")
                if src:
                    src = normalize_src(src)
                    all_video_urls.append({"url": src, "type": "mp4"})
                    if vid_count < MAX_VIDEOS:
                        flush_text()
                        sections.append({"type": "video", "url": src, "position": vid_count + 1})
                        vid_count += 1

            elif elem.name == "iframe":
                src = elem.get("src", "")
                if "youtube.com/embed/" in src or "youtu.be/" in src:
                    all_video_urls.append({"url": src, "type": "youtube"})
                    if vid_count < MAX_VIDEOS:
                        flush_text()
                        sections.append({"type": "video", "url": src, "position": vid_count + 1})
                        vid_count += 1

            else:
                t = elem.get_text(strip=True)
                if t:
                    text_buf.append(t)

        flush_text()

        # 重複動画URL除去
        seen = set()
        unique_videos = []
        for v in all_video_urls:
            if v["url"] not in seen:
                seen.add(v["url"])
                unique_videos.append(v)

        # 統計
        total_chars = sum(s["content"].__len__() for s in sections if s["type"] == "text")
        stats = {
            "chars": total_chars,
            "images": img_count,
            "videos": len(unique_videos),
        }

        log.info(f"記事解析完了(DOM順) — 文字:{total_chars}字 画像:{img_count}枚 動画:{len(unique_videos)}本 セクション:{len(sections)} オファー前:{offer_detected}")
        return {
            "sections": sections,
            "videos": unique_videos,
            "stats": stats,
            "offer_detected": offer_detected,
            "offer_trigger": offer_trigger,
        }

    except Exception as e:
        log.error(f"記事取得エラー(Playwright): {e}")
        return {"sections": [], "videos": [], "stats": {"chars": 0, "images": 0, "videos": 0}, "offer_detected": False, "offer_trigger": None}


# ─── 動画サムネイル抽出（OpenCV並列）────────────────────
def _extract_one_thumbnail(args: tuple):
    """1本の動画から先頭フレームをbase64 PNGで返す（並列Worker用）"""
    idx, vid = args
    url = vid["url"]
    try:
        cap = cv2.VideoCapture(url)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            log.warning(f"サムネイル取得失敗 [{idx+1}] {url}")
            return None
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64 = base64.standard_b64encode(buf.tobytes()).decode()
        log.info(f"サムネイル取得OK [{idx+1}] {url.split('/')[-1][:20]}")
        return {"position": idx + 1, "b64": b64, "url": url}
    except Exception as e:
        log.warning(f"サムネイル取得エラー [{idx+1}]: {e}")
        return None


def extract_video_thumbnails(videos: list) -> list[dict]:
    """全動画のサムネイルをMAX_VIDEO_WORKERSスレッドで並列取得"""
    if not videos:
        return []
    unique = list({v["url"]: v for v in videos}.values())[:MAX_VIDEOS]
    log.info(f"サムネイル並列取得開始 — {len(unique)}本 ({MAX_VIDEO_WORKERS}並列)")
    results = []
    with ThreadPoolExecutor(max_workers=MAX_VIDEO_WORKERS) as ex:
        futures = {ex.submit(_extract_one_thumbnail, (i, v)): i for i, v in enumerate(unique)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    results.sort(key=lambda x: x["position"])
    log.info(f"サムネイル取得完了 — {len(results)}/{len(unique)}本成功")
    return results


# ─── システムプロンプト ────────────────────────────────
SYSTEM_PROMPT = """あなたは澤田一進のマーケティング哲学を完全に内在化した、記事LPレビュー専門のAIです。

## あなたの判断基準（パクの哲学）
- 「愛ならどうする？」— N1のため、ユーザーのために判断する
- 「真に偉大か？」— そこそこ良いで満足しない。感動的なアウトプットを目指す
- 小さな嘘をつかない — 本物の体験・言葉だけを使う。都合の良い誇張はしない
- 超一流であろう — フィードバックもその業界のトップレベルで

## 記事LPの本質（澤田一進の哲学）
- 記事LPは「商品紹介の媒体」ではなく「セールスコピー」
- 購入CVRの約65%を記事LPが決める
- ゴールは読者に「損したくない」「得したい」を確信させること
- 「なんとなく良さそう」ではCVRは出ない

## ビジネスモデル前提
- 単品リピート通販（定期購入）
- 広告クリックから即定期購入申込みが最終ゴール（高難易度の記事LP）

## 記事LP 18パート構成（評価軸）
前半（温度感UP）: ①FV ②悩み共感 ③対策共感 ④未来想像 ⑤方法提示 ⑥ベネフィット視覚化 ⑦口コミ
教育パート（常識覆す）: ⑧新事実 ⑨真の原因 ⑩新パラダイム ⑪商品導入（伏線回収）
後半（確信・安心・行動）: ⑫実証 ⑬ベネフィット ⑭権威信頼 ⑮使ってみた ⑯ベネフィット再 ⑰口コミ多様 ⑱オファー

## 設計の大原則
- 一期通感: FVのキャッチ→教育→商品が全て繋がり「この商品じゃなきゃ私の悩みが解決しない」という結論に向かう
- ベネフィットを何度でも: 実証後・権威後・使ってみた後に繰り返し差し込む
- まだ商品を出さない: 前半〜教育パートは商品名を出さずに読者を教育する
- ペルソナなくして記事LPなし: 実在する「Aさん」に向けて書く

## 売れてる記事LP 4本から学んだ秘訣（必ず評価軸に入れる）

### ① 「皆まで言わずに」の法則
売れてる記事LPはテキストで答えを言わない。ビジュアルで直感的に理解させる。
- ❌ NG: 「この商品はシワに効きます」
- ✅ OK: 80代の美肌写真を先に��せる → 「なぜ？」と読者が自分で問いを立てる
- 「��？」「!?」「のはずでした、が…」で止めて、読者に想像させる
- 評価軸: テキストで説明しすぎていないか。ビジュアルが「問い」を立てているか

### ② ビジュアルファースト設計
売れてる記事LP（腸活: テキスト971文字・動画14本 / 腰痛: 画像52枚・動画32本）は動画・画像が情報の主体。テキストは補足。
- Before/After、使用シーン、感情シーン（孫と遊ぶ、鏡を見て驚く）を動画で見せる
- テキスト:ビジュアル = 3:7 が売れてるLPの比率感
- 評価軸: 動画・画像の密度は十分か。テキストに頼りすぎていないか

### ③ 感情先行→論理展開
売れてるLPは感情から入って論理で裏付ける。
- 腰痛LP: 「孫と遊びたいのに痛くて…」（感情）→「4つの原因がある」（論理）
- 手シワLP: おばあちゃんの手の写真（感情）→「コラーゲンが届いていなかった」（論理）
- 評価軸: FVは感情から入っているか。論理説明の前に共感があるか

### ④ 逆接の引っ張り構造
「〇〇なはずでした、が…」「〇〇と思っていませんか？それ実は…」のパターンで既存認識を覆す。
常識を否定してから新方法を提示する流れが売れてるLPの核心。

### ⑤ 口コミは「私と同じ状況」
「52歳・デスクワーク」「中学生の頃から慢性的に…」など境遇が具体的。
数字・属性・感情・行動変化をセットで入れる。匿名口コミは弱い。"""


# ─── DPro ジャンル判定 ──────────────────────────────────
BENCHMARK_PATH = Path(__file__).parent / "dpro_benchmark.json"

def detect_genre(article_data: dict, client: anthropic.Anthropic) -> dict:
    """LP テキスト冒頭からジャンル・悩み・ターゲット・キーワードを判定（Haiku 軽量呼び出し）"""
    sections = article_data.get("sections", [])
    text = "\n".join(s["content"] for s in sections if s["type"] == "text")[:2500]
    if not text.strip():
        return {}
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "以下の記事LPの冒頭テキストを読み、JSON のみで返してください。\n"
                    "フィールド: genre（ジャンル名・日本語）, worry（主な悩み・課題・日本語）, "
                    "target（ターゲット属性・日本語）, keywords（関連キーワードリスト・日本語5〜10個）\n\n"
                    f"テキスト:\n{text}\n\nJSON only:"
                )
            }]
        )
        raw = resp.content[0].text.strip()
        # コードブロックを除去
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        log.warning(f"ジャンル判定失敗: {e}")
        return {}


def find_genre_by_name(genre_hint: str) -> dict | None:
    """ジャンル指定文字列（例: '成長期' '膝' '腸活'）から benchmark.json のジャンルを直接引く"""
    if not BENCHMARK_PATH.exists():
        return None
    try:
        with open(BENCHMARK_PATH, encoding="utf-8") as f:
            benchmark = json.load(f)
    except Exception:
        return None
    hint = genre_hint.strip()
    for genre in benchmark.get("genres", []):
        # ジャンル名・キーワードのどちらかにヒントが含まれていればOK
        if hint in genre["name"] or any(hint in kw or kw in hint for kw in genre["keywords"]):
            log.info(f"ジャンル指定マッチ: '{hint}' → {genre['name']}")
            return genre
    log.warning(f"ジャンル指定 '{hint}' が benchmark に見つかりません")
    return None


def get_competitor_insights(genre_info: dict) -> dict | None:
    """benchmark.json からキーワード類似度で最もマッチするジャンルと競合TOP3を返す"""
    if not BENCHMARK_PATH.exists():
        log.warning("dpro_benchmark.json が見つかりません")
        return None
    try:
        with open(BENCHMARK_PATH, encoding="utf-8") as f:
            benchmark = json.load(f)
    except Exception as e:
        log.warning(f"benchmark.json 読み込みエラー: {e}")
        return None

    detected_kws = (
        genre_info.get("keywords", []) +
        genre_info.get("genre", "").split() +
        genre_info.get("worry", "").split("・")
    )
    detected_kws = [kw.strip() for kw in detected_kws if kw.strip()]

    best_genre = None
    best_score = 0
    for genre in benchmark.get("genres", []):
        bench_kws = genre.get("keywords", [])
        score = sum(
            1 for dkw in detected_kws
            if any(dkw in bkw or bkw in dkw for bkw in bench_kws)
        )
        if score > best_score:
            best_score = score
            best_genre = genre

    if not best_genre or best_score < 2:
        log.info(f"類似ジャンルなし（最高スコア: {best_score}）")
        return None

    log.info(f"類似ジャンル判定: {best_genre['name']}（スコア: {best_score}）")
    return best_genre


def build_competitor_block(genre_info: dict, competitor: dict) -> str:
    """競合インサイトをプロンプト用テキストブロックに変換"""
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"【DPro競合インサイト】ジャンル: {competitor['name']}",
        f"このLPの判定 → 悩み: {genre_info.get('worry','不明')} ／ ターゲット: {genre_info.get('target','不明')}",
        "",
        f"■ 勝ちLPの共通パターン:",
        competitor.get("winning_pattern", ""),
        "",
        "■ 今伸びてる競合LP TOP3（DPro cost_difference順）:",
    ]
    for item in competitor.get("top_items", []):
        lines += [
            f"",
            f"【{item['rank']}位】{item['product_name']}（{item['advertiser']}）",
            f"  媒体: {item['media']} ／ 形式: {item['transition_type']}",
            f"  推定広告費増加: ¥{item['cost_difference']:,}" if item.get('cost_difference') else "",
            f"  広告文: {item['ad_sentence']}",
            f"  FVフック: {item['fv_hook']}",
            f"  勝ちタクティクス:",
        ]
        for tactic in item.get("key_tactics", []):
            lines.append(f"    ・{tactic}")
        lines.append(f"  LPの流れ: {item.get('lp_flow','')}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(l for l in lines if l is not None)


# ─── フィードバック生成（DOM順セクション＋統計＋18パート分析）───
def generate_feedback(article_data: dict, url: str, client: anthropic.Anthropic,
                       video_thumbnails: list = [], competitor: dict | None = None,
                       genre_info: dict | None = None) -> str:
    sections  = article_data.get("sections", [])
    stats     = article_data.get("stats", {})
    offer_cut = article_data.get("offer_detected", False)

    # サムネイルをURL→b64のマップに変換
    thumb_map = {t["url"]: t["b64"] for t in video_thumbnails}

    # ── メッセージコンテンツ組み立て（DOM順：テキスト＋画像/動画セット）──
    content = []

    # 競合インサイトブロック（ジャンル判定済みの場合のみ先頭に追加）
    if competitor and genre_info:
        content.append({
            "type": "text",
            "text": build_competitor_block(genre_info, competitor)
        })

    content.append({
        "type": "text",
        "text": (
            f"以下の記事LPをDOM順（テキスト＋画像・動画のセット）でレビューしてください。\n"
            f"{'（オファーセクション手前まで）' if offer_cut else ''}\n\n"
            f"記事URL: {url}\n\n"
            f"📊 記事構成: 文字 {stats.get('chars',0):,}字 ／ "
            f"画像 {stats.get('images',0)}枚 ／ 動画 {stats.get('videos',0)}本\n\n"
            f"以下はテキストと画像・動画が記事中の出現順に並んでいます。\n"
            f"各セットで「このテキストにこのビジュアルが対応している」という構造を読み取ってください。"
        )
    })

    # DOM順でセクションを渡す（テキスト→画像/動画の順番を保持）
    for sec in sections:
        if sec["type"] == "text":
            content.append({"type": "text", "text": f"\n{sec['content']}"})

        elif sec["type"] == "image":
            content.append({
                "type": "image",
                "source": {"type": "url", "url": sec["url"]}
            })

        elif sec["type"] == "video":
            b64 = thumb_map.get(sec["url"])
            if b64:
                content.append({
                    "type": "text",
                    "text": f"[動画{sec['position']} サムネイル]"
                })
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}
                })

    # レビュー指示
    content.append({
        "type": "text",
        "text": """

---

以下のスタイルでフィードバックしてください。

## 澤田一進のFBスタイル（必ず守る）
- 口語・短い文で書く（「なんか急で違和感」「どゆいみ？」レベルで良い）
- 指摘だけで終わらない。必ず「こうしたら？」の代替コピーor構成案をセットで書く
- 代替コピーは実際に使えるレベルで具体的に書く（「〇〇が原因ではなかった？！」など）
- 素材の追加は「どのパートに何を入れる」を具体的に指示する
- 【絶対禁止】CTAに関する改善提案は一切するな。記事LPの設計思想に反する。
- ポジティブな指摘も入れる（良いところは良いと言う）

## 出力フォーマット（Slack Canvas用 Markdown）

必ず以下の構造・順番で出力してください。見出しは ## を使う。

## 📊 記事構成

冒頭で受け取った文字数・画像枚数・動画本数を記載。
テキスト:ビジュアル比率を計算して記載（売れてるLPは3:7が目安）。

## 🗺 18パート チェック

Markdownの表形式で出力してください：

| パート | 判定 | コメント |
|--------|------|---------|
| ① FV | ✅/⚠️/❌ | （⚠️❌のみコメント） |
...⑱まで全パートを書く。

## 🎯 一期通感: X/10

1文で理由を書く。

## 📝 パート別FB

問題があるパートのみ。各パートを ### 見出しにして：
→ 指摘（口語・短く）
→ 改善案（具体的なコピーまで）

## 🖼 ビジュアルFB

テキスト＋画像/動画のセットを見て気になる点と改善案。
「皆まで言わずに」の観点（ビジュアルで問いを立てているか）を必ず評価。

## 📸 追加したい素材

📷 画像：どのパートに・何の画像を・どう撮るか
🎬 動画：どのパートに・何秒の動画を・どんなシーンか
✍️ 口コミ：どんな属性・内容を何件

## 🏆 競合比較（DProトレンド）

上記の競合インサイストを踏まえて：
- このLPが競合と比べて「勝てている点」を1〜2個
- 「負けている・足りない点」を2〜3個（具体的に何が違うか）
- 「すぐ盗むべき競合の勝ちタクティクス」を1〜2個

このセクションは競合インサイトがある場合のみ出力してください。

## 📌 今週伸びてる競合記事3本（参考LP提案）

競合インサイトから、このLPと同ジャンルで今伸びている好調記事を3本ピックアップして提案してください。
各記事について以下を出力：
- 【商品名】（運営社）
- 📣 広告文（実際の配信コピー）
- 🎯 FVフック（冒頭の掴み）
- 🔗 URL（あれば）
- 💡 「ここを盗むべき」ポイント1点（なぜ今伸びているか・何が効いているか）

このセクションは競合インサイトがある場合のみ出力してください。

## 💬 総評

「真に偉大か？」視点から1〜2文。本音で。

各FBは現場が明日から動けるレベルで具体的に。評価より改善案を優先する。"""
    })

    # Vision対応でまず試みる。画像URLエラーが出たらテキストのみで再試行
    # Rate limitは最大3回リトライ（60秒待機）
    def _call_claude(msg_content):
        for attempt in range(3):
            try:
                return client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=16000,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": msg_content}],
                )
            except anthropic.RateLimitError:
                if attempt < 2:
                    wait = 60 * (attempt + 1)
                    log.warning(f"Rate limit。{wait}秒待機してリトライします（{attempt + 1}/3）")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError("リトライ上限に達しました")

    def _call_with_continuation(msg_content):
        """途中で切れた場合（stop_reason=max_tokens）は続きを取得して結合"""
        response = _call_claude(msg_content)
        result = response.content[0].text

        # max_tokensで止まった場合は続きをリクエスト
        if response.stop_reason == "max_tokens":
            log.warning("FBがmax_tokensで途中終了。続きを取得します。")
            continuation_messages = [
                {"role": "user", "content": msg_content},
                {"role": "assistant", "content": result},
                {"role": "user", "content": "続きを書いてください。"},
            ]
            for attempt in range(3):
                try:
                    cont = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=8000,
                        system=SYSTEM_PROMPT,
                        messages=continuation_messages,
                    )
                    result += cont.content[0].text
                    log.info("FB続き取得完了")
                    break
                except anthropic.RateLimitError:
                    if attempt < 2:
                        time.sleep(60 * (attempt + 1))
                    else:
                        log.warning("続き取得のRate limit上限。部分FBで返します。")

        return result

    try:
        return _call_with_continuation(content)
    except anthropic.BadRequestError as e:
        if "Could not process image" in str(e) or "image" in str(e).lower():
            log.warning("画像URLエラー。テキストのみで再試行します。")
            text_only_content = [c for c in content if c["type"] == "text"]
            return _call_with_continuation(text_only_content)
        else:
            raise


# ─── 記事スクリーンショット取得 ───────────────────────────
SCREENSHOT_JPEG_QUALITY = 60   # 圧縮率（高さ制限なし・ファイルサイズを質で調整）

def take_article_screenshot(url: str) -> str:
    """Playwrightで記事全体をfull_page=Trueでスクショ → JPEG圧縮してbase64文字列を返す"""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 750, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            )
            page.goto(url, wait_until="networkidle", timeout=30000)
            # lazyload展開のためページ末尾までスクロール
            page.evaluate("""async () => {
                await new Promise(resolve => {
                    let last = 0;
                    const timer = setInterval(() => {
                        window.scrollBy(0, 800);
                        const cur = window.scrollY;
                        if (cur === last) { clearInterval(timer); resolve(); }
                        last = cur;
                    }, 100);
                });
                window.scrollTo(0, 0);
            }""")
            page.wait_for_timeout(1000)

            # ページ全体をキャプチャ（高さ制限なし）
            png_bytes = page.screenshot(full_page=True)
            browser.close()

        # JPEG圧縮のみ（クロップなし）
        img = Image.open(io.BytesIO(png_bytes))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=SCREENSHOT_JPEG_QUALITY, optimize=True)
        jpg_bytes = buf.getvalue()

        b64 = base64.standard_b64encode(jpg_bytes).decode()
        log.info(f"スクショ取得完了 — {len(jpg_bytes)//1024}KB (高さ:{img.height}px)")
        return b64
    except Exception as e:
        log.warning(f"スクショ取得失敗: {e}")
        return ""


# ─── HTMLレポート生成 ──────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, "Hiragino Sans", sans-serif; display: flex; height: 100vh; overflow: hidden; background: #f5f5f7; }}
  .left {{ width: 48%; overflow-y: auto; background: #fff; border-right: 1px solid #ddd; }}
  .left-header {{ position: sticky; top: 0; background: #1a1a2e; color: #fff; padding: 12px 16px; font-size: 13px; z-index: 10; }}
  .left img {{ width: 100%; display: block; }}
  .right {{ width: 52%; overflow-y: auto; padding: 24px 28px; }}
  .right h1 {{ font-size: 18px; color: #1a1a2e; margin-bottom: 4px; }}
  .meta {{ font-size: 12px; color: #888; margin-bottom: 24px; }}
  .right h2 {{ font-size: 15px; color: #1a1a2e; margin: 24px 0 10px; padding-bottom: 6px; border-bottom: 2px solid #e8e8e8; }}
  .right h3 {{ font-size: 14px; color: #333; margin: 16px 0 6px; }}
  .right p {{ font-size: 14px; line-height: 1.8; color: #333; margin-bottom: 10px; }}
  .right ul {{ padding-left: 20px; margin-bottom: 10px; }}
  .right li {{ font-size: 14px; line-height: 1.8; color: #333; }}
  table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 13px; }}
  th {{ background: #1a1a2e; color: #fff; padding: 8px 10px; text-align: left; }}
  td {{ border: 1px solid #e0e0e0; padding: 8px 10px; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  .stat-bar {{ display: flex; gap: 12px; margin: 12px 0; flex-wrap: wrap; }}
  .stat {{ background: #1a1a2e; color: #fff; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: bold; }}
  blockquote {{ border-left: 3px solid #e8e8e8; padding-left: 12px; color: #555; margin: 8px 0; }}
  code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
</style>
</head>
<body>
  <div class="left">
    <div class="left-header">📄 記事プレビュー — {url_short}</div>
    {screenshot_html}
  </div>
  <div class="right">
    <h1>📋 記事LPフィードバック</h1>
    <p class="meta">{date_str} ／ {url}</p>
    <div class="stat-bar">
      <span class="stat">文字 {chars:,}字</span>
      <span class="stat">画像 {images}枚</span>
      <span class="stat">動画 {videos}本</span>
      <span class="stat">{offer_line}</span>
    </div>
    {feedback_html}
  </div>
</body>
</html>"""


def generate_html_report(feedback_md: str, screenshot_b64: str, url: str, stats: dict, offer_trigger: str) -> bytes:
    """フィードバックMarkdown＋スクショ → 自己完結HTMLのバイト列を返す"""
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    url_short = url.split("/")[2] if "/" in url else url[:40]
    offer_line = f"「{offer_trigger}」前まで" if offer_trigger else "全体"

    # MarkdownをHTMLに変換（テーブル・コードブロック対応）
    feedback_html = md_lib.markdown(
        feedback_md,
        extensions=["tables", "fenced_code"]
    )

    screenshot_html = (
        f'<img src="data:image/jpeg;base64,{screenshot_b64}" alt="記事スクショ">'
        if screenshot_b64
        else '<p style="padding:20px;color:#888">スクリーンショット取得失敗</p>'
    )

    html = HTML_TEMPLATE.format(
        title=f"記事LPフィードバック {date_str}",
        url=url,
        url_short=url_short,
        date_str=date_str,
        chars=stats.get("chars", 0),
        images=stats.get("images", 0),
        videos=stats.get("videos", 0),
        offer_line=offer_line,
        screenshot_html=screenshot_html,
        feedback_html=feedback_html,
    )
    return html.encode("utf-8")


# ─── Slack ファイル添付 ────────────────────────────────
def upload_html_report(html_bytes: bytes, url: str, slack: WebClient, channel: str, thread_ts: str) -> bool:
    """HTMLレポートをSlackスレッドにファイル添付"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"fb_{date_str}.html"
    try:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            f.write(html_bytes)
            tmp_path = f.name
        slack.files_upload_v2(
            channel=channel,
            thread_ts=thread_ts,
            file=tmp_path,
            filename=filename,
            title=f"記事LPフィードバック — {date_str}",
        )
        os.unlink(tmp_path)
        log.info(f"HTMLレポートアップロード完了 — {filename} ({len(html_bytes)//1024}KB)")
        return True
    except Exception as e:
        log.warning(f"HTMLアップロード失敗: {e}")
        return False


# ─── Slack Canvas作成 ─────────────────────────────────
def post_as_canvas(feedback_md: str, url: str, stats: dict, slack: WebClient, channel: str, thread_ts: str):
    """フィードバックをSlack Canvasとして作成しスレッドにリンク投稿"""
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"記事LPフィードバック — {date_str}"

    try:
        res = slack.canvases_create(
            title=title,
            document_content={"type": "markdown", "markdown": feedback_md},
        )
        canvas_id = res["canvas_id"]

        # CanvasをチャンネルのメンバーがアクセスできるようACLを設定
        slack.canvases_access_set(
            canvas_id=canvas_id,
            access_level="write",
            channel_ids=[channel],
        )

        # Canvas URLを取得して組み立て
        # slack_sdk はcanvas URLを返さないのでワークスペースドメインから組み立て
        team_res = slack.team_info()
        domain = team_res["team"]["domain"]
        canvas_url = f"https://{domain}.slack.com/docs/{canvas_id}"

        slack.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"📋 *フィードバックCanvasを作成しました*\n👉 {canvas_url}",
            mrkdwn=True,
        )
        log.info(f"Canvas作成完了 — {canvas_id}")
        return True

    except Exception as e:
        log.warning(f"Canvas作成失敗（テキスト返信にフォールバック）: {e}")
        return False


# ─── メッセージ処理 ───────────────────────────────────
GENRE_ALIASES = {
    "成長期": "成長期", "成長": "成長期", "身長": "成長期",
    "ジュニア": "成長期", "子供": "成長期", "こども": "成長期", "子ども": "成長期",
    "膝": "膝", "ひざ": "膝", "関節": "膝", "グルコサミン": "膝",
    "腸活": "腸活", "腸": "腸活", "便秘": "腸活",
    "美容": "美容", "コラーゲン": "美容", "シワ": "美容", "エイジング": "美容",
    "睡眠": "睡眠", "不眠": "睡眠", "眠れ": "睡眠",
}

def extract_genre_hint(text: str) -> str:
    """メッセージテキストからジャンル指定を抽出する。URLと'フィードバック'を除いた残りを解析。"""
    # URL を除去
    clean = re.sub(r'https?://\S+', '', text)
    # トリガーワードを除去
    for kw in TRIGGER_KEYWORDS:
        clean = clean.replace(kw, "")
    clean = clean.strip()
    if not clean:
        return ""
    # エイリアスマップで検索
    for alias, canonical in GENRE_ALIASES.items():
        if alias in clean:
            return canonical
    # そのままの文字列を返す（find_genre_by_name が処理）
    return clean.strip()


def process_message(msg: dict, slack: WebClient, client: anthropic.Anthropic):
    text = msg.get("text", "")
    ts   = msg.get("ts", "")

    urls = extract_urls(text)
    if not urls:
        return

    url = urls[0]

    # ジャンル手動指定チェック
    genre_hint = extract_genre_hint(text)
    forced_genre = find_genre_by_name(genre_hint) if genre_hint else None

    log.info(f"フィードバック依頼検知 — ts:{ts} url:{url} genre_hint:'{genre_hint}'")

    # 受付通知
    try:
        slack.chat_postMessage(
            channel=CHANNEL_ID,
            thread_ts=ts,
            text="記事を読んでいます（JS実行＋DOM順解析）... 🔍",
        )
    except SlackApiError as e:
        log.error(f"受付返信エラー: {e}")

    # 記事取得（DOM順解析）
    article_data = fetch_article_with_images(url)
    stats = article_data.get("stats", {})

    # 統計をSlackに通知
    offer_trigger = article_data.get("offer_trigger")
    offer_line = f"_「{offer_trigger}」の手前まで読み込みました_" if offer_trigger else "_記事全体を読み込みました_"
    try:
        slack.chat_postMessage(
            channel=CHANNEL_ID,
            thread_ts=ts,
            text=(
                f"📊 記事解析完了！\n"
                f"文字 *{stats.get('chars', 0):,}字* ／ "
                f"画像 *{stats.get('images', 0)}枚* ／ "
                f"動画 *{stats.get('videos', 0)}本*\n"
                f"{offer_line}\n"
                f"フィードバック生成中です... 少々お待ちください ✍️"
            ),
            mrkdwn=True,
        )
    except SlackApiError as e:
        log.error(f"統計通知エラー: {e}")

    # ── ジャンル判定 ＆ 競合インサイト取得 ──────────────────
    genre_info = {}
    competitor = None

    if forced_genre:
        # ジャンル手動指定 → Haiku スキップ
        competitor = forced_genre
        genre_info = {
            "genre": forced_genre["name"],
            "worry": forced_genre["worry"],
            "target": forced_genre["target"],
            "keywords": forced_genre["keywords"],
        }
        try:
            slack.chat_postMessage(
                channel=CHANNEL_ID, thread_ts=ts,
                text=(
                    f"🎯 ジャンル指定: *{forced_genre['name']}*\n"
                    f"→ 競合TOP{len(forced_genre['top_items'])}本を参照します\n"
                    "フィードバック生成中... ✍️"
                ),
                mrkdwn=True,
            )
        except SlackApiError:
            pass
    else:
        # 自動判定
        try:
            slack.chat_postMessage(
                channel=CHANNEL_ID, thread_ts=ts,
                text="🔍 ジャンル自動判定中（DPro競合データ照合）...",
            )
        except SlackApiError:
            pass
        genre_info = detect_genre(article_data, client)
        if genre_info:
            competitor = get_competitor_insights(genre_info)
            genre_label = f"{genre_info.get('genre','不明')} ／ ターゲット: {genre_info.get('target','不明')}"
            comp_label = f"類似ジャンル: *{competitor['name']}* — TOP{len(competitor['top_items'])}競合を参照します" if competitor else "該当ジャンルなし（汎用評価軸で実施）"
            try:
                slack.chat_postMessage(
                    channel=CHANNEL_ID, thread_ts=ts,
                    text=f"🎯 ジャンル判定完了\n→ {genre_label}\n→ {comp_label}\nフィードバック生成中... ✍️",
                    mrkdwn=True,
                )
            except SlackApiError:
                pass
        else:
            try:
                slack.chat_postMessage(
                    channel=CHANNEL_ID, thread_ts=ts,
                    text="ジャンル判定スキップ。汎用評価軸でFB生成中... ✍️",
                )
            except SlackApiError:
                pass

    # 動画サムネイル並列取得 ＆ 記事スクショを並列で実行
    video_thumbnails = []
    screenshot_b64 = ""
    from concurrent.futures import ThreadPoolExecutor as _TPE
    with _TPE(max_workers=2) as ex:
        thumb_future = ex.submit(
            lambda: extract_video_thumbnails(article_data["videos"]) if article_data.get("videos") else []
        )
        shot_future = ex.submit(take_article_screenshot, url)
        try:
            video_thumbnails = thumb_future.result()
            log.info(f"サムネイル取得完了: {len(video_thumbnails)}本")
        except Exception as e:
            log.warning(f"サムネイル取得スキップ: {e}")
        try:
            screenshot_b64 = shot_future.result()
        except Exception as e:
            log.warning(f"スクショ取得スキップ: {e}")

    # フィードバック生成（競合インサイト付き）
    feedback = generate_feedback(article_data, url, client, video_thumbnails,
                                  competitor=competitor, genre_info=genre_info)

    # HTMLレポート生成 → Slackにファイル添付。失敗したらCanvas → テキストにフォールバック
    html_bytes = generate_html_report(feedback, screenshot_b64, url, stats, offer_trigger)
    uploaded = upload_html_report(html_bytes, url, slack, CHANNEL_ID, ts)

    if uploaded:
        # HTML開き方の案内
        try:
            slack.chat_postMessage(
                channel=CHANNEL_ID,
                thread_ts=ts,
                text=(
                    "📂 *HTMLレポートの開き方*\n"
                    "1️⃣ 上のファイルをクリック\n"
                    "2️⃣ 右上の「・・・」→「ダウンロード」\n"
                    "3️⃣ ダウンロードしたファイルをダブルクリック → ブラウザで開く\n"
                    "_左に記事スクショ、右にFBが表示されます👀_"
                ),
                mrkdwn=True,
            )
        except SlackApiError:
            pass

    if not uploaded:
        # Canvas フォールバック
        canvas_ok = post_as_canvas(feedback, url, stats, slack, CHANNEL_ID, ts)
        if not canvas_ok:
            # テキスト分割フォールバック
            chunks = [feedback[i:i+2900] for i in range(0, len(feedback), 2900)]
            for i, chunk in enumerate(chunks):
                prefix = "📝 *記事フィードバック*\n\n" if i == 0 else ""
                try:
                    slack.chat_postMessage(
                        channel=CHANNEL_ID, thread_ts=ts,
                        text=f"{prefix}{chunk}", mrkdwn=True,
                    )
                except SlackApiError as e:
                    log.error(f"返信エラー (chunk {i}): {e}")
            log.info(f"テキスト返信完了 — ts:{ts}")
        else:
            log.info(f"Canvas返信完了 — ts:{ts}")
    else:
        log.info(f"HTMLレポート返信完了 — ts:{ts}")


# ─── トリガー判定 ─────────────────────────────────────
def is_trigger(text: str) -> bool:
    return any(kw in text.lower() for kw in TRIGGER_KEYWORDS)


# ─── メインループ ─────────────────────────────────────
def run():
    log.info("=== Slack フィードバックBot v6 起動（Canvas返信対応）===")

    slack_token   = get_env("SLACK_BOT_TOKEN")
    anthropic_key = get_env("ANTHROPIC_API_KEY")

    slack  = WebClient(token=slack_token)
    client = anthropic.Anthropic(api_key=anthropic_key)

    state = load_state()

    while True:
        try:
            kwargs = {"channel": CHANNEL_ID, "limit": 20}
            if state["last_ts"]:
                kwargs["oldest"] = state["last_ts"]

            result   = slack.conversations_history(**kwargs)
            messages = result.get("messages", [])

            if messages:
                new_messages = [
                    m for m in reversed(messages)
                    if m.get("ts") not in state["processed"]
                    and not m.get("thread_ts")
                ]

                for msg in new_messages:
                    if is_trigger(msg.get("text", "")) and extract_urls(msg.get("text", "")):
                        process_message(msg, slack, client)

                    state["processed"].append(msg.get("ts"))
                    state["last_ts"] = msg.get("ts")

                state["processed"] = state["processed"][-200:]
                save_state(state)

        except SlackApiError as e:
            log.error(f"Slack API エラー: {e}")
        except Exception as e:
            log.error(f"予期しないエラー: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()