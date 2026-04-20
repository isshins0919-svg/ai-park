# Park Patrol — スキル自動進化パトロール

毎日の初回起動時に自動実行。AI画像生成・広告テック・LLMの最新動向をスキャンし、Park Skills（Banner Park / Short Ad Park / 記事LP Park）のアップデート余地を検出する。

## 使い方

- **自動**: 毎日の初回起動時に CLAUDE.md のトリガーで実行される
- **手動**: `/park-patrol` で好きなタイミングでも呼べる

---

## 起動時の行動（必ずこの順序で実行）

### Step 0: タイムスタンプチェック

以下のファイルを確認する:

```
.claude/knowledge/patrol-last-run.txt
```

- ファイルが存在し、中身が **今日の日付（YYYY-MM-DD）** → 「本日パトロール済み」として **スキップ表示** を出して終了:

```
━━━━━━━━━━━━━━━━━━━
  PARK PATROL ✅ 本日チェック済み
━━━━━━━━━━━━━━━━━━━
```

- ファイルが存在しない、または日付が今日より前 → Step 1 へ進む

### Step 1: パトロール開始表示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PARK PATROL
  スキル自動進化パトロール
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  巡回中...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 2: 情報収集（WebSearch を使用）

以下の **5つの検索** を実行する。全て WebSearch ツールで行う。

**検索1: LM Arena 画像生成ランキング**
```
検索クエリ: "LM Arena image generation ranking 2026" OR "lmarena.ai image leaderboard"
目的: GPT Image 1.5（現1位）とGemini 3 Pro Image（現2位）の順位変動、新モデルの登場を検出
```

**検索2: AI画像生成モデル最新ニュース**
```
検索クエリ: "AI image generation new model 2026" (直近1週間)
目的: GPT Image 2.0、Imagen 5、FLUX新版、Midjourney v7 など新モデルのリリース情報
```

**検索3: AI動画生成の最新動向**
```
検索クエリ: "AI video generation latest model 2026" (直近1週間)
目的: Sora、Veo、Runway、Kling など動画生成の進化 → Short Ad Park への影響
```

**検索4: OpenAI / Google API変更**
```
検索クエリ: "OpenAI API update 2026" OR "Google Gemini API update 2026" (直近1週間)
目的: 価格改定、新機能追加、非推奨化などAPI変更 → 全スキルへの影響
```

**検索5: 広告クリエイティブトレンド**
```
検索クエリ: "digital advertising creative trends 2026" OR "広告クリエイティブ トレンド 2026"
目的: 新しいフォーマット、プラットフォーム仕様変更 → Banner Park / Short Ad Park への影響
```

### Step 2.5: パク理解 — Slack スキャン

**目的**: 相棒として、パクの今日の思考・関心・戦略を理解し、ナレッジDBに蓄積する。

#### 2.5-a: パクの発言を収集

以下の Bash コマンドで、パクさん（U04PULV9TQ9）の直近24時間の発言を取得する。
**対象チャンネル**（パクの思考が最も濃いチャンネル）:

