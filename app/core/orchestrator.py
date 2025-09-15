from typing import List, Dict, Any
from .types import AgentConfig, AgentResponse, EnrichedItem, RetrievalCandidate
from .tools.base import EmbedderTool, DatasetTool, VectorStoreTool, EnricherTool

class VisualAgent:
    def __init__(
        self,
        embedder: EmbedderTool,
        dataset: DatasetTool,
        vstore: VectorStoreTool,
        enricher: EnricherTool,
        config: AgentConfig = AgentConfig(),
    ):
        self.embedder = embedder
        self.dataset = dataset
        self.vstore = vstore
        self.enricher = enricher
        self.cfg = config
        self._indexed = False

    def _ensure_index(self, limit: int = 200):
        if self._indexed:
            return
        fps = self.dataset.sample_paths(limit=limit)
        vecs = [self.embedder.embed_image(fp) for fp in fps]
        payloads = [{"filepath": fp} for fp in fps]
        self.vstore.index(vecs, payloads)
        self._indexed = True

    def _retrieve(self, qvec: List[float], k: int) -> List[RetrievalCandidate]:
        raw = self.vstore.query(qvec, k=k)
        out: List[RetrievalCandidate] = []
        for r in raw:
            fp = r["filepath"]
            sim = float(r["score"])
            md = self.dataset.get_metadata(fp)
            out.append(RetrievalCandidate(id=fp, filepath=fp, similarity=sim, metadata=md))
        return out

    def _rank(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def key_fn(x):
            priority = 0 if (self.cfg.prefer_online and x.get("source") == "online") else 1
            sim = -float(x.get("similarity", 0.0))
            price = float(x.get("price", 1e12))
            return (priority, sim, price)
        return sorted(items, key=key_fn)

    def retrieve(self, query_image: str) -> AgentResponse:
        self._ensure_index()
        qvec = self.embedder.embed_image(query_image)
        cands = self._retrieve(qvec, k=self.cfg.top_k)
        items = [{"id": c.id, "filepath": c.filepath, "similarity": c.similarity, **c.metadata} for c in cands]
        enriched = self.enricher.enrich(items)
        ranked = self._rank(enriched)
        results = [
            EnrichedItem(
                id=x["id"], filepath=x["filepath"], similarity=float(x["similarity"]),
                title=x.get("title"), brand=x.get("brand"), color=x.get("color"),
                price=x.get("price"), currency=x.get("currency", "EUR"),
                source=x.get("source"), url=x.get("url")
            )
            for x in ranked
        ]
        return AgentResponse(query_image=query_image, results=results)
