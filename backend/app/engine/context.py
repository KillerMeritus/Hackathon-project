"""
Context Builder - builds context dictionaries for agents

Supports three modes:
- Traditional: Pass all previous outputs
- Semantic (hybrid): Facts → semantic outputs → full fallback
- Parallel-safe: No shared context between parallel agents
"""
from typing import Dict, Any, List, Optional

from .memory import SharedMemory
from ..core.models import AgentConfig


class ContextBuilder:
    """
    Builds context dictionaries for agents.

    Context defines what an agent can see at execution time.
    Agents never communicate directly; all information flow
    is mediated through this builder.
    """

    def __init__(self, memory: SharedMemory):
        self.memory = memory

    # ------------------------------------------------------------------
    # Initial context
    # ------------------------------------------------------------------

    def build_initial_context(self, query: str) -> Dict[str, Any]:
        """Build initial context with just the user query"""
        return {
            "query": query,
            "previous_outputs": {},
            "current_agent": None
        }

    # ------------------------------------------------------------------
    # Sequential workflow context
    # ------------------------------------------------------------------

    def build_sequential_context(
        self,
        query: str,
        current_agent: AgentConfig,
        executed_agents: List[str],
        use_semantic: bool = False,
        semantic_top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Build context for sequential workflows.

        Each agent receives:
        - The original query
        - Context from previously executed agents
        - Its own identity and goal
        """

        if use_semantic and self.memory.has_vector_memory():
            return self.build_semantic_context(
                query=query,
                current_agent=current_agent,
                top_k=semantic_top_k,
                exclude_agent_ids=[current_agent.id]
            )

        # Traditional deterministic context
        previous_outputs: Dict[str, str] = {}
        for agent_id in executed_agents:
            output = self.memory.get_output(agent_id)
            if output:
                previous_outputs[agent_id] = output

        return {
            "query": query,
            "previous_outputs": previous_outputs,
            "context_mode": "sequential",
            "current_agent": {
                "id": current_agent.id,
                "role": current_agent.role,
                "goal": current_agent.goal
            }
        }

    # ------------------------------------------------------------------
    # Parallel workflow context
    # ------------------------------------------------------------------

    def build_parallel_context(
        self,
        query: str,
        current_agent: AgentConfig
    ) -> Dict[str, Any]:
        """
        Build context for parallel workflow branches.

        Parallel agents run independently and do not
        receive previous outputs.
        """
        return {
            "query": query,
            "previous_outputs": {},
            "context_mode": "parallel",
            "current_agent": {
                "id": current_agent.id,
                "role": current_agent.role,
                "goal": current_agent.goal
            }
        }

    # ------------------------------------------------------------------
    # Aggregator context (parallel join)
    # ------------------------------------------------------------------

    def build_aggregator_context(
        self,
        query: str,
        aggregator_agent: AgentConfig,
        branch_agent_ids: List[str],
        use_semantic: bool = False,
        semantic_top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Build context for aggregator agent in parallel workflows.
        """

        if use_semantic and self.memory.has_vector_memory():
            return self.build_semantic_context(
                query=query,
                current_agent=aggregator_agent,
                top_k=semantic_top_k,
                exclude_agent_ids=[aggregator_agent.id]
            )

        previous_outputs = self.memory.get_outputs_for_agents(branch_agent_ids)

        return {
            "query": query,
            "previous_outputs": previous_outputs,
            "context_mode": "aggregator",
            "current_agent": {
                "id": aggregator_agent.id,
                "role": aggregator_agent.role,
                "goal": aggregator_agent.goal
            }
        }

    # ------------------------------------------------------------------
    # Hybrid semantic context (FACTS → OUTPUTS → FALLBACK)
    # ------------------------------------------------------------------

    def build_semantic_context(
        self,
        query: str,
        current_agent: AgentConfig,
        top_k: int = 5,
        exclude_agent_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build semantic context with safe degradation.

        Priority order:
        1. Structured facts (if available)
        2. Semantically relevant full outputs
        3. Full deterministic fallback
        """

        # --------------------------------------------------------------
        # 1️⃣ Try structured facts first
        # --------------------------------------------------------------

        if self.memory.has_vector_memory():
            relevant_facts = self.memory.search_facts(
                query=query,
                n_results=top_k,
                exclude_agent_ids=exclude_agent_ids
            )

            if relevant_facts:
                return {
                    "query": query,
                    "relevant_facts": relevant_facts,
                    "context_mode": "facts",
                    "current_agent": {
                        "id": current_agent.id,
                        "role": current_agent.role,
                        "goal": current_agent.goal
                    }
                }

        # --------------------------------------------------------------
        # 2️⃣ Fallback: semantic search over full outputs
        # --------------------------------------------------------------

        previous_outputs: Dict[str, str] = {}
        if self.memory.has_vector_memory():
            results = self.memory.search_relevant_context(
                query=query,
                n_results=top_k,
                exclude_agent_ids=exclude_agent_ids
            )

            for result in results:
                agent_id = result.get("agent_id")
                output = result.get("output")
                if agent_id and output:
                    previous_outputs[agent_id] = output

            if previous_outputs:
                return {
                    "query": query,
                    "previous_outputs": previous_outputs,
                    "context_mode": "semantic_outputs",
                    "current_agent": {
                        "id": current_agent.id,
                        "role": current_agent.role,
                        "goal": current_agent.goal
                    }
                }

        # --------------------------------------------------------------
        # 3️⃣ Final fallback: all outputs
        # --------------------------------------------------------------

        previous_outputs = self.memory.get_all_outputs()
        if exclude_agent_ids:
            for agent_id in exclude_agent_ids:
                previous_outputs.pop(agent_id, None)

        return {
            "query": query,
            "previous_outputs": previous_outputs,
            "context_mode": "all_outputs",
            "current_agent": {
                "id": current_agent.id,
                "role": current_agent.role,
                "goal": current_agent.goal
            }
        }

    # ------------------------------------------------------------------
    # Debug / display helper
    # ------------------------------------------------------------------

    def format_context_for_display(self, context: Dict[str, Any]) -> str:
        """Format context for human-readable inspection"""
        lines: List[str] = []

        if context.get("query"):
            lines.append(f"Query: {context['query']}")

        if context.get("current_agent"):
            agent = context["current_agent"]
            lines.append(
                f"Current Agent: {agent.get('role', 'Unknown')} ({agent.get('id', 'unknown')})"
            )

        if context.get("relevant_facts"):
            lines.append("Relevant Facts:")
            for fact in context["relevant_facts"]:
                content = fact.get("content") or fact.get("text") or str(fact)
                lines.append(f"  - {content}")

        if context.get("previous_outputs"):
            lines.append("Previous Outputs:")
            for agent_id, output in context["previous_outputs"].items():
                preview = output[:100] + "..." if len(output) > 100 else output
                lines.append(f"  - {agent_id}: {preview}")

        return "\n".join(lines)