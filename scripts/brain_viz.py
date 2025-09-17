# scripts/brain_viz.py
import os
import numpy as np
import fiftyone as fo
import fiftyone.brain as fob

DS_NAME   = os.getenv("FO_DATASET_NAME", "fashion_demo")
EMB_FIELD = os.getenv("FO_EMB_FIELD", "clip_embedding")
CLIP_MODEL = os.getenv("FO_CLIP_MODEL", "clip-vit-base32-torch")  # usado por FO Brain

ds = fo.load_dataset(DS_NAME)
schema = ds.get_field_schema()
print("[brain_viz] Campos del dataset:", list(schema.keys()))

def ensure_embeddings(ds: fo.Dataset, emb_field: str):
    if emb_field in ds.get_field_schema():
        # Verifica que haya valores (no None)
        some = ds.limit(5).values(emb_field)
        if any(v is not None for v in some):
            print(f"[brain_viz] Embeddings ya existen en '{emb_field}'")
            return

    # 1) Intento con FO Brain (calcula y guarda en emb_field)
    try:
        print(f"[brain_viz] Calculando embeddings con FO Brain -> {emb_field} (modelo={CLIP_MODEL})")
        # En algunas versiones no existe compute_embeddings; usar compute_similarity con compute_embeddings=True
        if getattr(fob, "compute_embeddings", None):
            fob.compute_embeddings(ds, embeddings_field=emb_field, model=CLIP_MODEL)
        else:
            fob.compute_similarity(
                ds,
                brain_key="tmp_clip_sim",
                model=CLIP_MODEL,
                embeddings_field=emb_field,
                compute_embeddings=True,
            )
        ds.save()
        print(f"[brain_viz] Listo: embeddings guardados en '{emb_field}'")
        return
    except Exception as e:
        print("[brain_viz] FO Brain falló o no disponible:", e)

    # 2) Intento con OpenCLIP (requiere instalación de open-clip-torch)
    try:
        print("[brain_viz] Intentandodocke con OpenCLIP (CLIPEmbedder)")
        from app.core.tools.clip_embedder import CLIPEmbedder
        embedder = CLIPEmbedder(model_name="ViT-B-32", pretrained="openai")
        # Crea el campo si no existe
        if emb_field not in ds.get_field_schema():
            ds.add_sample_field(emb_field, fo.VectorField)
        # Rellena
        for s in ds:
            vec = embedder.embed_image(s.filepath)
            setattr(s, emb_field, vec)
            s.save()
        print(f"[brain_viz] Listo: embeddings guardados en '{emb_field}'")
    except Exception as e:
        raise RuntimeError(f"[brain_viz] No pude generar embeddings por ningún camino: {e}")

# Asegura embeddings
ensure_embeddings(ds, EMB_FIELD)

# Trabaja con sólo los que tienen embeddings
view = ds.exists(EMB_FIELD)
embs = view.values(EMB_FIELD)

# Asegura que sean list[list[float]]
embs = [np.asarray(e).ravel().astype(float).tolist() if e is not None else None for e in embs]
embs = [e for e in embs if e is not None]

# Visualización 2D
print("[brain_viz] compute_visualization (umap)")
fob.compute_visualization(
    view,
    embeddings=embs,            # ¡Usamos embeddings explícitos para evitar el bug de kwargs!
    method="umap",
    brain_key="clip_umap",
    seed=51,
)

# Similaridad (vecinos)
print("[brain_viz] compute_similarity (cosine)")
fob.compute_similarity(
    view,
    embeddings=embs,            # también explícitos
    brain_key="clip_sim",
    metric="cosine",
    k=12,
)

view.save()
print("[brain_viz] OK. brain_runs =", ds.list_brain_runs())
