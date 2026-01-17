"""
YAML parser and validator for workflow configurations
"""
import yaml
from pathlib import Path
from typing import Tuple, List, Union

from .models import YAMLConfig, AgentConfig, WorkflowConfig, StepConfig, ModelConfig, MCPServerConfig
from .exceptions import YAMLParseError, ValidationError


def load_yaml(file_path: Union[str, Path]) -> dict:
    """Load YAML file and return as dictionary"""
    try:
        path = Path(file_path)
        if not path.exists():
            raise YAMLParseError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)

        if content is None:
            raise YAMLParseError("Empty YAML file")

        return content
    except yaml.YAMLError as e:
        line = getattr(e, 'problem_mark', None)
        if line:
            raise YAMLParseError(str(e), line=line.line + 1, column=line.column + 1)
        raise YAMLParseError(str(e))


def load_yaml_from_string(content: str) -> dict:
    """Load YAML from string content"""
    try:
        data = yaml.safe_load(content)
        if data is None:
            raise YAMLParseError("Empty YAML content")
        return data
    except yaml.YAMLError as e:
        line = getattr(e, 'problem_mark', None)
        if line:
            raise YAMLParseError(str(e), line=line.line + 1, column=line.column + 1)
        raise YAMLParseError(str(e))


def parse_config(yaml_dict: dict) -> YAMLConfig:
    """Parse YAML dictionary into YAMLConfig object"""
    try:
        # Parse agents
        agents = []
        for agent_data in yaml_dict.get('agents', []):
            agents.append(AgentConfig(**agent_data))

        if not agents:
            raise ValidationError("No agents defined", field="agents")

        # Parse workflow
        workflow_data = yaml_dict.get('workflow')
        if not workflow_data:
            raise ValidationError("No workflow defined", field="workflow")

        # Parse workflow steps
        if 'steps' in workflow_data and workflow_data['steps']:
            workflow_data['steps'] = [
                StepConfig(**step) if isinstance(step, dict) else StepConfig(agent=step)
                for step in workflow_data['steps']
            ]

        # Parse 'then' if exists
        if 'then' in workflow_data and workflow_data['then']:
            then_data = workflow_data['then']
            if isinstance(then_data, dict):
                workflow_data['then'] = StepConfig(**then_data)
            else:
                workflow_data['then'] = StepConfig(agent=then_data)

        workflow = WorkflowConfig(**workflow_data)

        # Parse models
        models = {}
        for model_name, model_data in yaml_dict.get('models', {}).items():
            models[model_name] = ModelConfig(**model_data)

        # Parse MCP servers
        mcp_servers = []
        for server_data in yaml_dict.get('mcp_servers', []):
            mcp_servers.append(MCPServerConfig(**server_data))

        return YAMLConfig(
            agents=agents,
            workflow=workflow,
            models=models,
            mcp_servers=mcp_servers
        )

    except Exception as e:
        if isinstance(e, (YAMLParseError, ValidationError)):
            raise
        raise ValidationError(str(e))


def validate_config(config: YAMLConfig) -> Tuple[bool, List[str]]:
    """Validate the configuration for consistency"""
    errors = []

    # Get all agent IDs
    agent_ids = {agent.id for agent in config.agents}

    # Check workflow type
    if config.workflow.type not in ['sequential', 'parallel']:
        errors.append(f"Invalid workflow type: {config.workflow.type}. Must be 'sequential' or 'parallel'")

    # Validate sequential workflow
    if config.workflow.type == 'sequential':
        if not config.workflow.steps:
            errors.append("Sequential workflow requires 'steps'")
        else:
            for i, step in enumerate(config.workflow.steps):
                if step.agent not in agent_ids:
                    errors.append(f"Step {i+1} references unknown agent: '{step.agent}'")

    # Validate parallel workflow
    if config.workflow.type == 'parallel':
        if not config.workflow.branches:
            errors.append("Parallel workflow requires 'branches'")
        else:
            for branch in config.workflow.branches:
                if branch not in agent_ids:
                    errors.append(f"Branch references unknown agent: '{branch}'")

        if config.workflow.then:
            if config.workflow.then.agent not in agent_ids:
                errors.append(f"'then' references unknown agent: '{config.workflow.then.agent}'")

    # Validate agent models
    for agent in config.agents:
        if agent.model and config.models:
            if agent.model not in config.models and agent.model not in ['claude', 'openai', 'gemini']:
                errors.append(f"Agent '{agent.id}' references unknown model: '{agent.model}'")

    # Validate MCP server configurations
    mcp_server_ids = set()
    for server in config.mcp_servers:
        if server.id in mcp_server_ids:
            errors.append(f"Duplicate MCP server ID: '{server.id}'")
        mcp_server_ids.add(server.id)
        
        if server.transport not in ['http', 'stdio']:
            errors.append(f"MCP server '{server.id}' has invalid transport: '{server.transport}'")

    # Validate agent tool references (MCP tools)
    for agent in config.agents:
        for tool in agent.tools:
            if tool.startswith('mcp:'):
                parts = tool.split(':')
                if len(parts) >= 2:
                    server_id = parts[1]
                    if server_id not in mcp_server_ids:
                        errors.append(f"Agent '{agent.id}' references unknown MCP server: '{server_id}'")

    return len(errors) == 0, errors


def load_and_parse(file_path: Union[str, Path]) -> YAMLConfig:
    """Load, parse, and validate a YAML configuration file"""
    yaml_dict = load_yaml(file_path)
    config = parse_config(yaml_dict)

    is_valid, errors = validate_config(config)
    if not is_valid:
        raise ValidationError("Configuration validation failed: " + "; ".join(errors))

    return config


def validate_yaml(content: str) -> Tuple[bool, List[str]]:
    """Validate YAML content without executing"""
    try:
        yaml_dict = load_yaml_from_string(content)
        config = parse_config(yaml_dict)
        return validate_config(config)
    except (YAMLParseError, ValidationError) as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Unexpected error: {str(e)}"]
