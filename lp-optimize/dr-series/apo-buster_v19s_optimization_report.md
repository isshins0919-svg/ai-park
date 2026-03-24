# LP高速化診断レポート
**対象LP:** アポバスタ-F v19s (me_apo-buster_v19s_test_kousokuka)
**クライアント:** Dr.Series
**診断日:** 2026-03-24
**環境:** EC-Force（__PAYMENT_FORM__ テンプレート確認済み）

---

## 診断サマリー

| 重要度 | 件数 |
|--------|------|
| 🔴 CRITICAL（即修正） | 5件 |
| 🟡 IMPORTANT（次回修正） | 4件 |
| 🟢 NICE TO HAVE | 2件 |
| ⚠️ 要確認・触らない | 3件 |

---

## 🔴 CRITICAL（修正済み）

### ① ヒーロー画像に preload / fetchpriority がない
- **現状:** apo_1-2.webp が最初の画像なのに読み込み優先度が未設定
- **修正:** HEADに `<link rel="preload" as="image">` を追加、imgに `fetchpriority="high" decoding="sync"` を追加
- **効果:** ★★★★★ LCP（最大コンテンツ描画）が大幅改善

### ② html5shiv（IE8/9向けレガシーコード）が残存
- **現状:** `<script src="//cdn.jsdelivr.net/html5shiv/3.7.2/html5shiv.min.js"></script>`
- **修正:** 完全削除
- **効果:** ★★★★★ 外部リクエスト1件削減、レンダリングブロック解消

### ③ fade.js / popup.js に defer がない
- **現状:** 同期読み込み（レンダリングブロック）
- **修正:** `defer` 属性を追加
- **効果:** ★★★★☆ スクリプト実行をDOM構築後に遅延

### ④ 動画が外部CDNから preload 未指定で読み込まれている
- **現状:** `<video autoplay loop muted>` — preload属性なし
- **修正:** `preload="metadata"` を追加（autoplay維持しつつ初期DL最小化）
- **効果:** ★★★☆☆ 大容量MP4の不要な先読みを防止

### ⑤ カウントダウンタイマーが10msポーリング
- **現状:** `setInterval(checkComplete, 10)` — 1秒100回のDOM操作
- **修正:** `setInterval(checkComplete, 100)` に変更（10倍省CPU）
- **効果:** ★★★☆☆ メインスレッドのブロッキングを大幅削減

---

## 🟡 IMPORTANT（修正済み）

### ⑥ 50枚超の画像が全件即時ロード（lazy-loadなし）
- **現状:** 全画像にloading属性なし → ページ読み込み時に全画像をダウンロード
- **修正:** 4枚目以降に `loading="lazy"` を追加
  - 除外: apo_1-2, 1-3, 1-4（hero3枚）
  - 除外: fixed固定ボタン（apo_chat_01.webp）
- **効果:** ★★★★☆ 初期読み込みのネットワーク帯域を大幅削減

### ⑦ `<map name="maplink">` が同一nameで5回重複
- **現状:** maplink という同一nameが5箇所 → HTML仕様上最初の1つだけ有効
- **修正:** 2回目以降を maplink2〜5 に変更し、usemapも対応
- **効果:** ★★★☆☆ HTML仕様準拠に修正（ブラウザ依存の動作を排除）

### ⑧ preconnect が設定されていない
- **現状:** googleapis / cdnjs / mysquadbeyond.com への事前接続なし
- **修正:** HEADに3件の `<link rel="preconnect">` を追加
- **効果:** ★★☆☆☆ DNS解決とTLS接続コストを削減

### ⑨ 末尾に空の `#fixed` divが重複存在
- **現状:** ボディ内で定義済みなのにfooter後にも空の#fixedが存在
- **修正:** 末尾の重複divを削除
- **効果:** ★★☆☆☆ 不要なDOMノードを削除

---

## ⚠️ 今回触らない（要確認 / リスクあり）

### A. jQuery 2.2.4（フッター）
- EC-Force環境確定のため変更・削除NG
- EC-Force管理画面でjQuery読み込み状況を確認後に判断

### B. canonical URLが別ドメイン
- `https://shop.rmh.co.jp/lp?u=proust_official`（proustからのコピペミス疑い）
- robots: noindexのため実害は低いが、正しいURL or 削除を検討
- **クライアント確認後に対応すること**

### C. GTM IDが2つ存在
- HEAD: `GTM-PKCQRWT` / noscript: `GTM-MKQ65DL`
- 2コンテナ運用の意図か設定ミスか確認が必要

### D. Slick Carousel CSS
- slick.css / slick-theme.css がHEADにあるが本文内にsliderのDOMが見当たらない
- `__PAYMENT_FORM__` 内で使用中かを確認のうえ、不要なら削除でrender-blocking解消

---

## 出力ファイル

| ファイル | 説明 |
|---------|------|
| `apo-buster_v19s_optimized_header.html` | 最適化済みヘッダー |
| `apo-buster_v19s_optimized_body.html` | 最適化済みボディ |
| `apo-buster_v19s_optimized_footer.html` | 最適化済みフッター |
| `apo-buster_v19s_optimization_report.md` | 本レポート |
