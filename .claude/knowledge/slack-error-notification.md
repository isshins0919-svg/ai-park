# Slack エラー通知プロトコル

## 概要
MCP連携やAPI呼び出しでエラーが発生した際、Slackで関係者に自動報告する仕組み。

---

## 通知先

### 絶対ルール
- **全てのSlack投稿は `yomite_ai-kiji_fb` (C0AMYLU2W5D) のみ**
- **DMは一切送らない**
- **連絡先には必ず `<@ユーザーID>` でtoメンションをつける**

### 鍋谷 準飛さん（エンジニアリング）
- **メンション**: `<@U04PD3YBXRB>`
- **通知対象**: MCP接続エラー、DPro APIエラー、インフラ系障害

### 三浦 莉さん（API管理）
- **メンション**: `<@U073VJMS751>`
- **通知対象**: Gemini API障害、APIキー関連問題

---

## 通知テンプレート

### MCP接続エラー → 鍋谷さんDM
```
パクさんの分身のAIパクです！🚨

【MCP接続エラー報告】

■ エラー内容
{エラーメッセージ}

■ 影響範囲
{何ができなくなったか}

■ 試した対策
{自分で試したこと}

■ 改善提案
1. {改善案1}
2. {改善案2}

■ 緊急度: {高/中/低}

よろしくお願いします！🙏
```

### Gemini API障害 → 三浦さんDM
```
パクさんの分身のAIパクです！🌸

🚨 Gemini API 障害報告

【状況】
{モデル名} が {ステータスコード} を返しています。
検証済みキー: {テストしたキーの数}

【影響】
{何ができなくなったか}

【お願い】
Google Cloud ステータスページの確認をお願いします！
https://status.cloud.google.com/

よろしくお願いします！🙏✨
```

---

## エラー判定ロジック（AIパクの行動規範）

### 自動通知するケース
1. **MCP tools が応答しない** → 鍋谷さんDM + 改善策
2. **DPro API が 4xx/5xx** → 鍋谷さんDM + 改善策
3. **Gemini API が 503** → 三浦さんDM + キーローテーション試行結果
4. **外部API が連続3回失敗** → 鍋谷さんDM

### 通知しないケース（自分で解決）
- 一時的なタイムアウト（1回目）→ リトライ
- レート制限 429 → 待機してリトライ
- パラメータミス 400 → 修正してリトライ

---

## APIキーローテーション手順

### Gemini API（3キー体制）
```python
keys = [
    os.environ.get("GEMINI_API_KEY"),
    os.environ.get("GEMINI_API_KEY_1"),
    os.environ.get("GEMINI_API_KEY_2"),
]

for i, key in enumerate(keys):
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(...)
        break  # 成功したら抜ける
    except Exception as e:
        if "503" in str(e) or "429" in str(e):
            continue  # 次のキーを試す
        raise  # その他のエラーは通知
else:
    # 全キー失敗 → Slack通知
    notify_slack_error(...)
```

---

## 改善策テンプレート（通知に添付）

### MCP接続エラーの場合
1. MCP server プロセスの再起動
2. settings.local.json の設定確認
3. ネットワーク接続の確認
4. MCP server のログ確認

### DPro APIエラーの場合
1. APIキーの有効期限確認
2. エンドポイントURLの正確性確認
3. リクエストパラメータのバリデーション
4. DPro側のサーバーステータス確認

### Gemini APIエラーの場合
1. 3キーローテーション実施
2. Google Cloud ステータスページ確認
3. 代替モデルへのフォールバック検討
4. レート制限の場合は待機時間調整

---

## 関連メンバー Slack ID 一覧

| 名前 | Slack ID | 役割 |
|------|---------|------|
| 鍋谷 準飛 | U04PD3YBXRB | エンジニアリング |
| 三浦 莉 | U073VJMS751 | API管理 |
| AIパク Bot | U0AGRJBP9G9 | 自動通知送信元 |
