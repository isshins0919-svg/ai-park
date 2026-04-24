# データ格納ルール

一進さんがPCにデータを置く時のルール。これを守ればClaudeが自動で発見・活用できる。

---

## 🗂 格納場所のルール

### クライアント資料 → `~/Desktop/_clients/<client-name>/`

- フォルダ名は `.claude/clients/<client-name>.md` と**完全一致**させる
  - 例: `sawada-co.md` ↔ `_clients/sawada-co/`
  - 例: `ameru.md` ↔ `_clients/ameru/`
- 澤田系は全部 `_clients/sawada-co/` に集約（Camicksは別だが、本体資料はsawada-co）
- ヨミテ系はブランド別に分ける（`_clients/gungun/` `_clients/proust/` など）

### 個人ごと → `~/Desktop/_personal/`
- 税金・ローン・保険・個人的メモなど
- Claudeは通常参照しない（聞かれた時だけ）

### マーケ横断知識 → `~/Desktop/marketing/`
- 特定クライアントに紐付かない知見・フレームワーク・口述メモ
- 例: 「マーケ評価基準についてべらべら喋ったメモ.txt」

### 受け渡し一時置き場 → `~/Desktop/_共通素材/`
- 複数案件で使い回す素材（ロゴ・汎用画像・テンプレ）

### ❌ Desktop直下にベタ置きしない
- どこにも紐付かないファイルが溜まると「発見できない資料」になる
- まず置き場所を決めてから置く

---

## 🏷 ファイル命名のルール

### 頭に「何のデータか」を入れる

- ❌ `資料.pdf` `提案書.pdf` `メモ.txt`
- ✅ `澤田_経営計画_第57期.pdf`
- ✅ `ameru_3rdデザイン提案_MTGメモ_2026-04-07.txt`
- ✅ `camicks_競合分析_SLEEPSINERO.pdf`

### 日付を入れる場合は YYYY-MM-DD（または YYYYMMDD）
- ✅ `2026-04-07_xxx.pdf` or `20260407_xxx.pdf`
- ❌ `4月7日_xxx.pdf` `260407_xxx.pdf`（並び順が崩れる）

### 日本語OK、スペースは避ける（アンダースコア推奨）
- `_` でつなぐと Glob / grep で扱いやすい

---

## 📁 サブフォルダのルール

### 1クライアントのファイルが**10件超えたら**サブフォルダ切る

推奨カテゴリ（必要な分だけ）:
```
_clients/<client>/
  ├── 経営・財務/        # 決算・事業計画・KPI
  ├── AI導入・業務改善/   # AI関連資料
  ├── クリエイティブ素材/  # ロゴ・画像・動画素材
  ├── インタビュー生データ/ # 顧客インタビュー・アンケート（実名含む）
  ├── 競合・市場調査/     # ベンチマーク・リサーチ
  ├── MTGメモ/           # 打ち合わせメモ
  └── その他/            # 分類不能の一時置き
```

### インタビュー生データは必ず「インタビュー生データ/」に集める
- `.claude/rules/anonymize.md` で「このフォルダのファイルは匿名化してから出力」ルールに紐付く

---

## 🔄 格納後のアクション

### ファイルを置いたら、Claudeにひとこと

```
「ameruフォルダに新規提案書入れた」
「sawada-coに決算追加した、整理して」
```

→ Claudeが `.claude/clients/<client>.md` のデータソース欄に追記する。

### 何も言わなくても差分チェックできる

```bash
./scripts/check_client_data.sh              # 全クライアント
./scripts/check_client_data.sh sawada-co    # 個別
```

→ 未登録ファイルを検出。起動時「おはよう」でも自動実行しても良い（朝パトロール拡張）。

---

## ⚠️ 絶対NG

- 実名入りファイルを `reports/` `docs/` `banner-park/output/` など**GitHubにpushされる場所**に置く
- クライアント資料を VOYAGE号リポジトリ内（`一進VOYAGE号/` 配下）に直接置く → Desktop/_clients/ に置く
- `.env` APIキー類を `_clients/` に混ぜる → `~/.zshrc` か `~/Desktop/_personal/credentials/` に隔離

---

## 📚 発端

- 2026-04-24: 大量のクライアント資料が Desktop/_clients/ に格納されているが、Claudeが存在すら把握できていない問題を発見
- 「僕がデータ置く→Claudeが自動で発見・活用できる」動線を確立するためにルール制定
