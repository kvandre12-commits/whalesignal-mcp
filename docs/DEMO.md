# WhaleSignal - Demo Tour

Full output of `./scripts/demo.sh` (runs on synthetic demo data, no API key).
A recorded asciinema cast is at [`docs/demo.cast`](demo.cast) - play it with `asciinema play docs/demo.cast`.

```text

== 1) Single-ticker conviction (fused signals + rationale) ==
** DEMO DATA ** (synthetic, deterministic per ticker — not live market data)

== NVDA  —  Strong Bearish  (BEARISH) ==
   [#####-------------------------] 17.5/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.76  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.60  w=0.14 
     - dark_pool            -0.46  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +0.78  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * options_flow_alerts: bearish (-0.76)
     * options_volume: bearish (-0.60)
     * dark_pool: bearish (-0.46)
     * gamma_regime: bearish (-0.50)
     * congress: bullish (+0.78)

== 2) Rank a watchlist (heatmap-ready, best first) ==
** DEMO DATA ** (synthetic, deterministic per ticker — not live market data)

WhaleSignal ranking (8 tickers, best first):
 1. AMZN    87.9  Strong Bullish
 2. AMD     78.1  Strong Bullish
 3. MSFT    77.8  Strong Bullish
 4. AAPL    76.0  Strong Bullish
 5. GOOG    65.0  Bullish
 6. META    29.1  Bearish
 7. TSLA    18.8  Strong Bearish
 8. NVDA    17.5  Strong Bearish

== AMZN  —  Strong Bullish  (BULLISH) ==
   [##########################----] 87.9/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +1.00  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       +0.84  w=0.14 
     - dark_pool            +0.09  w=0.12 
     - gamma_regime         +0.50  w=0.10 
     - congress             +0.00  w=0.06 
   why:
     * options_flow_alerts: bullish (+1.00)
     * net_premium: bullish (+1.00)
     * options_volume: bullish (+0.84)
     * gamma_regime: bullish (+0.50)
     * dark_pool: bullish (+0.09)

== AMD  —  Strong Bullish  (BULLISH) ==
   [#######################-------] 78.1/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +0.29  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       +0.49  w=0.14 
     - dark_pool            +0.76  w=0.12 
     - gamma_regime         +0.50  w=0.10 
     - congress             -0.21  w=0.06 
   why:
     * net_premium: bullish (+1.00)
     * dark_pool: bullish (+0.76)
     * options_flow_alerts: bullish (+0.29)
     * options_volume: bullish (+0.49)
     * gamma_regime: bullish (+0.50)
     * congress: bearish (-0.21)

== MSFT  —  Strong Bullish  (BULLISH) ==
   [#######################-------] 77.8/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +1.00  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       -0.14  w=0.14 
     - dark_pool            +0.32  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +0.12  w=0.06 
   why:
     * options_flow_alerts: bullish (+1.00)
     * net_premium: bullish (+1.00)
     * gamma_regime: bearish (-0.50)
     * dark_pool: bullish (+0.32)
     * options_volume: bearish (-0.14)
     * congress: bullish (+0.12)

== AAPL  —  Strong Bullish  (BULLISH) ==
   [#######################-------] 76.0/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +0.60  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       +0.25  w=0.14 
     - dark_pool            +0.12  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +1.00  w=0.06 
   why:
     * net_premium: bullish (+1.00)
     * options_flow_alerts: bullish (+0.60)
     * congress: bullish (+1.00)
     * gamma_regime: bearish (-0.50)
     * options_volume: bullish (+0.25)
     * dark_pool: bullish (+0.12)

== GOOG  —  Bullish  (BULLISH) ==
   [####################----------] 65.0/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.23  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       +0.23  w=0.14 
     - dark_pool            +0.07  w=0.12 
     - gamma_regime         +0.50  w=0.10 
     - congress             +0.00  w=0.06 
   why:
     * net_premium: bullish (+1.00)
     * options_flow_alerts: bearish (-0.23)
     * gamma_regime: bullish (+0.50)
     * options_volume: bullish (+0.23)
     * dark_pool: bullish (+0.07)

== META  —  Bearish  (BEARISH) ==
   [#########---------------------] 29.1/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.05  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.29  w=0.14 
     - dark_pool            -0.49  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +0.43  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * dark_pool: bearish (-0.49)
     * gamma_regime: bearish (-0.50)
     * options_volume: bearish (-0.29)
     * congress: bullish (+0.43)

== TSLA  —  Strong Bearish  (BEARISH) ==
   [######------------------------] 18.8/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.85  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.54  w=0.14 
     - dark_pool            -0.19  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +1.00  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * options_flow_alerts: bearish (-0.85)
     * options_volume: bearish (-0.54)
     * congress: bullish (+1.00)
     * gamma_regime: bearish (-0.50)
     * dark_pool: bearish (-0.19)

== NVDA  —  Strong Bearish  (BEARISH) ==
   [#####-------------------------] 17.5/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.76  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.60  w=0.14 
     - dark_pool            -0.46  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +0.78  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * options_flow_alerts: bearish (-0.76)
     * options_volume: bearish (-0.60)
     * dark_pool: bearish (-0.46)
     * gamma_regime: bearish (-0.50)
     * congress: bullish (+0.78)

== 3) One-call written market briefing ==
** DEMO DATA ** (synthetic, deterministic per ticker — not live market data)

WhaleSignal Market Briefing - 2026-09-18  [DEMO DATA - synthetic, not live]
========================================================
Market pulse: RISK-ON / BULLISH. Net options premium $3.62M into calls vs $983.87K into puts.
Whales leaning bullish: AMZN (88), AMD (78), MSFT (78).
Whales leaning bearish: PLTR (25), TSLA (19), NVDA (18).
Top conviction: AMZN - Strong Bullish (87.9/100). options_flow_alerts: bullish (+1.00); net_premium: bullish (+1.00).
Congress desk: 19 buys vs 10 sells recently. Notable: Purchase NVDA ($250.00K); Purchase AAPL ($250.00K); Purchase META ($250.00K).
--------------------------------------------------------
Not financial advice. Signals are heuristics over market data.

== 4) Also available ==
  * MCP server : python -m whalesignal.server            (WHALESIGNAL_DEMO=1 for demo)
  * Web heatmap: python -m whalesignal.web --demo        (http://127.0.0.1:8000)
  * Tests      : python tests/test_signals.py  (+ demo_pipeline / briefing / web)
```
