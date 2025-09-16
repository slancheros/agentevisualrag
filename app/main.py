import os, json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.deps import agent_singleton
from app.models import RetrieveRequest, RetrieveResponse, EnrichedItemOut, AskRequest
from app.agent_runtime import build_agent

from fastapi import BackgroundTasks
from app.models import IndexRequest

load_dotenv()
app = FastAPI(title="Visual Agents API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: RetrieveRequest):
    try:
   
        agent_singleton.cfg.top_k = req.top_k
        agent_singleton.cfg.prefer_online = req.prefer_online

        resp = agent_singleton.retrieve(req.query_image)
        items = []
        for r in resp.results:
            if req.filter_color and (r.color or "").lower() != req.filter_color.lower():
                continue
            if req.max_price is not None and (r.price is None or r.price > req.max_price):
                continue
            items.append(EnrichedItemOut(**r.__dict__))
        items = items[:req.top_k]
        return RetrieveResponse(query_image=req.query_image, count=len(items), results=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask(req: AskRequest):
    """
    Endpoint conversacional . 
    """
    try:
        agent = build_agent()  
        result = agent.invoke({"input": req.prompt})
        return JSONResponse({"output": result["output"]})
    except Exception as e:

        raise HTTPException(status_code=500, detail=f"No se pudo ejecutar el agente. {e}")
    

@app.post("/admin/index")
def admin_index(req: IndexRequest, bg: BackgroundTasks):
    """
    Dispara el proceso de indexación:
      - opcionalmente borra/recrea el schema en Weaviate
      - recorre el dataset -> embed -> upsert batch en Weaviate
    Corre en background para no bloquear la request.
    """
    def _job():
        vstore = agent_singleton.vstore
        embedder = agent_singleton.embedder
        dataset = agent_singleton.dataset

        # 1) schema
        if req.rebuild_schema:
            try:
                vstore.drop_class()
            except Exception:
                pass
        vstore.ensure_schema()

        # 2) data
        paths = dataset.sample_paths(limit=req.limit)
        vectors = [embedder.embed_image(p) for p in paths]

        payloads = []
        for p in paths:
            md = dataset.get_metadata(p)
            payloads.append({
                "filepath": p,
                "title": md.get("title"),
                "brand": md.get("brand"),
                "color": md.get("color"),
                "source": md.get("source"),
                "url": md.get("url"),
            })

        # 3) upsert
        vstore.index(vectors, payloads)

    bg.add_task(_job)
    return {"status": "started", "message": "Indexación lanzada en background"}