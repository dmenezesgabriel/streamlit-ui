import asyncio
import streamlit as st
from typing import List, Optional, Callable, Dict, Any
from agent import ChatAgent
from mcp_client import MCPServerClient
from tools import greeting, greeting_tool
from config import MCPServerConfig
from repositories import SessionStateUIRepository, StreamlitUIRepository
from ui_tools import UIToolService
from models import UIPage, ComponentType
from async_utils import GlobalLoopContext


import logging

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
        if st.session_state.mcp_connected:
            return

        logger.info("Connecting to MCP servers...")
        # We run the connection logic on the background loop
        # But we need to update session state and toast, which must be done in the main thread.
        # However, run_coroutine blocks until done, so we are back in main thread after it returns.

        async def _connect():
            connected_count = 0
            results = []
            for config in self.mcp_configs:
                if not config.enabled:
                    continue

                try:
                    if config.name in self.agent.mcp_servers:
                        continue

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
            st.write("MCP Servers:")
            for config in self.mcp_configs:
                status = (
                    "🟢 Connected"
                    if config.name in self.agent.mcp_servers
                    else "⚪ Disabled/Disconnected"
                )
                st.write(f"- **{config.name}**: {status}")


class MessageRenderer:
    """Responsible for rendering chat messages and tool updates."""

    def render_history(self, messages: List[Dict[str, Any]]):
        for message in messages:
            # We skip tool calls in the main history if we want a cleaner look,
            # or render them differently. For now, standard rendering.
            if message["role"] == "tool":
                continue  # Tool results are usually shown inside the assistant's turn or skipped

            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "tool_calls" in message:
                    for tool_call in message["tool_calls"]:
                        with st.status(
                            f"Used tool: {tool_call['function']['name']}",
                            state="complete",
                        ):
                            st.write(
                                f"Arguments: {tool_call['function']['arguments']}"
                            )

    def on_tool_call(self, tool_call):
        logger.info(f"🔧 Tool call initiated: {tool_call.function.name}")
        logger.debug(f"Tool arguments: {tool_call.function.arguments}")
        with st.status(
            f"Calling tool: {tool_call.function.name}...", expanded=False
        ) as status:
            st.write(f"Arguments: {tool_call.function.arguments}")
            status.update(
                label=f"Called tool: {tool_call.function.name}",
                state="complete",
            )

    def on_tool_result(self, tool_call, result):
        logger.info(f"✅ Tool result received: {tool_call.function.name}")
        logger.debug(f"Result preview: {result[:200]}...")
        with st.expander(f"Result from {tool_call.function.name}"):
            st.code(result)

    def user_choice_callback(self, tool_name: str, origins: List[str]) -> str:
        logger.warning(f"Ambiguous tool {tool_name} in {origins}")
        st.warning(
            f"Ambiguous tool '{tool_name}' found in {origins}. Defaulting to {origins[0]}."
        )
        return origins[0]


