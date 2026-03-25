# LP制作ルール（地雷管理）

過去の失敗事例から学習済みの禁止事項。必ず守る。

## 禁止事項

- **EC-ForceへのjQuery追加 → NG**
  LP側でjQueryを追加するとEC-Forceの購入スクリプトが壊れる

- **ヒーロー画像へのlazy-load → NG**
  ファーストビューの画像にlazy-loadをつけると表示速度が逆に悪化する

## LP高速化の診断項目

jQuery重複 / preload / fetchpriority / defer / lazy-load / レガシーコード除去

詳細手順: `.claude/commands/lp-speed.md`