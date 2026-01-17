# YAML Multi-Agent Orchestration Engine

This project is a hackathon MVP focused on building a
YAML-driven multi-agent AI orchestration system.

## High-Level Idea
- Agents are defined using YAML
- Each agent has a role, goal, and LLM backend
- A central orchestrator controls execution and memory
- Agents never communicate directly with each other

## Team Responsibilities

### Member A – Foundation & API
- YAML parsing and validation
- Pydantic models
- FastAPI endpoints
- CLI runner

### Member B – AI & Agent Layer (This Repository Area)
- LLM abstraction layer
- Concrete LLM providers (OpenAI, Claude, Gemini)
- Agent behavior and prompting logic
- Agent factory (YAML → runtime agents)
- Tool interface (for future extensions)

### Member C – Orchestration Engine
- Orchestrator core logic
- Sequential & parallel execution
- Shared memory and persistence
- Context building between agents

## Development Notes
- This repository is built collaboratively
- Each member owns a clear boundary to avoid conflicts
- Integration happens through well-defined interfaces

