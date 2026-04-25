# KOSURIちゃん v5 品質チェック レポート

**実行日時**: 2026-04-25 04:09:43
**サマリー**: ✅PASS=50 / ⚠️WARN=0 / ❌FAIL=0 / 💥ERROR=0 ／ **TOTAL 50**

## 1.基盤

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | profile_loader import | profile_loader OK (yaml=True) | 0.1s |
| ✅ | app.py import + routes | 25 routes registered | 1.09s |
| ✅ | data/dpro_fv_patterns.json健全性 | 79 patterns / 3.14MB / dim=3072 | 0.04s |

## 10.法規

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | yomite_gungun NG語リーク検査 | ng=5 copies_clean=6 | 0.01s |
| ✅ | yomite_proust NG語リーク検査 | ng=4 copies_clean=7 | 0.0s |
| ✅ | yomite_onmyskin NG語リーク検査 | ng=4 copies_clean=7 | 0.0s |
| ✅ | yomite_rkl NG語リーク検査 | ng=4 copies_clean=8 | 0.01s |

## 2.プロファイル

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | yomite_gungun load + 必須フィールド | 伸長ぐんぐん習慣 / hooks priority=7 | 0.01s |
| ✅ | yomite_gungun n1 完備 | all n1 fields present (scene=36char) | 0.01s |
| ✅ | yomite_gungun regulation完備 | yakki=strict ng=6 safe=3 | 0.0s |
| ✅ | yomite_proust load + 必須フィールド | プルーストクリーム / hooks priority=7 | 0.01s |
| ✅ | yomite_proust n1 完備 | all n1 fields present (scene=37char) | 0.0s |
| ✅ | yomite_proust regulation完備 | yakki=medium ng=4 safe=4 | 0.0s |
| ✅ | yomite_onmyskin load + 必須フィールド | on:my skin / hooks priority=8 | 0.01s |
| ✅ | yomite_onmyskin n1 完備 | all n1 fields present (scene=40char) | 0.0s |
| ✅ | yomite_onmyskin regulation完備 | yakki=medium ng=5 safe=4 | 0.01s |
| ✅ | yomite_rkl load + 必須フィールド | RKL 膝サポーター / hooks priority=6 | 0.02s |
| ✅ | yomite_rkl n1 完備 | all n1 fields present (scene=38char) | 0.01s |
| ✅ | yomite_rkl regulation完備 | yakki=medium ng=4 safe=4 | 0.01s |

## 3.注入

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | yomite_gungun build_profile_injection | 1761char injection | 4.18s |
| ✅ | yomite_proust build_profile_injection | 1685char injection | 0.48s |
| ✅ | yomite_onmyskin build_profile_injection | 1561char injection | 0.49s |
| ✅ | yomite_rkl build_profile_injection | 1750char injection | 0.58s |
| ✅ | build_profile_injection(None) | empty-safe | 0.0s |

## 4.RAG

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | yomite_gungun DPro RAG top-3 | {"top1": 0.851, "genres": ["成長期サポートサプリ", "成長期サポートサプリ", "成長期サポートサプリ"]} | 0.04s |
| ✅ | yomite_proust DPro RAG top-3 | {"top1": 0.814, "genres": ["体臭ケア", "体臭ケア", "体臭ケア"]} | 0.04s |
| ✅ | yomite_onmyskin DPro RAG top-3 | {"top1": 0.778, "genres": ["スキンケア", "美容液", "美容液"]} | 0.04s |
| ✅ | yomite_rkl DPro RAG top-3 | {"top1": 0.8, "genres": ["ヘルスケア用品", "ヘルスケア用品", "成長期サポートサプリ"]} | 0.04s |
| ✅ | RAGクエリembedキャッシュ | 1st=0.49s 2nd=0.037s (cached) | 0.53s |
| ✅ | KOSURI_DPRO_RAG=0でOFF | RAG-OFF respected | 0.01s |
| ✅ | API_KEY無しでgraceful | no-crash when GEMINI_API_KEY absent | 0.01s |

## 5.エラー系

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | 未登録 product_key | unknown key → None/empty | 0.0s |
| ✅ | malformed key | malformed keys handled | 0.0s |
| ✅ | list_available_products | 4 products listed | 0.02s |

## 6.Flask

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | /health | /health OK status=200 | 0.05s |
| ✅ | /login page | login page OK (1973B) | 0.01s |
| ✅ | 未認証→redirect | / redirects to login (302) | 0.01s |
| ✅ | ログイン後/kosuri-products | /kosuri-products returns 4 products | 0.03s |
| ✅ | パスワード間違い | wrong pw rejected with message | 0.01s |

