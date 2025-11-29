from typing import List, Optional, Protocol, Union
import streamlit as st
from models import UIPage, UIComponent, LayoutComponent, AnyComponent


class StreamlitUIRepository(Protocol):
    def get_all_pages(self) -> List[UIPage]: ...

    def get_page(self, page_id: str) -> Optional[UIPage]: ...

    def create_page(
        self, page_id: str, title: str, icon: Optional[str] = None
    ) -> UIPage: ...

    def add_component(
        self, page_id: str, component: Union[UIComponent, LayoutComponent]
    ) -> None: ...


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

    def _find_component_by_id(
        self, components: List[AnyComponent], component_id: str
    ) -> Optional[Union[UIComponent, LayoutComponent]]:
        """Recursively find a component by ID in the component tree."""
        for comp in components:
            # Early return: Found the component
            if comp.id == component_id:
                return comp

            # Guard: Skip if not a layout component
            if not isinstance(comp, LayoutComponent):
                continue

            # Recursively search children
            found = self._find_component_by_id(comp.children, component_id)
            if found:
                return found

        return None

    def add_component(
        self, page_id: str, component: Union[UIComponent, LayoutComponent]
    ) -> None:
        page = self.get_page(page_id)

        # Guard: Page not found
        if not page:
            raise ValueError(f"Page with ID '{page_id}' not found.")

        # Guard: No parent - add to top level
        if not hasattr(component, "parent_id") or not component.parent_id:
            page.components.append(component)
            st.session_state.ui_pages[page_id] = page
            return

        # Component has a parent - find and validate it
        parent = self._find_component_by_id(
            page.components, component.parent_id
        )

        # Guard: Parent not found
        if not parent:
            raise ValueError(
                f"Parent component with ID '{component.parent_id}' not found."
            )

        # Guard: Parent is not a layout component
        if not isinstance(parent, LayoutComponent):
            raise ValueError(
                f"Parent component '{component.parent_id}' is not a layout component."
            )

        # Add to parent's children
        parent.children.append(component)
        st.session_state.ui_pages[page_id] = page
