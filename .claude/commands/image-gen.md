# Image Gen ver.1.0 — OpenAI gpt-image-1 汎用画像生成スキル

## 目的
プロンプトを渡せば `gpt-image-1` で画像を生成し、指定場所に保存する汎用スキル。
Banner Park / こすりちゃん / 記事LP Park など各スキルから呼び出されるコア画像生成エンジン。

---

## 発動トリガー

- `/image-gen`
- 「画像生成して」「OpenAIで画像作って」「gpt-imageで出して」
- 他スキルからの内部呼び出し（画像生成が必要な任意のPark）

---

## 前提

- `OPENAI_API_KEY` が `~/.zshrc` に設定済み
- `.claude/scripts/openai_image.py` が存在
- OpenAI課金残高がある（billing hard limit未到達）

---

## モデル仕様

- **モデル**: `gpt-image-1`
- **サイズ**: `1024x1024`（正方形）/ `1024x1536`（縦長）/ `1536x1024`（横長）/ `auto`
- **品質**: `low` / `medium` / `high` / `auto`
- **料金目安（1024x1024）**: low $0.011 / medium $0.042 / high $0.167

---

## 実行手順

### Step 1: 引数解釈

ユーザー指示から以下を抽出：
- **prompt**（必須）: 画像プロンプト。日本語でも英語でもOK
- **out**（必須）: 出力先。`.png` 指定ならその名前で、ディレクトリ指定なら `openai_<timestamp>.png`
- **size**（任意、デフォルト `1024x1024`）
- **quality**（任意、デフォルト `medium`）
- **n**（任意、デフォルト `1`。最大10）

指示が曖昧なら1回だけ確認する。

### Step 2: CLI呼び出し

```bash
python3 /Users/ca01224/Desktop/一進VOYAGE号/.claude/scripts/openai_image.py \
  --prompt "<prompt>" \
  --out "<out_path>" \
  --size "<size>" \
  --quality "<quality>" \
  --n <n>
```

または Python モジュールとして import：

```python
from openai_image import generate_image
paths = generate_image(
    prompt="...",
    out_dir="/path/to/dir",
    filename_prefix="banner_a",
    size="1024x1024",
    quality="medium",
    n=1,
)
```

### Step 3: 結果確認

- 生成されたファイルパスを報告
- `Read` で画像を表示（1枚の場合）してユーザーに見せる
- エラー時：原因特定（billing / auth / rate_limit / invalid_request）と対処法を提示

---

## 他スキルからの呼び出しパターン

### Banner Park（エンジン選択オプション）
Banner Park の画像生成ステップで、Gemini (Nano Banana Pro) と並列 or 切替で使う。
プロンプトはBanner Parkが生成 → このスキルで実画像化。

### こすりちゃん（FV画像バリエーション）
FV固定ルール（音声・テロップ・タイミング固定）は守ったまま、
画像だけバリエーション出したい時に呼び出す。

### 記事LP Park（ヒーロー画像 / アイキャッチ）
FV画像やセクション挿絵をAI生成する際の実行エンジン。

---

## 出力先ルール

- **一時テスト**: `/tmp/`
- **Banner Park**: `banner-park/output/<project>/`
- **こすりちゃん**: `video-ai/output/<project>/`
- **記事LP**: `reports/projects/<client>/images/`
- **その他**: ユーザー指定 or `reports/images/`

※ 実名入りクライアント資料を含むプロンプトは使わない（`.claude/rules/anonymize.md` 準拠）

---

## エラーハンドリング

| エラー | 対処 |
|---|---|
| `OPENAI_API_KEY が未設定` | `~/.zshrc` 確認 → `source ~/.zshrc` |
| `billing_hard_limit_reached` | https://platform.openai.com/settings/organization/billing でチャージ |
| `invalid_api_key` | キー再発行 → `~/.zshrc` 更新 |
| `rate_limit_exceeded` | 30秒待機 → 再実行 |
| `invalid_request_error` | プロンプトにOpenAIポリシー違反要素（暴力・成人向け等）がないか確認 |

---

## プロンプト設計のコツ

gpt-image-1 は **英語プロンプトの方が精度高い**（日本語も動くが）。
以下の要素を含めると品質上がる：

- **被写体**: A photorealistic cat / a minimalist logo / ...
- **構図**: close-up / full body / top-down view
- **ライティング**: studio lighting / golden hour / soft diffused light
- **スタイル**: photorealistic / watercolor / flat illustration / cinematic
- **背景**: white background / blurred café / gradient blue
- **品質指示**: high detail / sharp focus / 8k

Gemini (Nano Banana Pro) との比較:
- **gpt-image-1**: テキスト入り画像・ロゴ・正確な構図指示に強い
- **Gemini**: 写真的リアリティ・人物表情・日本語コピー入り画像に強い

---

## バージョン

- **ver.1.0** (2026-04-24): 初版。CLIベース汎用呼び出し + 各Park統合前提
