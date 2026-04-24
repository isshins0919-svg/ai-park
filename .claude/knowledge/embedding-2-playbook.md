# embedding-2 活用プレイブック

> **目的**: VOYAGE号における embedding-2 の「いつ・何に使うか」を判断できる型。
> **作成**: 2026-04-24 / **対象モデル**: `gemini-embedding-2-preview`
> **位置づけ**: 退職後も引き継ぎ先が参照可能な形式知。

---

## 🧭 このファイルの立ち位置

ベクトル関連ナレッジ3点セットの中の「判断マップ」担当。

| ファイル | 役割 |
|---|---|
| [ccdd-strategy.md](ccdd-strategy.md) | **なぜやるか**（全体方針・Phase 1-4） |
| **embedding-2-playbook.md（これ）** | **いつ何に使うか**（ユースケース判断マップ） |
| [vector-utils.md](vector-utils.md) | **どう書くか**（共通コード） |

---

## 📐 embedding-2 の特性

| 項目 | 値 |
|---|---|
| モデル名 | `gemini-embedding-2-preview` |
| 次元数 | **3072**（推奨）/ 1536 / 768（可変） |
| 入力コンテクスト | **8,192トークン** |
| モーダル | **テキスト / 画像 / 動画 / 音声 / ドキュメント**（同一空間） |
| 言語 | 100+言語 |
| GA | 2026年4月 |
| 旧 `gemini-embedding-001` との互換 | ❌ ベクトル空間が別。混在NG |

### 🔑 001との決定的な差

**マルチモーダル**。テキストも画像も動画も音声も**同じ空間**にマッピングできる。
これが embedding-2 の革命ポイント。001時代は「テキスト同士しか比較できない」という制約があった。

---

## 🎯 使うべき／使うべきでない判断

### ✅ 使うべき4条件（いずれか該当）

1. **意味ベースの検索が必要** — キーワード/grep で引けない（同義語・表現ゆれ・文脈依存）
2. **大量データの横断** — 9クライアント × 数年の蓄積から「似た何か」を引きたい
3. **モーダル間の比較** — テキスト × 画像、テキスト × 動画等の橋渡し
4. **類似度スコアでの順位付け** — 「どれが一番近いか」を数値で出したい

### ❌ 使うべきでない場面

- **キーワードで引ける** → grep で終わるなら使うな
- **1ファイル内で完結** → 横断要素なし
- **構造化データの計算** → SQL / pandas / JSON で
- **リアルタイム応答必須でコスト許容不可** → API呼び出しは遅延あり

**原則**: 「物理量で解ける問題にAIを使うな」（feedback_tool_selection.md）。embedding も同じ。**必要な時だけ使う**。

---

## 🏆 VOYAGE号での活用TOP10

### 🥇 優先度 S（即効性 × 効果 ★★★★★）

#### 1. マルチモーダル画像検索（Banner/LP/ShortAd の革命）

- **何をする**: コピーテキスト と 画像 を **同じベクトル空間** で比較
- **使い道**:
  - 過去の勝ちバナー画像 × 新コピー の意味的マッチング
  - 競合LP画像との **視覚的差別化** チェック
  - 「このブランドの世界観に合う画像」の自動抽出
- **統合先**: Banner Park / 記事LP Park / Short Ad Park / Amazon Park
- **実装コスト**: 中（画像embedding API呼び出し量に注意）
- **embedding-2でしか実現不可** の革命的ユースケース

#### 2. クライアント資料の意味検索（毎日使う）

- **何をする**: `~/Desktop/_clients/<client>/` 配下の全資料をベクトル化
- **使い道**:
  - 「sawada-coの承継の話」で関連資料即時抽出
  - PDF/PPT/Word をドキュメント単位でベクトル化（embedding-2 のドキュメント対応）
  - 起動時「おはよう」パトロールで差分検出 → 自動ベクトル化
- **統合先**: 全スキル（client-context から自動呼び出し）
- **実装コスト**: 低（1案件500ファイルでもAPIコスト1万円以下の想定）
- **毎日効くので累積効果が異次元**

---

### 🥈 優先度 A（効果 ★★★★）

#### 3. N1インタビュー横断分析

