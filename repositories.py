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
            if comp.id == component_id:
                return comp
            # If it's a layout, search its children
            if isinstance(comp, LayoutComponent):
                found = self._find_component_by_id(comp.children, component_id)
                if found:
                    return found
        return None

    def add_component(
        self, page_id: str, component: Union[UIComponent, LayoutComponent]
    ) -> None:
        page = self.get_page(page_id)
        if not page:
            raise ValueError(f"Page with ID '{page_id}' not found.")

        # If component has a parent_id, find the parent and add to its children
        if hasattr(component, "parent_id") and component.parent_id:
            parent = self._find_component_by_id(
                page.components, component.parent_id
            )
            if not parent:
                raise ValueError(
                    f"Parent component with ID '{component.parent_id}' not found."
                )
            if not isinstance(parent, LayoutComponent):
                raise ValueError(
                    f"Parent component '{component.parent_id}' is not a layout component."
                )

            parent.children.append(component)
        else:
            # No parent, add to top level
            page.components.append(component)

        # Re-assign to trigger session state update
        st.session_state.ui_pages[page_id] = page
