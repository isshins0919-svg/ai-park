# AlphaGo判断原則（パク1.2.5輸入、思想版）

> 出典: `AIパクくん1.2.5/.claude/knowledge/skills/alphago-judgment-engine.md`
> 実装詳細: `reports/aipark_deep_dive_alphago.md`

---

## 最上位原則

> **Opus 4.6以降はAGI。AGIの力に最大レバレッジをかける。**
> Pythonのif文で判断するのは「AGIを電卓として使う」のと同じ。

AGIの本来の力は**推論**。因果推論・反実仮想・パターン認識・批判的思考。
全ての判断ポイントで問え:

**「Pythonで書けるか？ Opusに推論させるべきか？」**

---

## 判断の振り分け

| 対象 | 担当 | 理由 |
|---|---|---|
| データ集計・閾値判定 | Python | 速い、正確、確定的 |
| 因果推論（なぜ勝ったか / 負けたか） | Opus | 推論領域 |
| 仮説生成（次に何を試すか） | Opus | 創造的推論 |
| 批判的検証（この仮説は本当に正しいか） | Opus | 自己否定 |
| クロスプロダクト類推 | Opus | アナロジー推論 |

---

## フェーズ別武器選択（最重要）

**データ量に応じた武器を選べ。全部同時投入は過ち。**

| フェーズ | CV数 | 使う武器 | 使わない武器 |
|---|---|---|---|
| **Phase 1: 探索** | <10 | PAUSE判定 + 勝ち特定 + Slack通知 | UCB / ベイズ / Thompson（統計的に無意味） |
| **Phase 2: 検証** | 10-50 | + Opus推論（因果・反実仮想・自己否定） | ベイズ / Thompson（まだ薄い） |
| **Phase 3: 最適化** | 50+ | + UCB + ベイズCPA + Thompson Sampling | 全武器活用 |
| **Phase 4: 展開** | 安定 | + 多媒体 + 媒体間学習転移 | — |

**現象認識**: 「統計的に無意味なのに計算する」は **やらないより害が大きい**。数値が出て判断を歪める。

---

## VOYAGEでの実践

### 原則1: 判断の前に「これはPython? Opus?」を問う

- CRの良し悪し評価 → Opus（因果推論）
- 日本語OCRの合否 → Python（ffprobe / Vision API の出力）
- 競合との類似度判定 → Opus（意味理解）+ Python（cosine閾値）

### 原則2: 推論には必ずログを残す

```json
{
  "cr": "kiji-sawada-v3",
  "decision": "RELEASE",
  "reasoning": {
    "hook_score": 0.82,
    "trust_score": 0.76,
    "cta_score": 0.71,
    "composite_score": 0.76,
    "human_readable": "N1の課題認知→解決提示→権威性証明の流れが整合。CTA直前の納得感が強い"
  }
}
```

後から「judge_calibration」で正誤検証できる。

### 原則3: 負けCRの因果分解（losing_dna）

負けたCRの原因を構造化して記録:

- `hook_weak`: フックが弱い
- `n1_mismatch`: N1とのずれ
- `cta_unclear`: CTA不明確
- `trust_gap`: 信頼構築不足
- `concept_shallow`: コンセプト浅い
- `visual_competitor_similar`: ビジュアルが競合と酷似

VOYAGEでは `reports/losing_dna_{slug}.json` に蓄積するのが現実的。

### 原則4: フェーズを誤認しない

VOYAGE案件ごとに現在のフェーズを明記:

- sawada: Phase 3（CV50+、最適化段階）→ 全武器活用
- 新規案件: Phase 1（CV<10、探索段階）→ PAUSE判定のみ

`clients/{slug}.md` に `current_phase:` フィールドを追加する選択肢あり。

---

## VOYAGE独自の応用先

パクはMeta広告CR判断に特化。VOYAGEは以下への応用余地:

1. **Amazon商品選定**
   - UCB: 新規商品の探索ボーナス
   - ベイズ: 類似商品実績から初動売上予測

2. **SNS投稿タイミング最適化**
   - Thompson Sampling: 時間帯×曜日をスロットマシン化
   - CV出てる時間帯に予算シフト推奨

3. **記事LP ABテスト判定**
   - ベイズ事後推定: 少サンプルでのWIN/LOSE判定
   - 早期打ち切りの判断根拠化

4. **動画のシーン選定**
   - UCB: 未テストシーンパターンへの探索価値
   - 時間軸推論: CTR低下曲線から疲弊シーン特定

---

## 禁止事項

1. **Phase 1（CV<10）でベイズ推定を回す**（統計的無意味）
2. **全判断をPythonの if-else で書く**（AGIを電卓化）
3. **推論ログを残さない**（後から検証不能）
4. **同じ物差しで exploit / repair / explore を採点**（それぞれに最適な武器がある）