class DynamicPageRenderer:
    """Renders dynamic pages based on UIPage models."""

    @staticmethod
    def render_page(page: UIPage):
        st.title(page.title)
        for component in page.components:
            try:
                if component.type == ComponentType.TEXT:
                    st.write(component.data)
                elif component.type == ComponentType.MARKDOWN:
                    st.markdown(component.data)
                elif component.type == ComponentType.HEADER:
                    st.header(component.data)
                elif component.type == ComponentType.SUBHEADER:
                    st.subheader(component.data)
                elif component.type == ComponentType.CODE:
                    st.code(
                        component.data,
                        language=component.props.get("language", "python"),
                    )
                elif component.type == ComponentType.DATAFRAME:
                    # Parse JSON string if needed
                    data = component.data
                    if isinstance(data, str):
                        try:
                            import json
                            import pandas as pd

                            parsed = json.loads(data)
                            # Convert to DataFrame
                            if isinstance(parsed, dict) and "data" in parsed:
                                df = pd.DataFrame(
                                    parsed["data"],
                                    columns=parsed.get("columns", None),
                                )
                            else:
                                df = pd.DataFrame(parsed)
                            st.dataframe(df)
                        except Exception as e:
                            logger.error(
                                f"Failed to parse dataframe data: {e}"
                            )
                            st.error(f"Invalid dataframe data: {e}")
                            st.code(data)
                    else:
                        st.dataframe(data)
                elif component.type == ComponentType.BAR_CHART:
                    # Parse JSON string if needed
                    data = component.data
                    if isinstance(data, str):
                        try:
                            import json
                            import pandas as pd

                            parsed = json.loads(data)
                            if isinstance(parsed, dict) and "data" in parsed:
                                df = pd.DataFrame(
                                    parsed["data"],
                                    columns=parsed.get("columns", None),
                                )
                            else:
                                df = pd.DataFrame(parsed)
                            st.bar_chart(df)
                        except Exception as e:
                            logger.error(
                                f"Failed to parse bar chart data: {e}"
                            )
                            st.error(f"Invalid bar chart data: {e}")
                    else:
                        st.bar_chart(data)
                elif component.type == ComponentType.LINE_CHART:
                    # Parse JSON string if needed
                    data = component.data
                    if isinstance(data, str):
                        try:
                            import json
                            import pandas as pd

                            parsed = json.loads(data)
                            if isinstance(parsed, dict) and "data" in parsed:
                                df = pd.DataFrame(
                                    parsed["data"],
                                    columns=parsed.get("columns", None),
                                )
                            else:
                                df = pd.DataFrame(parsed)
                            st.line_chart(df)
                        except Exception as e:
                            logger.error(
                                f"Failed to parse line chart data: {e}"
                            )
                            st.error(f"Invalid line chart data: {e}")
                    else:
                        st.line_chart(data)
                elif component.type == ComponentType.METRIC:
                    st.metric(
                        label=component.props.get("label", ""),
                        value=component.data,
                    )
                else:
                    st.warning(f"Unknown component type: {component.type}")
            except Exception as e:
                logger.error(
                    f"Error rendering component {component.id}: {e}",
                    exc_info=True,
                )
                st.error(f"Failed to render component: {e}")
                st.json(
                    {
                        "type": component.type.value,
                        "data": str(component.data)[:200],
                    }
                )


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

        # Register UI tools if not already registered
        # We check if the tool is already in the agent to avoid duplicates on re-runs if agent persists
        # But agent is in session state, so it persists.
        # We should only add them once.

        # Simple check: look for tool name
        tool_names = [t.name for t in self.agent.tools]
        if "create_page" not in tool_names:
            ui_service = UIToolService(self.ui_repository)
            for tool in ui_service.get_tools():
                self.agent.add_tool_definition(tool)
                # We need to bind the methods to the service instance
                if tool.name == "create_page":
                    self.agent.add_tool_function(
                        tool.name, ui_service.create_page
                    )
                elif tool.name == "add_component":
                    self.agent.add_tool_function(
                        tool.name, ui_service.add_component
                    )

    def run(self):
        # Initialization (sync check, async execution inside)
        if not st.session_state.mcp_connected:
            self.initialize()

        self.sidebar.render()
        self.renderer.render_history(st.session_state.messages)

        if prompt := st.chat_input("What is up?"):
            st.session_state.messages.append(
                {"role": "user", "content": prompt}
            )
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                # Capture initial page count to detect changes
                initial_page_count = len(self.ui_repository.get_all_pages())

                try:
                    # Run the agent logic synchronously (callbacks in main thread)
                    # Pass the loop_context.run_coroutine as the executor for async MCP calls
                    response = self.agent.process_message(
                        prompt,
                        user_choice_callback=self.renderer.user_choice_callback,
                        on_tool_call=self.renderer.on_tool_call,
                        on_tool_result=self.renderer.on_tool_result,
                        tool_executor=self.loop_context.run_coroutine,
                    )
                    message_placeholder.markdown(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )

                    # Check if pages changed and rerun if necessary
                    final_page_count = len(self.ui_repository.get_all_pages())
                    if final_page_count != initial_page_count:
                        logger.info(
                            "Page count changed, rerunning to update navigation."
                        )
                        st.rerun()

                except Exception as e:
                    logger.error(
                        f"Error processing message: {e}", exc_info=True
                    )
                    st.error(f"An error occurred: {e}")
