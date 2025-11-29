from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    enabled: bool = True


def get_default_mcp_servers() -> List[MCPServerConfig]:
    return [
        # MCPServerConfig(
        #     name="playwright",
        #     command="pnpx",
        #     args=["@playwright/mcp@latest"],
        #     enabled=True,
        # ),
        # Example of how to add another server
        # MCPServerConfig(
        #     name="filesystem",
        #     command="npx",
        #     args=["-y", "@modelcontextprotocol/server-filesystem", "/home/user/allowed-dir"],
        #     enabled=False
        # ),
    ]
