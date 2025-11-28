import uuid
from typing import Any, Dict, Optional, List, Union
from agent import Tool
from models import (
    ComponentType,
    UIComponent,
    LayoutType,
    LayoutComponent,
    AnyComponent,
)
from repositories import StreamlitUIRepository
import logging

logger = logging.getLogger("ui_tools")


class UIToolService:
    def __init__(self, repository: StreamlitUIRepository):
        self.repository = repository

    def create_page(self, title: str, icon: Optional[str] = None) -> str:
        """Creates a new page in the UI."""
        page_id = str(uuid.uuid4())
        logger.info(f"Creating page: title='{title}', id={page_id}")
        try:
            self.repository.create_page(page_id, title, icon)
            logger.info(f"✅ Page created successfully: {page_id}")
            return f"Page created successfully. ID: {page_id}, Title: {title}"
        except Exception as e:
            logger.error(f"❌ Failed to create page: {e}", exc_info=True)
            return f"Failed to create page: {e}"

    def create_layout(
        self,
        page_id: str,
        layout_type: str,
        parent_id: Optional[str] = None,
        props: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Creates a layout component (columns or container)."""
        logger.info(
            f"Creating layout: type={layout_type}, page_id={page_id}, parent_id={parent_id}"
        )
        try:
            layout_type_enum = LayoutType(layout_type.lower())
        except ValueError:
            logger.error(f"Invalid layout type: {layout_type}")
            return f"Invalid layout type: {layout_type}. Valid types are: {[t.value for t in LayoutType]}"

        layout_id = str(uuid.uuid4())
        layout = LayoutComponent(
            id=layout_id,
            type=layout_type_enum,
            children=[],
            props=props or {},
            parent_id=parent_id,
        )

        try:
            self.repository.add_component(page_id, layout)
            logger.info(f"✅ Layout created successfully: {layout_id}")
            return f"Layout created successfully. ID: {layout_id}, Type: {layout_type}"
        except Exception as e:
            logger.error(f"❌ Failed to create layout: {e}", exc_info=True)
            return f"Failed to create layout: {e}"

    def add_component(
        self,
        page_id: str,
        type: str,
        data: Any,
        parent_id: Optional[str] = None,
        props: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Adds a component to a specific page or layout."""
        logger.info(
            f"Adding component: type={type}, page_id={page_id}, parent_id={parent_id}"
        )
        try:
            component_type = ComponentType(type.lower())
        except ValueError:
            logger.error(f"Invalid component type: {type}")
            return f"Invalid component type: {type}. Valid types are: {[t.value for t in ComponentType]}"

        component_id = str(uuid.uuid4())
        component = UIComponent(
            id=component_id,
            type=component_type,
            data=data,
            props=props or {},
            parent_id=parent_id,
        )

        try:
            self.repository.add_component(page_id, component)
            logger.info(
                f"✅ Component added successfully: {component_id} to page {page_id}"
            )
            return f"Component added successfully to page {page_id}. Component ID: {component_id}"
        except Exception as e:
            logger.error(f"❌ Failed to add component: {e}", exc_info=True)
            return f"Failed to add component: {e}"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="create_page",
                description="Create a new page in the application sidebar.",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the page",
                        },
                        "icon": {
                            "type": "string",
                            "description": "Icon for the page (emoji)",
                        },
                    },
                    "required": ["title"],
                    "additionalProperties": False,
                },
                strict=True,
            ),
            Tool(
                name="create_layout",
                description="Create a layout component (columns or container) on a page. For columns, specify column widths in props as 'spec' (e.g., [1,2,1] for 3 columns). Returns layout ID for adding nested components.",
                parameters={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page",
                        },
                        "layout_type": {
                            "type": "string",
                            "description": f"Type of layout: {[t.value for t in LayoutType]}",
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Optional parent layout ID for nesting",
                        },
                        "props": {
                            "type": "object",
                            "description": "Layout properties. For columns: spec (list of widths), gap ('small'/'medium'/'large'), vertical_alignment, border. For container: border, height, width, horizontal, gap",
                        },
                    },
                    "required": ["page_id", "layout_type"],
                    "additionalProperties": False,
                },
                strict=True,
            ),
            Tool(
                name="add_component",
                description='Add a UI component to a page or layout. For dataframe/chart components, pass data as JSON string with format: {"columns": ["col1", "col2"], "data": [[val1, val2], [val3, val4]]}',
                parameters={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page",
                        },
                        "type": {
                            "type": "string",
                            "description": f"Type of component: {[t.value for t in ComponentType]}",
                        },
                        "data": {
                            "type": "string",
                            "description": 'Content/Data for the component. For dataframe/charts, use JSON format: {"columns": [...], "data": [[...], [...]]}',
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Optional parent layout ID to add component inside a layout",
                        },
                        "props": {
                            "type": "object",
                            "description": "Additional properties (key-value pairs)",
                        },
                    },
                    "required": ["page_id", "type", "data"],
                    "additionalProperties": False,
                },
                strict=True,
            ),
        ]
