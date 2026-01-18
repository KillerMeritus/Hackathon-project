"""
FastAPI Application - REST API for the YAML Multi-Agent Orchestration Engine
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json

from .core.yaml_parser import load_and_parse, validate_yaml, load_yaml_from_string, parse_config
from .core.exceptions import YAMLParseError, ValidationError, WorkflowExecutionError
from .core.models import ExecutionResult
from .engine.orchestrator import Orchestrator
from .engine.memory import SharedMemory


# Create FastAPI app
app = FastAPI(
    title="YAML Multi-Agent Orchestration Engine",
    description="Declarative multi-agent workflows using YAML configuration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active orchestrators (in production, use Redis or database)
active_workflows: Dict[str, Orchestrator] = {}


# Request/Response Models
class ExecuteRequest(BaseModel):

    yaml_content: str
    query: str
    workflow_id: Optional[str] = None


class ValidateRequest(BaseModel):

    yaml_content: str


class ValidateResponse(BaseModel):

    valid: bool
    errors: List[str]


class HealthResponse(BaseModel):

    status: str
    version: str


class WorkflowStatusResponse(BaseModel):

    workflow_id: str
    exists: bool
    agent_outputs: Dict[str, str]
    log_count: int


# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/validate", response_model=ValidateResponse)
async def validate_workflow(request: ValidateRequest):
    """
    Validate YAML configuration without executing.

    Returns validation status and any errors found.
    """
    is_valid, errors = validate_yaml(request.yaml_content)
    return ValidateResponse(valid=is_valid, errors=errors)


@app.post("/api/execute", response_model=ExecutionResult)
async def execute_workflow(request: ExecuteRequest):
    """
    Execute a workflow from YAML configuration.

    Takes YAML content and a query, returns execution result.
    """
    try:
        # Parse and validate YAML
        yaml_dict = load_yaml_from_string(request.yaml_content)
        config = parse_config(yaml_dict)

        # Create orchestrator
        orchestrator = Orchestrator(config, workflow_id=request.workflow_id)

        # Store for later reference
        active_workflows[orchestrator.workflow_id] = orchestrator

        # Execute workflow
        result = await orchestrator.execute(request.query)

        return result

    except YAMLParseError as e:
        raise HTTPException(status_code=400, detail=f"YAML Parse Error: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(e)}")
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=500, detail=f"Execution Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@app.post("/api/execute/file")
async def execute_workflow_from_file(
    file: UploadFile = File(...),
    query: str = Form(...)
):
    """
    Execute a workflow from an uploaded YAML file.
    """
    try:
        # Read file content
        content = await file.read()
        yaml_content = content.decode('utf-8')

        # Parse and validate
        yaml_dict = load_yaml_from_string(yaml_content)
        config = parse_config(yaml_dict)

        # Create and execute
        orchestrator = Orchestrator(config)
        active_workflows[orchestrator.workflow_id] = orchestrator
        result = await orchestrator.execute(query)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """
    Get the status of a workflow execution.
    """
    orchestrator = active_workflows.get(workflow_id)

    if not orchestrator:
        # Try to load from file
        memory = SharedMemory(workflow_id)
        if memory.load_from_file():
            return WorkflowStatusResponse(
                workflow_id=workflow_id,
                exists=True,
                agent_outputs=memory.get_all_outputs(),
                log_count=len(memory.get_log())
            )

        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            exists=False,
            agent_outputs={},
            log_count=0
        )

    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        exists=True,
        agent_outputs=orchestrator.memory.get_all_outputs(),
        log_count=len(orchestrator.memory.get_log())
    )


@app.get("/api/memory/{workflow_id}")
async def get_workflow_memory(workflow_id: str):
    """
    Get the full memory state of a workflow.
    """
    orchestrator = active_workflows.get(workflow_id)

    if orchestrator:
        return orchestrator.get_memory_state()

    # Try to load from file
    memory = SharedMemory(workflow_id)
    if memory.load_from_file():
        return memory.to_dict()

    raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


@app.get("/api/workflows")
async def list_workflows():
    """
    List all active workflows.
    """
    return {
        "active_workflows": list(active_workflows.keys()),
        "count": len(active_workflows)
    }


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """
    Delete a workflow from active memory.
    """
    if workflow_id in active_workflows:
        del active_workflows[workflow_id]
        return {"deleted": True, "workflow_id": workflow_id}

    raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
