"""
Orchestrator - The main brain that controls the entire workflow execution

CRITICAL DESIGN PRINCIPLE:
All agent communications go through the Orchestrator.
Agents NEVER talk directly to each other.
"""
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from .memory import SharedMemory
from .context import ContextBuilder
from .memory_extractor import MemoryExtractor
from .executors.sequential import SequentialExecutor
from .executors.parallel import ParallelExecutor
from ..core.models import YAMLConfig, ExecutionResult, AgentConfig
from ..core.exceptions import WorkflowExecutionError, AgentNotFoundError
from ..agents.factory import create_agents_from_config


class Orchestrator:
    """
    Main orchestration engine.

    Responsibilities:
    1. Create agents from config
    2. Manage shared memory
    3. Control ALL agent execution
    4. Handle sequential and parallel workflows
    5. Extract structured memory safely
    6. Persist execution state
    """

    def __init__(self, config: YAMLConfig, workflow_id: Optional[str] = None):
        self.config = config
        self.workflow_id = workflow_id or str(uuid.uuid4())[:8]

        # Centralized memory
        self.memory = SharedMemory(self.workflow_id)

        # Context builder
        self.context_builder = ContextBuilder(self.memory)

        # Structured memory extractor (facts / insights / decisions)
        self.memory_extractor = MemoryExtractor()

        # MCP tool loading state
        self._mcp_loaded = False
        self._mcp_loader = None

        # Create agents
        self.agents = create_agents_from_config(config)

        # Agent config lookup
        self.agent_configs: Dict[str, AgentConfig] = {
            agent.id: agent for agent in config.agents
        }

        # Log initialization
        self.memory.add_log({
            "event": "orchestrator_initialized",
            "workflow_id": self.workflow_id,
            "agents": list(self.agents.keys()),
            "workflow_type": config.workflow.type,
            "mcp_servers": [s.id for s in config.mcp_servers]
        })

    async def execute(self, query: str) -> ExecutionResult:
        start_time = time.time()

        self.memory.add_log({
            "event": "execution_start",
            "query": query,
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Load MCP tools once
            await self._load_mcp_tools()

            executor = self._get_executor()

            # Execute workflow
            final_output = await executor.execute(
                workflow=self.config.workflow,
                query=query,
                run_agent=self.run_agent
            )

            execution_time = time.time() - start_time

            self.memory.add_log({
                "event": "execution_complete",
                "success": True,
                "execution_time": execution_time
            })

            self.memory.save_to_file()

            return ExecutionResult(
                workflow_id=self.workflow_id,
                success=True,
                final_output=final_output,
                agent_outputs=self.memory.get_all_outputs(),
                execution_log=self.memory.get_log(),
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time

            self.memory.add_log({
                "event": "execution_failed",
                "error": str(e),
                "execution_time": execution_time
            })

            self.memory.save_to_file()

            return ExecutionResult(
                workflow_id=self.workflow_id,
                success=False,
                final_output="",
                agent_outputs=self.memory.get_all_outputs(),
                execution_log=self.memory.get_log(),
                error=str(e),
                execution_time=execution_time
            )

    async def run_agent(self, agent_id: str, context: Dict[str, Any]) -> str:
        """
        CRITICAL METHOD.
        Every agent execution flows through here.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)

        self.memory.add_log({
            "event": "agent_start",
            "agent_id": agent_id,
            "agent_role": agent.role,
            "context_keys": list(context.keys())
        })

        try:
            # Run agent
            output = await agent.execute(context)

            # Store raw output (always)
            self.memory.store_output(agent_id, output)

            # Extract structured memory (must NEVER break execution)
            facts = []
            try:
                facts = await self.memory_extractor.extract_facts(
                    output=output,
                    agent_id=agent_id,
                    agent_role=agent.role
                )
                if facts:
                    self.memory.store_facts(
                        agent_id=agent_id,
                        agent_role=agent.role,
                        facts=[f.to_dict() for f in facts]
                    )
            except Exception as e:
                self.memory.add_log({
                    "event": "memory_extraction_failed",
                    "agent_id": agent_id,
                    "error": str(e)
                })

            self.memory.add_log({
                "event": "agent_complete",
                "agent_id": agent_id,
                "output_length": len(output),
                "facts_extracted": len(facts)
            })

            return output

        except Exception as e:
            self.memory.add_log({
                "event": "agent_error",
                "agent_id": agent_id,
                "error": str(e)
            })
            raise WorkflowExecutionError(str(e), agent_id=agent_id)

    def _get_executor(self):
        workflow_type = self.config.workflow.type.lower()

        if workflow_type == "sequential":
            return SequentialExecutor(
                memory=self.memory,
                context_builder=self.context_builder,
                agents=self.agents,
                agent_configs=self.agent_configs
            )

        if workflow_type == "parallel":
            return ParallelExecutor(
                memory=self.memory,
                context_builder=self.context_builder,
                agents=self.agents,
                agent_configs=self.agent_configs
            )

        raise WorkflowExecutionError(f"Unknown workflow type: {workflow_type}")

    async def _load_mcp_tools(self) -> None:
        if self._mcp_loaded:
            return

        if not self.config.mcp_servers:
            self._mcp_loaded = True
            return

        try:
            from ..tools.mcp_loader import MCPToolLoader, set_mcp_loader

            self._mcp_loader = MCPToolLoader(self.config.mcp_servers)
            loaded_tools = await self._mcp_loader.load_all_tools()

            set_mcp_loader(self._mcp_loader)

            self.memory.add_log({
                "event": "mcp_tools_loaded",
                "servers": [s.id for s in self.config.mcp_servers],
                "tools_count": len(loaded_tools),
                "tools": list(loaded_tools.keys())
            })

        except Exception as e:
            self.memory.add_log({
                "event": "mcp_tools_load_failed",
                "error": str(e)
            })

        self._mcp_loaded = True

    def get_mcp_tools(self) -> List[str]:
        if self._mcp_loader:
            return self._mcp_loader.list_loaded_tools()
        return []

    def get_memory_state(self) -> Dict[str, Any]:
        return self.memory.to_dict()

    def get_agent_output(self, agent_id: str) -> Optional[str]:
        return self.memory.get_output(agent_id)

    def get_execution_log(self):
        return self.memory.get_log()

    def load_previous_memory(self) -> bool:
        return self.memory.load_from_file()

    def __repr__(self) -> str:
        return f"Orchestrator(workflow_id={self.workflow_id}, agents={list(self.agents.keys())})"