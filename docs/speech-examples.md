# Speech examples: designed for ears, not eyes

AlphaVoice claims its answers are designed for ears. This page proves it with
real tool output from the demo fixtures: raw quant output on the left, the
spoken summary the tool actually returned on the right. Every example below is
a verbatim quote from a run of the tools on the synthetic fixtures (2026-09-19).

## The rules behind every answer

The summary/detail contract (`server/tools/contract.py`) enforces these rules on
every tool response:

1. **Precision budget.** `speak_number` rounds aggressively: one significant
   digit for values under 1, two for 1 to 100, three above. Listeners hear
   approximations, never false precision.
2. **"about" prefix.** Every rounded number is prefixed with "about" (or
   "minus" for negatives) so it sounds like an estimate, because it is one.
3. **Qualitative confidence.** Every summary states confidence as
   high, medium, or low. No p-values are read aloud.
4. **Always offer more.** Every summary ends with an offer for detail, so the
   listener can pull the full payload with one follow-up question.
5. **Honest numbers or silence.** If the data cannot support a claim, the
   verdict says so plainly: "I do not have usable data for that request:
   no ticker symbols were provided", with confidence "low" and empty
   key numbers. No invented numbers, ever.

Why the rules exist: `speak_number` once mangled any value that rounded to a
trailing zero (29.7 came out as "about 3"). The bug is fixed and covered by a
regression test; the friction-log entry tells the story.

## Pair 1: signal_scan (momentum and mean-reversion signals)

Raw quant output (from the `detail` payload):

```json
{
  "symbol": "MSFT",
  "expected_return": 0.01596794836972633
}
```

and the top feature driving it:

```json
{
  "feature": "momentum_roc20",
  "standardized_coef": -0.040199196962776865
}
```

Spoken summary returned by the tool:

> Signal scan ranks MSFT first, with about 1.6 percent expected return over
> 5 days, driven mainly by momentum roc20.

Key numbers (machine value vs what the listener hears):

| Label | Raw value | Spoken |
|---|---|---|
| MSFT expected return | 0.01596794836972633 | about 0.02 |
| NVDA expected return | 0.014748011784933367 | about 0.01 |
| AAPL expected return | -0.025846473445053645 | minus 0.03 |
| top feature weight | -0.040199196962776865 | minus 0.04 |

What changed: 16 decimal places became one significant digit, "about"
flagged every number as approximate, and the verdict named the driving
feature in plain words.

## Pair 2: news_microstructure (news-to-price impact, Hawkes fit)

Raw quant output (from the `detail` payload):

```json
{
  "beta": 1.4,
  "regime": "sub-critical",
  "log_likelihood": 1.6579188804693403,
  "n_events": 972,
  "estimator": "tick.hawkes.HawkesExpKern maximum likelihood"
}
```

Spoken summary returned by the tool:

> News impact is sub-critical: each news event adds about 0.6 expected price
> jumps, decaying with a half-life of about 0.5 minutes.

What changed: the beta parameter and log-likelihood never surface in the
spoken answer. The derived half-life, ln(2)/beta, is the only time constant
the listener hears. "sub-critical" is kept because it is the one technical
term a follow-up question ("what does sub-critical mean?") can unpack; the
verdict's offer ("say detail for...") is the door to the full fit.

## Pair 3: mispricing_check (cross-market mispricing, paper only)

Raw quant output (from the `detail` payload, abbreviated):

```json
{
  "net_edge_per_contract": 0.05,
  "buy_venue": "Polymarket",
  "fees_total": "...",
  "kelly_full": "...",
  "hypothetical_quantity": 0.0,
  "p_win_assumption": 0.55
}
```

Spoken summary returned by the tool:

> Mispricing found after costs, but at the assumed 55 percent win probability
> the Kelly sizer recommends no position, paper only.

What changed: the verdict leads with the honest outcome (no position), names
the 55 percent assumption out loud so it cannot masquerade as an estimate,
and ends with "paper only". The full cost waterfall stays in the detail
payload, one question away.

## Pair 4: market_brief (the composed path, all three engines)

The brief runs all three tools on the synthetic fixtures and composes one
spoken verdict. Nothing is a canned string; the numbers below came from the
same run as pairs 1 to 3:

> News is absorbed with a half-life of about 30 seconds; mispricing leaves a
> net edge of about 0.05 per contract, though the Kelly sizer recommends no
> position, paper only; and the signal scan ranks MSFT first, with about
> 1.6 percent expected return over 5 days.

What changed: three tools' worth of numbers became one 30-second spoken
paragraph, each clause carrying its own honesty note (30 seconds, not
0.495 minutes; paper only; about, not exactly). The demo script in
`docs/demo-script.md` reads this exact shape aloud.

## What to listen for in the demo

Ask the web sim any of the chips, then check: every number you hear starts
with "about" or "minus", no number has more precision than one or two
significant digits, confidence is stated in words, the answer ends with an
offer, and the data is labeled simulated. That is the whole design, audible.
