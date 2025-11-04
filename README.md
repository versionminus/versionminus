# versionminus

Welcome to `versionminus`. We're committed to assist you with becoming the best version of yourself by learning from your past behaviour and providing AI assisted decision making.

# Contributing

We're delighted that you decided to contribute to the project.

## about

```xml
<human-core-identity>
  <audience>
    A human software engineer new to the codebase who wants to become productive quickly and contribute a small, safe change within ~30–60 minutes.
  </audience>

  <constraints>
    <item>Frequent context switching; low spare cognitive bandwidth.</item>
    <item>Needs copy/paste runnable steps with sensible defaults.</item>
    <item>Prefers short, verifiable loops and clear pass/fail signals.</item>
    <item>Fast recovery from broken state without deep debugging.</item>
  </constraints>

  <goals>
    <goal>Run the full stack locally (API + DB + Milvus + Web + Observability).</goal>
    <goal>Understand the architecture and component responsibilities at a glance.</goal>
    <goal>Identify a good first task and where to implement it.</goal>
    <goal>Make a change, run checks/tests, verify locally, and open a PR.</goal>
    <goal>Know how to inspect logs, metrics, and traces to debug.</goal>
  </goals>

  <golden-paths>
    <fast-start>
      docker network create versionminus || true
      cp -n .env.example .env || true
      docker compose up -d milvus-etcd milvus-minio milvus db otel-collector prometheus tempo loki fluent-bit grafana
      docker compose up -d mcp api web
      echo API: http://versionminus-api:8000/health && echo Docs: http://versionminus-api:8000/docs && echo Web: http://localhost:5173 && echo Grafana: http://localhost:3000
    </fast-start>
    <api-only>
      docker network create versionminus || true
      cp -n .env.example .env || true
      docker compose up -d db
      make run
      # open http://versionminus-api:8000/docs
    </api-only>
  </golden-paths>

  <timeboxes>
    <t5>5m: copy .env, start DB + API, open /docs.</t5>
    <t15>15m: start web dev server, hit an endpoint, add a unit test.</t15>
    <t30>30–60m: implement tiny change (router/service), run lint/format/type/tests, open PR.</t30>
  </timeboxes>

  <reading-order>
    <step>Contributors Quickstart (copy/paste setup + run).</step>
    <step>Project Layout (map features to folders and layers).</step>
    <step>Common Workflows (build, run, test, lint, format, type-check).</step>
    <step>Environment (what variables matter and why).</step>
    <step>Troubleshooting (fast fixes for common issues).</step>
    <step>TODOs (pick a "good first task").</step>
  </reading-order>

  <contribution-checklist>
    <item>Fork or branch from dev; create a feature branch.</item>
    <item>Copy .env, fill required secrets (MODELHUB_*; optional AUTH_*).</item>
    <item>Start services via Docker; verify API at /docs and Web UI.</item>
    <item>Follow layering: schema → router → service → repo → model.</item>
    <item>Write tests (pytest). Keep changes small and focused.</item>
    <item>Quality gates: ruff (lint/format), mypy (types), pytest (unit/integration).</item>
    <item>Conventional Commits; open PR with clear scope and context.</item>
  </contribution-checklist>

  <reset-and-repair>
    <clean-api>docker compose down -v api || true && docker compose up -d api</clean-api>
    <clean-db>docker compose down -v db || true && docker compose up -d db</clean-db>
    <rebuild-api>make build-api && docker compose up -d api</rebuild-api>
    <logs>docker compose logs -f api</logs>
  </reset-and-repair>

  <state-audit>
    <containers>docker compose ps</containers>
    <health>curl -s -o /dev/null -w "%{http_code}\n" http://versionminus-api:8000/health</health>
    <db>docker exec versionminus-db psql -U versionminus -d versionminus -c "select 1"</db>
    <observability>open Grafana at http://localhost:3000 and check data sources</observability>
  </state-audit>

  <cheatsheet>
    <lint>make lint</lint>
    <format>make format</format>
    <types>make type</types>
    <tests>make ut && make it</tests>
    <smoke>make smoke-populate && make smoke-embed-populate</smoke>
    <pr>make pr title="feat: concise description"</pr>
  </cheatsheet>

  <first-tasks>
    <task>Verify an API router adheres to schema → router → service → repo → model, and add/adjust a unit test.</task>
    <task>Improve an error path to use versionminus.core.error with a clear message.</task>
    <task>Small React component rename or prop typing fix in web client.</task>
  </first-tasks>

  <conventions>
    <python>Ruff for lint/format; Mypy for typing; Pytest markers: unit, integration, smoke.</python>
    <errors>Prefer explicit domain errors (versionminus.core.error) with meaningful messages.</errors>
    <persistence>Favor soft deletes; consider GC for soft-deleted items.</persistence>
    <observability>Log JSON to stdout; traces/metrics via OTEL; inspect in Grafana/Loki/Tempo.</observability>
    <api>FastAPI; keep endpoints thin; business logic in services; repositories abstract IO.</api>
    <vectordb>Milvus for embeddings; align metadata and ordering with collection schema fields.</vectordb>
    <security>OIDC optional; respect CORS; never commit secrets; use .env.</security>
  </conventions>

  <success-criteria>
    <item>I can run the stack and see /docs and the Web UI.</item>
    <item>I can make a trivial change (e.g., small router/service fix) and verify it.</item>
    <item>I can add/execute a unit test and pass lint/format/type checks.</item>
    <item>I can open a PR that passes CI and is easy to review.</item>
  </success-criteria>
</human-core-identity>
```