- **何をする**: 全クライアントのN1発言をベクトル化 → クラスタリング
- **使い道**:
  - 「承認欲求系」「贈答系」「自分ケア系」のクラスタ発見
  - 新案件N1設計で過去の似た発言を参照
  - **8192トークン**で1時間インタビュー丸ごと1ベクトル
- **統合先**: LP Park / 記事LP Park / Research Park
- **実装コスト**: 低

#### 4. knowledge/ 全体の意味検索（CCDD Phase 1）

- **何をする**: knowledge/ 30ファイルをチャンク分割してベクトル化
- **使い道**: 「今回の案件に効く pak-philosophy の教え」を意味で抽出
- **実装**: `scripts/vector_store.py` のインフラは整備済み。動かすだけ
- **実装コスト**: 低（30ファイル、初回のみ）

#### 9. 競合広告のマルチモーダル差別化

- **何をする**: 競合のコピー × 画像 を両方ベクトル化 → 「見た目も意味も被ってない」領域発見
- **使い道**: Research Park の差別化距離測定を **画像まで拡張**
- **統合先**: Research Park / Banner Park

#### 10. 退職後の引き継ぎ資産化（人生視点★★★★★）

- **何をする**: 全案件・全知識をベクトル化した永続DBを「形式知の結晶」として残す
- **効果**: 引き継ぎ先が **意味で聞ける** 状態で業務を引き継げる
- **コスト**: 副次効果として自然発生（1〜9の副産物）

---

### 🥉 優先度 B（効果 ★★★）

#### 5. 勝ちパターン横断学習（CCDD Phase 2）

- **何をする**: DPro実績 × CRベクトルを紐付け → 「勝ちゾーン」重心計算
- **使い道**: 新CR生成時に「勝ちゾーンに近いか」でスクリーニング
- **実装コスト**: 高（DPro連携必要）

#### 6. 動画コンテンツの意味インデックス

- **何をする**: YouTube・ショート動画を embedding-2 の動画対応でベクトル化
- **使い道**: 「このトピックで伸びた動画」検索
- **実装コスト**: 中（動画API呼び出し量大）

#### 7. SNSバズ予測

- **何をする**: 過去バズった投稿 × 新企画 のベクトル類似度
- **使い道**: sns-marketer の精度向上
- **統合先**: sns-marketer / sns-post-crew

#### 8. 記事LP構造の横断分析

- **何をする**: 案件間で記事LP構造をベクトル化
- **使い道**: DPro benchmark.json の拡張。「勝ち構造」抽出
- **実装コスト**: 中

---

## 🔧 実装パターン

### 基本: テキストembedding

```python
# vector-utils.md の embed() を経由する
from google import genai
client = genai.Client(api_key=os.environ['GEMINI_API_KEY_1'])

def embed(text):
    r = client.models.embed_content(model='gemini-embedding-2-preview', contents=text)
    return r.embeddings[0].values
```

### マルチモーダル: テキスト + 画像（embedding-2 の真骨頂）

```python
# 画像も同じ空間に載せる
with open('banner.jpg', 'rb') as f:
    img_bytes = f.read()

r = client.models.embed_content(
    model='gemini-embedding-2-preview',
    contents=[
        {'text': 'コピー案: 自分の手で編む、世界でひとつの宝物'},
        {'image': img_bytes}
    ]
)
multimodal_vec = r.embeddings[0].values
```

### ChromaDBへの蓄積（永続化）

```python
import chromadb
client_db = chromadb.PersistentClient(path='.chroma')
coll = client_db.get_or_create_collection('assets')
coll.add(
    embeddings=[multimodal_vec],
    metadatas=[{'client': 'sawada-co', 'type': 'banner', 'date': '2026-04-24'}],
    documents=['コピー本文'],
    ids=['sawada_banner_001']
)
```

### 意味検索

```python
results = coll.query(
    query_embeddings=[embed("落ち着いた世界観のビジュアル")],
    n_results=5,
    where={'client': 'sawada-co'}
)
```

---

## 📍 既存スキル統合マップ

