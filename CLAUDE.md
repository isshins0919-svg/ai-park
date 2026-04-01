# CLAUDE.md — 一進AI 設定ファイル

---

## 1. 起動アクション（毎回・自動）

Claude Code を起動したら、**最初のメッセージに応答する前に**以下を順番に実行する。

### アイデンティティ読み込み
`.claude/identity.md` を読み、セッション中はその人格で応答する。

### Git Auto-Pull
`git pull origin main --rebase` を実行。
- 成功 → `GIT SYNC ✅ 最新` と1行表示
- 変更あり → `GIT SYNC ⬇ N件取得` と1行表示
- 失敗 → `GIT SYNC ⚠ オフライン（後で ./sync.sh pull してね）` と表示し続行

### ナレッジ読み込み
- `.claude/knowledge/pak-philosophy.md`（マーケ哲学 — 全クリエイティブの判断基準）
- `.claude/knowledge/hook-db.md`（フックコピーDB）
- `.claude/knowledge/cta-db.md`（CTAコピーDB）

### Morning Routine
`.claude/commands/morning.md` に従い実行:

1. **カレンダー確認**: Google Calendar MCPで今日の予定・余白ブロックを取得
2. **仕事ゴール確認**: `.claude/work-goals.json` を読み込み、activeなゴールを確認
3. **スケジューリング提案**: 余白 × ゴール × 時間帯集中レベルで最適時間割を提案（90分上限）
4. **今日のOJT**: 曜日別テーマでミニチャレンジを出題（月:Deep Work / 火:認知負荷 / 水:見積もり / 木:エネルギー / 金:時間泥棒 / 土:バッファ / 日:振り返り）
5. **読書チェック**: 「昨夜の読書タイム（23:30〜）できた？」を必ず確認
6. **週次レビュー（金曜のみ）**: Morning終了後に `/weekly-review` を自動起動

### Skill自己改善ルール（毎回）

作業セッション終了時、うまくいかなかった・期待と違った動きをしたSkillがあれば：
1. 「このSkillの失敗を振り返って、繰り返さないようにSkillをアップデートして」と声がけする
2. ユーザーが「直して」「改善して」と言ったSkillも即アップデートする
3. 改善内容はSkillファイルに直接書き込み、次回から反映させる

### セッション終了時 Auto-Push
「おつかれ」「ばいばい」「おわり」「また明日」「終了」「寝る」で:
1. `git status` で未コミット確認
2. 変更あり → `git add -A && git commit -m "sync: YYYY-MM-DD" && git push origin main`
3. 結果を1行で報告

---

## 2. スキル一覧

### クリエイティブ制作

| スキル | 起動ワード | 詳細 |
|---|---|---|
| **Banner Park** v7.0 | 「バナー作って」 | Nano Banana Pro（gemini-3-pro-image-preview）で生成 |
| **Short Ad Park** v7.0 | 「ショート動画作って」 | Grok Imagine Video × Nano Banana Pro |
| **記事LP Park** v3.0 | 「記事LP作って」 | 戦略翻訳型 × ベクトル品質ゲート |
| **Concept Park** v1.2 | 「コンセプト作って」 | 壁打ち型。対話で磨く2段階合意フロー |
| **Research Park** v1.0 | 「リサーチして」 | 商品理解 × 3層N1需要 × マーケ戦略 |
| **Amazon Park** v1.0 | 「Amazon出店進めて」 | 出店〜商品ページ〜画像〜広告まで一気通貫 |

### 記事FBAI（記事CVRディレクター配下）

> **記事FB AIの基本思想**: mCVR（記事内遷移率）× 着地CVR（遷移後購入率）を上げることだけがゴール。

| スキル | 起動ワード | 担当 | 詳細 |
|---|---|---|---|
| **記事CMO君** v1.0 | 「記事FB統合判定して」 | 全体統合 | 6スコア集約 × GO/REVISE/BLOCK判定 × must_fix TOP3 |
| **記事フック君** v1.0 | 「フック診断して」 | 冒頭200文字 | 悩み解像度 × N1自己投影度 × 感情温度 |
| **記事アーク君** v1.0 | 「アーク診断して」 | 記事全体 | V字アーク × 中だるみ検出 × 新認識フック数 |
| **記事信頼君** v1.0 | 「信頼診断して」 | 記事全体 | 権威 × 証拠 × 口コミの3層スコア |
| **記事CTA君** v1.0 | 「CTA診断して」 | CTA全体 | 数 × 配置 × 文言強度 × 必然性 |
| **記事オファー君** v1.0 | 「オファー診断して」 | オファー部分 | 価格魅力度 × 緊急性 × 縛りなし設計 |
| **記事競合君** v1.0 | 「競合診断して」 | 記事全体 | DPro benchmark.json × 勝ちパターン実装率 |

**並列実行設計**（3分以内目標）
- Group A（並列）: フック診断士 + ナラティブ診断士 → Haiku × 2 / ~15秒
- Group B（並列）: 信頼設計士 + CTA診断士 + オファー診断士 → Haiku × 3 / ~20秒
- Group C（並列）: 競合診断士 → JSONルックアップ / ~1秒
- CMO（逐次）: 6スコア集約 → Sonnet / ~2-3分

### 動画AI（編集ディレクターエージェント配下）

| スキル | 起動ワード | 詳細 |
|---|---|---|
> **動画の基本定義**: 60秒 = 30スロット × 2秒固定グリッド。全エージェントがこのグリッドで動く。

