# licodex: live coding exercise for a GenAI powered note-taking app

## about

This repository contains a live coding exercise for building a GenAI powered note-taking application called "licodex". The application allows users to create, manage, and search notes using natural language processing and AI capabilities.

## TODOs

- meaningful errors, e.g.: no user found on new note creation (`licodex.core.error`)
- verify that all router methods follow the pattern: schema -> router -> service -> repo -> model
- implement soft deletes in all models
- implement garbage collector for soft deleted items
- finish milvus setup: siphonn.utils -> licodex.core.config (get ConfigStore values)
- container for react
- nginx for CORS
- verify if we can remove licodex.core.milvus
- (embeddings router) verify different ordering of payload arrays: Silent misalignment of data. Always derive order from `coll.schema.fields`
- host model
- "return list of most similar vacancies"
- robustness and performance
- consider:
    - tested
    - deploy (EKS)
    - upgrade (docker pushes, kubectl)
    - maintain (microservices, monitoring, logging)
    - monitor
    - scale
    - ⚠️ host model
- retrieval
    - Return richer metadata (distance scores, highlight spans) to the chat layer.
    - Switch to cosine similarity if you normalize vectors—currently hard-coded L2.
    - nprobe fixed at 10; might need tuning or exposure as a parameter.
    - No pagination; strictly top_k.
    - search endpoint:
        - Deduplicate by logical note_id if chunks exist, returning best match plus snippet (can this replace my quotes?)
        - Support hybrid search (metadata + vector) in future.
    - Include timing metrics (embedding latency, search latency) for observability.
- chunk policy roadmap
    - add regression tests for each policy splitter variant
    - extend policy detector prompt with project-specific heuristics
- agentic behaviour
    - ⚠️ MCP
    - tool selection
- rename react components

# Contributing

## Devcontainer

```sh
docker network create licodex

# authn to ghcr (prerequisite: create gh token (classic) with read:packages and write:packages scopes)
echo GITHUB_TOKEN | docker login ghcr.io -u $USER --password-stdin

# Build devcontainer images
docker network create licodex # such that the containers can communicate
docker build -f .devcontainer/docker/Dockerfile.base -t ghcr.io/diogobaltazar/licodex-devcontainer-base:1.0.0 . # first setup only
docker build -f .devcontainer/docker/Dockerfile.tools -t ghcr.io/diogobaltazar/licodex-devcontainer-tools:1.0.0 . # first setup only
USRID=$(id -u) USRNAME=$(whoami) docker compose -f .devcontainer/compose.yml build --no-cache --pull=false
# attach to the devcontainer with vscode
```

## Local host

```sh
# system
sudo apt update && xargs -a .devcontainer/sys-requirements.txt sudo apt install -y --no-install-recommends && sudo apt clean

# solution dependencies
pip install -r .devcontainer/python-requirements.txt
cd src/licodex/sdk/ts && npm install && npm run build
cd ../../client/web && npm install && npm run build

# solution
docker compose build db milvus milvus-etcd milvus-minio api chunk-policy-mcp
docker compose up -d db milvus milvus-etcd milvus-minio chunk-policy-mcp
make up-api MODELHUB_API_KEY=paste MODELHUB_BASE_URL=paste MODELHUB=openai
cd src/licodex/client/web && npm run dev
```

### Debugging

Useful commands for debugging

```sh
docker exec licodex-db psql -U licodex -d licodex -c "select * from message"
docker exec licodex-db psql -U licodex -d licodex -c "select * from note"
docker exec licodex-db psql -U licodex -d licodex -c "select * from user"
docker exec licodex-db psql -U licodex -d licodex -c "select * from source"
docker exec licodex-db psql -U licodex -d licodex -c "select * from thread"
```

## Chunk policy detection & MCP integration

The embeddings pipeline can now decide chunk boundary strategies dynamically using a LangChain + LangGraph agent, a local CPU-friendly Hugging Face model, and an optional MCP tool server.

### Flow overview

1. Clients call `POST /api/v1/embeddings/` without `chunk_policy`.
2. The API runs `detect_chunk_policy`:
   - A LangGraph state machine prompts a local `llama-cpp` model (via LangChain) for a policy decision.
   - When the model signals `use_tool=true`, the agent invokes the MCP tool `detect_chunk_boundary_policy`.
3. The resolved policy feeds `chunk_text`, producing token-aware chunks (paragraph/sentence, code-preserving, headings, etc.).
4. Each vector carries metadata (`chunk_index`, `chunk_total`, `chunk_policy*`) so retrieval and chat responses can reason about source ordering.
5. API responses include `policies` summarising the decision source, reason, and (if applicable) MCP tool usage.

### Suggested local model (CPU only)

- Hugging Face: [`TheBloke/Mistral-7B-Instruct-v0.2-GGUF`](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
- Recommended quantization: `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (~4 GB RAM)
- Download manually and mount into the API/MCP containers, e.g. `./models/mistral-7b-instruct-q4_k_m.gguf`.
- Configure environment:

```sh
CHUNK_POLICY_DETECTION_ENABLED=true
CHUNK_POLICY_MODEL_PATH=/models/mistral-7b-instruct-q4_k_m.gguf
CHUNK_POLICY_MODEL_THREADS=8   # adjust to available cores
```

### MCP sidecar

The MCP server runs independently to keep the agent tool surface modular.

```sh
docker compose build chunk-policy-mcp
docker compose up -d chunk-policy-mcp

# point the API to the MCP endpoint
CHUNK_POLICY_MCP_ENABLED=true
CHUNK_POLICY_MCP_HOST=chunk-policy-mcp
CHUNK_POLICY_MCP_PORT=8080
```

When MCP is disabled, heuristics still provide reasonable defaults (code blocks → `code_blocks`, short notes → `minimal_words`, etc.). Extend `src/licodex/mcp/chunk_policy_server.py` to experiment with richer detectors or additional tools.
