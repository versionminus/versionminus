"""Collection setup utilities for Milvus (notes-focused).

This module loads JSON collection definition files stored under
`src/licodex/milvus/collection/config/` and ensures that each collection and
its corresponding index exist inside the Milvus instance. It is safe to run
multiple times (idempotent); only missing collections / indexes are created.

Current usage in this project is a single "notes" collection that stores
embeddings + minimal metadata for user notes. Additional collections can be
added simply by dropping new JSON definition files into the config directory
and re-running :func:`sync_collections`.

Definition JSON schema (example for the notes collection):
{
    "description": "User notes embeddings (content + metadata).",
    "fields": [
        {"name": "id", "type": "INT64", "is_primary": true, "auto_id": true},
        {"name": "vector", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "note_id", "type": "VARCHAR", "max_length": 64},
        {"name": "user_id", "type": "VARCHAR", "max_length": 64},
        {"name": "status", "type": "VARCHAR", "max_length": 20},
        {"name": "metadata", "type": "VARCHAR", "max_length": 2048}
    ],
    "index": {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
}

Collection name is inferred from the file stem (e.g. `notes.json` -> `notes`).

Environment configuration (resolved through legacy ``ConfigStore`` currently):
    - EMBEDDINGS_MILVUS_HOST      (defaults to 127.0.0.1 if unset)
    - EMBEDDINGS_MILVUS_HTTP_PORT (defaults to 19530)

Planned improvement: migrate away from the legacy ``siphonn`` ConfigStore to
use the unified `licodex.core.config.Settings` for host/port resolution. The
rest of the codebase (e.g. runtime embeddings scripts) already uses
`Settings`.

Usage (container startup or ad-hoc):
        from licodex.milvus.collection.setup import sync_collections
        sync_collections()

"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from pymilvus import (  # type: ignore
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
)

from licodex.core.config import get_settings

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"
SUPPORTED_VECTOR_TYPES = {"FLOAT_VECTOR"}

_TYPE_MAP = {
    "INT64": DataType.INT64,
    "FLOAT": DataType.FLOAT,
    "DOUBLE": DataType.DOUBLE,
    "VARCHAR": DataType.VARCHAR,
    "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
}


def _build_field(field_def: Dict[str, Any]) -> FieldSchema:
    name = field_def["name"]
    type_name = field_def["type"].upper()
    if type_name not in _TYPE_MAP:
        raise ValueError(f"Unsupported field type '{type_name}' for field '{name}'")
    dtype = _TYPE_MAP[type_name]

    params: Dict[str, Any] = {}
    if dtype == DataType.VARCHAR:
        max_length = field_def.get("max_length")
        if not max_length:
            raise ValueError(f"VARCHAR field '{name}' missing 'max_length'")
        params["max_length"] = int(max_length)
    if dtype == DataType.FLOAT_VECTOR:
        dim = field_def.get("dim")
        if not dim:
            raise ValueError(f"FLOAT_VECTOR field '{name}' missing 'dim'")
        params["dim"] = int(dim)

    is_primary = bool(field_def.get("is_primary", False))
    auto_id = bool(field_def.get("auto_id", False))
    description = field_def.get("description", "")

    return FieldSchema(
        name=name,
        dtype=dtype,
        description=description,
        is_primary=is_primary,
        auto_id=auto_id,
        **params,
    )


def _load_definitions() -> List[Path]:
    if not CONFIG_DIR.exists():
        logger.warning("Milvus collection config directory not found: %s", CONFIG_DIR)
        return []
    return sorted([p for p in CONFIG_DIR.glob("*.json") if p.is_file()])


def _ensure_connection():
    settings = get_settings()
    host = settings.milvus_host or "127.0.0.1"
    port = str(settings.milvus_http_port or 19530)
    alias = "default"
    if not connections.has_connection(alias):
        logger.info("Connecting to Milvus host=%s port=%s", host, port)
        connections.connect(alias=alias, host=host, port=port)


def _create_collection(name: str, definition: Dict[str, Any]):
    fields = definition.get("fields", [])
    if not fields:
        raise ValueError(f"Collection '{name}' definition has no fields")
    field_schemas = [_build_field(fd) for fd in fields]
    description = definition.get("description", "")
    schema = CollectionSchema(fields=field_schemas, description=description)
    logger.info("Creating Milvus collection '%s'", name)
    Collection(name=name, schema=schema)  # side-effect creation


def _create_index(coll: Collection, definition: Dict[str, Any]):
    index_def = definition.get("index")
    if not index_def:
        logger.info("No index definition for collection '%s'", coll.name)
        return
    # Heuristic: first FLOAT_VECTOR field becomes target
    vector_fields = [f.name for f in coll.schema.fields if f.dtype == DataType.FLOAT_VECTOR]
    if not vector_fields:
        logger.info("Collection '%s' has no FLOAT_VECTOR field for indexing", coll.name)
        return
    target_field = vector_fields[0]
    existing = coll.indexes
    if any(idx.field_name == target_field for idx in existing):
        logger.info("Index already exists on '%s' for field '%s'", coll.name, target_field)
        return
    params = index_def.get("params", {})
    index_type = index_def.get("index_type", "IVF_FLAT")
    metric_type = index_def.get("metric_type", "L2")
    logger.info("Creating index on collection '%s' field '%s' type=%s metric=%s params=%s", coll.name, target_field, index_type, metric_type, params)
    coll.create_index(
        field_name=target_field,
        index_params={
            "index_type": index_type,
            "metric_type": metric_type,
            "params": params,
        },
    )


def sync_collections() -> None:
    """Ensure all configured Milvus collections and indexes exist.

    Safe to call repeatedly. Logs each action. Any fatal error will raise to
    the caller so container startup can surface problems early.
    """
    _ensure_connection()
    for path in _load_definitions():
        name = path.stem
        try:
            with path.open("r", encoding="utf-8") as f:
                definition = json.load(f)
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Failed to load collection definition '%s': %s", path, e)
            continue
        if utility.has_collection(name):
            logger.info("Collection '%s' already exists", name)
            coll = Collection(name)
        else:
            _create_collection(name, definition)
            coll = Collection(name)
        _create_index(coll, definition)
        # Load into memory (warmup)
        try:
            coll.load()
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to load collection '%s' into memory: %s", name, e)

__all__ = ["sync_collections"]
