"""
MCP (Model Context Protocol) Client - basic implementation
"""
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseTool
from ..core.exceptions import ToolExecutionError


class MCPTool(BaseTool):
    """A tool that wraps an MCP server endpoint"""

    def __init__(
        self,
        tool_name: str,
        tool_description: str,
        server_url: str,
        endpoint: str
    ):
        self._name = tool_name
        self._description = tool_description
        self.server_url = server_url
        self.endpoint = endpoint

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def execute(self, input_data: Any, **kwargs) -> str:
        """Execute the MCP tool via HTTP"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}{self.endpoint}",
                    json={"input": input_data, **kwargs},
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return str(result.get("output", result))
        except httpx.HTTPError as e:
            raise ToolExecutionError(self.name, f"HTTP error: {str(e)}")
        except Exception as e:
            raise ToolExecutionError(self.name, f"Error: {str(e)}")


class MCPClient:
    """Client for connecting to MCP servers and discovering tools"""

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self.tools: Dict[str, MCPTool] = {}

    async def discover_tools(self) -> List[MCPTool]:
        """Discover available tools from the MCP server"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.server_url}/tools",
                    timeout=10.0
                )
                response.raise_for_status()
                tools_data = response.json()

                tools = []
                for tool_info in tools_data.get("tools", []):
                    tool = MCPTool(
                        tool_name=tool_info["name"],
                        tool_description=tool_info.get("description", ""),
                        server_url=self.server_url,
                        endpoint=tool_info.get("endpoint", f"/tools/{tool_info['name']}")
                    )
                    self.tools[tool.name] = tool
                    tools.append(tool)

                return tools

        except httpx.HTTPError as e:
            raise ToolExecutionError("mcp", f"Failed to discover tools: {str(e)}")
        except Exception as e:
            raise ToolExecutionError("mcp", f"Error: {str(e)}")

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a discovered tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all discovered tool names"""
        return list(self.tools.keys())