```bash
TOKEN="$(zsh -i -c 'echo $SLACK_BOT_TOKEN' 2>/dev/null)"
OLDEST=$(python3 -c "import time; print(int(time.time()) - 86400)")

# チャンネルごとにファイル保存（チャンネル直投稿 + スレッド返信）
# C05H9N7C33L = #sr-99-パクの脳内可視化-with相棒のaiパクくん（メイン）
# C05H8388YR1 = #all-03-雑談
for CH in C05H9N7C33L C05H8388YR1; do
  curl -s "https://slack.com/api/conversations.history?channel=$CH&oldest=$OLDEST&limit=50" \
    -H "Authorization: Bearer $TOKEN" -o "/tmp/slack_patrol_${CH}.json" 2>/dev/null
done

# スレッド返信も取得（reply_count > 0 のメッセージのスレッドを展開）
python3 << 'PYEOF'
import json, glob, subprocess, os, time

TOKEN = subprocess.run(["zsh", "-i", "-c", "echo $SLACK_BOT_TOKEN"],
                       capture_output=True, text=True).stdout.strip()
PAK_ID = "U04PULV9TQ9"
OLDEST = str(int(time.time()) - 86400)
CHANNELS = ["C05H9N7C33L", "C05H8388YR1"]

msgs = []  # パクの発言（チャンネル直投稿 + スレッド返信）

for ch_id in CHANNELS:
    fpath = f"/tmp/slack_patrol_{ch_id}.json"
    try:
        with open(fpath) as f:
            d = json.load(f)
    except:
        continue

    for m in d.get("messages", []):
        # チャンネル直投稿
        if m.get("user") == PAK_ID:
            msgs.append(m.get("text", ""))

        # スレッドがある場合、返信も取得
        if m.get("reply_count", 0) > 0:
            ts = m.get("ts", "")
            tmp = f"/tmp/slack_thread_{ch_id}_{ts}.json"
            subprocess.run([
                "curl", "-s",
                f"https://slack.com/api/conversations.replies?channel={ch_id}&ts={ts}&oldest={OLDEST}&limit=50",
                "-H", f"Authorization: Bearer {TOKEN}",
                "-o", tmp
            ], capture_output=True)
            try:
                with open(tmp) as tf:
                    td = json.load(tf)
                for rm in td.get("messages", []):
                    # スレッド内のパク発言（親メッセージは重複するのでスキップ）
                    if rm.get("user") == PAK_ID and rm.get("ts") != ts:
                        msgs.append(rm.get("text", ""))
            except:
                pass

print(json.dumps(msgs, ensure_ascii=False, indent=2))
PYEOF
```

**注意**: チャンネルが追加/アーカイブされた場合は、このリストを更新する。`conversations.join` でBotが事前参加済みであること。

#### 2.5-b: パクのリアクション傾向を収集

パクがリアクションしたメッセージも、関心の指標として重要。
AI-Park チャンネルの最新メッセージから、パクのリアクションがあるものを抽出する。

#### 2.5-b2: パクの X（Twitter）スキャン（X API v2）

**目的**: Slack外でのパクの思考・関心・インプットを把握する。

以下の Bash スクリプトで X API v2 経由でパクの直近ツイート＋いいね＋ブックマークを取得する。

