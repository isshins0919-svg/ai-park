#!/usr/bin/env python3
"""
GitHub Actions 用 1回実行ラッパー
slack_feedback_bot.py の while True ループを1回だけ実行して終了する
環境変数 SLACK_BOT_TOKEN / ANTHROPIC_API_KEY を直接読む（zshrc 不要）
"""
import os
import sys
import logging

# ボットスクリプトと同じディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

import anthropic
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from slack_feedback_bot import (
    CHANNEL_ID,
    load_state,
    save_state,
    is_trigger,
    extract_urls,
    process_message,
    log,
)


def run_once():
    log.info("=== Slack フィードバックBot (GitHub Actions / 1回実行) ===")

    slack_token   = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    if not slack_token or not anthropic_key:
        log.error("SLACK_BOT_TOKEN / ANTHROPIC_API_KEY が未設定です")
        sys.exit(1)

    slack  = WebClient(token=slack_token)
    client = anthropic.Anthropic(api_key=anthropic_key)
    state  = load_state()

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

            log.info(f"未処理メッセージ: {len(new_messages)}件")

            for msg in new_messages:
                if is_trigger(msg.get("text", "")) and extract_urls(msg.get("text", "")):
                    process_message(msg, slack, client)

                state["processed"].append(msg.get("ts"))
                state["last_ts"] = msg.get("ts")

            state["processed"] = state["processed"][-200:]
            save_state(state)
        else:
            log.info("新しいメッセージなし")

    except SlackApiError as e:
        log.error(f"Slack API エラー: {e}")
        sys.exit(1)
    except Exception as e:
        log.error(f"予期しないエラー: {e}", exc_info=True)
        sys.exit(1)

    log.info("=== 完了 ===")


if __name__ == "__main__":
    run_once()