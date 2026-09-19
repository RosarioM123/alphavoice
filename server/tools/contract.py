"""Tool response contract for AlphaVoice.

Every tool returns this exact JSON shape::

    {
      "summary": {
        "verdict": str,        # one spoken sentence
        "key_numbers": [{"label": str, "spoken": str, "value": number}],
        "confidence": "high" | "medium" | "low",
        "data_freshness": str,
        "offer": str,          # always offers more detail
      },
      "detail": {...},
      "simulated": bool,
    }

Contract rules (enforced here, tested in tests/test_contract.py):
- ``spoken`` values never carry more precision than the data earns. Use
  ``speak_number`` / ``make_key_number`` to generate them.
- Qualitative confidence only; low confidence or missing data means the
  verdict says so plainly (honest numbers or silence).
- Every summary ends with an offer for detail.
- ``simulated`` is True whenever the numbers come from synthetic fixtures,
  and ``data_freshness`` must say so.
"""

from __future__ import annotations

import math
import re

CONFIDENCES = ("high", "medium", "low")
_SIMULATED_WORDS = ("simulat", "synthetic", "fixture", "illustrative", "no data")


def speak_number(value: float | int, *, floor_zero: bool = False) -> str:
    """Render a number for voice with aggressively rounded precision.

    Budget: 1 significant digit for |v| < 1 (e.g. 0.6341 -> "about 0.6"),
    2 for 1 <= |v| < 100, 3 above. Prefixed with "about " (or "minus" for
    negatives) so listeners hear it as an approximation.
    """
    v = float(value)
    if v == 0:
        return "0"
    neg = v < 0
    a = abs(v)
    if a < 1:
        sig = 1
    elif a < 100:
        sig = 2
    else:
        sig = 3
    exp = math.floor(math.log10(a))
    decimals = sig - 1 - exp
    rounded = round(a, decimals)
    if decimals >= 0:
        text = f"{rounded:.{decimals}f}".rstrip("0").rstrip(".")
    else:
        text = str(int(rounded))
    prefix = "minus " if neg else "about "
    if floor_zero and rounded == 0:
        return "0"
    return prefix + text


def make_key_number(label: str, value: float | int, spoken: str | None = None) -> dict:
    """Build one key_numbers entry, auto-generating an honest spoken form."""
    if not label or not isinstance(label, str):
        raise ValueError("key_number label must be a non-empty string")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("key_number value must be a number")
    return {"label": label, "spoken": speak_number(value) if spoken is None else spoken, "value": float(value)}


def _spoken_sig_digits(spoken: str) -> int:
    """Count significant digits in the first numeric token of a spoken string."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", spoken)
    if not m:
        return 0
    digits = m.group(0).replace(",", "").replace(".", "").lstrip("0")
    return len(digits) if digits else 1


def _sig_budget(value: float) -> int:
    a = abs(float(value))
    if a == 0:
        return 1
    if a < 1:
        return 1
    if a < 100:
        return 2
    return 3


def make_result(
    *,
    verdict: str,
    key_numbers: list[dict],
    confidence: str,
    data_freshness: str,
    offer: str,
    detail: dict,
    simulated: bool,
) -> dict:
    """Build and validate a tool result. Raises ValueError on contract breach."""
    if not verdict or not isinstance(verdict, str):
        raise ValueError("verdict must be a non-empty string")
    body = verdict.rstrip()
    if body.endswith("."):
        body = body[:-1]
    scrubbed = re.sub(r"\d[\d,]*\.\d+", "NUM", body)  # periods inside numbers are fine
    if "." in scrubbed or "?" in scrubbed or "!" in scrubbed:
        raise ValueError("verdict must be a single spoken sentence")
    if confidence not in CONFIDENCES:
        raise ValueError(f"confidence must be one of {CONFIDENCES}")
    if not data_freshness or not isinstance(data_freshness, str):
        raise ValueError("data_freshness must be a non-empty string")
    if not offer or not isinstance(offer, str):
        raise ValueError("offer must be a non-empty string")
    if not isinstance(detail, dict):
        raise ValueError("detail must be a dict")
    if not isinstance(simulated, bool):
        raise ValueError("simulated must be a bool")
    if not isinstance(key_numbers, list):
        raise ValueError("key_numbers must be a list")
    for kn in key_numbers:
        if set(kn.keys()) != {"label", "spoken", "value"}:
            raise ValueError("key_number entries must have exactly label/spoken/value")
        if not isinstance(kn["label"], str) or not kn["label"]:
            raise ValueError("key_number label must be a non-empty string")
        if not isinstance(kn["spoken"], str) or not kn["spoken"]:
            raise ValueError("key_number spoken must be a non-empty string")
        v = kn["value"]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("key_number value must be a number")
        if _spoken_sig_digits(kn["spoken"]) > _sig_budget(v) + 1:
            raise ValueError(
                f"spoken {kn['spoken']!r} carries more precision than {v} earns"
            )
    if simulated and not any(w in data_freshness.lower() for w in _SIMULATED_WORDS):
        raise ValueError("simulated results must say so in data_freshness")
    return {
        "summary": {
            "verdict": body + ".",
            "key_numbers": key_numbers,
            "confidence": confidence,
            "data_freshness": data_freshness,
            "offer": offer,
        },
        "detail": detail,
        "simulated": simulated,
    }


def no_data_result(reason: str, *, detail: dict | None = None) -> dict:
    """Honest silence: the tool could not produce numbers, and says so."""
    return make_result(
        verdict=f"I do not have usable data for that request: {reason}",
        key_numbers=[],
        confidence="low",
        data_freshness="No data available; nothing was computed.",
        offer="Ask me to retry with different inputs, or say detail for what I attempted.",
        detail=detail or {},
        simulated=True,
    )
