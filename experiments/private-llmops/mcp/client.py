"""
mcp/client.py — MCP client with trace context propagation.

Demonstrates propagating W3C Trace Context across the MCP boundary
so tool execution on the MCP server appears inside the workflow trace.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from tracing import inject_trace_context, tool_span

logging.basicConfig(level=logging=logging.INFO)
logger = logging.getLogger(__name__)


class MCPClient:
    """
    Minimal MCP client that propagates trace context.

    In a real MCP implementation, trace metadata would be carried
    through the MCP protocol's transport layer. This lab uses HTTP
    headers (W3C traceparent) to demonstrate the concept.
    """

    def __init__(self, server_url: str = "http://localhost:8020"):
        self.server_url = server_url

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server with propagated trace context.

        The traceparent header carries trace-id and parent-span-id so
        the MCP server's tool execution span joins the caller's trace.
        """
        with tool_span(f"mcp.{tool_name}", tool_type="mcp"):
            headers = {"Content-Type": "application/json"}
            headers = inject_trace_context(headers)

            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        f"{self.server_url}/tools/{tool_name}",
                        json=arguments,
                        headers=headers,
                        timeout=30.0,
                    )
                    resp.raise_for_status()
                    return resp.json()
                except httpx.ConnectError:
                    logger.warning("MCP server unreachable at %s", self.server_url)
                    return {"error": "mcp_server_unreachable"}
                except httpx.TimeoutException:
                    logger.warning("MCP server timeout for tool %s", tool_name)
                    return {"error": "mcp_timeout"}