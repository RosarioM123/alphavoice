"""Hawkes microstructure adapter.

Fits a bivariate Hawkes model (news -> price) with the real `tick` package
(`tick.hawkes.SimuHawkesExpKernels` for synthesis, `tick.hawkes.HawkesExpKern`
for the fit). The metric computation (alpha_10 news-to-price impact,
half-life ln(2)/beta, sub-critical vs explosive regime from the spectral
radius) is vendored here following ~/workspace/hawkes/hawkes_fit.py.

Deliberately NOT imported: hawkes_fit.py (simulates, fits, and prints at
import time). Only the metric math is reused, per the recon note.

The event streams are synthetic (seeded), so results are simulated=True;
the estimator itself is the real tick maximum-likelihood fit.
"""

from __future__ import annotations

import re

import numpy as np
import tick
from tick.hawkes import HawkesExpKern, SimuHawkesExpKernels

# tick lazily loads its model/solver/prox submodules; import everything once
# so the attr-repair lookup below can find any class by name.
import pkgutil as _pkgutil
import importlib as _importlib

for _mod in _pkgutil.walk_packages(tick.__path__, tick.__name__ + "."):
    try:
        _importlib.import_module(_mod.name)
    except Exception:
        pass
del _pkgutil, _importlib, _mod

TRUE_BETA = 2.0
TRUE_ALPHA = np.array([[0.30, 0.00], [0.50, 0.20]])  # dim 0 = news, dim 1 = price
BASELINES = np.array([0.40, 1.20])


def _tick_class_by_name(name: str):
    import sys

    candidates = []
    for cls in HawkesExpKern.mro():
        if cls.__name__ == name:
            candidates.append(cls)
    for mod_name, mod in sys.modules.items():
        if mod_name == "tick" or mod_name.startswith("tick."):
            obj = getattr(mod, name, None)
            if isinstance(obj, type) and obj not in candidates:
                candidates.append(obj)
    # Prefer the BaseMeta-managed Python wrapper over the raw C++ binding.
    for cls in candidates:
        if "_attrinfos" in getattr(cls, "__dict__", {}):
            return cls
    raise RuntimeError(f"tick class {name} not found for attr repair")


def _repair_from_error(exc: AttributeError) -> bool:
    """Register one missing tick attribute. Returns False if unrecognized."""
    msg = str(exc)
    attr = re.search(r"no settable attribute '(\w+)'", msg)
    cls_name = re.search(r"'(\w+)' object has no settable attribute", msg)
    if not attr or not cls_name:
        return False
    _tick_class_by_name(cls_name.group(1))._attrinfos.setdefault(
        attr.group(1), {"writable": True}
    )
    return True


def _make_learner(**kwargs) -> HawkesExpKern:
    """Construct HawkesExpKern, repairing tick 0.8.0.2's attr registry as needed.

    This tick build's BaseMeta rejects attributes its own constructors set
    (e.g. ``events``, ``dtype``) because they are missing from the generated
    attr registry even though they are documented. Register each missing name
    (bounded retries) so the real estimator can be used.
    """
    for _ in range(64):
        try:
            return HawkesExpKern(**kwargs)
        except AttributeError as exc:
            if not _repair_from_error(exc):
                raise
    raise RuntimeError("could not repair tick learner attribute registry")


def _fit_learner(learner: HawkesExpKern, timestamps) -> None:
    """Fit, repairing the model/solver attr registry the same way."""
    for _ in range(64):
        try:
            learner.fit(timestamps)
            return
        except AttributeError as exc:
            if not _repair_from_error(exc):
                raise
    raise RuntimeError("could not repair tick model attribute registry")


def simulate_streams(end_time: float, seed: int = 11) -> list[np.ndarray]:
    """Synthesize news (dim 0) and price-jump (dim 1) timestamps."""
    sim = SimuHawkesExpKernels(
        adjacency=TRUE_ALPHA,
        decays=TRUE_BETA,
        baseline=BASELINES,
        end_time=end_time,
        seed=seed,
        verbose=False,
    )
    sim.simulate()
    return sim.timestamps


def fit_hawkes(timestamps: list[np.ndarray], betas: np.ndarray | None = None) -> dict:
    """Grid-search beta, fit HawkesExpKern, return the microstructure metrics.

    This is the ~6-line metric core from the user's hawkes_fit.py, adapted:
    alpha_10 = alpha[1, 0]; half-life = ln(2)/beta; endogeneity = spectral
    radius of alpha; regime sub-critical when it is below 1.
    """
    if betas is None:
        betas = np.linspace(0.5, 5.0, 6)
    best_ll, best_beta, best_model = -np.inf, None, None
    for beta in betas:
        learner = _make_learner(decays=float(beta), penalty="l2", C=1e4, max_iter=100)
        _fit_learner(learner, timestamps)
        ll = learner.score()
        if ll > best_ll:
            best_ll, best_beta, best_model = ll, float(beta), learner
    alpha = np.asarray(best_model.adjacency)
    alpha_10 = float(alpha[1, 0])
    half_life = float(np.log(2) / best_beta)
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(alpha))))
    regime = "sub-critical" if spectral_radius < 1.0 else "explosive"
    return {
        "beta": best_beta,
        "alpha_10": alpha_10,
        "half_life": half_life,
        "spectral_radius": spectral_radius,
        "regime": regime,
        "log_likelihood": float(best_ll),
        "n_events": int(sum(len(t) for t in timestamps)),
    }


def run_news_microstructure(window_minutes: int = 390, seed: int = 11) -> dict:
    """Fit the Hawkes model on synthetic streams over the requested window.

    One stream time unit is treated as one minute of the window.
    """
    if window_minutes is None or window_minutes <= 0:
        return {"ok": False, "reason": "window_minutes must be positive"}
    timestamps = simulate_streams(end_time=float(window_minutes), seed=seed)
    if sum(len(t) for t in timestamps) < 20:
        return {"ok": False, "reason": "too few synthetic events to fit"}
    metrics = fit_hawkes(timestamps)
    metrics.update(
        {
            "ok": True,
            "simulated": True,
            "freshness": (
                "Synthetic news and price-jump streams (deterministic seed 11, "
                f"{window_minutes}-minute window); fit just now with the real "
                "tick HawkesExpKern maximum-likelihood estimator. Illustrative only."
            ),
        }
    )
    return metrics
