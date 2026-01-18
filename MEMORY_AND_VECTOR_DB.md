# Memory & Vector DB Integration Walkthrough

This document explains how the **Dual Memory System** work in the YAML Multi-Agent Orchestrator. It combines short-term context sharing with long-term semantic storage.

## 1. The Two Types of Memory

### A. Short-Term Memory (Context Passing)
This is ephemeral memory that lasts only for the duration of a workflow execution.
- **Purpose**: Allows Agent B to know what Agent A did.
- **Mechanism**: The orchestrator passes the `previous_outputs` dictionary to the next agent in the chain.
- **Storage**: In-memory Python dictionary.

### B. Long-Term Memory (Vector DB)
This is persistent memory that survives between different workflow runs.
- **Purpose**: Recall facts, decisions, or insights from days or weeks ago.
- **Mechanism**: Data is embedded (converted to vectors) and stored in a local vector database.
- **Storage**: `chromadb` (local file-based vector store) in the `vector_db/` folder.

## 2. Default Configuration

The system uses **ChromaDB** by default for vector storage.

```python
# app/core/memory.py logic
class VectorMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./vector_db")
        self.collection = self.client.get_or_create_collection("agent_memory")
```

## 3. How Memory is Saved (Write Path)

When an agent completes a task, two things happen:

1.  **Output Extraction**: The system looks for key information in the agent's response.
2.  **Vectorization**: The text is converted into a 384-dimensional vector using `sentence-transformers/all-MiniLM-L6-v2`.
3.  **Storage**: The vector + original text + metadata (agent_id, timestamp) is saved to ChromaDB.

*Note: This usually happens automatically if `memory: true` is enabled in the agent config, or can be triggered manually.*

## 4. How Memory is Retrieved (Read Path)

Before an agent runs, the system queries the Vector DB:

1.  **Query Embedding**: The agent's current instruction/goal is taken as the query.
2.  **Semantic Search**: The system asks ChromaDB: *"Find top 3 past memories semantically related to this goal"*.
3.  **Context Injection**: These retrieved memories are added to the System Prompt under a `## Relevant Context` section.

## 5. YAML Configuration

You can enable/disable memory for specific agents in your YAML file.

```yaml
agents:
  - id: researcher
    role: Research Assistant
    memory: true        # Enable persistent memory read/write
    
workflow:
  type: sequential
  steps:
    - agent: researcher
```

## 6. Directory Structure

```
final-YAML-Project/
├── vector_db/          # ChromaDB files (SQLite + bin files)
│   ├── chroma.sqlite3
│   └── ...
├── memory/             # JSON logs of past executions (human readable)
│   ├── workflow_run_1.json
│   └── ...
```

## 7. Summary Diagram

```mermaid
graph TD
    A[Agent Execution] -->|Generates Output| B(Orchestrator)
    
    B -->|1. Pass Output| C[Next Agent (Short-term)]
    B -->|2. Embed & Save| D[(Vector DB / Chroma)]
    
    D -->|3. Semantic Search| E[Next Run Context]
    E --> A
```
