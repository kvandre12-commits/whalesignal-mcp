"""Configuration and constants — the single source of truth.

Everything that could vary (base URL, headers, timeouts, weights) lives here so the
rest of the codebase never hardcodes a magic string. Zen of Python: "There should be
one-- and preferably only one --obvious way to do it."
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()  # pull ~/uw-challenge/.env into the environment if present
except Exception:  # pragma: no cover - dotenv is optional at runtime
    pass

# --- Unusual Whales API contract (per official skill.md anti-hallucination rules) ---
BASE_URL = "https://api.unusualwhales.com"
CLIENT_API_ID = "100001"  # required UW-CLIENT-API-ID header
API_KEY_ENV = "UW_API_KEY"

# Every documented endpoint we touch. Keeping them named + centralised means a single
# typo can never spread, and we can assert against the official whitelist in tests.
ENDPOINTS = {
    "flow_alerts": "/api/option-trades/flow-alerts",
    "option_trades": "/api/option-trades",
    "screener": "/api/screener/option-contracts",
    "flow_recent": "/api/stock/{ticker}/flow-recent",
    "darkpool_ticker": "/api/darkpool/{ticker}",
    "darkpool_recent": "/api/darkpool/recent",
    "market_tide": "/api/market/market-tide",
    "net_prem_ticks": "/api/stock/{ticker}/net-prem-ticks",
    "greeks": "/api/stock/{ticker}/greeks",
    "gex_strike_static": "/api/stock/{ticker}/greek-exposure/strike",
    "gex_strike_spot": "/api/stock/{ticker}/spot-exposures/strike",
    "interpolated_iv": "/api/stock/{ticker}/interpolated-iv",
    "options_volume": "/api/stock/{ticker}/options-volume",
    "insider": "/api/insider/transactions",
    "congress": "/api/congress/recent-trades",
    "news": "/api/news/headlines",
}


@dataclass(frozen=True)
class ConvictionWeights:
    """Weights for the composite conviction score. Sum is normalised at runtime, so
    these are relative importances, not required to add to 1.0."""

    flow_alerts: float = 0.30
    net_premium: float = 0.28
    options_volume: float = 0.14
    dark_pool: float = 0.12
    gamma: float = 0.10
    congress: float = 0.06


@dataclass(frozen=True)
class Settings:
    api_key: str | None = field(default_factory=lambda: os.getenv(API_KEY_ENV))
    request_timeout: float = 20.0
    max_retries: int = 2
    weights: ConvictionWeights = field(default_factory=ConvictionWeights)

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)


settings = Settings()
