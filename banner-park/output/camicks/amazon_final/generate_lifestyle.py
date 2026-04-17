#!/usr/bin/env python3
"""Camicks Amazon Final — AI素材生成（Imagen 4.0 + Gemini 3 Pro Image）"""
import os, subprocess, json, base64
from pathlib import Path

result = subprocess.run(['zsh', '-c', 'source ~/.zshrc && echo $GEMINI_API_KEY_1'], capture_output=True, text=True)
api_key = result.stdout.strip()

from google import genai
from google.genai import types

OUT = Path("/Users/ca01224/Desktop/一進VOYAGE号/banner-park/output/camicks/amazon_final/ai_assets")
OUT.mkdir(exist_ok=True)

client = genai.Client(api_key=api_key)

# Imagen 4.0 for photorealistic assets
imagen_prompts = {
    "lifestyle_office": "Professional Japanese woman in her late 30s, sitting at a clean modern office desk, legs crossed, showing elegant dark gray mid-calf ribbed socks with brown leather loafers, warm natural window lighting, shot from waist down, shallow depth of field, editorial fashion photography, clean minimalist Japanese office, ultra high quality",
    "lifestyle_casual": "Close-up of Japanese person's lower legs wearing dark gray mid-calf ribbed socks with clean white leather sneakers and rolled-up raw denim jeans, walking on a clean stone garden path, natural golden hour outdoor lighting, editorial street fashion photography, ultra high quality",
    "washi_texture": "Extreme macro close-up of Japanese washi paper fiber texture, showing natural paper fibers beautifully intertwined with textile threads, soft warm diffused natural lighting, very shallow depth of field, cream and off-white tones, scientific documentary photography, ultra high quality",
    "factory_heritage": "Interior of a traditional Japanese textile factory in Osaka, showing vintage yarn spinning machinery with wooden spools holding cream and gray colored yarn threads, warm amber industrial lighting, experienced Japanese craftsman's weathered hands carefully working with fine threads, nostalgic documentary photography style, ultra high quality",
    "main_product": "A single pair of elegant dark gray mid-calf ribbed socks standing upright on a pure white background, professional product photography with clean studio lighting and very subtle soft shadow underneath, the socks are the main subject taking up most of the frame, ultra high resolution, Amazon product listing style photo",
}

results = {}

# Try Imagen 4.0 first
for name, prompt in imagen_prompts.items():
    print(f"Generating [{name}] with imagen-4.0-generate-001...")
    try:
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="BLOCK_ONLY_HIGH",
            )
        )
        if response.generated_images:
            out_path = OUT / f"{name}.png"
            response.generated_images[0].image.save(str(out_path))
            results[name] = {"status": "ok", "path": str(out_path), "model": "imagen-4.0"}
            print(f"  ✅ Saved: {out_path}")
        else:
            results[name] = {"status": "no_images", "model": "imagen-4.0"}
            print(f"  ⚠️ No images returned")
    except Exception as e:
        print(f"  ❌ imagen-4.0 failed: {e}")
        # Fallback to gemini-3-pro-image-preview
        print(f"  Trying gemini-3-pro-image-preview...")
        try:
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        out_path = OUT / f"{name}.png"
                        img_bytes = part.inline_data.data
                        with open(out_path, 'wb') as f:
                            f.write(img_bytes)
                        results[name] = {"status": "ok", "path": str(out_path), "model": "gemini-3-pro"}
                        print(f"  ✅ Saved (fallback): {out_path}")
                        break
                else:
                    results[name] = {"status": "no_images", "model": "gemini-3-pro"}
                    print(f"  ⚠️ No image in response")
            else:
                results[name] = {"status": "no_images", "model": "gemini-3-pro"}
                print(f"  ⚠️ No candidates")
        except Exception as e2:
            results[name] = {"status": "error", "error": str(e2)}
            print(f"  ❌ Both failed: {e2}")

with open(OUT / "generation_results.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

ok = sum(1 for v in results.values() if v['status']=='ok')
print(f"\n✅ Done! {ok}/{len(results)} succeeded")
