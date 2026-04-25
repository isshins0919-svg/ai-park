---
# 🤝 HANDOFF — 2026-04-25 KOSURI v5 N1+RAG 本番反映完了

## このセッションのゴール
KOSURI品質向上の2タスク（N1軸プロファイル + DPro勝ちFV RAG化）を実装し、QA品質チェックを通して本番反映する。

---

## 完了済み ✅

### 実装
- ✅ N1軸プロファイル追加（4商品: gungun / proust / onmyskin / rkl）
  - scene / emotion / visual_hook_emotion / target_moment の4要素
  - `build_profile_injection()` で「【N1ターゲット（1カット目で刺せ）】」として注入
- ✅ DPro勝ちFV RAG化
  - `data/dpro_fv_patterns.json`: 5ジャンル×79件 / `gemini-embedding-2-preview` 3072次元 / 3.14MB
  - `scripts/build_dpro_rag.py`: DProAPI → embed → JSON保存（レート制御済）
  - `profile_loader.search_dpro_patterns()`: N1+ペルソナで cosine類似 TOP-k検索（cost加重・キャッシュ付）
  - `build_profile_injection()` 末尾に【DPro勝ちFVパターン TOP3】自動注入
  - `KOSURI_DPRO_RAG=0` で無効化可
- ✅ requirements.txt に `google-genai` 追加
- ✅ Dockerfile に `PYTHONUNBUFFERED=1` 追加（Cloud Run ログ遅延対策）

### QA
- ✅ 62テスト全合格（基本50 + 深層12）
- ✅ 5人の動画編集者シミュレーション全パス（フックフィルタ正常・リーク0）
- ✅ DPro RAG sim: gungun=0.85 / proust=0.81 / onmyskin=0.78 / rkl=0.80
- ✅ 回帰テスト: ①②③ファイル名 / mkdir parents / 429リトライ 全件OK
- ✅ 並列性: 10スレッド×12回 race無し / jobs dict 800並列書き込みOK
- ✅ レポート: `reports/kosuri_qa_report.md` (258行)

### デプロイ
- ✅ Cloud Run revision 30 → **32** へ更新（2026-04-25 01:26 UTC ビルド）
- ✅ Status: Ready / URL: `https://kosuri-studio-mbhuqpt6ma-an.a.run.app`
- ✅ env: `GEMINI_API_KEY` 設定済 → 本番でRAG embedding 動作可能

### コミット
- `b3b315a` feat(kosuri): N1軸プロファイル + DPro勝ちFV RAG化
- `40a210c` qa(kosuri): v5 品質チェック 62テスト全合格 + Dockerfile微修正

---

## 次セッションでやること 🚀

### 【優先度1】 5人の編集者リアル運用 → フィードバック収集（必須）
**動作確認なき品質改善は座礁する。**

1. 後輩編集者に「商品セレクタから選んで10パターン生成してみて」と展開
2. 1週間程度の運用で以下のフィードバックを収集:
   - 生成された画像が「N1感情に刺さってるか」
   - DPro勝ち広告の構成参考が「実際に活きてるか」
   - 旧バージョン（N1なし）と比較して mCVR or 着地CVR の変化
3. 集めたフィードバックを `feedback.json` または `kosuri-history.md` に集約

### 【優先度2】 rkl の DPro パターン拡充
- 現状: `genre_id=1467 (ヘルスケア用品)` のみ20件 → TOP3に異ジャンル混入
- 対策: `genre_id=92 (健康サプリ)` も収集対象に追加 → 関連度UP
- 手順: `scripts/build_dpro_rag.py` の `SOURCE_FILES` に新ジャンル追加 → MCP get_items_by_rds → 再ビルド

### 【優先度3】 A/Bテスト設計（CKO連携）
- 旧FV(N1なし) vs 新FV(N1+RAG) で着地CVR差分を測る
- Squad Beyond で2系統並列、最低14日 / セッション200以上で有意差判定
- 結果を `kiji-rag` 同様に Cloud Run 履歴と紐付けて学習材料化

