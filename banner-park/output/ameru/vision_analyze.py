#!/usr/bin/env python3
"""Phase 3.2: Gemini Vision で10バナーの要素分解
   出力: reference/vision_elements.json
"""
import os, json, subprocess
from pathlib import Path

from google import genai
from google.genai import types

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
VISION_MODEL = "gemini-2.5-flash"

ROOT = Path(__file__).parent
CLUSTER_JSON = ROOT / "reference" / "clusters.json"
OUT_JSON = ROOT / "reference" / "vision_elements.json"

PROMPT = """この広告バナー画像を分析してください。必ず以下のJSONフォーマットで返答してください（```json等の装飾なし、純JSON）:

{
  "main_visual": "画面の中心に何が写っているか（1文）",
  "palette": ["メイン色1", "メイン色2", "アクセント色"],
  "layout": {
    "copy_position": "トップ/ミドル/ボトム/左/右/中央 のいずれか",
    "product_position": "同上",
    "cta_position": "トップ/ボトム/右下/なし"
  },
  "main_copy": "一番目立つ文言（画像から読み取る）",
  "sub_copy": "サブコピー・説明文（あれば）",
  "cta": "CTAの文言（無ければnull）",
  "emotional_tone": "広告のトーン1語（例: 癒し / 達成感 / 驚き / 高級感 / ワクワク）",
  "appeal_axis": "何を売っているかの訴求軸を1文で",
  "visual_style": "写真/イラスト/実写+テロップ/CGモデル のいずれか"
}"""

def analyze_image(path: Path):
    img_bytes = path.read_bytes()
    mime = "image/webp" if path.suffix.lower() == ".webp" else ("image/jpeg" if path.suffix.lower() in [".jpg",".jpeg"] else "image/png")
    resp = client.models.generate_content(
        model=VISION_MODEL,
        contents=[
            types.Part(text=PROMPT),
            types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes))
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return json.loads(resp.text)

if __name__ == "__main__":
    data = json.loads(CLUSTER_JSON.read_text())
    refs = data['refs']
    print(f"=== Vision要素分解 ({len(refs)}件) via {VISION_MODEL} ===\n")

    for i, ref in enumerate(refs, 1):
        print(f"[{i:2}/{len(refs)}] {ref['id']} ... ", end="", flush=True)
        try:
            analysis = analyze_image(Path(ref['local_path']))
            ref['vision'] = analysis
            print(f"✅ {analysis.get('emotional_tone','?')} / {analysis.get('appeal_axis','?')[:40]}")
        except Exception as e:
            print(f"❌ {type(e).__name__}: {str(e)[:120]}")
            ref['vision'] = None

    OUT_JSON.write_text(json.dumps(refs, ensure_ascii=False, indent=2))
    print(f"\nsaved: {OUT_JSON}")
