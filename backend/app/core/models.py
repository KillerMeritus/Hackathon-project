"""
Pydantic models for YAML configuration and execution results
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class StepConfig(BaseModel):
    """Configuration for a single workflow step"""
    agent: str = Field(..., description="Agent ID to execute")
    input: Optional[str] = Field(None, description="Optional input override")


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    id: str = Field(..., description="Unique agent identifier")
    role: str = Field(..., description="Human-readable role")
    goal: str = Field(..., description="Task or objective")
    model: str = Field(default="claude", description="LLM model to use")
    tools: List[str] = Field(default_factory=list, description="List of tools")
    instruction: Optional[str] = Field(None, description="Custom instruction")
    description: Optional[str] = Field(None, description="Agent description")
    sub_agents: List[str] = Field(default_factory=list, description="Sub-agent IDs")


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution"""
    type: str = Field(..., description="Workflow type: sequential or parallel")
    steps: Optional[List[StepConfig]] = Field(None, description="Steps for sequential")
    branches: Optional[List[str]] = Field(None, description="Branches for parallel")
    then: Optional[StepConfig] = Field(None, description="Aggregator after parallel")


class ModelConfig(BaseModel):
    """Configuration for an LLM model"""
    provider: str = Field(..., description="Provider: anthropic, openai, google")
    model: str = Field(..., description="Model name/ID")
    max_tokens: int = Field(default=4096, description="Max output tokens")
    temperature: float = Field(default=0.7, description="Temperature setting")


class YAMLConfig(BaseModel):
    """Root configuration parsed from YAML"""
    agents: List[AgentConfig] = Field(..., description="List of agent configurations")
    workflow: WorkflowConfig = Field(..., description="Workflow configuration")
    models: Dict[str, ModelConfig] = Field(
        default_factory=dict,
        description="Model configurations"
    )


class LogEntry(BaseModel):
    """A single log entry"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event: str
    agent_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class MemoryState(BaseModel):
    """Represents the current memory state"""
    workflow_id: str
    agent_outputs: Dict[str, str] = Field(default_factory=dict)
    execution_log: List[LogEntry] = Field(default_factory=list)
    persistent_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Result of workflow execution"""
    workflow_id: str
    success: bool
    final_output: str
    agent_outputs: Dict[str, str] = Field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    execution_time: Optional[float] = None