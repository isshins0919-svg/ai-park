"""
Amazon部長クン — メイン画像 v1
Amazonルール: 純白背景 / 商品85%以上 / テキスト・装飾NG
目的: 検索結果サムネイル = 最重要画像
戦略: Camicksらしいエレガントさ × Amazonルール完全準拠
"""
import subprocess, os, time

def _load_env(var):
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass

for _v in ['GEMINI_API_KEY_1','GEMINI_API_KEY_2','GEMINI_API_KEY_3']:
    _load_env(_v)

from google import genai
from google.genai import types

API_KEYS = [k for k in [os.environ.get(f'GEMINI_API_KEY_{i}','').strip() for i in range(1,4)] if k]
clients = [genai.Client(api_key=k) for k in API_KEYS]
print(f"✅ API Keys: {len(API_KEYS)}本")

slug = 'camicks'
assets_dir = f'banner-park/output/{slug}/source_assets'
out_dir = f'banner-park/output/{slug}/amazon_c_final'

def load_asset(filename):
    path = os.path.join(assets_dir, filename)
    if not os.path.exists(path):
        print(f"  ⚠️ 素材なし: {filename}")
        return None
    with open(path, 'rb') as f:
        data = f.read()
    ext = path.split('.')[-1].lower()
    mime = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png'}.get(ext,'image/jpeg')
    return types.Part.from_bytes(data=data, mime_type=mime)

prompt = """
Create a professional Amazon product main image for Camicks secret five-finger socks.

AMAZON MAIN IMAGE RULES (CRITICAL — must follow exactly):
  - Pure white background: RGB(255, 255, 255) — absolutely no off-white, cream, or gray
  - Product must occupy at least 85% of the image frame
  - NO text of any kind — no logos, no labels, no watermarks, no Japanese text
  - NO props, NO backgrounds elements, NO decorative items
  - NO shadows that are too dramatic — soft natural shadow only
  - The product must be fully visible — nothing cropped at edges

PRODUCT DESCRIPTION:
Camicks socks are mid-length (ミドル丈) socks in deep navy or dark charcoal color.
The CRITICAL feature: from the OUTSIDE, these look like completely normal, elegant, seamless socks.
The five-finger structure is completely hidden inside.
Show them as beautiful, premium, elegant mid-ankle socks.

COMPOSITION:
Show 2 socks arranged elegantly:
  Option A: One sock upright/displayed, one folded neatly beside it — like a luxury retail display
  Option B: Both socks side by side, slightly angled, showing the top and toe of each

The socks should look like premium Japanese craftsmanship.
Clean, precise, elegant — like a product from a high-end Japanese sock brand.
Very soft, even studio lighting from above — no harsh shadows.
The socks should look substantial and well-made.

STYLE:
  - Professional product photography style
  - Even, diffused studio lighting
  - Socks look premium and worth ¥2,480
  - Color: deep navy (濃紺) or dark charcoal gray
  - They look like completely normal, beautifully made mid-ankle socks
"""

assets = [
    "camicks-s_darkgray.jpg",
    "camicks-women-inside.jpg",
]

print(f"\n[メイン画像 v1] 白背景・商品単体")

contents = []
for asset_name in assets:
    part = load_asset(asset_name)
    if part:
        contents.append(part)
        print(f"  📎 {asset_name}")
contents.append(prompt)

fn = "amazon_main_v1.png"
fp = os.path.join(out_dir, fn)

for attempt in range(3):
    client = clients[attempt % len(clients)]
    try:
        resp = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(aspect_ratio='1:1')
            )
        )
        img_data = next((p.inline_data.data for p in resp.parts if p.inline_data), None)
        if not img_data or len(img_data) < 10240:
            if attempt < 2: time.sleep(5)
            continue
        with open(fp, 'wb') as f:
            f.write(img_data)
        print(f"  ✅ 完了: {fn} ({len(img_data)//1024}KB)")
        break
    except Exception as e:
        print(f"  ⚠️ attempt {attempt+1}: {e}")
        if attempt < 2: time.sleep(8)
else:
    print(f"  ❌ 失敗")

print(f"\n出力先: {fp}")
