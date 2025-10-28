"""Initialization script to ensure Milvus 'notes' collection exists.

Rewritten to align with new single-collection strategy.
"""
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from versionminus.core.milvus.milvus import get_milvus  # centralized resilient connection
import json
from pathlib import Path

def ensure_notes_collection():
    """Ensure the 'notes' collection (and its index) exists.

    Preference order for definition:
      1. JSON config file at versionminus/milvus/collection/config/notes.json
      2. Fallback hard-coded schema + IVF_FLAT index
    """
    name = "notes"
    config_path = Path("/opt/versionminus/milvus/collection/config/notes.json")  # inside container

    # If collection missing, create it
    if name not in utility.list_collections():
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                fields_def = cfg.get("fields", [])
                field_schemas = []
                for fd in fields_def:
                    dtype = fd["type"].upper()
                    if dtype == "INT64":
                        field_schemas.append(FieldSchema(name=fd["name"], dtype=DataType.INT64, is_primary=fd.get("is_primary", False), auto_id=fd.get("auto_id", False)))
                    elif dtype == "FLOAT_VECTOR":
                        field_schemas.append(FieldSchema(name=fd["name"], dtype=DataType.FLOAT_VECTOR, dim=int(fd.get("dim", 1536))))
                    elif dtype == "VARCHAR":
                        field_schemas.append(FieldSchema(name=fd["name"], dtype=DataType.VARCHAR, max_length=int(fd.get("max_length", 64))))
                    else:
                        print(f"[milvus-init] WARNING unsupported dtype '{dtype}' in config; skipping field {fd.get('name')}")
                desc = cfg.get("description", "User notes embeddings (content + metadata)")
                schema = CollectionSchema(field_schemas, description=desc)
                Collection(name=name, schema=schema)
                print(f"[milvus-init] Created collection '{name}' from config")
            except Exception as e:  # pragma: no cover
                print(f"[milvus-init] ERROR reading config file {config_path}: {e}; using fallback schema")
        if name not in utility.list_collections():  # either config missing or failed
            schema = CollectionSchema(
                [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),
                    FieldSchema(name="note_id", dtype=DataType.VARCHAR, max_length=64),
                    FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
                    FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=20),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=2048),
                ],
                description="User notes embeddings (content + metadata)",
            )
            Collection(name=name, schema=schema)
            print(f"[milvus-init] Created collection '{name}' (fallback schema)")
    else:
        print(f"[milvus-init] Collection '{name}' already exists")

    # Ensure index exists (IVF_FLAT default)
    coll = Collection(name)
    # Detect existing vector field
    vector_fields = [f.name for f in coll.schema.fields if f.dtype == DataType.FLOAT_VECTOR]
    if vector_fields:
        vf = vector_fields[0]
        if not coll.indexes:
            # Try config-defined index first
            index_params = {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
            if config_path.exists():
                try:
                    cfg = json.loads(config_path.read_text(encoding="utf-8"))
                    if cfg.get("index"):
                        idx_cfg = cfg["index"]
                        index_params = {
                            "index_type": idx_cfg.get("index_type", "IVF_FLAT"),
                            "metric_type": idx_cfg.get("metric_type", "L2"),
                            "params": idx_cfg.get("params", {"nlist": 128}),
                        }
                except Exception as e:  # pragma: no cover
                    print(f"[milvus-init] WARNING failed reading index config: {e}; using defaults")
            print(f"[milvus-init] Creating index on '{name}.{vf}' -> {index_params}")
            coll.create_index(field_name=vf, index_params=index_params)
        else:
            print(f"[milvus-init] Index already present on collection '{name}'")
    else:
        print(f"[milvus-init] WARNING no vector field found in '{name}' schema; skipping index creation")


def main():
    try:
        get_milvus(host="localhost") # default host inside container
        print("[milvus-init] Milvus connection ready")
    except Exception as e:  # pragma: no cover
        print(f"[milvus-init] ERROR Milvus not ready: {e}")
        return

    # Diagnostics after confirmed connection
    try:
        active = connections.list_connections()  # type: ignore[attr-defined]
        print(f"[milvus-init] Active connections: {active}")
    except Exception as e:  # pragma: no cover
        print(f"[milvus-init] WARNING unable to list connections: {e}")

    ensure_notes_collection()
    print("[milvus-init] Existing collections:", utility.list_collections())

if __name__ == "__main__":
    main()