# app/core/tools/enricher.py
from typing import Dict, Any, List, Tuple
from PIL import Image
from collections import Counter
import os, re, hashlib, math

BASIC_COLORS = [
    "black","white","gray","red","green","blue","yellow","purple","orange","brown","pink","beige","navy"
]

def _nearest_basic_color(rgb: Tuple[int,int,int]) -> str:
    # distancia euclidiana a una paleta simple
    palette = {
        "black": (0,0,0), "white": (255,255,255), "gray": (128,128,128),
        "red": (200,30,30), "green": (30,160,60), "blue": (40,80,200),
        "yellow": (230,220,30), "purple": (140,60,160), "orange": (240,140,20),
        "brown": (120,80,40), "pink": (240,160,200), "beige": (220,210,180), "navy": (20,40,100)
    }
    def dist(a,b): return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))
    name, _ = min(palette.items(), key=lambda kv: dist(rgb, kv[1]))
    return name

def _dominant_color(path: str) -> str:
    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((64,64))
        pixels = list(img.getdata())
        # mayor frecuencia
        common = Counter(pixels).most_common(1)[0][0]
        return _nearest_basic_color(common)
    except Exception:
        return None

def _guess_brand_from_path(path: str) -> str:
    # heurística: carpeta o prefijo en el filename
    fname = os.path.basename(path).lower()
    folders = os.path.dirname(path).split(os.sep)
    # busca un token que parezca marca
    pats = [r"(zara|h&m|hm|mango|uniqlo|gap|bershka|pullbear|nike|adidas|levi)"]
    for p in pats:
        m = re.search(p, fname)
        if m: return m.group(1).upper()
    for seg in folders:
        m = re.search(pats[0], seg.lower())
        if m: return m.group(1).upper()
    return None

def _deterministic_price(path: str, min_p=15, max_p=120) -> float:
    h = hashlib.sha256(path.encode("utf-8")).hexdigest()
    x = int(h[:8], 16) / 0xFFFFFFFF
    return round(min_p + x * (max_p - min_p), 2)

class SimpleEnricher:
    """
    Enriquecedor sin dependencias externas:
      - color dominante (PIL)
      - brand por heurística de path
      - precio determinista
      - url sintética
    """
    def __init__(self, base_url: str = "https://shop.example/item"):
        self.base_url = base_url

    def enrich_batch(self, payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for p in payloads:
            fp = p.get("filepath")
            md = {**p}
            md.setdefault("brand", _guess_brand_from_path(fp))
            md.setdefault("color", _dominant_color(fp))
            md.setdefault("price", _deterministic_price(fp))
            md.setdefault("source", "online")
            md.setdefault("url", f"{self.base_url}?q={hashlib.md5(fp.encode()).hexdigest()[:10]}")
            out.append(md)
        return out
