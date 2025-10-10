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
    - make it work:
        - what are the embeddings endpoints?
        - what are the chat endpoints?
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
