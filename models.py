from enum import Enum
from typing import Any, Dict, List, Optional
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


class UIComponent(BaseModel):
    id: str = Field(..., description="Unique identifier for the component")
    type: ComponentType
    data: Any = Field(
        None,
        description="Data content for the component (text, dataframe, etc.)",
    )
    props: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional properties (e.g., key, help, etc.)",
    )


class UIPage(BaseModel):
    id: str = Field(..., description="Unique identifier for the page")
    title: str
    icon: Optional[str] = None
    components: List[UIComponent] = Field(default_factory=list)
