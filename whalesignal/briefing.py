"""market_briefing: turn a pile of endpoints into a written, plain-English brief.

Separation of concerns:
  * ``summarize_*`` and ``compose_brief`` are PURE (take dicts/lists -> return values),
    so the interesting narrative logic is unit-tested with no key and no network.
  * ``build_briefing`` is the only async seam that fetches, then delegates to the pure bits.
"""
from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

from .analysis import analyze_ticker
from .client import make_client
from .config import bound_tickers, settings
from .signals import _num, _ratio_score, parse_amount  # reuse the same robust extractors

DEFAULT_WATCHLIST = [
    "NVDA", "AAPL", "TSLA", "AMZN", "MSFT", "META", "AMD", "GOOG", "SPY", "PLTR",
]


def _money(x: float) -> str:
    """Compact human money formatting: 1_250_000 -> $1.25M."""
    sign = "-" if x < 0 else ""
    a = abs(x)
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if a >= div:
            return f"{sign}${a / div:.2f}{unit}"
    return f"{sign}${a:.0f}"


# --- pure summarizers ----------------------------------------------------
def summarize_market_tide(ticks: list[dict]) -> dict[str, Any]:
    net_call = sum(_num(t, "net_call_premium", "call_premium") for t in ticks)
    net_put = sum(_num(t, "net_put_premium", "put_premium") for t in ticks)
    score = _ratio_score(max(net_call, 0.0) + max(-net_put, 0.0),
                         max(net_put, 0.0) + max(-net_call, 0.0))
    if score > 0.15:
        label = "risk-on / bullish"
    elif score < -0.15:
        label = "risk-off / bearish"
    else:
        label = "mixed / indecisive"
    return {
        "net_call_premium": net_call,
        "net_put_premium": net_put,
        "score": round(score, 3),
        "label": label,
    }


def summarize_congress(trades: list[dict], notable: int = 3) -> dict[str, Any]:
    buys = sells = 0
    sized: list[tuple[float, dict]] = []
    for t in trades:
        txn = str(t.get("txn_type", t.get("transaction_type", t.get("type", "")))).lower()
        amt = parse_amount(t)  # tolerates "$15,001 - $50,000" range strings
        if "purchase" in txn or "buy" in txn:
            buys += 1
        elif "sale" in txn or "sell" in txn:
            sells += 1
        sized.append((amt, t))
    sized.sort(key=lambda p: p[0], reverse=True)
    top = [
        {
            "ticker": str(t.get("ticker", t.get("ticker_symbol", "?"))).upper(),
            "type": str(t.get("txn_type", t.get("transaction_type", t.get("type", "?")))).title(),
            "amount": amt,
            "amount_label": str(t.get("amounts", _money(amt))),
        }
        for amt, t in sized[:notable]
    ]
    return {"total": len(trades), "buys": buys, "sells": sells, "notable": top}


def compose_brief(
    market: dict[str, Any],
    ranked: list[dict[str, Any]],
    congress: dict[str, Any],
    *,
    is_demo: bool,
    day: str,
) -> str:
    """Assemble the final human-readable briefing text."""
    lines: list[str] = []
    banner = "  [DEMO DATA - synthetic, not live]" if is_demo else ""
    lines.append(f"WhaleSignal Market Briefing - {day}{banner}")
    lines.append("=" * 56)

    # Market pulse
    lines.append(
        f"Market pulse: {market['label'].upper()}. "
        f"Net call premium {_money(market['net_call_premium'])}, "
        f"net put premium {_money(market['net_put_premium'])}."
    )

    bulls = [r for r in ranked if r.get("bias") == "bullish"]
    bears = [r for r in ranked if r.get("bias") == "bearish"]

    if bulls:
        lead = ", ".join(f"{r['ticker']} ({r['conviction_score']:.0f})" for r in bulls[:3])
        lines.append(f"Whales leaning bullish: {lead}.")
    if bears:
        lag = ", ".join(f"{r['ticker']} ({r['conviction_score']:.0f})" for r in bears[-3:])
        lines.append(f"Whales leaning bearish: {lag}.")
    if not bulls and not bears:
        lines.append("No standout directional conviction across the watchlist today.")

    # Single strongest name gets a one-liner rationale
    if ranked:
        star = ranked[0]
        why = "; ".join(star.get("rationale", [])[:2])
        lines.append(
            f"Top conviction: {star['ticker']} - {star['label']} "
            f"({star['conviction_score']:.1f}/100). {why}."
        )

    # Congress desk
    c = congress
    if c["total"]:
        notable = "; ".join(
            f"{n['type']} {n['ticker']} ({n.get('amount_label') or _money(n.get('amount', 0))})"
            for n in c["notable"]
        )
        lines.append(
            f"Congress desk: {c['buys']} buys vs {c['sells']} sells recently. "
            f"Notable: {notable}."
        )

    lines.append("-" * 56)
    lines.append("Not financial advice. Signals are heuristics over market data.")
    return "\n".join(lines)


# --- async orchestrator --------------------------------------------------
async def build_briefing(
    tickers: list[str] | None = None,
    top: int = 5,
) -> dict[str, Any]:
    watchlist = bound_tickers(tickers or DEFAULT_WATCHLIST)  # normalise + cap fan-out
    async with make_client() as client:
        tide, cong, *analyses = await asyncio.gather(
            client.market_tide(),
            client.congress_recent(),
            *(analyze_ticker(t, client=client) for t in watchlist),
        )

    ranked = sorted(analyses, key=lambda a: a["conviction_score"], reverse=True)
    market = summarize_market_tide(tide)
    congress = summarize_congress(cong)
    text = compose_brief(
        market, ranked, congress, is_demo=settings.demo_mode, day=str(date.today())
    )
    return {
        "text": text,
        "date": str(date.today()),
        "demo": settings.demo_mode,
        "market": market,
        "top": ranked[:top],
        "congress": congress,
    }
