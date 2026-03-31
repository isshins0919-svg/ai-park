# Skill: generate (rough-cut)

トーク動画のラフカット自動化。無音カット、フィラー除去、リテイク検出、誤字脱字修正、テロップ付与を一気通貫で実行する。

## 使い方

```
/generate {動画ファイルパス} [--project {project.yamlパス}]
```

## 前提条件

- Python 3.11+ (`.venv/bin/python` 推奨)
- FFmpeg (システムインストール)
- Node.js 18+
- ELEVEN_API_KEY 環境変数
- `python/requirements.txt` インストール済み
- `remotion/node_modules` インストール済み

## 実行手順

### 変数定義

```
{vpk_dir} = rough-cut ディレクトリの絶対パス
{run}      = run名 (例: 20260324_test)
{動画パス}  = 入力動画の絶対パス
{project}  = プロジェクト設定パス (省略時は自動判定で vertical.yaml or horizontal.yaml)
```

### 準備

1. run名を決定 (例: `20260324_test`)
2. `runs/{run}/` ディレクトリを作成

### Step 1: preprocess (Python)

```bash
cd {vpk_dir}/python
.venv/bin/python step01_preprocess.py \
  --video {動画パス} \
  --output ../runs/{run}/step01_preprocess
```

出力確認:
- `preprocess.json` の `orientation` フィールドを確認 (vertical or horizontal)
- この値に応じて以降のステップで使う project 設定が決まる
- project 未指定時: `templates/{orientation}.yaml` を自動使用

### Step 2: stt (Python)

```bash
.venv/bin/python step02_stt.py \
  --audio ../runs/{run}/step01_preprocess/audio.wav \
  --output ../runs/{run}/step02_stt
```

出力確認: `stt_result.json` の sentences 数と raw_text をユーザーに報告

### Step 3: vad (Python)

```bash
.venv/bin/python step03_vad.py \
  --audio ../runs/{run}/step01_preprocess/audio.wav \
  --stt ../runs/{run}/step02_stt/stt_result.json \
  --output ../runs/{run}/step03_vad
```

出力確認: 検出された silence_regions 数を報告

### Step 4: filler_detect (Python)

```bash
.venv/bin/python step04_filler_detect.py \
  --stt ../runs/{run}/step02_stt/stt_result.json \
  --vad ../runs/{run}/step03_vad/vad_result.json \
  --output ../runs/{run}/step04_filler_detect
```

出力確認: フィラー数と種類を報告

### Step 4b: filler_review (Claude Code LLM)

Step 4 のパターンマッチ結果を Claude Code が確認・修正する。

1. `runs/{run}/step02_stt/stt_result.json` を Read で読む
2. `runs/{run}/step04_filler_detect/fillers.json` を Read で読む
3. STT テキストを通し読みしながら以下を実施:
   - 検出されたフィラーが本当にフィラーか確認 (誤検出の除外)
   - パターンで検出できなかったフィラーの追加検出
   - 特に「あの」「その」「こう」等の文脈依存フィラーを重点確認
4. 修正が必要な場合、`fillers.json` を更新して Write で上書き保存
5. 修正内容をユーザーに報告

### Step 5: retake_detect (Claude Code LLM)

1. `runs/{run}/step02_stt/stt_result.json` を Read で読む
2. sentences の内容を確認し、言い直しを判断 (retake-detect skill の基準)
3. `runs/{run}/step05_retake_detect/` ディレクトリを作成
4. 結果を `runs/{run}/step05_retake_detect/retakes.json` に Write で保存

### Step 6: review (Claude Code LLM)

1. `runs/{run}/step02_stt/stt_result.json` を Read で読む
2. テキスト全体を通し読みし、以下を実施:
   - 誤字脱字の特定 (STT誤認識、固有名詞の間違い等)
   - カット後の流れの品質チェック
3. `runs/{run}/step06_review/` ディレクトリを作成
4. 結果を `runs/{run}/step06_review/review.json` に Write で保存:
   ```json
   {
     "corrections": {"間違い": "正しい"},
     "quality_notes": ["全体的に問題なし"]
   }
   ```
5. corrections は Step 8 で `--review` 引数経由でテロップに自動反映される

### Step 7: cut_proposal (Python)

scenes.json が必要。リテイク検出結果がなければ空で作成。

```bash
# scenes.json が未作成の場合、空で作成
mkdir -p ../runs/{run}/step06_scene_structure
echo '{"scenes": []}' > ../runs/{run}/step06_scene_structure/scenes.json

.venv/bin/python step07_cut_proposal.py \
  --stt ../runs/{run}/step02_stt/stt_result.json \
  --fillers ../runs/{run}/step04_filler_detect/fillers.json \
  --retakes ../runs/{run}/step05_retake_detect/retakes.json \
  --scenes ../runs/{run}/step06_scene_structure/scenes.json \
  --output ../runs/{run}/step07_cut_proposal
```

出力確認: keep_segments 数、削減率をユーザーに報告し確認を取る

### Step 8: composition (Python)

```bash
.venv/bin/python step08_composition.py \
  --proposal ../runs/{run}/step07_cut_proposal/cut_proposal.json \
  --stt ../runs/{run}/step02_stt/stt_result.json \
  --video {動画パス} \
  --output ../runs/{run}/step08_composition \
  --project ../templates/{orientation}.yaml \
  --review ../runs/{run}/step06_review/review.json
```

`{orientation}` は Step 1 で判定した値 (vertical or horizontal)。
ユーザーが --project で別の yaml を指定した場合はそちらを使う。

出力確認:
- `composition.json` 生成確認
- `segments/` にカットごとのMP4が生成されたか確認
- カット数とテロップページ数を報告

### Step 9: プレビュー (Remotion Studio)

**本番レンダリングの前に必ずプレビューで確認する。**

```bash
cd {vpk_dir}/remotion
npx remotion studio
```

ユーザーに以下を案内:
- ブラウザで http://localhost:3000 を開く
- composition.json を読み込んでプレビュー
- テロップ表示タイミング、見た目、黒フラッシュの有無を確認
- 問題があれば修正してから Step 10 に進む

### Step 10: render (Remotion CLI)

プレビュー確認後にのみ実行。

```bash
cd {vpk_dir}/remotion
npx tsx scripts/render-cli.ts \
  --composition ../runs/{run}/step08_composition/composition.json \
  --output ../runs/{run}/output/final.mp4 \
  --width {display_width} --height {display_height} \
  --concurrency 4
```

`{display_width}` `{display_height}` は composition.json の meta から取得。
concurrency は 4 固定 (8以上だと OffthreadVideo タイムアウト)。

### 完了報告

ユーザーに以下を報告:
- 元動画: {duration}秒 ({orientation})
- 編集後: {edited_duration}秒 (削減率 {reduction}%)
- 検出: フィラー {n}個、リテイク {n}個、無音 {n}箇所
- カット: {n}個、テロップページ: {n}ページ
- 出力: `{出力パス}`
