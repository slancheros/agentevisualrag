from typing import List, Dict, Any, Tuple
from ..utils import cosine_similarity

class MockVectorStore:
    """
    Vector store en memoria, sin numpy/FAISS.
    Guarda vectores y payloads y responde top-K por coseno.
    """
    def __init__(self):
        self._vecs: List[List[float]] = []
        self._payloads: List[Dict[str, Any]] = []

    def index(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> None:
        assert len(vectors) == len(payloads)
        self._vecs.extend(vectors)
        self._payloads.extend(payloads)

    def query(self, vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
        scores: List[Tuple[int, float]] = []
        for i, v in enumerate(self._vecs):
            sim = cosine_similarity(vector, v)
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:k]
        return [{"filepath": self._payloads[i]["filepath"], "score": s} for i, s in top]
