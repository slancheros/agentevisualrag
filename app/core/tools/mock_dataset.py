import os
from typing import List, Dict, Any

class MockDataset:
    """
    Dataset mock. Si `root_dir` existe, toma archivos de imagen;
    si no, devuelve rutas sintéticas.
    """
    def __init__(self, root_dir: str = "data/images", synthetic_size: int = 200):
        self.root_dir = root_dir
        self.synthetic_size = synthetic_size

    def sample_paths(self, limit: int = 200) -> List[str]:
        paths: List[str] = []
        if os.path.isdir(self.root_dir):
            for name in os.listdir(self.root_dir):
                if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    paths.append(os.path.join(self.root_dir, name))
                    if len(paths) >= limit:
                        break
        if not paths:
            # genera rutas sintéticas
            limit = min(limit, self.synthetic_size)
            paths = [f"SYNTH/img_{i:04d}.jpg" for i in range(limit)]
        return paths

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        # Mapear por nombre (p. ej. "blazer", "shirt")
        # Aquí devolvemos metadatos mínimos simulados.
        base = os.path.basename(filepath)
        return {
            "title": f"Item {base}",
            "brand": "MockBrand",
            "color": "black" if "black" in filepath.lower() else "grey",
            "source": "online" if hash(filepath) % 2 == 0 else "store",
            "url": None,
        }
