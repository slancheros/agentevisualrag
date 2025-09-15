from app.core.orchestrator import VisualAgent
from app.core.types import AgentConfig
from app.core.tools.mock_embedder import MockEmbedder
from app.core.tools.mock_dataset import MockDataset
from app.core.tools.mock_vector_store import MockVectorStore
from app.core.tools.mock_enricher import MockEnricher

# Singletons simples para evitar reindexación constante
_embedder = MockEmbedder(dim=128)
_dataset  = MockDataset(root_dir="data/images", synthetic_size=200)
_vstore   = MockVectorStore()
_enricher = MockEnricher(seed=42)

agent_singleton = VisualAgent(
    embedder=_embedder,
    dataset=_dataset,
    vstore=_vstore,
    enricher=_enricher,
    config=AgentConfig(top_k=12, prefer_online=True),
)
