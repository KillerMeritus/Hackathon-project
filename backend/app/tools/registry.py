"""
Tool Registry - manages available tools including MCP tools
"""
from typing import Dict, List, Optional, TYPE_CHECKING

from .base import BaseTool
from ..core.exceptions import ToolExecutionError

if TYPE_CHECKING:
    from ..core.models import MCPServerConfig


# Global tool registry
TOOL_REGISTRY: Dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    """Register a tool in the registry"""
    TOOL_REGISTRY[tool.name] = tool


def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool by name"""
    return TOOL_REGISTRY.get(name)


def get_tools(names: List[str]) -> List[BaseTool]:
    """
    Get multiple tools by name.
    
    Supports:
    - Built-in tools: 'python'
    - MCP tools: 'mcp:server-id' or 'mcp:server-id:tool-name'
    """
    tools = []
    for name in names:
        if name.startswith('mcp:'):
            # Resolve MCP tool reference
            from .mcp_loader import resolve_mcp_tool_reference
            mcp_tools = resolve_mcp_tool_reference(name)
            tools.extend(mcp_tools)
        else:
            # Built-in tool
            tool = get_tool(name)
            if tool:
                tools.append(tool)
    return tools


def list_tools() -> List[str]:
    """List all available tool names (built-in only)"""
    return list(TOOL_REGISTRY.keys())


def list_all_tools() -> Dict[str, List[str]]:
    """
    List all available tools including MCP tools.
    
    Returns:
        Dictionary with 'builtin' and 'mcp' keys
    """
    from .mcp_loader import get_mcp_loader
    
    result = {
        'builtin': list(TOOL_REGISTRY.keys()),
        'mcp': []
    }
    
    loader = get_mcp_loader()
    if loader:
        result['mcp'] = loader.list_loaded_tools()
    
    return result


def _initialize_builtin_tools():
    """Initialize built-in tools"""
    from .python_tool import PythonTool

    # Register built-in tools
    register_tool(PythonTool())


# Initialize on import
_initialize_builtin_tools()