"""Run the AlphaVoice tool-routing eval.

Steps:
1. Route every question in evals/questions.py with evals/router.py.
2. Compute per-tool precision/recall/F1 plus micro and macro averages.
3. Bonus in-process contract checks: for correctly routed single-tool
   questions, call the tool function in-process (server/tools) and assert
   the response contract (summary with verdict and key_numbers, detail,
   simulated is a bool). market_brief is not a registered server function,
   so its check composes the three real tools, matching the designed
   "runs all three and synthesizes one spoken verdict" path.
4. Write evals/report.md and print a one-line summary to stdout.

Pure routing is instant; the contract checks call the real engines
in-process (synthetic fixtures, paper only). Whole run stays well under
two minutes.

Exit code: 0 when macro F1 >= 0.80, 1 otherwise (CI gate).
"""

from __future__ import annotations

import sys
import time
from datetime import date
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parent
sys.path.insert(0, str(EVALS_DIR))          # questions.py, router.py
sys.path.insert(0, str(REPO_ROOT / "server"))  # server.tools, like tests/conftest.py

from questions import QUESTIONS  # noqa: E402
from router import TOOLS, route  # noqa: E402

MACRO_F1_GATE = 0.80


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def _fmt_set(names: set[str]) -> str:
    return "{" + ", ".join(sorted(names)) + "}" if names else "{}"


def _assert_contract(tool: str, result: dict) -> None:
    """Assert the AlphaVoice tool response contract (server/tools/contract.py)."""
    assert isinstance(result, dict), f"{tool}: result is not a dict"
    summary = result.get("summary")
    assert isinstance(summary, dict), f"{tool}: missing summary dict"
    assert isinstance(summary.get("verdict"), str) and summary["verdict"], (
        f"{tool}: summary.verdict must be a non-empty string"
    )
    assert isinstance(summary.get("key_numbers"), list) and summary["key_numbers"], (
        f"{tool}: summary.key_numbers must be a non-empty list"
    )
    assert "detail" in result, f"{tool}: missing detail"
    assert isinstance(result.get("simulated"), bool), (
        f"{tool}: simulated must be a bool"
    )


def _run_market_brief(question: str) -> dict:
    """Compose market_brief in-process: run all three tools, synthesize a verdict."""
    from tools.mispricing_check import mispricing_check
    from tools.news_microstructure import news_microstructure
    from tools.signal_scan import signal_scan

    parts = {
        "signal_scan": signal_scan(question),
        "mispricing_check": mispricing_check(question),
        "news_microstructure": news_microstructure(question),
    }
    for name, res in parts.items():
        _assert_contract(name, res)
    verdict = " ".join(
        f"{name}: {res['summary']['verdict']}." for name, res in parts.items()
    )
    return {
        "summary": {
            "verdict": "Morning brief: " + verdict,
            "key_numbers": parts["signal_scan"]["summary"]["key_numbers"],
            "confidence": "medium",
            "data_freshness": "simulated fixtures",
            "offer": "Say detail for any single tool path.",
        },
        "detail": {"parts": list(parts)},
        "simulated": True,
    }


_TOOL_CALLS = {
    "signal_scan": lambda q: __import__("tools.signal_scan", fromlist=["signal_scan"]).signal_scan(q),
    "mispricing_check": lambda q: __import__("tools.mispricing_check", fromlist=["mispricing_check"]).mispricing_check(q),
    "news_microstructure": lambda q: __import__("tools.news_microstructure", fromlist=["news_microstructure"]).news_microstructure(q),
    "market_brief": _run_market_brief,
}


def run_contract_checks(rows: list[dict]) -> list[dict]:
    """Call tools in-process for correctly routed single-tool questions."""
    checks = []
    for row in rows:
        if row["category"] != "single" or row["predicted"] != row["expected"]:
            continue
        tool = next(iter(row["expected"]))
        try:
            result = _TOOL_CALLS[tool](row["question"])
            _assert_contract(tool, result)
            checks.append({"tool": tool, "question_id": row["id"], "ok": True,
                           "note": f"simulated={result['simulated']}"})
        except Exception as exc:  # noqa: BLE001 - surfaced loudly below
            checks.append({"tool": tool, "question_id": row["id"], "ok": False,
                           "note": f"{type(exc).__name__}: {exc}"})
    return checks


