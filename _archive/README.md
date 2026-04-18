# 🗑️ _archive/ — 削除候補置き場

> 船長（一進さん）の最終削除判断待ち。一進AIが「もう使わないだろう」と判定したファイルの隔離場所。

## 使い方

1. 一進AIがここに隔離する
2. 船長が中身を確認
3. OKなら `rm -rf _archive/` で完全削除 / 必要ならrepo内に戻す

---

## 2026-04-19 隔離分

### old-backups/ — 古いバックアップ
- `CLAUDE.md.backup-20260418` — CLAUDE.md 編集前の旧版。Git履歴に残ってるので不要。

### deprecated/ — 古い/不要ドキュメント
- `CLAUDE-mauri.md` — mauri案件専用。案件終了確認済。`.claude/clients/mauri.md` も現存するが案件自体終了。
- `SETUP-intern.md` — インターン受け入れ手順。継続予定なしと確認済。

### deprecated-scripts/ — スキル化済みの旧スクリプト
- `weekly-report.py` — `.claude/commands/weekly-review.md` スキル化で代替済。cron非稼働確認済。
- `weekly-report.sh` — 同上。

### duplicate-textbook/ — 重複
- `textbook/` — ルート直下の textbook。`docs/textbook/` の方が ch00〜ch10 まで揃った完全版なので、ルートは旧版。

---

## 削除する前にチェック

- [ ] `git log -- {path}` で履歴確認
- [ ] `grep -r {filename} ..` で他から参照されてないか確認
- [ ] 消して困らないか腹落ち

**最終削除コマンド:**
```bash
cd /Users/ca01224/Desktop/一進VOYAGE号
rm -rf _archive/
```
