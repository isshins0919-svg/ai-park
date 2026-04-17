/**
 * DPro MCP プロキシ — Cloudflare Worker
 *
 * DPro MCP Server（認証不要）を外部からRESTで叩けるようにするプロキシ。
 * n8n や任意のHTTPクライアントから呼び出せる。
 *
 * エンドポイント:
 *   GET /apps                    → 媒体一覧
 *   GET /genres?q=ヒザ           → ジャンル検索
 *   GET /items?app_id=1&limit=3  → 広告データ取得
 *
 * デプロイ先: Cloudflare Workers（無料プラン）
 */

const MCP_URL = 'https://api.kashika-20mile.com/mcp';

// ツール名マッピング
const TOOL_MAP = {
  '/apps':   'read_apps_api_v1_apps_get',
  '/genres': 'search_genres_api_v1_genres_get',
  '/items':  'get_items_by_rds_api_v1_items_get',
};

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // CORS対応（n8nからのクロスオリジンリクエスト用）
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const toolName = TOOL_MAP[url.pathname];
    if (!toolName) {
      return new Response(
        JSON.stringify({ error: 'Unknown endpoint. Use /apps /genres /items' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // クエリパラメータをtool argumentsに変換
    const args = {};
    for (const [k, v] of url.searchParams.entries()) {
      // 数値に変換できるものは数値に
      args[k] = isNaN(v) || v === '' ? v : Number(v);
    }

    try {
      const result = await callMCPTool(toolName, args);
      return new Response(JSON.stringify(result), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    } catch (e) {
      return new Response(
        JSON.stringify({ error: e.message }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
  },
};

/**
 * MCP ツールを呼び出してレスポンスを返す
 * 1. initialize でセッション確立
 * 2. tools/call でツール実行
 * 3. SSE or JSON レスポンスをパースして返す
 */
async function callMCPTool(toolName, args) {
  let sessionId = null;

  // Step 1: initialize
  const initRes = await fetch(MCP_URL, {
    method: 'POST',
    headers: buildHeaders(null),
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'dpro-cf-proxy', version: '1.0' },
      },
    }),
  });

  sessionId = initRes.headers.get('mcp-session-id') || null;

  // initialized 通知を送る（セッションありの場合）
  if (sessionId) {
    await fetch(MCP_URL, {
      method: 'POST',
      headers: buildHeaders(sessionId),
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'notifications/initialized',
      }),
    });
  }

  // Step 2: tools/call
  const toolRes = await fetch(MCP_URL, {
    method: 'POST',
    headers: buildHeaders(sessionId),
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: { name: toolName, arguments: args },
    }),
  });

  // Step 3: レスポンスパース（SSE or JSON）
  const contentType = toolRes.headers.get('content-type') || '';
  let data;

  if (contentType.includes('text/event-stream')) {
    data = await parseSSE(toolRes.body);
  } else {
    data = await toolRes.json();
  }

  // JSON-RPCエラーチェック
  if (data.error) {
    throw new Error(`MCP error: ${JSON.stringify(data.error)}`);
  }

  // result.content[0].text をパースして返す
  const content = data?.result?.content;
  if (Array.isArray(content) && content[0]?.type === 'text') {
    try {
      return JSON.parse(content[0].text);
    } catch {
      return content[0].text;
    }
  }

  return data?.result ?? data;
}

function buildHeaders(sessionId) {
  const h = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream',
  };
  if (sessionId) h['Mcp-Session-Id'] = sessionId;
  return h;
}

/**
 * SSE ストリームをパースして最後の JSON-RPC レスポンスを返す
 */
async function parseSSE(body) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let lastResult = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop(); // 最後の不完全行を保持

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') continue;
        try {
          const parsed = JSON.parse(raw);
          if (parsed.id !== undefined) lastResult = parsed; // idあり = レスポンス
        } catch { /* 無視 */ }
      }
    }
  }

  return lastResult;
}
