"""
Sequential Executor - executes agents one after another
"""
from typing import Dict, Any, Callable, Awaitable, List

from .base import BaseExecutor
from ..memory import SharedMemory
from ..context import ContextBuilder
from ...core.models import WorkflowConfig, AgentConfig
from ...core.exceptions import WorkflowExecutionError


class SequentialExecutor(BaseExecutor):
    """
    Executes workflow steps sequentially.

    Each agent receives context from all previous agents.
    Flow: Agent1 → Orchestrator → Agent2 → Orchestrator → Agent3 → ...
    """

    async def execute(
        self,
        workflow: WorkflowConfig,
        query: str,
        run_agent: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ) -> str:
        """
        Execute sequential workflow

        Args:
            workflow: Workflow configuration with steps
            query: User's query
            run_agent: Orchestrator's run_agent callback

        Returns:
            Output from the final agent
        """
        if not workflow.steps:
            raise WorkflowExecutionError("Sequential workflow requires steps")

        executed_agents: List[str] = []
        final_output = ""

        self.memory.add_log({
            "event": "sequential_start",
            "total_steps": len(workflow.steps)
        })

        for step_index, step in enumerate(workflow.steps):
            agent_id = step.agent
            agent_config = self._get_agent_config(agent_id)

            if not agent_config:
                raise WorkflowExecutionError(
                    f"Agent not found: {agent_id}",
                    agent_id=agent_id,
                    step=step_index
                )

            self.memory.add_log({
                "event": "step_start",
                "step": step_index + 1,
                "agent_id": agent_id,
                "agent_role": agent_config.role
            })

            # Build context with all previous outputs
            context = self.context_builder.build_sequential_context(
                query=query,
                current_agent=agent_config,
                executed_agents=executed_agents
            )

            # Run agent through orchestrator (NOT directly!)
            try:
                output = await run_agent(agent_id, context)
                final_output = output
                executed_agents.append(agent_id)

                self.memory.add_log({
                    "event": "step_complete",
                    "step": step_index + 1,
                    "agent_id": agent_id,
                    "output_length": len(output)
                })

            except Exception as e:
                self.memory.add_log({
                    "event": "step_failed",
                    "step": step_index + 1,
                    "agent_id": agent_id,
                    "error": str(e)
                })
                raise WorkflowExecutionError(
                    str(e),
                    agent_id=agent_id,
                    step=step_index
                )

        self.memory.add_log({
            "event": "sequential_complete",
            "agents_executed": executed_agents
        })

        return final_output
