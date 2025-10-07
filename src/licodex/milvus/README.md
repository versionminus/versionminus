# Collection

| Field                              | Purpose                                                                                 |
|------------------------------------|-----------------------------------------------------------------------------------------|
| id (INT64, auto)                   | Internal Milvus primary key (auto-generated)                                            |
| vector (FLOAT_VECTOR, dim 1536)    | The embedding itself                                                                    |
| note_id (VARCHAR 64)               | UUID of the note in your relational DB                                                  |
| user_id (VARCHAR 64)               | Owner of the note                                                                       |
| status (VARCHAR 20)                | Logical state of the note (e.g. AVAILABLE / DELETED / EMBEDDED)                         |
| metadata (VARCHAR 2048)            | Arbitrary JSON-ish string (you can pack title, timestamps, etc.)                        |

# Index

`IVF_FLAT` + `L2` metric. `IVF_FLAT` = inverted file with no compression (straightforward, fine for small–moderate scale). `L2` means Euclidean distance is used: closer == more similar.

TODOs for enhancement:

- IVF_FLAT + L2 has `nlist=128`, search param `nprobe=10`. Higher `nlist` (index build) + moderate `nprobe` (query) balances recall vs speed.
- For larger scale, the index may change to `IVF_SQ8` (compression) or `HNSW` (graph-based).
- If using `cosine` similarity, set metric_type: `COSINE` and (optionally) normalize vectors.

# Dimension

1536 matches OpenAI's `text-embedding-ada-002` model.