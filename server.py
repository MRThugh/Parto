"""
Parto Development & Status Server
Author: Ali Kamrani (علی کامرانی)

Development-only server for the Parto desktop application.
Restricts file serving to prevent exposing source code, project files, or secrets.
"""

import http.server
import json
import os
import socketserver
import sys

from parto import __version__ as PARTO_VERSION, __author__ as PARTO_AUTHOR

PORT = int(os.environ.get("PORT", 3000))
HOST = "0.0.0.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SafePartoHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Safe HTTP Request Handler:
    - Exposes API health and info endpoints.
    - Prevents directory traversal and source code leakage (.py, .json, .git, etc.).
    - Serves an informational status page for web preview.
    """

    def do_GET(self):
        clean_path = self.path.split("?")[0].rstrip("/")

        # API Endpoints
        if clean_path in ("/api/status", "/api/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            payload = {
                "status": "healthy",
                "app": "Parto (پرتو)",
                "author": PARTO_AUTHOR,
                "version": PARTO_VERSION,
                "python": sys.version.split()[0],
            }
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
            return

        if clean_path == "/api/info":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            payload = {
                "name": "Parto (پرتو)",
                "tagline": "Lightweight Desktop Image Editor",
                "version": PARTO_VERSION,
                "author": PARTO_AUTHOR,
                "github": "https://github.com/MRThugh/Parto",
                "features": [
                    "Authoritative Single-Document Architecture",
                    "Offset-aware Crop, Resize, Rotate, and Flip transformations",
                    "Multi-layer system with non-destructive compositing & visibility-aware merge",
                    "Professional Brush Tool with 1-500px range, color swapping, and stroke safety",
                    "Explicit Canvas interaction ownership (Space-pan, Middle-click pan)",
                    "Live non-destructive color adjustments with Compare Original inspection",
                    "Strict history no-op detection and safe undo/redo rollback",
                    "Safe file I/O with EXIF orientation handling",
                ],
            }
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
            return

        # Block source code and sensitive file access
        forbidden_extensions = (
            ".py", ".json", ".md", ".txt", ".lock", ".sh",
            ".yml", ".yaml", ".git", ".env", ".toml", ".ini",
        )
        lower_path = clean_path.lower()
        if (
            any(lower_path.endswith(ext) for ext in forbidden_extensions)
            or "/." in lower_path
            or lower_path.startswith("/parto")
        ):
            self.send_response(403)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"403 Forbidden: Access to application source files is restricted.")
            return

        # Root or status page request: Serve Parto Desktop App Status Page
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parto (پرتو) — Lightweight Desktop Image Editor</title>
    <style>
        :root {
            --bg: #09090b;
            --surface: #18181b;
            --border: #27272a;
            --text: #f4f4f5;
            --muted: #a1a1aa;
            --primary: #0284c7;
            --accent: #38bdf8;
            --font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: var(--font);
            display: flex;
            min-height: 100vh;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .container {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            max-width: 680px;
            width: 100%;
            padding: 36px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        }
        .header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
        .badge {
            background: rgba(2, 132, 199, 0.15);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }
        h1 { font-size: 26px; font-weight: 700; }
        .tagline { color: var(--muted); margin-bottom: 24px; font-size: 15px; line-height: 1.5; }
        .author { margin-bottom: 24px; font-size: 14px; color: var(--text); }
        .author strong { color: var(--accent); }
        .features-card {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 24px;
        }
        .features-card h3 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--muted); margin-bottom: 12px; }
        ul { list-style: none; display: flex; flex-direction: column; gap: 8px; font-size: 14px; }
        li { display: flex; align-items: center; gap: 8px; }
        li::before { content: "✓"; color: #22c55e; font-weight: bold; }
        .actions { display: flex; gap: 12px; }
        .btn {
            display: inline-flex;
            align-items: center;
            padding: 10px 18px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s;
        }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: #0369a1; }
        .btn-secondary { background: var(--border); color: var(--text); }
        .btn-secondary:hover { background: #3f3f46; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Parto (پرتو)</h1>
            <span class="badge">v0.3.1 Desktop Image Editor</span>
        </div>
        <p class="tagline">A fast, modern, and lightweight desktop image editor built with Python and PySide6.</p>
        <div class="author">
            Author & Owner: <strong>Ali Kamrani (علی کامرانی)</strong>
        </div>
        <div class="features-card">
            <h3>Engine & Architecture Highlights</h3>
            <ul>
                <li>Authoritative Single-Document Architecture with LayerStack</li>
                <li>Offset-aware Crop, Resize, Rotate, and Flip transformations</li>
                <li>Multi-layer compositing with visibility-aware Merge Down</li>
                <li>Interactive Brush Tool with 1–500px range, color swap, and stroke safety</li>
                <li>Explicit interaction ownership for Space-pan and Middle-mouse navigation</li>
                <li>Live non-destructive color adjustments with Compare Original</li>
                <li>Strict history no-op detection and atomic undo/redo restoration</li>
                <li>Safe file I/O with EXIF orientation handling</li>
            </ul>
        </div>
        <div class="actions">
            <a href="/api/info" class="btn btn-primary">API Specification</a>
            <a href="/api/health" class="btn btn-secondary">Health Check</a>
        </div>
    </div>
</body>
</html>"""
        rendered_html = html.replace("v0.3.1", f"v{PARTO_VERSION}").replace("Ali Kamrani (علی کامرانی)", PARTO_AUTHOR)
        self.wfile.write(rendered_html.encode("utf-8"))

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((HOST, PORT), SafePartoHTTPRequestHandler) as httpd:
        print(f"Parto Server running on http://{HOST}:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()


if __name__ == "__main__":
    run_server()
