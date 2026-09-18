from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .engine import SemanticKnowledgePlane


class SemanticRequestHandler(BaseHTTPRequestHandler):
    plane: SemanticKnowledgePlane
    server_version = "MotionSemantic/1.0"

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict[str, Any]:
        size = int(self.headers.get("Content-Length", "0") or 0)
        if size > 2_000_000:
            raise ValueError("request body too large")
        raw = self.rfile.read(size) if size else b"{}"
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            report = self.plane.doctor()
            self._json(200 if report.get("ok") else 503, report)
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._body()
            if self.path == "/index":
                repos = body.get("repos") or []
                if not isinstance(repos, list) or not repos:
                    raise ValueError("repos must be a non-empty list of local repository paths")
                reports = [self.plane.index_repository(Path(str(repo))) for repo in repos]
                self._json(200, {"reports": reports})
                return
            if self.path == "/graphify":
                repos = body.get("repo_ids")
                result = self.plane.graphify(
                    repo_ids=repos if isinstance(repos, list) else None,
                    neighbors=int(body.get("neighbors", 8)),
                    min_semantic_score=float(body.get("min_semantic_score", 0.15)),
                )
                self._json(200, result)
                return
            if self.path == "/cos-graph-engine":
                query = str(body.get("query") or "")
                repos = body.get("repo_ids")
                result = self.plane.cos_graph_engine(
                    query,
                    limit=int(body.get("limit", 10)),
                    repo_ids=repos if isinstance(repos, list) else None,
                )
                self._json(200, result)
                return
            self._json(404, {"error": "not_found"})
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": "bad_request", "detail": str(exc)})
        except Exception as exc:  # service boundary: controlled diagnostic, keep process alive
            self._json(500, {"error": "semantic_plane_error", "detail": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(plane: SemanticKnowledgePlane, host: str = "127.0.0.1", port: int = 8791) -> None:
    handler = type("BoundSemanticRequestHandler", (SemanticRequestHandler,), {"plane": plane})
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
