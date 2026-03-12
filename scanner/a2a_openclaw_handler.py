"""
A2A Protocol Handler for OpenClaw Gateway
Adds /.well-known/agent-card.json endpoint to serve A2A agent discovery
"""
import http.server
import json
import os
from pathlib import Path

WELL_KNOWN_DIR = Path.home() / '.openclaw' / '.well-known'

class A2AHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/.well-known/agent-card.json':
            card_path = WELL_KNOWN_DIR / 'agent-card.json'
            if card_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(card_path, 'r') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error":"Agent card not found"}')
        elif self.path == '/':
            # Health check
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"openclaw-a2a-handler"}')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"Not found"}')
    
    def log_message(self, format, *args):
        # Quiet logging
        pass

def start_a2a_server(port=18788):
    """Start A2A handler on alternate port (OpenClaw uses 18789)"""
    server = http.server.HTTPServer(('0.0.0.0', port), A2AHandler)
    print(f"🔑 A2A Protocol Handler running on port {port}")
    print(f"   Agent card: http://<host>:{port}/.well-known/agent-card.json")
    server.serve_forever()

if __name__ == '__main__':
    start_a2a_server()
