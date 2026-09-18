"""Failure-mode and correctness tests (no key, no network).

Covers the three v0.1.2 fixes:
  * 401 auth failures propagate (never faked into a neutral score).
  * 403 / transient failures drop only that one sub-signal.
  * cumulative series (net premium, market tide) use the LATEST snapshot, not a sum.
  * shared congress payload skips the per-ticker congress call.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whalesignal import briefing as brief
from whalesignal import signals as sig
from whalesignal.analysis import analyze_ticker
from whalesignal.client import UWClient, UWError

FIX = Path(__file__).parent / "fixtures"
_FIX_ROUTES = {
    "/api/option-trades/flow-alerts": "flow_alerts",
    "/net-prem-ticks": "net_prem_ticks",
    "/options-volume": "options_volume",
    "/api/darkpool/": "darkpool_ticker",
    "/spot-exposures/strike": "gex_spot",
    "/api/congress/recent-trades": "congress",
}


def _serve(path: str) -> httpx.Response:
    for frag, name in _FIX_ROUTES.items():
        if frag in path:
            return httpx.Response(200, json=json.loads((FIX / f"{name}.json").read_text()))
    return httpx.Response(200, json={"data": []})


def test_auth_401_propagates_not_neutral():
    # Every endpoint returns 401 -> analyze_ticker must RAISE, not return 50/neutral.
    transport = httpx.MockTransport(
        lambda r: httpx.Response(401, json={"reason": "unrecognized_token"})
    )

    async def run():
        async with UWClient(api_key="bad", transport=transport) as c:
            return await analyze_ticker("NVDA", client=c)

    raised_auth = False
    try:
        asyncio.run(run())
    except UWError as exc:
        raised_auth = exc.is_auth
    assert raised_auth, "401 should surface as an auth error, never a fake neutral score"


def test_403_drops_only_that_signal():
    # flow-alerts is permission-gated (403); the rest succeed and analysis completes.
    def handler(r: httpx.Request) -> httpx.Response:
        if "/flow-alerts" in r.url.path:
            return httpx.Response(403, json={"reason": "route_not_permitted"})
        return _serve(r.url.path)

    async def run():
        async with UWClient(api_key="ok", transport=httpx.MockTransport(handler)) as c:
            return await analyze_ticker("MSFT", client=c)

    result = asyncio.run(run())
    subs = {s["name"]: s for s in result["subsignals"]}
    assert subs["options_flow_alerts"]["available"] is False  # dropped
    assert subs["net_premium"]["available"] is True           # others fine
    assert 0 <= result["coverage"] < 1.0


def test_shared_congress_skips_endpoint():
    hits = {"congress": 0}

    def handler(r: httpx.Request) -> httpx.Response:
        if "/congress/recent-trades" in r.url.path:
            hits["congress"] += 1
        return _serve(r.url.path)

    async def run():
        async with UWClient(api_key="ok", transport=httpx.MockTransport(handler)) as c:
            # congress supplied -> analyze_ticker must NOT call the congress endpoint
            return await analyze_ticker("MSFT", client=c, congress=([], True))

    asyncio.run(run())
    assert hits["congress"] == 0


def test_net_premium_uses_latest_not_sum():
    ticks = [
        {"tape_time": "2026-01-02T14:00:00Z",
         "net_call_premium": "100", "net_put_premium": "-50"},
        {"tape_time": "2026-01-02T14:05:00Z",
         "net_call_premium": "5000", "net_put_premium": "-200"},
    ]
    _, detail = sig.net_premium_score(ticks)
    assert detail["net_call_premium"] == 5000  # latest, not 5100 (sum)
    assert detail["as_of"] == "2026-01-02T14:05:00Z"


def test_market_tide_uses_latest_not_sum():
    ticks = [
        {"timestamp": "2026-01-02T09:30:00-05:00",
         "net_call_premium": "100000", "net_put_premium": "-50000"},
        {"timestamp": "2026-01-02T16:00:00-05:00",
         "net_call_premium": "900000", "net_put_premium": "-400000"},
    ]
    market = brief.summarize_market_tide(ticks)
    assert market["net_call_premium"] == 900000  # latest snapshot only


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} robustness tests passed")


if __name__ == "__main__":
    _run_all()
