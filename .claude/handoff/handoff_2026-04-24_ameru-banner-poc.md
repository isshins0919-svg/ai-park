# Handoff: 2026-04-24 → ameru バナーPOC（embedding-2 マルチモーダル）

> **次セッションの最優先ミッション**: ameru用バナー10本を embedding-2 マルチモーダル活用で生成するPOCを実行する。
> 設計は本セッションで確定済み。**次セッションは実行だけに集中**。

---

## ✅ 本セッション完了事項

### 1. embedding モデル 001 → 2 移行（5ファイル）
- `.claude/knowledge/vector-utils.md`
- `scripts/vector_store.py`
- `.claude/commands/amazon-captain.md`
- `.claude/commands/research-park.md`
- `.claude/commands/記事LP-park.md`
- 全箇所 `gemini-embedding-001` → `gemini-embedding-2-preview` 置換済み
- commit: `70f0186`

### 2. embedding-2 プレイブック新規作成
- `.claude/knowledge/embedding-2-playbook.md` — ユースケース判断マップ（TOP10活用場面、ロードマップPhase A-C）
- `INDEX.md` に「🧲 ベクトル活用」カテゴリ新設（vector-utils / ccdd-strategy / embedding-2-playbook の3点セット）

### 3. ameru バナーPOC 設計確定
（次セッションの実行内容）

---

## 🔍 重要発見: LP用 embedding-2 POC は別セッションで先行稼働中

### 既存ファイル（次セッションで流用可能）

| ファイル | 内容 |
|---|---|
| `reports/projects/ameru/embed_and_match.py` | **gemini-embedding-2-preview 実装サンプル**。API config: `task_type="RETRIEVAL_QUERY"`, `output_dimensionality=3072` |
| `reports/projects/ameru/refs/`（43枚） | ameru ブランド画像資産（ロゴ/公式キャラ/phase1画像/phase2画像/ヒーロー各種） |
| `reports/projects/ameru/matches.json` | LP 10スクリーン × refs 43枚の top-3 マッチング結果 |
| `reports/projects/ameru/ameru_lp_v4.html` | 最新LP v4 |
| `reports/projects/ameru/screens_v4/` | LPスクリーン画像 v4 |

### バナーPOCへの流用ポイント

- `embed_and_match.py` の embedding-2 呼び出し実装をそのまま使える
- refs/ の既存43枚を ameru ブランドベクトルとして活用可能
- cosine_sim 閾値感覚が既にある

---

## 🎯 次セッション実行計画: ameru バナーPOC

### 確定設計（本セッションで合意済み）

| # | 項目 | 決定 |
|---|---|---|
| ① | DProジャンル | 🧸 **推し活・キャラグッズ・ぬいぐるみ** |
| ② | 配信面 | Meta/Instagram → **スクエア 1:1** |
| ③ | 参考軸 | **デザイン寄り**（画像ベクトル主体、コピーはサブ） |
| ④ | 構成分析 | **C: 要素分解 + クラスタ + 勝ちパターン抽出** |
| ⑤ | ameru strategy | **Y: ameru.md + reports/projects/ameru/screens_v4 から抽出**（30分） |

### フロー（総工数 約3時間）

```
Phase 0.5: ameru strategy.json 抽出（30分）
  入力: .claude/clients/ameru.md + reports/projects/ameru/screens_v4/
  出力: banner-park/output/ameru/strategy.json
  必須項目: concept / N1 / layer / layer_demand / offer / ブランドガイド / 禁忌ルール

Phase 1: DPro 推し活系バナー10本選定（30分）
  ツール: DPro MCP（mcp__df6842ef-*** 系）
  フィルタ: 推し活/キャラグッズ/ぬい + スクエア1:1 + 静止画 + 実績上位
  出力: 20本候補 → 一進さん目視で10本確定

Phase 2: マルチモーダル embedding（20分）
  参考: reports/projects/ameru/embed_and_match.py 流用
  処理: 10本の画像 + コピー両方を embedding-2-preview でベクトル化
  出力: banner-park/output/ameru/reference/all_vectors.json

Phase 3: 構成分析 C（30分）★ 革命ポイント
  3.1: 画像ベクトルでクラスタリング（10本→2-3グループ、階層クラスタリング）
  3.2: Gemini Vision で各バナー要素分解
       - FVコピー（1行目の文言）
       - メインビジュアル（何が中心か）
       - 配色3色（カラーピッカー or Vision推定）
       - レイアウト（コピー位置/画像位置/CTA位置）
       - CTA（有無・文言）
  3.3: クラスタごと勝ちパターン抽出（共通要素のテキスト化）
  出力: banner-park/output/ameru/reference_analysis.md

Phase 4: ameru用バナー10本生成（60分）
  入力: strategy.json + reference_analysis.md
  処理:
    - 3クラスタに沿って10本割り振り（クラスタA:3 / B:3 / C:3 / ameruオリジナル:1）
    - Banner Park で生成 or 直接 Gemini Image で生成
    - ベクトル品質ゲート: 参考との差別化 + コンセプト一貫性
  出力: banner-park/output/ameru/banners/01.png ～ 10.png

Phase 5: 成果まとめ（15分）
  出力: banner-park/output/ameru/POC_report.md
```

