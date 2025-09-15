from typing import List
from ..utils import deterministic_vector

class MockEmbedder:
    """
    Embedder determinista sin dependencias.
    Convierte la ruta de la imagen en un vector fijo (128d).
    A reemplazar luego por CLIP/OpenCLIP.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed_image(self, image_path: str) -> List[float]:
        return deterministic_vector(image_path, self.dim)
