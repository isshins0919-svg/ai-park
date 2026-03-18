# on:myskin face v112 LPO TEST 高速化レポート
最終更新: 2026-03-18

## 変更点サマリー

### HEAD（3箇所）
1. `jquery-3.6.0.js`（非圧縮・未minified）→ `jquery-3.6.0.min.js` に変更
2. ヒーロー画像（バナー）の `<link rel="preload">` を追加
3. YouTubeサムネのための `preconnect` を追加

### BODY（2箇所）
1. ヒーロー画像に `fetchpriority="high" decoding="sync"` 追加
2. `<video>` タグに `preload="none"` 追加

### FOOTER（4箇所）
1. jQuery 2.2.4 重複削除（HEADで3.6.0を読み込み済み）
2. `fade.js` / `popup.js` に `defer` 追加
3. `html5shiv`（IE9以前向け・不要）削除
4. 空の重複 `<div id="fixed">` 削除

## 禁止事項（やっていないこと）
- ❌ `loading="lazy"` の追加
- ❌ video の lazy load 化
- ❌ カルーセルJS変更
- ❌ body内 style タグ削除
- ❌ CSS欄への変更
