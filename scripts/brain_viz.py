# scripts/brain_viz.py
import fiftyone as fo
import fiftyone.brain as fob

DS_NAME   = "fashion_demo"
EMB_FIELD = "clip_embedding"   

ds = fo.load_dataset(DS_NAME)


view = ds.exists(EMB_FIELD)

embs = view.values(EMB_FIELD)


fob.compute_visualization(
    view,
    embeddings=embs,
    method="umap",         # o "tsne"
    brain_key="clip_umap",
    seed=51,
)

# 4) Índice de similitud (opcional) usando también `embeddings=`
fob.compute_similarity(
    view,
    embeddings=embs,
    brain_key="clip_sim",
    metric="cosine",
    k=12,
)

view.save()  # persiste en el dataset
print("Brain runs:", ds.list_brain_runs())
