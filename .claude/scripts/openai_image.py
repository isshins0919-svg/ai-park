#!/usr/bin/env python3
"""
OpenAI gpt-image-1 画像生成コアクライアント

CLI:
    python3 openai_image.py --prompt "a red apple" --out /tmp/out.png
    python3 openai_image.py --prompt "..." --out out.png --size 1024x1024 --quality medium --n 2

Module:
    from openai_image import generate_image
    paths = generate_image(prompt="...", out_dir="/tmp", size="1024x1024", quality="medium", n=1)

サイズ:   1024x1024 / 1024x1536 / 1536x1024 / auto
品質:     low / medium / high / auto
API仕様: https://platform.openai.com/docs/api-reference/images
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import requests

API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-1"
VALID_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}
VALID_QUALITIES = {"low", "medium", "high", "auto"}


class OpenAIImageError(Exception):
    """OpenAI Image API エラー。billing / auth / rate_limit / invalid 等を含む"""


def _resolve_api_key(api_key: Optional[str]) -> str:
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise OpenAIImageError(
            "OPENAI_API_KEY が未設定。~/.zshrc に `export OPENAI_API_KEY=sk-...` を追記して `source ~/.zshrc` を実行して。"
        )
    return key


def _handle_error(resp_json: dict) -> None:
    err = resp_json.get("error", {})
    msg = err.get("message", "不明なエラー")
    etype = err.get("type", "")
    code = err.get("code", "")

    if "billing" in msg.lower() or code == "billing_hard_limit_reached":
        raise OpenAIImageError(
            f"課金上限到達。https://platform.openai.com/settings/organization/billing でチャージ or Usage limits引き上げ。原文: {msg}"
        )
    if etype == "invalid_request_error":
        raise OpenAIImageError(f"リクエスト不正: {msg}")
    if "rate" in msg.lower() or code == "rate_limit_exceeded":
        raise OpenAIImageError(f"レート制限: {msg}")
    if code == "invalid_api_key":
        raise OpenAIImageError(f"APIキー無効: ~/.zshrc のキーを確認して。原文: {msg}")
    raise OpenAIImageError(f"[{etype}/{code}] {msg}")


def generate_image(
    prompt: str,
    out_dir: str,
    filename_prefix: str = "openai",
    size: str = "1024x1024",
    quality: str = "medium",
    n: int = 1,
    api_key: Optional[str] = None,
    timeout: int = 180,
) -> List[str]:
    """
    画像生成して保存。生成された画像のパスのリストを返す。

    Args:
        prompt: 画像プロンプト
        out_dir: 保存先ディレクトリ（存在しなければ作る）
        filename_prefix: ファイル名プレフィックス（{prefix}_{timestamp}_{i}.png）
        size: 1024x1024 / 1024x1536 / 1536x1024 / auto
        quality: low / medium / high / auto
        n: 生成枚数（1〜10）
        api_key: 明示指定。省略時は OPENAI_API_KEY 環境変数
        timeout: HTTPタイムアウト秒

    Returns:
        保存した画像ファイルの絶対パス（リスト）
    """
    if size not in VALID_SIZES:
        raise OpenAIImageError(f"size不正: {size}. 選択肢: {sorted(VALID_SIZES)}")
    if quality not in VALID_QUALITIES:
        raise OpenAIImageError(f"quality不正: {quality}. 選択肢: {sorted(VALID_QUALITIES)}")
    if not (1 <= n <= 10):
        raise OpenAIImageError(f"n不正: {n}. 1〜10で指定")

    key = _resolve_api_key(api_key)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": n,
        "size": size,
        "quality": quality,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise OpenAIImageError(f"レスポンスがJSONでない: HTTP {resp.status_code} {resp.text[:200]}")

    if resp.status_code != 200 or "error" in data:
        _handle_error(data)

    ts = int(time.time())
    paths: List[str] = []
    for i, item in enumerate(data.get("data", [])):
        b64 = item.get("b64_json")
        if not b64:
            continue
        suffix = f"_{i+1}" if n > 1 else ""
        fpath = out_path / f"{filename_prefix}_{ts}{suffix}.png"
        fpath.write_bytes(base64.b64decode(b64))
        paths.append(str(fpath.resolve()))

    if not paths:
        raise OpenAIImageError("画像データが返らなかった")
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="OpenAI gpt-image-1 画像生成CLI")
    ap.add_argument("--prompt", required=True, help="画像プロンプト")
    ap.add_argument("--out", required=True, help="出力先ファイルパス（単発） or ディレクトリ（複数枚）")
    ap.add_argument("--size", default="1024x1024", choices=sorted(VALID_SIZES))
    ap.add_argument("--quality", default="medium", choices=sorted(VALID_QUALITIES))
    ap.add_argument("--n", type=int, default=1)
    args = ap.parse_args()

    out = Path(args.out)
    if out.suffix.lower() == ".png" and args.n == 1:
        out_dir = str(out.parent)
        prefix = out.stem
    else:
        out_dir = str(out)
        prefix = "openai"

    try:
        paths = generate_image(
            prompt=args.prompt,
            out_dir=out_dir,
            filename_prefix=prefix,
            size=args.size,
            quality=args.quality,
            n=args.n,
        )
    except OpenAIImageError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    # 単発 & 拡張子.png指定なら、指定ファイル名にリネーム
    if out.suffix.lower() == ".png" and args.n == 1 and len(paths) == 1:
        final = out.resolve()
        Path(paths[0]).rename(final)
        paths = [str(final)]

    for p in paths:
        print(f"✅ {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
