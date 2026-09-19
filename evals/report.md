# AlphaVoice tool-routing eval report

Date: 2026-09-19. Questions: 15. Eval runtime: 2.4s (routing plus in-process contract checks).

## Method

The router (`evals/router.py`) is a deterministic keyword scorer that mirrors the web sim approach (`web/app.js`): one case-insensitive hit count per tool. It returns every tool scoring within one of the best hit count, so near-ties route multi-tool. Zero hits returns the empty set: honest silence, never a default tool. The question set (`evals/questions.py`) has 5 clearly single-tool questions, 5 ambiguous multi-tool questions, and 5 out-of-scope questions.

## Scores

| tool | precision | recall | F1 | support |
| --- | --- | --- | --- | --- |
| signal_scan | 1.000 | 1.000 | 1.000 | 4 |
| mispricing_check | 1.000 | 1.000 | 1.000 | 5 |
| news_microstructure | 1.000 | 1.000 | 1.000 | 5 |
| market_brief | 1.000 | 1.000 | 1.000 | 2 |
| micro avg | 1.000 | 1.000 | 1.000 | 15 |
| macro avg | 1.000 | 1.000 | 1.000 | 15 |

Exact-match accuracy: 15/15 (100%). Per category: single 100%, ambiguous 100%, out-of-scope 100%.

## Interpretation

Macro F1 1.000 clears the 0.80 gate. Routing discriminates cleanly: single-tool questions hit exactly one tool, ambiguous phrasings (CPI plus prediction-market position, brief plus mispricing) return the full expected set with no extras, and out-of-scope questions return silence instead of a default scan. Caveat: this is a 15-question seed set written alongside the router, so it measures discrimination on clean phrasings, not robustness to paraphrase. The honest next step is an adversarial round: reworded questions and near-miss distractors.

## In-process contract checks

5/5 correctly routed single-tool questions passed the response contract in-process (real engines, synthetic fixtures, paper only).
- S1 mispricing_check: pass (simulated=True)
- S2 news_microstructure: pass (simulated=True)
- S3 signal_scan: pass (simulated=True)
- S4 market_brief: pass (simulated=True)
- S5 signal_scan: pass (simulated=True)

## Confusion list (expected vs predicted)

- S1 [single] correct
  - question: Is anything mispriced right now?
  - expected: {mispricing_check}
  - predicted: {mispricing_check}
- S2 [single] correct
  - question: How fast did the market absorb the CPI print?
  - expected: {news_microstructure}
  - predicted: {news_microstructure}
- S3 [single] correct
  - question: What signals are firing today?
  - expected: {signal_scan}
  - predicted: {signal_scan}
- S4 [single] correct
  - question: Morning brief please.
  - expected: {market_brief}
  - predicted: {market_brief}
- S5 [single] correct
  - question: Which names show the strongest momentum right now?
  - expected: {signal_scan}
  - predicted: {signal_scan}
- A1 [ambiguous] correct
  - question: Given this morning's CPI print, is my prediction-market position still sane?
  - expected: {mispricing_check, news_microstructure}
  - predicted: {mispricing_check, news_microstructure}
- A2 [ambiguous] correct
  - question: CPI is out, what is moving and is anything mispriced?
  - expected: {mispricing_check, news_microstructure, signal_scan}
  - predicted: {mispricing_check, news_microstructure, signal_scan}
- A3 [ambiguous] correct
  - question: The Fed just spoke, how did prices react, and should I scan for momentum plays?
  - expected: {news_microstructure, signal_scan}
  - predicted: {news_microstructure, signal_scan}
- A4 [ambiguous] correct
  - question: Give me the morning brief, and check whether the election market is mispriced.
  - expected: {market_brief, mispricing_check}
  - predicted: {market_brief, mispricing_check}
- A5 [ambiguous] correct
  - question: Is there arbitrage between Polymarket and Kalshi on the inflation print?
  - expected: {mispricing_check, news_microstructure}
  - predicted: {mispricing_check, news_microstructure}
- O1 [out_of_scope] correct
  - question: What's the weather in Boston this weekend?
  - expected: {}
  - predicted: {}
- O2 [out_of_scope] correct
  - question: Should I buy a house this year?
  - expected: {}
  - predicted: {}
- O3 [out_of_scope] correct
  - question: Draft a birthday toast for my dad.
  - expected: {}
  - predicted: {}
- O4 [out_of_scope] correct
  - question: Explain how photosynthesis works.
  - expected: {}
  - predicted: {}
- O5 [out_of_scope] correct
  - question: What's a good recipe for lasagna?
  - expected: {}
  - predicted: {}

## Notes

- market_brief is a designed composed path in this harness (runs all three tools, synthesizes one verdict). It is not a registered tool in server/mcp_server.py, so its contract check composes the three real server tool functions in-process.
- Generic tokens (today, news) were dropped from the keyword lists because they fire on nearly any phrasing and would break honest silence for out-of-scope questions.
