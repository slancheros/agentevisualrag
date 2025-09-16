from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class RetrievalCandidate:
    '''
    Candidato para la recuperación visual.
    '''
    id: str
    filepath: str
    similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnrichedItem:
    '''
    Item enriquecido para la recuperación visual.
    '''
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
    '''
    Respuesta del agente para la recuperación visual.
    '''
    query_image: str
    results: List[EnrichedItem]

@dataclass
class AgentConfig:
    '''Configuración del agente visual.'''
    top_k: int = 10
    prefer_online: bool = True