## 7.デプロイ

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | requirements.txt完備 | all key packages listed | 0.01s |
| ✅ | Dockerfile sanity | Dockerfile has ffmpeg + noto + gunicorn + copy-all | 0.01s |
| ✅ | deploy.sh clients コピー | deploy.sh copies .claude/clients/ into build context | 0.01s |
| ✅ | data/ がgitignoreされてない | data/ not ignored | 0.0s |

## 8.パフォーマンス

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | DBロード速度 | loaded 79 patterns in 35ms | 0.04s |
| ✅ | 注入レイテンシ(4商品) | avg=491ms max=533ms (4 products, first-call embed) | 1.96s |

## 9.編集者5人

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | 編集者A・身長サプリ担当 | {"product": "伸長ぐんぐん習慣", "injection_bytes": 1761, "suffix_bytes": 152, "filtered_hooks": 10, "leaked": 0} | 0.05s |
| ✅ | 編集者B・ワキガクリーム担当 | {"product": "プルーストクリーム", "injection_bytes": 1685, "suffix_bytes": 144, "filtered_hooks": 12, "leaked": 0} | 0.05s |
| ✅ | 編集者C・スキンケア担当 | {"product": "on:my skin", "injection_bytes": 1561, "suffix_bytes": 154, "filtered_hooks": 14, "leaked": 0} | 0.05s |
| ✅ | 編集者D・膝サポーター担当 | {"product": "RKL 膝サポーター", "injection_bytes": 1750, "suffix_bytes": 212, "filtered_hooks": 12, "leaked": 0} | 0.05s |
| ✅ | 編集者E・プロファイル未使用 | {"product": "(generic)", "injection_bytes": 0, "suffix_bytes": 0, "filtered_hooks": 14, "leaked": 0} | 0.01s |

## 総合判定

🚢 **デプロイ可能**: 致命的な問題なし。

---

# 深層監査 (Deep Audit)

**サマリー**: ✅PASS=11 / ⚠️WARN=1 / ❌FAIL=0 / 💥ERROR=0 ／ **TOTAL 12**

## 1.回帰

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | ①②③ファイル名バグ回帰 | 6件の丸数字・絵文字・空文字ケース合格 | 0.55s |
| ✅ | mkdir parents=True 全網羅 | 全13件のmkdirで parents=True 付き | 0.0s |
| ✅ | Gemini 429リトライ経由 | 429リトライ関数経由で呼ばれている | 0.0s |

## 2.互換性

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | Python3.11互換 | 3ファイル全て3.11互換 | 0.01s |

## 3.並列

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | 並列RAG検索 race無し | 10スレッド×12回 = 120回 race無し | 7.26s |
| ✅ | jobs dict 並列書き込み | 800並列書き込み全てdict格納 | 0.02s |

## 4.プロファイル品質

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | N1 scene内容品質 | 全商品でN1の誰が明示 | 0.02s |
| ✅ | 画像suffix年代反映 | 年代/senior指定OK | 0.01s |

## 5.Docker

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | Docker context size | build context: 8.3MB | 0.04s |
| ✅ | data/ build含まれる | data/ は build に含まれる | 0.0s |

## 6.ログ

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ⚠️ | stdout flush対策 | Dockerfile に PYTHONUNBUFFERED=1 なし → ログ遅延の可能性 | 0.0s |

## 7.設計

| 結果 | テスト名 | 詳細 | 時間 |
|---|---|---|---|
| ✅ | google.genai 遅延import | google.genai は遅延import | 0.0s |

---

# 🚢 デプロイチェックリスト & 総合判定

## ✅ デプロイ可能（ブロッカー無し）

総テスト数: **62**（基本50 + 深層12）
- ✅ PASS: 61
- ⚠️ WARN: 1（→ 即修正済: Dockerfile に `PYTHONUNBUFFERED=1` 追加）
- ❌ FAIL: 0
- 💥 ERROR: 0

## 🎬 5人の動画編集者シミュレーション結果

| 編集者 | 商品 | プロファイル | 注入バイト | 画像suffix | フィルタ後フック | リーク |
|---|---|---|---|---|---|---|
| A・身長サプリ担当 | gungun | 伸長ぐんぐん習慣 | 1,761B | 152B (30-40代) | 10個 (V1/V2/V7/V8除外) | 0 |
| B・ワキガクリーム担当 | proust | プルーストクリーム | 1,685B | 144B (20-40代) | 12個 (V8/V12除外) | 0 |
| C・スキンケア担当 | onmyskin | on:my skin | 1,561B | 154B (30-50代) | 14個 (avoid無し) | 0 |
| D・膝サポーター担当 | rkl | RKL 膝サポーター | 1,750B | 212B (senior強制) | 12個 (V2/V3除外) | 0 |
| E・プロファイル未指定 | (generic) | — | 0B | 0B | 14個 | 0 |

