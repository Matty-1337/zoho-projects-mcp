"""
Zoho Projects MCP Server
Full Zoho Projects v3 API coverage via FastMCP with SSE transport.
"""

import os
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from api.tools import mcp


async def health(request):
    return JSONResponse({"status": "ok", "service": "zoho-projects-mcp"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    sse = mcp.sse_app()
    app = Starlette(routes=[
        Route("/health", health),
        Mount("/", app=sse),
    ])
    uvicorn.run(app, host="0.0.0.0", port=port)
