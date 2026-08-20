"""
ai/mcp/run.py
-------------
Entry point to start the SiteSync MCP server.

Usage:
    # From project root:
    python ai/mcp/run.py

    # Or as a module:
    python -m ai.mcp.run

The server starts on http://localhost:8001 by default.
Set MCP_PORT env var to change the port.

When deployed, replace localhost:8001 with your domain URL.
Claude Desktop config:
  {
    "mcpServers": {
      "sitesync": { "url": "http://localhost:8001/mcp" }
    }
  }
"""

import os
import sys

# Ensure project root is on path
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_here))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import uvicorn
from ai.mcp.server import mcp_app, _TOOL_REGISTRY

if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", 8001))
    print(f"\n{'='*60}")
    print(f"  SiteSync MCP Server")
    print(f"{'='*60}")
    print(f"  URL:        http://localhost:{port}")
    print(f"  Tools:      {len(_TOOL_REGISTRY)} available")
    print(f"  Info:       GET  http://localhost:{port}/mcp/info")
    print(f"  Tool list:  GET  http://localhost:{port}/mcp/tools")
    print(f"  Tool call:  POST http://localhost:{port}/mcp/call")
    print(f"  NL query:   POST http://localhost:{port}/mcp/query")
    print(f"{'='*60}\n")
    uvicorn.run(mcp_app, host="0.0.0.0", port=port, reload=False)
