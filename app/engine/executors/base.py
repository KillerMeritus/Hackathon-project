"""
Base Executor class - abstract interface for workflow executors
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Awaitable

from ..memory import SharedMemory
from ..context import ContextBuilder
from ...core.models import WorkflowConfig, AgentConfig


class BaseExecutor(ABC):
    """Abstract base class for workflow executors"""

    def __init__(
        self,
        memory: SharedMemory,
        context_builder: ContextBuilder,
        agents: Dict[str, Any],  # Dict[str, Agent]
        agent_configs: Dict[str, AgentConfig]
    ):
        self.memory = memory
        self.context_builder = context_builder
        self.agents = agents
        self.agent_configs = agent_configs

    @abstractmethod
    async def execute(
        self,
        workflow: WorkflowConfig,
        query: str,
        run_agent: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ) -> str:
        """
        Execute the workflow

        Args:
            workflow: Workflow configuration
            query: User's query
            run_agent: Callback to orchestrator's run_agent method
                      (ensures all agent calls go through orchestrator)

        Returns:
            Final output from the workflow
        """
        pass

    def _get_agent_config(self, agent_id: str) -> AgentConfig:
        """Get agent configuration by ID"""
        return self.agent_configs.get(agent_id)
