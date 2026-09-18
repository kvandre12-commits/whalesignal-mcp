"""Real-response fixture tests - the live-compatibility evidence.

Fixtures in ``tests/fixtures/*.json`` are the exact example payloads published in the
official Unusual Whales operation docs (real field names, real envelopes, values as the
API returns them - including numeric-strings and range strings). Two layers:

1. Feed each fixture's rows straight into the pure signal functions and assert the math
   reads the REAL field names correctly.
2. Drive the actual ``UWClient`` against these payloads via ``httpx.MockTransport`` to
   prove auth headers + the ``data`` envelope unwrap work end-to-end - no network, no key.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whalesignal import signals as sig
from whalesignal.client import UWClient

FIX = Path(__file__).parent / "fixtures"


def _rows(name: str) -> list[dict]:
    return json.loads((FIX / f"{name}.json").read_text())["data"]


# --- Layer 1: real fields -> pure signals -------------------------------
def test_flow_alerts_real_ask_bid_split():
    # MSFT example: a call with ask-side prem 151875 >> bid-side 405 -> strongly bullish.
    score, detail = sig.flow_alert_score(_rows("flow_alerts"))
    assert score > 0.9, detail
    assert detail["alerts"] == 1
    assert detail["bull_premium"] > detail["bear_premium"]


def test_net_premium_real_fields():
    score, detail = sig.net_premium_score(_rows("net_prem_ticks"))
    assert score > 0  # positive net call premium, negative net put premium
    assert detail["net_call_premium"] > 0


def test_options_volume_real_fields():
    score, detail = sig.options_volume_score(_rows("options_volume"))
    assert score > 0  # call_volume 1,071,546 > put_volume 666,386
    assert detail["put_call_ratio"] is not None


def test_dark_pool_real_fields_run():
    score, detail = sig.dark_pool_score(_rows("darkpool_ticker"))
    assert -1.0 <= score <= 1.0
    assert detail["prints"] == 2
    assert detail["notional"] > 0  # premium strings parsed


def test_gamma_real_call_put_gamma_oi():
    score, detail = sig.gamma_score(_rows("gex_spot"))
    assert score in (-0.5, 0.0, 0.5)
    assert detail["regime"] in {"positive", "negative", "flat"}
    assert detail["net_gamma"] != 0  # proves call_gamma_oi/put_gamma_oi were read


def test_congress_real_txn_type_and_amount_range():
    # Fixture has one MSFT "Sell" with amounts "$1,000 - $15,000".
    score, detail = sig.congress_score(_rows("congress"), "MSFT")
    assert detail["trades"] == 1
    assert score < 0  # a sale is bearish
    assert detail["sells"] == 1000  # range string lower-bound parsed


def test_parse_amount_range_string():
    assert sig.parse_amount({"amounts": "$15,001 - $50,000"}) == 15001.0
    assert sig.parse_amount({"amount": 4200}) == 4200.0
    assert sig.parse_amount({"amounts": "not-disclosed"}) == 0.0


# --- Layer 2: real UWClient against real payloads via MockTransport ------
def _mock_transport(captured: dict) -> httpx.MockTransport:
    routes = {
        "/api/option-trades/flow-alerts": "flow_alerts",
        "/net-prem-ticks": "net_prem_ticks",
        "/options-volume": "options_volume",
        "/api/darkpool/": "darkpool_ticker",
        "/spot-exposures/strike": "gex_spot",
        "/api/market/market-tide": "market_tide",
        "/api/congress/recent-trades": "congress",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization")
        captured["client_id"] = request.headers.get("UW-CLIENT-API-ID")
        for frag, name in routes.items():
            if frag in request.url.path:
                return httpx.Response(200, json=json.loads((FIX / f"{name}.json").read_text()))
        return httpx.Response(404, json={"reason": "no fixture"})

    return httpx.MockTransport(handler)


def test_client_headers_and_envelope_unwrap():
    captured: dict = {}
    transport = _mock_transport(captured)

    async def run():
        async with UWClient(api_key="test-token", transport=transport) as c:
            alerts = await c.flow_alerts("MSFT")
            tide = await c.market_tide()
            gex = await c.gex_by_strike("SPY")
            return alerts, tide, gex

    alerts, tide, gex = asyncio.run(run())
    # Auth headers actually sent (anti-hallucination contract)
    assert captured["auth"] == "Bearer test-token"
    assert captured["client_id"] == "100001"
    # `data` envelope unwrapped into plain lists with real fields present
    assert isinstance(alerts, list) and "total_ask_side_prem" in alerts[0]
    assert "net_call_premium" in tide[0]
    assert "call_gamma_oi" in gex[0]


def test_client_feeds_signals_end_to_end():
    captured: dict = {}
    transport = _mock_transport(captured)

    async def run():
        async with UWClient(api_key="t", transport=transport) as c:
            return await c.flow_alerts("MSFT")

    score, _ = sig.flow_alert_score(asyncio.run(run()))
    assert score > 0.9  # real client -> real payload -> correct bullish read


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} fixture tests passed")


if __name__ == "__main__":
    _run_all()
