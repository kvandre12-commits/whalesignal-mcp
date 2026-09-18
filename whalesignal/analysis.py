"""Orchestration: fetch many endpoints concurrently, then feed pure signal math.

This is the only place that combines I/O (client) with logic (signals). If a single
endpoint errors out we mark that sub-signal unavailable and carry on — one flaky route
should never sink the whole analysis.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Any

from . import signals as sig
from .client import UWClient, make_client
from .config import ConvictionWeights, bound_tickers, settings


async def _safe(coro: Awaitable[list[dict]]) -> tuple[list[dict], bool]:
    """Await a fetch, returning ([], False) on any failure."""
    try:
        return await coro, True
    except Exception:
        return [], False


async def analyze_ticker(
    ticker: str,
    client: UWClient | None = None,
    weights: ConvictionWeights | None = None,
) -> dict[str, Any]:
    """Full conviction analysis for one ticker across all fused datasets."""
    weights = weights or settings.weights
    owns_client = client is None
    client = client or make_client()
    if owns_client:
        await client.__aenter__()
    try:
        results = await asyncio.gather(
            _safe(client.flow_alerts(ticker)),
            _safe(client.net_prem_ticks(ticker)),
            _safe(client.options_volume(ticker)),
            _safe(client.darkpool(ticker)),
            _safe(client.gex_by_strike(ticker)),
            _safe(client.congress_recent()),
        )
    finally:
        if owns_client:
            await client.__aexit__(None, None, None)

    ((flow, ok_flow), (net, ok_net), (vol, ok_vol),
     (dp, ok_dp), (gex, ok_gex), (cong, ok_cong)) = results

    builders: list[tuple[str, float, tuple[float, dict], bool]] = [
        ("options_flow_alerts", weights.flow_alerts,
         sig.flow_alert_score(flow), ok_flow and bool(flow)),
        ("net_premium", weights.net_premium,
         sig.net_premium_score(net), ok_net and bool(net)),
        ("options_volume", weights.options_volume,
         sig.options_volume_score(vol), ok_vol and bool(vol)),
        ("dark_pool", weights.dark_pool, sig.dark_pool_score(dp), ok_dp and bool(dp)),
        ("gamma_regime", weights.gamma, sig.gamma_score(gex), ok_gex and bool(gex)),
        ("congress", weights.congress, sig.congress_score(cong, ticker), ok_cong),
    ]

    subsignals = [
        sig.SubSignal(name=name, score=score_detail[0], weight=weight,
                      detail=score_detail[1], available=available)
        for name, weight, score_detail, available in builders
    ]
    result = sig.compute_conviction(ticker, subsignals, weights)
    return result.to_dict()


async def rank_tickers(
    tickers: list[str],
    top: int | None = None,
) -> list[dict[str, Any]]:
    """Analyze several tickers concurrently and rank by conviction score."""
    tickers = bound_tickers(tickers)  # normalise + enforce MAX_TICKERS
    async with make_client() as client:
        analyses = await asyncio.gather(
            *(analyze_ticker(t, client=client) for t in tickers)
        )
    ranked = sorted(analyses, key=lambda a: a["conviction_score"], reverse=True)
    return ranked[:top] if top else ranked
