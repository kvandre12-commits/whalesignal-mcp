"""Tests for the web layer that need no sockets: ticker parsing + asset presence."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whalesignal import web
from whalesignal.briefing import DEFAULT_WATCHLIST


def test_html_asset_loads():
    assert "<!DOCTYPE html>" in web._HTML
    assert "WhaleSignal" in web._HTML
    assert "/api/rank" in web._HTML  # front-end talks to the right endpoint


def test_parse_tickers_space_and_comma():
    assert web._parse_tickers("tickers=nvda%20aapl") == ["NVDA", "AAPL"]
    assert web._parse_tickers("tickers=nvda,aapl,tsla") == ["NVDA", "AAPL", "TSLA"]


def test_parse_tickers_defaults_when_empty():
    assert web._parse_tickers("") == list(DEFAULT_WATCHLIST)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} web tests passed")


if __name__ == "__main__":
    _run_all()
