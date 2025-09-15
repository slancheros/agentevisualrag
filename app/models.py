from pydantic import BaseModel, Field
from typing import Optional, List

class RetrieveRequest(BaseModel):
    query_image: str = Field(..., description="Ruta o identificador de la imagen de consulta")
    top_k: int = Field(10, ge=1, le=30)
    prefer_online: bool = True
    filter_color: Optional[str] = None
    max_price: Optional[float] = Field(None, ge=0)

class EnrichedItemOut(BaseModel):
    id: str
    filepath: str
    similarity: float
    title: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    source: Optional[str] = None
    url: Optional[str] = None

class RetrieveResponse(BaseModel):
    query_image: str
    count: int
    results: List[EnrichedItemOut]

class AskRequest(BaseModel):
    prompt: str
