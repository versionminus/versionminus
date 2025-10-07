from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    model: str
    input: list[str] | str
    collection: Optional[str] = None  # default to 'notes' if not provided
    upsert: bool = True               # if false, only generate and return vectors
    # Optional metadata for insertion
    note_ids: Optional[List[str]] = Field(default=None, description="Parallel list of note ids (len must match inputs if provided)")
    user_ids: Optional[List[str]] = Field(default=None, description="Parallel list of user ids (len must match inputs if provided)")
    statuses: Optional[List[str]] = Field(default=None, description="Parallel list of statuses (len must match inputs if provided)")
    metadatas: Optional[List[str]] = Field(default=None, description="Parallel list of JSON metadata strings (len must match inputs if provided)")


class SearchRequest(BaseModel):
    collection: Optional[str] = None
    query: str
    top_k: int = 5
    metric_type: str = Field(default="L2", pattern="^(L2|IP|COSINE)$")
    # Optionally allow raw embedding vector for advanced clients
    vector: Optional[List[float]] = None


class HealthResponse(BaseModel):
    collections: List[str]
    ready: bool
    default_collection_present: bool
