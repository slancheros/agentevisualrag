# app/indexer.py
import os, uuid
import fiftyone as fo
import fiftyone.zoo as foz
import fiftyone.brain as fob
import weaviate

DATASET_NAME = os.getenv("FO_DATASET_NAME", "fashion_demo")
USE_EXISTING  = os.getenv("FO_USE_EXISTING", "false").lower() == "true"
ZOO_DATASET   = os.getenv("FO_ZOO_DATASET", "fashion-mnist")
ZOO_SPLIT     = os.getenv("FO_ZOO_SPLIT", "test")
MAX_SAMPLES   = int(os.getenv("FO_MAX_SAMPLES", "1000"))

EMB_FIELD     = os.getenv("FO_EMB_FIELD", "clip_embedding")
CLIP_MODEL    = os.getenv("FO_CLIP_MODEL", "clip-vit-base32-torch")

WEAVIATE_URL  = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
WVT_CLASS     = os.getenv("WVT_CLASS", "FashionItem")
BATCH_SIZE    = int(os.getenv("BATCH_SIZE", "128"))

def ensure_schema(client: weaviate.Client, class_name: str):
    existing = {c["class"] for c in (client.schema.get().get("classes") or [])}
    if class_name in existing:
        print(f"[Indexer] Clase ya existe: {class_name}")
        return
    client.schema.create_class({
        "class": class_name,
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
    print(f"[Indexer] Clase creada: {class_name}")

def load_dataset() -> fo.Dataset:
    if USE_EXISTING:
        print(f"[Indexer] Cargando dataset existente: {DATASET_NAME}")
        return fo.load_dataset(DATASET_NAME)
    print(f"[Indexer] Zoo -> {ZOO_DATASET} (split={ZOO_SPLIT}, max={MAX_SAMPLES})")
    ds = foz.load_zoo_dataset(
        ZOO_DATASET, split=ZOO_SPLIT, max_samples=MAX_SAMPLES, dataset_name=DATASET_NAME
    )
    print(f"[Indexer] Dataset listo: {ds.name} ({len(ds)} muestras)")
    return ds

def compute_embeddings(ds: fo.Dataset):
    need = EMB_FIELD not in ds.get_field_schema().keys()
    if not need:
        for s in ds.take(5):
            if s.get(EMB_FIELD, None) is None:
                need = True
                break

    if not need:
        print(f"[Indexer] Usando embeddings existentes en '{EMB_FIELD}'")
        return

    print(f"[Indexer] Calculando embeddings vía FiftyOne Brain (modelo={CLIP_MODEL})")
    # En algunas versiones no existe fob.compute_embeddings; usa compute_similarity con compute_embeddings=True
    import fiftyone.brain as fob
    try:
        # Camino nuevo (si existiera en tu versión, lo intentamos primero)
        compute_embeddings = getattr(fob, "compute_embeddings", None)
        if compute_embeddings is not None:
            compute_embeddings(
                ds,
                embeddings_field=EMB_FIELD,
                model=CLIP_MODEL,
                # device="cpu"  # o "cuda"
            )
        else:
     
            fob.compute_similarity(
                ds,
                brain_key="clip_sim_tmp",
                model=CLIP_MODEL,
                embeddings_field=EMB_FIELD,
                compute_embeddings=True,
                # device="cpu"  # o "cuda"
            )
        ds.save()
        print(f"[Indexer] Embeddings listos en '{EMB_FIELD}'")
    except Exception as e:
        raise RuntimeError(f"No se pudieron calcular embeddings con FiftyOne Brain: {e}")


def upsert(ds: fo.Dataset, client: weaviate.Client):
    ensure_schema(client, WVT_CLASS)
    total, pushed = len(ds), 0

    import numpy as np

    with client.batch as batch:
        batch.batch_size = BATCH_SIZE
        for s in ds:
            # ----- OBTENER EMBEDDING -----
            if not s.has_field(EMB_FIELD):
                continue
            vec = getattr(s, EMB_FIELD) 
            if vec is None:
                continue
            
            if not isinstance(vec, list):
                vec = np.asarray(vec).ravel().astype(float).tolist()
            if not vec:
                continue

            # ----- METADATOS -----
            props = {
                "filepath": s.filepath,
                "title": None,
                "brand": None,
                "color": None,
                "source": "online",
                "url": None,
            }
            if hasattr(s, "ground_truth") and hasattr(s.ground_truth, "label"):
                props["title"] = s.ground_truth.label

            if hasattr(s, "attributes") and isinstance(getattr(s, "attributes"), dict):
                props["color"] = s.attributes.get("color") or props["color"]

            # ----- UPSERT -----
            batch.add_data_object(
                data_object=props,
                class_name=WVT_CLASS,
                uuid=uuid.uuid4(),
                vector=vec,
            )
            pushed += 1

    print(f"[Indexer] Upsert a Weaviate completado. {pushed}/{total} objetos")


def main():
    print("[Indexer] Iniciando indexado REAL (FiftyOne + Weaviate)")
    ds = load_dataset()
    compute_embeddings(ds)
    auth = weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY) if WEAVIATE_API_KEY else None
    client = weaviate.Client(url=WEAVIATE_URL, auth_client_secret=auth)
    upsert(ds, client)
    print("[Indexer] DONE")

if __name__ == "__main__":
    main()
