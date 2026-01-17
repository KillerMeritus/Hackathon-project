"""
Vector Memory Store - ChromaDB-based semantic memory for agent outputs

This module provides vector-based storage and retrieval for agent outputs,
enabling semantic search over previous outputs for context building.
"""
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorMemory:
    """
    ChromaDB-based vector storage for agent outputs.
    
    Stores agent outputs with embeddings for semantic search.
    All agent outputs pass through the orchestrator and are stored here
    alongside the JSON-based SharedMemory for hybrid storage.
    """
    
    def __init__(
        self,
        workflow_id: str,
        persist_directory: str = "vector_db",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize VectorMemory with ChromaDB.
        
        Args:
            workflow_id: Unique identifier for this workflow
            persist_directory: Directory to persist ChromaDB data
            embedding_model: Sentence transformer model for embeddings
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. Install with: pip install chromadb sentence-transformers"
            )
        
        self.workflow_id = workflow_id
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        self.embedding_model = embedding_model
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection for this workflow
        # Using default embedding function (sentence-transformers)
        self.collection = self.client.get_or_create_collection(
            name=self._sanitize_collection_name(workflow_id),
            metadata={"workflow_id": workflow_id, "created_at": datetime.now().isoformat()}
        )
        
        self.created_at = datetime.now().isoformat()
    
    def _sanitize_collection_name(self, name: str) -> str:
        """Sanitize collection name to meet ChromaDB requirements."""
        # ChromaDB collection names: 3-63 chars, alphanumeric, underscores, hyphens
        sanitized = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        sanitized = sanitized[:63] if len(sanitized) > 63 else sanitized
        if len(sanitized) < 3:
            sanitized = f"wf_{sanitized}"
        return sanitized
    
    def store_output(
        self,
        agent_id: str,
        output: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store an agent's output in the vector database.
        
        Args:
            agent_id: Unique identifier for the agent
            output: The agent's output text
            metadata: Optional additional metadata
        """
        if not output or not output.strip():
            return
        
        # Build metadata
        doc_metadata = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "output_length": len(output),
            "workflow_id": self.workflow_id,
            "item_type": "full_output"  # Mark as full output (not a fact)
        }
        if metadata:
            doc_metadata.update(metadata)
        
        # Generate unique ID for this document
        doc_id = f"{self.workflow_id}_{agent_id}_output"
        
        # Upsert (update or insert) the document
        self.collection.upsert(
            ids=[doc_id],
            documents=[output],
            metadatas=[doc_metadata]
        )
    
    def store_facts(
        self,
        agent_id: str,
        agent_role: str,
        facts: List[Dict[str, Any]]
    ) -> None:
        """
        Store extracted facts in the vector database.
        Each fact is stored as a separate document for fine-grained retrieval.
        
        Args:
            agent_id: ID of the source agent
            agent_role: Role of the source agent
            facts: List of fact dicts with type, content, etc.
        """
        if not facts:
            return
        
        ids = []
        documents = []
        metadatas = []
        
        for i, fact in enumerate(facts):
            fact_id = f"{self.workflow_id}_{agent_id}_fact_{i}"
            ids.append(fact_id)
            documents.append(fact.get("content", ""))
            metadatas.append({
                "agent_id": agent_id,
                "agent_role": agent_role,
                "item_type": fact.get("type", "fact"),
                "timestamp": fact.get("timestamp", datetime.now().isoformat()),
                "confidence": fact.get("confidence", 1.0),
                "workflow_id": self.workflow_id
            })
        
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    def search_relevant_context(
        self,
        query: str,
        n_results: int = 3,
        exclude_agent_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant previous outputs using semantic similarity.
        
        Args:
            query: The query to search for
            n_results: Maximum number of results to return
            exclude_agent_ids: Agent IDs to exclude from results
        
        Returns:
            List of dicts with {agent_id, output, score, metadata}
        """
        if self.collection.count() == 0:
            return []
        
        # Adjust n_results if we have fewer documents
        actual_n = min(n_results, self.collection.count())
        
        # Build where filter if excluding agents
        where_filter = None
        if exclude_agent_ids:
            where_filter = {
                "agent_id": {"$nin": exclude_agent_ids}
            }
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_n,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            # If where filter fails, query without it
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_n,
                include=["documents", "metadatas", "distances"]
            )
        
        # Process results
        context_results = []
        if results and results.get("documents") and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 0
                
                # Filter by exclude list if where filter wasn't supported
                agent_id = metadata.get("agent_id", f"agent_{i}")
                if exclude_agent_ids and agent_id in exclude_agent_ids:
                    continue
                
                context_results.append({
                    "agent_id": agent_id,
                    "output": doc,
                    "score": 1 - distance,  # Convert distance to similarity score
                    "metadata": metadata
                })
        
        return context_results
    
    def search_facts(
        self,
        query: str,
        n_results: int = 10,
        item_types: Optional[List[str]] = None,
        exclude_agent_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant facts (not full outputs) using semantic similarity.
        
        Args:
            query: The query to search for
            n_results: Maximum number of results
            item_types: Filter by types (fact, decision, requirement, insight)
            exclude_agent_ids: Agent IDs to exclude
        
        Returns:
            List of dicts with {type, content, agent_id, agent_role, score}
        """
        if self.collection.count() == 0:
            return []
        
        # Filter to exclude full outputs
        where_filter = {"item_type": {"$ne": "full_output"}}
        
        actual_n = min(n_results, self.collection.count())
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_n,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_n,
                include=["documents", "metadatas", "distances"]
            )
        
        fact_results = []
        if results and results.get("documents") and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 0
                
                # Skip full outputs
                if metadata.get("item_type") == "full_output":
                    continue
                
                agent_id = metadata.get("agent_id", "unknown")
                if exclude_agent_ids and agent_id in exclude_agent_ids:
                    continue
                
                fact_results.append({
                    "type": metadata.get("item_type", "fact"),
                    "content": doc,
                    "agent_id": agent_id,
                    "agent_role": metadata.get("agent_role", "Unknown"),
                    "score": 1 - distance,
                    "confidence": metadata.get("confidence", 1.0)
                })
        
        return fact_results
    
    def get_output(self, agent_id: str) -> Optional[str]:
        """
        Get a specific agent's output.
        
        Args:
            agent_id: The agent ID to retrieve
        
        Returns:
            The agent's output or None if not found
        """
        doc_id = f"{self.workflow_id}_{agent_id}"
        
        try:
            result = self.collection.get(
                ids=[doc_id],
                include=["documents"]
            )
            if result and result.get("documents"):
                return result["documents"][0]
        except Exception:
            pass
        
        return None
    
    def get_all_outputs(self) -> Dict[str, str]:
        """
        Retrieve all stored outputs.
        
        Returns:
            Dictionary mapping agent_id to output
        """
        if self.collection.count() == 0:
            return {}
        
        try:
            results = self.collection.get(
                include=["documents", "metadatas"]
            )
        except Exception:
            return {}
        
        outputs = {}
        if results and results.get("documents"):
            documents = results["documents"]
            metadatas = results.get("metadatas", [])
            
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                agent_id = metadata.get("agent_id", f"agent_{i}")
                outputs[agent_id] = doc
        
        return outputs
    
    def get_outputs_for_agents(self, agent_ids: List[str]) -> Dict[str, str]:
        """
        Get outputs for specific agents.
        
        Args:
            agent_ids: List of agent IDs to retrieve
        
        Returns:
            Dictionary mapping agent_id to output
        """
        outputs = {}
        for agent_id in agent_ids:
            output = self.get_output(agent_id)
            if output:
                outputs[agent_id] = output
        return outputs
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self._sanitize_collection_name(self.workflow_id),
                metadata={"workflow_id": self.workflow_id, "cleared_at": datetime.now().isoformat()}
            )
        except Exception:
            # If delete fails, try to get all IDs and delete them
            try:
                all_ids = self.collection.get()["ids"]
                if all_ids:
                    self.collection.delete(ids=all_ids)
            except Exception:
                pass
    
    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()
    
    def __repr__(self) -> str:
        return f"VectorMemory(workflow_id={self.workflow_id}, count={self.count()})"


def is_chromadb_available() -> bool:
    """Check if ChromaDB is available."""
    return CHROMADB_AVAILABLE
