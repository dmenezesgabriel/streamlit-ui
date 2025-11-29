import asyncio
import streamlit as st
from typing import List, Optional, Callable, Dict, Any, Union
from src.agent import ChatAgent
from src.mcp_client import MCPServerClient
from src.tools import greeting, greeting_tool
from src.config import MCPServerConfig
from src.repositories import SessionStateUIRepository, StreamlitUIRepository
from src.ui_tools import UIToolService
from src.models import (
    UIPage,
    ComponentType,
    LayoutComponent,
    LayoutType,
    UIComponent,
)
from src.async_utils import GlobalLoopContext
import logging
from src.component_strategies import ComponentStrategyFactory

logger = logging.getLogger("ui")


class SessionManager:
    """Manages Streamlit session state initialization."""

    @staticmethod
    def initialize_state(agent_factory: Callable[[], ChatAgent]):
        if "loop_context" not in st.session_state:
            logger.info("Initializing GlobalLoopContext")
            loop_context = GlobalLoopContext()
            loop_context.start()
            st.session_state.loop_context = loop_context

        if "agent" not in st.session_state:
            logger.info("Initializing ChatAgent")
            st.session_state.agent = agent_factory()
            st.session_state.mcp_connected = False

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Initialize UI Repository (it handles its own session state check)
        if "ui_repository" not in st.session_state:
            logger.info("Initializing UI Repository")
            st.session_state.ui_repository = SessionStateUIRepository()


class SidebarManager:
    """Manages the sidebar and MCP server connections."""

    def __init__(
        self,
        agent: ChatAgent,
        mcp_configs: List[MCPServerConfig],
        loop_context: GlobalLoopContext,
    ):
        self.agent = agent
        self.mcp_configs = mcp_configs
        self.loop_context = loop_context

    def connect_servers(self):
        # Guard: Already connected
        if st.session_state.mcp_connected:
            return

        logger.info("Connecting to MCP servers...")
        # We run the connection logic on the background loop
        # But we need to update session state and toast, which must be done in the main thread.
        # However, run_coroutine blocks until done, so we are back in main thread after it returns.

        async def _connect():
            results = []
            for config in self.mcp_configs:
                # Guard: Skip disabled servers
                if not config.enabled:
                    continue

                # Guard: Skip already connected servers
                if config.name in self.agent.mcp_servers:
                    continue

                try:
                    logger.debug(f"Connecting to {config.name}...")
                    client = MCPServerClient(
                        name=config.name,
                        command=config.command,
                        args=config.args,
                    )
                    await client.connect()
                    self.agent.add_mcp_server(config.name, client)
                    results.append((config.name, True, None))
                except Exception as exc:
                    logger.error(f"Failed to connect to {config.name}: {exc}")
                    results.append((config.name, False, str(exc)))
            return results

        results = self.loop_context.run_coroutine(_connect())

        for name, success, error in results:
            if success:
                st.toast(f"Connected to MCP server '{name}'", icon="✅")
            else:
                st.error(f"Failed to connect to '{name}': {error}")

        st.session_state.mcp_connected = True

    def render(self):
        with st.sidebar:
            st.header("System Status")
            with st.expander("MCP Servers:"):
                for config in self.mcp_configs:
                    status = (
                        "Connected"
                        if config.name in self.agent.mcp_servers
                        else "Disabled/Disconnected"
                    )
                st.write(f"- **{config.name}**: {status}")


