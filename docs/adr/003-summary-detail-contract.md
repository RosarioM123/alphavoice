# ADR 003: The summary/detail response contract

Date: 2026-09-18
Status: Accepted

## Context

A spoken answer has a 30-second budget. The full quant payload (cost
waterfall, per-family contributions, Hawkes fit parameters) does not fit
in one turn, but dropping it would make the answer uncheckable. Voice
agents fail here in two opposite ways: reading a wall of numbers, or
summarizing so aggressively the user cannot audit the claim.

## Decision

Every tool returns one JSON shape, enforced by `server/tools/contract.py`
and tested in `tests/test_contract.py`:

- `summary`: a single spoken sentence (`verdict`), a few `key_numbers`
  each with an exact `value` and a pre-rounded `spoken` form, qualitative
  `confidence`, a `data_freshness` string, and an `offer` of more detail.
- `detail`: the full payload, one question away.
- `simulated`: a boolean flag on every result.

The contract validator rejects breaches at construction time: multi-sentence
verdicts, missing offers, simulated data not labeled as simulated, or spoken
forms carrying more precision than the value earns.

## Consequences

- Speech formatting lives in one place (`speak_number`, `make_key_number`),
  which is where the trailing-zeros rounding bug was caught and fixed
  (see `docs/friction-log.md`).
- The web sim and any future Alexa skill both render from the same shape:
  speak `summary`, offer `detail` as the follow-up.
- The contract is a choke point: a new engine must fit it, which forces
  speakable output from day one.
