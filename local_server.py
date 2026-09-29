"""Short-lived localhost server for the browser preview."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import threading
from urllib.parse import parse_qs, unquote, urlparse

from document_model import KmzDocument
from route_model import RouteModel

IDLE_SECONDS = 10 * 60


def start_server(model: RouteModel, document: KmzDocument | None = None) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    web_root = Path(__file__).with_name("web").resolve()
    token = secrets.token_urlsafe(24)
    route_payload = json.dumps(model.to_dict(), ensure_ascii=False).encode("utf-8")
    document_payload = json.dumps(document.to_dict(), ensure_ascii=False).encode("utf-8") if document else b""

    class Handler(BaseHTTPRequestHandler):
        server_version = "KMZPreview/0.3"

        def log_message(self, _format: str, *_args) -> None:
            return

        def _authorized(self, query: dict[str, list[str]]) -> bool:
            header_token = self.headers.get("X-Preview-Token", "")
            query_token = query.get("token", [""])[0]
            return secrets.compare_digest(header_token or query_token, token)

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob: https://tile.openstreetmap.org; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-eval' blob:; worker-src 'self' blob:; connect-src 'self'; font-src 'self' data:")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            host = self.headers.get("Host", "").split(":", 1)[0].lower()
            if host not in {"127.0.0.1", "localhost", "[::1]"}:
                self._send(403, "text/plain; charset=utf-8", "仅允许本机访问".encode())
                return
            if parsed.path.startswith("/api/") and not self._authorized(query):
                self._send(403, "text/plain; charset=utf-8", "访问令牌无效".encode())
                return
            if parsed.path == "/api/route":
                self._send(200, "application/json; charset=utf-8", route_payload)
                return
            if parsed.path == "/api/document":
                if not document:
                    self._send(404, "text/plain; charset=utf-8", "文档数据不可用".encode())
                else:
                    self._send(200, "application/json; charset=utf-8", document_payload)
                return
            if parsed.path.startswith("/api/file/") and document:
                name = unquote(parsed.path.removeprefix("/api/file/"))
                selected = document.files.get(name)
                if selected is None:
                    self._send(404, "text/plain; charset=utf-8", "文件不存在".encode())
                else:
                    self._send(200, "application/json; charset=utf-8", json.dumps(selected.to_dict(), ensure_ascii=False).encode("utf-8"))
                return
            if parsed.path == "/api/status":
                self._send(200, "application/json; charset=utf-8", b'{"status":"ok"}')
                return
            relative = "index.html" if parsed.path in ("", "/") else parsed.path.lstrip("/")
            candidate = (web_root / relative).resolve()
            if web_root not in candidate.parents and candidate != web_root:
                self._send(404, "text/plain; charset=utf-8", "Not found".encode())
                return
            if not candidate.is_file():
                self._send(404, "text/plain; charset=utf-8", "Not found".encode())
                return
            content_types = {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".svg": "image/svg+xml",
                ".wasm": "application/wasm",
                ".ktx2": "image/ktx2",
                ".bin": "application/octet-stream",
                ".woff2": "font/woff2",
            }
            self._send(200, content_types.get(candidate.suffix.lower(), "application/octet-stream"), candidate.read_bytes())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server.preview_token = token  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, name="kmz-preview-server", daemon=True)
    thread.start()
    timer = threading.Timer(IDLE_SECONDS, server.shutdown)
    timer.daemon = True
    timer.start()
    url = f"http://127.0.0.1:{server.server_port}/#token={token}"
    return server, thread, url
