# ameru banner16 — 納品INDEX

**納品日**: 2026-04-24
**構成**: 4ペルソナ × 4バナー = 16枚（image-gen 8 + Gemini 8）
**フォーマット**: 1:1 スクエア 1024×1024 / Meta・Instagram Feed 想定

---

## 0. コンセプト全体像

| ID | ペルソナ | 軸 | 一言コンセプト |
|----|---------|----|----|
| P1 | 田中さとみ（38歳・広告AE） | 推し活ハイブリッド・IP発見型 | らぶいーず、自分の手で産む。 |
| P2 | 村上あかり（31歳・UXデザイナー） | デジタル解毒・手触り充電者 | 今夜、指先で脳を洗う。 |
| P3 | 小林ゆきの（34歳・教員） | フィエロ・コレクター（完結） | 5体揃う日に、会いに行く。 |
| P4 | 橋本なな（26歳・アパレル販売員） | ギフト設計者（贈与） | 渡す日を、自分の手で編む。 |

**軸の非重複**: 発見 × 解毒 × 完結 × 贈与 — 情緒の着火点が4方向に分散。

---

## 1. バナー16枚 マッピング

### P1 推し活IP発見型（田中さとみ）
| # | ツール | ファイル | 角度 | ヘッドコピー |
|---|--------|----------|------|-------------|
| 1 | image-gen | [P1/image_gen_1.png](P1/image_gen_1.png) | 発見フック純度100% | 「らぶいーず、編めます。」 |
| 2 | image-gen | [P1/image_gen_2.png](P1/image_gen_2.png) | ステージ更新 | 「推しは、産む時代へ。」 |
| 3 | Gemini | [P1/gemini_1.png](P1/gemini_1.png) | 所有欲×固有性（手の中のすもっぴマクロ） | — |
| 4 | Gemini | [P1/gemini_2.png](P1/gemini_2.png) | UGC保存数ドリブン（手元×スマホ） | — |

### P2 デジタル解毒（村上あかり）
| # | ツール | ファイル | 角度 | ヘッドコピー |
|---|--------|----------|------|-------------|
| 1 | image-gen | [P2/image_gen_1.png](P2/image_gen_1.png) | 静謐 | 「画面を閉じて、糸に触れる。」 |
| 2 | image-gen | [P2/image_gen_2.png](P2/image_gen_2.png) | 時間軸 | 「無心で、2時間。」 |
| 3 | Gemini | [P2/gemini_1.png](P2/gemini_1.png) | 静謐の夜・手元マクロ（ランプ・湯気） | — |
| 4 | Gemini | [P2/gemini_2.png](P2/gemini_2.png) | 開封の瞬間・編み始め完成済みキット | — |

### P3 フィエロ・コレクター（小林ゆきの）
| # | ツール | ファイル | 角度 | ヘッドコピー |
|---|--------|----------|------|-------------|
| 1 | image-gen | [P3/image_gen_1.png](P3/image_gen_1.png) | 進捗ゲージ | 「5分の1から、5分の5へ。」 |
| 2 | image-gen | [P3/image_gen_2.png](P3/image_gen_2.png) | 棚整列 | 「5体目を棚に置く、その日のために。」 |
| 3 | Gemini | [P3/gemini_1.png](P3/gemini_1.png) | 5体全員集合・完結スナップ | — |
| 4 | Gemini | [P3/gemini_2.png](P3/gemini_2.png) | 1組目カップル（すもっぴ×ぴょんちー） | — |

### P4 ギフト贈与（橋本なな）
| # | ツール | ファイル | 角度 | ヘッドコピー |
|---|--------|----------|------|-------------|
| 1 | image-gen | [P4/image_gen_1.png](P4/image_gen_1.png) | 手交差 | 「渡す日を、自分の手で編む。」 |
| 2 | image-gen | [P4/image_gen_2.png](P4/image_gen_2.png) | 俯瞰 | 「これ、自分で作ったの？」 |
| 3 | Gemini | [P4/gemini_1.png](P4/gemini_1.png) | 渡す瞬間・受け取る側の表情 | — |
| 4 | Gemini | [P4/gemini_2.png](P4/gemini_2.png) | 過去挫折→今度こそ（編みかけ→完成にゃぽ） | — |

