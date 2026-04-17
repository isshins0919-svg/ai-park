#!/bin/bash
# Slack DPro Bot 起動/停止スクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_SCRIPT="$SCRIPT_DIR/slack_dpro_bot.py"
PID_FILE="$SCRIPT_DIR/slack_dpro_bot.pid"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "既に起動中です (PID: $(cat "$PID_FILE"))"
      exit 1
    fi
    # 環境変数を ~/.zshrc から読み込んでnohupに渡す
    source ~/.zshrc 2>/dev/null
    if [ -z "$SLACK_BOT_TOKEN" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
      echo "⚠️ 環境変数が未設定です (SLACK_BOT_TOKEN / ANTHROPIC_API_KEY)"
      exit 1
    fi
    echo "DPro Bot を起動します..."
    nohup env SLACK_BOT_TOKEN="$SLACK_BOT_TOKEN" ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
      python3.11 "$BOT_SCRIPT" > /dev/null 2>&1 &
    echo $! > "$PID_FILE"
    echo "起動完了 (PID: $!)"
    echo "ログ: $SCRIPT_DIR/slack_dpro_bot.log"
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      kill "$PID" 2>/dev/null && echo "Bot停止 (PID: $PID)" || echo "プロセスが見つかりません"
      rm -f "$PID_FILE"
    else
      echo "Botは起動していません"
    fi
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "稼働中 (PID: $(cat "$PID_FILE"))"
    else
      echo "停止中"
    fi
    ;;
  log)
    tail -f "$SCRIPT_DIR/slack_dpro_bot.log"
    ;;
  *)
    echo "使い方: $0 {start|stop|status|log}"
    ;;
esac
