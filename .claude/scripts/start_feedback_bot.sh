#!/bin/bash
# Slack フィードバックBot 起動/停止スクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_SCRIPT="$SCRIPT_DIR/slack_feedback_bot.py"
PID_FILE="$SCRIPT_DIR/slack_feedback_bot.pid"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "既に起動中です (PID: $(cat "$PID_FILE"))"
      exit 1
    fi
    echo "Botを起動します..."
    nohup python3 "$BOT_SCRIPT" > /dev/null 2>&1 &
    echo $! > "$PID_FILE"
    echo "起動完了 (PID: $!)"
    echo "ログ: $SCRIPT_DIR/slack_feedback_bot.log"
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
    tail -f "$SCRIPT_DIR/slack_feedback_bot.log"
    ;;
  *)
    echo "使い方: $0 {start|stop|status|log}"
    ;;
esac