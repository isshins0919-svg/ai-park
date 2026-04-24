#!/usr/bin/env bash
# check_client_data.sh — クライアントのデータソース差分チェック
#
# Usage:
#   ./scripts/check_client_data.sh                  # 全クライアントチェック
#   ./scripts/check_client_data.sh sawada-co        # 個別チェック
#
# 動作:
#   ~/Desktop/_clients/<client>/ 配下のファイルを列挙し、
#   .claude/clients/<client>.md の「データソース」セクションに
#   未登録のファイルを警告表示する。登録は手動 or Claudeに依頼。

set -euo pipefail

ROOT="/Users/ca01224/Desktop/一進VOYAGE号"
CLIENTS_DATA_DIR="/Users/ca01224/Desktop/_clients"
CLIENTS_MD_DIR="$ROOT/.claude/clients"

check_one() {
  local client="$1"
  local data_dir="$CLIENTS_DATA_DIR/$client"
  local md_file="$CLIENTS_MD_DIR/$client.md"

  if [[ ! -d "$data_dir" ]]; then
    return
  fi

  if [[ ! -f "$md_file" ]]; then
    echo "⚠️  [$client] _clients/ にフォルダあるが clients/$client.md が無い"
    return
  fi

  # データフォルダ内の全ファイル（.DS_Store と .fld/ 内部除く）
  local actual_files
  actual_files=$(find "$data_dir" -type f \
    ! -name ".DS_Store" \
    ! -path "*.fld/*" \
    | sed "s|$data_dir/||" | sort)

  if [[ -z "$actual_files" ]]; then
    return
  fi

  # md内に登録されてないファイルを検出
  local missing=()
  while IFS= read -r f; do
    # ファイル名（basename）でざっくり検索。フルパス一致より緩く
    local basename_f
    basename_f=$(basename "$f")
    if ! grep -qF "$basename_f" "$md_file" 2>/dev/null; then
      missing+=("$f")
    fi
  done <<< "$actual_files"

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo ""
    echo "📁 [$client] データソース未登録: ${#missing[@]}件"
    for f in "${missing[@]}"; do
      echo "   - $f"
    done
    echo "   → Claudeに: 「$client.md のデータソース更新して」"
  fi
}

if [[ $# -ge 1 ]]; then
  check_one "$1"
else
  for dir in "$CLIENTS_DATA_DIR"/*/; do
    check_one "$(basename "$dir")"
  done
fi

echo ""
echo "✅ データソースチェック完了"