| スキル | 現状のベクトル活用 | 拡張候補 | 優先度 |
|---|---|---|---|
| Research Park | テキストembedding | マルチモーダル（競合画像embedding） | A |
| Banner Park | テキスト品質ゲート | **画像品質ゲート・勝ちビジュアル参照** | **S** |
| 記事LP Park | hookVector + 4段階ゲート | 画像品質ゲート追加 | **S** |
| Short Ad Park | 未使用 | 動画embedding・シーン類似検索 | A |
| LP Park | 未使用 | N1横断・クライアント資料検索 | A |
| Concept Park | conceptベクトル | ブランド資料から自動コンセプト抽出 | B |
| Amazon Captain | 商品ページembedding | 商品画像込みのマルチモーダル | A |
| sns-marketer | 未使用 | バズ予測・類似投稿検索 | B |
| client-context | 未使用 | **資料意味検索で自動発見** | **S** |

---

## ⚠️ 運用上の注意

### 1. ベクトル空間の互換性

- `001` vs `2` は **別空間**。混在した瞬間コサイン類似度が嘘をつく
- 2に切り替えた今、既存 `all_vectors.json` と `knowledge_vectors.db` は **作り直し必須**
- 各案件の過去ベクトルは「旧モデル時代の記録」として分離保管

### 2. 次元数の統一

- DB格納時は **3072固定** 推奨（1536/768可変は混ぜるな）
- ChromaDBのコレクション作成時に次元数固定

### 3. 閾値の再キャリブレーション

- 001時代の閾値（概念 `>=0.50` / 競合 `<=0.55` / 多様性 `<=0.70`）は **仮値**
- 2で動かしてみて、分布ずれがあれば再調整

### 4. API レート・コスト

- Gemini API Free Tier に制限あり。大量ベクトル化時は Paid 推奨
- マルチモーダル（画像・動画）はテキスト比でコスト高め

### 5. Preview版ゆえのリスク

- `gemini-embedding-2-preview` は2026年4月GA直後。安定性はまだ要観察
- APIの破壊的変更の可能性あり → 四半期に一度 Google Blog 確認

### 6. データプライバシー

- 実名含む資料を embedding する時は `.claude/rules/anonymize.md` 準拠
- GitHub push される場所にベクトルDBを置かない（個人情報が逆引き可能になるリスク）

---

## 🚢 ロードマップ提案

### Phase A（2026年5月・退職前着手）

1. ✅ モデル差し替え完了（2026-04-24）
2. 🔲 **マルチモーダル画像検索のPOC**（Banner Parkに導入）
3. 🔲 **クライアント資料ベクトル化**（sawada-co / ameru で試作）
4. 🔲 ユースケース1・2の運用検証

### Phase B（2026年6月・引き継ぎ期）

5. 🔲 knowledge/ 全体ベクトル化（CCDD Phase 1完了）
6. 🔲 N1インタビュー横断分析の試作
7. 🔲 引き継ぎ資料化・このプレイブック更新

### Phase C（退職後 = 引き継ぎ先のロードマップ）

8. 🔲 勝ちパターン横断学習（DPro実績連携）
9. 🔲 動画コンテンツ意味インデックス
10. 🔲 SNSバズ予測

---

## 🔗 関連ファイル

| ファイル | 関係 |
|---|---|
| [vector-utils.md](vector-utils.md) | 共通コード（`embed()` / `cosine_sim()`） |
| [ccdd-strategy.md](ccdd-strategy.md) | 全体方針（Phase 1-4構想） |
| [aipark-imports/vector-first-constitution.md](aipark-imports/vector-first-constitution.md) | Vector-First憲法 |
| [../rules/anonymize.md](../rules/anonymize.md) | 個人情報保護 |
| [../../scripts/vector_store.py](../../scripts/vector_store.py) | 永続DBインフラ |
| [../commands/記事LP-park.md](../commands/記事LP-park.md) | 既存ベクトル活用例 |

---

## 🏴‍☠️ このプレイブックの核心

> embedding の価値は「**意味で繋がる**」こと。
> キーワード検索では見えない繋がりを発見し、モーダルの壁を超えて資産を横断する。
> embedding-2 で VOYAGE号の全資産が "引ける" 状態になる。
> **退職後もここは残る形式知。**
