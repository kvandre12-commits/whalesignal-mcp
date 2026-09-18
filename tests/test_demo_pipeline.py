"""Integration tests: full analyze/rank pipeline via DemoClient (no key, no network).

These exercise the real fetch -> fuse -> score wiring in analysis.py, not just the
pure math in signals.py — using the deterministic DemoClient as a stand-in for the API.
Run with pytest (`pytest -q`) or standalone (`python tests/test_demo_pipeline.py`).
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["WHALESIGNAL_DEMO"] = "1"  # settings reads this live

from whalesignal.analysis import analyze_ticker, rank_tickers


def test_analyze_ticker_shape():
    result = asyncio.run(analyze_ticker("NVDA"))
    assert result["ticker"] == "NVDA"
    assert 0 <= result["conviction_score"] <= 100
    assert result["bias"] in {"bullish", "bearish", "neutral"}
    assert result["coverage"] == 1.0  # demo provides every signal
    assert len(result["subsignals"]) == 6
    assert result["rationale"]


def test_demo_is_deterministic():
    a = asyncio.run(analyze_ticker("TSLA"))
    b = asyncio.run(analyze_ticker("TSLA"))
    assert a["conviction_score"] == b["conviction_score"]


def test_rank_orders_by_score_desc():
    ranked = asyncio.run(rank_tickers(["NVDA", "AAPL", "TSLA", "AMZN", "MSFT"]))
    scores = [r["conviction_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert len(ranked) == 5


def test_rank_top_n():
    ranked = asyncio.run(rank_tickers(["NVDA", "AAPL", "TSLA", "AMZN"], top=2))
    assert len(ranked) == 2


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} integration tests passed")


if __name__ == "__main__":
    _run_all()
