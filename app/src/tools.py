from src.tool_models import Tool

greeting_tool = Tool(
    name="greeting",
    description="greet a user",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the person to greet",
            },
        },
        "required": ["name"],
        "additionalProperties": False,
    },
    strict=True,
)


def greeting(name: str):
    return f"Hello, {name}"
