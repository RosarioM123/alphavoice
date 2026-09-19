"""composed_brief: the composed multi-tool morning brief.

Runs all three quant tools in-process on their synthetic fixtures and
synthesizes ONE spoken verdict as a single sentence, per the tool contract.

PAPER ONLY, SIMULATED DATA. This module adds no order path: mispricing_check
only ever reports a hypothetical size, and this composition never executes.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.mispricing_check import mispricing_check  # noqa: E402
from tools.news_microstructure import news_microstructure  # noqa: E402
from tools.signal_scan import signal_scan  # noqa: E402
from tools.contract import make_key_number, make_result, speak_number  # noqa: E402

SYMBOLS = "AAPL,MSFT,NVDA"
HORIZON_DAYS = 5
TOP_N = 3
SIZE = 100.0
BANKROLL = 100.0
KELLY_FRACTION = 0.25
WINDOW_MINUTES = 390


def _key_number(summary: dict, label: str) -> dict | None:
    for kn in summary.get("key_numbers", []):
        if kn.get("label") == label:
            return kn
    return None


def _speak_percent(frac: float) -> str:
    pct = round(float(frac) * 100, 1)
    return ("minus " if pct < 0 else "about ") + str(abs(pct))


def _join_clauses(clauses: list[str]) -> str:
    if len(clauses) == 1:
        return clauses[0]
    return "; ".join(clauses[:-1]) + "; and " + clauses[-1]


def _news_clause(result: dict) -> tuple[str | None, dict | None]:
    kn = _key_number(result["summary"], "impact half life minutes")
    if kn is None:
        return None, None
    seconds = float(kn["value"]) * 60.0
    return (
        f"news is absorbed with a half-life of {speak_number(seconds)} seconds",
        make_key_number("news impact half life minutes", kn["value"]),
    )


def _mispricing_clause(result: dict) -> tuple[str | None, dict | None]:
    kn = _key_number(result["summary"], "net edge per contract")
    if kn is None:
        return None, None
    detail = result.get("detail", {})
    edge = speak_number(kn["value"])
    qty = float(detail.get("hypothetical_quantity", 0.0) or 0.0)
    actionable = bool(detail.get("actionable"))
    if not actionable:
        clause = "mispricing shows no actionable edge after costs, paper only"
    elif qty > 0:
        clause = (
            f"mispricing leaves a net edge of {edge} per contract, "
            f"sized at about {round(qty, 1)} contracts, paper only"
        )
    else:
        clause = (
            f"mispricing leaves a net edge of {edge} per contract, "
            "though the Kelly sizer recommends no position, paper only"
        )
    return clause, make_key_number("mispricing net edge per contract", kn["value"])


def _signal_clause(result: dict) -> tuple[str | None, dict | None]:
    top = None
    for kn in result["summary"].get("key_numbers", []):
        label = kn.get("label", "")
        if label.endswith("expected return"):
            top = kn
            break
    if top is None:
        return None, None
    symbol = top["label"][: -len(" expected return")]
    return (
        f"the signal scan ranks {symbol} first, with {_speak_percent(top['value'])} "
        f"percent expected return over {HORIZON_DAYS} days",
        make_key_number(f"{symbol} expected return", top["value"]),
    )


def composed_brief(question: str) -> dict:
    """Run all three tools on synthetic fixtures; return one spoken verdict.

    A tool that raises is caught: the brief continues with the others, the
    miss is recorded in detail["failed"], and confidence drops to low.
    """
    calls = (
        ("news_microstructure", news_microstructure, {"window_minutes": WINDOW_MINUTES}),
        (
            "mispricing_check",
            mispricing_check,
            {"size": SIZE, "bankroll": BANKROLL, "kelly_fraction": KELLY_FRACTION},
        ),
        (
            "signal_scan",
            signal_scan,
            {"symbols": SYMBOLS, "horizon_days": HORIZON_DAYS, "top_n": TOP_N},
        ),
    )

    results: dict[str, dict] = {}
    failed: list[dict] = []
    for name, fn, kwargs in calls:
        try:
            results[name] = fn(question, **kwargs)
        except Exception as exc:  # honest miss, never fabricated
            failed.append({"tool": name, "error": f"{type(exc).__name__}: {exc}"})
            results[name] = {"error": f"{type(exc).__name__}: {exc}"}

    clauses: list[str] = []
    keys: list[dict] = []
    for name, builder in (
        ("news_microstructure", _news_clause),
        ("mispricing_check", _mispricing_clause),
        ("signal_scan", _signal_clause),
    ):
        if name in {f["tool"] for f in failed}:
            continue
        try:
            clause, key = builder(results[name])
        except Exception as exc:
            failed.append({"tool": name, "error": f"extraction failed: {type(exc).__name__}: {exc}"})
            results[name] = {"error": str(exc)}
            continue
        if clause is None:
            failed.append({"tool": name, "error": "tool returned no usable numbers"})
            continue
        clauses.append(clause)
        keys.append(key)

    if not clauses:
        verdict = "I could not build the brief: all three tools failed"
    else:
        verdict = _join_clauses(clauses)
    verdict = verdict[0].upper() + verdict[1:]

    return make_result(
        verdict=verdict,
        key_numbers=keys,
        confidence="low" if failed else "medium",
        data_freshness=(
            "Synthetic fixtures: deterministic SIGNAL price panel, synthetic "
            "two-venue order books, and synthetic Hawkes news streams; computed just now."
        ),
        offer="Say which lens to unpack: news absorption, mispricing, or the signal ranking.",
        detail={
            "question": question,
            "news_microstructure": results["news_microstructure"],
            "mispricing_check": results["mispricing_check"],
            "signal_scan": results["signal_scan"],
            "failed": failed,
        },
        simulated=True,
    )
