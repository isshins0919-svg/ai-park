/**
 * 画像生成モデル比較テスト
 * 使い方: node compare.js "プロンプト"
 * 結果: compare-result.html に並べて表示
 */

const https = require('https');
const fs = require('fs');

const API_KEY = process.env.GEMINI_API_KEY_1;
if (!API_KEY) { console.error('❌ GEMINI_API_KEY_1 未設定'); process.exit(1); }

const PROMPT = process.argv[2] || 'A minimalist Japanese product ad, white background, luxury soap bar with herbs, clean aesthetic';

// ─── Imagen 4 (predict) ───────────────────────────────────────────
function generateImagen4(prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      instances: [{ prompt }],
      parameters: { sampleCount: 1, aspectRatio: '1:1' }
    });
    const options = {
      hostname: 'generativelanguage.googleapis.com',
      path: '/v1beta/models/imagen-4.0-generate-001:predict?key=' + API_KEY,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (c) => { data += c; });
      res.on('end', () => {
        if (res.statusCode !== 200) return reject(new Error('Imagen4 ' + res.statusCode + ': ' + data.substring(0, 200)));
        const json = JSON.parse(data);
        const b64 = json.predictions?.[0]?.bytesBase64Encoded;
        if (!b64) return reject(new Error('Imagen4: 画像データなし'));
        resolve({ model: 'Imagen 4', b64, sizeKB: Math.round(Buffer.from(b64, 'base64').length / 1024) });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ─── Gemini 3 Pro Image (generateContent) ────────────────────────
function generateGemini3Pro(prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { responseModalities: ['TEXT', 'IMAGE'] }
    });
    const options = {
      hostname: 'generativelanguage.googleapis.com',
      path: '/v1beta/models/gemini-3-pro-image-preview:generateContent?key=' + API_KEY,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (c) => { data += c; });
      res.on('end', () => {
        if (res.statusCode !== 200) return reject(new Error('Gemini3Pro ' + res.statusCode + ': ' + data.substring(0, 200)));
        const json = JSON.parse(data);
        const parts = json.candidates?.[0]?.content?.parts || [];
        const imagePart = parts.find((p) => p.inlineData?.mimeType?.startsWith('image/'));
        const textPart = parts.find((p) => p.text);
        if (!imagePart) return reject(new Error('Gemini3Pro: 画像パートなし'));
        const b64 = imagePart.inlineData.data;
        resolve({
          model: 'Gemini 3 Pro',
          b64,
          sizeKB: Math.round(Buffer.from(b64, 'base64').length / 1024),
          text: textPart?.text || ''
        });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ─── Imagen 4 Fast ────────────────────────────────────────────────
function generateImagen4Fast(prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      instances: [{ prompt }],
      parameters: { sampleCount: 1, aspectRatio: '1:1' }
    });
    const options = {
      hostname: 'generativelanguage.googleapis.com',
      path: '/v1beta/models/imagen-4.0-fast-generate-001:predict?key=' + API_KEY,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (c) => { data += c; });
      res.on('end', () => {
        if (res.statusCode !== 200) return reject(new Error('Imagen4Fast ' + res.statusCode + ': ' + data.substring(0, 200)));
        const json = JSON.parse(data);
        const b64 = json.predictions?.[0]?.bytesBase64Encoded;
        if (!b64) return reject(new Error('Imagen4Fast: 画像データなし'));
        resolve({ model: 'Imagen 4 Fast', b64, sizeKB: Math.round(Buffer.from(b64, 'base64').length / 1024) });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ─── HTML レポート生成 ─────────────────────────────────────────────
function buildHTML(prompt, results, elapsed) {
  const now = new Date().toLocaleString('ja-JP');
  const cards = results.map((r) => {
    if (r.error) {
      return `
      <div class="card error">
        <div class="model-name">${r.model}</div>
        <div class="error-msg">❌ ${r.error}</div>
      </div>`;
    }
    return `
      <div class="card">
        <div class="model-name">${r.model}</div>
        <img src="data:image/png;base64,${r.b64}" alt="${r.model}" />
        <div class="meta">${r.sizeKB} KB${r.text ? ' · テキスト付き' : ''}</div>
        ${r.text ? `<div class="ai-text">${r.text.substring(0, 300)}</div>` : ''}
      </div>`;
  }).join('');

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>画像生成モデル比較</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #0f0f0f; color: #eee; padding: 32px; }
  h1 { font-size: 1.4rem; margin-bottom: 8px; color: #fff; }
  .prompt-box { background: #1a1a2e; border: 1px solid #444; border-radius: 8px; padding: 12px 16px; margin-bottom: 24px; font-size: 0.9rem; color: #aaa; }
  .prompt-box span { color: #7eb8f7; font-weight: bold; }
  .meta-info { font-size: 0.75rem; color: #666; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
  .card { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; overflow: hidden; }
  .card.error { border-color: #c0392b; padding: 24px; }
  .model-name { background: #111; padding: 10px 16px; font-weight: bold; font-size: 0.85rem; color: #7eb8f7; border-bottom: 1px solid #333; }
  .card img { width: 100%; display: block; }
  .meta { padding: 8px 16px; font-size: 0.75rem; color: #888; border-top: 1px solid #222; }
  .ai-text { padding: 8px 16px 12px; font-size: 0.78rem; color: #aaa; line-height: 1.5; border-top: 1px solid #222; }
  .error-msg { color: #e74c3c; font-size: 0.85rem; margin-top: 8px; }
</style>
</head>
<body>
<h1>🎨 画像生成モデル比較テスト</h1>
<div class="prompt-box">プロンプト: <span>${prompt}</span></div>
<div class="meta-info">生成時刻: ${now} ／ 所要時間: ${elapsed}秒</div>
<div class="grid">${cards}</div>
</body>
</html>`;
}

// ─── メイン ───────────────────────────────────────────────────────
async function main() {
  console.log('🚀 3モデル同時生成スタート...');
  console.log('   プロンプト:', PROMPT);
  console.log('');

  const start = Date.now();

  const jobs = [
    { name: 'Imagen 4', fn: generateImagen4 },
    { name: 'Imagen 4 Fast', fn: generateImagen4Fast },
    { name: 'Gemini 3 Pro', fn: generateGemini3Pro },
  ];

  const results = await Promise.all(
    jobs.map(async (job) => {
      process.stdout.write(`  ⏳ ${job.name} 生成中...`);
      try {
        const t0 = Date.now();
        const result = await job.fn(PROMPT);
        const sec = ((Date.now() - t0) / 1000).toFixed(1);
        console.log(` ✅ ${result.sizeKB}KB (${sec}s)`);
        return result;
      } catch (e) {
        console.log(` ❌ ${e.message.substring(0, 80)}`);
        return { model: job.name, error: e.message.substring(0, 200) };
      }
    })
  );

  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  const html = buildHTML(PROMPT, results, elapsed);
  fs.writeFileSync('compare-result.html', html);

  console.log('');
  console.log(`✅ 完了！ → compare-result.html を開いてね (${elapsed}秒)`);
}

main();
