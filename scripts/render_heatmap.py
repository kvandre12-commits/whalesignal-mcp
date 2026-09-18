"""Render the conviction heatmap to a real SVG from live /api/rank output.

This is NOT a mockup: it runs the same ``rank_tickers`` the web dashboard's
``/api/rank`` endpoint serves and draws each tile with the identical colour function
used in ``dashboard.html``. Use ``--demo`` (default) for synthetic data, or set
``UW_API_KEY`` and pass ``--live`` for real market data.

    python scripts/render_heatmap.py --demo -o docs/heatmap-demo.svg
"""
from __future__ import annotations

import argparse
import asyncio
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whalesignal.analysis import rank_tickers
from whalesignal.briefing import DEFAULT_WATCHLIST
from whalesignal.config import DEMO_ENV, settings

COLS = 5
TILE_W, TILE_H, GAP, PAD, TOP = 150, 92, 14, 22, 78


def _color(score: float) -> str:
    # identical logic to dashboard.html scoreColor()
    hue = round(score / 100 * 135)
    light = 26 + abs(score - 50) / 50 * 12
    return f"hsl({hue}, 55%, {light:.0f}%)"


def render_svg(rows: list[dict], demo: bool) -> str:
    n = len(rows)
    cols = min(COLS, max(n, 1))
    import math
    rows_n = math.ceil(n / cols)
    width = PAD * 2 + cols * TILE_W + (cols - 1) * GAP
    height = TOP + PAD + rows_n * TILE_H + (rows_n - 1) * GAP
    badge = "DEMO DATA" if demo else "LIVE"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="monospace">',
        f'<rect width="{width}" height="{height}" fill="#0b0f17"/>',
        f'<text x="{PAD}" y="34" fill="#e7edf7" font-size="22" font-weight="700">'
        f'<tspan fill="#4da3ff">Whale</tspan>Signal '
        f'<tspan fill="#8a97ac" font-size="15">Conviction Heatmap</tspan></text>',
        f'<rect x="{PAD}" y="48" width="96" height="20" rx="10" fill="#3a2a00" '
        f'stroke="#5a4400"/><text x="{PAD + 12}" y="62" fill="#ffcc66" '
        f'font-size="11">{badge}</text>',
    ]
    for i, r in enumerate(rows):
        cx = PAD + (i % cols) * (TILE_W + GAP)
        cy = TOP + PAD + (i // cols) * (TILE_H + GAP)
        score = float(r["conviction_score"])
        fill = _color(score)
        tkr = html.escape(str(r["ticker"]))
        lbl = html.escape(str(r["label"]))
        parts.append(
            f'<g><rect x="{cx}" y="{cy}" width="{TILE_W}" height="{TILE_H}" rx="12" '
            f'fill="{fill}" stroke="rgba(255,255,255,.10)"/>'
            f'<text x="{cx + 12}" y="{cy + 26}" fill="#fff" font-size="16" '
            f'font-weight="700">{tkr}</text>'
            f'<text x="{cx + 12}" y="{cy + 58}" fill="#fff" font-size="26" '
            f'font-weight="800">{score:.0f}</text>'
            f'<text x="{cx + 12}" y="{cy + 80}" fill="#f0f4fb" font-size="11">{lbl}</text>'
            f'</g>'
        )
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    p = argparse.ArgumentParser(description="Render WhaleSignal heatmap to SVG")
    p.add_argument("-o", "--out", default="docs/heatmap-demo.svg")
    p.add_argument("--tickers", nargs="*", default=list(DEFAULT_WATCHLIST))
    p.add_argument("--demo", action="store_true", default=True)
    p.add_argument("--live", dest="demo", action="store_false")
    args = p.parse_args()
    if args.demo:
        os.environ[DEMO_ENV] = "1"

    ranked = asyncio.run(rank_tickers(args.tickers))
    svg = render_svg(ranked, demo=settings.demo_mode)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(svg + "\n")
    print(f"wrote {args.out} ({len(ranked)} tiles, {'demo' if settings.demo_mode else 'live'})")


if __name__ == "__main__":
    main()
