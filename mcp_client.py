import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters  # type: ignore
from mcp.client.stdio import stdio_client  # type: ignore


class MCPServerClient:
    def __init__(
        self,
        name: str,
        server_script_path: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
    ):
        # server_script_path used with default runner: `uv run <script>`
        self.server_script_path = server_script_path
        # explicit command and args (e.g. command='npx', args=['@playwright/mcp@latest'])
        self.command = command
        self.args = args or []
        self.name = name
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
        self.tools: List[Dict[str, Any]] = []

    async def connect(self):
        # Require explicit `command` + `args` to start MCP servers. No implicit `uv run` fallback.
        if not self.command:
            raise ValueError(
                "MCPServerClient requires a 'command' to start the server. Provide command+args in the MCP config."
            )

        server_params = StdioServerParameters(
            command=self.command, args=self.args
        )
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()
        await self.fetch_tools()

    async def disconnect(self):
        await self.exit_stack.aclose()

    async def fetch_tools(self):
        if self.session is None:
            raise Exception("No session")
        tools_result = await self.session.list_tools()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
                "origin": self.name,
            }
            for tool in tools_result.tools
        ]

    async def call_tool(self, name: str, arguments: dict):
        if self.session is None:
            raise Exception("No session")
        result = await self.session.call_tool(name, arguments=arguments)
        if hasattr(result, "content"):
            content_str = json.dumps(
                [
                    (
                        {"type": item.type, "text": item.text}
                        if hasattr(item, "text")
                        else str(item)
                    )
                    for item in result.content
                ]
            )
        else:
            content_str = str(result)
        return content_str
