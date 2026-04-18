# video-ai/ — 動画AI作業エリア

動画編集AI（edit_ai_v2, fv_studio, gungun_render 等）の実装・実行領域。

---

## 📁 ディレクトリのルール

### 🟢 git管理下（コード・設定・素材スクリプト）

- `*.py` / `*.md` / `*.json` / `*.csv` — 実装・設定
- `fv_studio/app.py`, `fv_studio/Dockerfile`, `fv_studio/templates/`, `fv_studio/static/` — サーバー実装
- `remotion/` — Remotionテンプレート
- `sakura/` — 固定素材

### 🔴 git管理外（ローカル専用 = `.gitignore` 指定）

| パス | 性質 | 再現方法 |
|---|---|---|
| `fv_studio/uploads/` | ユーザーアップロード動画 + AI中間生成物 | 再アップロード |
| `output/` | `edit_ai_v2.py` 等のAI生成動画 | スキル再実行で再生成 |
| `fv_studio/feedback.json` | 動的ユーザーフィードバック | サーバー稼働で蓄積 |

**Why git管理外?**
- 動画ファイル（50MB〜100MB超）は GitHub の推奨サイズを超える
- AI生成物は再生成可能。コードとプロンプトさえあれば再現できる
- アップロード動画はN1のローカル作業。共有不要

---

## 🤖 動画AIへの指示（将来のAIセッション向け）

このフォルダで作業する時の鉄則:

1. **`uploads/` と `output/` に動画を置くのは自由。ただしcommitするな**
2. **`fv_studio/app.py` の `UPLOAD_DIR` は起動時に自動生成される** — フォルダごと消えててもサーバーは立ち上がる
3. **他デバイスで動画が必要** → 船長がDrive/iCloudで個別共有する運用
4. **生成物を共有したい時** → `reports/clients/{client}/` にサムネ + 説明を置く（動画本体ではなく成果物ドキュメント）

---

## 🔗 関連スキル

- `.claude/commands/movie-kantoku.md` — 動画制作ディレクション
- `.claude/commands/shortad-park.md` — ショート動画生成
- `.claude/commands/sns-marketer.md` — SNS配信用編集

---

## 🚨 2026-04-19 履歴整理済

過去commit（〜2026-04-17）に `uploads/` 配下の大容量動画（最大107MB）が混入しており、
GitHub の 100MB 制限で push不可になってたため、**履歴から完全削除**した。

それ以降は `.gitignore` で防御済。同じミスをしないように。
