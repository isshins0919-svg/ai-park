#!/usr/bin/env python3
"""
batch_fv.py — FVバリアント別バッチ動画生成スクリプト
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CSVに「1-1」〜「1-9」形式のFVパターンが含まれる場合、
各FVパターンを個別に取り出して9本の動画を生成する。

使い方:
  python3 batch_fv.py --csv "台本.csv" --clips "素材フォルダ" --output-dir "output/" [--fv 1]

オプション:
  --fv N    : 指定したFVパターンのみ生成（例: --fv 1 で1-1のみ）
  --fv all  : 全パターン生成（デフォルト）
  --top-banner TEXT : 上部固定バナーテキスト
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


EDIT_AI = Path(__file__).parent / "edit_ai_v2.py"


def parse_fv_csv(csv_path: str) -> dict:
    """
    CSVを解析して以下を返す:
    - header_rows: ヘッダーメタデータ行（■セクション）
    - fv_scenes: {"1-1": row, "1-2": row, ...}  FVパターン行
    - body_scenes: [(no_str, row), ...]  ボディシーン行
    - top_banner: 依頼メモから自動抽出したバナーテキスト（あれば）
    """
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    header_rows: list[list[str]] = []
    fv_scenes: dict[str, list[str]] = {}
    body_scenes: list[tuple[str, list[str]]] = []
    top_banner: str | None = None
    in_script = False
    in_memo = False

    for row in rows:
        if not row:
            header_rows.append(row)
            continue
        col0 = row[0].strip()

        if "■ 台本" in col0:
            in_script = True
            in_memo = False
            header_rows.append(row)
            continue
        elif "■ 素材リスト" in col0:
            break
        elif col0.startswith("■"):
            in_script = False
            in_memo = "依頼メモ" in col0 or "■依頼メモ" in col0
            header_rows.append(row)
            continue

        if in_memo:
            # 依頼メモからバナーテキストを抽出
            full_text = " ".join(row)
            m = re.search(r'「([^」]+)」という文字', full_text)
            if m and top_banner is None:
                top_banner = m.group(1)
            header_rows.append(row)
            continue

        if not in_script:
            header_rows.append(row)
            continue

        # スクリプト行の解析
        # フォーマット: No., テキスト, 素材, 注釈
        # または: (空), No., テキスト, 素材, 注釈
        no_str = ""
        if col0 == "" and len(row) > 1:
            no_str = row[1].strip()
        elif col0:
            no_str = col0

        if not no_str:
            header_rows.append(row)
            continue

        # FVパターン: "1-1", "1-2", ...
        if re.match(r'^\d+-\d+$', no_str):
            fv_scenes[no_str] = row
        # ヘッダ行スキップ
        elif "No" in no_str or "テキスト" in no_str:
            header_rows.append(row)
        # ボディシーン: "2", "3", ...（空テキストはスキップ）
        elif re.match(r'^\d+$', no_str):
            text = row[2].strip() if col0 == "" and len(row) > 2 else (row[1].strip() if len(row) > 1 else "")
            if text and text not in ("【ここに書く】",):
                body_scenes.append((no_str, row))
            else:
                pass  # 空シーンスキップ
        else:
            header_rows.append(row)

    return {
        "header_rows": header_rows,
        "fv_scenes": fv_scenes,
        "body_scenes": body_scenes,
        "top_banner": top_banner,
    }


def make_temp_csv(parsed: dict, fv_key: str, fv_no: int = 1) -> str:
    """
    指定FVパターン + ボディシーンの一時CSVを生成して返す（ファイルパス）。
    シーン番号は 1, 2, 3... に振り直す。
    """
    fv_row = parsed["fv_scenes"][fv_key]
    body_scenes = parsed["body_scenes"]

    # FV行を scene No.=1 に振り直す
    # フォーマット検出
    if fv_row[0].strip() == "":
        # 5列形式: (空), No., テキスト, 素材, 注釈
        new_fv = ["", str(fv_no)] + fv_row[2:]
    else:
        # 4列形式: No., テキスト, 素材, 注釈
        new_fv = [str(fv_no)] + fv_row[1:]

    # ボディシーンを 2, 3, ... に振り直す
    new_body = []
    for i, (_, row) in enumerate(body_scenes, start=fv_no + 1):
        if row[0].strip() == "":
            new_row = ["", str(i)] + row[2:]
        else:
            new_row = [str(i)] + row[1:]
        new_body.append(new_row)

    # 一時ファイルに書き出し
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", encoding="utf-8", delete=False,
        prefix=f"gungun_{fv_key.replace('-', '_')}_"
    )
    writer = csv.writer(tmp)
    for row in parsed["header_rows"]:
        writer.writerow(row)
    writer.writerow(new_fv)
    for row in new_body:
        writer.writerow(row)
    tmp.close()
    return tmp.name


def run_edit(csv_path: str, clips_dir: str, output_path: str,
             top_banner: str | None, ref_video: str | None,
             no_ai: bool = False) -> bool:
    """edit_ai_v2.py を呼び出して動画を生成する。"""
    cmd = [
        sys.executable, str(EDIT_AI),
        "--script", csv_path,
        "--clips",  clips_dir,
        "--output", output_path,
    ]
    if top_banner:
        cmd += ["--top-banner", top_banner]
    if ref_video:
        cmd += ["--ref-video", ref_video]
    if no_ai:
        cmd += ["--no-ai"]

    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

    print(f"\n🎬 生成中: {Path(output_path).name}")
    result = subprocess.run(cmd, env=env)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="FVバリアント別バッチ動画生成")
    parser.add_argument("--csv",     required=True, help="台本CSVパス")
    parser.add_argument("--clips",   required=True, help="素材フォルダパス")
    parser.add_argument("--output-dir", required=True, help="出力フォルダパス")
    parser.add_argument("--fv",      default="all",
                        help="生成するFVパターン番号（例: 1）またはall（デフォルト）")
    parser.add_argument("--top-banner", default=None,
                        help="上部固定バナーテキスト（未指定時はCSVから自動抽出）")
    parser.add_argument("--ref-video", default=None, help="参考動画パス")
    parser.add_argument("--no-ai",   action="store_true", help="AI APIを使わない")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV解析
    print(f"📄 CSV解析: {args.csv}")
    parsed = parse_fv_csv(args.csv)
    fv_scenes = parsed["fv_scenes"]
    body_scenes = parsed["body_scenes"]

    print(f"  FVパターン: {sorted(fv_scenes.keys())}")
    print(f"  ボディシーン: {len(body_scenes)}シーン")

    # バナーテキスト決定
    top_banner = args.top_banner or parsed["top_banner"]
    if top_banner:
        print(f"  🏷  上部バナー: 「{top_banner}」（自動検出）")

    # 生成するFVを絞り込む
    if args.fv == "all":
        target_fvs = sorted(fv_scenes.keys())
    else:
        key = f"1-{args.fv}"
        if key not in fv_scenes:
            print(f"❌ FVパターン {key} が見つかりません。利用可能: {sorted(fv_scenes.keys())}")
            sys.exit(1)
        target_fvs = [key]

    print(f"\n🚀 生成対象: {target_fvs}")

    results = []
    for fv_key in target_fvs:
        # 一時CSV生成
        tmp_csv = make_temp_csv(parsed, fv_key)
        output_path = str(output_dir / f"gungun_{fv_key.replace('-', '_')}.mp4")

        ok = run_edit(tmp_csv, args.clips, output_path, top_banner, args.ref_video, args.no_ai)
        os.unlink(tmp_csv)

        results.append((fv_key, output_path, ok))
        status = "✅" if ok else "❌"
        print(f"  {status} {fv_key} → {Path(output_path).name}")

    # サマリー
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  完了: {sum(1 for _,_,ok in results if ok)}/{len(results)}本")
    for fv_key, path, ok in results:
        s = "✅" if ok else "❌"
        print(f"  {s} {fv_key}: {path}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
