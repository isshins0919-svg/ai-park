# AIパクくん 1.2.5 × 一進VOYAGE号 — 完全差分マップ

> 作成: 2026-04-18
> 対象: `~/Downloads/AIパクくん1.2.5/` vs `~/Desktop/一進VOYAGE号/`
> 目的: 輸入可否・統合ポイント・既存優位性の精密マッピング

---

## 0. エグゼクティブサマリー

| 軸 | VOYAGE号の状態 | パク1.2.5の状態 | 結論 |
|---|---|---|---|
| **哲学基盤** | pak-philosophy.md 357行（独自深化あり） | CLAUDE.md 316行 + pak-philosophy 94行 | **補完統合**（V本体を尊重しつつパクの「判断階層」を追加） |
| **組織アーキ** | flat 29 agents × 44 skills | CEO→CMO→4部長→7共通Agent 階層 | **Director層をVOYAGE kiji-cko型で拡張** |
| **中央ハブ** | clients/ 10社（フリーフォーマットMD） | strategy.json スキーマ v3.0 | **段階移行**（clients→strategy.json化） |
| **ベクトル基盤** | vector-utils.md 設計のみ、実装は小規模 | vector_intelligence.py + 3空間Embedding 2稼働 | **完全輸入可**（CCDD Phase 1-4の完成品） |
| **判断エンジン** | 直感ベース + DPro benchmark.json 参照 | AlphaGo v4.0（UCB+Bayesian+期待値+Thompson） | **輸入推奨**（運用スキル用） |
| **OODAループ** | morning.md（AIニュース）+ Slack bot常駐 | night-brain + morning-check（データ駆動） | **並行運用→段階統合** |
| **リフレクション** | /nice-dive + /park-kaizen 手動 | ceo-reflection 週次自動 + reflection-queue | **輸入価値高** |
| **実戦資産** | 10クライアント運用中、DPro benchmark蓄積 | サンプル商材のみ | **VOYAGE優位** |

---

## 1. ディレクトリ構造対比

### パク 1.2.5

```
ai-park-cmo-1.2.5/
├── CLAUDE.md (316行)
├── .claude/
│   ├── agents/          ← 38体（4部長 + 34専門Agent）
│   ├── commands/        ← 37コマンド（スキル）
│   ├── knowledge/
│   │   ├── pak-philosophy.md
│   │   ├── goals.md
│   │   ├── growth/      ← kaizen-memory, pak-insight, session-learnings, taste 等
│   │   ├── reference/   ← gemini-models, meta-ads-playbook, squad-beyond, etc
│   │   ├── skills/      ← 50+ DNA/DB/ルール
│   │   └── lp-parts-db/
│   ├── rules/           ← 8ルール（creative-output, execution-model, etc）
│   ├── routines/        ← session-start, session-end
│   ├── scripts/         ← 23 Python（embedding_utils, dpro_rag, orchestrator_pipeline）
│   ├── settings.json    ← 詳細Hooks + 外部送信ブロック
│   └── launch.json
├── parks/
│   ├── scripts/         ← 70+ Python（vector_intelligence, alphago, meta_deploy, etc）
│   ├── config/          ← agent-contracts, circuit-breakers, defaults
│   ├── strategies/      ← strategy-schema.json + sample-beauty/ + squad-beyond/
│   ├── knowledge/       ← genre / global / patterns
│   ├── banner/ article-lp/ shortad/
├── tools/               ← 8 Python + bootstrap shell
├── docs/                ← 5ガイドMD
├── requirements-python312.txt
└── .mcp.json            ← DPro MCP接続テンプレ
```

### VOYAGE号 現状

