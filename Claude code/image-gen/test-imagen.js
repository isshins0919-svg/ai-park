/**
 * Gemini Imagen 画像生成 テストスクリプト
 * 使い方: node test-imagen.js "プロンプト文"
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = process.env.GEMINI_API_KEY_1;
if (!API_KEY) {
  console.error('❌ GEMINI_API_KEY_1 が未設定です');
  process.exit(1);
}

const PROMPT = process.argv[2] || 'A beautiful Japanese mountain landscape at sunset, photorealistic';
const OUTPUT_FILE = process.argv[3] || 'output.png';

// Imagen 3 エンドポイント
const MODEL = 'imagen-3.0-generate-002';
const ENDPOINT = `/v1beta/models/${MODEL}:predict?key=${API_KEY}`;

const requestBody = JSON.stringify({
  instances: [{ prompt: PROMPT }],
  parameters: {
    sampleCount: 1,
    aspectRatio: '1:1',
    safetyFilterLevel: 'block_few',
  }
});

console.log(`🎨 画像生成開始...`);
console.log(`   モデル: ${MODEL}`);
console.log(`   プロンプト: ${PROMPT}`);
console.log(`   出力先: ${OUTPUT_FILE}`);

const options = {
  hostname: 'generativelanguage.googleapis.com',
  path: ENDPOINT,
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(requestBody),
  }
};

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    if (res.statusCode !== 200) {
      console.error(`❌ APIエラー (${res.statusCode}):`, data);
      return;
    }

    try {
      const json = JSON.parse(data);
      const predictions = json.predictions;

      if (!predictions || predictions.length === 0) {
        console.error('❌ 画像データが返ってきませんでした');
        console.log('レスポンス:', JSON.stringify(json, null, 2));
        return;
      }

      const imageBase64 = predictions[0].bytesBase64Encoded;
      const buffer = Buffer.from(imageBase64, 'base64');
      const outputPath = path.resolve(OUTPUT_FILE);
      fs.writeFileSync(outputPath, buffer);

      const sizeKB = Math.round(buffer.length / 1024);
      console.log(`✅ 画像生成成功！`);
      console.log(`   ファイル: ${outputPath}`);
      console.log(`   サイズ: ${sizeKB} KB`);
    } catch (e) {
      console.error('❌ パースエラー:', e.message);
      console.log('生レスポンス:', data.substring(0, 500));
    }
  });
});

req.on('error', (e) => {
  console.error('❌ リクエストエラー:', e.message);
});

req.write(requestBody);
req.end();
