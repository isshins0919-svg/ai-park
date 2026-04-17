#!/usr/bin/env python3.11
"""
Slack DPro質問Bot v1.2
- #yomite_ai-kiji_fb を2分おきにポーリング
- 「dpro」を含む投稿を検知（大文字小文字問わず）
- ローカルMCPクライアントでDPro（localhost:8888）に直接接続
- 取得データをClaudeに渡して解釈・回答を生成
- 結果をSlackスレッドに返信

起動: bash start_dpro_bot.sh start
停止: bash start_dpro_bot.sh stop
ログ: bash start_dpro_bot.sh log
"""
from __future__ import annotations

import os
import re
import json
import time
import logging
import asyncio
import subprocess
from pathlib import Path

import anthropic
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# ─── 設定 ─────────────────────────────────────────────
CHANNEL_ID     = "C0AMYLU2W5D"   # #yomite_ai-kiji_fb
POLL_INTERVAL  = 120              # 2分おきにチェック
STATE_FILE     = Path(__file__).parent / "slack_dpro_state.json"
LOG_FILE       = Path(__file__).parent / "slack_dpro_bot.log"
DPRO_MCP_URL   = "http://localhost:8888/mcp"

# トリガーキーワード（大文字小文字問わず、単語単位）
TRIGGER_PATTERN = re.compile(r'\bdpro\b', re.IGNORECASE)

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
    val = os.environ.get(key, "")
    if val:
        return val
    raise EnvironmentError(f"環境変数 {key} が未設定です。start_dpro_bot.sh から起動してください。")

# ─── 状態管理 ─────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_ts": None, "processed": []}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ─── トリガー判定 ─────────────────────────────────────
def is_trigger(text: str) -> bool:
    return bool(TRIGGER_PATTERN.search(text))