→ **5人全員、フックフィルタが正しく機能**。ペルソナに合わない攻めフック（V8嫌悪顔/V12医療など）が確実に除外されている。

## 📊 DPro RAG ヒット精度

| 商品 | TOP1 sim | TOP3ジャンル分布 | 評価 |
|---|---|---|---|
| gungun | **0.851** | 成長期サポートサプリ×3 | 完璧（全件同ジャンル） |
| proust | **0.814** | 体臭ケア×3 | 完璧 |
| onmyskin | **0.778** | スキンケア×1 / 美容液×2 | 良好（ジャンル隣接） |
| rkl | **0.800** | ヘルスケア用品×2 / 成長期サプリ×1 | 許容（DB件数少なめ） |

→ rklのみTOP3に異ジャンル混入。**ヘルスケア用品の収集件数増（次回パターンDB再構築で改善）が推奨タスク**。

## ⚙️ Cloud Run 現状

- URL: `https://kosuri-studio-mbhuqpt6ma-an.a.run.app` ✅ 稼働中
- Latest revision: `kosuri-studio-00030-wrh`
- 設定済 env: `GOOGLE_SERVICE_ACCOUNT_JSON_B64` / `GCS_BUCKET` / `GEMINI_API_KEY` ✅
- → **`GEMINI_API_KEY` 設定済なので RAG embedding が本番で動作**
- 次回 deploy で N1+RAG コードが反映される（コード commit `b3b315a`）

## 🔍 既知の地雷（修正済み・回帰テスト合格）

| 過去バグ | 修正コミット | QAテスト |
|---|---|---|
| ①②③ファイル名HTTPヘッダー破壊 | 04f33b2 | ✅ 6ケース回帰OK |
| FVカット mkdir 500 | 04f33b2 | ✅ 全13箇所 parents=True |
| Gemini 429 リトライ | 04f33b2 | ✅ 全LLM呼び出しが retry経由 |

## 📦 Docker build context

- サイズ: **8.3MB**（uploads/4GB を .dockerignore で除外済）
- Dockerfile: ✅ ffmpeg + Noto CJK + gunicorn + PYTHONUNBUFFERED + COPY全部
- requirements.txt: ✅ google-genai 追加済（RAG runtime用）

## ⚡ パフォーマンス

| 項目 | 計測値 |
|---|---|
| DB JSON ロード（初回） | 35ms |
| プロファイル注入（初回・embed込） | 平均 491ms / 最大 533ms |
| プロファイル注入（2回目以降・cached） | ~37ms |
| 並列10スレ × 12回 RAG検索 | レース条件無し |

→ **FV生成1ジョブあたり追加 +0.5秒** 程度。許容範囲。

## 🔒 法規・薬機法

- 全4商品で NG表現と勝ちコピーの相互チェック：**リーク0**
- gungun: yakkihou=strict / NG=6 / safe=3
- proust: yakkihou=medium / NG=4 / safe=4
- onmyskin: yakkihou=medium / NG=5 / safe=4
- rkl: yakkihou=medium / NG=4 / safe=4

## 🚀 次デプロイ手順（朝、一進さんの判断後）

```bash
cd /Users/ca01224/Desktop/一進VOYAGE号
bash video-ai/fv_studio/deploy.sh
```

→ commit `b3b315a` (N1+RAG) と Dockerfile (PYTHONUNBUFFERED追加) が反映される。

## 🧹 軽微な改善余地（必須ではない）

1. **rkl の DPro パターン件数増** — `genre_id=1467 (ヘルスケア用品)` のサンプルが少ないため、追加で `genre_id=92 (健康サプリ)` あたりも収集すると関連度UP
2. **jobs dict のメモリリーク** — Cloud Run min-instances=1 で長期稼働時に蓄積。完了ジョブの古いものを定期削除する仕組みがあれば理想（`/cancel` の TTL拡張）
3. **`_DPRO_CACHE` の query_vec_by_key TTL** — 商品プロファイル更新時に古いキャッシュが残る。SIGHUP で再読み込み or プロセス再起動で対応中

## 結論

> **🚢 Bon Voyage — デプロイGO**。
> 5人編集者シミュレーション全パス、回帰テスト全パス、本番環境変数設定済み。
> 次回 `bash video-ai/fv_studio/deploy.sh` で N1+DPro RAG が後輩編集者全員の手元で動く。
