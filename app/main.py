import streamlit as st
from src.ui import ChatInterface, DynamicPageRenderer
from src.config import get_default_mcp_servers
from src.repositories import SessionStateUIRepository
from src.logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Agent", page_icon="🤖")


def main():
    logger.info("Starting main application")
    # Initialize repository to get pages
    # Note: ChatInterface also initializes it, but we need it here for navigation
    # We can rely on SessionStateUIRepository being idempotent in its init (checking session state)
    repo = SessionStateUIRepository()

    # Define the main chat page
    chat_page = st.Page(
        lambda: ChatInterface(get_default_mcp_servers()).run(),
        title="Chat",
        icon="💬",
        url_path="chat",  # explicit url path
    )

    pages = [chat_page]

    # Add dynamic pages
    for ui_page in repo.get_all_pages():
        # We need to capture the page object in the lambda default argument
        # otherwise all pages will render the last page in the loop
        def render_dynamic_page(p=ui_page):
            DynamicPageRenderer.render_page(p)

        # Create a simple URL-safe slug from the page ID (no slashes allowed)
        url_slug = ui_page.id.replace("-", "_")

        pages.append(
            st.Page(
                render_dynamic_page,
                title=ui_page.title,
                icon=ui_page.icon or "📄",
                url_path=url_slug,
            )
        )

    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    main()
