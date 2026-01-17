"""
Custom exceptions for the orchestration engine
"""


class OrchestrationError(Exception):
    """Base exception for all orchestration errors"""
    pass


class YAMLParseError(OrchestrationError):
    """Raised when YAML parsing fails"""
    def __init__(self, message: str, line: int = None, column: int = None):
        self.line = line
        self.column = column
        super().__init__(f"YAML Parse Error: {message}" +
                        (f" at line {line}" if line else "") +
                        (f", column {column}" if column else ""))


class ValidationError(OrchestrationError):
    """Raised when configuration validation fails"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(f"Validation Error: {message}" +
                        (f" (field: {field})" if field else ""))


class AgentNotFoundError(OrchestrationError):
    """Raised when a referenced agent doesn't exist"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: '{agent_id}'")


class WorkflowExecutionError(OrchestrationError):
    """Raised when workflow execution fails"""
    def __init__(self, message: str, agent_id: str = None, step: int = None):
        self.agent_id = agent_id
        self.step = step
        super().__init__(f"Workflow Execution Error: {message}" +
                        (f" (agent: {agent_id})" if agent_id else "") +
                        (f" at step {step}" if step is not None else ""))


class LLMProviderError(OrchestrationError):
    """Raised when LLM provider fails"""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"LLM Provider Error ({provider}): {message}")


class ToolExecutionError(OrchestrationError):
    """Raised when tool execution fails"""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"Tool Execution Error ({tool_name}): {message}")