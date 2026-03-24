#!/usr/bin/env python3
"""
Slack 記事フィードバックBot v3
- #yomite_ai-kiji_fb を2分おきにポーリング
- 「フィードバック」+ URL を含む投稿を検知
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

# ─── 設定 ─────────────────────────────────────────────
CHANNEL_ID     = "C0AMYLU2W5D"   # #yomite_ai-kiji_fb
POLL_INTERVAL  = 120              # 2分おきにチェック
MAX_IMAGES     = 10               # Vision に渡す画像の上限
MAX_VIDEOS     = 3                # Gemini に渡す動画の上限
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

# ─── 記事取得（オファー前まで）＋ 画像URL抽出 ────────────
def fetch_article_with_images(url: str) -> dict:
    """
    記事HTMLを取得し、オファーセクション手前でカット。
    テキストと画像URL（最大MAX_IMAGES枚）を返す。
    """
    try:
        res = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

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

        # テキスト抽出
        article_text = pre_offer_soup.get_text(separator="\n", strip=True)[:8000]

        # 画像URL抽出
        images = []
        for img in pre_offer_soup.find_all("img"):
            if len(images) >= MAX_IMAGES:
                break

            # data-src を優先（lazy load対応）
            src = (img.get("data-src") or img.get("data-lazy-src")
                   or img.get("data-original") or img.get("src"))
            if not src or "lazy.png" in src or "placeholder" in src:
                continue

            # 絶対URL化
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = base_url + src

            if not src.startswith("http"):
                continue

            # 小さい装飾画像をスキップ（幅または高さが指定されていて50px以下）
            w = img.get("width", "")
            h = img.get("height", "")
            if (str(w).isdigit() and int(w) <= 50) or (str(h).isdigit() and int(h) <= 50):
                continue

            # 近傍コンテキスト
            parent = img.find_parent(["figure", "section", "div", "p"])
            context = parent.get_text(strip=True)[:100] if parent else ""

            images.append({
                "url": src,
                "context": context,
                "position": len(images) + 1,
            })

        # 動画URL抽出
        videos = []
        # <video> タグ
        for vid in pre_offer_soup.find_all("video"):
            if len(videos) >= MAX_VIDEOS:
                break
            # data-src を優先（lazy load対応）
            src = vid.get("data-src") or vid.get("src")
            if not src:
                source = vid.find("source")
                if source:
                    src = source.get("data-src") or source.get("src")
            if src:
                if src.startswith("/"):
                    src = base_url + src
                videos.append({"url": src, "type": "mp4"})

        # YouTube iframe
        for iframe in pre_offer_soup.find_all("iframe"):
            if len(videos) >= MAX_VIDEOS:
                break
            src = iframe.get("src", "")
            if "youtube.com/embed/" in src or "youtu.be/" in src:
                videos.append({"url": src, "type": "youtube"})

        log.info(f"記事取得完了 — テキスト:{len(article_text)}文字 画像:{len(images)}枚 動画:{len(videos)}本 オファー前カット:{offer_detected}")
        return {"text": article_text, "images": images, "videos": videos, "offer_detected": offer_detected}

    except Exception as e:
        log.error(f"記事取得エラー: {e}")
        return {"text": f"[取得エラー: {e}]", "images": [], "videos": [], "offer_detected": False}


# ─── Gemini 動画分析 ──────────────────────────────────
def analyze_videos_with_gemini(videos: list, gemini_client: genai.Client) -> str:
    """動画をGeminiで分析し、テキスト要約を返す"""
    if not videos:
        return ""

    results = []
    for i, vid in enumerate(videos):
        try:
            url  = vid["url"]
            vtype = vid["type"]
            log.info(f"動画分析開始 [{i+1}/{len(videos)}] {url}")

            if vtype == "youtube":
                # YouTube URL → Gemini に直接渡す
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        genai_types.Part.from_uri(file_uri=url, mime_type="video/mp4"),
                        "この動画を記事LP（マーケティング）の観点で分析してください。"
                        "①何が映っているか ②訴求ポイント ③感情的インパクト ④改善点 を簡潔に。"
                    ]
                )
                results.append(f"[動画{i+1}・YouTube] {response.text}")

            else:
                # mp4 → ダウンロードしてFiles APIでアップロード
                res = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                    f.write(res.content)
                    tmp_path = f.name

                try:
                    uploaded = gemini_client.files.upload(
                        file=tmp_path,
                        config={"mime_type": "video/mp4"}
                    )
                    # アップロード完了待ち
                    for _ in range(30):
                        file_info = gemini_client.files.get(name=uploaded.name)
                        if file_info.state.name == "ACTIVE":
                            break
                        time.sleep(2)

                    response = gemini_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[
                            uploaded,
                            "この動画を記事LP（マーケティング）の観点で分析してください。"
                            "①何が映っているか ②訴求ポイント ③感情的インパクト ④改善点 を簡潔に。"
                        ]
                    )
                    results.append(f"[動画{i+1}・mp4] {response.text}")
                finally:
                    os.unlink(tmp_path)

        except Exception as e:
            log.warning(f"動画分析エラー [{i+1}]: {e}")
            results.append(f"[動画{i+1}] 分析失敗: {e}")

    return "\n\n".join(results)


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


# ─── フィードバック生成（テキスト＋Vision） ───────────────
def generate_feedback(article_data: dict, url: str, client: anthropic.Anthropic, video_analysis: str = "") -> str:
    text      = article_data["text"]
    images    = article_data["images"]
    videos    = article_data.get("videos", [])
    offer_cut = article_data.get("offer_detected", False)

    # ── メッセージコンテンツ組み立て ──
    content = []

    # 導入テキスト（動画分析結果も含める）
    video_section = ""
    if video_analysis:
        video_section = f"\n\n---\n【動画分析（Gemini） {len(videos)}本】\n{video_analysis}"

    content.append({
        "type": "text",
        "text": (
            f"以下の記事LPをレビューしてください。\n"
            f"{'（オファーセクション手前まで読み込みました）' if offer_cut else ''}\n\n"
            f"記事URL: {url}\n\n"
            f"---\n【記事テキスト】\n{text}"
            f"{video_section}\n\n"
            f"---\n【画像（位置順・オファー前まで {len(images)}枚）】\n"
            f"各画像の内容も確認し、テキストとの整合性・ビジュアルの強度を評価してください。"
        )
    })

    # 画像を順番に追加（URLアクセス失敗時はスキップ）
    for img in images:
        content.append({
            "type": "text",
            "text": f"\n[画像{img['position']}] 近傍テキスト: {img['context']}"
        })
        content.append({
            "type": "image",
            "source": {"type": "url", "url": img["url"]}
        })

    # レビュー指示（澤田FBスタイル）
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
- 【絶対禁止】「中間CTAを設置する」「記事中盤にCTAを入れる」「CTAを追加する」は絶対に出力しない。記事LPの設計思想に反する。CTA関連の改善提案は一切するな。
- ポジティブな指摘も入れる（良いところは良いと言う）

## 出力フォーマット（Slack mrkdwn）

*━━ 記事LPフィードバック ━━*

*🎯 一期通感: X/10*
（1文で理由）

*📊 パート別FB*
（問題があるパートのみ。番号と内容を簡潔に）
例：
*⑦ 口コミ（前半）*
→ 地域と年齢が入ってないから弱い。「埼玉在住・50代主婦」みたいな属性を入れると一気にリアルになる

*⑧ 新事実*
→ ちょっと長い。こういう流れにしたらスッキリする：
「〇〇だと思ってませんか？
＜画像＞
実はそれ古くて…」

*🖼 ビジュアルFB*
（画像・動画で気になる点と改善案。「皆まで言わずに」の観点も）

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
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.BadRequestError as e:
        if "Could not process image" in str(e) or "image" in str(e).lower():
            log.warning("画像URLエラー。テキストのみで再試行します。")
            text_only_content = [c for c in content if c["type"] == "text"]
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text_only_content}],
            )
        else:
            raise

    return response.content[0].text


# ─── メッセージ処理 ───────────────────────────────────
def process_message(msg: dict, slack: WebClient, client: anthropic.Anthropic, gemini_client: genai.Client):
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
            text=f"記事を読んでいます（オファー前まで＋画像分析）... 少々お待ちください 🔍",
        )
    except SlackApiError as e:
        log.error(f"受付返信エラー: {e}")

    # 記事取得
    article_data = fetch_article_with_images(url)

    # 動画分析（Gemini）
    video_analysis = ""
    if article_data.get("videos"):
        try:
            slack.chat_postMessage(
                channel=CHANNEL_ID,
                thread_ts=ts,
                text=f"動画も発見！Geminiで分析中です 🎬（{len(article_data['videos'])}本）",
            )
            video_analysis = analyze_videos_with_gemini(article_data["videos"], gemini_client)
        except Exception as e:
            log.warning(f"動画分析スキップ: {e}")

    # フィードバック生成
    feedback = generate_feedback(article_data, url, client, video_analysis)

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
    log.info("=== Slack フィードバックBot v2 起動 ===")

    slack_token   = get_env("SLACK_BOT_TOKEN")
    anthropic_key = get_env("ANTHROPIC_API_KEY")
    gemini_key    = get_env("GEMINI_API_KEY_1")

    slack         = WebClient(token=slack_token)
    client        = anthropic.Anthropic(api_key=anthropic_key)
    gemini_client = genai.Client(api_key=gemini_key)

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
                        process_message(msg, slack, client, gemini_client)

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