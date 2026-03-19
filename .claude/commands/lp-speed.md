# LP Speed Park ver.1.0 — LP高速化自動診断 × 修正スキル

## 目的
LPのHTMLファイルを渡すだけで、速度ボトルネックを自動診断し、
優先順位付きの改善リストと修正済みHTMLを即出力する。

---

## 発動トリガー

- 「〇〇のLP高速化して」
- 「このLPを速くして」
- 「LP診断して」
- 「lp speed」
- 「〇〇のLPチェックして」

---

## 実行手順

### Step 1: 対象ファイル特定

クライアント名を言えばファイルを自動検索:
```
lp-optimize/{client_name}/ 配下のHTMLファイルを特定
```

複数ある場合は確認してから進む。

### Step 2: 自動診断（チェックリスト全項目）

HTMLを読み込み、以下を全件チェックする。

---

## 診断チェックリスト

### 🔴 CRITICAL（必ず直す — 最速改善効果）

#### HEAD最適化
- [ ] **jQuery重複読み込み**: HEAD + FOOTERの両方にjQueryがないか
  - ⚠️ EC-Force注意: LP側でjQuery追加するとEC-Forceの購入スクリプトが壊れる
  - → HEADのEC-Force読み込みをそのままにし、LP独自のjQueryのみ削除
- [ ] **jQuery非圧縮版**: `jquery.min.js` でなく `jquery.js` を読んでいないか
  - → `jquery-X.X.X.min.js` に変更
- [ ] **ヒーロー画像のpreload**: 最初に見えるメイン画像にpreloadがあるか
  - → `<link rel="preload" as="image" href="hero.jpg">` を追加
- [ ] **YouTube/外部サービスのpreconnect**: YouTubeサムネなどを使っている場合
  - → `<link rel="preconnect" href="https://i.ytimg.com">` 等を追加

#### BODY最適化
- [ ] **ヒーロー画像のfetchpriority**: 最初の画像にhighが設定されているか
  - → `fetchpriority="high" decoding="sync"` を追加
- [ ] **動画のpreload**: videoタグにpreload="auto"が設定されていないか
  - → `preload="none"` に変更（自動読み込みを防ぐ）

#### FOOTER最適化
- [ ] **JSにdefer/async**: body末尾のscriptタグにdefer/asyncがあるか
  - → `fade.js` / `popup.js` 等に `defer` を追加
- [ ] **不要なレガシーコード**: `html5shiv`（IE9以前向け）等が残っていないか
  - → 削除
- [ ] **空のDOM要素**: 空のdivや重複要素がないか
  - → 削除

---

### 🟡 IMPORTANT（次に直す — 中程度の改善効果）

#### 画像最適化
- [ ] **サイズの大きい画像**: 1MB超えの画像がないか
  - → WebP変換 + 圧縮を推奨（ただし変換は別途作業）
- [ ] **lazy-loadの適用**: スクロールしないと見えない画像にloading="lazy"があるか
  - ⚠️ 注意: ヒーロー画像（最初に見える）にはloading="lazy"を絶対つけない
  - ⚠️ 注意: カルーセル内の画像には個別判断が必要（動作確認必須）
  - → スクロール以降の静止画像に `loading="lazy"` を追加

#### CSS最適化
- [ ] **未使用のインラインスタイル**: bodyタグ内の大量styleブロックがないか
  - → ※ EC-Force系は触らない（購入フォームのスタイルが壊れるリスク）
- [ ] **render-blocking CSS**: CSSの読み込み順が最適か
  - → 重要でないCSSをfooterに移動

#### JavaScript最適化
- [ ] **同期読み込みのJS**: bodyタグ途中にblockingなscriptがないか
  - → deferまたはbottomに移動

---

### 🟢 NICE TO HAVE（余裕があれば）

- [ ] **フォントの最適化**: Google Fontsを大量に読んでいないか
  - → 使うウェイトのみに絞る / font-displayを追加
- [ ] **サードパーティスクリプトの遅延**: タグマネージャー / チャットツール等
  - → `defer` または `async` を追加
- [ ] **メタ情報**: OGP / description が設定されているか
  - → LP SEOとしてではなくSNS拡散時の見た目のため

---

## Step 3: 診断レポートを出力

```
🔍 LP高速化診断レポート
対象: [ファイル名] ｜ クライアント: [名前] ｜ [日付]
━━━━━━━━━━━━━━━━━━━━━━━━━━

【診断サマリー】
🔴 CRITICAL: X件
🟡 IMPORTANT: X件
🟢 NICE TO HAVE: X件

━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 今すぐ直す（CRITICAL）

① jQuery重複読み込み
   現状: HEAD + FOOTER両方にjQuery 2.2.4が存在
   修正: FOOTERの重複を削除
   ⚠️ EC-Force確認: [EC-Force利用の有無]
   効果: ★★★★★

② jQueryが非圧縮版
   現状: jquery-2.2.4.js
   修正: jquery-2.2.4.min.js に変更
   効果: ★★★★☆

...

━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 次に直す（IMPORTANT）

...

━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 今回触らない（リスクあり）
- [理由とともに、あえてやらなかったことを明記]

━━━━━━━━━━━━━━━━━━━━━━━━━━

【変更サマリー】
HEAD: X箇所変更
BODY: X箇所変更
FOOTER: X箇所変更
削除: X箇所
```

---

## Step 4: 修正済みHTMLを出力

診断レポート確認後、修正を適用して保存:

```
lp-optimize/{client_name}/{original_name}_optimized.html
```

同時に変更ログを `.md` ファイルとして保存:
```
lp-optimize/{client_name}/{original_name}_optimization_report.md
```

---

## ⚠️ 絶対にやらないこと（禁止事項）

これまでの作業で確認された地雷リスト:

| 禁止事項 | 理由 |
|---------|------|
| EC-Force利用LPにjQueryを追加 | EC-Forceの購入スクリプトが壊れる（onmyskin事例） |
| ヒーロー画像にloading="lazy" | 最初に見える画像が遅延表示され、UXが悪化 |
| カルーセルJS内の画像を無断でlazy化 | カルーセルの動作が壊れる可能性 |
| body内styleタグの削除 | EC-Force / 購入フォームのスタイルが壊れるリスク |
| CSS変更 | LPのデザイン崩れリスク |
| videoのlazy load化 | 再生タイミングが狂う可能性 |

---

## クライアント別の注意事項

### on:my skin（ヨミテ）
- **EC-Force利用**: jQueryは触らない（追加・変更ともにNG）
- LP番号管理あり（v8, v112 等）。ファイル名に番号を含める

### proust（ヨミテ）
- 動画 + 画像の複合型LP。動画のpreloadに注意
- scrollTo(0,0)バグ修正の前例あり（既存の挙動を壊さないよう注意）

### gungun（ヨミテ）
- 薬機法準拠LP。コピーは変更しない（高速化のみ）

---

## 過去の実績（参照事例）

| クライアント | 対象LP | 対応内容 | 時期 |
|------------|--------|---------|------|
| on:my skin | v8 / v112 | HEAD/BODY/FOOTER最適化、jQuery重複削除 | 2026-03-18 |
| proust | メインLP | 高速化 + 動画二重表示バグ修正 | 2026-03-05〜09 |
| gungun | メインLP | 高速化対応 | 2026-03-05 |
