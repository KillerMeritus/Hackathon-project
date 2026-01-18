# 🚀 Demo Walkthrough Guide

Use this guide to present the **YAML Multi-Agent Orchestration Engine**. It is structured to start simple and build up to complex features.

## 📋 Preparation
Before starting the demo, ensure your environment is set up.

```bash
# 1. Export your API Key (do this once)
export GOOGLE_API_KEY="AIzaSyCX-0xVDXMw6pqdKqeSOZPCqliE1Mx-d2o" 

# 2. Clear previous memory (optional, for a fresh start)
rm -rf memory/* vector_db/*
```

---

## 🔹 Step 1: The "Hello World" (Sequential Workflow)
**Goal:** Show how easy it is to define a pipeline.
**Talking Point:** "We define agents and their order in YAML. No code required. Context is passed automatically."

**Command:**
```bash
python3 run.py examples/sequential.yaml --query "Tell me about electric vehicles"
```
**What to highlight:**
- Show the **Workflow Diagram** printed at the start.
- Show how the **Researcher** passes data to the **Writer**.
- Show the final clean output.

---

## 🔹 Step 2: Advanced Orchestration (Parallel Execution)
**Goal:** Demonstrate the engine's ability to handle complex logic.
**Talking Point:** "Here we run a Backend and Frontend engineer at the same time. The engine waits for both to finish, then aggregates their work for the Tech Lead."

**Command:**
```bash
python3 run.py examples/parallel.yaml --query "Design a simple To-Do App"
```
**What to highlight:**
- Point out `Workflow Type: parallel`.
- Notice how `backend` and `frontend` agents run concurrently.
- Show the `reviewer` consolidating both plans into one final architecture.

---

## 🔹 Step 3: Tool Integration (MCP Support)
**Goal:** Show real-world capability (connecting to external tools).
**Talking Point:** "Agents aren't just for text. They can use tools via the Model Context Protocol (MCP). Here, an agent connects to a local server to fetch data."

**Setup (Requires 2 Terminals):**

**Terminal 1 (Start Server):**
```bash
python3 mcp_server.py
```

**Terminal 2 (Run Workflow):**
```bash
python3 run.py examples/submission/03_tool_enabled_data_analysis.yaml --query "Analyze Q4 sales predictions"
```
**What to highlight:**
- Explain that the `fetch_data` tool is running on the local server.
- The agent *decides* to call the tool, gets the JSON data, and interprets it.

---

## 🔹 Step 4: Under the Hood (Verbose Logs)
**Goal:** Show transparency and debugging.
**Talking Point:** "For developers, we provide full visibility into the execution lifecycle."

**Command:**
```bash
python3 run.py examples/sequential.yaml --query "Explain Quantum Physics" --verbose
```
**What to highlight:**
- Show the **Event Table** at the end.
- Explain events like `output_stored`, `facts_stored`, and `memory_saved`.

---

## 🔹 Step 5: Persistent Memory (The "Magic")
**Goal:** Show the system learns across sessions.
**Talking Point:** "Unlike standard scripts, our agents remember previous interactions using a vector database."

**Run 1 (Teach it something):**
```bash
python3 run.py examples/sequential.yaml --query "My project name is 'Project Achievers'. It is built in Python."
```

**Run 2 (Ask it to recall):**
```bash
python3 run.py examples/sequential.yaml --query "What is the name of my project and what language is it in?"
```
**What to highlight:**
- In Run 2, the agent knows the project name without being told again.
- This proves the **Vector DB** integration is working.

---

## 🏁 Closing
**Summary:** "We've seen declarative YAML configs, parallel execution, tool usage, and long-term memory—all without writing a single line of orchestration code."
