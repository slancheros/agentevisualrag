from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class RetrievalCandidate:
    id: str
    filepath: str
    similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnrichedItem:
    id: str
    filepath: str
    similarity: float
    title: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    source: Optional[str] = None
    url: Optional[str] = None

@dataclass
class AgentResponse:
    query_image: str
    results: List[EnrichedItem]

@dataclass
class AgentConfig:
    top_k: int = 10
    prefer_online: bool = True
