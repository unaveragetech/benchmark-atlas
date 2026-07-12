"""Tiny Ollama-compatible server used for batch-run smoke tests."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = {"models": [{"name": "smoke-test:latest"}]}
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0)); self.rfile.read(length)
        body = {"message": {"role": "assistant", "content": "smoke-test-answer"}}
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *_):
        pass


HTTPServer(("127.0.0.1", 8199), Handler).serve_forever()
