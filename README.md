# YAML Multi-Agent Orchestration Engine

A declarative AI agent workflow system that enables you to define and execute multi-agent pipelines using simple YAML configuration files.

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────────┐
│                         USER / CLI                          │
│                                                             │
│   python run.py workflow.yaml --query "User Task"           │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION ENGINE                     │
│                                                             │
│  • Parses YAML workflow                                     │
│  • Resolves execution pattern                               │
│    - Sequential / Parallel / Hierarchical                   │
│  • Mediates ALL memory access & tool calls                  │
│  • Assembles final prompts for agents (injects context)     │
└───────────────┬───────────────────────────────┬─────────────┘
                │                               │
                │                               │
                │                               │
   ┌────────────▼─────────────┐     ┌────────────▼─────────────┐
   │   (Orchestrator retrieves│     │   (Orchestrator retrieves│
   │    shared context first) │     │    shared context first) │
   └────────────┬─────────────┘     └────────────┬─────────────┘
                │                               │
                ▼                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      VECTOR DATABASE (ChromaDB)                      │
│                                                                      │
│  • Stores semantic embeddings, original text, metadata (agent_id,   │
│    workflow_id, timestamp, type)                                     │
│  • Queried by Orchestrator for Top-K relevant memories               │
└──────────────────────────────────────────────────────────────────────┘
                ▲                               ▲
                │                               │
                │  (Orchestrator injects retrieved context into prompts)
                │                               │
┌───────────────┴──────────────┐     ┌──────────┴───────────┐
│ SHORT-TERM WORKFLOW MEMORY   │     │  PROMPT ASSEMBLY      │
│  (in-memory store inside     │     │  (Orchestrator builds │
│   Orchestrator for runtime)  │     │   Role + Goal +       │
│                              │     │   Retrieved Context)  │
└───────────────┬──────────────┘     └──────────┬───────────┘
                │                               │
                │                               │
                ▼                               ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│        AGENT A          │      │        AGENT B          │
│   (Role + Goal + Prompt)│      │   (Role + Goal + Prompt)│
│                         │      │                         │
│  • Receives final prompt│      │  • Receives final prompt│
│    from Orchestrator    │      │    from Orchestrator    │
│  • Executes LLM call    │      │  • Executes LLM call    │
│  • When tool needed ->  │      │  • When tool needed ->  │
│    ASK ORCHESTRATOR     │      │    ASK ORCHESTRATOR     │
│  • Returns output to    │      │  • Returns output to    │
│    Orchestrator         │      │    Orchestrator         │
└──────────────┬──────────┘      └──────────────┬──────────┘
               │                                │
               │                                │
               │                                │
               ▼                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR                                   │
│  • Receives agent outputs                                               │
│  • Stores outputs to:                                                   │
│     - SHORT-TERM (workflow context)                                     │
│     - VECTOR DB (long-term memory; creates embeddings & metadata)       │
│  • Handles agent tool requests:                                         │
│     1) Agent asks Orchestrator for a tool call                          │
│     2) Orchestrator forwards request to MCP Server                      │
│     3) MCP Server processes and returns result to Orchestrator          │
│     4) Orchestrator returns tool result to requesting Agent             │
└──────────────┬───────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                         MCP SERVER                           │
│                                                              │
│  • Exposes tools via Model Context Protocol                  │
│  • Performs external API calls, DB access, file ops, etc.    │
│  • Returns results to Orchestrator (never directly to agent) │
└─────────────────────────────────────────────────────────────┘



## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to project
cd final-YAML-Project

# Install dependencies
pip install -r requirements.txt

# Set your API key (choose one)
echo 'GOOGLE_API_KEY=your-gemini-api-key' > .env
# OR
echo 'OPENAI_API_KEY=your-openai-api-key' > .env
```

### 2. Run a Workflow

```bash
# Basic execution
python3 run.py examples/sequential.yaml --query "Tell me about AI"

