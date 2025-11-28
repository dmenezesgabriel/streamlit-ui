from typing import List, Optional, Protocol
import streamlit as st
from models import UIPage, UIComponent


class StreamlitUIRepository(Protocol):
    def get_all_pages(self) -> List[UIPage]: ...

    def get_page(self, page_id: str) -> Optional[UIPage]: ...

    def create_page(
        self, page_id: str, title: str, icon: Optional[str] = None
    ) -> UIPage: ...

    def add_component(self, page_id: str, component: UIComponent) -> None: ...


class SessionStateUIRepository:
    def __init__(self):
        if "ui_pages" not in st.session_state:
            st.session_state.ui_pages = {}  # Dict[str, UIPage]

    def get_all_pages(self) -> List[UIPage]:
        return list(st.session_state.ui_pages.values())

    def get_page(self, page_id: str) -> Optional[UIPage]:
        return st.session_state.ui_pages.get(page_id)

    def create_page(
        self, page_id: str, title: str, icon: Optional[str] = None
    ) -> UIPage:
        if page_id in st.session_state.ui_pages:
            raise ValueError(f"Page with ID '{page_id}' already exists.")

        page = UIPage(id=page_id, title=title, icon=icon)
        st.session_state.ui_pages[page_id] = page
        return page

    def add_component(self, page_id: str, component: UIComponent) -> None:
        page = self.get_page(page_id)
        if not page:
            raise ValueError(f"Page with ID '{page_id}' not found.")

        page.components.append(component)
        # Re-assign to trigger session state update if needed (though mutable objects usually update in place)
        st.session_state.ui_pages[page_id] = page
