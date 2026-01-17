"""
Base Agent class - represents an AI agent with a role, goal, and LLM
"""
from typing import Optional, Dict, Any, List

from ..llm.base import BaseLLMProvider
from ..tools.base import BaseTool
from ..core.models import AgentConfig


class Agent:
    

    def __init__(
        self,
        config: AgentConfig,
        llm_provider: BaseLLMProvider,
        tools: Optional[List[BaseTool]] = None
    ):
        self.id = config.id
        self.role = config.role
        self.goal = config.goal
        self.instruction = config.instruction
        self.description = config.description
        self.sub_agents = config.sub_agents

        self.llm_provider = llm_provider
        self.tools = tools or []

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent"""
        prompt_parts = [
            f"You are a {self.role}.",
            f"Your goal is: {self.goal}",
        ]

        if self.description:
            prompt_parts.append(f"Description: {self.description}")

        if self.instruction:
            prompt_parts.append(f"\nInstructions:\n{self.instruction}")

        if self.tools:
            tool_names = [t.name for t in self.tools]
            prompt_parts.append(f"\nYou have access to these tools: {', '.join(tool_names)}")

        prompt_parts.append("\nProvide clear, well-structured responses that fulfill your goal.")

        return "\n".join(prompt_parts)

    def _build_task_prompt(self, context: Dict[str, Any]) -> str:
        """Build the task prompt from context"""
        prompt_parts = []

        # Add the current agent info
        current_agent = context.get("current_agent", {})
        if current_agent:
            prompt_parts.append(f"Complete your task as {current_agent.get('role', self.role)}.")

        # Add goal reminder
        prompt_parts.append(f"\nYour goal: {self.goal}")

        # If there's a specific query, include it
        if context.get("query"):
            prompt_parts.append(f"\nUser Query: {context['query']}")

        return "\n".join(prompt_parts)

    async def execute(self, context: Dict[str, Any]) -> str:
       
        system_prompt = self._build_system_prompt()
        task_prompt = self._build_task_prompt(context)

        # Call the LLM
        response = await self.llm_provider.generate(
            prompt=task_prompt,
            context=context,
            system_prompt=system_prompt
        )

        return response

    def __repr__(self) -> str:
        return f"Agent(id={self.id}, role={self.role}, llm={self.llm_provider.provider_name})"
