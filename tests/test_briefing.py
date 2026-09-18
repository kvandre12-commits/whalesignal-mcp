"""Pure-logic tests for the market briefing composer (no key, no network)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whalesignal import briefing as b  # noqa: E402


def test_money_formatting():
    assert b._money(1_250_000) == "$1.25M"
    assert b._money(2_000_000_000) == "$2.00B"
    assert b._money(-500_000) == "-$500.00K"
    assert b._money(42) == "$42"


def test_summarize_market_tide_bullish():
    ticks = [{"net_call_premium": 1_000_000, "net_put_premium": 100_000}]
    s = b.summarize_market_tide(ticks)
    assert s["score"] > 0.15
    assert "bullish" in s["label"]


def test_summarize_market_tide_bearish():
    ticks = [{"net_call_premium": -200_000, "net_put_premium": 900_000}]
    s = b.summarize_market_tide(ticks)
    assert s["score"] < -0.15
    assert "bearish" in s["label"]


def test_summarize_congress_counts_and_notable():
    trades = [
        {"ticker": "NVDA", "transaction_type": "Purchase", "amount": 250_000},
        {"ticker": "AAPL", "transaction_type": "Sale", "amount": 15_000},
        {"ticker": "TSLA", "transaction_type": "Purchase", "amount": 100_000},
    ]
    s = b.summarize_congress(trades, notable=2)
    assert s["total"] == 3
    assert s["buys"] == 2 and s["sells"] == 1
    assert s["notable"][0]["ticker"] == "NVDA"  # largest first
    assert len(s["notable"]) == 2


def test_compose_brief_contains_key_sections():
    market = {"net_call_premium": 3_000_000, "net_put_premium": 900_000,
              "score": 0.4, "label": "risk-on / bullish"}
    ranked = [
        {"ticker": "AMZN", "bias": "bullish", "conviction_score": 88.0,
         "label": "Strong Bullish", "rationale": ["net_premium: bullish (+1.00)"]},
        {"ticker": "NVDA", "bias": "bearish", "conviction_score": 18.0,
         "label": "Strong Bearish", "rationale": ["net_premium: bearish (-1.00)"]},
    ]
    congress = {"total": 5, "buys": 3, "sells": 2,
                "notable": [{"ticker": "NVDA", "type": "Purchase", "amount": 250_000}]}
    text = b.compose_brief(market, ranked, congress, is_demo=True, day="2026-01-01")
    assert "Market Briefing" in text
    assert "DEMO DATA" in text
    assert "AMZN" in text and "NVDA" in text
    assert "Congress desk" in text
    assert "Not financial advice" in text


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} briefing tests passed")


if __name__ == "__main__":
    _run_all()
