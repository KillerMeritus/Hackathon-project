"""
Memory Extractor - Extracts key facts from agent outputs

Converts unstructured agent outputs into structured memory items
for better retrieval and context building.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MemoryItemType(str, Enum):
    """Types of memory items that can be extracted"""
    FACT = "fact"           # Data points, statistics, observations
    DECISION = "decision"   # Strategic choices, recommendations
    REQUIREMENT = "requirement"  # Product/technical needs
    INSIGHT = "insight"     # Analysis conclusions, interpretations


@dataclass
class MemoryItem:
    """A structured memory item extracted from agent output"""
    type: MemoryItemType
    content: str
    source_agent: str
    source_role: str
    timestamp: str = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "content": self.content,
            "source_agent": self.source_agent,
            "source_role": self.source_role,
            "timestamp": self.timestamp,
            "confidence": self.confidence
        }


class MemoryExtractor:
    """
    Extracts structured memory items from agent outputs.
    
    Uses simple parsing to extract:
    - Facts: Data points and observations
    - Decisions: Recommendations and choices
    - Requirements: Needs and specifications
    - Insights: Conclusions and interpretations
    """

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
    
    async def extract_facts(
        self,
        output: str,
        agent_id: str,
        agent_role: str,
        use_llm: bool = False
    ) -> List[MemoryItem]:
        """
        Extract structured facts from agent output.
        
        Args:
            output: The agent's raw output text
            agent_id: ID of the source agent
            agent_role: Role of the source agent
            use_llm: If True, use LLM for extraction (not implemented yet)
        
        Returns:
            List of MemoryItem objects
        """
        if not output or not output.strip():
            return []
        
        return self._extract_simple(output, agent_id, agent_role)
    
    def _extract_simple(
        self,
        output: str,
        agent_id: str,
        agent_role: str
    ) -> List[MemoryItem]:
        """
        Simple extraction without LLM.
        Extracts bullet points and numbered items.
        """
        items = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith('#'):
                continue
            
            # Extract bullet points
            if line.startswith(('-', '*', '•', '>')):
                content = line.lstrip('-*•> ').strip()
                if len(content) > 10 and len(content) < 500:
                    item_type = self._guess_type(content)
                    items.append(MemoryItem(
                        type=item_type,
                        content=content,
                        source_agent=agent_id,
                        source_role=agent_role,
                        confidence=0.7
                    ))
            
            # Extract numbered items
            elif line and line[0].isdigit() and '.' in line[:3]:
                content = line.split('.', 1)[-1].strip()
                if len(content) > 10 and len(content) < 500:
                    item_type = self._guess_type(content)
                    items.append(MemoryItem(
                        type=item_type,
                        content=content,
                        source_agent=agent_id,
                        source_role=agent_role,
                        confidence=0.7
                    ))
        
        # Limit to top 10 items
        return items[:10]
    
    def _guess_type(self, content: str) -> MemoryItemType:
        """Guess the type of a memory item based on content keywords"""
        content_lower = content.lower()
        
        decision_keywords = ['recommend', 'should', 'suggest', 'price', 'choose', 'decision', 'strategy']
        requirement_keywords = ['must', 'need', 'require', 'essential', 'critical', 'should have']
        insight_keywords = ['trend', 'predict', 'expect', 'analysis', 'conclude', 'indicates']
        
        if any(kw in content_lower for kw in decision_keywords):
            return MemoryItemType.DECISION
        elif any(kw in content_lower for kw in requirement_keywords):
            return MemoryItemType.REQUIREMENT
        elif any(kw in content_lower for kw in insight_keywords):
            return MemoryItemType.INSIGHT
        else:
            return MemoryItemType.FACT
