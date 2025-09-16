
# app/core/utils.py
import math
import random
import hashlib
from typing import List

"""Funciones utilitarias para la recuperación visual."""    

def seed_from_text(text: str) -> int:
    """Genera una semilla entera a partir de un texto."""

    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def deterministic_vector(key: str, dim: int = 128) -> List[float]:
    """Genera un vector determinista a partir de una clave de texto."""
    rnd = random.Random(seed_from_text(key))
    v = [rnd.uniform(-1.0, 1.0) for _ in range(dim)]
    return normalize(v)

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Similitud coseno entre dos listas numéricas."""
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) or 1.0
    nb = math.sqrt(sum(y*y for y in b)) or 1.0
    return dot / (na * nb)

def normalize(v: List[float]) -> List[float]:
    """Normaliza un vector a longitud 1."""
    n = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x / n for x in v]
