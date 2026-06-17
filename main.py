"""
Zoho Projects MCP Server
Full Zoho Projects v3 API coverage via FastMCP with SSE transport.
"""

import os
import uvicorn
from api.tools import mcp

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = mcp.sse_app()
    uvicorn.run(app, host="0.0.0.0", port=port)
