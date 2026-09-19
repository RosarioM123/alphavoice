"""AlphaVoice MCP server entry point.

Uses the official MCP Python SDK (mcp.server): tool definitions on an
MCPServer instance, served over Streamable HTTP at /mcp (MCP spec 2025-11-25).

Run:
    ~/workspace/alphavoice/.venv/bin/python -m server.mcp_server
Serves http://localhost:8000/mcp
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.mcpserver import MCPServer  # noqa: E402

from tools.mispricing_check import mispricing_check  # noqa: E402
from tools.news_microstructure import news_microstructure  # noqa: E402
from tools.signal_scan import signal_scan  # noqa: E402

mcp = MCPServer("alphavoice")


@mcp.tool(
    name="signal_scan",
    description=(
        "Scan market signals with the SIGNAL engine: six signal families plus "
        "a ridge combiner, ranked by expected return. Simulated price panel."
    ),
)
def _signal_scan(query: str, symbols: str = "AAPL,MSFT,NVDA", horizon_days: int = 5, top_n: int = 3) -> dict:
    return signal_scan(query, symbols=symbols, horizon_days=horizon_days, top_n=top_n)


@mcp.tool(
    name="mispricing_check",
    description=(
        "Check cross-venue prediction-market mispricing with the ODDS engine: "
        "full-book VWAP, cost waterfall, fractional Kelly sizing. PAPER ONLY, "
        "reports hypothetical size, never executes."
    ),
)
def _mispricing_check(query: str, size: float = 100.0, bankroll: float = 100.0, kelly_fraction: float = 0.25) -> dict:
    return mispricing_check(query, size=size, bankroll=bankroll, kelly_fraction=kelly_fraction)


@mcp.tool(
    name="news_microstructure",
    description=(
        "Measure how news moves prices with a Hawkes model: news-to-price "
        "impact (alpha_10), half-life, sub-critical vs explosive regime. "
        "Fit with tick on synthetic streams."
    ),
)
def _news_microstructure(query: str, window_minutes: int = 390) -> dict:
    return news_microstructure(query, window_minutes=window_minutes)


def main() -> None:
    import os

    import uvicorn

    app = mcp.streamable_http_app(streamable_http_path="/mcp")
    port = int(os.environ.get("ALPHAVOICE_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
