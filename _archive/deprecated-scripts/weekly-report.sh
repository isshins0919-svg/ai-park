#!/bin/zsh
# ================================================
# 週次 Claude Code 使用レポート
# 使い方: ./weekly-report.sh [YYYY-MM-DD終了日]
# 例: ./weekly-report.sh 2026-03-25
# ================================================

END_DATE="${1:-$(date +%Y-%m-%d)}"
START_DATE=$(date -j -v-6d -f "%Y-%m-%d" "$END_DATE" +%Y-%m-%d)
PREV_END=$(date -j -v-7d  -f "%Y-%m-%d" "$END_DATE" +%Y-%m-%d)
PREV_START=$(date -j -v-13d -f "%Y-%m-%d" "$END_DATE" +%Y-%m-%d)

BOLD=$'\e[1m'; CYAN=$'\e[0;36m'; GREEN=$'\e[0;32m'
YELLOW=$'\e[0;33m'; RED=$'\e[0;31m'; DIM=$'\e[2m'; RESET=$'\e[0m'

# ---- ヘルパー ----
new_files() { git log --since="${1}T00:00:00" --until="${2}T23:59:59" \
  --diff-filter=A --name-only --format="" 2>/dev/null | grep -iE "$3" | wc -l | tr -d ' '; }

match_commits() { git log --since="${1}T00:00:00" --until="${2}T23:59:59" \
  --oneline 2>/dev/null | grep -iE "$3" | wc -l | tr -d ' '; }

all_commits() { git log --since="${1}T00:00:00" --until="${2}T23:59:59" \
  --oneline 2>/dev/null | wc -l | tr -d ' '; }

feat_commits() { git log --since="${1}T00:00:00" --until="${2}T23:59:59" \
  --oneline 2>/dev/null | grep -E "feat" | wc -l | tr -d ' '; }

delta_str() {
  local c=$1 p=$2
  [[ $p -eq 0 ]] && { echo "new"; return; }
  local d=$(( c - p ))
  [[ $d -gt 0 ]] && echo "+${d}" || echo "${d}"
}

delta_col() {
  local d="$1"
  [[ "$d" == +* || "$d" == "new" ]] && echo "${GREEN}${d}${RESET}" && return
  [[ "$d" == -* ]] && echo "${RED}${d}${RESET}" && return
  echo "${DIM}±0${RESET}"
}

row() {
  local icon="$1" label="$2" curr="$3" prev="$4"
  local d=$(delta_str $curr $prev)
  local dc=$(delta_col "$d")
  printf "  %s  %-12s ${BOLD}%3d${RESET}   %s vs 先週\n" "$icon" "$label" "$curr" "$dc"
}

# ---- 今週 ----
TW_TOT=$(all_commits  "$START_DATE" "$END_DATE")
TW_FT=$(feat_commits  "$START_DATE" "$END_DATE")
TW_IMG=$(new_files    "$START_DATE" "$END_DATE" "\.(png|jpg|jpeg|webp|gif)")
TW_VID=$(new_files    "$START_DATE" "$END_DATE" "\.(mp4|mov|webm)")
TW_REP=$(new_files    "$START_DATE" "$END_DATE" "\.(html|pdf)")
TW_MOR=$(match_commits "$START_DATE" "$END_DATE" "morning|モーニング")
TW_REV=$(match_commits "$START_DATE" "$END_DATE" "weekly.review|週次|振り返り")
TW_RES=$(match_commits "$START_DATE" "$END_DATE" "research|リサーチ|strategy")

# ---- 先週 ----
PW_TOT=$(all_commits  "$PREV_START" "$PREV_END")
PW_FT=$(feat_commits  "$PREV_START" "$PREV_END")
PW_IMG=$(new_files    "$PREV_START" "$PREV_END" "\.(png|jpg|jpeg|webp|gif)")
PW_VID=$(new_files    "$PREV_START" "$PREV_END" "\.(mp4|mov|webm)")
PW_REP=$(new_files    "$PREV_START" "$PREV_END" "\.(html|pdf)")
PW_MOR=$(match_commits "$PREV_START" "$PREV_END" "morning|モーニング")
PW_REV=$(match_commits "$PREV_START" "$PREV_END" "weekly.review|週次|振り返り")
PW_RES=$(match_commits "$PREV_START" "$PREV_END" "research|リサーチ|strategy")

# ---- 日別バー ----
typeset -A DAY_CNT
CURRENT="$START_DATE"
MAX=0
while [[ "$CURRENT" <= "$END_DATE" ]]; do
  CNT=$(all_commits "$CURRENT" "$CURRENT")
  DAY_CNT[$CURRENT]=$CNT
  [[ $CNT -gt $MAX ]] && MAX=$CNT
  CURRENT=$(date -j -v+1d -f "%Y-%m-%d" "$CURRENT" +%Y-%m-%d)
done

# ---- 表示 ----
echo ""
echo "${BOLD}╔══════════════════════════════════════════════╗${RESET}"
echo "${BOLD}║   📊  週次 Claude Code レポート              ║${RESET}"
echo "${BOLD}║   ${CYAN}${START_DATE} 〜 ${END_DATE}${RESET}${BOLD}              ║${RESET}"
echo "${BOLD}╚══════════════════════════════════════════════╝${RESET}"
echo ""

echo "${BOLD}▌ 成果物${RESET}"
row "🖼 " "画像"      $TW_IMG $PW_IMG
row "🎬" "動画"      $TW_VID $PW_VID
row "📄" "レポート"  $TW_REP $PW_REP
echo ""

echo "${BOLD}▌ アクティビティ${RESET}"
row "📦" "総コミット"  $TW_TOT $PW_TOT
row "✨" "feat件数"    $TW_FT  $PW_FT
row "🔍" "リサーチ"    $TW_RES $PW_RES
echo ""

echo "${BOLD}▌ 習慣・振り返り${RESET}"
row "🌅" "Morning"     $TW_MOR $PW_MOR
row "🔄" "週次レビュー" $TW_REV $PW_REV
echo ""

echo "${BOLD}▌ 日別アクティビティ${RESET}"
CURRENT="$START_DATE"
while [[ "$CURRENT" <= "$END_DATE" ]]; do
  CNT=${DAY_CNT[$CURRENT]:-0}
  DOW=$(date -j -f "%Y-%m-%d" "$CURRENT" "+%a")
  LABEL="${CURRENT:5} ${DOW}"
  BAR_LEN=$(( MAX > 0 ? CNT * 22 / MAX : 0 ))
  BAR=$(printf '█%.0s' {1..$BAR_LEN} 2>/dev/null || printf '%0.s█' $(seq 1 $BAR_LEN))
  [[ $BAR_LEN -eq 0 ]] && BAR="·"
  if [[ $CNT -eq $MAX && $MAX -gt 0 ]]; then
    printf "  ${YELLOW}%-11s${RESET}  ${YELLOW}%-22s${RESET}  ${BOLD}%2d件${RESET}\n" "$LABEL" "$BAR" "$CNT"
  else
    printf "  ${DIM}%-11s${RESET}  ${CYAN}%-22s${RESET}  %2d件\n" "$LABEL" "$BAR" "$CNT"
  fi
  CURRENT=$(date -j -v+1d -f "%Y-%m-%d" "$CURRENT" +%Y-%m-%d)
done

echo ""
echo "${DIM}先週: ${PREV_START} 〜 ${PREV_END}${RESET}"
echo ""
