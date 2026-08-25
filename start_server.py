"""
Simple helper to start the MLB TestPlan MCP server (server.py on port 8080).

Run directly (one-shot, starts server and exits):
    python start_server.py

Run as a background HTTP agent so the dashboard "Start Server" button can
trigger it (listens on port 8090, exposes GET /start):
    python start_server.py --agent

Or import and call from elsewhere:
    from start_server import start_server
    start_server()
"""
import json
import socket
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LAUNCH_BAT = BASE_DIR / "launch.bat"
SERVER_PORT = 8080
AGENT_PORT = 8090


def is_server_running(host: str = "127.0.0.1", port: int = SERVER_PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def start_server() -> bool:
    """Starts the server via launch.bat if it isn't already running.

    Returns True if a start was triggered, False if it was already running.
    """
    if is_server_running():
        print(f"Server already running on port {SERVER_PORT}.")
        return False

    if not LAUNCH_BAT.exists():
        raise FileNotFoundError(f"launch.bat not found at {LAUNCH_BAT}")

    subprocess.Popen(
        ["cmd", "/c", "start", "MLB TestPlan MCP", str(LAUNCH_BAT)],
        cwd=str(BASE_DIR),
    )
    print(f"Launching server via {LAUNCH_BAT} ...")
    return True


class _AgentHandler(BaseHTTPRequestHandler):
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
        if self.path.startswith("/start"):
            try:
                started = start_server()
                self._send_json({"started": started})
            except FileNotFoundError as exc:
                self._send_json({"started": False, "error": str(exc)}, status=500)
            return
        if self.path.startswith("/status"):
            self._send_json({"running": is_server_running()})
            return
        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format, *args):
        pass  # keep console quiet


def run_agent():
    httpd = ThreadingHTTPServer(("127.0.0.1", AGENT_PORT), _AgentHandler)
    print(f"start_server agent listening on http://127.0.0.1:{AGENT_PORT}  (GET /start, GET /status)")
    httpd.serve_forever()


if __name__ == "__main__":
    if "--agent" in sys.argv:
        run_agent()
    else:
        sys.exit(0 if start_server() is not None else 1)

