# Sample utterances: drive the demo in 30 seconds

Type any of these into the web sim ("open web/index.html", then ask), or say
them the way the chips read. Each utterance routes to one MCP tool through the
sim's keyword routing, which is labeled in the UI as simulated agent routing.

## The four demo chips

These are the exact chip questions in `web/index.html`. In order, they show a
judge the whole product: the composed path, then each engine on its own.

| Try saying | Tool it reaches | What you will hear back |
|---|---|---|
| "Morning brief roundup: this morning's CPI print, anything mispriced, and today's signals" | market_brief | One spoken verdict from all three engines: news absorption half-life, mispricing edge (paper only), and the top-ranked signal |
| "How fast did the market absorb this morning's CPI print?" | news_microstructure | Sub-critical or explosive verdict with the impact half-life in plain words |
| "Anything mispriced between Polymarket and Kalshi right now?" | mispricing_check | Net edge after costs, the Kelly sizer's hypothetical size (often no position), always paper only |
| "Any unusual momentum or mean-reversion signals today?" | signal_scan | Top-ranked symbol, expected return over 5 days, and the driving signal family |

## More utterances to try

Each tool answers any question that contains one of its routing keywords.
Keywords are listed under each tool so you can invent your own phrasing.

**market_brief** (keywords: morning brief, brief, full picture, everything
today, all three, roundup)

- "Give me the full picture: everything today."
- "Morning brief, please."
- "Run all three and tell me what matters."

**news_microstructure** (keywords: cpi, inflation, fed, news, print, absorb,
absorbed, absorption, headline, release, announcement, macro, earnings)

- "Did the Fed announcement move the market?"
- "How fast was the inflation print absorbed?"
- "Walk me through the macro news impact."

**mispricing_check** (keywords: mispric, polymarket, kalshi, arbitrage, spread,
rich to, cheap to, price gap, cross-market, election market, paper position)

- "Show me the Polymarket versus Kalshi spread."
- "Is there an arbitrage gap after fees?"
- "What paper position would the sizer take?"

**signal_scan** (keywords: momentum, mean-reversion, mean reversion, reversion,
signal, unusual, scan, movers, trade idea, ranking, today)

- "Rank today's trade ideas."
- "Any unusual movers in the scan?"
- "Show me the momentum ranking."

## What happens with anything else

A question that matches no tool keywords falls back to a broad signal_scan,
and the UI says so. That is the honest default: scan first, ask a sharper
question next. A judge can start vague, watch the routing explain itself, and
then use the table above to go deeper.

## 30-second path for a judge

1. Ask the morning-brief chip. You hear all three engines in one verdict.
2. Ask "detail" after any answer to see the full payload behind the spoken
   summary, the summary/detail contract in action.
3. Note every number starts with "about", the data is labeled simulated, and
   the mispricing leg ends with "paper only". That is the design.