```
一進VOYAGE号/
├── CLAUDE.md (101行)
├── .claude/
│   ├── agents/          ← 29体（crew中心。gate-* / kiji-* / movie-* / sns-*）
│   ├── commands/        ← 44コマンド（kiji-cko, movie-kantoku, pak-sensei 等）
│   ├── knowledge/       ← 26ファイル（pak-philosophy 357行含む独自深化）
│   ├── rules/           ← anonymize, security, lp-rules
│   ├── clients/         ← 10社（フリーフォーマット .md）
│   └── scripts/         ← 17 Python（slack bots常駐、dpro_benchmark等）
├── banner-park/
├── shortad-park/
├── 記事LP-park/
├── video-ai/
├── amazon-park/ (?)    ← amazon-captain.md からの派生
├── lp-optimize/
├── rough-cut/
├── textbook/
├── research-park/
├── article-banner-maker/
├── docs/
├── reports/
└── scripts/             ← slack_dpro_bot 等
```

---

## 2. Agent/Skill 精密マッピング

### VOYAGEが既に持っている（パク版より深い or 同等）

| VOYAGE | パク相当 | 優劣/備考 |
|---|---|---|
| `kiji-cko` (カントクパターン) | `director-article-lp-01-aipark` | **VOYAGE優位** — v3.0の「診断→治療→テスト設計」一気通貫はパクより具体化 |
| `pak-sensei` | なし（パクには「コンセプト AIパク」で類似機能） | **VOYAGE独自** — N1/Only1/コンセプト仮説設計の哲学専門家 |
| `gate-*`系9体（marketing/n1/hook/visual/legal/brand/typography/image-prompt/quality） | `cr-self-refiner-aipark` + 部長内部のGemini検品 | **VOYAGE優位** — 評価軸が細分化されており専門性が高い |
| `movie-kantoku` | `director-video-aipark` | 近似 — パクの部長の方がKPI記録が厳密 |
| `kiji-hook/trust/cta/offer/arc/compass` | `article-lp-writer-aipark` 内の自己検査 | **VOYAGE独自** — 5軸並列スコアリングは独自価値 |
| `sns-*` 5体（script/edit/retake/post/analytics） | なし（パクにSNS運用系なし） | **VOYAGE独自** |
| `amazon-captain` + `amazon-park` | なし | **VOYAGE独自** |
| `morning.md`（AIニュース） | `morning-check`（OODA答え合わせ） | 別機能。並存可 |
| `dpro_benchmark.json`（運用中） | 同等（configとして） | 同等 |
| Slack常駐bot（dpro/feedback）動作中 | 配布版では無効化 | **VOYAGE優位** |
| client登録 10社 | サンプル商材のみ | **VOYAGE優位** — 実戦データ |

### VOYAGEにない（パクから輸入候補）

#### 【S級】本質的に欠けている（CCDD Strategy Phase 1-4 の完成品）

| パク | 機能 | 輸入優先度 |
|---|---|---|
| `vector_intelligence.py` | V/C/X 3空間Embedding 2 + harmony/stickiness計算 | **★★★** |
| `embedding_utils.py` + `knowledge_rag.py` | Gemini Embedding 2（3072D）基盤 + ハイブリッド検索 | **★★★** |
| `asset_embedder.py` | 素材セマンティック検索 | **★★★** |
| `dpro_rag.py` + `dpro_rag_analyzer.py` | DPro MCP連携 + ランキング | **★★★** |
| `reflection_trigger.py` + `reflection_tracker.py` | 自動リフレクション起動 | **★★** |
| `event_store.py` + `materialize_views.py` | イベントソーシング + 派生ビュー自動生成 | **★★** |
| `validate_handoff.py` + `agent-contracts.json` | Agent間契約検証 | **★★★** |
| `circuit_breaker.py` + `circuit-breakers.json` | サーキットブレーカー | **★★★** |
| `verify_output_substance.py` | ファイル実在検証（Stage 0） | **★★** |
| `meta_cv_extract.py` | Meta CV抽出正規実装 | **★★** |
| `runtime_paths.py` | Runtime↔legacy 二重読み | **★** |

#### 【A級】ナレッジDB（即座に価値を生む）

