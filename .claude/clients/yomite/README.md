# ⚓ ヨミテ デイリーニュース システム

ヨミテ系5商品（on:myskin / プルーストクリーム2 / 伸長ぐんぐん習慣 / RKL / アポバスターF）の日次DProレポートを Slack `#yomite_ai-agents` に毎朝自動投稿する仕組み。

---

## 🚨 絶対ルール（忘れると誤読バグる）

### ① to_date は「前日」を必ず指定
朝8時投稿時点で当日データは5〜10%しか消化されてない。ノイズ混入を避けるため `to_date=前日, interval=2` で「前々日〜前日」の確定2日分だけを扱う。

### ② グラフのX軸は「観測日」ラベル（発行日ではない）
| 概念 | 説明 |
|---|---|
| **発行日** | history JSONの `date` フィールド（朝投稿する日） |
| **観測日** | APIの `to_date`（データの最新地点＝前日） |
| **X軸ラベル** | 必ず**観測日**を使う ← 発行日を使うと「今日に何が起きた？」と誤読される |

例: history/2026-04-21.json は to_date_api=2026-04-20 → グラフ上は「4/20」ラベルで描画。
過去にこのラベルミスで「4/20の点が当日データ」と誤読されたバグあり。二度と繰り返さない。

---

## 🧭 構成

```
.claude/clients/yomite/
├── daily_news_config.json   ← 4商品・市場定義・象限ルール
├── history/                 ← 日次スナップショット（時系列分析の土台）
│   ├── 2026-04-17.json
│   ├── 2026-04-18.json
│   └── ...
├── charts/                  ← VOYAGE航路図PNG（毎朝自動生成）
│   ├── 2026-04-20_voyage_onmyskin.png
│   ├── 2026-04-20_voyage_proust.png
│   ├── 2026-04-20_voyage_gungun.png
│   └── 2026-04-20_voyage_rkl.png
├── scripts/
│   └── generate_charts.py   ← matplotlib VOYAGE航路図ジェネレーター
└── README.md                ← このファイル

~/.claude/scheduled-tasks/dpro-yomite-daily-news/
└── SKILL.md                 ← 毎朝 8:07 に実行されるスキル定義
```

---

## 🎯 毎朝の流れ

1. **8:07 頃**: スケジュールタスク `dpro-daily-news-remote` が自動実行
2. DPro MCP で 4商品×自社/市場データ取得（interval=2）
3. 象限判定（🌊追い風 / 🚀独走 / ⚠️波に乗れてない / 📉市場縮小）
4. `history/YYYY-MM-DD.json` に保存
5. `generate_charts.py` 実行 → 4枚のVOYAGE航路図PNG生成
6. Slack メイン投稿（チャンネル） + スレッド4本（各商品）
7. メイン投稿末尾にチャート画像の**ローカル絶対パス**が記載される

## 📎 画像の手動添付（日々のオペレーション）

Slackに画像を自動アップロードする手段がMCPにないため、以下の運用にしている:

1. 朝のSlack通知で生成画像のパスを確認
2. Finder で `.claude/clients/yomite/charts/` を開く
3. 4枚のPNGをSlackのメイン投稿にドラッグ&ドロップして添付
4. 追加コメントでハイライトを一言

将来的に Slack `files.upload` API 経由で自動化する場合は Phase 2.5 として検討。

---

## 🎨 VOYAGE航路図のデザイン要素

- **配色**: 深海ネイビー×ゴールド（VOYAGE号のブランドカラー）
- **ヘッダー**: 錨マーク×コンパス×タイトル
- **折れ線**: 自社（太線＋3層グロー） ／ 競合TOP2（点線）
- **ステータスバー**: 象限バッジ ／ 今日のシェア特大 ／ 自社vs市場金額
- **フッター**: 「一進 VOYAGE 号 ～ Navigate the tides ～」

商品カラー:
| 商品 | カラー |
|---|---|
| on:myskin | #4FC3F7 (水色) |
| プルーストクリーム2 | #BA68C8 (紫) |
| 伸長ぐんぐん習慣 | #66BB6A (緑) |
| RKL | #FFA726 (オレンジ) |

---

## 🛠️ 手動でチャートだけ再生成したい場合

```bash
python3 /Users/ca01224/Desktop/一進VOYAGE号/.claude/clients/yomite/scripts/generate_charts.py
```

履歴JSONが最低2日分あればチャート生成可能。日が経つほど推移ラインが濃くなる。

---

## ⚙️ 市場定義のカスタマイズ

`daily_news_config.json` の `products[].market` を編集:

- `type: "genre"` → 単純にジャンル指定
- `type: "hybrid_genre_keyword"` → ジャンル × キーワード × 除外語で疑似ジャンル化

カスタマイズ例（RKLの除外語追加）:
```json
"exclude_keywords": ["キャンペーン","求人","腰","デオドラント",... "新たな除外語"]
```

---

## 📈 Phase ロードマップ

| Phase | 内容 | 状態 |
|---|---|---|
| 1 | 4商品×シェア×象限 数値ニュース | ✅ 完了 |
| 2 | 履歴永続化 + VOYAGE航路図チャート | ✅ 完了 |
| 2.5 | Slack files.upload で画像自動添付 | 📋 検討中 |
| 3 | 新規競合参入アラート／自社失速アラート／月曜MVP | 📋 検討中 |

---

## 🚨 トラブルシュート

**Q. 画像が生成されない**
→ history/ に2日分以上のJSONがあるか確認。無ければ手動で過去日の取得を実行。

**Q. Slack投稿が `invalid_blocks` エラー**
→ URLを `<url>` や markdown link 記法で囲むとSlack MCPがエラーを返す。生URLで投稿する。

**Q. シェア％が0.00%になる**
→ 市場定義が広すぎるかも（ノイズ商品が分母を膨らませてる）。`exclude_keywords` を追加して絞る。

**Q. product_id が 複数ある商品の集計漏れ**
→ config の `product_id_aliases` に追記。自社コスト合算時にループして集計する。