```bash
# === X API: パクのツイート + いいね + ブックマーク取得 ===
zsh -i -c 'python3 << "PYEOF"
import os, json, urllib.request, urllib.parse, base64

CK = os.environ.get("X_CONSUMER_KEY", "")
CS = os.environ.get("X_CONSUMER_SECRET", "")
AT = os.environ.get("X_ACCESS_TOKEN", "")
ATS = os.environ.get("X_ACCESS_TOKEN_SECRET", "")
BEARER = os.environ.get("X_BEARER_TOKEN", "")
OAUTH2_CLIENT_ID = os.environ.get("X_OAUTH2_CLIENT_ID", "")
OAUTH2_CLIENT_SECRET = os.environ.get("X_OAUTH2_CLIENT_SECRET", "")
USER_ID = "523335409"  # @masapark95
TOKEN_FILE = os.path.expanduser("~/Desktop/パクの戦略室/AIパク/.claude/knowledge/x_oauth2_token.json")

result = {"tweets": [], "likes": [], "bookmarks": []}

# --- 1. 最新ツイート（Bearer Token） ---
req = urllib.request.Request(
    f"https://api.twitter.com/2/users/{USER_ID}/tweets?max_results=10&tweet.fields=text,created_at,public_metrics",
    headers={"Authorization": f"Bearer {BEARER}"}
)
try:
    with urllib.request.urlopen(req) as resp:
        result["tweets"] = json.loads(resp.read()).get("data", [])
except Exception as e:
    result["tweets_error"] = str(e)

# --- 2. いいねしたツイート（OAuth 1.0a） ---
try:
    from requests_oauthlib import OAuth1Session
    oauth = OAuth1Session(CK, client_secret=CS, resource_owner_key=AT, resource_owner_secret=ATS)
    r = oauth.get(f"https://api.twitter.com/2/users/{USER_ID}/liked_tweets",
        params={"max_results": 10, "tweet.fields": "text,created_at,author_id"})
    if r.status_code == 200:
        result["likes"] = json.loads(r.text).get("data", [])
    else:
        result["likes_error"] = f"{r.status_code}: {r.text[:100]}"
except Exception as e:
    result["likes_error"] = str(e)

# --- 3. ブックマーク（OAuth 2.0 + refresh token） ---
def refresh_oauth2_token(rt):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": rt}).encode()
    creds = base64.b64encode(f"{OAUTH2_CLIENT_ID}:{OAUTH2_CLIENT_SECRET}".encode()).decode()
    req = urllib.request.Request("https://api.twitter.com/2/oauth2/token", data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Authorization", "Basic " + creds)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

try:
    with open(TOKEN_FILE) as f:
        oauth2 = json.load(f)
    access_token = oauth2["access_token"]
    # Try bookmarks
    req = urllib.request.Request(
        f"https://api.twitter.com/2/users/{USER_ID}/bookmarks?max_results=10&tweet.fields=text,created_at,author_id",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result["bookmarks"] = json.loads(resp.read()).get("data", [])
    except urllib.error.HTTPError as e:
        if e.code == 401 and "refresh_token" in oauth2:
            # Token expired, refresh
            new_tokens = refresh_oauth2_token(oauth2["refresh_token"])
            with open(TOKEN_FILE, "w") as f:
                json.dump(new_tokens, f, indent=2)
            req2 = urllib.request.Request(
                f"https://api.twitter.com/2/users/{USER_ID}/bookmarks?max_results=10&tweet.fields=text,created_at,author_id",
                headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
            )
            with urllib.request.urlopen(req2) as resp2:
                result["bookmarks"] = json.loads(resp2.read()).get("data", [])
        else:
            result["bookmarks_error"] = f"{e.code}: {e.read().decode()[:100]}"
except Exception as e:
    result["bookmarks_error"] = str(e)

with open("/tmp/x_patrol.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

tc = len(result.get("tweets", []))
lc = len(result.get("likes", []))
bc = len(result.get("bookmarks", []))
print(f"Tweets: {tc}, Likes: {lc}, Bookmarks: {bc}")
PYEOF'
```

結果は `/tmp/x_patrol.json` に保存される。以下を抽出:
- **ツイート**: パクが何を発信しているか（RT含む）
- **いいね**: どんな投稿に反応しているか → 関心の指標
- **ブックマーク**: パクが後で読みたい・重要と思った投稿 → 深い関心の指標
- **Slack とのクロスチェック**: Slack で共有されたX記事との関連性

**注意**:
- X ハンドル: `@masapark95` (User ID: 523335409)
- ハンドルが変わった場合は `.claude/knowledge/pak-insight.md` の基本プロファイルと上記 USER_ID を更新すること
- OAuth 1.0a キーが無効になった場合: X Developer Console で Access Token を再生成し `.zshrc` を更新
- ブックマークは OAuth 2.0 PKCE が必要なため未対応

#### 2.5-b3: パクの Chatwork スキャン

**目的**: DProユーザーとのやり取り、チームへの指示、未完了タスクを把握する。

以下の Bash スクリプトで Chatwork API 経由でパクの直近メッセージを取得する。

