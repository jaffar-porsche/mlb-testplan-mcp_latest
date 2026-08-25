"""
Tiny always-on local launcher agent for the MLB TestPlan MCP dashboard.

Why this exists:
Browsers cannot spawn local processes for security reasons, so a page button
alone cannot start server.py. This script is a minimal helper process that
listens on 127.0.0.1:8090 and, on request, launches launch.bat (which starts
server.py on port 8080). It uses only the Python standard library — no extra
dependencies required.

Usage:
    python launcher_agent.py

Recommended: add this to Windows Startup (Win+R -> shell:startup) via a
shortcut, or Task Scheduler "At log on", so it is always running in the
background. It is extremely lightweight (idle HTTP server) and safe to
leave running permanently.

Endpoints:
    GET /start   -> launches launch.bat (no-op if already running on 8080)
    GET /status  -> {"running": true/false} based on whether port 8080 accepts connections
"""
import json
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LAUNCH_BAT = BASE_DIR / "launch.bat"
AGENT_PORT = 8090
SERVER_PORT = 8080


def is_port_open(port: str, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/status"):
            self._send_json({"running": is_port_open(SERVER_PORT)})
            return

        if self.path.startswith("/start"):
            if is_port_open(SERVER_PORT):
                self._send_json({"started": False, "reason": "already running"})
                return
            if not LAUNCH_BAT.exists():
                self._send_json({"started": False, "reason": "launch.bat not found"}, status=500)
                return
            # Detached, minimized window so it doesn't block this agent.
            subprocess.Popen(
                ["cmd", "/c", "start", "MLB TestPlan MCP", "/min", str(LAUNCH_BAT)],
                cwd=str(BASE_DIR),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            )
            self._send_json({"started": True})
            return

        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format, *args):
        pass  # keep console quiet


if __name__ == "__main__":
    httpd = ThreadingHTTPServer(("127.0.0.1", AGENT_PORT), Handler)
    print(f"Launcher agent listening on http://127.0.0.1:{AGENT_PORT}  (start=/start, status=/status)")
    httpd.serve_forever()
