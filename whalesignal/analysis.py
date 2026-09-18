"""Orchestration: fetch many endpoints concurrently, then feed pure signal math.

This is the only place that combines I/O (client) with logic (signals). Failure policy:
  * A 401 (authentication failure) is re-raised so the whole analysis surfaces an
    error - we never fake a neutral score when the token is bad. "The score never lies."
  * A 403 (route not permitted for this token) or a transient failure drops just that
    one sub-signal (marked unavailable); the rest of the analysis proceeds.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Any

from . import signals as sig
from .client import UWClient, UWError, make_client
from .config import ConvictionWeights, bound_tickers, settings

# Shared congress payload passed into analyze_ticker: (rows, available).
Shared = tuple[list[dict], bool]


async def _safe(coro: Awaitable[list[dict]]) -> tuple[list[dict], bool]:
    """Await a fetch. Re-raise auth (401) errors; swallow everything else.

    Returning ([], False) marks the sub-signal unavailable for 403/transient failures,
    but a 401 must never be silently turned into a neutral score.
    """
    try:
        return await coro, True
    except UWError as exc:
        if exc.is_auth:
            raise
        return [], False
    except Exception:
        return [], False


async def analyze_ticker(
    ticker: str,
    client: UWClient | None = None,
    weights: ConvictionWeights | None = None,
    congress: Shared | None = None,
) -> dict[str, Any]:
    """Full conviction analysis for one ticker across all fused datasets.

    ``congress`` lets a batch caller fetch the (ticker-agnostic) congressional feed
    once and share it across every ticker instead of refetching it N times.
    """
    weights = weights or settings.weights
    owns_client = client is None
    client = client or make_client()
    if owns_client:
        await client.__aenter__()
    try:
        tasks = [
            _safe(client.flow_alerts(ticker)),
            _safe(client.net_prem_ticks(ticker)),
            _safe(client.options_volume(ticker)),
            _safe(client.darkpool(ticker)),
            _safe(client.gex_by_strike(ticker)),
        ]
        if congress is None:
            tasks.append(_safe(client.congress_recent()))
        results = await asyncio.gather(*tasks)
    finally:
        if owns_client:
            await client.__aexit__(None, None, None)

    (flow, ok_flow), (net, ok_net), (vol, ok_vol), (dp, ok_dp), (gex, ok_gex) = results[:5]
    cong, ok_cong = results[5] if congress is None else congress

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
    """Analyze several tickers concurrently and rank by conviction score.

    Congress data is ticker-agnostic, so we fetch it once and share it across the
    batch (instead of N redundant calls). The client caps overall concurrency.
    """
    tickers = bound_tickers(tickers)  # normalise + enforce MAX_TICKERS
    async with make_client() as client:
        congress = await _safe(client.congress_recent())  # fetch once, share
        analyses = await asyncio.gather(
            *(analyze_ticker(t, client=client, congress=congress) for t in tickers)
        )
    ranked = sorted(analyses, key=lambda a: a["conviction_score"], reverse=True)
    return ranked[:top] if top else ranked