---

## 2. ツール使い分けの思想

| ツール | 得意領域 | 今回の役割 |
|--------|----------|-----------|
| **OpenAI gpt-image-1** | 文字描画・テキスト合成・コピー前面型 | ヘッドコピーを画像内に焼き込む完成形バナー |
| **Gemini 2.5 Flash Image (Nano Banana Pro)** | フォトリアル質感・手元マクロ・人物表情 | コピー焼き込みなし・構図で物語が立つ素材型 |

Gemini側はコピー別合成前提なので、余白に後工程でコピーを乗せてA/Bテスト可能。

---

## 3. 関連ドキュメント

| ファイル | 内容 |
|---------|------|
| [../../../reports/projects/ameru/banner16/product_understanding.md](../../../reports/projects/ameru/banner16/product_understanding.md) | 商品深掘り理解（6軸分析） |
| [../../../reports/projects/ameru/banner16/personas.json](../../../reports/projects/ameru/banner16/personas.json) | N=1 × 4人 設計JSON |
| [../../../reports/projects/ameru/banner16/concepts/concept_P1.md](../../../reports/projects/ameru/banner16/concepts/concept_P1.md) | P1コンセプト詳細 |
| [../../../reports/projects/ameru/banner16/concepts/concept_P2.md](../../../reports/projects/ameru/banner16/concepts/concept_P2.md) | P2コンセプト詳細 |
| [../../../reports/projects/ameru/banner16/concepts/concept_P3.md](../../../reports/projects/ameru/banner16/concepts/concept_P3.md) | P3コンセプト詳細 |
| [../../../reports/projects/ameru/banner16/concepts/concept_P4.md](../../../reports/projects/ameru/banner16/concepts/concept_P4.md) | P4コンセプト詳細 |
| [../../../reports/projects/ameru/banner16/gen_image_gen.py](../../../reports/projects/ameru/banner16/gen_image_gen.py) | image-gen生成スクリプト |
| [../../../reports/projects/ameru/banner16/gen_gemini.py](../../../reports/projects/ameru/banner16/gen_gemini.py) | Gemini生成スクリプト |
| [../../../reports/projects/ameru/banner16/prompts_image_gen.md](../../../reports/projects/ameru/banner16/prompts_image_gen.md) | image-gen全プロンプト記録 |
| [../../../reports/projects/ameru/banner16/prompts_gemini.md](../../../reports/projects/ameru/banner16/prompts_gemini.md) | Gemini全プロンプト記録 |

---

## 4. 遵守した絶対ルール

- ✅ 「らぶいーず」完全ひらがな表記（Love is... 等英語表記は全バナーで不使用）
- ✅ 「買う」系ネガアンカー不使用（肯定形のみ）
- ✅ 時間依存ワード不使用（本日/今日/24時間/いまだけ）
- ✅ 誕生月訴求不使用
- ✅ 助数詞「1体」統一
- ✅ キャラ公式名のみ（すもっぴ／ぴょんちー／にゃぽ／うるる／ぱおぱお）
- ✅ 画像重複なし（16枚すべて異なるビジュアル・角度）

---

## 5. A/Bテスト推奨ロードマップ

1. **第一段**: ペルソナ別にベスト1枚を選定（計4枚）
2. **第二段**: ベスト1枚 × コピー差し替え（Gemini素材を活用）
3. **第三段**: 当たり軸が確定したら動画展開（shortad-park連携）

F2転換率85%死守ラインを踏まえ、CPO ¥4,000・媒体CPA ¥2,000に到達した軸から予算寄せ。
