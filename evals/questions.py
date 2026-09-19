"""Eval questions for the AlphaVoice tool-routing harness.

Each entry is a natural-language question with a gold ``expected`` set of
MCP tool names (exact names, as registered in server/mcp_server.py plus the
designed market_brief composed path) and a category:

- "single": clearly one tool.
- "ambiguous": two or three tools; the router should return all of them.
- "out_of_scope": no tool applies; the honest answer is the empty set.
"""

QUESTIONS = [
    # --- Clearly single-tool (5) ---
    {
        "id": "S1",
        "category": "single",
        "question": "Is anything mispriced right now?",
        "expected": {"mispricing_check"},
    },
    {
        "id": "S2",
        "category": "single",
        "question": "How fast did the market absorb the CPI print?",
        "expected": {"news_microstructure"},
    },
    {
        "id": "S3",
        "category": "single",
        "question": "What signals are firing today?",
        "expected": {"signal_scan"},
    },
    {
        "id": "S4",
        "category": "single",
        "question": "Morning brief please.",
        "expected": {"market_brief"},
    },
    {
        "id": "S5",
        "category": "single",
        "question": "Which names show the strongest momentum right now?",
        "expected": {"signal_scan"},
    },
    # --- Ambiguous multi-tool (5) ---
    {
        "id": "A1",
        "category": "ambiguous",
        "question": "Given this morning's CPI print, is my prediction-market position still sane?",
        "expected": {"news_microstructure", "mispricing_check"},
    },
    {
        "id": "A2",
        "category": "ambiguous",
        "question": "CPI is out, what is moving and is anything mispriced?",
        "expected": {"news_microstructure", "signal_scan", "mispricing_check"},
    },
    {
        "id": "A3",
        "category": "ambiguous",
        "question": "The Fed just spoke, how did prices react, and should I scan for momentum plays?",
        "expected": {"news_microstructure", "signal_scan"},
    },
    {
        "id": "A4",
        "category": "ambiguous",
        "question": "Give me the morning brief, and check whether the election market is mispriced.",
        "expected": {"market_brief", "mispricing_check"},
    },
    {
        "id": "A5",
        "category": "ambiguous",
        "question": "Is there arbitrage between Polymarket and Kalshi on the inflation print?",
        "expected": {"mispricing_check", "news_microstructure"},
    },
    # --- Out of scope: honest silence (5) ---
    {
        "id": "O1",
        "category": "out_of_scope",
        "question": "What's the weather in Boston this weekend?",
        "expected": set(),
    },
    {
        "id": "O2",
        "category": "out_of_scope",
        "question": "Should I buy a house this year?",
        "expected": set(),
    },
    {
        "id": "O3",
        "category": "out_of_scope",
        "question": "Draft a birthday toast for my dad.",
        "expected": set(),
    },
    {
        "id": "O4",
        "category": "out_of_scope",
        "question": "Explain how photosynthesis works.",
        "expected": set(),
    },
    {
        "id": "O5",
        "category": "out_of_scope",
        "question": "What's a good recipe for lasagna?",
        "expected": set(),
    },
]
