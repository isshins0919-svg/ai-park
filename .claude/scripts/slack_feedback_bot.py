#!/usr/bin/env python3
"""
Slack 記事フィードバックBot v4
- #yomite_ai-kiji_fb を2分おきにポーリング
- 「フィードバック」+ URL を含む投稿を検知
- Playwright でJS実行後の画像URLを取得（SquadBeyond対応）
- オファー前まで テキスト＋画像(Claude Vision)＋動画(Gemini)を読み込み
- フィードバック＋コンテンツ制作ブリーフを返信
"""

import re
import json
import time
import subprocess
import logging
import tempfile
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import anthropic
import google.genai as genai
from google.genai import types as genai_types
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
    val = subprocess.run(
        ["zsh", "-i", "-c", f"echo ${key}"],
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
        for trigger in OFFER_TRIGGERS:
            pos = full_html.find(trigger)
            if pos != -1 and pos < offer_pos:
                offer_pos = pos
                offer_detected = True

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
        }

    except Exception as e:
        log.error(f"記事取得エラー(Playwright): {e}")
        return {"sections": [], "videos": [], "stats": {"chars": 0, "images": 0, "videos": 0}, "offer_detected": False}


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
- ✅ OK: 80代の美肌写真を先に見せる → 「なぜ？」と読者が自分で問いを立てる
- 「え？」「!?」「のはずでした、が…」で止めて、読者に想像させる
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


# ─── フィードバック生成（DOM順セクション＋統計＋18パート分析）───
def generate_feedback(article_data: dict, url: str, client: anthropic.Anthropic, video_thumbnails: list = []) -> str:
    sections  = article_data.get("sections", [])
    stats     = article_data.get("stats", {})
    offer_cut = article_data.get("offer_detected", False)

    # サムネイルをURL→b64のマップに変換
    thumb_map = {t["url"]: t["b64"] for t in video_thumbnails}

    # ── メッセージコンテンツ組み立て（DOM順：テキスト＋画像/動画セット）──
    content = []

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

## 出力フォーマット（Slack mrkdwn）

*━━ 記事LPフィードバック ━━*

*📊 記事構成スコア*
文字 {chars}字 ／ 画像 {images}枚 ／ 動画 {videos}本
テキスト:ビジュアル比率 → （売れてるLPは3:7が目安。この記事は？）

*🗺 18パート マッピング*
（各パートが「ある／弱い／ない」を一覧で。問題点があればコメント）
① FV: ／ ② 悩み共感: ／ ③ 対策共感: ／ ④ 未来想像: ／ ⑤ 方法提示:
⑥ ベネフィット視覚化: ／ ⑦ 口コミ前半: ／ ⑧ 新事実: ／ ⑨ 真の原因:
⑩ 新パラダイム: ／ ⑪ 商品導入: ／ ⑫ 実証: ／ ⑬ ベネフィット:
⑭ 権威信頼: ／ ⑮ 使ってみた: ／ ⑯ ベネフィット再: ／ ⑰ 口コミ多様: ／ ⑱ オファー:

*🎯 一期通感: X/10*
（1文で理由）

*📝 パート別FB*
（問題があるパートのみ。番号＋具体的な改善案をセットで）

*🖼 ビジュアルFB*
（テキスト＋画像/動画の対応を見て。「皆まで言わずに」の観点も）

*📸 追加したい素材*
📷 （どのパートに・何の画像を・どう撮るか）
🎬 （どのパートに・何秒の動画を・どんなシーンか）
✍️ （どんな属性・内容の口コミを何件）

*💬 総評*
（「真に偉大か？」視点から1〜2文。本音で）

---
各FBは現場が明日から動けるレベルで具体的に。評価より改善案を優先する。"""
    })

    # Vision対応でまず試みる。画像URLエラーが出たらテキストのみで再試行
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.BadRequestError as e:
        if "Could not process image" in str(e) or "image" in str(e).lower():
            log.warning("画像URLエラー。テキストのみで再試行します。")
            text_only_content = [c for c in content if c["type"] == "text"]
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text_only_content}],
            )
        else:
            raise

    return response.content[0].text


# ─── メッセージ処理 ───────────────────────────────────
def process_message(msg: dict, slack: WebClient, client: anthropic.Anthropic):
    text = msg.get("text", "")
    ts   = msg.get("ts", "")

    urls = extract_urls(text)
    if not urls:
        return

    url = urls[0]
    log.info(f"フィードバック依頼検知 — ts:{ts} url:{url}")

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
    try:
        slack.chat_postMessage(
            channel=CHANNEL_ID,
            thread_ts=ts,
            text=(
                f"📊 記事解析完了！\n"
                f"文字 *{stats.get('chars', 0):,}字* ／ "
                f"画像 *{stats.get('images', 0)}枚* ／ "
                f"動画 *{stats.get('videos', 0)}本*\n"
                f"フィードバック生成中です... 少々お待ちください ✍️"
            ),
            mrkdwn=True,
        )
    except SlackApiError as e:
        log.error(f"統計通知エラー: {e}")

    # 動画サムネイル並列取得
    video_thumbnails = []
    if article_data.get("videos"):
        try:
            video_thumbnails = extract_video_thumbnails(article_data["videos"])
            log.info(f"サムネイル取得完了: {len(video_thumbnails)}本")
        except Exception as e:
            log.warning(f"サムネイル取得スキップ: {e}")

    # フィードバック生成
    feedback = generate_feedback(article_data, url, client, video_thumbnails)

    # Slackへ返信（2000文字超の場合は分割）
    chunks = [feedback[i:i+2900] for i in range(0, len(feedback), 2900)]
    for i, chunk in enumerate(chunks):
        prefix = "*📝 記事フィードバック*\n\n" if i == 0 else ""
        try:
            slack.chat_postMessage(
                channel=CHANNEL_ID,
                thread_ts=ts,
                text=f"{prefix}{chunk}",
                mrkdwn=True,
            )
        except SlackApiError as e:
            log.error(f"返信エラー (chunk {i}): {e}")

    log.info(f"フィードバック送信完了 — ts:{ts} {len(chunks)}分割")


# ─── トリガー判定 ─────────────────────────────────────
def is_trigger(text: str) -> bool:
    return any(kw in text.lower() for kw in TRIGGER_KEYWORDS)


# ─── メインループ ─────────────────────────────────────
def run():
    log.info("=== Slack フィードバックBot v5 起動（DOM順解析＋18パート＋サムネイル）===")

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