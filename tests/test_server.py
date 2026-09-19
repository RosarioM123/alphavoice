"""MCP server tests: tool registry plus a real Streamable HTTP round trip."""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_NAMES = {"signal_scan", "mispricing_check", "news_microstructure", "market_brief"}
E2E_PORT = 8123


def test_server_registers_exact_four_tools():
    import mcp_server

    async def _list():
        return await mcp_server.mcp.list_tools()

    tools = asyncio.run(_list())
    assert {t.name for t in tools} == TOOL_NAMES


def test_tool_descriptions_present():
    import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    for t in tools:
        assert t.description and len(t.description) > 20


def _wait_for_port(port: int, timeout: float = 25.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.3)
    raise TimeoutError(f"server did not come up on port {port}")


PROXY_VARS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def _clean_env(base: dict | None = None) -> dict:
    env = dict(base if base is not None else os.environ)
    for var in PROXY_VARS:
        env.pop(var, None)
    return env


@pytest.fixture(scope="module")
def live_server():
    env = _clean_env(dict(os.environ, ALPHAVOICE_PORT=str(E2E_PORT)))
    proc = subprocess.Popen(
        [sys.executable, "-m", "server.mcp_server"],
        cwd=str(REPO_ROOT),
        env={**env, "PYTHONPATH": str(REPO_ROOT / "server")},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port(E2E_PORT)
        yield f"http://127.0.0.1:{E2E_PORT}/mcp"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def _client_round_trip(url: str):
    import httpx2
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async def _run():
        # trust_env=False: localhost tests must not go through the sandbox proxy
        async with httpx2.AsyncClient(trust_env=False) as http_client:
            async with streamable_http_client(
                url, http_client=http_client
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {t.name for t in tools.tools}
                    results = {}
                    for name in TOOL_NAMES:
                        res = await session.call_tool(name, {"query": "e2e check"})
                        text = res.content[0].text
                        results[name] = json.loads(text)
                    return names, results

    return asyncio.run(_run())


def test_e2e_list_tools_shows_all_four(live_server):
    names, _ = _client_round_trip(live_server)
    assert names == TOOL_NAMES


def test_e2e_tool_results_match_contract(live_server):
    _, results = _client_round_trip(live_server)
    assert set(results.keys()) == TOOL_NAMES
    for name, r in results.items():
        assert set(r.keys()) == {"summary", "detail", "simulated"}, name
        assert set(r["summary"].keys()) == {
            "verdict",
            "key_numbers",
            "confidence",
            "data_freshness",
            "offer",
        }, name
        assert r["summary"]["verdict"].endswith(".")
        assert r["summary"]["confidence"] in ("high", "medium", "low")
        assert r["summary"]["offer"]
        assert r["simulated"] is True


def test_e2e_mispricing_is_paper_only(live_server):
    _, results = _client_round_trip(live_server)
    assert results["mispricing_check"]["detail"]["paper_only"] is True