## gh-pages

This repository serves a static site via GitHub Pages at `https://versionminus.com`.

Included files
- `index.html` – org‑style landing page (adds canonical and www→apex redirect).
- `404.html` – not‑found page.
- `CNAME` – contains `versionminus.com`.

Publish steps
1. Push site files to `gh-pahes`.
2. GitHub → Settings → Pages → Source: Deploy from a branch → `gh-pahes` / `(root)`.
3. Set Custom domain to `versionminus.com` and wait for TLS.
4. Enable `Enforce HTTPS`

DNS (GoDaddy)
- Apex `@` → A records: 185.199.108.153, .109.153, .110.153, .111.153
- `www` → CNAME: `versionminus.github.io`
- Remove URL forwarding and conflicting A/AAAA/CNAME records.

Verify
- `dig +short versionminus.com A` → four 185.199.* IPs
- `dig +short www.versionminus.com CNAME` → `versionminus.github.io.`
- Pages Settings shows `DNS check successful` and HTTPS enabled.

## GitHub setup

- Generate an npm automation token with publish rights for the `versionminus` package (Account → Access Tokens in npm).
- Ensure the token type is **Automation**; classic or publish tokens tied to 2FA will trigger `npm ERR! code EOTP` in the GitHub Actions workflow.
- In GitHub go to `Settings → Secrets and variables → Actions → New repository secret`, name it `NPM_TOKEN`, and paste the npm token value.
- The `Publish TypeScript SDK` workflow uses this secret to authenticate `npm publish` when `sdk-v*` tags (or manual dispatches) run.

## TLS/HTTPS (How it works)

High‑level flow

```
 Browser              DNS                 GitHub Pages              Let's Encrypt (CA)
   |                   |                           |                           |
   | 1) GET https://versionminus.com               |                           |
   |---------------------------------------------->|                           |
   |                   | 2) Resolve A/CNAME        |                           |
   |<------------------| (185.199.* / github.io)   |                           |
   |                   |                           | 3) Present certificate    |
   |                   |                           |<--------------------------|
   | 4) TLS handshake (verify cert + encrypt)      |                           |
   |<--------------------------------------------->|                           |
   | 5) Encrypted HTTP (serve your index.html)     |                           |
   |<--------------------------------------------->|                           |
```

Key points
- GitHub requests and auto‑renews a TLS cert for `versionminus.com` using `Let’s Encrypt` once DNS is correct.
- The cert proves your site’s identity and enables encrypted HTTPS.
- After issuance, enable `Enforce HTTPS` so all traffic is redirected to the secure URL.

Checklist to keep HTTPS healthy
- Keep `CNAME` file with `versionminus.com` in the repo root.
- Ensure A records for `@` point to GitHub Pages IPs and `www` CNAME points to `versionminus.github.io` (or your org/user).
- Avoid conflicting A/AAAA/CNAME or forwarding at the registrar.

## Contributors Quickstart

- Prerequisites
  - Docker and Docker Compose

- One‑time setup
  - Create the shared docker network: `docker network create versionminus`
  - Copy env: `cp .env.example .env` and set required values
    - `MODELHUB_API_KEY`, `MODELHUB_BASE_URL`, `MODELHUB`
    - `AUTH_*` variables

- Start core services (database, vector store, observability)
  - `docker compose up -d milvus-etcd milvus-minio milvus db otel-collector prometheus tempo loki fluent-bit grafana`

- Start API
  - `docker compose up -d mcp`
  - `docker compose up -d api`
  - Verify: `curl http://versionminus-api:8000/health` → `200 OK`
  - Docs: open `http://versionminus-api:8000/docs`

