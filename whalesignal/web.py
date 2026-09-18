"""Zero-dependency web dashboard for WhaleSignal.

Uses only the Python standard library (http.server) so it runs anywhere the package
does. Serves a single-page heatmap plus two JSON endpoints that reuse the exact same
analysis/briefing code as the CLI and MCP server:

    GET /                      -> the dashboard HTML
    GET /api/rank?tickers=...  -> ranked conviction JSON
    GET /api/briefing?tickers  -> written market briefing JSON

Run:
    python -m whalesignal.web --demo            # synthetic data, no key
    python -m whalesignal.web --port 8000       # live (needs UW_API_KEY)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .analysis import rank_tickers
from .briefing import DEFAULT_WATCHLIST, build_briefing
from .client import UWError
from .config import DEMO_ENV, settings

_HTML = (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")


def _parse_tickers(query: str) -> list[str]:
    params = parse_qs(query)
    raw = (params.get("tickers", [""])[0]).replace(",", " ").split()
    return [t.upper() for t in raw] or list(DEFAULT_WATCHLIST)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:  # keep the console quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, code: int = 200) -> None:
        self._send(code, json.dumps(payload).encode("utf-8"), "application/json")

    def do_GET(self) -> None:
        route = urlparse(self.path)
        if route.path == "/":
            self._send(200, _HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif route.path == "/api/rank":
            self._handle_rank(_parse_tickers(route.query))
        elif route.path == "/api/briefing":
            self._handle_brief(_parse_tickers(route.query))
        else:
            self._json({"error": "not found"}, code=404)

    def _handle_rank(self, tickers: list[str]) -> None:
        try:
            ranked = asyncio.run(rank_tickers(tickers))
            self._json({"demo": settings.demo_mode, "count": len(ranked), "ranking": ranked})
        except UWError as exc:
            self._json({"error": str(exc)}, code=502)

    def _handle_brief(self, tickers: list[str]) -> None:
        try:
            result = asyncio.run(build_briefing(tickers))
            self._json(result)
        except UWError as exc:
            self._json({"error": str(exc)}, code=502)


def main() -> None:
    p = argparse.ArgumentParser(description="WhaleSignal web dashboard")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--demo", action="store_true", help="serve synthetic data, no API key")
    args = p.parse_args()
    if args.demo:
        os.environ[DEMO_ENV] = "1"  # settings reads this live

    mode = "DEMO" if settings.demo_mode else ("LIVE" if settings.has_key else "NO-KEY")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"WhaleSignal dashboard [{mode}] -> http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