class MessageRenderer:
    """Responsible for rendering chat messages and tool updates."""

    def __init__(self):
        self.current_tool_calls = []  # Temporary storage for current execution

    def render_history(self, messages: List[Dict[str, Any]]):
        for message in messages:
            # Guard: Skip tool messages
            if message["role"] == "tool":
                continue

            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Render stored tool calls and results
                if "tool_calls_metadata" in message:
                    for tool_meta in message["tool_calls_metadata"]:
                        with st.status(
                            f"Called tool: {tool_meta['name']}",
                            state="complete",
                        ):
                            st.write(f"Arguments: ")
                            st.json(tool_meta["arguments"])

                        if "result" in tool_meta:
                            with st.expander(
                                f"Result from {tool_meta['name']}"
                            ):
                                st.code(tool_meta["result"])

    def on_tool_call(self, tool_call):
        logger.info(f"🔧 Tool call initiated: {tool_call.function.name}")
        logger.debug(f"Tool arguments: {tool_call.function.arguments}")

        # Store tool call metadata
        tool_meta = {
            "name": tool_call.function.name,
            "arguments": tool_call.function.arguments,
        }
        self.current_tool_calls.append(tool_meta)

        with st.status(
            f"Calling tool: {tool_call.function.name}...", expanded=False
        ) as status:
            st.write(f"Arguments:   ")
            st.json(tool_call.function.arguments)
            status.update(
                label=f"Called tool: {tool_call.function.name}",
                state="complete",
            )

    def on_tool_result(self, tool_call, result):
        logger.info(f"✅ Tool result received: {tool_call.function.name}")
        logger.debug(f"Result preview: {result[:200]}...")

        # Add result to the most recent tool call with matching name
        for tool_meta in reversed(self.current_tool_calls):
            if (
                tool_meta["name"] == tool_call.function.name
                and "result" not in tool_meta
            ):
                tool_meta["result"] = result
                break

        with st.expander(f"Result from {tool_call.function.name}"):
            st.code(result)

    def get_and_clear_tool_calls(self) -> List[Dict[str, Any]]:
        """Get current tool calls and clear the list for next execution."""
        tool_calls = self.current_tool_calls.copy()
        self.current_tool_calls = []
        return tool_calls

    def user_choice_callback(self, tool_name: str, origins: List[str]) -> str:
        logger.warning(f"Ambiguous tool {tool_name} in {origins}")
        st.warning(
            f"Ambiguous tool '{tool_name}' found in {origins}. Defaulting to {origins[0]}."
        )
        return origins[0]


class DynamicPageRenderer:
    """Renders dynamic pages based on UIPage models using Strategy pattern."""

    @staticmethod
    def _render_component(
        component: Union[UIComponent, LayoutComponent], depth: int = 0
    ):
        """Recursively render a component (content or layout)."""

        try:
            # Handle layout components
            if isinstance(component, LayoutComponent):
                if component.type == LayoutType.COLUMNS:
                    spec = component.props.get(
                        "spec", len(component.children) or 1
                    )
                    gap = component.props.get("gap", "small")
                    vertical_alignment = component.props.get(
                        "vertical_alignment", "top"
                    )
                    border = component.props.get("border", False)

                    cols = st.columns(
                        spec,
                        gap=gap,
                        vertical_alignment=vertical_alignment,
                        border=border,
                    )

                    # Render children into columns
                    for idx, child in enumerate(component.children):
                        if idx < len(cols):
                            with cols[idx]:
                                DynamicPageRenderer._render_component(
                                    child, depth + 1
                                )
                    return

                if component.type == LayoutType.CONTAINER:
                    border = component.props.get("border")
                    height = component.props.get("height", "content")
                    width = component.props.get("width", "stretch")
                    horizontal = component.props.get("horizontal", False)
                    gap = component.props.get("gap", "small")

                    with st.container(
                        border=border,
                        height=height,
                        width=width,
                        horizontal=horizontal,
                        gap=gap,
                    ):
                        # Render children inside container
                        for child in component.children:
                            DynamicPageRenderer._render_component(
                                child, depth + 1
                            )
                    return

                # Unknown layout type
                logger.warning(f"Unknown layout type: {component.type}")
                st.warning(f"Unknown layout type: {component.type}")
                return

            # Handle content components using Strategy pattern
            strategy = ComponentStrategyFactory.get_strategy(component.type)
            strategy.render(component)

        except ValueError as e:
            # Strategy not found
            logger.warning(f"Unknown component type: {component.type}")
            st.warning(f"Unknown component type: {component.type}")
        except Exception as e:
            logger.error(
                f"Error rendering component {component.id}: {e}", exc_info=True
            )
            st.error(f"Failed to render component: {e}")
            if hasattr(component, "type"):
                st.json(
                    {
                        "type": (
                            component.type.value
                            if hasattr(component.type, "value")
                            else str(component.type)
                        ),
                        "id": component.id,
                    }
                )

    @staticmethod
    def render_page(page: UIPage):
        """Render a complete page with all its components."""
        st.title(page.title)

        # Build a tree structure: separate top-level components from nested ones
        top_level_components = [
            c
            for c in page.components
            if not hasattr(c, "parent_id") or c.parent_id is None
        ]

        # Render top-level components
        for component in top_level_components:
            DynamicPageRenderer._render_component(component)