# Parallel workflow
python3 run.py examples/parallel.yaml --query "Design a todo app"
```

---

## 📊 Viewing Execution Logs

To see detailed logs of what happens during the generation process, use the `--verbose` flag:

```bash
python3 run.py examples/sequential.yaml --query "Tell me about AI" --verbose
```

### Sample Verbose Output

```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Time                ┃ Event                     ┃ Agent      ┃ Details    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 2026-01-18T10:13:19 │ vector_memory_initialized │ -          │            │
│ 2026-01-18T10:13:19 │ orchestrator_initialized  │ -          │            │
│ 2026-01-18T10:13:19 │ execution_start           │ -          │            │
│ 2026-01-18T10:13:19 │ sequential_start          │ -          │            │
│ 2026-01-18T10:13:19 │ step_start                │ researcher │            │
│ 2026-01-18T10:13:19 │ agent_start               │ researcher │            │
│ 2026-01-18T10:13:31 │ output_stored             │ researcher │ 9407 chars │
│ 2026-01-18T10:13:31 │ facts_stored              │ researcher │            │
│ 2026-01-18T10:13:31 │ agent_complete            │ researcher │ 9407 chars │
│ 2026-01-18T10:13:31 │ step_complete             │ researcher │ 9407 chars │
│ 2026-01-18T10:13:31 │ step_start                │ writer     │            │
│ 2026-01-18T10:13:31 │ agent_start               │ writer     │            │
│ 2026-01-18T10:13:38 │ output_stored             │ writer     │ 2828 chars │
│ 2026-01-18T10:13:39 │ agent_complete            │ writer     │ 2828 chars │
│ 2026-01-18T10:13:39 │ step_complete             │ writer     │ 2828 chars │
│ 2026-01-18T10:13:39 │ sequential_complete       │ -          │            │
│ 2026-01-18T10:13:39 │ execution_complete        │ -          │            │
│ 2026-01-18T10:13:39 │ memory_saved              │ -          │            │
└─────────────────────┴───────────────────────────┴────────────┴────────────┘
```

### Log Events Explained

| Event | Description |
|-------|-------------|
| `vector_memory_initialized` | Vector database for persistent memory is ready |
| `orchestrator_initialized` | Workflow engine is set up |
| `execution_start` | Workflow execution begins |
| `agent_start` | An agent starts processing |
| `output_stored` | Agent output saved to memory |
| `facts_stored` | Key facts extracted and stored |
| `agent_complete` | Agent finished processing |
| `execution_complete` | Entire workflow completed |
| `memory_saved` | All data persisted to disk |

---

## 📁 Log Storage Locations

| Location | Description |
|----------|-------------|
| `memory/` | Workflow execution history and agent outputs |
| `vector_db/` | Semantic vector embeddings for persistent memory |

---

## 🛠️ CLI Commands

```bash
# Run workflow
python3 run.py <yaml_file> --query "your query"

# Run with verbose logs
python3 run.py <yaml_file> --query "your query" --verbose

# Validate YAML only (no execution)
python3 run.py --validate <yaml_file>

# Start API server
python3 run.py --server
```

---

## 🔑 Supported Models

| Provider | Model | Environment Variable |
|----------|-------|---------------------|
| Google | gemini-2.5-flash | `GOOGLE_API_KEY` |
| OpenAI | gpt-4o | `OPENAI_API_KEY` |
| Anthropic | claude-sonnet-4-20250514 | `ANTHROPIC_API_KEY` |

---

## 📄 Example YAML Structure

```yaml
agents:
  - id: researcher
    role: Research Assistant
    model: gemini
    goal: Find key insights
    instruction: |
      Analyze the topic and provide findings.

  - id: writer
    role: Content Writer
    model: gemini
    goal: Write engaging content
    instruction: |
      Create a summary from the research.

workflow:
  type: sequential
  steps:
    - agent: researcher
    - agent: writer

models:
  gemini:
    provider: google
    model: gemini-2.5-flash
    max_tokens: 4096
    temperature: 0.7
```

---

## 🚀 MCP Tools Integration

To use MCP (Model Context Protocol) tools:

### Terminal 1: Start MCP Server
```bash
python3 mcp_server.py
```

### Terminal 2: Run Tool-Enabled Workflow
```bash
python3 run.py examples/submission/03_tool_enabled_data_analysis.yaml --query "Analyze Q4 sales data"
```