```bash
# === Chatwork API: パクの直近メッセージ取得 ===
zsh -i -c 'python3 << "PYEOF"
import os, json, urllib.request, time
from datetime import datetime

TOKEN = os.environ.get("CHATWORK_API_TOKEN", "")
PAK_ID = 7115249  # パク(河野) のアカウントID

# 重要ルーム（パクの思考が濃いルーム）
ROOMS = {
    280535397: "全体連絡部屋【動画広告分析Pro】",
    423036437: "【Claude Code DIVE】みんなで遊ぶ部屋",
    409044202: "CMO AI メイン",
}

result = {"messages": [], "errors": []}

for room_id, room_name in ROOMS.items():
    try:
        req = urllib.request.Request(
            f"https://api.chatwork.com/v2/rooms/{room_id}/messages?force=1",
            headers={"X-ChatWorkToken": TOKEN}
        )
        with urllib.request.urlopen(req) as resp:
            msgs = json.loads(resp.read())

        cutoff = int(time.time()) - 86400 * 3  # 直近3日
        for m in msgs:
            if m["send_time"] > cutoff:
                result["messages"].append({
                    "room": room_name,
                    "name": m["account"]["name"],
                    "is_pak": m["account"]["account_id"] == PAK_ID,
                    "time": datetime.fromtimestamp(m["send_time"]).strftime("%Y-%m-%d %H:%M"),
                    "body": m["body"][:300]
                })
    except Exception as e:
        result["errors"].append(f"{room_name}: {str(e)[:100]}")

with open("/tmp/chatwork_patrol.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

pak_msgs = [m for m in result["messages"] if m["is_pak"]]
other_msgs = [m for m in result["messages"] if not m["is_pak"]]
print(f"Chatwork: パク {len(pak_msgs)}件, 他 {len(other_msgs)}件 (直近3日)")
PYEOF'
```

結果は `/tmp/chatwork_patrol.json` に保存される。以下を抽出:
- **パクの投稿**: DProユーザーへの告知・連絡内容
- **他メンバーの反応**: ユーザーからの質問・要望
- **未完了タスク**: パクが「やる」「作る」「検討する」と言った未完了事項
- **Slack/Xとのクロスチェック**: 同じトピックの言及があるか

**注意**:
- Chatwork アカウントID: 7115249（パク(河野) / 動画広告分析Pro / Pro ai）
- `CHATWORK_API_TOKEN` を `.zshrc` に設定済みであること
- ルームが追加された場合は ROOMS dict を更新する

#### 2.5-c: 分析＆蓄積

収集した **Slack発言・リアクション・X活動・Chatwork** から、以下を **短く** 抽出する:

1. **今日の関心事**: パクが今日触れたテーマ（箇条書き3-5個）
2. **戦略的思考**: 意思決定や方向性に関する発言があれば記録
3. **感情・テンション**: 発言のトーンから読み取れるパクの状態（1行）
4. **X での動き**: 公開発信や反応から読み取れる関心（1-2行）
5. **Chatwork での動き**: DProユーザーへの連絡・チーム指示・未完了タスク（1-2行）

抽出結果を `.claude/knowledge/pak-insight.md` に追記する:
- 「パクの今の関心事」セクションを最新の内容で **上書き**
- 「日別ログ」セクションに今日のエントリーを **先頭に追加**

日別ログのフォーマット:
```markdown
### YYYY-MM-DD
- **発言数**: X件（Slack）/ X のポストY件 / Chatwork Z件
- **関心テーマ**: テーマ1, テーマ2, テーマ3
- **戦略メモ**: {あれば1行で。なければ省略}
- **X の動き**: {注目トピック・いいね傾向。なければ省略}
- **Chatwork**: {DProユーザー向け連絡・未完了タスク。なければ省略}
- **テンション**: {絵文字1個 + 1行}
```

#### 2.5-d: レポートへの反映

Step 5 のレポートに以下を追加表示する:

```
  👤 パク今日の動き:
  - Slack: {テーマ1, テーマ2}
  - X: {注目トピック}
  - Chatwork: {DPro連絡・未完了タスク}
  - テンション: {1行}
```

**ADHD設計**: この部分は3行以内に収める。パクが自分のことを長々と読まされても困る。

---

### Step 2.6: リポジトリ健康診断

**目的**: git repo に大容量ファイルや未整理の差分が溜まる前に検知し、push不可 / session肥大 / 整理コスト膨張を予防する。

**背景**: 2026-04-19 に video-ai/fv_studio/uploads/ に3.6GB / 動画80ファイルが混入し、GitHub 100MB制限で push不可になった事故が発生。原因は `.gitignore` メンテ怠慢。事前検知できれば2時間の整理作業を予防できた。

以下の bash を実行し、3つの健康指標を取得する:

