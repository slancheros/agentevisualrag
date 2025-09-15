from typing import List, Dict, Any
import random

class MockEnricher:
    """
    Enriquecedor de precios/disponibilidad simulado.
    Cambiar por API real (REST/CSV).
    """
    def __init__(self, seed: int = 123):
        self.rnd = random.Random(seed)

    def enrich(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for it in items:
            price = round(self.rnd.uniform(15.0, 120.0), 2)
            source = it.get("source") or ("online" if self.rnd.random() > 0.5 else "store")
            it2 = {**it, "price": price, "currency": "EUR", "source": source, "url": it.get("url")}
            out.append(it2)
        return out
