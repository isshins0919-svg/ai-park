# CR運用4原則（パク1.2.5輸入）

> 出典: `AIパクくん1.2.5/.claude/agents/cmo-aipark.md`
> 目的: 日次PDCA設計の思想基盤

---

## 原則1: 毎日新CRを作る（センターピン）

**CRは花。咲いて枯れる。だから毎日植え続ける。**

- night-brain が毎晩1-2本生成 → 翌朝入稿 → 48hで学び → 次の生成に反映
- 「勝ちCRをスケールする」は **延命策**
- 本質は「**次の大当たりを見つけ続ける**」

### VOYAGEでの解釈

VOYAGE は広告代理案件が多く、クライアントごとに供給ペースが異なる。

- クライアント直営（sawada-co等）: デイリーPDCA可能 → 原則1を厳密適用
- 代理店案件: 週次PDCAが現実的 → 原則1を「週次で新CR」に緩和

いずれにせよ、「勝ちCRに満足して次を作らない」は禁止。

---

## 原則2: 予算は固定する

**予算はCRの力を増幅する装置。装置の出力を上げてもCRが同じなら崩れる。**

- 予算固定で変数を「CR」だけにする → 因果推論を純粋にする
- スケールしたい場合は**水平展開**（同じCR、新CPN、同じ低予算）で並列

### VOYAGEでの解釈

- 新CR投入時は予算を変えない（因果混乱を防ぐ）
- 勝ちCRを見つけたら、同じ予算・同じCR・新キャンペーンID で並列稼働
- 「予算上げれば伸びる」思考は捨てる

---

## 原則3: 勝ちCRは休ませて復活（補助）

**CRの力は不変。変わるのはオーディエンスとの関係性。**

- 疲弊PAUSE 14日 → 新CPN で復活テスト（低予算）
- 最大2回復活
- 3回目は引退

**これは補助。主力は常に新CR。**

### VOYAGEでの解釈

- 疲弊検知はVOYAGEのDPro benchmark比較で可能
- 14日休ませる運用ルールを導入
- 記事LPやSNSにも応用可能（記事は90日、SNSは30日など期間調整）

---

## 原則4: 学びを蓄積し、リフレクションループを閉じる（複利の源泉）

### 4層リフレクション

| Lv | 頻度 | 対象 | 責任 |
|---|---|---|---|
| Lv.1 | 日次 | CR実績 → 48h判定 | 運用AIパク（自動） |
| Lv.2 | Director毎 | CR品質→feedback RAG | 各Director |
| Lv.3 | 週次 | Agent/Skill 改善 | CMO |
| Lv.4 | 構造改善 | Agent定義 / 組織設計 | CEO |

### `cr-learnings-db.json` 構造

パクでは `parks/strategies/{slug}/cr-learnings-db.json` に48h判定のたびに自動記録:

```json
{
  "cr_id": "banner_v9.0_14_D",
  "concept": "D",
  "layer": "顕在層",
  "vector": {"v": [...], "c": [...], "x": [...]},
  "48h_result": {
    "ctr": 2.3,
    "cpa": 3200,
    "verdict": "WIN",
    "win_reason": "顕在層にC空間（コピー）の権威性訴求が刺さった"
  },
  "created_at": "2026-04-17"
}
```

---

## VOYAGEでの実装案

### Step 1: learnings-db の導入

各クライアント配下に `learnings-db.json` を作成:
```
clients/
  sawada/
    learnings-db.json   ← 新規
  ameru/
    learnings-db.json
  ...
```

### Step 2: 記録タイミング

- 新CR投入時 → `learnings-db` に仮レコード追加（verdict: pending）
- 48h / 7日 / 30日 のタイミングで verdict 更新（WIN/LOSE/HOLD）
- 疲弊PAUSE時 → verdict: fatigued

### Step 3: 次CR生成時に参照

- `/banner-park` / `/movie-kantoku` / `/kiji-cko` 起動時に learnings-db を読み込み
- 勝ちパターン近傍 × 負けパターン遠方で次の仮説を配置

### Step 4: 週次リフレクション

- `/weekly-review` に learnings-db 統計を組み込み
- 「今週のWINパターン」「今週のLOSEパターン」を自動集計

---

## 禁止事項

1. **1本のCRを延命させて次を作らない**
2. **予算を上げて勝ちCRを伸ばそうとする**（水平展開で）
3. **学びを記録しないまま次のCRを作る**
4. **疲弊CRを3回以上復活させる**（3回目は引退）
