"""Pure-logic tests for WhaleSignal — no API key, no network required.

Run with pytest (`pytest -q`) or standalone (`python tests/test_signals.py`).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whalesignal import signals as sig  # noqa: E402


def test_flow_alerts_bullish_when_calls_dominate():
    alerts = [
        {"type": "call", "total_premium": 500_000, "side": "ask"},
        {"type": "call", "total_premium": 300_000, "has_sweep": True},
        {"type": "put", "total_premium": 50_000, "side": "bid"},
    ]
    score, detail = sig.flow_alert_score(alerts)
    assert score > 0.4, detail
    assert detail["alerts"] == 3


def test_flow_alerts_bearish_when_puts_dominate():
    alerts = [
        {"type": "put", "total_premium": 800_000, "side": "ask"},
        {"type": "call", "total_premium": 100_000, "side": "bid"},
    ]
    score, _ = sig.flow_alert_score(alerts)
    assert score < -0.3


def test_net_premium_score_directional():
    bullish = [{"net_call_premium": 1_000_000, "net_put_premium": -200_000}]
    bearish = [{"net_call_premium": -500_000, "net_put_premium": 900_000}]
    assert sig.net_premium_score(bullish)[0] > 0.3
    assert sig.net_premium_score(bearish)[0] < -0.3


def test_options_volume_put_call_ratio():
    rows = [{"call_volume": 300_000, "put_volume": 100_000}]
    score, detail = sig.options_volume_score(rows)
    assert score > 0
    assert detail["put_call_ratio"] == round(100_000 / 300_000, 3)


def test_dark_pool_accumulation_vs_distribution():
    prints = [
        {"price": 101, "size": 10_000, "nbbo_ask": 101, "nbbo_bid": 100, "premium": 1_010_000},
        {"price": 100, "size": 5_000, "nbbo_ask": 101, "nbbo_bid": 100, "premium": 500_000},
    ]
    score, detail = sig.dark_pool_score(prints)
    assert score > 0  # first print at ask (buy) outweighs second at bid
    assert detail["prints"] == 2


def test_congress_score_filters_by_ticker():
    trades = [
        {"ticker": "NVDA", "transaction_type": "Purchase", "amount": 50_000},
        {"ticker": "NVDA", "transaction_type": "Sale", "amount": 10_000},
        {"ticker": "AAPL", "transaction_type": "Sale", "amount": 999_999},
    ]
    score, detail = sig.congress_score(trades, "NVDA")
    assert detail["trades"] == 2
    assert score > 0


def test_conviction_blends_and_labels():
    subs = [
        sig.SubSignal("options_flow_alerts", 0.8, 0.30, {}, True),
        sig.SubSignal("net_premium", 0.6, 0.28, {}, True),
        sig.SubSignal("options_volume", 0.4, 0.14, {}, True),
        sig.SubSignal("dark_pool", 0.0, 0.12, {}, False),  # unavailable -> ignored
    ]
    res = sig.compute_conviction("NVDA", subs)
    assert res.ticker == "NVDA"
    assert res.score > 60
    assert res.bias == "bullish"
    assert res.coverage == 0.75
    assert res.rationale  # non-empty


def test_conviction_neutral_when_no_signal():
    subs = [sig.SubSignal("options_flow_alerts", 0.0, 0.30, {}, True)]
    res = sig.compute_conviction("SPY", subs)
    assert 45 <= res.score <= 55
    assert res.bias == "neutral"


def _run_all():
    fns = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} tests passed")


if __name__ == "__main__":
    _run_all()