- Start Web UI (choose one)
  - Docker (static build): `docker compose up -d web` → `http://localhost:5173`
  - Dev server: `cd src/versionminus/client/web && npm install && npm run dev`

- First data smoke tests (optional)

## Auth0 configuration

### Inject email into access tokens

When `AUTH_ENABLED=true` the API auto‑provisions users from Auth0. The backend expects the Auth0 **access token** (not just the ID token) to carry an email address. Add an Auth0 Action so each issued access token includes the email claim:

1. In the Auth0 dashboard open `Actions → Library → Build Custom`.
2. Choose the **Post Login** trigger, name the action (e.g. `AttachEmailToAccessToken`), and create it.
3. Replace the generated code with:

   ```js
   exports.onExecutePostLogin = async (event, api) => {
     const email = event.user?.email;
     if (!email) return;

     api.accessToken.setCustomClaim('https://versionminus.com/email', email);
     api.accessToken.setCustomClaim('https://versionminus.com/email_verified', !!event.user?.email_verified);
     api.accessToken.setCustomClaim('email', email); // temporary compatibility with existing backend
   };
   ```

4. Click **Deploy**.
5. Go to `Actions → Triggers → post-login`, drag the new action into the flow between **Start** and **Complete**, and press **Apply**.
6. Sign out and back in. Inspect the network request for `/api/v1/users/me` — the bearer token should now contain `email` (and the namespaced claim). The backend will auto-provision the local user on the next request.

If you later move the backend to the namespaced claim, remove the temporary line that sets the top-level `email`.
  - Populate threads/messages: `make smoke-populate clean_before=1`
  - Populate embeddings: `make smoke-embed-populate`

## Project Layout

- API: `src/versionminus/api` (FastAPI app, Dockerfile)
- Domain models: `src/versionminus/models`
- Repositories: `src/versionminus/repositories`
- Services: `src/versionminus/services`
- Schemas: `src/versionminus/schemas`
- Vector DB (Milvus) assets: `src/versionminus/milvus`
- Observability: `src/versionminus/observability/{otel-collector,loki,tempo,prometheus}`
- SDKs: `src/versionminus/sdk/{python,ts}`
- Clients: `src/versionminus/client/{web,cli,chatgpt}`
- DB image + migrations: `src/versionminus/db` (alembic in `src/versionminus/alembic`)

## Common Workflows

- Run everything
  - `docker compose up -d` (ensure `docker network create versionminus` ran once)

- Rebuild images
  - All: `make build`
  - API only: `make build-api`
  - DB only: `make build-db`

- Local development (API hot‑reload)
  - Python deps: `pip install -r .devcontainer/python-requirements.txt`
  - App: `pip install -e .`
  - Run: `make run` → `http://versionminus-api:8000`

- Frontend development
  - SDK build: `cd src/versionminus/sdk/ts && npm install && npm run build`
  - Web: `cd src/versionminus/client/web && npm install && npm run dev`

- Quality gates
  - Lint: `make lint`
  - Format: `make format`
  - Types: `make type`
  - Tests: `pytest` or `make ut` / `make it`

- Database
  - DB container runs migrations automatically on start
  - Connect: `docker exec -it versionminus-db psql -U versionminus -d versionminus`

- Observability
  - Grafana: `http://localhost:3000` (admin/admin)
  - Prometheus: `http://localhost:9090`
  - Loki: `http://localhost:3100`
  - Tempo: `http://localhost:3200`

## Environment

- Copy `.env.example` to `.env` and adjust
- Key variables
  - API: `API_PREFIX`, `LOG_LEVEL`, `ENABLE_CORS`
  - Database: `POSTGRES_*`, `DATABASE_URL`
  - Chunking/RAG: `CHUNK_*`
  - MCP: `CHUNK_POLICY_MCP_*`
  - Auth: `AUTH_*`

## Authentication

- Populate the `AUTH_*` entries in `.env` with your Auth0 tenant values (`AUTH_ENABLED`, `AUTH_DOMAIN`, `AUTH_API_AUDIENCE`, etc.) and restart the API to pick them up.
- Provide the SPA variables (`VITE_AUTH0_*`, `VITE_API_BASE`) to the React app so it can talk to Auth0 and the API.
- Step-by-step guidance for configuring Auth0, the SDK, and CLI access lives in `docs/auth0.md`.
- The web client now logs in with Auth0 automatically and feeds the access token to `useversionminus({ token })`. `GET /api/v1/users/me` returns the local user associated with the token.
- Scripts and curl callers can use the Auth0 client credentials flow; send requests with `Authorization: Bearer <token>`.