# ─── DPro MCPを叩いてデータ取得 ──────────────────────
async def fetch_dpro_data(question: str) -> dict:
    """
    ローカルMCPクライアントでDPro（localhost:8888）に直接接続し、
    質問に関連するデータを取得して返す。
    最大5ツール呼び出しまで。
    """
    results = {}
    call_count = 0
    max_calls = 5

    try:
        async with streamablehttp_client(DPRO_MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 利用可能なツール一覧を取得
                tools_response = await session.list_tools()
                available_tools = {t.name: t for t in tools_response.tools}
                log.info(f"DPro利用可能ツール: {list(available_tools.keys())}")

                # 1. アプリ一覧（媒体ID取得）
                if "read_apps_api_v1_apps_get" in available_tools and call_count < max_calls:
                    r = await session.call_tool("read_apps_api_v1_apps_get", {})
                    results["apps"] = r.content[0].text if r.content else "{}"
                    call_count += 1

                # 2. ジャンル検索（質問からキーワード抽出）
                # 質問文からジャンルキーワードを抽出（簡易）
                genre_keywords = re.findall(
                    r'(ヒザ|膝|サプリ|美容|コスメ|ダイエット|育毛|薄毛|脱毛|肌|スキンケア|健康|筋トレ|プロテイン)',
                    question
                )
                genre_keyword = genre_keywords[0] if genre_keywords else ""

                if genre_keyword and "search_genres_api_v1_genres_get" in available_tools and call_count < max_calls:
                    r = await session.call_tool(
                        "search_genres_api_v1_genres_get",
                        {"keyword": genre_keyword}
                    )
                    results["genres"] = r.content[0].text if r.content else "{}"
                    call_count += 1

                    # 3. ジャンルIDからアイテム取得
                    genres_data = json.loads(results["genres"]) if results.get("genres") else {}
                    genre_list = genres_data if isinstance(genres_data, list) else genres_data.get("genres", [])
                    if genre_list and call_count < max_calls:
                        genre_id = genre_list[0].get("id") if isinstance(genre_list[0], dict) else None
                        if genre_id and "get_items_by_rds_api_v1_items_get" in available_tools:
                            r = await session.call_tool(
                                "get_items_by_rds_api_v1_items_get",
                                {"genre_id": genre_id, "limit": 5}
                            )
                            results["items"] = r.content[0].text if r.content else "{}"
                            call_count += 1

                # ジャンルキーワードが取れなかった場合、商品検索
                if not genre_keyword and "search_products_with_relevance_api_v1_products_get" in available_tools and call_count < max_calls:
                    # 質問から検索ワードを抽出（「dpro」以外の名詞を使う）
                    search_word = re.sub(r'\bdpro\b', '', question, flags=re.IGNORECASE).strip()[:30]
                    if search_word:
                        r = await session.call_tool(
                            "search_products_with_relevance_api_v1_products_get",
                            {"keyword": search_word}
                        )
                        results["products"] = r.content[0].text if r.content else "{}"
                        call_count += 1

    except Exception as e:
        log.error(f"DPro MCP接続エラー: {e}")
        results["error"] = str(e)

    return results

# ─── ClaudeでDProデータを解釈して回答生成 ─────────────
DPRO_SYSTEM_PROMPT = """あなたは🌟 DProフロントエージェントです。「言葉の裏を読んで、数字で答える」陽気なAIアナリスト。

## キャラクター
- トーン: 明るく、テンポよく、でも答えは真剣
- 口調: 親しみやすい敬語 + ときどき絵文字
- NG: データがなくても「わかりません」で終わること。必ず代替案・示唆を出す

## 回答フォーマット
【質問の本質】（1行）

【データ解釈】
📊 取得データをもとに、TOP商品・フック・特徴を整理

【示唆・アクション】（2〜3行）
今のトレンドから読み取れること + 制作・戦略への示唆

## 注意
- 数字は「推定値」と明示
- 競合他社の実名は出さない（商品A/競合Bに置き換え）
- DProデータがエラーの場合はその旨を伝え、別のアプローチを提案する
"""

def generate_answer(question: str, dpro_data: dict, client: anthropic.Anthropic) -> str:
    """Claude APIでDProデータを解釈して回答生成"""

    # DProデータをコンテキストとして整形
    if dpro_data.get("error"):
        data_context = f"⚠️ DPro接続エラー: {dpro_data['error']}\n※ DPro MCPサーバー（localhost:8888）が起動しているか確認してください。"
    else:
        data_context = "【DProから取得したデータ】\n"
        for key, val in dpro_data.items():
            data_context += f"\n[{key}]\n{val[:2000]}\n"  # 各データ2000文字まで

    user_message = f"""質問: {question}

{data_context}

上記のDProデータをもとに、質問に答えてください。"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=DPRO_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    except Exception as e:
        log.error(f"Claude API エラー: {e}")
        return f"⚠️ 回答生成エラー: {str(e)}"

# ─── メッセージ処理 ────────────────────────────────────
def process_message(msg: dict, slack: WebClient, anthropic_client: anthropic.Anthropic):
    text = msg.get("text", "")
    ts   = msg["ts"]
    user = msg.get("user", "unknown")

    log.info(f"DPro質問検知: user={user}, text={text[:80]}")

    # 受信確認
    try:
        slack.chat_postMessage(
            channel=CHANNEL_ID,
            thread_ts=ts,
            text="📊 DPro調べてきます！少々お待ちを〜"
        )
    except SlackApiError as e:
        log.warning(f"受信確認の送信失敗: {e}")

    # DProデータ取得（非同期 → 同期で実行）
    dpro_data = asyncio.run(fetch_dpro_data(text))
    log.info(f"DProデータ取得完了: keys={list(dpro_data.keys())}")

    # Claude で解釈・回答生成
    answer = generate_answer(text, dpro_data, anthropic_client)

    # スレッドに返信（3000文字超えたら分割）
    chunks = [answer[i:i+3000] for i in range(0, len(answer), 3000)]
    for chunk in chunks:
        try:
            slack.chat_postMessage(
                channel=CHANNEL_ID,
                thread_ts=ts,
                text=chunk
            )
            time.sleep(0.5)
        except SlackApiError as e:
            log.error(f"Slack投稿失敗: {e}")

    log.info(f"回答送信完了: ts={ts}")

# ─── メインループ ─────────────────────────────────────
def main():
    log.info("=== Slack DPro Bot 起動 ===")
    log.info(f"監視チャンネル: {CHANNEL_ID}")
    log.info(f"ポーリング間隔: {POLL_INTERVAL}秒")
    log.info(f"DPro MCPサーバー: {DPRO_MCP_URL}")

    slack_token      = get_env("SLACK_BOT_TOKEN")
    anthropic_key    = get_env("ANTHROPIC_API_KEY")
    slack            = WebClient(token=slack_token)
    anthropic_client = anthropic.Anthropic(api_key=anthropic_key)

    state = load_state()
    log.info(f"状態読み込み: last_ts={state['last_ts']}, processed={len(state['processed'])}件")

    while True:
        try:
            kwargs = {"channel": CHANNEL_ID, "limit": 20}
            if state["last_ts"]:
                kwargs["oldest"] = state["last_ts"]

            result   = slack.conversations_history(**kwargs)
            messages = list(reversed(result.get("messages", [])))

            new_messages = [
                m for m in messages
                if m["ts"] not in state["processed"]
                and not m.get("thread_ts")
                and not m.get("bot_id")
            ]

            for msg in new_messages:
                if is_trigger(msg.get("text", "")):
                    process_message(msg, slack, anthropic_client)

                state["processed"].append(msg["ts"])
                state["last_ts"] = msg["ts"]

            state["processed"] = state["processed"][-200:]
            save_state(state)

            if new_messages:
                log.info(f"チェック完了: {len(new_messages)}件の新規メッセージ")

        except SlackApiError as e:
            log.error(f"Slack APIエラー: {e}")
        except Exception as e:
            log.error(f"予期しないエラー: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
