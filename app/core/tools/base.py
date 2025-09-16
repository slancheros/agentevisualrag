from typing import Protocol, List, Dict, Any

"""Definiciones de protocolos para las herramientas del agente visual."""   

class EmbedderTool(Protocol):
    """Herramienta para incrustar imágenes."""
    def embed_image(self, image_path: str) -> List[float]: ...

class DatasetTool(Protocol):
    """Herramienta para interactuar con el conjunto de datos."""
    def sample_paths(self, limit: int = 200) -> List[str]: ...
    def get_metadata(self, filepath: str) -> Dict[str, Any]: ...

class VectorStoreTool(Protocol):
    """Herramienta para almacenar y recuperar vectores."""
    def index(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> None: ...
    def query(self, vector: List[float], k: int = 10) -> List[Dict[str, Any]]: ...

class EnricherTool(Protocol):
    """Herramienta para enriquecer los resultados de la recuperación visual."""
    def enrich(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...
