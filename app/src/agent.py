import json
from typing import Any, Callable, Dict, List, Optional
import logging

import litellm  # type: ignore
from pydantic import BaseModel  # type: ignore

from src.mcp_client import MCPServerClient
from src.tool_models import Tool
from src.tool_manager import ToolManager

logger = logging.getLogger("agent")


class ChatAgent:
    def __init__(
        self, max_iterations: int = 10, use_tool_manager: bool = True
    ):
        # System message to guide the agent
        system_message = {
            "role": "system",
            "content": (
                "You are an autonomous AI assistant with access to tools. "
                "Your primary goal is to EXECUTE the user's request using available tools. "
                "CRITICAL INSTRUCTION: When you use search_tools and it returns relevant tools, you MUST use them IMMEDIATELY in the next turn. "
                "DO NOT ask for permission. DO NOT say 'I found a tool, should I use it?'. Just USE the tool. "
                "If the user says 'create a page' and you find 'create_page', call create_page(title=...) immediately. "
                "Assume the user wants you to take action, not just chat about it."
            ),
        }

        self.messages: List[Dict[str, Any]] = [system_message]
        self.tools: List[Tool] = []
        self.max_iterations: int = max_iterations
        self.current_iteration: int = 0
        self.tool_map: Dict[str, Callable[..., str]] = {}
        self.mcp_servers: Dict[str, MCPServerClient] = {}
        self.mcp_tools: Dict[str, List[Dict[str, Any]]] = (
            {}
        )  # server_name -> tools

        # Tool Manager for lazy loading
        self.use_tool_manager = use_tool_manager
        self.tool_manager = ToolManager() if use_tool_manager else None

        if self.tool_manager:
            # Register the search_tools function
            self.tool_map["search_tools"] = self.tool_manager.search
            logger.info(
                "🔧 ToolManager enabled - tools will be loaded on-demand"
            )

    def add_tool_definition(
        self,
        tool: Tool,
        keywords: Optional[List[str]] = None,
        category: str = "general",
        always_load: bool = False,
    ) -> None:
        """Add a tool definition, optionally registering with ToolManager."""
        if self.tool_manager:
            # Register with ToolManager for lazy loading
            keywords = keywords or [tool.name.replace("_", " ")]
            self.tool_manager.register_tool(
                name=tool.name,
                tool=tool,
                keywords=keywords,
                category=category,
                always_load=always_load,
            )
        else:
            # Legacy: add directly to tools list
            self.tools.append(tool)

    def add_tool_function(self, name: str, func: Callable[..., str]) -> None:
        self.tool_map[name] = func

    def add_mcp_server(self, server_name: str, mcp_client: MCPServerClient):
        self.mcp_servers[server_name] = mcp_client

    def aggregate_tools(self):
        """Get tools to send to LLM - uses ToolManager if enabled."""
        if self.tool_manager:
            # Get active tools from ToolManager + search_tools
            active_tools = self.tool_manager.get_active_tools()
            search_tool = self.tool_manager.get_search_tool()

            local_tool_schemas = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                    "origin": "local",
                }
                for tool in [search_tool] + active_tools
            ]
        else:
            # Legacy: all tools
            local_tool_schemas = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                    "origin": "local",
                }
                for tool in self.tools
            ]

        # MCP tools
        mcp_tool_schemas = []
        for server_name, mcp_client in self.mcp_servers.items():
            mcp_tool_schemas.extend(
                [dict(tool, origin=server_name) for tool in mcp_client.tools]
            )
        return local_tool_schemas + mcp_tool_schemas

    def process_message(
        self,
        user_input: str,
        user_choice_callback: Optional[Callable[[str, List[str]], str]] = None,
        on_tool_call: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_tool_result: Optional[Callable[[Dict[str, Any], str], None]] = None,
        tool_executor: Optional[Callable[[Any], Any]] = None,
    ):
        """
        Process a user message and return the final agent response.

        Args:
            user_input: The message from the user.
            user_choice_callback: Callback to resolve ambiguous tool origins.
            on_tool_call: Callback invoked when the agent decides to call a tool.
            on_tool_result: Callback invoked when a tool execution completes.
            tool_executor: Function to execute async tool calls (e.g. on a background loop).
        """
        self.messages.append({"role": "user", "content": user_input})
        tool_schemas = self.aggregate_tools()

        self.current_iteration = 0
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1

            try:
                # Log the prompt being sent
                logger.debug(f"📤 Sending prompt to LLM:")
                logger.debug(
                    f"Messages: {json.dumps(self.messages, indent=2)}"
                )

                completion = litellm.completion(
                    model="gemini/gemini-2.0-flash",
                    messages=self.messages,
                    tools=(
                        [
                            {k: v for k, v in tool.items() if k != "origin"}
                            for tool in tool_schemas
                        ]
                        if tool_schemas
                        else None
                    ),
                )

                # Guard: Check for empty response
                if not completion.choices:
                    raise Exception("Model returned an empty response.")

                # Log token usage
                usage = getattr(completion, "usage", None)
                if usage:
                    logger.info(
                        f"📊 Token Usage - "
                        f"Prompt: {usage.prompt_tokens}, "
                        f"Completion: {usage.completion_tokens}, "
                        f"Total: {usage.total_tokens}"
                    )

                choice = completion.choices[0].message
                tool_calls = getattr(choice, "tool_calls", None)

                # Log the completion result
                logger.debug(f"📥 Received completion:")
                logger.debug(f"Content: {choice.content}")
                if tool_calls:
                    logger.debug(
                        f"Tool calls: {[tc.function.name for tc in tool_calls]}"
                    )

                # Early return: No tool calls means final response
                if not tool_calls:
                    final_content = choice.content
                    if not final_content:
                        raise Exception(
                            "Agent did not return a response content."
                        )

                    logger.info("💬 Simple completion (no tool calls)")
                    logger.info(
                        f"Response: {final_content[:200]}{'...' if len(final_content) > 200 else ''}"
                    )
                    self.messages.append(
                        {"role": "assistant", "content": final_content}
                    )
                    return final_content

                # Tool calls detected - add to message history
                logger.info(
                    f"🔧 Tool calls detected: {len(tool_calls)} tool(s)"
                )
                for tc in tool_calls:
                    logger.info(
                        f"  - {tc.function.name}({tc.function.arguments[:100]}{'...' if len(tc.function.arguments) > 100 else ''})"
                    )
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": choice.content,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                            for tool_call in tool_calls
                        ],
                    }
                )

                # Process each tool call
                for tool_call in tool_calls:
                    if on_tool_call:
                        on_tool_call(tool_call)

                    name = tool_call.function.name
                    kwargs = json.loads(tool_call.function.arguments)

                    # Find tool origin
                    origins = [
                        tool["origin"]
                        for tool in tool_schemas
                        if tool["function"]["name"] == name
                    ]

                    # Guard: No origins found
                    if not origins:
                        result_str = f"Error: Tool '{name}' not found in available tools."
                        self._append_tool_result(tool_call.id, result_str)
                        if on_tool_result:
                            on_tool_result(tool_call, result_str)
                        continue

                    # Resolve origin if ambiguous
                    chosen_origin = origins[0]
                    if len(origins) > 1 and user_choice_callback:
                        chosen_origin = user_choice_callback(name, origins)

                    # Execute tool based on origin
                    result_str = self._execute_tool(
                        name, kwargs, chosen_origin, tool_executor
                    )

                    if on_tool_result:
                        on_tool_result(tool_call, result_str)

                    self._append_tool_result(tool_call.id, result_str)

            except Exception as error:
                print(f"Error: {error}")
                return f"An error occurred: {error}"

        return "Maximum iterations reached without completion."

    def _execute_tool(
        self,
        name: str,
        kwargs: Dict[str, Any],
        origin: str,
        tool_executor: Optional[Callable[[Any], Any]],
    ) -> str:
        """Execute a tool and return the result as a string."""
        # Local tool execution
        if origin == "local":
            result = self.tool_map[name](**kwargs)
            return result if isinstance(result, str) else str(result)

        # MCP tool execution
        mcp_client = self.mcp_servers[origin]

        # Guard: Require executor for MCP tools
        if not tool_executor:
            raise ValueError("tool_executor is required for MCP tool calls")

        return tool_executor(mcp_client.call_tool(name, kwargs))

    def _append_tool_result(self, tool_call_id: str, result: str) -> None:
        """Append a tool result to the message history."""
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result,
            }
        )
