"""DemoClient: deterministic synthetic data with the exact UWClient interface.

Lets WhaleSignal run end-to-end with no API key and no network — perfect for demos,
CI, and integration tests. It is a drop-in substitute for :class:`whalesignal.client.UWClient`
(same async methods), so :mod:`whalesignal.analysis` never knows the difference.

Data is seeded from the ticker symbol, so every symbol has a stable "personality"
(some lean bullish, some bearish) and results are reproducible run-to-run.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any


def _seed(ticker: str) -> random.Random:
    # md5 gives a well-distributed seed so ticker biases spread across the range
    # instead of clustering (a plain char-sum hash collides badly for similar symbols).
    digest = hashlib.md5(ticker.upper().encode()).hexdigest()
    return random.Random(int(digest, 16))


def _bias(ticker: str) -> float:
    """A stable per-ticker directional lean in roughly [-1, 1]."""
    rng = _seed(ticker)
    return round(rng.uniform(-1.0, 1.0), 3)


class DemoClient:
    """Async, context-managed, and interface-compatible with UWClient."""

    IS_DEMO = True

    def __init__(self, *_: Any, **__: Any) -> None:
        pass

    async def __aenter__(self) -> DemoClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    # --- flow ---------------------------------------------------------
    async def flow_alerts(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "flow")
        bias = _bias(ticker)
        out = []
        for _ in range(rng.randint(6, 18)):
            call = rng.random() < 0.5 + bias * 0.35
            out.append({
                "ticker": ticker.upper(),
                "type": "call" if call else "put",
                "total_premium": rng.randint(30_000, 900_000),
                "total_size": rng.randint(200, 8_000),
                "side": rng.choice(["ask", "ask", "bid"]) if call == (bias > 0) else "bid",
                "has_sweep": rng.random() < 0.4,
            })
        return out

    async def net_prem_ticks(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "net")
        bias = _bias(ticker)
        out = []
        for _ in range(rng.randint(20, 40)):
            out.append({
                "net_call_premium": int(rng.gauss(bias * 400_000, 300_000)),
                "net_put_premium": int(rng.gauss(-bias * 250_000, 250_000)),
            })
        return out

    async def options_volume(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "vol")
        bias = _bias(ticker)
        call_v = int(200_000 * (1 + bias) + rng.randint(0, 120_000))
        put_v = int(200_000 * (1 - bias) + rng.randint(0, 120_000))
        return [{"call_volume": max(call_v, 1), "put_volume": max(put_v, 1)}]

    async def darkpool(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "dp")
        bias = _bias(ticker)
        base = rng.uniform(20, 500)
        out = []
        for _ in range(rng.randint(8, 25)):
            ask, bid = base * 1.001, base * 0.999
            price = ask if rng.random() < 0.5 + bias * 0.3 else bid
            size = rng.randint(5_000, 60_000)
            out.append({
                "ticker": ticker.upper(),
                "price": round(price, 2),
                "size": size,
                "premium": round(price * size, 2),
                "nbbo_ask": round(ask, 2),
                "nbbo_bid": round(bid, 2),
            })
        return out

    async def gex_by_strike(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "gex")
        bias = _bias(ticker)
        out = []
        for i in range(12):
            gamma = rng.gauss(bias * 2e8, 4e8)
            out.append({"strike": 100 + i * 5, "gamma": gamma})
        return out

    async def market_tide(self, **_: Any) -> list[dict]:
        rng = _seed("MARKET")
        out = []
        for i in range(30):
            out.append({
                "timestamp": f"2026-01-01T{9 + i // 6:02d}:{(i % 6) * 10:02d}:00Z",
                "net_call_premium": int(rng.gauss(120_000, 200_000)),
                "net_put_premium": int(rng.gauss(80_000, 180_000)),
            })
        return out

    async def congress_recent(self, **_: Any) -> list[dict]:
        rng = _seed("CONGRESS")
        tickers = ["NVDA", "AAPL", "TSLA", "MSFT", "AMD", "PLTR", "SPY", "META"]
        out = []
        for _ in range(rng.randint(15, 30)):
            t = rng.choice(tickers)
            out.append({
                "ticker": t,
                "transaction_type": rng.choice(["Purchase", "Sale", "Purchase"]),
                "amount": rng.choice([15_000, 50_000, 100_000, 250_000]),
            })
        return out

    async def interpolated_iv(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "iv")
        return [{"iv": round(rng.uniform(0.2, 0.9), 4)}]
