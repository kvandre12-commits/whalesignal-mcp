# WhaleSignal - Demo Tour

Full output of `./scripts/demo.sh` (runs on synthetic demo data, no API key).
A recorded asciinema cast is at [`docs/demo.cast`](demo.cast) - play it with `asciinema play docs/demo.cast`.

```text

== 1) Single-ticker conviction (fused signals + rationale) ==
** DEMO DATA ** (synthetic, deterministic per ticker — not live market data)

== NVDA  —  Strong Bearish  (BEARISH) ==
   [#######-----------------------] 24.3/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.32  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.60  w=0.14 
     - dark_pool            -0.46  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +0.85  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * options_flow_alerts: bearish (-0.32)
     * options_volume: bearish (-0.60)
     * dark_pool: bearish (-0.46)
     * congress: bullish (+0.85)
     * gamma_regime: bearish (-0.50)

== 2) Rank a watchlist (heatmap-ready, best first) ==
** DEMO DATA ** (synthetic, deterministic per ticker — not live market data)

WhaleSignal ranking (8 tickers, best first):
 1. AMZN    83.1  Strong Bullish
 2. AMD     81.5  Strong Bullish
 3. AAPL    77.0  Strong Bullish
 4. GOOG    68.6  Bullish
 5. MSFT    53.4  Neutral / Mixed
 6. NVDA    24.3  Strong Bearish
 7. TSLA    23.2  Strong Bearish
 8. META    20.0  Strong Bearish

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

== AMD  —  Strong Bullish  (BULLISH) ==
   [########################------] 81.5/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +0.57  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       +0.49  w=0.14 
     - dark_pool            +0.76  w=0.12 
     - gamma_regime         +0.50  w=0.10 
     - congress             -0.52  w=0.06 
   why:
     * net_premium: bullish (+1.00)
     * options_flow_alerts: bullish (+0.57)
     * dark_pool: bullish (+0.76)
     * options_volume: bullish (+0.49)
     * gamma_regime: bullish (+0.50)
     * congress: bearish (-0.52)

== AAPL  —  Strong Bullish  (BULLISH) ==
   [#######################-------] 77.0/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +0.34  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       +0.25  w=0.14 
     - dark_pool            +0.12  w=0.12 
     - gamma_regime         +0.50  w=0.10 
     - congress             +1.00  w=0.06 
   why:
     * net_premium: bullish (+1.00)
     * options_flow_alerts: bullish (+0.34)
     * congress: bullish (+1.00)
     * gamma_regime: bullish (+0.50)
     * options_volume: bullish (+0.25)
     * dark_pool: bullish (+0.12)

== GOOG  —  Bullish  (BULLISH) ==
   [#####################---------] 68.6/100   coverage 100%
   sub-signals:
     - options_flow_alerts  +0.01  w=0.30 
     - net_premium          +1.00  w=0.28 
     - options_volume       +0.23  w=0.14 
     - dark_pool            +0.07  w=0.12 
     - gamma_regime         +0.50  w=0.10 
     - congress             +0.00  w=0.06 
   why:
     * net_premium: bullish (+1.00)
     * gamma_regime: bullish (+0.50)
     * options_volume: bullish (+0.23)
     * dark_pool: bullish (+0.07)

== MSFT  —  Neutral / Mixed  (NEUTRAL) ==
   [################--------------] 53.4/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.30  w=0.30 
     - net_premium          +0.29  w=0.28 
     - options_volume       -0.14  w=0.14 
     - dark_pool            +0.32  w=0.12 
     - gamma_regime         +0.50  w=0.10 
     - congress             +0.14  w=0.06 
   why:
     * options_flow_alerts: bearish (-0.30)
     * net_premium: bullish (+0.29)
     * gamma_regime: bullish (+0.50)
     * dark_pool: bullish (+0.32)
     * options_volume: bearish (-0.14)
     * congress: bullish (+0.14)

== NVDA  —  Strong Bearish  (BEARISH) ==
   [#######-----------------------] 24.3/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.32  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.60  w=0.14 
     - dark_pool            -0.46  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +0.85  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * options_flow_alerts: bearish (-0.32)
     * options_volume: bearish (-0.60)
     * dark_pool: bearish (-0.46)
     * congress: bullish (+0.85)
     * gamma_regime: bearish (-0.50)

== TSLA  —  Strong Bearish  (BEARISH) ==
   [#######-----------------------] 23.2/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.56  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.54  w=0.14 
     - dark_pool            -0.19  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +1.00  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * options_flow_alerts: bearish (-0.56)
     * options_volume: bearish (-0.54)
     * congress: bullish (+1.00)
     * gamma_regime: bearish (-0.50)
     * dark_pool: bearish (-0.19)

== META  —  Strong Bearish  (BEARISH) ==
   [######------------------------] 20.0/100   coverage 100%
   sub-signals:
     - options_flow_alerts  -0.64  w=0.30 
     - net_premium          -1.00  w=0.28 
     - options_volume       -0.29  w=0.14 
     - dark_pool            -0.49  w=0.12 
     - gamma_regime         -0.50  w=0.10 
     - congress             +0.33  w=0.06 
   why:
     * net_premium: bearish (-1.00)
     * options_flow_alerts: bearish (-0.64)
     * dark_pool: bearish (-0.49)
     * gamma_regime: bearish (-0.50)
     * options_volume: bearish (-0.29)
     * congress: bullish (+0.33)

== 3) One-call written market briefing ==
** DEMO DATA ** (synthetic, deterministic per ticker — not live market data)

WhaleSignal Market Briefing - 2026-09-18  [DEMO DATA - synthetic, not live]
========================================================
Market pulse: RISK-ON / BULLISH. Net call premium $5.31M, net put premium -$4.25M.
Whales leaning bullish: AMZN (83), AMD (82), AAPL (77).
Whales leaning bearish: NVDA (24), TSLA (23), META (20).
Top conviction: AMZN - Strong Bullish (83.1/100). net_premium: bullish (+1.00); options_flow_alerts: bullish (+0.68).
Congress desk: 19 buys vs 10 sells recently. Notable: Buy NVDA ($100,001 - $250,000); Buy AAPL ($100,001 - $250,000); Buy META ($100,001 - $250,000).
--------------------------------------------------------
Not financial advice. Signals are heuristics over market data.

== 4) Also available ==
  * MCP server : python -m whalesignal.server            (WHALESIGNAL_DEMO=1 for demo)
  * Web heatmap: python -m whalesignal.web --demo        (http://127.0.0.1:8000)
  * Tests      : python tests/test_signals.py  (+ demo_pipeline / briefing / web)
```
