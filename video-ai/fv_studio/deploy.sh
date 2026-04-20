#!/bin/bash
# KOSURIちゃん → Cloud Run デプロイスクリプト
# 使い方: bash video-ai/fv_studio/deploy.sh

set -e

# gcloud PATH（Homebrew Cask経由でインストールされている場合）
export PATH="/opt/homebrew/Caskroom/gcloud-cli/564.0.0/google-cloud-sdk/bin:$PATH"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ここだけ書き換えてください
PROJECT_ID="yomite-douga-studio-ai"   # GCPプロジェクトID
REGION="asia-northeast1"            # 東京リージョン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SERVICE_NAME="kosuri-studio"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
VOYAGE_ROOT="$(cd "${REPO_ROOT}/../.." && pwd)"

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
