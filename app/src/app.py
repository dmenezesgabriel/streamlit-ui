import streamlit as st
import logging
from typing import List
from src.repositories import StreamlitUIRepository
from src.ui import ChatInterface, DynamicPageRenderer

logger = logging.getLogger("app")


class StreamlitApp:
    """
    Main application class that orchestrates the Streamlit UI.
    Follows dependency injection for better testability and modularity.
    """

    def __init__(
        self,
        repository: StreamlitUIRepository,
        chat_interface: ChatInterface,
    ):
        self.repository = repository
        self.chat_interface = chat_interface

    def run(self):
        """Run the main application loop."""
        logger.info("Starting StreamlitApp run loop")

        # Define the chat page
        chat_page = st.Page(
            self.chat_interface.run,
            title="Chat",
            icon="💬",
            url_path="chat",
        )

        pages = [chat_page]

        # Load dynamic pages from repository
        for ui_page in self.repository.get_all_pages():
            # Capture loop variable
            def render_dynamic_page(p=ui_page):
                DynamicPageRenderer.render_page(p)

            # Create a simple URL-safe slug
            url_slug = ui_page.id.replace("-", "_")

            pages.append(
                st.Page(
                    render_dynamic_page,
                    title=ui_page.title,
                    icon=ui_page.icon or "📄",
                    url_path=url_slug,
                )
            )

        # Setup navigation
        pg = st.navigation(pages)
        pg.run()