### 【優先度4・後回しOK】 FVカット精度向上（CapCut対応）
- 前セッション handoff から持ち越し: CapCut動画のカット点±50msズレ
- `app.py` のFVカット分析ロジックに前後50ms自動トリミング追加

### 【優先度5・必須ではない】 軽微な改善
- jobs dict TTL（現状無制限増加 → min-instances=1の再起動で実質OK）
- `_DPRO_CACHE.query_vec_by_key` の TTL（プロファイル更新時の古いキャッシュ）

---

## プラン詳細（設計メモ）

### N1注入の構造
```yaml
n1:
  scene: "[誰が][どこで][何をしている瞬間]"
  emotion: "[現状感情] × [希望感情]"
  visual_hook_emotion: "[1カット目で何を見せるか]"
  target_moment: "[いつターゲットがこの広告に出会うか]"
```
→ `build_profile_injection()` で「1カット目で刺せ」として強調注入。Geminiが画像プロンプト設計時にN1感情を踏まえる。

### RAG検索の重み付け
```python
score = cosine_sim(query_vec, pattern_vec) + log10(cost_difference) / 200
```
- メイン: cosine類似度（意味マッチ）
- 微加重: cost_difference（勝ちの強さ）
- TOP-k=3 をプロンプト末尾に「冒頭120字 + 冒頭セリフ + cost / sim / ジャンル / 媒体」で注入

### キャッシュ階層
- L1: `_DPRO_CACHE["patterns"]` — モジュールロード時1回だけJSON読込
- L2: `_DPRO_CACHE["query_vec_by_key"]` — product_keyごとにクエリembedをキャッシュ
- → Cloud Run 1ワーカー内で2回目以降のRAG検索は ~37ms（embed呼び出し無し）

### Cloud Run env構成
- `GEMINI_API_KEY` ← embedding + 画像生成 + 動画解析で使用
- `GOOGLE_SERVICE_ACCOUNT_JSON_B64` ← GCS署名URL用
- `GCS_BUCKET` ← セッションファイル保管
- `APP_PASSWORD` ← デフォルト `kosuri.yomite`（編集者と共有）

---

## 注意点 ⚠️

1. **deploy.sh は `~/Desktop/一進VOYAGE号/` で実行** — homeディレクトリで叩くと "No such file" になる（一進さんが今日踏んだ地雷）
2. **Cloud Run env は deploy.sh では設定しない** — `gcloud run deploy` は既存env vars を保持するが、**新規追加するときは別途 `--set-env-vars` か Console から手動**
3. **DPro パターンDB再生成時の rate limit** — `gemini-embedding-2-preview` は ~60req/min なので `build_dpro_rag.py` は1.1秒/件のレート制御済。100件超なら更に粘る必要あり
4. **rkl の TOP3 sim=0.72** — 件数足りないだけで仕組みは正常。混入したジャンルでも意味的には参考になる広告なので致命的ではない
5. **N1のscene文字数** — 現在36-40字。長すぎず短すぎずのちょうどいいライン。次回更新時もこのレンジを保つ
6. **動画編集者へ展開時** — `KOSURI_DPRO_RAG=0` を環境変数で渡せばRAG無効。トラブル時の切り戻し用

---

## 関連ファイル

- 実装: `video-ai/fv_studio/profile_loader.py` (search_dpro_patterns, build_profile_injection)
- データ: `video-ai/fv_studio/data/dpro_fv_patterns.json` (3.14MB / 79件)
- 構築: `video-ai/fv_studio/scripts/build_dpro_rag.py`
- QA: `video-ai/fv_studio/scripts/qa_harness.py` + `qa_deep_audit.py`
- レポート: `reports/kosuri_qa_report.md`
- プロファイル: `.claude/clients/yomite/{gungun,proust,onmyskin,rkl}/kosuri-profile.yaml`

---

## 次セッション用ワンライナー

> `.claude/handoff/handoff_2026-04-25_kosuri-deployed.md` を読んで、KOSURI v5の次フェーズに入って。最初は「5人の編集者リアル運用フィードバックがあれば集約、なければ rkl の DPro パターン拡充（genre_id=92 健康サプリ追加）」から。

---
