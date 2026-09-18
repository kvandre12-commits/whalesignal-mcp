# WhaleSignal MCP - Challenge Submission

## One-liner

WhaleSignal is an MCP server that turns raw Unusual Whales data into a single,
explainable 0-100 conviction score per ticker - so any AI (or human) gets an *answer*,
not a spreadsheet.

## Elevator pitch (≈100 words)

Unusual Whales already ships a great MCP that returns raw data. WhaleSignal goes one
step further: it fuses six Unusual Whales datasets - options flow alerts, net premium,
call/put volume, dark-pool accumulation, dealer gamma regime, and congressional trades -
into one conviction score, complete with a per-signal breakdown and a plain-English
rationale. Ask Claude, Cursor, or ChatGPT "what's the conviction on NVDA?" and get a
decision-ready read. It also writes a one-call daily market briefing and ships a
zero-dependency web heatmap. Every part runs in a keyless demo mode, so you can try the
whole thing in ten seconds.

## Why it deserves first place

- **It's an answer, not a data dump.** Composite scoring + rationale, not raw JSON.
- **Data fusion is the moat.** Six datasets blended with tunable, renormalising weights.
- **Graceful + honest.** Missing endpoints drop out and weights renormalise; ambiguous
  signals use conservative sign-only contributions instead of fake precision.
- **Real endpoints only.** Built off the official `skill.md` whitelist - correct
  `Authorization` + `UW-CLIENT-API-ID: 100001` headers, all GET, zero hallucinated routes.
- **Live-compatibility fixtures.** Tests replay the official API example payloads (real
  field names + envelopes, e.g. `total_ask_side_prem`, `call_gamma_oi`, `amounts` ranges)
  through the real `UWClient` via `httpx.MockTransport` - the same code path live data uses.
- **Bounded & efficient.** `MAX_TICKERS` cap + fetch-once shared congress feed + a
  concurrency semaphore keep a batch from bursting the rate limit.
- **Fails honestly.** 401 auth errors surface (never a fake neutral); 403/transient
  failures drop only that sub-signal. Cumulative series use the latest snapshot, not a sum.
- **Try it in 10 seconds, no key.** Deterministic demo mode doubles as CI.
- **Tested prototype.** 34 tests, ruff-clean, SOLID tiny modules, works on mcp 1.x + 2.x.

## What's included

- **7 MCP tools:** `conviction_score`, `rank_watchlist`, `market_briefing`,
  `flow_alerts`, `dark_pool`, `market_pulse`, `congress_trades`
- **CLI** for terminal demos (`--brief`, `--rank`, `--demo`)
- **Web dashboard** - stdlib-only conviction heatmap + briefing panel
- **Demo mode** - synthetic, deterministic, keyless
- **Docs** - README, demo tour (`docs/DEMO.md` + asciinema cast), dashboard preview

## 30-second demo

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m whalesignal.cli NVDA AAPL TSLA AMZN MSFT --demo   # ranked heatmap in the terminal
python -m whalesignal.cli --brief --demo                     # written market briefing
python -m whalesignal.web --demo                             # web heatmap at :8000
```

## Connect to an MCP client

```json
{
  "mcpServers": {
    "whalesignal": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "whalesignal.server"],
      "env": { "UW_API_KEY": "your-uw-api-token" }
    }
  }
}
```

## Tech notes

- Python 3.10+, `mcp` (FastMCP / MCPServer), `httpx`, `python-dotenv`
- Pure scoring core (`signals.py`) with no I/O - fully unit tested
- Concurrent fetch/fuse via `asyncio.gather`
- Flip `UW_API_KEY` on and drop `--demo` to go live - zero code changes

*Not financial advice. Signals are heuristics over market data.*
