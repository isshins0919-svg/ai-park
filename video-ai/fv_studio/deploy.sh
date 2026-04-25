#!/bin/bash
# KOSURIちゃん → Cloud Run デプロイスクリプト
# 使い方: bash video-ai/fv_studio/deploy.sh
#   どのディレクトリから叩いても動く（home dirからでもOK）

set -e

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# どこから実行されてもスクリプト自身の場所を解決して移動
# 2026-04-25: home dir から叩いて "No such file" になる地雷を根治
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)"
if [ -z "${SCRIPT_PATH}" ] || [ ! -f "${SCRIPT_PATH}/deploy.sh" ]; then
  echo "❌ deploy.sh の場所を解決できませんでした"
  echo "   フルパスで実行してください: bash ~/Desktop/一進VOYAGE号/video-ai/fv_studio/deploy.sh"
  exit 1
fi
cd "${SCRIPT_PATH}"

# gcloud PATH（Homebrew Cask経由でインストールされている場合）
export PATH="/opt/homebrew/Caskroom/gcloud-cli/564.0.0/google-cloud-sdk/bin:$PATH"

# gcloud が見つからなければ早期エラー
if ! command -v gcloud >/dev/null 2>&1; then
  echo "❌ gcloud コマンドが見つかりません"
  echo "   Homebrew で入れる: brew install --cask gcloud-cli"
  exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ここだけ書き換えてください
PROJECT_ID="yomite-douga-studio-ai"   # GCPプロジェクトID
REGION="asia-northeast1"            # 東京リージョン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SERVICE_NAME="kosuri-studio"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
# SCRIPT_PATH は冒頭で解決済み（どこから実行されても script 自身の絶対パス）
REPO_ROOT="${SCRIPT_PATH}"
VOYAGE_ROOT="$(cd "${REPO_ROOT}/../.." && pwd)"

# 健全性チェック
if [ ! -d "${VOYAGE_ROOT}/.claude/clients" ]; then
  echo "❌ ${VOYAGE_ROOT}/.claude/clients が見つかりません"
  echo "   一進VOYAGE号 リポジトリの video-ai/fv_studio/ から実行されているか確認してください"
  exit 1
fi

echo "=== KOSURIちゃん Cloud Run デプロイ ==="
echo "  Project : ${PROJECT_ID}"
echo "  Region  : ${REGION}"
echo "  Image   : ${IMAGE}"
echo ""

# 1. gcloud プロジェクト設定
gcloud config set project "${PROJECT_ID}"

# 2. 必要なAPIを有効化
echo "[1/4] APIを有効化..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com --quiet

# 商品プロファイルを一時コピー（Cloud Buildのコンテキストに含める）
echo "  [prep] 商品プロファイルをコンテキストにコピー中..."
rm -rf "${REPO_ROOT}/clients"
cp -r "${VOYAGE_ROOT}/.claude/clients" "${REPO_ROOT}/clients"
trap 'echo "  [cleanup] clients/ を削除"; rm -rf "${REPO_ROOT}/clients"' EXIT

# 3. Dockerイメージをビルド & push (Cloud Build使用 → ローカルDockerが不要)
echo "[2/4] Cloud Buildでイメージをビルド中..."
gcloud builds submit "${REPO_ROOT}" \
  --tag "${IMAGE}" \
  --gcs-log-dir="gs://${PROJECT_ID}_cloudbuild/logs"

# 4. Cloud Run にデプロイ
echo "[3/4] Cloud Run にデプロイ中..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=1 \
  --memory=4Gi \
  --cpu=2 \
  --timeout=3600 \
  --quiet

# 5. URLを表示
echo ""
echo "[4/4] デプロイ完了！"
URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format="value(status.url)")
echo ""
echo "  ✅ URL: ${URL}"
echo ""
echo "  このURLをチームに共有してください！"
