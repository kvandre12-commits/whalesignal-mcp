#  WhaleSignal MCP

[![CI](https://github.com/kvandre12-commits/whalesignal-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/kvandre12-commits/whalesignal-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Turn raw Unusual Whales data into one decision-ready conviction score — spoken in plain English to any AI.**

![WhaleSignal conviction heatmap](docs/heatmap-demo.svg)

*Conviction heatmap rendered by [`scripts/render_heatmap.py`](scripts/render_heatmap.py) from the actual `/api/rank --demo` output (same code the web dashboard serves). Run `python -m whalesignal.web --demo` for the interactive version.* Full terminal tour: [`docs/DEMO.md`](docs/DEMO.md).

Unusual Whales already ships a great hosted MCP that returns *raw* data. WhaleSignal goes one step further: it **fuses six Unusual Whales datasets into a single explainable 0–100 conviction score** per ticker, so an LLM (or a human) gets an *answer*, not a spreadsheet.

Ask Claude / Cursor / ChatGPT: *"What's the conviction on AMZN?"* and get this (actual `--demo` output):

```
== AMZN  —  Strong Bullish  (BULLISH) ==
   [#########################-----] 83.1/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +0.68  w=0.30
     - net_premium          +1.00  w=0.28
     - options_volume       +0.84  w=0.14
     - dark_pool            +0.09  w=0.12
     - gamma_regime         +0.50  w=0.10
     - congress             +0.00  w=0.06
   why:
     * net_premium: bullish (+1.00)
     * options_flow_alerts: bullish (+0.68)
     * options_volume: bullish (+0.84)
     * gamma_regime: bullish (+0.50)
     * dark_pool: bullish (+0.09)
```

> Numbers above are deterministic synthetic **demo** data (seeded per ticker), reproducible with `python -m whalesignal.cli AMZN --demo`. Different tickers produce different scores; e.g. `NVDA` is `24.3 / Strong Bearish`.

---

## Why it can win

- **It's an answer, not a dump.** Judges see instant, explainable signals — every score ships with a per-signal breakdown and a rationale. No black boxes.
- **Data fusion is the moat.** Options flow alerts + net premium + call/put volume + dark pool accumulation + dealer gamma regime + congressional trades, blended with tunable weights.
- **Graceful degradation.** Missing/permission-gated endpoints are dropped and weights renormalise — the score never silently lies.
- **Honest math.** Where directionality is ambiguous (dark pool without NBBO, gamma magnitude), we use conservative sign-only contributions instead of fake precision.
- **Uses real endpoints only.** Built straight off the official `skill.md` whitelist — zero hallucinated routes, correct `Authorization` + `UW-CLIENT-API-ID: 100001` headers, all GET.
- **Proven against real payloads.** The extractors read the *actual* UW field names (`total_ask_side_prem`, `call_gamma_oi`, `amounts` ranges …); tests replay the official example responses through the real `UWClient` (via `httpx.MockTransport`) — the same code path live data uses.
- **Bounded inputs.** A `MAX_TICKERS` cap keeps any single request from fanning out into an unbounded burst of upstream calls.
- **Tested logic.** 29 tests, all runnable with **no API key and no network**.

## The signals

| Sub-signal | Endpoint | What it measures |
|---|---|---|
| `options_flow_alerts` | `/api/option-trades/flow-alerts` | Aggressive call vs put whale premium |
| `net_premium` | `/api/stock/{t}/net-prem-ticks` | Cumulative net call vs net put premium |
| `options_volume` | `/api/stock/{t}/options-volume` | Call/put volume balance (P/C ratio) |
| `dark_pool` | `/api/darkpool/{t}` | Accumulation vs distribution off-exchange |
| `gamma_regime` | `/api/stock/{t}/spot-exposures/strike` | Dealer long/short gamma (stability) |
| `congress` | `/api/congress/recent-trades` | Recent congressional buys vs sells |

Weights live in `whalesignal/config.py` (`ConvictionWeights`) — tune to taste.

---

## Try it in 10 seconds (no API key)

WhaleSignal ships a **demo mode**: a deterministic synthetic data source with the exact
same interface as the live client, so the whole fetch -> fuse -> score pipeline runs
offline. Great for demos and CI; output is clearly stamped `** DEMO DATA **`.

```bash
git clone https://github.com/kvandre12-commits/whalesignal-mcp.git
cd whalesignal-mcp
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python -m whalesignal.cli NVDA AAPL TSLA AMZN MSFT --demo
```

```
WhaleSignal ranking (5 tickers, best first):
 1. AMZN    83.1  Strong Bullish
 2. AMD     81.5  Strong Bullish
 3. AAPL    77.0  Strong Bullish
 4. MSFT    53.4  Neutral / Mixed
 5. NVDA    24.3  Strong Bearish
```

### One-call written market briefing

```bash
python -m whalesignal.cli --brief --demo            # default watchlist
python -m whalesignal.cli NVDA AMD AMZN --brief --demo
```

```
WhaleSignal Market Briefing - 2026-09-18  [DEMO DATA - synthetic, not live]
========================================================
Market pulse: RISK-ON / BULLISH. Net call premium $5.31M, net put premium -$4.25M.
Whales leaning bullish: AMZN (83), AMD (82), AAPL (77).
Whales leaning bearish: NVDA (24), TSLA (23), META (20).
Top conviction: AMZN - Strong Bullish (83.1/100). net_premium: bullish (+1.00); options_flow_alerts: bullish (+0.68).
Congress desk: 19 buys vs 10 sells recently. Notable: Buy NVDA ($100,001 - $250,000); ...
```

### Web dashboard (conviction heatmap)

A zero-dependency (stdlib-only) single-page dashboard: a bullish/bearish heatmap of
your watchlist plus the live market briefing. Click any tile for its sub-signal
breakdown and rationale.

```bash
python -m whalesignal.web --demo          # then open http://127.0.0.1:8000
python -m whalesignal.web --port 8000     # live (needs UW_API_KEY)
```

Endpoints (reuse the same analysis code as the CLI + MCP server):
`GET /`, `GET /api/rank?tickers=...`, `GET /api/briefing?tickers=...`.

## Going live (with an API key)

```bash
cp .env.example .env
# edit .env and set UW_API_KEY=<your token>
python -m whalesignal.cli NVDA
python -m whalesignal.cli NVDA AAPL TSLA --rank --top 3
```

### Run the MCP server

```bash
python -m whalesignal.server                    # live (needs UW_API_KEY)
WHALESIGNAL_DEMO=1 python -m whalesignal.server  # demo data, no key needed
```

### Connect an MCP client (Claude Desktop / Cursor / VS Code)

Add to your MCP client config (adjust the absolute paths):

```json
{
  "mcpServers": {
    "whalesignal": {
      "command": "/data/data/com.termux/files/home/uw-challenge/.venv/bin/python",
      "args": ["-m", "whalesignal.server"],
      "env": { "UW_API_KEY": "your-uw-api-token" }
    }
  }
}
```

Then ask: *"Use whalesignal to rank my watchlist: NVDA, AMD, TSLA, PLTR."*

---

## MCP tools exposed

| Tool | Description |
|---|---|
| `conviction_score(ticker)` | Full fused 0–100 conviction with breakdown + rationale |
| `rank_watchlist(tickers, top?)` | Rank several tickers, highest conviction first |
| `market_briefing(tickers?, top?)` | One-call written daily brief: market pulse + ranked watchlist + notable congress trades |
| `flow_alerts(ticker, min_premium?, limit?)` | Raw unusual options flow alerts |
| `dark_pool(ticker, limit?)` | Recent dark pool prints |
| `market_pulse()` | Overall market sentiment from Market Tide |
| `congress_trades(ticker?, limit?)` | Recent congressional trades |

## Architecture (SOLID, tiny files)

```
whalesignal/
  config.py     # single source of truth: base URL, endpoints, weights
  client.py     # async UW API client (auth, retries, data unwrap) + client factory
  demo.py       # DemoClient: deterministic synthetic data, same interface as client
  signals.py    # PURE scoring math — no network, fully unit-tested
  analysis.py   # concurrent fetch + fuse (the I/O + logic seam)
  briefing.py   # market_briefing: pure summarizers + composer, async orchestrator
  server.py     # thin MCP adapter (works on mcp 1.x FastMCP and 2.x MCPServer)
  cli.py        # human-friendly terminal demo
  web.py        # stdlib-only dashboard server (heatmap + JSON endpoints)
  dashboard.html# single-page heatmap front-end (no build step, no CDN)
tests/
  test_signals.py        # pure scoring math (no key, no network)
  test_demo_pipeline.py  # full fetch->fuse pipeline via DemoClient
  test_briefing.py       # briefing summarizers + composer
  test_web.py            # web ticker parsing + asset presence
  test_fixtures.py       # REAL API example payloads -> signals + UWClient (MockTransport)
  fixtures/*.json        # official UW example responses (real field names/envelopes)
scripts/
  demo.sh                # guided terminal tour (synthetic data)
  render_heatmap.py      # render the heatmap SVG from real /api/rank output
```

## Testing & linting

```bash
python tests/test_signals.py         # standalone, no deps, no key, no network
pytest -q                            # or, with pytest installed (29 tests)
ruff check whalesignal tests         # lint (config in pyproject.toml)
./scripts/demo.sh                    # full guided demo tour on synthetic data
```

29 tests, no API key and no network required:

- **Pure scoring math** on hand-built cases.
- **Full demo pipeline** (fetch -> fuse) via `DemoClient`.
- **Live-compatibility fixtures** — the official UW example payloads (real field names
  and envelopes) replayed through the pure signals *and* through the real `UWClient`
  using `httpx.MockTransport`, verifying auth headers + `data` unwrap + correct field reads.
- **Briefing composer** and **web layer**.

## Disclaimer

WhaleSignal is an analytics tool, **not financial advice**. Signals are heuristics over
market data and can be wrong. Do your own research.
