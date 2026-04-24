#!/usr/bin/env python3
"""ameru バナーPOC Phase 2: 10本のリファレンス画像+コピーを embedding-2-preview でベクトル化

出力:
  - reference/all_vectors.json  (image_vec / text_vec / multimodal_vec を各refに付加)
"""
import os, json, subprocess
from pathlib import Path

from google import genai
from google.genai import types

# env loader
def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass

_load_env('GEMINI_API_KEY_1')
API_KEY = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY", "")
assert API_KEY, "GEMINI_API_KEY_1 未設定"

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-embedding-2-preview"

ROOT = Path(__file__).parent
REF_JSON = ROOT / "reference" / "final_10.json"
OUT_JSON = ROOT / "reference" / "all_vectors.json"

def embed_text(text: str):
    r = client.models.embed_content(
        model=MODEL, contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=3072),
    )
    return r.embeddings[0].values

def embed_image(path: Path):
    img_bytes = path.read_bytes()
    mime = "image/webp" if path.suffix.lower() == ".webp" else ("image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png")
    r = client.models.embed_content(
        model=MODEL,
        contents=types.Content(parts=[types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes))]),
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=3072),
    )
    return r.embeddings[0].values

def embed_multimodal(text: str, path: Path):
    """画像+テキスト両方を同じContent内で送信→1ベクトル化"""
    img_bytes = path.read_bytes()
    mime = "image/webp" if path.suffix.lower() == ".webp" else ("image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png")
    r = client.models.embed_content(
        model=MODEL,
        contents=types.Content(parts=[
            types.Part(text=text),
            types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes)),
        ]),
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=3072),
    )
    return r.embeddings[0].values

if __name__ == "__main__":
    refs = json.loads(REF_JSON.read_text())
    print(f"=== embed {len(refs)} refs via {MODEL} (image + text + multimodal) ===\n")

    for i, ref in enumerate(refs, 1):
        path = Path(ref['local_path'])
        copy = ref.get('copy', '') or ref.get('src', '')
        print(f"[{i:2}/{len(refs)}] {ref['id']}")
        try:
            ref['image_vec'] = embed_image(path)
            print(f"        image ✅ ({len(ref['image_vec'])} dim)")
        except Exception as e:
            print(f"        image ❌ {type(e).__name__}: {str(e)[:120]}")
            ref['image_vec'] = None
        try:
            ref['text_vec'] = embed_text(copy)
            print(f"        text  ✅")
        except Exception as e:
            print(f"        text  ❌ {type(e).__name__}: {str(e)[:120]}")
            ref['text_vec'] = None
        try:
            ref['multimodal_vec'] = embed_multimodal(copy, path)
            print(f"        multi ✅")
        except Exception as e:
            print(f"        multi ❌ {type(e).__name__}: {str(e)[:120]}")
            ref['multimodal_vec'] = None

    OUT_JSON.write_text(json.dumps(refs, ensure_ascii=False, indent=2))
    print(f"\n=== saved → {OUT_JSON} ===")
    print(f"file size: {OUT_JSON.stat().st_size // 1024}KB")
