from app.core.orchestrator import VisualAgent
from app.core.types import AgentConfig
from app.core.tools.mock_embedder import MockEmbedder
from app.core.tools.mock_dataset import MockDataset
from app.core.tools.mock_vector_store import MockVectorStore
from app.core.tools.mock_enricher import MockEnricher
from app.core.tools.weaviate_vector_store import WeaviateVectorStore
from app.core.tools.clip_embedder import CLIPEmbedder
from app.core.tools.enricher import SimpleEnricher

import os

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
WVT_CLASS = os.getenv("WVT_CLASS", "FashionItem")   


# Singletons simples para evitar reindexación constante
_embedder = MockEmbedder(dim=128)

_vstore   = WeaviateVectorStore(url=WEAVIATE_URL, api_key=WEAVIATE_API_KEY, class_name=WVT_CLASS)
_enricher = MockEnricher(seed=42)

agent_singleton = VisualAgent(
    embedder=_embedder,
    dataset=None,# placeholder, se inyecta en runtime
    vstore=_vstore,
    enricher=_enricher,
    config=AgentConfig(top_k=12, prefer_online=True),
)