class ChatInterface:
    """Main class for the Chat Interface."""

    def __init__(self, mcp_configs: List[MCPServerConfig]):
        self.mcp_configs = mcp_configs
        self.renderer = MessageRenderer()

        # Initialize session
        SessionManager.initialize_state(self._create_agent)
        self.agent: ChatAgent = st.session_state.agent
        self.loop_context: GlobalLoopContext = st.session_state.loop_context
        self.sidebar = SidebarManager(
            self.agent, self.mcp_configs, self.loop_context
        )
        self.ui_repository: StreamlitUIRepository = (
            st.session_state.ui_repository
        )

    def _create_agent(self) -> ChatAgent:
        agent = ChatAgent()
        agent.add_tool_definition(greeting_tool)
        agent.add_tool_function("greeting", greeting)

        # Add UI tools
        # Note: We need to access the repository, but it might not be initialized yet when this runs inside initialize_state.
        # However, initialize_state initializes ui_repository immediately after agent if not present.
        # But here we are passing a factory.
        # A better approach is to add tools AFTER agent creation in __init__ if possible, or lazy load.
        # For now, we will add them in __init__ of ChatInterface to ensure repository exists.
        return agent

    def initialize(self):
        # Synchronous wrapper that calls async logic on background loop
        self.sidebar.connect_servers()

        # Guard: Tools already registered
        tool_names = [t.name for t in self.agent.tools]
        if "create_page" in tool_names:
            return

        # Register UI tools
        ui_service = UIToolService(self.ui_repository)

        # Map tool names to their implementation methods
        tool_function_map = {
            "create_page": ui_service.create_page,
            "create_layout": ui_service.create_layout,
            "add_component": ui_service.add_component,
            "update_page": ui_service.update_page,
            "update_component": ui_service.update_component,
            "update_layout": ui_service.update_layout,
        }

        for tool in ui_service.get_tools():
            self.agent.add_tool_definition(tool)

            # Register tool function using mapping
            if tool.name in tool_function_map:
                self.agent.add_tool_function(
                    tool.name, tool_function_map[tool.name]
                )

    def _process_user_message(self, prompt: str) -> None:
        """Process a user message and handle the agent response."""
        message_placeholder = st.empty()

        # Capture initial page count to detect changes
        initial_page_count = len(self.ui_repository.get_all_pages())

        try:
            # Run the agent logic synchronously (callbacks in main thread)
            response = self.agent.process_message(
                prompt,
                user_choice_callback=self.renderer.user_choice_callback,
                on_tool_call=self.renderer.on_tool_call,
                on_tool_result=self.renderer.on_tool_result,
                tool_executor=self.loop_context.run_coroutine,
            )
            message_placeholder.markdown(response)

            # Get tool calls metadata and save with message
            tool_calls_metadata = self.renderer.get_and_clear_tool_calls()
            assistant_message = {"role": "assistant", "content": response}
            if tool_calls_metadata:
                assistant_message["tool_calls_metadata"] = tool_calls_metadata

            st.session_state.messages.append(assistant_message)

            # Check if pages changed and rerun if necessary
            final_page_count = len(self.ui_repository.get_all_pages())
            if final_page_count != initial_page_count:
                logger.info(
                    "Page count changed, rerunning to update navigation."
                )
                st.rerun()

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            st.error(f"An error occurred: {e}")

    def run(self):
        # Guard: Initialize if not connected
        if not st.session_state.mcp_connected:
            self.initialize()

        self.sidebar.render()
        self.renderer.render_history(st.session_state.messages)

        # Guard: No input, nothing to do
        prompt = st.chat_input("What is up?")
        if not prompt:
            return

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process with assistant
        with st.chat_message("assistant"):
            self._process_user_message(prompt)
