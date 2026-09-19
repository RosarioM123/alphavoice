"""Deterministic keyword router for the AlphaVoice tool-routing eval.

Approach mirrors the web sim (web/app.js ``routeQuestion``): a
case-insensitive keyword scan with one hit-count score per tool. Two
deliberate differences from the sim:

1. Multi-tool return: the router returns every tool whose hit count is
   within one of the best score (hits >= max(1, best - 1)), so near-ties
   route multi-tool instead of forcing a single winner.
2. Honest silence: zero keyword hits returns the empty set. The sim falls
   back to signal_scan; this router never defaults to a tool.

Pure Python, no network, deterministic: identical input always yields the
identical set.

Keyword notes: the lists start from the tool keyword sets in the project
brief. The generic tokens "today" and "news" were dropped on purpose: they
fire on almost any phrasing (for example, "what's the weather today") and
would break honest silence for out-of-scope questions. "position" was added
to mispricing_check so "my prediction-market position" routes without
requiring the literal phrase "paper position".
"""

from __future__ import annotations

TOOLS = ("signal_scan", "mispricing_check", "news_microstructure", "market_brief")

KEYWORDS = {
    "signal_scan": (
        "momentum",
        "mean reversion",
        "mean-reversion",
        "reversion",
        "signals",
        "signal",
        "movers",
        "moving",
        "scan",
        "ranking",
        "trade idea",
        "trade ideas",
        "unusual",
    ),
    "mispricing_check": (
        "mispric",
        "polymarket",
        "kalshi",
        "arbitrage",
        "spread",
        "rich to",
        "cheap to",
        "price gap",
        "cross-market",
        "election market",
        "paper position",
        "position",
        "prediction market",
    ),
    "news_microstructure": (
        "cpi",
        "inflation",
        "fed",
        "print",
        "absorb",
        "absorbed",
        "absorption",
        "headline",
        "release",
        "macro",
        "earnings",
    ),
    "market_brief": (
        "morning brief",
        "daily brief",
        "brief me",
        "full picture",
        "everything",
        "all three",
        "roundup",
        "whole picture",
    ),
}


def score(question: str) -> dict[str, int]:
    """Return the keyword hit count per tool for a question."""
    q = (question or "").lower()
    return {
        tool: sum(1 for kw in keywords if kw in q)
        for tool, keywords in KEYWORDS.items()
    }


def route(question: str) -> set[str]:
    """Route a question to a set of tool names.

    Returns every tool with hits >= max(1, best - 1). Returns the empty
    set when no tool has any keyword hit (honest silence).
    """
    hits = score(question)
    best = max(hits.values())
    if best == 0:
        return set()
    threshold = max(1, best - 1)
    return {tool for tool, n in hits.items() if n >= threshold}