```bash
# --- 健康指標1: 50MB超のgit追跡ファイル ---
LARGE_FILES=$(git ls-files -z | xargs -0 -I {} sh -c 'if [ -f "{}" ]; then sz=$(stat -f%z "{}" 2>/dev/null); if [ "$sz" -gt 52428800 ] 2>/dev/null; then echo "$sz {}"; fi; fi' 2>/dev/null | sort -rn | head -5)

# --- 健康指標2: .gitignore に入るべき疑いフォルダの検出 ---
# ランタイム生成型っぽいフォルダ名 (uploads/, output/, cache/, tmp/, generated/, .cache/) がgit追跡下にあるか
SUSPICIOUS_DIRS=$(git ls-files | awk -F'/' '{for(i=1;i<NF;i++){if($i~/^(uploads|output|cache|tmp|generated|\.cache|node_modules)$/){print $0; break}}}' | awk -F'/' '{path=""; for(i=1;i<=NF;i++){if(path)path=path"/"; path=path $i; if($i~/^(uploads|output|cache|tmp|generated|\.cache|node_modules)$/){print path; break}}}' | sort -u | head -5)

# --- 健康指標3: 未コミット変更件数 ---
UNSTAGED_COUNT=$(git status --short | wc -l | tr -d ' ')

# 出力
echo "LARGE_FILES: $LARGE_FILES"
echo "SUSPICIOUS_DIRS: $SUSPICIOUS_DIRS"
echo "UNSTAGED_COUNT: $UNSTAGED_COUNT"
```

**判定基準:**

| 指標 | 注意 (🟡) | 警告 (🔴) |
|---|---|---|
| 50MB超 git追跡ファイル | 1件以上 | 100MB超 1件以上（= push不可） |
| 疑いフォルダがgit追跡下 | 1個以上 | ー |
| 未コミット変更件数 | 50件以上 | 100件以上 |

**Step 5 レポートへの反映:**

すべてクリアなら:
```
  🏥 リポ健康: ✅ クリア
```

何かあれば:
```
  🏥 リポ健康: ⚡ 注意あり
     - 🔴 100MB超ファイル: {パス}（push不可）
     - 🟡 50MB超ファイル: {件数}件
     - 🟡 疑いフォルダがgit下: {パス}（.gitignore追加推奨）
     - 🟡 未コミット {件数}件（コミット推奨）
```

**⚡ 要注目の判定基準に追加（Step 5 原則）:**
- **100MB超ファイル検出** → 🔴 最優先。Park Kaizen 提案を出す前に `git-cleanup-captain`（未実装のSkill提案あり）で対応
- **疑いフォルダ検出** → 🟡 中。`.gitignore` 更新を推奨アクションで出す
- **未コミット100件超** → 🟡 中。整理コストが膨張中。いったん `/おつかれ` で commit 推奨

---

### Step 3: 過去のパトロール記録を読み込み

以下のファイルを Read する:

```
.claude/knowledge/patrol-log.md
```

- 存在する場合 → 前回までの検出事項を把握し、「既に対応済み」の項目を除外
- 存在しない場合 → 初回パトロールとして扱う

### Step 4: 現在のスキル構成を確認

各スキルの現行バージョンと主要構成を把握するため、以下を Read する:

```
.claude/commands/banner-park.md     → 冒頭30行（バージョン・搭載システム）
.claude/commands/shortad-park.md    → 冒頭30行
.claude/commands/記事LP-park.md      → 冒頭30行
```

### Step 5: 分析＆レポート生成

Step 2〜4 の情報を統合し、以下のフォーマットで **簡潔に** レポートを出力する。

**原則: ADHD設計 — 短く、アクション明確に、ダラダラ書かない**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PARK PATROL REPORT  YYYY-MM-DD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  👤 パク今日の動き:
  - 関心: {テーマ1, テーマ2, テーマ3}
  - テンション: {絵文字 + 1行}

  🖼️ 画像生成:  {変動なし | ⚡ 要注目: 内容}
  🎬 動画生成:  {変動なし | ⚡ 要注目: 内容}
  🔌 API変更:   {変動なし | ⚡ 要注目: 内容}
  📢 広告トレンド: {変動なし | ⚡ 要注目: 内容}
  🏥 リポ健康: {✅ クリア | ⚡ 注意あり: 内訳}

  ─────────────────────────────────────────
  影響スキル:
  - Banner Park ver.X.X    → {異常なし | ⚡ アクション内容}
  - Short Ad Park ver.X.X  → {異常なし | ⚡ アクション内容}
  - 記事LP Park ver.X.X    → {異常なし | ⚡ アクション内容}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**⚡ 要注目の判定基準:**

