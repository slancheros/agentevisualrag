# app/core/tools/weaviate_vector_store.py
from typing import List, Dict, Any, Optional
import uuid
import weaviate

class WeaviateVectorStore:
    """
    VectorStore para VisualAgent sobre Weaviate con vectorizer='none'.
    Implementa:
      - index(vectors, payloads)
      - query(vector, k)
    """
    def __init__(
        self,
        url: str,
        api_key: str = "",
        class_name: str = "FashionItem",
        text_props: Optional[List[str]] = None,
        consistency_level: Optional[str] = None,
    ):
        auth = weaviate.AuthApiKey(api_key=api_key) if api_key else None
        self.client = weaviate.Client(url=url, auth_client_secret=auth)
        self.class_name = class_name
        self.text_props = text_props or ["filepath", "title", "brand", "color", "source", "url"]
        self.consistency_level = consistency_level

    # ------- Schema helpers -------
    def ensure_schema(self):
        schema = self.client.schema.get()
        classes = {c["class"] for c in (schema.get("classes") or [])}
        if self.class_name in classes:
            return
        self.client.schema.create_class({
            "class": self.class_name,
            "vectorizer": "none",
            "properties": [
                {"name": "filepath", "dataType": ["text"]},
                {"name": "title",    "dataType": ["text"]},
                {"name": "brand",    "dataType": ["text"]},
                {"name": "color",    "dataType": ["text"]},
                {"name": "source",   "dataType": ["text"]},
                {"name": "url",      "dataType": ["text"]},
            ],
        })

    def drop_class(self):
        try:
            self.client.schema.delete_class(self.class_name)
        except Exception:
            pass

    # ------- VisualAgent API -------
    def index(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> None:
        assert len(vectors) == len(payloads), "vectors y payloads deben tener igual longitud"
        with self.client.batch as batch:
            # batch.batch_size = 128  # opcional
            for v, p in zip(vectors, payloads):
                props = {
                    "filepath": p.get("filepath"),
                    "title":    p.get("title"),
                    "brand":    p.get("brand"),
                    "color":    p.get("color"),
                    "source":   p.get("source"),
                    "url":      p.get("url"),
                }
                batch.add_data_object(
                    data_object=props,
                    class_name=self.class_name,
                    uuid=uuid.uuid4(),
                    vector=v,
                    consistency_level=self.consistency_level,
                )

    def query(self, vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
        q = (
            self.client.query
            .get(self.class_name, self.text_props)
            .with_near_vector({"vector": vector})
            .with_additional(["distance"])
            .with_limit(k)
        )
        if self.consistency_level:
            q = q.with_consistency_level(self.consistency_level)
        res = q.do()
        data = res.get("data", {}).get("Get", {}).get(self.class_name, []) or []
        items = []
        for d in data:
            dist = (d.get("_additional") or {}).get("distance")
            score = None
            if isinstance(dist, (int, float)):
                # aproximación: similitud ≈ 1 - distancia (si métrica cosine)
                score = max(0.0, 1.0 - float(dist))
            item = {"score": score}
            for prop in self.text_props:
                item[prop] = d.get(prop)
            items.append(item)
        return items
