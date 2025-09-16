# app/core/tools/clip_embedder.py
from typing import List, Optional
import torch
import open_clip
from PIL import Image

class CLIPEmbedder:
    """
    Encoder de imágenes -> vector unitario (OpenCLIP).
    """
    def __init__(
        self,
        model_name: str = "ViT-B-32",
        pretrained: str = "openai",
        device: Optional[str] = None,
        dtype: torch.dtype = torch.float32,
        normalize: bool = True,
    ):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=self.device
        )
        self.model.eval()
        self.dtype = dtype
        self.normalize = normalize

        # Detecta dimensión (una sola pasada)
        with torch.no_grad():
            dummy = torch.zeros(1, 3, 224, 224, dtype=self.dtype, device=self.device)
            out = self.model.encode_image(dummy)
            self._dim = int(out.shape[-1])

    @property
    def dim(self) -> int:
        return self._dim

    @torch.inference_mode()
    def embed_image(self, image_path: str) -> List[float]:
        img = Image.open(image_path).convert("RGB")
        pixel = self.preprocess(img).unsqueeze(0).to(self.device, dtype=self.dtype)
        feats = self.model.encode_image(pixel).squeeze(0)
        if self.normalize:
            feats = feats / (feats.norm(p=2) + 1e-12)
        return feats.detach().cpu().tolist()