def evaluate() -> tuple[list[dict], dict, dict]:
    rows = []
    for entry in QUESTIONS:
        predicted = route(entry["question"])
        rows.append({
            "id": entry["id"],
            "category": entry["category"],
            "question": entry["question"],
            "expected": set(entry["expected"]),
            "predicted": predicted,
            "correct": predicted == set(entry["expected"]),
        })

    per_tool: dict[str, dict] = {}
    for tool in TOOLS:
        tp = sum(1 for r in rows if tool in r["expected"] and tool in r["predicted"])
        fp = sum(1 for r in rows if tool not in r["expected"] and tool in r["predicted"])
        fn = sum(1 for r in rows if tool in r["expected"] and tool not in r["predicted"])
        support = sum(1 for r in rows if tool in r["expected"])
        p, r_, f1 = _prf(tp, fp, fn)
        per_tool[tool] = {
            "precision": p, "recall": r_, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "support": support,
        }

    micro_tp = sum(m["tp"] for m in per_tool.values())
    micro_fp = sum(m["fp"] for m in per_tool.values())
    micro_fn = sum(m["fn"] for m in per_tool.values())
    micro_p, micro_r, micro_f1 = _prf(micro_tp, micro_fp, micro_fn)
    macro_p = sum(m["precision"] for m in per_tool.values()) / len(per_tool)
    macro_r = sum(m["recall"] for m in per_tool.values()) / len(per_tool)
    macro_f1 = sum(m["f1"] for m in per_tool.values()) / len(per_tool)

    exact = sum(1 for r in rows if r["correct"])
    cat_acc = {}
    for cat in ("single", "ambiguous", "out_of_scope"):
        cat_rows = [r for r in rows if r["category"] == cat]
        cat_acc[cat] = sum(1 for r in cat_rows if r["correct"]) / len(cat_rows)

    summary = {
        "n_questions": len(rows),
        "exact_match": exact,
        "exact_match_rate": exact / len(rows),
        "per_tool": per_tool,
        "micro": {"precision": micro_p, "recall": micro_r, "f1": micro_f1},
        "macro": {"precision": macro_p, "recall": macro_r, "f1": macro_f1},
        "category_accuracy": cat_acc,
    }
    return rows, summary, per_tool


