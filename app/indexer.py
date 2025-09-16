# app/indexer.py
import os
from app.core.orchestrator import VisualAgent
from app.core.types import AgentConfig
from app.core.tools.mock_embedder import MockEmbedder
from app.core.tools.mock_dataset import MockDataset
from app.core.tools.mock_vector_store import MockVectorStore
from app.core.tools.mock_enricher import MockEnricher

# Intercambiable entre MockVectorStore y un backend real (Weaviate, FAISS, etc.) VectorStoreTool.

def main():
    data_dir = os.getenv("INDEX_DATA_DIR", "/app/data/images")
    limit = int(os.getenv("INDEX_LIMIT", "300"))

    agent = VisualAgent(
        embedder=MockEmbedder(dim=128),
        dataset=MockDataset(root_dir=data_dir, synthetic_size=limit),
        vstore=MockVectorStore(),  # cambia a tu backend de Weaviate real
        enricher=MockEnricher(seed=42),
        config=AgentConfig(top_k=12, prefer_online=True),
    )

    # Fuerza indexación (el orquestador ya lo hace lazy dentro de retrieve,
    # pero aquí dejamos el índice "caliente")
    # Llama a método interno o replica su lógica de indexado:
    fps = agent.dataset.sample_paths(limit=limit)
    vecs = [agent.embedder.embed_image(fp) for fp in fps]
    payloads = [{"filepath": fp} for fp in fps]
    agent.vstore.index(vecs, payloads)

    print(f"Indexados {len(fps)} items desde {data_dir}")

if __name__ == "__main__":
    main()
