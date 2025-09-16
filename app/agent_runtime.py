import json
from dataclasses import asdict
from typing import Optional
from pydantic import BaseModel, Field
from app.deps import agent_singleton
import os

DEFAULT_QUERY_IMAGE = os.getenv("DEFAULT_QUERY_IMAGE", "data/images/SYNTH/img_0001.jpg")

try:
    from langchain.tools import StructuredTool
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI
except Exception as e:
    StructuredTool = None
    initialize_agent = None
    ChatOpenAI = None

class VisualRetrieveInput(BaseModel):
    query_image: Optional[str] = Field(None, description="Ruta a la imagen de consulta")
    top_k: int = Field(10, ge=1, le=30)
    prefer_online: bool = True
    filter_color: Optional[str] = None
    max_price: Optional[float] = Field(None, ge=0)

def visual_agent_tool_fn(query_image: str, top_k: int = 10, prefer_online: bool = True,
                         filter_color: Optional[str] = None, max_price: Optional[float] = None) -> str:
    query_image = query_image or DEFAULT_QUERY_IMAGE
    agent = agent_singleton
    agent.cfg.top_k = top_k
    agent.cfg.prefer_online = prefer_online
    resp = agent.retrieve(query_image)
    items = [asdict(r) for r in resp.results]
    if filter_color:
        items = [x for x in items if (x.get("color") or "").lower() == filter_color.lower()]
    if max_price is not None:
        items = [x for x in items if x.get("price") is not None and x["price"] <= max_price]
    items = items[:top_k]
    return json.dumps({"query_image": query_image, "count": len(items), "results": items}, ensure_ascii=False)

def build_agent():
    if StructuredTool is None:
        raise RuntimeError("Instala extras: pip install -r requirements-agent.txt")
    tool = StructuredTool.from_function(
        name="visual_retrieve",
        description="Busca prendas similares a una imagen y devuelve JSON. Soporta filtros color y precio.",
        func=visual_agent_tool_fn,
        args_schema=VisualRetrieveInput,
        return_direct=False,
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  
    agent = initialize_agent(
        tools=[tool],
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,
        handle_parsing_errors=True,
    )
    return agent
