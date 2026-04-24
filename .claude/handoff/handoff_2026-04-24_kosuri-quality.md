---
# 🤝 HANDOFF — 2026-04-24 KOSURI品質向上

## このセッションのゴール
KOSURI v5 品質向上タスクの引き継ぎ。N1軸プロファイル追加 + DPro勝ちFV RAG化。

---

## 前セッションでの完了 ✅

- ✅ v5 テロップ位置自動検出 (`_detect_caption_placement_from_segments()`)
- ✅ Cloud Run 商品プロファイル対応 (deploy.sh + profile_loader.py フォールバック)
- ✅ ①②③ファイル名バグ修正 (`_sanitize_filename_prefix()`)
- ✅ Gemini 429 対策 (`_gemini_request_with_retry()` + GCP 請求先有料化)
- ✅ FVカット mkdir 500 修正 (全13箇所 `parents=True`)
- ✅ パスワード認証 `kosuri.yomite` 追加・後輩へ展開済み
- ✅ 注釈デフォルト文字設定
- ✅ アップロード状態可視化 (`_setZoneUploading/Done()`)
- ✅ Cloud Run デプロイ完了: `https://kosuri-studio-mbhuqpt6ma-an.a.run.app`

---

## 次セッションでやること 🚀

### 【タスク1】N1軸をプロファイルに追加（品質向上・最優先）

**背景**:
記事LP知見のN1ペルソナ×感情軸をKOSURIに注入し、「刺さるFV」精度を上げる。
現状プロファイルは商品スペック中心で「誰の、どんな瞬間の感情に刺さるか」が薄い。

**実装内容**:

1. 4商品 (`gungun / proust / onmyskin / rkl`) の `kosuri-profile.yaml` に追加:
   ```yaml
   n1:
     scene: "深夜0時、鏡で顔をチェックして溜め息をついている28歳OL"
     emotion: "現状への焦り × 変われるかもという期待"
     visual_hook_emotion: "Before→After の劇的変化を1カット目で見せる"
     target_moment: "洗顔後スキンケアタイム、一人の時間"
   ```

2. `video-ai/fv_studio/app.py` の `_build_kosuri_injection()` でn1をプロンプト注入:
   ```python
   if n1 := profile.get("n1"):
       lines.append(f"【N1ターゲット】シーン: {n1.get('scene', '')}")
       lines.append(f"感情軸: {n1.get('emotion', '')}")
       lines.append(f"ビジュアルフック: {n1.get('visual_hook_emotion', '')}")
   ```

**参考ファイル**:
- `.claude/clients/yomite/gungun/kosuri-profile.yaml` (既存)
- `.claude/knowledge/pak-philosophy.md` (N1設計思想)

---

### 【タスク2】DPro勝ちFVのRAG化（品質向上・中期）

**背景**:
DPro TOP広告のFVビジュアルパターンを参照して生成クオリティを引き上げる。
「人間の発想を超えるビジュアルフック」の実現に必要。

**実装方針（2ステップ）**:

**Step 1: パターンDB作成**
- DPro API (`search_products_with_relevance_api_v1_products_get`) で美容・健康ジャンルTOP広告取得
- 各FVの「ビジュアル構造」「感情フック」「カット構成」を記述
- `video-ai/fv_studio/data/dpro_fv_patterns.json` に格納

**Step 2: 生成時に類似検索→プロンプト注入**
- 商品カテゴリ × ターゲット感情でベクトル類似検索
- TOP3パターンを `_build_kosuri_injection()` 末尾に注入

**Embedding候補**: `models/text-embedding-004`（Gemini、すでにAPIキーあり）
**ベクトルDB**: 初期はJSONにnumpy配列で十分（件数<1000）

---

### 【タスク3】FVカット精度向上（CapCut対応、後回しOK）

CapCut動画のカット点が±50ms程度ズレる問題。
カット検出後に前後50ms自動トリミングを追加する。
場所: `app.py` のFVカット分析ロジック。

---

## 次セッション用ワンライナー

```
.claude/handoff/handoff_2026-04-24_kosuri-quality.md を読んで、KOSURIちゃん品質向上の2タスク（N1軸プロファイル追加 + DPro勝ちFV RAG化）から始めて。
```

---

## Cloud Run 現状

- URL: `https://kosuri-studio-mbhuqpt6ma-an.a.run.app`
- パスワード: `kosuri.yomite`
- デプロイ: `bash video-ai/fv_studio/deploy.sh`
- Project: `yomite-douga-studio-ai` / Region: `asia-northeast1`

## 注意点 ⚠️

1. **GCP 請求先有料化済み** → 429は基本解消。次回テストで確認
2. **N1フィールドは4商品分手書き必要** → pak-philosophy + 各商品ターゲット知識が要る
3. **RAG化はDPro APIアクセス確認から** → APIが繋がるか確認してから設計詰める
4. **min-instances=1** → 使わない期間は0にしてコスト削減可能
