"""
Tool model definition.
"""

from typing import Any, Dict
from pydantic import BaseModel


class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: bool