---

## ⚠️ 絶対遵守ルール（ameru 禁忌）

**Phase 4 生成時のストッパー**:

1. **らぶいーず表記はひらがな絶対**
   - ✅ `らぶいーず`、`らぶいーず × ameru`、`#らぶいーず`
   - ❌ `Love is...`、`love is...`、`LOVE IS...`、`Love Eez`、`LOVE EEZ`
   - FV/タグ/マーキー/footer/title/alt 全てひらがな

2. **誕生月訴求NG**
   - ❌ 「すもっぴ誕生日11/7」「誕生月で祝う」「◯月スタートがおすすめ」

3. **5キャラの正式名称のみ使用**
   - ✅ すもっぴ / ぴょんちー / にゃぽ / うるる / ぱおぱお
   - ❌ ずもっぴ / さくら / そら / もり / ゆめ（ameru版別名は存在しない）

4. **商品ラインナップは 5回定期便 + 単品 のみ**
   - ❌ カップル2体セット・バレンタイン限定パック等の派生は存在しない

5. **時間依存コピーNG**（`.claude/rules/lp-copy.md`）
   - ❌ 「本日より」「今日から」「24時間限定」「いまだけ」
   - ✅ 「限定300セット」等の数量限定

6. **「買う」系ネガアンカーNG**
   - ❌ 「買うより編む」「買うのではなく作る」
   - ✅ 「自分の手で編む」等の肯定形

---

## 📚 次セッション起動時の読み込み推奨

1. `.claude/clients/ameru.md` — ameru 全体像・禁忌ルール・N1
2. `.claude/knowledge/embedding-2-playbook.md` — 活用判断マップ
3. `.claude/knowledge/vector-utils.md` — 共通コード
4. `.claude/rules/lp-copy.md` — コピー禁忌
5. `reports/projects/ameru/embed_and_match.py` — 先行実装（流用元）
6. 本ファイル — 実行計画

---

## 🚦 実行開始の合言葉

次セッションで一進さんが「**ameru バナーPOC始める**」と言ったら:

```
1. 上記6ファイルを読み込み（並列）
2. Phase 0.5 から順次実行
3. 各Phaseで一進さんに確認ゲート挟む
4. Phase 5 で成果物まとめて報告
```

---

## 💡 本セッションでの学び（次セッションに活かす）

- **embedding-2 はマルチモーダル**が真価。画像×テキスト両方ベクトル化すべし
- **001と2は別空間**。混在厳禁。閾値も再キャリブレ前提
- **LP用の実装が既に動いてる** → バナーPOCで流用すればゼロからじゃない
- **構成分析は C まで行かないと転用できる知見にならない**（embedding単体では「意味近い」止まり）
- **ameru の禁忌6項目**は Phase 4 のストッパーとして必須

---

## 🔗 関連ファイル

- `.claude/knowledge/embedding-2-playbook.md` — 活用判断マップ
- `.claude/knowledge/vector-utils.md` — 共通コード
- `.claude/knowledge/ccdd-strategy.md` — 全体方針
- `.claude/clients/ameru.md` — クライアント情報
- `.claude/rules/lp-copy.md` — コピー禁忌
- `.claude/rules/anonymize.md` — 個人情報保護
- `reports/projects/ameru/embed_and_match.py` — 先行実装（流用元）
- `reports/projects/ameru/refs/` — 43枚の ameru ブランド画像
- `reports/projects/ameru/matches.json` — LP用試行結果

---

**🏴‍☠️ Bon Voyage! 次セッションでバナーPOC完走を目指す。**
