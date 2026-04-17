---
# 🤝 HANDOFF — 2026-04-17

## このセッションのゴール
KOSURIちゃん FVスタジオ の最終仕上げ & Cloud Run デプロイ

## 完了済み ✅
- KOSURIちゃんチャット: フィードバックタブ削除（質問・要望のみ）
- 右パネル評価に「🙆 問題なし」追加（good / no_issue / bad）
- フォーム・bot-question・bot-feature → 「ユーザーの声」シートに統合
  - 列構成: 日時 / ソース / 担当者名 / 評価 / カテゴリ / コメント / ジョブID / BOT返答
- Cloud Run デプロイ完了（revision: kosuri-studio-00022-qnn）
  - URL: https://kosuri-studio-839065147347.asia-northeast1.run.app

## 次セッションでやること 🚀
1. **Sheetsセットアップ**: `curl -X POST https://kosuri-studio-839065147347.asia-northeast1.run.app/setup-sheets` を叩いて「ユーザーの声」シートを自動作成
2. **deploy.sh修正**: 先頭に `export PATH="/opt/homebrew/Caskroom/gcloud-cli/564.0.0/google-cloud-sdk/bin:$PATH"` を追加（gcloud not found 対策）
3. **動作確認**: フォーム送信・KOSURIちゃんチャット → Sheetsに「ユーザーの声」として記録されることを確認
4. **次の機能**: ユーザーと相談して優先度を決める

## プラン詳細（設計メモ）
### Sheets構造
- **生成ログ**: 動画生成ごとに記録（モード・FV本数・処理時間等）
- **ユーザーの声** (統合): source列で種別区別
  - `form` = 右パネルのフィードバックフォーム
  - `bot-question` = KOSURIちゃんへの質問
  - `bot-feature` = KOSURIちゃんへの機能要望
- **スクリプト一覧**: ツール目録（静的）
- ~~フィードバック~~ → ユーザーの声に統合
- ~~BOTログ~~ → ユーザーの声に統合

### デプロイ方法（次回）
```bash
export PATH="/opt/homebrew/Caskroom/gcloud-cli/564.0.0/google-cloud-sdk/bin:$PATH"
cd /Users/ca01224/Desktop/一進VOYAGE号/video-ai/fv_studio
gcloud builds submit . --tag gcr.io/yomite-douga-studio-ai/kosuri-studio
gcloud run deploy kosuri-studio \
  --image gcr.io/yomite-douga-studio-ai/kosuri-studio \
  --region asia-northeast1 --platform managed --allow-unauthenticated \
  --min-instances=1 --max-instances=1 --memory=4Gi --cpu=2 --timeout=3600 --quiet
```

## 注意点 ⚠️
- `gcloud` はPATHに入っていない → フルパス or PATH export 必須
- `--ephemeral-storage` フラグは使わない（Cloud Runでエラーになる）
- KOSURIちゃん画像は `static/kosuri/` にwebp形式で保存済み（再生成不要）
- SPREADSHEET_ID は app.py の環境変数 or 定数で管理されている

## 次セッション用ワンライナー
> `.claude/handoff/handoff_2026-04-17_kosuri.md` を読んで、KOSURIちゃんスタジオの続きを始めて。最初のタスクは「setup-sheets を叩いてユーザーの声シートを初期化」から。
---
