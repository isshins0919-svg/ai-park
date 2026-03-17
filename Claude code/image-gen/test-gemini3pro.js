const https = require('https');
const fs = require('fs');
const API_KEY = process.env.GEMINI_API_KEY_1;

const MODEL = 'gemini-3-pro-image-preview';
const PROMPT = process.argv[2] || 'A minimalist Japanese product ad, white background, luxury soap bar with herbs, clean aesthetic';
const OUTPUT = process.argv[3] || 'gemini3pro-test.png';

const body = JSON.stringify({
  contents: [{ parts: [{ text: PROMPT }] }],
  generationConfig: { responseModalities: ['TEXT', 'IMAGE'] }
});

const options = {
  hostname: 'generativelanguage.googleapis.com',
  path: '/v1beta/models/' + MODEL + ':generateContent?key=' + API_KEY,
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body)
  }
};

console.log('🎨 gemini-3-pro-image-preview テスト中...');
console.log('   プロンプト:', PROMPT);

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', (c) => { data += c; });
  res.on('end', () => {
    if (res.statusCode !== 200) {
      console.error('❌ エラー', res.statusCode, data.substring(0, 500));
      return;
    }
    const json = JSON.parse(data);
    const parts = json.candidates?.[0]?.content?.parts || [];
    const imagePart = parts.find((p) => p.inlineData && p.inlineData.mimeType && p.inlineData.mimeType.startsWith('image/'));
    const textPart = parts.find((p) => p.text);
    if (textPart) console.log('テキスト:', textPart.text.substring(0, 200));
    if (!imagePart) {
      console.log('❌ 画像パート無し');
      console.log('parts keys:', JSON.stringify(parts.map((p) => Object.keys(p))));
      return;
    }
    const b64 = imagePart.inlineData.data;
    const buf = Buffer.from(b64, 'base64');
    fs.writeFileSync(OUTPUT, buf);
    console.log('✅ 成功！→', OUTPUT, '(' + Math.round(buf.length / 1024) + ' KB)');
  });
});

req.on('error', (e) => { console.error('❌ リクエストエラー:', e.message); });
req.write(body);
req.end();
