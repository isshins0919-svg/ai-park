# n8n Cloud セットアップガイド — DPro Slack AIボット

PCオフでも動く完全クラウド自動化の手順書。

---

## 📋 前提条件

| 項目 | 状態 |
|---|---|
| DPro API Base URL | `https://api.kashika-20mile.com` |
| Slack Bot Token | 取得済み（xoxb-...） |
| Slack Channel | `#yomite_ai-agents`（ID: C0AMYLU2W5D） |
| Slack App | 既存のものを流用 |

---

## Step 1: n8n Cloud アカウント作成

1. [https://app.n8n.cloud/register](https://app.n8n.cloud/register) にアクセス
2. メールアドレスで無料登録（クレカ不要）
3. **Free プランで OK**（月5,000回実行まで無料）

---

## Step 2: 環境変数の設定

n8n Cloud で以下の環境変数を設定します。

`Settings` → `Environment Variables` → 追加：

| 変数名 | 値 |
|---|---|
| `DPRO_API_KEY` | DPro APIキー（動画Proの認証キー） |
| `SLACK_BOT_TOKEN` | `xoxb-...`（Slack Bot Token） |

> **注意**: n8n Free プランは環境変数が使えない場合あり。その場合は各ノードの設定値にトークンを直接入力してください。

---

## Step 2.5: Cloudflare Worker をデプロイ（← DPro認証問題の解決策）

DPro APIへの直REST呼び出しは有料認証が必要なため、MCP経由のプロキシWorkerを挟みます。

### Cloudflare アカウント作成
1. https://dash.cloudflare.com/sign-up にアクセス（無料）
2. メール登録してログイン

### Worker 作成
1. ダッシュボード左メニュー → `Workers & Pages`
2. `Create` → `Create Worker`
3. Worker名を入力（例: `dpro-proxy`）
4. `Deploy` → `Edit code` をクリック

### コードを貼り付け
1. エディタの中身を全選択して削除
2. `scripts/cloudflare/dpro-proxy.worker.js` の内容を丸ごとコピペ
3. 右上の `Deploy` をクリック

### 動作テスト
ブラウザで以下にアクセス → 媒体一覧JSONが返ればOK ✅
```
https://dpro-proxy.{あなたのサブドメイン}.workers.dev/apps
```

### n8nワークフローのURL設定
`dpro-daily-news.workflow.json` の Code node 内の1行を差し替え：
```javascript
const DPRO_BASE = 'https://dpro-proxy.xxxx.workers.dev'; // ← 実際のWorker URL
```

---

## Step 3: Workflow 1「デイリーニュース」インポート

1. n8n Cloud 上部メニューの `Workflows` → `Add workflow`
2. 右上 `...` → `Import from file`
3. `dpro-daily-news.workflow.json` をアップロード
4. インポート後、ワークフローを開く

### タイムゾーン確認

- Schedule Trigger ノードをクリック
- `Timezone` が `Asia/Tokyo` になっているか確認（なければ設定）

### テスト実行

1. ワークフロー上部の `Test workflow` をクリック
2. データが取得されて Slack に投稿されれば成功 ✅

### 本番有効化

- ワークフロー右上のトグルスイッチを `Active` に切り替え
- **これでPCオフでも毎朝8:00に自動実行されます** 🎉

---

## Step 4: Workflow 2「検索・回答ボット」インポート

1. `Workflows` → `Add workflow` → `Import from file`
2. `dpro-slack-search.workflow.json` をアップロード

### Webhook URLの取得

1. `Slack Webhook受信` ノードをクリック
2. `Webhook URLs` → **Production URL** をコピー
   - 例: `https://xxxx.app.n8n.cloud/webhook/dpro-slack-events`

### Slack App にWebhook URLを登録

1. [https://api.slack.com/apps](https://api.slack.com/apps) → 既存のSlack Appを開く
2. 左メニュー `Event Subscriptions` → **Enable Events: ON**
3. `Request URL` に n8n の Webhook URL を貼り付け
4. Slack が `Verified ✓` になるまで待つ（n8nが自動でチャレンジ応答）
5. `Subscribe to bot events` → `Add Bot User Event` → `message.channels` を追加
6. 画面下部の `Save Changes`
7. `Install App` → `Reinstall to Workspace`

### ボットをチャンネルに追加

Slack の `#yomite_ai-agents` チャンネルで：
```
/invite @ボット名
```

### テスト

チャンネルに「ヒザ系で伸びてる広告は？」と投稿 → スレッドに回答が返れば成功 ✅

---

## Step 5: ローカルの Scheduled Task を無効化

n8n に移行したら、Claude Code のローカル Scheduled Task を止めます：

Claude Code で実行：
```
dpro-daily-news のScheduled Taskを無効化して
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| DPro API 401エラー | APIキーが未設定 or 間違い | 環境変数 `DPRO_API_KEY` を確認 |
| Slack投稿されない | Bot Tokenが間違い | `SLACK_BOT_TOKEN` を確認 |
| Webhook URL検証が通らない | n8nがActiveでない | ワークフローをActiveにしてから登録 |
| 毎朝8:00に動かない | タイムゾーンがUTC | Schedule TriggerのTimezoneをAsia/Tokyoに変更 |
| ボットが自分の投稿に反応してしまう | フィルタが効いていない | `有効メッセージ判定`ノードのbot_id条件を確認 |

---

## アーキテクチャ図

```
【Workflow 1: デイリーニュース】
n8n Cloud (毎朝8:00 JST)
  └─ DPro API /api/v1/apps        → 媒体ID取得
  └─ DPro API /api/v1/genres × 4  → ジャンルID取得
  └─ DPro API /api/v1/items × 10  → TOP3データ取得
  └─ Slack API chat.postMessage    → チャンネルに1投稿
  └─ Slack API chat.postMessage × n → スレッドに詳細投稿

【Workflow 2: 検索・回答】
Slack メッセージ投稿
  → Slack Event API
  → n8n Webhook (常時待機)
  → DPro API 検索
  → Slack API chat.postMessage (スレッド返信)
```

---

*作成: 2026-04-08 | 一進VOYAGE号*
