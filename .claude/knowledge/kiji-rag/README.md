# kiji-rag — 記事LP ベクトル参照DB

記事LP（Squad Beyond系・広告記事LP）をベクトル化して、**新規記事LP制作時の参照・引用元**にするためのRAG基盤。

---

## 目的

- 新規記事LP生成時、過去の勝ち記事から「近い訴求」「近い構成」を検索・参照できるようにする
- 20要素セールスライティング軸で「ほしい機能を持つチャンク」を直接引ける
- 将来的に成果データ（mCVR/着地CVR）と紐付け、「勝ちチャンクだけ参照」できるようにする

---

## データ構造

```
.claude/knowledge/kiji-rag/
├── README.md              # このファイル
├── sales_elements.md      # 20要素（5層×4要素）定義とルーブリック
├── schema.md              # chunks.json / meta.json スキーマ定義
├── INDEX.md               # 格納済み記事一覧
└── articles/
    └── <YYYYMMDD>_<brand>_<keyword>/
        ├── meta.json      # 記事全体メタ（URL, ブランド, 取得日, 成果等）
        ├── chunks.json    # チャンク列（ブロック統合済 + 20要素スコア）
        └── embeddings.npy # ベクトル（embedding-2生成、後工程）
```

---

## チャンクの作り方（本質ルール）

1. **ブロック切り替わり = チャンク境界**
   - `text → text → text` は1チャンクに統合
   - `text → image → text` は3チャンク
2. **block_type は3種のみ**: `text` / `image` / `video`
3. **テキストチャンクが長くなりすぎる場合**（概ね600字超え）は段落で内部分割（embedding-2の精度安定域）
4. **各チャンクに 20要素スコア を付与**（0.0〜1.0、詳細 → `sales_elements.md`）

---

## クエリ検索の設計

ベクトル類似度 × 20要素フィルタの二段構え。

### 典型クエリ例

```
# 権威性の強い信頼ブロックを探す
WHERE authority >= 0.7 AND dominant_layer = "B"

# 悩み共感系のフック候補（記事冒頭）
WHERE dominant_layer = "A" AND chunk_order <= 5

# ビフォーアフター画像事例
WHERE transformation >= 0.6 AND block_type = "image"

# CTA直前の反論処理
WHERE objection_handling >= 0.5 AND chunk_order = (cta_order - 1)

# 新記事のフック用に「似た悩み × 勝ちチャンク」
ORDER BY cosine_sim(query_vec, chunk_vec) DESC
WHERE dominant_layer = "A" AND article_mCVR_percentile >= 70
```

---

## 記事の追加フロー

1. 記事URLから全ブロック抽出（順序・block_type・content）
2. ブロック切り替わりで統合してチャンク化
3. 各チャンクを20要素ルーブリックでスコアリング
4. `chunks.json` / `meta.json` に保存
5. `INDEX.md` に1行追加
6. embedding-2 でベクトル生成（後工程バッチ）

---

## 運用原則

- **個人実名** は匿名化ルール（`.claude/rules/anonymize.md`）に従う
- 口コミのファーストネーム1文字（例: Kさん）は原文保持可、フルネーム・居住地市区町村は匿名化
- 成果データ（mCVR/CVR）は `meta.json.performance` に入れる。未取得なら `null` のまま
