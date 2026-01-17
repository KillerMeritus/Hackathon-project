"""
Shared Memory Store - centralized memory managed by the orchestrator

Supports hybrid storage:
- JSON files for persistence and full state
- ChromaDB vector database for semantic search (optional)
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from pathlib import Path

from ..core.models import LogEntry, MemoryState

# Lazy import to avoid circular imports and optional dependency
if TYPE_CHECKING:
    from .vector_memory import VectorMemory


class SharedMemory:
    """
    Centralized memory store for the orchestration engine.

    All agent outputs pass through the orchestrator and are stored here.
    Agents NEVER communicate directly - everything goes through this memory.
    """

    def __init__(
        self,
        workflow_id: str,
        memory_dir: str = "memory",
        use_vector_db: bool = True,
        vector_db_dir: str = "vector_db"
    ):
        self.workflow_id = workflow_id
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)

        # Core storage (JSON-based)
        self.agent_outputs: Dict[str, str] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.persistent_data: Dict[str, Any] = {}

        # Metadata
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

        # Vector memory (ChromaDB-based) - optional
        self.vector_memory: Optional["VectorMemory"] = None
        self._use_vector_db = use_vector_db
        
        if use_vector_db:
            self._init_vector_memory(vector_db_dir)

    def _init_vector_memory(self, vector_db_dir: str) -> None:
        """Initialize vector memory if ChromaDB is available"""
        try:
            from .vector_memory import VectorMemory, is_chromadb_available
            
            if is_chromadb_available():
                self.vector_memory = VectorMemory(
                    workflow_id=self.workflow_id,
                    persist_directory=vector_db_dir
                )
                self.add_log({
                    "event": "vector_memory_initialized",
                    "vector_db_dir": vector_db_dir
                })
            else:
                self.add_log({
                    "event": "vector_memory_unavailable",
                    "reason": "ChromaDB not installed"
                })
        except Exception as e:
            self.add_log({
                "event": "vector_memory_init_failed",
                "error": str(e)
            })

    def store_output(self, agent_id: str, output: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store an agent's output in memory.
        
        Stores in both JSON (for persistence) and vector DB (for semantic search).
        
        Args:
            agent_id: Unique identifier for the agent
            output: The agent's output text
            metadata: Optional additional metadata for vector storage
        """
        # Store in JSON-based memory
        self.agent_outputs[agent_id] = output
        self.updated_at = datetime.now().isoformat()

        # Store in vector memory if available
        if self.vector_memory:
            try:
                self.vector_memory.store_output(
                    agent_id=agent_id,
                    output=output,
                    metadata=metadata
                )
            except Exception as e:
                self.add_log({
                    "event": "vector_store_failed",
                    "agent_id": agent_id,
                    "error": str(e)
                })

        self.add_log({
            "event": "output_stored",
            "agent_id": agent_id,
            "output_length": len(output),
            "stored_in_vector_db": self.vector_memory is not None
        })

    def store_facts(
        self,
        agent_id: str,
        agent_role: str,
        facts: List[Dict[str, Any]]
    ) -> None:
        """
        Store extracted facts in vector DB.
        
        Args:
            agent_id: ID of source agent
            agent_role: Role of source agent
            facts: List of fact dicts
        """
        if not self.vector_memory or not facts:
            return
        
        try:
            self.vector_memory.store_facts(agent_id, agent_role, facts)
            self.add_log({
                "event": "facts_stored",
                "agent_id": agent_id,
                "facts_count": len(facts)
            })
        except Exception as e:
            self.add_log({
                "event": "facts_store_failed",
                "agent_id": agent_id,
                "error": str(e)
            })

    def search_facts(
        self,
        query: str,
        n_results: int = 10,
        exclude_agent_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant facts using semantic similarity.
        
        Args:
            query: Query to search for
            n_results: Max results
            exclude_agent_ids: Agents to exclude
        
        Returns:
            List of fact dicts
        """
        if not self.vector_memory:
            return []
        
        try:
            return self.vector_memory.search_facts(
                query=query,
                n_results=n_results,
                exclude_agent_ids=exclude_agent_ids
            )
        except Exception as e:
            self.add_log({
                "event": "facts_search_failed",
                "error": str(e)
            })
            return []

    def get_output(self, agent_id: str) -> Optional[str]:
        """Get a specific agent's output"""
        return self.agent_outputs.get(agent_id)

    def get_all_outputs(self) -> Dict[str, str]:
        """Get all agent outputs"""
        return self.agent_outputs.copy()

    def get_outputs_for_agents(self, agent_ids: List[str]) -> Dict[str, str]:
        """Get outputs for specific agents"""
        return {
            agent_id: output
            for agent_id, output in self.agent_outputs.items()
            if agent_id in agent_ids
        }

    def add_log(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the execution log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            **entry
        }
        self.execution_log.append(log_entry)

    def get_log(self) -> List[Dict[str, Any]]:
        """Get the full execution log"""
        return self.execution_log.copy()

    def set_persistent(self, key: str, value: Any) -> None:
        """Store persistent data that survives across runs"""
        self.persistent_data[key] = value
        self.updated_at = datetime.now().isoformat()

    def get_persistent(self, key: str, default: Any = None) -> Any:
        """Get persistent data"""
        return self.persistent_data.get(key, default)

    def search_relevant_context(
        self,
        query: str,
        n_results: int = 3,
        exclude_agent_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant previous outputs using semantic similarity.
        
        Only available if vector memory is enabled.
        
        Args:
            query: The query to search for
            n_results: Maximum number of results to return
            exclude_agent_ids: Agent IDs to exclude from results
        
        Returns:
            List of dicts with {agent_id, output, score, metadata}
        """
        if not self.vector_memory:
            return []
        
        try:
            return self.vector_memory.search_relevant_context(
                query=query,
                n_results=n_results,
                exclude_agent_ids=exclude_agent_ids
            )
        except Exception as e:
            self.add_log({
                "event": "vector_search_failed",
                "error": str(e)
            })
            return []

    def has_vector_memory(self) -> bool:
        """Check if vector memory is available and initialized"""
        return self.vector_memory is not None

    def clear_outputs(self) -> None:
        """Clear all agent outputs (but keep logs and persistent data)"""
        self.agent_outputs = {}
        self.updated_at = datetime.now().isoformat()
        
        # Clear vector memory too
        if self.vector_memory:
            try:
                self.vector_memory.clear()
            except Exception:
                pass
        
        self.add_log({"event": "outputs_cleared"})

    def clear_all(self) -> None:
        """Clear everything except workflow_id"""
        self.agent_outputs = {}
        self.execution_log = []
        self.persistent_data = {}
        self.updated_at = datetime.now().isoformat()
        
        # Clear vector memory too
        if self.vector_memory:
            try:
                self.vector_memory.clear()
            except Exception:
                pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory state to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "agent_outputs": self.agent_outputs,
            "execution_log": self.execution_log,
            "persistent_data": self.persistent_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def to_state(self) -> MemoryState:
        """Convert to MemoryState model"""
        return MemoryState(
            workflow_id=self.workflow_id,
            agent_outputs=self.agent_outputs,
            execution_log=[LogEntry(**log) for log in self.execution_log],
            persistent_data=self.persistent_data
        )

    def save_to_file(self, filename: Optional[str] = None) -> str:
        """Save memory state to JSON file"""
        if filename is None:
            filename = f"{self.workflow_id}.json"

        filepath = self.memory_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        self.add_log({
            "event": "memory_saved",
            "filepath": str(filepath)
        })

        return str(filepath)

    def load_from_file(self, filename: Optional[str] = None) -> bool:
        """Load memory state from JSON file"""
        if filename is None:
            filename = f"{self.workflow_id}.json"

        filepath = self.memory_dir / filename

        if not filepath.exists():
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.agent_outputs = data.get("agent_outputs", {})
            self.execution_log = data.get("execution_log", [])
            self.persistent_data = data.get("persistent_data", {})
            self.created_at = data.get("created_at", self.created_at)
            self.updated_at = datetime.now().isoformat()

            self.add_log({
                "event": "memory_loaded",
                "filepath": str(filepath)
            })

            return True

        except (json.JSONDecodeError, KeyError) as e:
            self.add_log({
                "event": "memory_load_failed",
                "error": str(e)
            })
            return False

    def __repr__(self) -> str:
        return f"SharedMemory(workflow_id={self.workflow_id}, agents={list(self.agent_outputs.keys())})"
