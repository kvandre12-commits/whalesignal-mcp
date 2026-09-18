"""Human-friendly CLI for demos — the same signals the MCP server serves, in your terminal.

Usage:
    python -m whalesignal.cli NVDA
    python -m whalesignal.cli NVDA AAPL TSLA --rank
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

from .analysis import analyze_ticker, rank_tickers
from .briefing import build_briefing
from .client import UWError
from .config import DEMO_ENV, settings

BAR_WIDTH = 30


def _bar(score_100: float) -> str:
    filled = int(round(score_100 / 100 * BAR_WIDTH))
    return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + f"] {score_100:.1f}/100"


def _print_report(a: dict) -> None:
    if "error" in a:
        print(f"  ! {a['error']}")
        return
    print(f"\n== {a['ticker']}  —  {a['label']}  ({a['bias'].upper()}) ==")
    print(f"   {_bar(a['conviction_score'])}   coverage {int(a['coverage'] * 100)}%")
    print("   sub-signals:")
    for s in a["subsignals"]:
        flag = " " if s["available"] else " (no data)"
        print(f"     - {s['name']:<20} {s['score']:+.2f}  w={s['weight']:.2f}{flag}")
    print("   why:")
    for r in a["rationale"]:
        print(f"     * {r}")


async def _main(tickers: list[str], rank: bool, top: int | None, brief: bool) -> int:
    if settings.demo_mode:
        print("** DEMO DATA ** (synthetic, deterministic per ticker \u2014 not live market data)")
    elif not settings.has_key:
        print("No UW_API_KEY set. Add it to ~/uw-challenge/.env, export it, or pass --demo.")
        return 2
    if brief:
        try:
            result = await build_briefing(tickers or None, top=top or 5)
            print("\n" + result["text"])
            return 0
        except UWError as exc:
            print(f"API error: {exc}")
            return 1
    try:
        if rank or len(tickers) > 1:
            ranked = await rank_tickers(tickers, top=top)
            print(f"\nWhaleSignal ranking ({len(ranked)} tickers, best first):")
            for i, a in enumerate(ranked, 1):
                if "error" in a:
                    print(f" {i}. {a['error']}")
                    continue
                print(f" {i}. {a['ticker']:<6} {a['conviction_score']:>5.1f}  {a['label']}")
            for a in ranked:
                _print_report(a)
        else:
            _print_report(await analyze_ticker(tickers[0]))
        return 0
    except UWError as exc:
        print(f"API error: {exc}")
        return 1


def main() -> None:
    p = argparse.ArgumentParser(description="WhaleSignal conviction analysis")
    p.add_argument("tickers", nargs="*", help="ticker symbols (optional with --brief)")
    p.add_argument("--brief", action="store_true", help="print a written market briefing")
    p.add_argument("--rank", action="store_true", help="force ranked comparison output")
    p.add_argument("--top", type=int, default=None, help="only show the top N")
    p.add_argument("--demo", action="store_true", help="run on synthetic data, no API key needed")
    args = p.parse_args()
    if args.demo:
        os.environ[DEMO_ENV] = "1"  # settings reads this live
    if not args.tickers and not args.brief:
        p.error("provide at least one ticker, or use --brief")
    tickers = [t.upper() for t in args.tickers]
    sys.exit(asyncio.run(_main(tickers, args.rank, args.top, args.brief)))


if __name__ == "__main__":
    main()