## Troubleshooting

- Network missing: `docker network create versionminus`
- Loki exits: restart with `docker compose up -d loki` (known local issue)
- Milvus not ready: ensure `milvus-etcd` and `milvus-minio` are healthy; then `docker compose up -d milvus`
- Ports busy: stop conflicting services or change published ports in `compose.yml`
- API cannot reach DB: confirm `.env` matches compose host `db` and port `5432`

## Contributing Workflow

- Branch from `main`
- Keep changes small and scoped
- Add or update tests under `tests`
- Run `make lint format type ut`
- Open PR with clear title: `make pr title="feat: concise description"`


`versionminus` allows users to create, manage, and search notes using natural language processing and AI capabilities.

## TODOs

- user
  - I want to access this application in ChatGPT
  - I want to be able to have ChatGPT prompting me for consent to access my notes
  - I will then be able to
    - lst my notes
    - edit my notes
    - delete my notes
    - create new notes
    - ask questions and relevant notes retrieved, if any, and answer taking into account the notes (listing the notes as references).
  - I will also be able to ask questions about the contents of the notes:
    - *"what notes did I take on my trip to Japan?"*
    - *"Did I ever write about Nabokov?"*
  - I want to be able to make meta questions about the notes:
    - *"what are the main topics I covered in my notes last week?"*
    - *"How many notes have I taken?"*
    - *"With what frequency?"*
    - *"What is the average length of my notes and the size in Kb?"*
    - *"What are the most common topics in my notes?"*
  - I want to be able to ask that actions be completed in the system
    - *"from this conversation generate a new note"* (push notification to `MFA`, then to app)
    - *"delete these notes"* (`MFA`)
    - *"signout"*
    - *"create a new note"* (`MFA`)
  - I want to be able to ask questions about the application:
    - *"how many notes can I create?"*
    - *"what is versionminus?"*
    - *"who built versionminus?"*
  -  I want to be able to ask questions about the system (will depend on my permissions):
    - *"what is the current load on the system?"*
    - *"how many users are currently online?"*
    - *"what is the backend of this solution?"*
    - *"block user"*
- authorisation
- expand to manage apple and google calendars (notes have tags like `nature in [chore, ...]`, `latest`, `earliest`, `delayed`, `criticality`, ...)
- expand to report on financial transactions (OpenBank) and detect patters of behaviour
- publish the SDK, docker compose build web should install the SDK, not copy it
- meaningful errors, e.g.: no user found on new note creation (`versionminus.core.error`)
- verify that all router methods follow the pattern: schema -> router -> service -> repo -> model
- implement soft deletes in all models
- implement garbage collector for soft deleted items
- finish milvus setup: siphonn.utils -> versionminus.core.config (get ConfigStore values)
- nginx for CORS
- verify if we can remove versionminus.core.milvus
- (embeddings router) verify different ordering of payload arrays: Silent misalignment of data. Always derive order from `coll.schema.fields`
- robustness and performance
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
    - MCP
    - tool selection
- rename react components

# Contributing

## docker compose

The solution is orchestrated by the following containers (the containers run locally in the docker network `versionminus` and remotely in the K8s network)

```sh
versionminus-web               # react client (see versionminus.sdk.ts)
versionminus-api               # REST API
versionminus-mcp               # MCP tools
versionminus-db                # postgres for context & user data (see versionminus.models)
versionminus-milvus            # embed: vector database
versionminus-milvus-minio      # embed: object storage
versionminus-milvus-etcd       # embed: metadata KV
versionminus-grafana           # obs: query, dashboard
versionminus-loki              # obs: logs
versionminus-fluent-bit        # obs: logs
versionminus-prometheus        # obs: metrics
versionminus-tempo             # obs: traces
versionminus-otel-collector    # obs: telemetry
```

- The `web` image build reads `DEPLOYMENT_ENV` (`dev`, `beta`, `rc`, `stable`) and installs `versionminus` from the matching npm dist-tag (`dev`, `beta`, `rc`, `latest`). Run each stack with its own compose project name, e.g. `DEPLOYMENT_ENV=dev docker compose -p versionminus-dev up --build web`, so every environment serves the SDK version published for that channel.

Flow diagram

```sh
versionminus-web
|
| HTTPS/REST + SDK
v
versionminus-api
|---> versionminus-db
|---> versionminus-milvus
|     |---> versionminus-milvus-minio
|     |---> versionminus-milvus-etcd
|
|---> versionminus-mcp
|
|---> versionminus-otel-collector
|      |----> versionminus-tempo
|      |----> versionminus-prometheus
|
| Logs (stdout JSON)
v
versionminus-fluent-bit
|
| push
|
v
versionminus-loki

versionminus-grafana
|---> versionminus-prometheus
|---> versionminus-loki
|---> versionminus-tempo
```

