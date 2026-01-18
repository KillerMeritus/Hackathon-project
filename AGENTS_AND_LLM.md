# Agents & LLM Integration Walkthrough

This document explains the core **Agent** and **LLM** (Large Language Model) architecture in the system.

## 1. The Agent (`Agent` Class)

An Agent is an autonomous entity with a specific role, goal, and access to an LLM.

### Internal Structure (`app/agents/base.py`)
Each agent is initialized with:
- **`id`**: Unique identifier (e.g., `researcher`).
- **`role`**: Professional persona (e.g., `Research Assistant`).
- **`goal`**: What it tries to achieve.
- **`llm_provider`**: The AI model powering it (Gemini, OpenAI, etc.).
- **`tools`**: Optional list of tools (discussed in `MCP_INTEGRATION.md`).

### How It Thinks
When an agent runs `execute()`, it constructs a prompt merging:
1.  **System Prompt**: Its role, goal, and tool definitions.
2.  **Task Prompt**: The specific user query + context from previous agents.
3.  **Context**: History from the Vector DB (long-term memory).

## 2. LLM Providers (`BaseLLMProvider`)

The system uses a factory pattern to support multiple AI models interchangeably.

### Architecture
- **`BaseLLMProvider`**: Abstract class defining the `generate()` method.
- **`GeminiProvider`**: Implementation for Google's Gemini models.
- **`OpenAIProvider`**: Implementation for GPT-4 etc.

### Factory Pattern (`app/llm/factory.py`)
When you set `model: gemini` in YAML, the factory automatically:
1.  Check's the provider registry.
2.  Instantiates `GeminiProvider`.
3.  Injects the API key from environment variables.

## 3. Configuration via YAML

You define everything in the `agents` and `models` sections of your YAML file.

### A. Defining Models
Configure connection details for different providers.

```yaml
models:
  gemini_flash:
    provider: google
    model: gemini-2.5-flash
    temperature: 0.7
  
  gpt4:
    provider: openai
    model: gpt-4o
    temperature: 0.2
```

### B. Configuring Agents
Link an agent to a specific model configuration.

```yaml
agents:
  - id: coder
    role: Senior Developer
    model: gemini_flash    # References 'gemini_flash' from models section above
    goal: Write clean Python code
    instruction: |
      Follow PEP 8 standards.
      Include docstrings.
```

## 4. Execution Flow

1.  **Orchestrator** reads YAML.
2.  **Factory** creates `GeminiProvider` for the `coder` agent.
3.  **Agent** `coder` is initialized with this provider.
4.  **Workflow** triggers `coder.execute()`.
5.  **Agent** sends prompt to `GeminiProvider`.
6.  **GeminiProvider** calls Google API -> returns text.
7.  **Agent** returns text to Orchestrator.

## 5. Adding Support for New LLMs

To add a new provider (e.g., Anthropic):

1.  Create `app/llm/anthropic.py` inheriting from `BaseLLMProvider`.
2.  Implement the `generate()` method.
3.  Register it in `app/llm/factory.py`.
4.  Add `ANTHROPIC_API_KEY` to `.env`.

## 6. Diagram

```mermaid
graph TD
    YAML[YAML Config] -->|Defines| AgentConf[Agent Config]
    YAML -->|Defines| ModelConf[Model Config]
    
    Factory[LLM Factory] -->|Reads| ModelConf
    Factory -->|Creates| Provider[LLM Provider (Gemini/OpenAI)]
    
    AgentConf -->|Init| Agent[Agent Instance]
    Provider -->|Injected Into| Agent
    
    Agent -->|Execute| Provider
    Provider -->|API Call| Cloud[Google/OpenAI Cloud]
```
