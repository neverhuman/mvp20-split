"""Scripted authenticated runtime peer, test-only and never a production authority."""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

if __name__ == "__main__":
    config = json.loads(sys.stdin.readline())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            if self.path != "/outcome" or self.headers.get("Authorization") != "Bearer " + config["token"]:
                self.send_error(401)
                return
            binding = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if config.get("mismatch"):
                binding["intent"]["intent_id"] = "wrong-intent"
            body = json.dumps({"binding": binding, "proof": config["proof"]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        print(server.server_port, flush=True)
        server.serve_forever()
