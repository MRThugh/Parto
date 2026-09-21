"""
Parto Web Dev & Production Server
Serves the Parto web application and API endpoints on port 3000.
"""

import http.server
import json
import os
import socketserver
import sys

PORT = int(os.environ.get("PORT", 3000))
HOST = "0.0.0.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class PartoHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        # API Routes
        if self.path == "/api/status" or self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            payload = {
                "status": "healthy",
                "app": "Parto",
                "version": "0.3.0",
                "python": sys.version,
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if self.path == "/api/info":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            payload = {
                "name": "Parto (پرتو)",
                "tagline": "Lightweight Desktop Image Editor",
                "version": "0.3.0",
                "author": "Ali Kamrani (MRThugh)",
                "features": [
                    "Multi-layer system with opacity & blend compositing",
                    "Live non-destructive color adjustments",
                    "Smooth anti-aliased brush tool with context brush bar",
                    "Zero-collision keyboard shortcuts",
                    "5 curated palettes (Dark, Light, Graphite, Midnight, Nord)",
                    "Lossless and lossy export (PNG, JPEG, WebP)",
                ],
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        # Default to index.html for root path or SPA-style fallback
        if self.path == "/" or not os.path.exists(os.path.join(BASE_DIR, self.path.lstrip("/").split("?")[0])):
            potential_file = os.path.join(BASE_DIR, self.path.lstrip("/").split("?")[0])
            if not os.path.exists(potential_file) and not self.path.startswith("/api/"):
                self.path = "/index.html"

        super().do_GET()

    def end_headers(self):
        # Add CORS and cache control headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        # Standard quiet logging
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((HOST, PORT), PartoHTTPRequestHandler) as httpd:
        print(f"Parto Server running on http://{HOST}:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()


if __name__ == "__main__":
    run_server()
