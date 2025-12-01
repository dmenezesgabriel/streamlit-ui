import streamlit as st
import logging
from src.ui import ChatInterface
from src.config import get_default_mcp_servers
from src.repositories import SessionStateUIRepository
from src.logging_config import setup_logging
from src.app import StreamlitApp
from src.agent import ChatAgent
from src.tools import greeting, greeting_tool

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Agent", page_icon="🤖")


def create_agent() -> ChatAgent:
    """Factory function to create the ChatAgent with default tools."""
    agent = ChatAgent(use_tool_manager=True)
    agent.add_tool_definition(
        greeting_tool,
        keywords=["hello", "hi", "greet", "greeting"],
        category="general",
        always_load=True,  # Always available for simple interactions
    )
    agent.add_tool_function("greeting", greeting)
    return agent


def main():
    logger.info("Starting main application")

    # 1. Initialize Repository
    repo = SessionStateUIRepository()

    # 2. Initialize Chat Interface (injecting agent factory)
    chat_interface = ChatInterface(
        mcp_configs=get_default_mcp_servers(), agent_factory=create_agent
    )

    # 3. Initialize App (injecting dependencies)
    app = StreamlitApp(repository=repo, chat_interface=chat_interface)

    # 4. Run App
    app.run()


if __name__ == "__main__":
    main()
