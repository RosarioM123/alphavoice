"""Compatibility alias: `python -m server.main` from the repo root.

The canonical entry point is `server/mcp_server.py`
(`python -m server.mcp_server`). This shim exists because sibling docs
reference `python -m server.main`.
"""

from server.mcp_server import main

if __name__ == "__main__":
    main()
