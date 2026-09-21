# Contributing

Thanks for considering a contribution. This project is an Alexa+ hackathon
entry that turns quant models into spoken answers, so it holds a few extra
rules beyond the usual.

## Setup

AlphaVoice wraps two existing quant engines, so clone them as siblings first
(or point `SIGNAL_ROOT` and `ODDS_ROOT` at wherever yours live):

```bash
mkdir -p ~/workspace
git clone https://github.com/RosarioM123/signal-research-lab.git ~/workspace/signal-build
git clone https://github.com/RosarioM123/odds-prediction-mispricing.git ~/workspace/odds-prediction-mispricing
```

Then set up and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/python -m server.main   # MCP server on port 8000
open web/index.html               # simulated web experience
```

## Tests

Run the full suite before opening a pull request:

```bash
.venv/bin/python -m pytest tests/ -q
```

The suite includes the tool-routing eval (15 utterances must route to the
correct tool) and the MCP server contract tests. Keep the suite green.

## Pull request expectations

- One change per pull request, with a short imperative title
  (for example, `docs: add Alexa integration guide`).
- Code changes come with tests. Docs changes should be accurate against the
  running server and web demo.
- Add an entry to `CHANGELOG.md` under `[Unreleased]`. This file feeds the
  Devpost story, so describe what changed and why.
- Anything user-facing (README, docs, web UI text) must be written for ears:
  short sentences, plain words, no jargon the spoken version would choke on.
- New tools must follow the summary/detail contract: a speakable summary under
  a 30-second budget, with the full detail payload one question away.

## Hard rules

- **Paper only.** Never add order placement, trading keys, or execution paths.
  The mispricing tool reports hypothetical sizes only.
- **Simulated data stays labeled simulated.** No live-performance claims.
- **No secrets** in code, logs, or commits. Ever.
- Do not touch `LICENSE` (MIT, pending confirmation) or the engine repos
  (`signal-research-lab`, `odds-prediction-mispricing`); contribute to those
  projects separately.
