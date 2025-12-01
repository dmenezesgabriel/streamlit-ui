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

        if "ui_repository" not in st.session_state:
            logger.info("Initializing UI Repository")
            st.session_state.ui_repository = SessionStateUIRepository()


class SidebarManager:
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
        if st.session_state.mcp_connected:
            return

        logger.info("Connecting to MCP servers...")

        async def _connect():
            results = []
            for config in self.mcp_configs:
                if self.mcp_configs is None:
                    continue

                if not config.enabled:
                    continue

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
                if not self.mcp_configs:
                    return
                for config in self.mcp_configs:

                    status = (
                        "Connected"
                        if config.name in self.agent.mcp_servers
                        else "Disabled/Disconnected"
                    )
                st.write(f"- **{config.name}**: {status}")


class MessageRenderer:
    def __init__(self):
        self.current_tool_calls = []

    def render_history(self, messages: List[Dict[str, Any]]):
        for message in messages:
            if message["role"] == "tool":
                continue

            with st.chat_message(message["role"]):
                st.markdown(message["content"])

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
    @staticmethod
    def _render_component(
        component: Union[UIComponent, LayoutComponent], depth: int = 0
    ):
        """Recursively render a component (content or layout)."""

        try:
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

                logger.warning(f"Unknown layout type: {component.type}")
                st.warning(f"Unknown layout type: {component.type}")
                return

            strategy = ComponentStrategyFactory.get_strategy(component.type)
            strategy.render(component)

        except ValueError as e:
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

        for component in top_level_components:
            DynamicPageRenderer._render_component(component)


class ChatInterface:
    """Main class for the Chat Interface."""

    def __init__(
        self,
        mcp_configs: List[MCPServerConfig],
        agent_factory: Callable[[], ChatAgent],
    ):
        self.mcp_configs = mcp_configs
        self.renderer = MessageRenderer()
        self.agent_factory = agent_factory

        SessionManager.initialize_state(self.agent_factory)

        self.agent: ChatAgent = st.session_state.agent
        self.loop_context: GlobalLoopContext = st.session_state.loop_context
        self.sidebar = SidebarManager(
            self.agent, self.mcp_configs, self.loop_context
        )
        self.ui_repository: StreamlitUIRepository = (
            st.session_state.ui_repository
        )

    def initialize(self):
        self.sidebar.connect_servers()

        if self.agent.tool_manager:
            stats = self.agent.tool_manager.get_stats()
            if stats["total_registered"] > 1:  # More than just search_tools
                return
        else:
            tool_names = [t.name for t in self.agent.tools]
            if "create_page" in tool_names:
                return

        ui_service = UIToolService(self.ui_repository)

        tool_metadata = ui_service.get_tool_metadata()

        tool_function_map = {
            "create_page": ui_service.create_page,
            "create_layout": ui_service.create_layout,
            "add_component": ui_service.add_component,
            "update_page": ui_service.update_page,
            "update_component": ui_service.update_component,
            "update_layout": ui_service.update_layout,
        }

        for tool in ui_service.get_tools():
            metadata = tool_metadata.get(tool.name, {})
            self.agent.add_tool_definition(
                tool,
                keywords=metadata.get("keywords", [tool.name]),
                category=metadata.get("category", "general"),
                always_load=False,  # Don't load UI tools by default
            )

            if tool.name in tool_function_map:
                self.agent.add_tool_function(
                    tool.name, tool_function_map[tool.name]
                )

        logger.info(
            f"✅ Registered {len(tool_function_map)} UI tools for lazy loading"
        )

    def _process_user_message(self, prompt: str) -> None:
        message_placeholder = st.empty()

        initial_page_count = len(self.ui_repository.get_all_pages())

        try:
            response = self.agent.process_message(
                prompt,
                user_choice_callback=self.renderer.user_choice_callback,
                on_tool_call=self.renderer.on_tool_call,
                on_tool_result=self.renderer.on_tool_result,
                tool_executor=self.loop_context.run_coroutine,
            )
            message_placeholder.markdown(response)

            tool_calls_metadata = self.renderer.get_and_clear_tool_calls()
            assistant_message = {"role": "assistant", "content": response}
            if tool_calls_metadata:
                assistant_message["tool_calls_metadata"] = tool_calls_metadata

            st.session_state.messages.append(assistant_message)

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
        if not st.session_state.mcp_connected:
            self.initialize()

        self.sidebar.render()
        self.renderer.render_history(st.session_state.messages)

        prompt = st.chat_input("What is up?")
        if not prompt:
            return

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            self._process_user_message(prompt)