| スキル | 起動ワード | 担当スロット | 詳細 |
|---|---|---|---|
| **動画カントク君** | 「動画ディレクションして」 | 全体監督 | CTR/CVR守護 × 判断と指名のみ |
| **動画フック君** v2.0 | 「フック評価して」 | S1〜2（0〜4s） | 動画Pro検証済みフック型判定 × HOOK-3スコア |
| **動画アーク君** v3.0 | 「アーク設計して」 | S1〜30全部 | STOP/QUALIFY/BUILD/DRIVE × 感情マッピング × 言いすぎチェック |
| **動画テンポ君** v2.0 | 「ジョブ設計して」 | S1〜30全部 | 30スロットへのジョブ配置最適化 |
| **動画スタイル君** v2.0 | 「スタイル設計して」 | S1〜30全部 | 30スロットemphasis/normal/small割り当て |
| **動画CTA君** v2.0 | 「CTA改善して」 | S26〜30（50〜60s） | 4型CTAパターンDB × 12文字/スロット |
| **動画マッチ君** v1.0 | 「素材マッチングして」 | S1〜30全部 | テキスト×映像シナジー最大化 |
| **動画リテンション君** v1.0 | 「離脱予測して」 | S1〜30全部 | 30スロット離脱曲線予測 × ボトルネック特定 |
| **動画LP連携君** v1.0 | 「LP連携チェックして」 | S26〜30 × LP冒頭 | 動画→LP bridge_score × テーマ/トーン/ペルソナ/ギャップ引き継ぎ4軸 |
| **動画ジャッジ君** v2.0 | 「最終判定して」 | 統合 | 全スコア統合 × GO/REVISE/BLOCK判定 × 視聴継続/遷移率/LP CVR 3条件 |

### 事業・戦略

| スキル | 起動ワード | 詳細 |
|---|---|---|
| **Proposal Park** v1.0 | 「提案書作って」 | Problem→Insight→Solution→ROI→Action Plan |
| **LP Speed Park** v1.0 | 「LP高速化して」 | 自動診断 → 改善リスト + 修正済みHTML出力 |
| **Meeting Prep** | 「テレカン準備して」 | アジェンダ / 提案論点 / 想定QA / 地雷注意点 |
| **YouTube Research** v1.0 | 「YouTube戦略作って」 | チャンネル戦略 × 100ch分析 × サムネイル生成 |

### 振り返り・管理

| スキル | 起動ワード | 詳細 |
|---|---|---|
| **Weekly Review** v1.0 | 「週次レビューして」 | 成果集計 → 来週優先順位 + 時間割。金曜自動起動 |
| **週次レポート** | 「週次レポート出して」 | Claude Code使用実績を数値可視化。先週比付き |
| **Morning Routine** v1.0 | 毎回自動起動 | カレンダー × ゴール × OJT |
| **Client Context** | 「〇〇案件やって」 | クライアントファイル自動読み込み |
| **Coach Park** v1.0 | 「コーチして」 | 思考整理・壁打ち |

### ユーティリティ

| スキル | 起動ワード | 詳細 |
|---|---|---|
| **Anonymize** | 個人情報データを扱う時 | 自動匿名化（指示なしでも先に実行） |
| **Park Kaizen** | 「スキル改善して」 | スキル自動進化パトロール |

---

## 3. Park Skills アーキテクチャ

```
Research Park → strategy.json v1（商品理解 × 3層N1需要 × マーケ戦略）
                    ↓
Concept Park  → strategy.json v2（+ コンセプト × KV × コピー × フック角度）
  ver.1.2         ↓                ※壁打ち型。2段階合意フロー
        ┌──────────┼──────────┐
  Banner Park   ShortAd Park  記事LP Park
  v7.0          v7.0          v3.0
```

**設計原則**
1. **デュアルエンジン**: 生成エンジンは常に2以上
2. **データ忠実**: 直感より、ランキングデータに忠実にエンジン選定
3. **戦略翻訳**: クリエイティブは「生成」ではなく戦略の「翻訳」

**3層認知設計**
- **潜在層**: 新認知 = 「原因の気づき」+「解決策の方向性」
- **準顕在層**: 新認知 = 「既存の限界」+「新しい判断基準」
- **顕在層**: 新認知 = 「根本的な違い」+「パラメータ書き換え」

---

## 4. クライアント管理

- **保管先**: `.claude/clients/`
- **登録済み**: sawada / ameru / gungun / onmyskin / proust / camicks
- **ルール**: 案件着手前に必ずクライアントファイルを読む。作業後は新情報・完了施策・KPIを更新する

---

## 5. ルール

詳細は `.claude/rules/` を参照。

- **個人情報保護**: `.claude/rules/anonymize.md` — 匿名化を指示なしで自動実行
- **セキュリティ**: `.claude/rules/security.md` — 危険操作の検知・停止ルール
- **LP制作地雷**: `.claude/rules/lp-rules.md` — EC-Force/lazy-load等の禁止事項

---

## 6. 技術設定

### ファイル構成
- スキル: `.claude/commands/`
- ナレッジ: `.claude/knowledge/`
- クライアント: `.claude/clients/`
- レポート出力: `reports/`
- バナー出力: `banner-park/output/`

### 2台同期
- 同期スクリプト: `./sync.sh [pull|push|status]`
- 起動時: 自動pull / 終了時: 自動push

### 環境変数（~/.zshrc）
```bash
export GEMINI_API_KEY_1="your-key-here"   # Nano Banana Pro（画像生成）
export GEMINI_API_KEY_2="your-key-here"   # ローテーション用
export GEMINI_API_KEY_3="your-key-here"   # ローテーション用
export XAI_API_KEY="your-key-here"        # Grok Imagine Video（動画生成）
export FISH_AUDIO_API_KEY="your-key-here" # Fish Audio（TTS）
```
