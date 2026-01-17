"""
Context Builder - builds context dictionaries for agents

Supports two modes:
- Traditional: Pass all previous outputs
- Semantic: Use vector search to find relevant outputs
"""
from typing import Dict, Any, List, Optional

from .memory import SharedMemory
from ..core.models import AgentConfig


class ContextBuilder:
    """
    Builds context dictionaries for agents.

    The context is what gets passed to an agent when it executes.
    All context flows through the orchestrator - agents never talk directly.
    """

    def __init__(self, memory: SharedMemory):
        self.memory = memory

    def build_initial_context(self, query: str) -> Dict[str, Any]:
        """Build initial context with just the user query"""
        return {
            "query": query,
            "previous_outputs": {},
            "current_agent": None
        }

    def build_sequential_context(
        self,
        query: str,
        current_agent: AgentConfig,
        executed_agents: List[str],
        use_semantic: bool = False,
        semantic_top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Build context for sequential workflow.

        In sequential mode, each agent receives:
        - The original query
        - Outputs from previous agents (all or semantically relevant)
        - Info about itself
        
        Args:
            query: The user's query
            current_agent: Configuration of the current agent
            executed_agents: List of agent IDs that have already executed
            use_semantic: If True, use semantic search for relevant outputs
            semantic_top_k: Number of relevant outputs to retrieve (if semantic)
        """
        # Use semantic search if enabled and vector memory is available
        if use_semantic and self.memory.has_vector_memory():
            return self.build_semantic_context(
                query=query,
                current_agent=current_agent,
                top_k=semantic_top_k,
                exclude_agent_ids=[current_agent.id]
            )
        
        # Traditional mode: get outputs from all previously executed agents
        previous_outputs = {}
        for agent_id in executed_agents:
            output = self.memory.get_output(agent_id)
            if output:
                previous_outputs[agent_id] = output

        return {
            "query": query,
            "previous_outputs": previous_outputs,
            "current_agent": {
                "id": current_agent.id,
                "role": current_agent.role,
                "goal": current_agent.goal
            }
        }

    def build_parallel_context(
        self,
        query: str,
        current_agent: AgentConfig
    ) -> Dict[str, Any]:
        """
        Build context for parallel workflow branches.

        In parallel mode, branch agents receive:
        - The original query
        - NO previous outputs (they run simultaneously)
        - Info about themselves
        """
        return {
            "query": query,
            "previous_outputs": {},
            "current_agent": {
                "id": current_agent.id,
                "role": current_agent.role,
                "goal": current_agent.goal
            }
        }

    def build_aggregator_context(
        self,
        query: str,
        aggregator_agent: AgentConfig,
        branch_agent_ids: List[str],
        use_semantic: bool = False,
        semantic_top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Build context for the aggregator agent in parallel workflow.

        The aggregator receives:
        - The original query
        - Outputs from branch agents (all or semantically relevant)
        - Info about itself
        
        Args:
            query: The user's query
            aggregator_agent: Configuration of the aggregator agent
            branch_agent_ids: List of branch agent IDs
            use_semantic: If True, use semantic search for relevant outputs
            semantic_top_k: Number of relevant outputs to retrieve (if semantic)
        """
        # Use semantic search if enabled
        if use_semantic and self.memory.has_vector_memory():
            return self.build_semantic_context(
                query=query,
                current_agent=aggregator_agent,
                top_k=semantic_top_k,
                exclude_agent_ids=[aggregator_agent.id]
            )
        
        # Traditional mode: get all branch outputs
        previous_outputs = self.memory.get_outputs_for_agents(branch_agent_ids)

        return {
            "query": query,
            "previous_outputs": previous_outputs,
            "current_agent": {
                "id": aggregator_agent.id,
                "role": aggregator_agent.role,
                "goal": aggregator_agent.goal
            }
        }

    def build_semantic_context(
        self,
        query: str,
        current_agent: AgentConfig,
        top_k: int = 3,
        exclude_agent_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build context using semantic search over previous outputs.
        
        Uses ChromaDB vector search to find the most relevant previous
        outputs based on semantic similarity to the query.
        
        Args:
            query: The user's query (used for semantic search)
            current_agent: Configuration of the current agent
            top_k: Maximum number of relevant outputs to include
            exclude_agent_ids: Agent IDs to exclude from search results
        
        Returns:
            Context dictionary with semantically relevant previous outputs
        """
        previous_outputs = {}
        relevance_scores = {}
        
        # Search for relevant context using vector memory
        if self.memory.has_vector_memory():
            results = self.memory.search_relevant_context(
                query=query,
                n_results=top_k,
                exclude_agent_ids=exclude_agent_ids
            )
            
            for result in results:
                agent_id = result.get("agent_id")
                output = result.get("output")
                score = result.get("score", 0)
                
                if agent_id and output:
                    previous_outputs[agent_id] = output
                    relevance_scores[agent_id] = score
        
        # If no vector memory or no results, fall back to all outputs
        if not previous_outputs:
            previous_outputs = self.memory.get_all_outputs()
            # Remove current agent's output if present
            if exclude_agent_ids:
                for agent_id in exclude_agent_ids:
                    previous_outputs.pop(agent_id, None)
        
        return {
            "query": query,
            "previous_outputs": previous_outputs,
            "relevance_scores": relevance_scores,  # Optional: for debugging/logging
            "context_mode": "semantic" if relevance_scores else "all",
            "current_agent": {
                "id": current_agent.id,
                "role": current_agent.role,
                "goal": current_agent.goal
            }
        }

    def format_context_for_display(self, context: Dict[str, Any]) -> str:
        """Format context for human-readable display"""
        lines = []

        if context.get("query"):
            lines.append(f"Query: {context['query']}")

        if context.get("current_agent"):
            agent = context["current_agent"]
            lines.append(f"Current Agent: {agent.get('role', 'Unknown')} ({agent.get('id', 'unknown')})")

        if context.get("previous_outputs"):
            lines.append("Previous Outputs:")
            for agent_id, output in context["previous_outputs"].items():
                preview = output[:100] + "..." if len(output) > 100 else output
                lines.append(f"  - {agent_id}: {preview}")

        return "\n".join(lines)