| パクの知識ファイル | VOYAGEでの相当 | 輸入価値 |
|---|---|---|
| `alphago-judgment-engine.md` | なし | **★★★** 思想のみでも | 
| `creative-philosophy-templates.md` | なし | ★★ |
| `hook-db.md`（2層構造 骨格DNA + バリエーション） | `hook-db.md` あり（構造異なる） | 差分マージ |
| `cta-db.md`（パク構造） | `cta-db.md` あり | 差分マージ |
| `banner-dna-templates.md` | `banner-dna-templates.md` あり | 差分マージ |
| `shortad-dna.md` + `shortad-dna-templates.md` | `shortad-dna-templates.md` あり | 差分マージ |
| `shortad-dpro-winning-patterns.md` | なし | ★★ |
| `article-lp-fv-patterns.md` + `fv-design-rules.md` | `fv-detection-revolution.md` あり | 補完 |
| `article-lp-research-framework.md` | なし | ★★ |
| `article-lp-quality-gates.md` | なし | ★★ |
| `article-lp-writing-techniques.md` | `sawada-article-lp-philosophy.md` あり | 補完 |
| `article-lp-gimmick-engine.md` + `gimmick-mapping.md` + `gimmick-prompts.md` | なし | ★★ |
| `trust-badge-rules.md` | なし | ★★ |
| `philosophy-constraints.md` | なし | **★★★** 哲学の計算可能化 |
| `meta-ads-playbook.md` + `meta-ops-2026-best-practices.md` | なし | ★★ |
| `squad-beyond-complete-guide.md` | kiji-tester で類似 | 補完 |
| `agent-factory-guide.md` | なし | ★★ |

#### 【B級】運用スキル（Meta API等の本番連携が必要）

| パク | 注記 |
|---|---|
| `/night-brain` | Meta API連携必須。VOYAGE側のSlack botと統合で活きる |
| `/morning-check` | 上記とセット |
| `/meta-ops-park` | Meta Ads Manager API必須 |
| `/strategy-autopilot-orchestrator` | 上記の前提 |
| `/ceo-reflection` | 週次CMO改善（輸入価値★★★） |
| `/cmo-weekly-review` | 上記の補助 |

---

## 3. ナレッジファイル 精密差分

### 3-1. `pak-philosophy.md` の統合設計

**VOYAGE版の独自要素**（パク版にない）:
- 「今この瞬間、この美しき世界を愛し、愛されること」という **目的**宣言
- 「AIにもリスペクトを」
- 「質問には提案をセット」（マッキンゼー式）
- 「超一流であろう — セルフブラッシュアップ」
- 「パクの分身であろう — 共創の行動規範6つ」
- 「3つの魂」= **CR構成要素視点**（KV魂・キラーコピー魂・仮説魂）
- ポメ太DIVE哲学（記事LP用9原則）

**パク版の独自要素**（VOYAGE版にない）:
- 「3つの魂」= **判断基準階層**（愛→偉大→可能）
- 「階層構造で評価し、下位が不合格なら上位は評価しない」ルール
- 「愛が土台。偉大がフィルター。可能が拡張。この順序を崩すな」

**統合方針**: VOYAGE版を本体とし、パク版の「判断階層」を追加セクション化。
両者の「3つの魂」は**視点が違うだけ**で矛盾しない:
- CR構成視点 = 「何を作るか」の3要素（KV/コピー/仮説）
- 判断階層視点 = 「どう評価するか」の3段（愛/偉大/可能）

### 3-2. hook-db.md の差分

| 項目 | VOYAGE | パク |
|---|---|---|
| 構造 | カテゴリ単位のエントリDB | 骨格DNA + バリエーション 2層 |
| 自動進化ゾーン | なし | `<!-- AUTO-EVOLUTION-ZONE -->` コメントマーカー |
| コスト実績統合 | 設計なし | `cost_diff -` を各バリエーションに記録 |

