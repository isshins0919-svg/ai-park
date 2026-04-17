#!/usr/bin/env python3
"""
MCP通信傍受プロキシ
Claude Code → このプロキシ → 実際のDPro MCP
リクエストヘッダーをログに記録してトークンを特定する
"""

import http.server
import urllib.request
import json
import sys
from datetime import datetime

REAL_MCP_URL = "https://api.kashika-20mile.com/mcp"
PROXY_PORT = 8888
LOG_FILE = "/tmp/mcp-headers.log"

class MCPProxyHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # 標準ログを抑制

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        # ========== ヘッダーをログに記録 ==========
        with open(LOG_FILE, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Claude Code → DPro MCP\n")
            f.write("--- HEADERS ---\n")
            for key, val in self.headers.items():
                f.write(f"  {key}: {val}\n")
            try:
                body_json = json.loads(body)
                f.write(f"--- METHOD ---\n  {body_json.get('method','?')}\n")
            except:
                pass
            f.write(f"{'='*60}\n")

        # ========== 実際のDPro MCPに転送 ==========
        forward_headers = {}
        for key, val in self.headers.items():
            if key.lower() not in ("host", "content-length"):
                forward_headers[key] = val

        try:
            req = urllib.request.Request(
                REAL_MCP_URL,
                data=body,
                headers=forward_headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as res:
                res_body = res.read()
                self.send_response(res.status)
                for key, val in res.headers.items():
                    if key.lower() not in ("transfer-encoding",):
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(res_body)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"proxy running"}')


if __name__ == "__main__":
    print(f"🔍 MCPプロキシ起動中 → localhost:{PROXY_PORT}")
    print(f"📝 ログ出力先: {LOG_FILE}")
    print(f"   (Ctrl+C で停止)")
    open(LOG_FILE, "w").close()  # ログファイルをクリア
    server = http.server.HTTPServer(("localhost", PROXY_PORT), MCPProxyHandler)
    server.serve_forever()
