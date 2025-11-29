from typing import List, Optional, Protocol, Union
import streamlit as st
from src.models import UIPage, UIComponent, LayoutComponent, AnyComponent


class StreamlitUIRepository(Protocol):
    def get_all_pages(self) -> List[UIPage]: ...

    def get_page(self, page_id: str) -> Optional[UIPage]: ...

    def create_page(
        self, page_id: str, title: str, icon: Optional[str] = None
    ) -> UIPage: ...

    def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> UIPage: ...

    def add_component(
        self, page_id: str, component: Union[UIComponent, LayoutComponent]
    ) -> None: ...

    def update_component(
        self,
        page_id: str,
        component_id: str,
        data: Optional[str] = None,
        props: Optional[dict] = None,
    ) -> None: ...

    def update_layout(
        self, page_id: str, layout_id: str, props: Optional[dict] = None
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

            if not isinstance(comp, LayoutComponent):
                continue

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

        if not hasattr(component, "parent_id") or not component.parent_id:
            page.components.append(component)
            st.session_state.ui_pages[page_id] = page
            return

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
        st.session_state.ui_pages[page_id] = page

    def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> UIPage:
        """Update a page's attributes."""
        page = self.get_page(page_id)

        if not page:
            raise ValueError(f"Page with ID '{page_id}' not found.")

        if title is not None:
            page.title = title
        if icon is not None:
            page.icon = icon

        st.session_state.ui_pages[page_id] = page
        return page

    def update_component(
        self,
        page_id: str,
        component_id: str,
        data: Optional[str] = None,
        props: Optional[dict] = None,
    ) -> None:
        """Update a component's data or props."""
        page = self.get_page(page_id)

        if not page:
            raise ValueError(f"Page with ID '{page_id}' not found.")

        component = self._find_component_by_id(page.components, component_id)

        if not component:
            raise ValueError(f"Component with ID '{component_id}' not found.")

        if isinstance(component, LayoutComponent):
            raise ValueError(f"Use update_layout to update layout components.")

        if data is not None:
            component.data = data
        if props is not None:
            component.props.update(props)

        st.session_state.ui_pages[page_id] = page

    def update_layout(
        self, page_id: str, layout_id: str, props: Optional[dict] = None
    ) -> None:
        """Update a layout component's props."""
        page = self.get_page(page_id)

        if not page:
            raise ValueError(f"Page with ID '{page_id}' not found.")

        layout = self._find_component_by_id(page.components, layout_id)

        if not layout:
            raise ValueError(f"Layout with ID '{layout_id}' not found.")

        if not isinstance(layout, LayoutComponent):
            raise ValueError(
                f"Component '{layout_id}' is not a layout component."
            )

        if props is not None:
            layout.props.update(props)

        st.session_state.ui_pages[page_id] = page