→ **VOYAGEの内容をパクの2層構造に再構成**すると「AIが自動でバリエーション追加する器」になる。

### 3-3. CLAUDE.md の差分

| パクの要素 | VOYAGE本体への統合可否 |
|---|---|
| 本質・AGI解放・意図汲み取り の3指令 | **統合推奨** |
| Vector-First Learning 憲法 | **統合推奨** |
| Runtime パス解決 | VOYAGEは不要（repo完結派） |
| Gate-L1/L2/L3 品質ゲート | **統合推奨**（概念として） |
| サーキットブレーカー概念 | **統合推奨**（実装は後） |
| degraded mode 報告義務 | **統合推奨** |
| CMO実務禁止原則 | **統合推奨**（VOYAGEのkiji-cko型を裏付け） |
| エージェント要件すり合わせ5本質問 | **統合推奨** |
| 既存スクリプト利用義務 | **統合推奨** |

---

## 4. 運用基盤の対比

### 4-1. Hooks（`.claude/settings.json`）

**VOYAGE現状**（推定）: limited hooks
**パク1.2.5**:
- PreToolUse Edit → `immutable_guard.py` で保護ファイルチェック
- PreToolUse Slack/Chatwork/Gmail/X送信 → **全BLOCK**（外部送信禁止）
- StopFailure rate_limit/auth/billing → エラー別メッセージ
- PostCompact → 哲学再注入（pak-philosophy.md head-103行を再表示）

**輸入推奨**: PreToolUseの外部送信ブロック + PostCompactの哲学再注入。immutable_guardは独自実装でOK。

### 4-2. Python Runtime

**VOYAGE**: `.claude/scripts/requirements.txt` に最小限
**パク**: `tools/bootstrap_python_runtime.sh` + `requirements-python312.txt` で統合管理

**輸入推奨**: Python 3.12+ への統一（VOYAGEの video-ai 等と整合確認必要）

### 4-3. MCP接続

**VOYAGE**: DPro MCP 既に接続、複数クライアント運用
**パク**: `.mcp.json` はプレースホルダのみ

→ **VOYAGE優位**。パクの配布版を輸入する際は .mcp.json を上書きしない。

---

## 5. データスキーマ対比

### 5-1. strategy.json vs clients/*.md

**VOYAGE clients/sawada.md（例）**:
- フリーフォーマットMarkdown
- 商材情報・KPI・過去CR履歴を手書き
- `last_updated` を14日超チェック（CLAUDE.mdに警告ルールあり）

**パク strategy.json v3.0**:
- JSON Schema厳格（productIntel / n1SelectionFramework / primaryN1 / layers / concept / brandGuard / formatStrategy を required）
- V1(baseline) → V5(learning_contract) の成熟度レベル
- `hookVectors[].performance` / `concept.hypotheses[].performance` で実績紐付け
- `rewardSchema` で最適化ゴール・閾値・ガードレール定義

**移行戦略**:
```
Phase 1: VOYAGE clients/ を読んで strategy.json を自動生成する変換スクリプト
Phase 2: 新規案件は strategy.json ベース
Phase 3: 既存10社を順次移行（sawada/ameru から優先）
Phase 4: clients/*.md は参考資料として残す（history用）
```

### 5-2. イベント記録

