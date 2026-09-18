"""Composite signal math — the actual value-add of WhaleSignal.

Every function here is PURE: it takes already-fetched Unusual Whales rows and returns
numbers. No network, no globals, no surprises. That makes the interesting logic unit
testable without an API key and keeps the MCP layer a thin adapter.

Sub-scores are all normalised to [-1, 1] where +1 = maximally bullish, -1 = maximally
bearish, 0 = neutral. The composite ``conviction`` maps the weighted blend to 0-100.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .config import ConvictionWeights


def _num(row: dict, *keys: str, default: float = 0.0) -> float:
    """Fetch the first present, numeric-coercible key from a row."""
    for k in keys:
        if k in row and row[k] is not None:
            try:
                return float(row[k])
            except (TypeError, ValueError):
                continue
    return default


def _str(row: dict, *keys: str, default: str = "") -> str:
    for k in keys:
        if k in row and row[k] is not None:
            return str(row[k]).lower()
    return default


def _ratio_score(bull: float, bear: float) -> float:
    """Map two competing magnitudes to a [-1, 1] score."""
    total = bull + bear
    if total <= 0:
        return 0.0
    return max(-1.0, min(1.0, (bull - bear) / total))


# --- individual sub-signals ---------------------------------------------
def flow_alert_score(alerts: Iterable[dict]) -> tuple[float, dict[str, Any]]:
    """Score directional conviction from unusual options flow alerts.

    Bullish = call premium hitting the ask + put premium on the bid.
    Bearish = put premium at the ask + call premium on the bid.
    """
    bull = bear = 0.0
    n = 0
    for a in alerts:
        n += 1
        prem = _num(a, "total_premium", "premium", "total_ask_side_prem", default=0.0)
        kind = _str(a, "type", "option_type", "put_call")
        is_call = kind.startswith("c") or bool(a.get("is_call"))
        is_put = kind.startswith("p") or bool(a.get("is_put"))
        side = _str(a, "side", "aggressor", "flow_side")
        ask_leaning = (
            "ask" in side
            or bool(a.get("has_sweep"))
            or _num(a, "ask_vol") > _num(a, "bid_vol")
        )
        weight = prem if prem > 0 else 1.0
        if is_call:
            if ask_leaning or side == "":
                bull += weight
            else:
                bear += weight * 0.5
        elif is_put:
            if ask_leaning or side == "":
                bear += weight
            else:
                bull += weight * 0.5
    score = _ratio_score(bull, bear)
    return score, {"alerts": n, "bull_premium": round(bull), "bear_premium": round(bear)}


def net_premium_score(ticks: Iterable[dict]) -> tuple[float, dict[str, Any]]:
    """Score from cumulative net call vs net put premium over the session."""
    net_call = net_put = 0.0
    for t in ticks:
        net_call += _num(t, "net_call_premium", "call_premium")
        net_put += _num(t, "net_put_premium", "put_premium")
    # Net put premium being *positive* means put buying (bearish), so it competes.
    score = _ratio_score(max(net_call, 0.0) + max(-net_put, 0.0),
                         max(net_put, 0.0) + max(-net_call, 0.0))
    return score, {"net_call_premium": round(net_call), "net_put_premium": round(net_put)}


def options_volume_score(rows: Iterable[dict]) -> tuple[float, dict[str, Any]]:
    """Score from call/put volume balance (a soft, high-level sentiment read)."""
    call_v = put_v = 0.0
    for r in rows:
        call_v += _num(r, "call_volume", "bullish_volume")
        put_v += _num(r, "put_volume", "bearish_volume")
    score = _ratio_score(call_v, put_v)
    pc = round(put_v / call_v, 3) if call_v else None
    return score, {"call_volume": round(call_v), "put_volume": round(put_v), "put_call_ratio": pc}


def dark_pool_score(prints: Iterable[dict]) -> tuple[float, dict[str, Any]]:
    """Estimate accumulation vs distribution from dark pool prints.

    Prints near/above the ask lean accumulation (bullish); near/below the bid lean
    distribution (bearish). Absent NBBO context, dark pool is treated as neutral
    interest and contributes little — honesty over false precision.
    """
    buy = sell = 0.0
    total_notional = 0.0
    n = 0
    for p in prints:
        n += 1
        price = _num(p, "price")
        size = _num(p, "size", "volume")
        notional = _num(p, "premium", default=price * size)
        total_notional += notional
        ask = _num(p, "nbbo_ask", "ask")
        bid = _num(p, "nbbo_bid", "bid")
        if ask and bid and price:
            mid = (ask + bid) / 2
            if price >= mid:
                buy += notional
            else:
                sell += notional
    score = _ratio_score(buy, sell)
    return score, {
        "prints": n,
        "notional": round(total_notional),
        "accumulation": round(buy),
        "distribution": round(sell),
    }


def gamma_score(strikes: Iterable[dict]) -> tuple[float, dict[str, Any]]:
    """Context signal from net dealer gamma.

    Net positive gamma => dealers dampen moves (mean-reverting, mildly constructive).
    Net negative gamma => dealers amplify moves (fragile). Reported small-weight.
    """
    net_gamma = 0.0
    for s in strikes:
        net_gamma += _num(s, "gamma", "gamma_exposure", "net_gamma")
    # Squash into [-1, 1] with a gentle sign-preserving transform.
    # Coarse but honest: we only trust the sign of net gamma, not its magnitude.
    score = 0.5 if net_gamma > 0 else (-0.5 if net_gamma < 0 else 0.0)
    regime = "positive" if net_gamma > 0 else "negative"
    return score, {"net_gamma": round(net_gamma), "regime": regime}


def congress_score(trades: Iterable[dict], ticker: str) -> tuple[float, dict[str, Any]]:
    """Score recent congressional trades for the ticker (buys bullish, sells bearish)."""
    buy = sell = 0.0
    n = 0
    tkr = ticker.upper()
    for t in trades:
        if _str(t, "ticker", "ticker_symbol").upper() != tkr:
            continue
        n += 1
        txn = _str(t, "transaction_type", "type", "txn_type")
        amt = _num(t, "amount", "amounts", default=1.0) or 1.0
        if "purchase" in txn or "buy" in txn:
            buy += amt
        elif "sale" in txn or "sell" in txn:
            sell += amt
    score = _ratio_score(buy, sell)
    return score, {"trades": n, "buys": round(buy), "sells": round(sell)}


# --- composite -----------------------------------------------------------
@dataclass
class SubSignal:
    name: str
    score: float
    weight: float
    detail: dict[str, Any]
    available: bool = True


@dataclass
class ConvictionResult:
    ticker: str
    score: float  # 0-100
    label: str
    bias: str  # bullish | bearish | neutral
    subsignals: list[SubSignal] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    coverage: float = 0.0  # fraction of signals with real data

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "conviction_score": self.score,
            "label": self.label,
            "bias": self.bias,
            "coverage": self.coverage,
            "subsignals": [
                {"name": s.name, "score": round(s.score, 3), "weight": round(s.weight, 3),
                 "available": s.available, "detail": s.detail}
                for s in self.subsignals
            ],
            "rationale": self.rationale,
        }


def _label(score: float) -> tuple[str, str]:
    if score >= 72:
        return "Strong Bullish", "bullish"
    if score >= 58:
        return "Bullish", "bullish"
    if score > 42:
        return "Neutral / Mixed", "neutral"
    if score > 28:
        return "Bearish", "bearish"
    return "Strong Bearish", "bearish"


def compute_conviction(
    ticker: str,
    subsignals: list[SubSignal],
    weights: ConvictionWeights | None = None,
) -> ConvictionResult:
    """Blend available sub-signals into a 0-100 conviction score.

    Weights are renormalised over only the *available* signals, so missing data
    degrades gracefully instead of silently dragging the score toward 50.
    """
    weights = weights or ConvictionWeights()
    available = [s for s in subsignals if s.available]
    total_w = sum(s.weight for s in available) or 1.0
    blended = sum(s.score * s.weight for s in available) / total_w  # [-1, 1]
    score_100 = round((blended + 1) * 50, 1)
    label, bias = _label(score_100)

    rationale: list[str] = []
    for s in sorted(available, key=lambda x: abs(x.score * x.weight), reverse=True):
        if abs(s.score) < 0.05:
            continue
        direction = "bullish" if s.score > 0 else "bearish"
        rationale.append(f"{s.name}: {direction} ({s.score:+.2f})")
    if not rationale:
        rationale.append("No strong directional signals — market is undecided on this name.")

    coverage = round(len(available) / max(len(subsignals), 1), 2)
    return ConvictionResult(
        ticker=ticker.upper(),
        score=score_100,
        label=label,
        bias=bias,
        subsignals=subsignals,
        rationale=rationale,
        coverage=coverage,
    )
