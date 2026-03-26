# インターン生セットアップガイド — mauri担当

> 作成: 2026-03-27 / 対象: 4/1〜 インターン生

---

## このAIで何ができるか

mauri MANUKA HONEYの新規獲得を、AIで高速に回す。

| やること | 使うSkill |
|---|---|
| 商品・競合リサーチ | Research Park |
| バナー画像生成 | Banner Park |
| 記事LP作成 | 記事LP Park |

---

## Step 1: Claude Code をインストールする

### 1-1. インストール

```bash
npm install -g @anthropic-ai/claude-code
```

Node.jsが入っていない場合は先に [https://nodejs.org](https://nodejs.org) からインストール（LTS版）。

### 1-2. ログイン

```bash
claude
```

初回起動時にブラウザが開く → Anthropicアカウントでログイン。
**アカウントはヨミテの会社用メールで作成すること**（一進さんに確認）。

---

## Step 2: APIキーを設定する

バナー生成（Banner Park）にGemini APIキーが必要。

### 2-1. Gemini APIキーを取得

1. [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey) にアクセス
2. Googleアカウントでログイン
3. 「APIキーを作成」→ コピー

### 2-2. ~/.zshrc に追記

```bash
# ターミナルで実行
echo 'export GEMINI_API_KEY_1="ここにAPIキーを貼る"' >> ~/.zshrc
source ~/.zshrc
```

### 2-3. 確認

```bash
echo $GEMINI_API_KEY_1
```

キーが表示されればOK。

---

## Step 3: リポジトリをクローンする

```bash
# Desktopに置く（一進さんと同じ場所）
cd ~/Desktop
git clone [リポジトリURL] AI一進-Claude-Code
cd AI一進-Claude-Code
```

> ※ リポジトリURLは一進さんから共有してもらう。

---

## Step 4: 初回起動

```bash
cd ~/Desktop/AI一進-Claude-Code
claude
```

起動すると自動でセットアップが走る（Git sync / ナレッジ読み込み）。

**最初に確認すること**:
- `GIT SYNC ✅` が表示されるか
- エラーが出ていないか

---

## Step 5: mauri案件を始める

起動後、このように話しかけるだけ：

```
mauri案件やって
```

→ mauriのクライアントファイルが自動で読み込まれる。

### よく使うコマンド

| やりたいこと | 入力例 |
|---|---|
| バナーを作る | `mauriのバナー作って` |
| 記事LPを作る | `mauriの記事LP作って` |
| リサーチする | `mauriのリサーチして` |

---

## mauri案件の基本知識

### ターゲット
- 60代〜女性
- 天然・本物志向、薬に頼らない予防派

### コアコンセプト
> **「本物が守る」**
> 毎朝1杯。体に入れるものは、本物だけでいい。

### 絶対NG表現（薬機法）
- 「抗菌」「免疫力向上」「風邪が治る」「完全無農薬」「生マヌカハニー」
- 子供・家族に言及する場合 → **「1歳未満の乳児には与えないでください」** を必ず入れる

---

## 困ったとき

1. まず `claude` に聞く（AIが答えてくれる）
2. それでも解決しなければ一進さんに確認

---

## データファイルについて

mauri関連の資料（N1インタビュー・商品資料・既存記事）は
**一進さんのMacにある**。インターン生のMacには入っていない。

必要なデータは都度一進さんに共有してもらうか、
Google DriveやSlackで受け取ること。
