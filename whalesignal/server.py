"""WhaleSignal MCP server.

Exposes composite, decision-ready market-intelligence tools over the Model Context
Protocol. Point any MCP client (Claude Desktop, Cursor, VS Code, ChatGPT, ...) at this
server and ask, in plain English, "what's the conviction on NVDA?".

Run:  python -m whalesignal.server         (stdio transport, for MCP clients)
"""
from __future__ import annotations

from typing import Any

# Compat shim: mcp 1.x exposes FastMCP; mcp 2.x renamed it to MCPServer. Both share the
# same name/instructions/.tool()/.run() surface we rely on, so we bind whichever exists.
try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # pragma: no cover - mcp 1.x fallback
    from mcp.server.fastmcp import FastMCP as _Server

from .analysis import analyze_ticker, rank_tickers
from .briefing import build_briefing
from .client import UWError, make_client
from .config import settings

mcp = _Server(
    "WhaleSignal",
    instructions=(
        "WhaleSignal fuses Unusual Whales options flow, net premium, dark pool, gamma "
        "exposure and congressional trades into explainable conviction signals. Use "
        "`conviction_score` for a single ticker, `rank_watchlist` to compare several, "
        "and the raw tools for drill-downs. Scores are 0-100 (50 = neutral)."
    ),
)


def _need_key() -> str | None:
    if settings.has_key or settings.demo_mode:
        return None
    return (
        "No Unusual Whales API key configured. Set UW_API_KEY in the environment or in "
        "~/uw-challenge/.env, or run with WHALESIGNAL_DEMO=1 for synthetic demo data."
    )


@mcp.tool()
async def conviction_score(ticker: str) -> dict[str, Any]:
    """Composite 0-100 bullish/bearish conviction for a ticker.

    Fuses options flow alerts, net premium, call/put volume, dark pool accumulation,
    dealer gamma regime and recent congressional trades into one explainable score
    with per-signal breakdown and a plain-English rationale.
    """
    if (err := _need_key()):
        return {"error": err}
    try:
        return await analyze_ticker(ticker)
    except UWError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def rank_watchlist(tickers: list[str], top: int | None = None) -> dict[str, Any]:
    """Rank a watchlist of tickers by WhaleSignal conviction score (highest first)."""
    if (err := _need_key()):
        return {"error": err}
    if not tickers:
        return {"error": "Provide at least one ticker."}
    try:
        ranked = await rank_tickers([t.upper() for t in tickers], top=top)
        return {"count": len(ranked), "ranking": ranked}
    except UWError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def market_briefing(tickers: list[str] | None = None, top: int = 5) -> dict[str, Any]:
    """One-call plain-English daily market brief.

    Blends Market Tide sentiment, WhaleSignal conviction ranking over a watchlist,
    and notable congressional trades into a written narrative plus structured data.
    Pass your own `tickers` list or use the default liquid-name watchlist.
    """
    if (err := _need_key()):
        return {"error": err}
    try:
        return await build_briefing(tickers, top=top)
    except UWError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def flow_alerts(ticker: str, min_premium: int = 50_000, limit: int = 25) -> dict[str, Any]:
    """Raw unusual options flow alerts for a ticker (whale trades)."""
    if (err := _need_key()):
        return {"error": err}
    try:
        async with make_client() as c:
            data = await c.flow_alerts(ticker, min_premium=min_premium, limit=limit)
        return {"ticker": ticker.upper(), "count": len(data), "alerts": data}
    except UWError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def dark_pool(ticker: str, limit: int = 25) -> dict[str, Any]:
    """Recent dark pool prints for a ticker."""
    if (err := _need_key()):
        return {"error": err}
    try:
        async with make_client() as c:
            data = await c.darkpool(ticker, limit=limit)
        return {"ticker": ticker.upper(), "count": len(data), "prints": data}
    except UWError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def market_pulse() -> dict[str, Any]:
    """Overall market sentiment from Unusual Whales Market Tide (net premium flow)."""
    if (err := _need_key()):
        return {"error": err}
    try:
        async with make_client() as c:
            data = await c.market_tide()
        latest = data[-1] if data else {}
        return {"points": len(data), "latest": latest}
    except UWError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def congress_trades(ticker: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Recent congressional trades, optionally filtered to one ticker."""
    if (err := _need_key()):
        return {"error": err}
    try:
        async with make_client() as c:
            data = await c.congress_recent(limit=limit)
        if ticker:
            tkr = ticker.upper()
            data = [
                d for d in data
                if str(d.get("ticker", d.get("ticker_symbol", ""))).upper() == tkr
            ]
        return {"count": len(data), "trades": data}
    except UWError as exc:
        return {"error": str(exc)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
