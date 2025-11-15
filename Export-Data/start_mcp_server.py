#!/usr/bin/env python3
"""
Start the Peru Frozen Fruit Exports MCP Server (Coherent Architecture)

Usage:
    python start_mcp_server.py

Or add to Claude Desktop config:
    {
      "mcpServers": {
        "peru-exports": {
          "command": "python",
          "args": [
            "/path/to/Export-Data/start_mcp_server.py"
          ]
        }
      }
    }
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Start the MCP server
from mcp_tools.server import mcp

if __name__ == "__main__":
    mcp.run()