## Devcontainer

```sh
docker network create versionminus

# authn to ghcr (prerequisite: create gh token (classic) with read:packages and write:packages scopes)
echo GITHUB_TOKEN | docker login ghcr.io -u $USER --password-stdin

# Build devcontainer images
docker network create versionminus # such that the containers can communicate
docker build -f .devcontainer/docker/Dockerfile.base -t ghcr.io/versionminus/versionminus-devcontainer-base:1.0.0 . # first setup only
docker build -f .devcontainer/docker/Dockerfile.tools -t ghcr.io/versionminus/versionminus-devcontainer-tools:1.0.0 . # first setup only
USRID=$(id -u) USRNAME=$(whoami) docker compose -f .devcontainer/compose.yml build --no-cache --pull=false
# attach to the devcontainer with vscode
```

## localhost

```sh
# system dependencies
sudo apt update && xargs -a .devcontainer/sys-requirements.txt sudo apt install -y --no-install-recommends && sudo apt clean
```

```sh
# python dependencies
pip install -r .devcontainer/python-requirements.txt
```

```sh
# typescript dependencies
cd src/versionminus/sdk/ts && npm install
cd ../../client/web && npm install
cd ../../../..
```

```sh
# observability TODO loki shuts down
docker compose up -d loki tempo prometheus
```

```sh
# backend
docker compose build db milvus milvus-etcd milvus-minio api mcp
docker compose up -d db milvus milvus-etcd milvus-minio mcp

cp .env.example .env
# edit .env as needed (--force-recreate will apply changes to .env)
docker compose up -d --force-recreate api
```

```sh
# sdk
cd src/versionminus/sdk/ts && npm install && npm run build && cd # first time setup

# frontend
cd src/versionminus/client/web && npm install && npm run build && cd # first time setup
cd src/versionminus/client/web && npm run dev && cd
```
### Debugging

Useful commands for debugging

```sh
docker exec versionminus-db psql -U versionminus -d versionminus -c "select * from message"
docker exec versionminus-db psql -U versionminus -d versionminus -c "select * from note"
docker exec versionminus-db psql -U versionminus -d versionminus -c "select * from users"
docker exec versionminus-db psql -U versionminus -d versionminus -c "select * from source"
docker exec versionminus-db psql -U versionminus -d versionminus -c "select * from thread"
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
docker compose build mcp
docker compose up -d mcp

# point the API to the MCP endpoint
CHUNK_POLICY_MCP_ENABLED=true
CHUNK_POLICY_MCP_HOST=mcp
CHUNK_POLICY_MCP_PORT=8080
```

When MCP is disabled, heuristics still provide reasonable defaults (code blocks → `code_blocks`, short notes → `minimal_words`, etc.). Extend `src/versionminus/mcp/main.py` to experiment with richer detectors or additional tools.


```sh
# create vector store
curl https://api.openai.com/v1/vector_stores \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "name": "versionminus-notes"
  }'
VSID=vs_68f574d862dc8191842f22916d97a1c8

curl -s -X POST https://api.openai.com/v1/files \
-H "Authorization: Bearer $OPENAI_API_KEY" \
-H "OpenAI-Beta: assistants=v2" \
-F "purpose=assistants" \
-F "file=@README.md"
FID=file-R2aX3XmpRi1AXorNpp2CSa

curl -s -X POST https://api.openai.com/v1/vector_stores/$VSID/files \
-H "Authorization: Bearer $OPENAI_API_KEY" \
-H "Content-Type: application/json" \
-H "OpenAI-Beta: assistants=v2" \
-d '{"file_id":"file-R2aX3XmpRi1AXorNpp2CSa"}'

# expose MCP
ngrok config add-authtoken <paste>
ngrok http 8000
```

```sh
curl https://api.openai.com/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
  "model": "o4-mini-deep-research",
  "input": [
    {
      "role": "developer",
      "content": [
        {
          "type": "input_text",
          "text": "You are a research assistant that searches MCP servers to find answers to your questions."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "What is versionminus about?"
        }
      ]
    }
  ],
  "reasoning": {
    "summary": "auto"
  },
  "tools": [
    {
      "type": "mcp",
      "server_label": "cats",
      "server_url": "https://otilia-exergonic-janise.ngrok-free.dev/sse/",
      "allowed_tools": [
        "search",
        "fetch"
      ],
      "require_approval": "never"
    }
  ]
}'
```
