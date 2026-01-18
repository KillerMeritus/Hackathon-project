"""
MCP Tool Loader - Loads and registers MCP tools from configured servers

"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import asyncio
import logging

from .mcp_client import MCPClient, MCPTool
from .base import BaseTool
from ..core.exceptions import ToolExecutionError

if TYPE_CHECKING:
    from ..core.models import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPToolLoader:

    
    def __init__(self, mcp_configs: List["MCPServerConfig"]):

        self.configs = {config.id: config for config in mcp_configs}
        self.clients: Dict[str, MCPClient] = {}
        self.tools: Dict[str, MCPTool] = {}  # Keyed by "server_id:tool_name"
        self._loaded = False
    
    async def load_all_tools(self) -> Dict[str, MCPTool]:

        if self._loaded:
            return self.tools
        
        for server_id, config in self.configs.items():
            try:
                client = MCPClient(config.url)
                self.clients[server_id] = client
                
                if config.auto_discover:
                    # Discover all tools from server
                    discovered = await client.discover_tools()
                    for tool in discovered:
                        tool_key = f"{server_id}:{tool.name}"
                        self.tools[tool_key] = tool
                        logger.info(f"Loaded MCP tool: {tool_key}")
                else:
                    # Load only specific tools
                    discovered = await client.discover_tools()
                    for tool in discovered:
                        if tool.name in config.tools:
                            tool_key = f"{server_id}:{tool.name}"
                            self.tools[tool_key] = tool
                            logger.info(f"Loaded MCP tool: {tool_key}")
                            
            except Exception as e:
                logger.warning(f"Failed to load tools from MCP server '{server_id}': {e}")
                # Don't fail completely - just skip this server
        
        self._loaded = True
        return self.tools
    
    def get_tool(self, server_id: str, tool_name: str) -> Optional[MCPTool]:

        tool_key = f"{server_id}:{tool_name}"
        return self.tools.get(tool_key)
    
    def get_all_tools_for_server(self, server_id: str) -> List[MCPTool]:

        prefix = f"{server_id}:"
        return [
            tool for key, tool in self.tools.items()
            if key.startswith(prefix)
        ]
    
    def resolve_tool_reference(self, ref: str) -> List[BaseTool]:

        if not ref.startswith('mcp:'):
            return []
        
        parts = ref.split(':')
        
        if len(parts) == 2:
            # Format: mcp:server-id -> all tools from server
            server_id = parts[1]
            return self.get_all_tools_for_server(server_id)
        
        elif len(parts) == 3:
            # Format: mcp:server-id:tool-name -> specific tool
            server_id = parts[1]
            tool_name = parts[2]
            tool = self.get_tool(server_id, tool_name)
            return [tool] if tool else []
        
        return []
    
    def list_loaded_tools(self) -> List[str]:
        """List all loaded tool keys."""
        return list(self.tools.keys())
    
    def __repr__(self) -> str:
        return f"MCPToolLoader(servers={list(self.configs.keys())}, tools={len(self.tools)})"


# Global MCP tool loader instance (set during orchestrator initialization)
_mcp_loader: Optional[MCPToolLoader] = None


def get_mcp_loader() -> Optional[MCPToolLoader]:

    return _mcp_loader


def set_mcp_loader(loader: MCPToolLoader) -> None:
 
    global _mcp_loader
    _mcp_loader = loader


def resolve_mcp_tool_reference(ref: str) -> List[BaseTool]:

    loader = get_mcp_loader()
    if loader:
        return loader.resolve_tool_reference(ref)
    return []
