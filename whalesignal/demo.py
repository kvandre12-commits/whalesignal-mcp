"""DemoClient: deterministic synthetic data with the exact UWClient interface.

Lets WhaleSignal run end-to-end with no API key and no network - perfect for demos,
CI, and integration tests. It is a drop-in substitute for :class:`whalesignal.client.UWClient`
(same async methods), so :mod:`whalesignal.analysis` never knows the difference.

The synthetic rows use the SAME field names and shapes as the real Unusual Whales API
(verified against the official operation docs and captured in ``tests/fixtures``), so
demo mode drives the identical extractor/scoring code paths as live data.

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

    # --- flow (real fields: type, total_ask_side_prem, total_bid_side_prem) ----
    async def flow_alerts(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "flow")
        bias = _bias(ticker)
        out = []
        for _ in range(rng.randint(6, 18)):
            call = rng.random() < 0.5 + bias * 0.35
            ask = rng.randint(20_000, 800_000)
            bid = rng.randint(0, 80_000)
            out.append({
                "ticker": ticker.upper(),
                "type": "call" if call else "put",
                "total_premium": str(ask + bid),
                "total_ask_side_prem": str(ask),
                "total_bid_side_prem": str(bid),
                "total_size": rng.randint(200, 8_000),
                "has_sweep": rng.random() < 0.4,
            })
        return out

    async def net_prem_ticks(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "net")
        bias = _bias(ticker)
        out = []
        for _ in range(rng.randint(20, 40)):
            out.append({
                "net_call_premium": f"{rng.gauss(bias * 400_000, 300_000):.2f}",
                "net_put_premium": f"{rng.gauss(-bias * 250_000, 250_000):.2f}",
                "call_volume": rng.randint(500, 3_000),
                "put_volume": rng.randint(300, 2_000),
                "tape_time": "2025-03-21T19:58:00.000000Z",
            })
        return out

    async def options_volume(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "vol")
        bias = _bias(ticker)
        call_v = int(200_000 * (1 + bias) + rng.randint(0, 120_000))
        put_v = int(200_000 * (1 - bias) + rng.randint(0, 120_000))
        return [{
            "call_volume": max(call_v, 1),
            "put_volume": max(put_v, 1),
            "call_premium": str(max(call_v, 1) * 180),
            "put_premium": str(max(put_v, 1) * 170),
        }]

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
                "price": f"{price:.4f}",
                "size": size,
                "premium": f"{price * size:.2f}",
                "nbbo_ask": f"{ask:.2f}",
                "nbbo_bid": f"{bid:.2f}",
                "executed_at": "2025-05-02T13:42:12Z",
            })
        return out

    async def gex_by_strike(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "gex")
        bias = _bias(ticker)
        out = []
        for i in range(12):
            call_g = abs(rng.gauss(2e9, 1e9)) * (1 + bias)
            put_g = abs(rng.gauss(2e9, 1e9)) * (1 - bias)
            out.append({
                "price": str(100 + i * 5),
                "call_gamma_oi": f"{call_g:.2f}",
                "put_gamma_oi": f"{put_g:.2f}",
            })
        return out

    async def market_tide(self, **_: Any) -> list[dict]:
        rng = _seed("MARKET")
        out = []
        for i in range(30):
            out.append({
                "date": "2026-01-02",
                "timestamp": f"2026-01-02T{9 + i // 6:02d}:{(i % 6) * 10:02d}:00-05:00",
                "net_call_premium": f"{rng.gauss(220_000, 200_000):.4f}",
                "net_put_premium": f"{rng.gauss(-120_000, 180_000):.4f}",
                "net_volume": rng.randint(20_000, 90_000),
            })
        return out

    async def congress_recent(self, **_: Any) -> list[dict]:
        rng = _seed("CONGRESS")
        tickers = ["NVDA", "AAPL", "TSLA", "MSFT", "AMD", "PLTR", "SPY", "META"]
        ranges = [
            "$1,001 - $15,000", "$15,001 - $50,000",
            "$50,001 - $100,000", "$100,001 - $250,000",
        ]
        out = []
        for _ in range(rng.randint(15, 30)):
            out.append({
                "ticker": rng.choice(tickers),
                "txn_type": rng.choice(["Buy", "Sell", "Buy"]),
                "amounts": rng.choice(ranges),
                "transaction_date": "2026-01-02",
                "member_type": "house",
            })
        return out

    async def interpolated_iv(self, ticker: str, **_: Any) -> list[dict]:
        rng = _seed(ticker + "iv")
        return [{"iv": round(rng.uniform(0.2, 0.9), 4)}]
