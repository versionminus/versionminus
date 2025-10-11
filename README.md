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
    - langchain/langgraph
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
docker compose build db milvus milvus-etcd milvus-minio api
docker compose up -d db milvus milvus-etcd milvus-minio
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