1. **LM Arena ランキング変動**: 現在採用中のモデル（GPT Image 1.5, Gemini 3 Pro Image）の順位が下がった、または新モデルが1-2位に入った
2. **新モデルリリース**: 明確に現行モデルを上回る性能のモデルが一般公開された
3. **API破壊的変更**: 現在使用中のAPIエンドポイントやモデルIDが非推奨化・廃止予定
4. **価格改定**: 現行モデルの大幅値上げ、または高性能な安価モデルの登場
5. **広告プラットフォーム変更**: Meta/Google/TikTok等の広告仕様変更でクリエイティブ要件が変わった

**判定基準に当てはまらない場合は「変動なし」と書く。ノイズを拾わない。**

### Step 6: ⚡ 要注目があった場合のアクション提案

⚡ が1つ以上ある場合のみ、以下を追加表示:

```
  ─────────────────────────────────────────
  💡 推奨アクション:
  1. {具体的なアクション}（緊急度: 🔴高 / 🟡中 / 🟢低）
  2. ...

  → /park-kaizen で対応する？ (y/n)
  ─────────────────────────────────────────
```

ユーザーが `y` と答えたら、Park Kaizen を起動して改善セッションに移行する旨を伝える。

### Step 7: 記録の保存

#### 7-a: タイムスタンプ更新

以下のファイルに今日の日付を書き込む:

```
.claude/knowledge/patrol-last-run.txt
```

中身: `YYYY-MM-DD` （日付のみ）

#### 7-b: パトロールログ追記

以下のファイルに結果を **追記** する（先頭に追加、最新が上）:

```
.claude/knowledge/patrol-log.md
```

追記フォーマット:

```markdown
## YYYY-MM-DD

### パクの動き
- 関心: {テーマ}
- テンション: {1行}

### 検出事項
- {検出した変化を箇条書き。変化なしの場合は「変動なし」}

### アクション
- {提案したアクションと、ユーザーの反応（対応する/スキップ）}

---
```

ログが長くなりすぎた場合（50エントリー超）、古い方から削除して最新30エントリーを維持する。

---

## 現在のスキル構成（パトロール基準値）

パトロール時に「変化があったか」を判定するための基準値。スキルが更新されたら、ここも Park Kaizen が更新する。

```yaml
banner_park:
  version: "5.4"
  engines:
    - name: "GPT Image 1.5"
      model_id: "gpt-image-1.5"
      provider: "OpenAI"
      lm_arena_rank: 1
      lm_arena_elo: 1264
      slots: "#1-5"
    - name: "Gemini 3 Pro Image"
      model_id: "gemini-3-pro-image-preview"
      provider: "Google"
      lm_arena_rank: 2
      lm_arena_elo: 1235
      slots: "#6-10"
  text_rendering: "HTML overlay"
  api_keys: ["OPENAI_API_KEY", "GEMINI_API_KEY / _2 / _3"]

shortad_park:
  version: "4.3"
  video_generation: "none (script only)"
  notes: "台本品質革命 × 映像プロンプト構造化"

article_lp_park:
  version: "2.2"
  notes: "渾身の2本 × FV3パターン × FB深化分析 × 品質ゲート"
```

---

## 注意事項

- **ノイズフィルタリング**: 噂・リーク・ベータ版は ⚡ にしない。一般公開（GA）されたものだけ拾う
- **ADHD設計**: レポートは最短で。変化なしなら3行で終了。長文禁止
- **過剰反応しない**: 毎週「全部入れ替え！」にならないよう、本当に影響があるものだけフラグ
- **WebSearch 必須**: 全検索はメインエージェントの WebSearch で実行（サブエージェントには権限が渡らないため）
