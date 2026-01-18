"""
Parallel Executor - executes agents concurrently with optional aggregation
"""
import asyncio
from typing import Dict, Any, Callable, Awaitable, List

from .base import BaseExecutor
from ..memory import SharedMemory
from ..context import ContextBuilder
from ...core.models import WorkflowConfig, AgentConfig
from ...core.exceptions import WorkflowExecutionError


class ParallelExecutor(BaseExecutor):
    """
    Executes workflow branches in parallel.

    All branch agents run simultaneously, then optionally an aggregator
    collects and processes all outputs.

    Flow:
        ┌─→ Agent1 ─┐
        │           │
    Query ─┼─→ Agent2 ─┼─→ Aggregator → Output
        │           │
        └─→ Agent3 ─┘
    """

    async def execute(
        self,
        workflow: WorkflowConfig,
        query: str,
        run_agent: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ) -> str:
        """
        Execute parallel workflow

        Args:
            workflow: Workflow configuration with branches and optional 'then'
            query: User's query
            run_agent: Orchestrator's run_agent callback

        Returns:
            Aggregated output or combined branch outputs
        """
        if not workflow.branches:
            raise WorkflowExecutionError("Parallel workflow requires branches")

        self.memory.add_log({
            "event": "parallel_start",
            "branches": workflow.branches,
            "has_aggregator": workflow.then is not None
        })

        # Execute all branches in parallel
        branch_outputs = await self._execute_branches(
            workflow.branches,
            query,
            run_agent
        )

        # If there's an aggregator, run it
        if workflow.then:
            final_output = await self._execute_aggregator(
                workflow.then.agent,
                query,
                workflow.branches,
                run_agent
            )
        else:
            # No aggregator - combine all outputs
            final_output = self._combine_outputs(branch_outputs)

        self.memory.add_log({
            "event": "parallel_complete",
            "branches_executed": list(branch_outputs.keys())
        })

        return final_output

    async def _execute_branches(
        self,
        branch_ids: List[str],
        query: str,
        run_agent: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ) -> Dict[str, str]:
        """Execute all branches in parallel"""

        async def execute_branch(agent_id: str) -> tuple:
            """Execute a single branch and return (agent_id, output)"""
            agent_config = self._get_agent_config(agent_id)

            if not agent_config:
                raise WorkflowExecutionError(
                    f"Agent not found: {agent_id}",
                    agent_id=agent_id
                )

            self.memory.add_log({
                "event": "branch_start",
                "agent_id": agent_id,
                "agent_role": agent_config.role
            })

            # Build context for parallel execution (no previous outputs)
            context = self.context_builder.build_parallel_context(
                query=query,
                current_agent=agent_config
            )

            try:
                output = await run_agent(agent_id, context)

                self.memory.add_log({
                    "event": "branch_complete",
                    "agent_id": agent_id,
                    "output_length": len(output)
                })

                return (agent_id, output)

            except Exception as e:
                self.memory.add_log({
                    "event": "branch_failed",
                    "agent_id": agent_id,
                    "error": str(e)
                })
                raise WorkflowExecutionError(str(e), agent_id=agent_id)

        # Run all branches concurrently
        tasks = [execute_branch(agent_id) for agent_id in branch_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        branch_outputs = {}
        for result in results:
            if isinstance(result, Exception):
                raise result
            agent_id, output = result
            branch_outputs[agent_id] = output

        return branch_outputs

    async def _execute_aggregator(
        self,
        aggregator_id: str,
        query: str,
        branch_ids: List[str],
        run_agent: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ) -> str:
        """Execute the aggregator agent"""
        agent_config = self._get_agent_config(aggregator_id)

        if not agent_config:
            raise WorkflowExecutionError(
                f"Aggregator agent not found: {aggregator_id}",
                agent_id=aggregator_id
            )

        self.memory.add_log({
            "event": "aggregator_start",
            "agent_id": aggregator_id,
            "input_branches": branch_ids
        })

        # Build context with all branch outputs
        context = self.context_builder.build_aggregator_context(
            query=query,
            aggregator_agent=agent_config,
            branch_agent_ids=branch_ids
        )

        try:
            output = await run_agent(aggregator_id, context)

            self.memory.add_log({
                "event": "aggregator_complete",
                "agent_id": aggregator_id,
                "output_length": len(output)
            })

            return output

        except Exception as e:
            self.memory.add_log({
                "event": "aggregator_failed",
                "agent_id": aggregator_id,
                "error": str(e)
            })
            raise WorkflowExecutionError(str(e), agent_id=aggregator_id)

    def _combine_outputs(self, branch_outputs: Dict[str, str]) -> str:
        """Combine branch outputs when no aggregator is specified"""
        lines = ["## Combined Results from Parallel Execution\n"]

        for agent_id, output in branch_outputs.items():
            agent_config = self._get_agent_config(agent_id)
            role = agent_config.role if agent_config else agent_id
            lines.append(f"### {role} ({agent_id})\n")
            lines.append(output)
            lines.append("\n---\n")

        return "\n".join(lines)
