from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    HEADER = "header"
    SUBHEADER = "subheader"
    CODE = "code"
    DATAFRAME = "dataframe"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    METRIC = "metric"


class LayoutType(str, Enum):
    COLUMNS = "columns"
    CONTAINER = "container"


class UIComponent(BaseModel):
    id: str
    type: ComponentType
    data: Any
    props: Dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None  # For nesting inside layouts


class LayoutComponent(BaseModel):
    id: str
    type: LayoutType
    children: List[Union["UIComponent", "LayoutComponent"]] = Field(
        default_factory=list
    )
    props: Dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None  # For nesting layouts inside other layouts


# Union type for any component (content or layout)
AnyComponent = Union[UIComponent, LayoutComponent]


class UIPage(BaseModel):
    id: str
    title: str
    icon: Optional[str] = None
    components: List[AnyComponent] = Field(default_factory=list)


# Enable forward references for recursive types
LayoutComponent.model_rebuild()
