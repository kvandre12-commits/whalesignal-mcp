"""Async Unusual Whales API client.

Thin, correct, and boring on purpose — it only knows how to authenticate, make GET
requests (the API is 100% GET), retry transient failures, and unwrap the ``data``
envelope. All cleverness lives in :mod:`whalesignal.signals`.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import BASE_URL, CLIENT_API_ID, ENDPOINTS, settings


class UWError(RuntimeError):
    """Raised when the Unusual Whales API returns an unrecoverable error.

    ``status`` carries the HTTP status when known. Callers distinguish:
      * 401 -> authentication failure (fatal; never degrade to a neutral signal)
      * 403 -> route not permitted for this token (a single signal may be dropped)
      * other/None -> transient or unexpected failure (signal may be dropped)
    """

    def __init__(self, message: str, *, status: int | None = None,
                 reason: str | None = None, retryable: bool = False) -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason
        self.retryable = retryable

    @property
    def is_auth(self) -> bool:
        """True for a 401 - a hard authentication failure that must surface."""
        return self.status == 401


class UWClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        concurrency: int | None = None,
    ) -> None:
        self._api_key = api_key or settings.api_key
        self._timeout = timeout or settings.request_timeout
        self._transport = transport  # inject httpx.MockTransport in tests
        self._client: httpx.AsyncClient | None = None
        # Bounds simultaneous upstream requests regardless of how many tickers
        # are being analysed in parallel (protects your rate limit).
        self._sem = asyncio.Semaphore(concurrency or settings.max_concurrency)

    # --- lifecycle -------------------------------------------------------
    async def __aenter__(self) -> UWClient:
        if not self._api_key:
            raise UWError(
                "No API key. Set UW_API_KEY in your environment or ~/uw-challenge/.env"
            )
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=self._timeout,
            transport=self._transport,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "UW-CLIENT-API-ID": CLIENT_API_ID,
                "Accept": "application/json",
                "User-Agent": "WhaleSignal-MCP/0.1",
            },
        )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # --- core request ----------------------------------------------------
    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET ``path`` and return the parsed JSON body (whole envelope)."""
        if self._client is None:  # allow use without context manager too
            async with self as bound:
                return await bound.get(path, params)

        last_exc: Exception | None = None
        async with self._sem:  # cap concurrent upstream requests
            for attempt in range(settings.max_retries + 1):
                try:
                    resp = await self._client.get(path, params=_clean_params(params))
                    if resp.status_code == 429:  # rate limited — back off and retry
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    if resp.status_code in (401, 403):
                        reason = _safe_reason(resp)
                        raise UWError(
                            f"Auth failed ({resp.status_code}): {reason}",
                            status=resp.status_code, reason=reason, retryable=False,
                        )
                    resp.raise_for_status()
                    return resp.json()
                except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                    last_exc = exc
                    if attempt < settings.max_retries:
                        await asyncio.sleep(0.6 * (attempt + 1))
                        continue
        status = getattr(getattr(last_exc, "response", None), "status_code", None)
        raise UWError(f"Request to {path} failed: {last_exc}", status=status, retryable=True)

    async def data(self, path: str, params: dict[str, Any] | None = None) -> list[dict]:
        """GET and unwrap the ``data`` list (the common UW response shape)."""
        body = await self.get(path, params)
        if isinstance(body, dict):
            payload = body.get("data", body)
        else:
            payload = body
        if isinstance(payload, dict):
            return [payload]
        return list(payload or [])

    # --- named endpoint helpers (typed sugar over ENDPOINTS) -------------
    async def flow_alerts(self, ticker: str, **params: Any) -> list[dict]:
        params.setdefault("ticker_symbol", ticker.upper())
        params.setdefault("limit", 200)
        return await self.data(ENDPOINTS["flow_alerts"], params)

    async def net_prem_ticks(self, ticker: str, **params: Any) -> list[dict]:
        return await self.data(_fmt("net_prem_ticks", ticker), params)

    async def options_volume(self, ticker: str, **params: Any) -> list[dict]:
        return await self.data(_fmt("options_volume", ticker), params)

    async def darkpool(self, ticker: str, **params: Any) -> list[dict]:
        params.setdefault("limit", 100)
        return await self.data(_fmt("darkpool_ticker", ticker), params)

    async def gex_by_strike(self, ticker: str, **params: Any) -> list[dict]:
        return await self.data(_fmt("gex_strike_spot", ticker), params)

    async def market_tide(self, **params: Any) -> list[dict]:
        return await self.data(ENDPOINTS["market_tide"], params)

    async def congress_recent(self, **params: Any) -> list[dict]:
        params.setdefault("limit", 200)
        return await self.data(ENDPOINTS["congress"], params)

    async def interpolated_iv(self, ticker: str, **params: Any) -> list[dict]:
        return await self.data(_fmt("interpolated_iv", ticker), params)


# --- module helpers ------------------------------------------------------
def make_client() -> UWClient:
    """Return the appropriate client: DemoClient in demo mode, else a real UWClient.

    Kept here (not in analysis) so every entry point shares one selection rule.
    """
    if settings.demo_mode:
        from .demo import DemoClient

        return DemoClient()  # type: ignore[return-value]  # duck-typed twin
    return UWClient()


def _fmt(key: str, ticker: str) -> str:
    return ENDPOINTS[key].format(ticker=ticker.upper())


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    return {k: v for k, v in params.items() if v is not None}


def _safe_reason(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        return str(body.get("reason") or body)
    except Exception:
        return resp.text[:200]