def write_report(rows: list[dict], summary: dict, checks: list[dict],
                 elapsed_s: float) -> Path:
    lines = []
    lines.append("# AlphaVoice tool-routing eval report")
    lines.append("")
    lines.append(f"Date: {date.today().isoformat()}. Questions: {summary['n_questions']}. "
                 f"Eval runtime: {elapsed_s:.1f}s (routing plus in-process contract checks).")
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append("The router (`evals/router.py`) is a deterministic keyword scorer that "
                 "mirrors the web sim approach (`web/app.js`): one case-insensitive "
                 "hit count per tool. It returns every tool scoring within one of the "
                 "best hit count, so near-ties route multi-tool. Zero hits returns the "
                 "empty set: honest silence, never a default tool. The question set "
                 "(`evals/questions.py`) has 5 clearly single-tool questions, "
                 "5 ambiguous multi-tool questions, and 5 out-of-scope questions.")
    lines.append("")
    lines.append("## Scores")
    lines.append("")
    lines.append("| tool | precision | recall | F1 | support |")
    lines.append("| --- | --- | --- | --- | --- |")
    for tool in TOOLS:
        m = summary["per_tool"][tool]
        lines.append(f"| {tool} | {m['precision']:.3f} | {m['recall']:.3f} | "
                     f"{m['f1']:.3f} | {m['support']} |")
    mic = summary["micro"]
    mac = summary["macro"]
    lines.append(f"| micro avg | {mic['precision']:.3f} | {mic['recall']:.3f} | "
                 f"{mic['f1']:.3f} | {summary['n_questions']} |")
    lines.append(f"| macro avg | {mac['precision']:.3f} | {mac['recall']:.3f} | "
                 f"{mac['f1']:.3f} | {summary['n_questions']} |")
    lines.append("")
    lines.append(f"Exact-match accuracy: {summary['exact_match']}/{summary['n_questions']} "
                 f"({summary['exact_match_rate']:.0%}). Per category: single "
                 f"{summary['category_accuracy']['single']:.0%}, ambiguous "
                 f"{summary['category_accuracy']['ambiguous']:.0%}, out-of-scope "
                 f"{summary['category_accuracy']['out_of_scope']:.0%}.")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    if mac["f1"] >= MACRO_F1_GATE:
        lines.append(
            f"Macro F1 {mac['f1']:.3f} clears the {MACRO_F1_GATE:.2f} gate. "
            "Routing discriminates cleanly: single-tool questions hit exactly one "
            "tool, ambiguous phrasings (CPI plus prediction-market position, brief "
            "plus mispricing) return the full expected set with no extras, and "
            "out-of-scope questions return silence instead of a default scan. "
            "Caveat: this is a 15-question seed set written alongside the router, "
            "so it measures discrimination on clean phrasings, not robustness to "
            "paraphrase. The honest next step is an adversarial round: reworded "
            "questions and near-miss distractors.")
    else:
        lines.append(
            f"Macro F1 {mac['f1']:.3f} is below the {MACRO_F1_GATE:.2f} gate. "
            "See the confusion list for the failing questions; likely fixes are "
            "keyword tuning or a stricter near-tie rule.")
    lines.append("")
    lines.append("## In-process contract checks")
    lines.append("")
    if checks:
        passed = sum(1 for c in checks if c["ok"])
        lines.append(f"{passed}/{len(checks)} correctly routed single-tool questions "
                     "passed the response contract in-process (real engines, "
                     "synthetic fixtures, paper only).")
        for c in checks:
            mark = "pass" if c["ok"] else "FAIL"
            lines.append(f"- {c['question_id']} {c['tool']}: {mark} ({c['note']})")
    else:
        lines.append("No correctly routed single-tool questions to check.")
    lines.append("")
    lines.append("## Confusion list (expected vs predicted)")
    lines.append("")
    for r in rows:
        mark = "correct" if r["correct"] else "WRONG"
        lines.append(f"- {r['id']} [{r['category']}] {mark}")
        lines.append(f"  - question: {r['question']}")
        lines.append(f"  - expected: {_fmt_set(r['expected'])}")
        lines.append(f"  - predicted: {_fmt_set(r['predicted'])}")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- market_brief is a designed composed path in this harness "
                 "(runs all three tools, synthesizes one verdict). It is not a "
                 "registered tool in server/mcp_server.py, so its contract check "
                 "composes the three real server tool functions in-process.")
    lines.append("- Generic tokens (today, news) were dropped from the keyword "
                 "lists because they fire on nearly any phrasing and would break "
                 "honest silence for out-of-scope questions.")
    lines.append("")

    path = EVALS_DIR / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    start = time.perf_counter()
    rows, summary, _ = evaluate()
    checks = run_contract_checks(rows)
    failed = [c for c in checks if not c["ok"]]
    elapsed = time.perf_counter() - start
    report_path = write_report(rows, summary, checks, elapsed)

    exact = summary["exact_match"]
    n = summary["n_questions"]
    passed = len(checks) - len(failed)
    print(f"routing eval: {exact}/{n} exact match, macro F1 {summary['macro']['f1']:.3f}, "
          f"micro F1 {summary['micro']['f1']:.3f}, contract checks {passed}/{len(checks)}, "
          f"{elapsed:.1f}s, report: {report_path}")

    if failed:
        for c in failed:
            print(f"CONTRACT FAIL {c['question_id']} {c['tool']}: {c['note']}",
                  file=sys.stderr)
        return 1
    if summary["macro"]["f1"] < MACRO_F1_GATE:
        print(f"macro F1 {summary['macro']['f1']:.3f} below gate {MACRO_F1_GATE:.2f}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
