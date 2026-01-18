"""
Engine module – Orchestrator, Memory, Context, and Executors

This module exposes the public engine API.
Optional components (VectorMemory) degrade gracefully if dependencies are missing.
"""

from .memory import SharedMemory
from .context import ContextBuilder
from .orchestrator import Orchestrator
from .memory_extractor import MemoryExtractor

# Optional: VectorMemory (requires chromadb)
try:
    from .vector_memory import VectorMemory, is_chromadb_available
except ImportError:
    VectorMemory = None

    def is_chromadb_available() -> bool:
        return False

__all__ = [
    "SharedMemory",
    "ContextBuilder",
    "Orchestrator",
    "MemoryExtractor",
    "VectorMemory",
    "is_chromadb_available",
]