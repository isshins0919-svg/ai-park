"""T04 リトライ（IP_RECITATION回避プロンプト）"""
import os, subprocess, time

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh', '-i', '-c', f'echo ${var}'],
                               capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except Exception: pass

for _v in ['GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
    _load_env(_v)

from google import genai
from google.genai import types

key = os.environ.get('GEMINI_API_KEY_1', '').strip()
if not key:
    raise RuntimeError("GEMINI_API_KEY_1 未設定")

client = genai.Client(api_key=key)
OUT = 'reports/clients/ameru/images/phase2/T04_bg_kraft_texture.png'

prompt = """A simple warm beige-brown natural fiber flat texture surface, uniform color (hex #C9B39A to #B8A184), subtle organic grain and slight fiber patterns visible at normal viewing. Soft even lighting. Edge to edge flat surface only, no objects, no folds, no text. 1:1 square composition. Pure abstract natural texture background suitable for product photography backdrop."""

print("🎨 T04 retry 開始...")
t0 = time.time()
resp = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents=[types.Content(role='user', parts=[types.Part.from_text(text=prompt + "\n\nAspect ratio: 1:1 square.")])],
    config=types.GenerateContentConfig(response_modalities=['IMAGE'])
)

saved = False
for c in resp.candidates or []:
    for p in c.content.parts or []:
        if p.inline_data:
            with open(OUT, 'wb') as f:
                f.write(p.inline_data.data)
            saved = True
            break
    if saved: break

elapsed = time.time() - t0
if saved:
    print(f"✅ T04 完了 {elapsed:.1f}s ({os.path.getsize(OUT)/1024:.0f}KB)")
else:
    print(f"⚠️ T04 失敗 (finish_reason等): {elapsed:.1f}s")
    for c in resp.candidates or []:
        print(f"   finish_reason: {c.finish_reason}")
