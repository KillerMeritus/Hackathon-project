"""
Base Tool class - abstract interface for all tools
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    """Abstract base class for all tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does"""
        pass

    @abstractmethod
    async def execute(self, input_data: Any, **kwargs) -> str:
        """
        Execute the tool with the given input

        Args:
            input_data: The input to the tool (type depends on tool)
            **kwargs: Additional arguments

        Returns:
            String result from the tool execution
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input (for LLM function calling)"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input for the tool"
                    }
                },
                "required": ["input"]
            }
        }

    def __repr__(self) -> str:
        return f"Tool({self.name})"