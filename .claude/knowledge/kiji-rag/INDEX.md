# kiji-rag INDEX — 格納済み記事一覧

最終更新: 2026-04-26

| article_id | brand | title | fetched | chunks | dominant_layer_dist | strategy_type | mCVR | CVR | status |
|---|---|---|---|---|---|---|---|---|---|
| 20260424_aurelie_megumi_kakusen | Aurelie. | MEGUMIさんの角栓溶解法が話題！毛穴年齢19歳の秘密 | 2026-04-24 | 92 (text46/image46/video0) | E:24/B:16/D:15/C:13/A:10 | 権威×オファー強押し型 | - | - | embedded (3072dim) |
| 20260424_proust_cream2_wakiga | Proust | ワキガに悩む私が実際に体験した出来事です | 2026-04-24 | 55 (text28/image27/video0) | C:15/B:11/D:8/A:4/E:3 | 問題再定義×論理メカニズム型 | 0.76% | 15.0% | embedded (3072dim) / with_performance |
| 20260425_proust_cream2_fuyumotto | Proust | 冬ワキガあるある言います！〜冬のワキガ対策特集〜 | 2026-04-25 | 108 (text161/image33/video29) | C:19/B:15/D:15/E:13/A:6 | 季節フック型×動画連打×後半CTA集中（情報過剰型敗者） | 0.20% | 17.6% | embedded (3072dim) / with_performance |
| 20260426_sirojam_hand | Siro jam | 手のシワ改善ハンドセラム（日本初×アンケートゲート型） | 2026-04-26 | 100 (text50/image50/video0) | B:26/E:22/C:19/A:11/D:10 | 問題再定義×日本初権威×アンケートゲートCTA型 | - | - | embedded (3072dim) / day100件伸び中 |

---

## status 凡例
- `raw`: 取得直後・スコアリング未
- `scoring中`: 20要素スコアリング作業中
- `scored, embedding待`: 20要素付与済・ベクトル未生成
- `embedded`: ベクトル生成済・検索可能
- `with_performance`: 成果データ紐付け済

## 追加方法
1. 記事URL取得 → `articles/<YYYYMMDD>_<brand>_<keyword>/blocks_raw.json` に保存
2. チャンク統合 + 20要素スコアリング → `chunks.json` 出力
3. `meta.json` 作成
4. このINDEXに1行追加
5. 後工程で embedding-2 生成 → status を `embedded` に更新
