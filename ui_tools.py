import uuid
from typing import Any, Dict, Optional
from agent import Tool
from models import ComponentType, UIComponent
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

    def add_component(
        self,
        page_id: str,
        type: str,
        data: Any,
        props: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Adds a component to a specific page."""
        logger.info(f"Adding component: type={type}, page_id={page_id}")
        try:
            component_type = ComponentType(type.lower())
        except ValueError:
            logger.error(f"Invalid component type: {type}")
            return f"Invalid component type: {type}. Valid types are: {[t.value for t in ComponentType]}"

        component_id = str(uuid.uuid4())
        component = UIComponent(
            id=component_id, type=component_type, data=data, props=props or {}
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
                name="add_component",
                description='Add a UI component to a page. For dataframe/chart components, pass data as JSON string with format: {"columns": ["col1", "col2"], "data": [[val1, val2], [val3, val4]]}',
                parameters={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to add to",
                        },
                        "type": {
                            "type": "string",
                            "description": f"Type of component: {[t.value for t in ComponentType]}",
                        },
                        "data": {
                            "type": "string",
                            "description": 'Content/Data for the component. For dataframe/charts, use JSON format: {"columns": [...], "data": [[...], [...]]}',
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
