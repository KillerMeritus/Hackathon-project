"""
Agent Factory - creates agents from configuration
"""
from typing import Dict, List, Optional

from .base import Agent
from ..core.models import AgentConfig, YAMLConfig
from ..llm.factory import get_provider_for_agent
from ..tools.registry import get_tools


def create_agent(
    agent_config: AgentConfig,
    models_config: Optional[Dict] = None
) -> Agent:

    models_config = models_config or {}

    # Get the LLM provider for this agent
    llm_provider = get_provider_for_agent(
        agent_config.model,
        models_config
    )

    # Get tools if specified
    tools = []
    if agent_config.tools:
        tools = get_tools(agent_config.tools)

    # Create and return the agent
    return Agent(
        config=agent_config,
        llm_provider=llm_provider,
        tools=tools
    )


def create_agents_from_config(config: YAMLConfig) -> Dict[str, Agent]:
    
    agents = {}

    # Convert models to dict format if needed
    models_dict = {}
    for name, model_cfg in config.models.items():
        if hasattr(model_cfg, 'model_dump'):
            models_dict[name] = model_cfg.model_dump()
        else:
            models_dict[name] = model_cfg

    # Create each agent
    for agent_config in config.agents:
        agent = create_agent(agent_config, models_dict)
        agents[agent.id] = agent

    return agents