**VOYAGE**: ログは scripts/*.log（非構造化）
**パク**: `event-store.jsonl` + `execution-tracker.jsonl` + `transaction-log.jsonl` の3層

**輸入価値**: Agent lifecycle（start/complete/error/cb_skip）をJSONLで追跡できると、週次リフレクションで機械分析可能になる。

---

## 6. 哲学レベルの核差分

### VOYAGE「3つの魂」（CR構成要素視点）

```
魂1: キービジュアルそのもの — 広告枠を埋める画像ではなく、作品
魂2: キラーキャッチコピー — 説明文ではなく、1行で買わせる
魂3: 別の仮説 — 量ではなく仮説の数
```

### パク「3つの魂」（判断階層視点）

```
愛（土台）    → N1の感情に寄り添う / 相手を否定しない / 恐怖→希望の道
  ↓ PASS
偉大（フィルター）→ 時間耐久性 / コンセプト浸透率 / 非コモディティ
  ↓ PASS
可能（拡張）  → 未探索の可能性 / AGI活用度 / パターン超越
```

**統合の正解**: 2つの「3つの魂」は **制作時** と **評価時** で使い分ける
- 制作: VOYAGE「KV/コピー/仮説」を設計軸に
- 評価: パク「愛→偉大→可能」を判定軸に

これを知識として明文化すれば、VOYAGEの既存スキルと自然に統合できる。

---

## 7. 優位性マトリクス

```
                   VOYAGEが勝つ                パクが勝つ
                        │                        │
  制作品質  ├────────────┤         │
  組織骨格                              ├────────────┤
  ベクトル基盤                              ├────────────┤
  判断エンジン                           ├────────────┤
  実戦データ  ├────────────┤
  SNS運用    ├────────────┤
  Amazon運用  ├────────────┤
  Slack自動化 ├────────────┤
  細分化クルー├────────────┤
```

**結論**: VOYAGEは **制作品質 × 運用実績 × 専門性** で勝ち、パクは **基盤技術 × 組織アーキ × 学習ループ** で勝つ。補完関係。

---

## 8. 採択ロードマップ（5フェーズ）

### Phase A: 哲学・ナレッジ輸入（1セッション、破壊ゼロ）

**目標**: CLAUDE.mdとpak-philosophy.mdにパクの判断階層を統合

**実行**:
- 新規作成: `.claude/knowledge/aipark-imports/` ディレクトリ
  - `three-souls-judgment-hierarchy.md`（愛→偉大→可能）
  - `vector-first-constitution.md`
  - `alphago-judgment-principles.md`（思想のみ）
  - `cr-pdca-philosophy.md`（CR運用4原則）
  - `agent-requirements-5-questions.md`（エージェント要件すり合わせ5本質問）
  - `philosophy-constraints.md`
  - `degraded-mode-reporting.md`
- CLAUDE.md マージ提案を `reports/aipark_claude_md_merge_proposal.md` に作成（自動適用はしない）

### Phase B: DNAテンプレート差分輸入（2セッション）

- hook-db.md を2層構造（骨格DNA + バリエーション）に再構成
- cta-db.md 同上
- banner-dna-templates.md 差分マージ
- shortad-dna-templates.md 差分マージ + `shortad-dpro-winning-patterns.md` 新規輸入
- article-lp系フレームワーク4本輸入（research-framework, quality-gates, writing-techniques, gimmick-engine）

### Phase C: strategy.json スキーマ導入（3-5セッション）

- `parks/strategies/strategy-schema.json` をVOYAGEに配置
- `scripts/client_to_strategy.py` で clients/*.md → strategy.json 変換
- sawada / ameru を先行移行（実戦データで検証）
- Park Skills を strategy.json 読み込みに対応（後方互換維持）

### Phase D: Director層の再編（5+セッション）

- VOYAGE の `kiji-cko` を `director-kiji-aipark` 相当に拡張
- `director-banner-voyage` 新設（banner-park を束ねる）
- `director-movie-voyage` 新設（movie-kantoku を束ねる）
- 4部長体制: kiji-cko / director-banner / director-movie / director-amazon（Amazon Park用）
- agent-contracts.json 相当の契約定義

### Phase E: Vector-First 基盤（10+セッション、本命）

- `scripts/embedding_utils.py` 輸入（Gemini Embedding 2対応）
- `scripts/knowledge_rag.py` 輸入 → VOYAGE knowledge/ 全ファイルをベクトル化
- `scripts/vector_intelligence.py` 輸入 → V/C/X 3空間分析を各部長に統合
- `scripts/reflection_trigger.py` 輸入 → PDCAループ閉じる
- ChromaDB ローカル永続化（CCDD Strategy Phase 2 の完全実現）
- DPro benchmark.json × vector score の統合

### Phase F: OODA + Reflection Lv.4（本番運用）

- night-brain / morning-check を VOYAGE 既存Slack botと統合
- ceo-reflection-aipark を月曜10:00 cron
- reflection-queue.json + event-store.jsonl 運用

---

## 9. 注意点・地雷

### 9-1. 輸入時の既知問題

- **パク Runtime ディレクトリ依存** (`~/Documents/AIパク-runtime/`) → VOYAGEは repo 完結派。Runtime層は採用しない、または別設計
- **パク settings.json の Bash 権限が広い**（`curl *`, `pip install *`）→ VOYAGE `rules/security.md` と衝突。絞ってから適用
- **`immutable_guard.py` hooks** → ファイル保護は良いが、VOYAGE側の編集ワークフローと干渉する可能性。動作確認必要
- **`tools/py` ヘルパー** → パスとPython環境の前提が異なる。bootstrap_python_runtime.sh の移植が必要

### 9-2. スキル名の衝突

VOYAGE と パクで同名かつ挙動が異なるスキル:

| 名前 | VOYAGE版 | パク版 |
|---|---|---|
| `/banner-park` | v7.0（独自実装） | v9.0（Gemini一体型生成 + 9項目検品） |
| `/concept-park` | v2.1（壁打ち型） | v2.1（同） |
| `/research-park` | 独自 | DPro + product-research統合 |
| `/morning` | morning.md（AIニュース） | morning-check.md（OODA答え合わせ） |
| `/handoff` | 独自 | 類似 |

→ **命名空間分離**を推奨: パク版は `/aipark:banner-park` のように prefix化して共存

### 9-3. クライアント情報の扱い

VOYAGE clients/ は個人名・会社名を含む。パクの strategy.json は productSlug（匿名化）前提。
→ 移行時は `.claude/rules/anonymize.md` に従う。strategy.json は商材コード基軸で設計する。

---

## 10. 最終判定表

| 輸入対象 | 優先度 | リスク | 推奨タイミング |
|---|---|---|---|
| 哲学・ナレッジMD | ★★★ | 低 | 即時（Phase A） |
| hook-db / cta-db 2層化 | ★★ | 低 | Phase B |
| strategy-schema.json | ★★★ | 中 | Phase C |
| Director層の設計思想 | ★★★ | 中 | Phase D |
| vector_intelligence.py | ★★★ | 中 | Phase E |
| AlphaGo エンジン | ★★ | 中 | Phase E（運用系整備後） |
| night-brain / morning-check | ★★ | 高 | Phase F（Meta API統合後） |
| ceo-reflection | ★★★ | 低 | Phase F |
| Runtime dir 設計 | ★ | 高 | 採用しない推奨 |
| immutable_guard hooks | ★ | 中 | 独自実装推奨 |

---

## 11. VOYAGE優位性の保存ルール

輸入時に **捨ててはいけない** VOYAGE独自資産:

1. `kiji-cko.md` のカントクパターン（診断→治療→テスト設計一気通貫）
2. `pak-sensei.md` の哲学壁打ち機能
3. `gate-*` 9体の細分化専門性
4. `sns-*` 5体のSNS運用パイプライン
5. `amazon-captain` + `amazon-park`
6. 10クライアントの実戦データ
7. Slack常駐bot（dpro / feedback）
8. `pak-philosophy.md` の「目的」「パクの分身6規範」「ポメ太DIVE9原則」
9. `ccdd-strategy.md` の構想文書（パク輸入で実装が追いつく）

---

*このレポートはVOYAGE号の次のエボリューション方針書として機能する。Phase A の実行から始めて、段階的にパク1.2.5の長所を取り込みつつ、VOYAGE独自の優位性を守る。*
