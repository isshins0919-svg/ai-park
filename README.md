# AI Park — 広告クリエイティブ自動生成システム

> Claude Code で動く、マーケティング戦略 → クリエイティブ自動生成の統合スキルセット

## アーキテクチャ

```
Research Park → strategy.json v1（商品理解 × 3層N1需要 × ベクトルインテリジェンス）
                    |
Concept Park  → strategy.json v2（+ コンセプト × KV × セールスコピー × フック角度）
  ver.1.2         |
        +---------+---------+
        |         |         |
  Banner Park  ShortAd    記事LP Park
  v7.0         Park v7.0  v3.0
```

**設計思想**: クリエイティブは「生成」ではなく戦略の「翻訳」

---

## クイックスタート

### 1. 前提条件
- [Claude Code](https://claude.ai/claude-code) がインストール済み
- Git がインストール済み
- Python 3.9+
- FFmpeg（動画生成に必要）

### 2. セットアップ

```bash
# 1. このフォルダをプロジェクトルートに配置
#    例: ~/Desktop/my-project/

# 2. Claude Codeのプロジェクトとして開く
cd ~/Desktop/my-project
claude

# 3. 環境変数を設定（~/.zshrc に追加）
export GEMINI_API_KEY_1="your-gemini-api-key"
export XAI_API_KEY="your-xai-api-key"
export FISH_AUDIO_API_KEY="your-fish-audio-key"

# 4. Python依存ライブラリ
pip install moviepy Pillow requests
```

### 3. 初回設定

1. `.claude/identity.md` を作成してAIの個性を定義
2. `CLAUDE.md` を自社プロジェクトに合わせてカスタマイズ
3. APIキーを環境変数に設定

### 4. 使い方

Claude Code内でスキルをスラッシュコマンドで呼び出す:

```
/research-park    — 商材リサーチ → strategy.json v1
/concept-park     — コンセプト壁打ち → strategy.json v2
/banner-park      — バナー自動生成（Nano Banana Pro）
/shortad-park     — ショート動画自動生成（Grok + NanoBanana）
/記事LP-park      — 記事LP自動生成
/youtube-research — YouTubeチャンネルリサーチ
/park-kaizen      — 改善壁打ち
/park-patrol      — スキル自動進化パトロール
```

---

## ファイル構成

### スキル（`.claude/commands/`）
| ファイル | バージョン | 説明 |
|---------|-----------|------|
| `research-park.md` | v1.0 | 商品理解 × 3層N1需要 × ベクトルインテリジェンス × マーケ戦略 |
| `concept-park.md` | v1.2 | 壁打ち型コンセプト確定。KV × セールスコピー × フック角度 |
| `banner-park.md` | v7.0 | Nano Banana Pro画像生成 × 仮説駆動 × ベクトル品質ゲート × PDFレポート |
| `shortad-park.md` | v7.0 | DNA転用 × デスマス調連続トーク × デュアル素材（Grok + NanoBanana） |
| `記事LP-park.md` | v3.0 | 戦略翻訳型 × ベクトル品質ゲート × hookVector × PDFレポート |
| `youtube-research.md` | v1.0 | チャンネル戦略 × 100chリサーチ × 企画設計 × サムネイル生成 |
| `park-kaizen.md` | — | 改善壁打ちパートナー |
| `park-patrol.md` | — | スキル自動進化パトロール |

### ナレッジ（`.claude/knowledge/`）
| ファイル | 説明 |
|---------|------|
| `pak-philosophy.md` | マーケティング哲学全文（全クリエイティブの判断基準） |
| `hook-db.md` | フックコピーDB（BH1〜BH8パターン） |
| `cta-db.md` | CTAコピーDB（BC1〜BC8パターン） |
| `banner-dna-templates.md` | バナー勝ちDNAテンプレート（BN-A〜F） |
| `shortad-dna-templates.md` | 動画勝ちDNAテンプレート |
| `scene-role-tags.md` | シーン役割タグ定義 |
| `motion-patterns.md` | モーションパターン集 |
| `article-lp-rules.md` | 記事LPルール |
| `asset-guide.md` | 素材収集ガイド |
| `google-slides-recipe.md` | Googleスライド制作レシピ |
| `slack-error-notification.md` | エラー通知テンプレート |

### エージェント（`.claude/agents/`）— 一進VOYAGE号クルー

**見張り台（Gate部門）**
| ファイル | アイコン | 説明 |
|---------|---------|------|
| `gate-legal-crew.md` | ⚖️ | 法規クルー |
| `gate-brand-crew.md` | 🛡️ | ブランドクルー |
| `gate-quality-crew.md` | 🚦 | 品質クルー |
| `gate-n1-crew.md` | 🎯 | N1クルー |
| `cvr-crew.md` | 📈 | CVRクルー |
| `gate-hook-crew.md` | 🪝 | フック監査クルー |
| `gate-marketing-crew.md` | 📊 | マーケ監査クルー |
| `gate-typography-crew.md` | 🔤 | 文字クルー |
| `gate-visual-crew.md` | 👁️ | ビジュアルクルー |
| `gate-image-prompt-crew.md` | 🎨 | 画像プロンプトクルー |

**記事甲板（Kiji部門）**
| ファイル | アイコン | 説明 |
|---------|---------|------|
| `kiji-hook-crew.md` | 🎣 | 記事フッククルー |
| `kiji-arc-crew.md` | 🌊 | 記事アーククルー |
| `kiji-trust-crew.md` | ⚓ | 記事トラストクルー |
| `kiji-cta-crew.md` | 🔔 | 記事CTAクルー |
| `kiji-offer-crew.md` | 💎 | 記事オファークルー |
| `kiji-compass-crew.md` | 🧭 | 記事コンパスクルー |

**動画甲板（Movie部門）**
| ファイル | アイコン | 説明 |
|---------|---------|------|
| `movie-cta-crew.md` | 📣 | 動画CTAクルー |
| `movie-hook-crew.md` | ⚡ | 動画フッククルー |
| `movie-script-crew.md` | 📜 | 動画スクリプトクルー |
| `movie-visual-crew.md` | 🎨 | 動画ビジュアルクルー |

**その他**
| ファイル | アイコン | 説明 |
|---------|---------|------|
| `pak-sensei.md` | 🧙‍♂️ | パク師匠（航海哲学者） |
| `brand-collector.md` | — | ブランド素材収集 |
| `research-dive.md` | — | リサーチDIVE |

### その他
| ファイル | 説明 |
|---------|------|
| `CLAUDE.md` | プロジェクト設定テンプレート（カスタマイズ用） |
| `sync.sh` | 2台同期スクリプト（pull/push/status） |

---

## 生成エンジン

| エンジン | 用途 | APIキー |
|---------|------|---------|
| Nano Banana Pro（`gemini-3-pro-image-preview`） | 画像生成 | `GEMINI_API_KEY_1/2/3` |
| Grok Imagine Video | 動画生成 | `XAI_API_KEY` |
| Fish Audio TTS | ナレーション音声 | `FISH_AUDIO_API_KEY` |

---

## 基本ワークフロー

```
1. /research-park で商材を深掘り → strategy.json v1 出力
2. /concept-park でコンセプトを壁打ち確定 → strategy.json v2 出力
3. 各アウトプットスキルで制作:
   - /banner-park → バナー画像 10枚 + PDFレポート
   - /shortad-park → ショート動画 30秒 × 3フック
   - /記事LP-park → 記事LP HTML
```

---

## カスタマイズ

### 自社ナレッジの追加
`.claude/knowledge/` に自社のマーケティングナレッジをMarkdownで追加。
CLAUDE.mdの「ナレッジ読み込み」セクションに追記すれば、毎セッション自動で読み込まれます。

### スキルの拡張
`.claude/commands/` に新しいスキルファイルを追加すると、`/スキル名` で呼び出せます。

---

## 注意事項

- APIキーは環境変数で管理。ファイルに直書きしない
- `strategy.json` は商材ごとに出力フォルダを分けて管理推奨
- Grok動画は常に横型（848x480）で出力 → FFmpegでポートレート変換が必要（スキル内で自動処理）

---

Built with Claude Code
