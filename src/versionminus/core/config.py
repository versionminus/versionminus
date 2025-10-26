from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, SecretStr, model_validator
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # API
    app_name: str = Field(
        default="versionminus",
        validation_alias=AliasChoices("APP_NAME"),
    )
    environment: str = Field(default="local", validation_alias=AliasChoices("DEPLOYMENT_ENV"))
    api_prefix: str = Field(default="/api/v1", validation_alias=AliasChoices("API_PREFIX"))
    enable_cors: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_CORS"))
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL"))

    # Database components (primary source of truth)
    db_user: str = Field(default="versionminus", validation_alias=AliasChoices("POSTGRES_USER"))
    db_password: str = Field(default="versionminuspwd", validation_alias=AliasChoices("POSTGRES_PASSWORD"))
    db_host: str = Field(default="db", validation_alias=AliasChoices("POSTGRES_HOST"))
    db_port: int = Field(default=5432, validation_alias=AliasChoices("POSTGRES_PORT"))
    db_name: str = Field(default="versionminus", validation_alias=AliasChoices("POSTGRES_DB"))
    database_url: Optional[str] = Field(default="postgresql+asyncpg://versionminus:versionminuspwd@db:5432/versionminus", validation_alias=AliasChoices("DATABASE_URL"))

    # ⚠️ inject from runtime only (.env or runtime)
    modelhub_api_key: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY"),
        description="Secret API key for external AI provider",
    )
    # include all base_urls
    modelhub_base_url: Optional[str] = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("MODELHUB_BASE_URL"),
        description="Base URL for model provider / marketplace",
    )
    # include all modelhubs
    modelhub: Optional[str] = Field(
        default="openai",
        validation_alias=AliasChoices("MODELHUB"),
        description="Logical model provider identifier",
    )
    # Default model names / identifiers
    chat_completion_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("CHAT_COMPLETION_MODEL"),
        description="Default model identifier used for chat completion endpoints when a model isn't explicitly supplied.",
    )

    # Milvus / Vector store + embeddings related configuration
    # Milvus connection (used by collection setup utilities and any runtime vector ops)
    milvus_host: Optional[str] = Field(
        default="versionminus-milvus",
        validation_alias=AliasChoices("MILVUS_HOST"),
        description="Milvus host (hostname or service name)."
    )
    milvus_http_port: Optional[int] = Field(
        default=19530,
        validation_alias=AliasChoices("MILVUS_PORT"),
        description="Milvus HTTP / gRPC port"
    )
    milvus_connect_timeout: float = Field(
        default=60.0,
        validation_alias=AliasChoices("MILVUS_CONNECT_TIMEOUT"),
        description="Maximum seconds to wait for initial Milvus connection before failing."
    )
    milvus_connect_interval: float = Field(
        default=2.0,
        validation_alias=AliasChoices("MILVUS_CONNECT_INTERVAL"),
        description="Seconds between retry attempts while establishing initial Milvus connection."
    )

    rag_embedding_model: Optional[str] = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("EMBEDDING_MODEL"),
        description="Embedding model name used for RAG / vector creation."
    )
    rag_embedding_model_output: Optional[int] = Field(
        default=1536,
        validation_alias=AliasChoices("EMBEDDING_MODEL_OUTPUT"),
        description="Expected embedding vector dimension for validation."
    )

    # Chunking / boundary detection configuration
    chunk_boundary_policy_default: str = Field(
        default="paragraph_sentence",
        validation_alias=AliasChoices("CHUNK_BOUNDARY_POLICY_DEFAULT"),
        description="Default chunk boundary policy when none is provided or detected."
    )
    chunk_overlap_tokens: int = Field(
        default=50,
        validation_alias=AliasChoices("CHUNK_OVERLAP_TOKENS"),
        description="Maximum overlap tokens injected between adjacent chunks."
    )
    chunk_target_tokens: int = Field(
        default=800,
        validation_alias=AliasChoices("CHUNK_TARGET_TOKENS"),
        description="Target token budget per chunk before overlap.")
    chunk_policy_detection_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("CHUNK_POLICY_DETECTION_ENABLED"),
        description="Enable LangChain/LangGraph powered chunk policy detection before embedding."
    )
    # ⚠️ the user is welcome to save models locally wherever it prefers, but a
    # default path is provided. Additionally, this same path has been added to
    # `.gigitgnore`. Should the user provide a different path, don't forget to
    # add it to `.gigitgnore`
    chunk_policy_model_path: Optional[str] = Field(
        default="models",
        validation_alias=AliasChoices("CHUNK_POLICY_MODEL_PATH"),
        description="Filesystem path to the GGUF model used for chunk policy detection (llama.cpp compatible)."
    )
    chunk_policy_model_ctx: int = Field(
        default=2048,
        validation_alias=AliasChoices("CHUNK_POLICY_MODEL_CTX"),
        description="Context window (tokens) for the local chunk policy model."
    )
    chunk_policy_model_threads: int = Field(
        default=16,
        validation_alias=AliasChoices("CHUNK_POLICY_MODEL_THREADS"),
        description="Number of CPU threads to allocate when running the chunk policy model."
    )
    chunk_policy_mcp_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("CHUNK_POLICY_MCP_ENABLED"),
        description="If true, the chunk policy detector will call an MCP server for tool execution."
    )
    chunk_policy_mcp_host: str = Field(
        default="versionminus-mcp",
        validation_alias=AliasChoices("CHUNK_POLICY_MCP_HOST"),
        description="Hostname of the MCP server exposing chunk policy tools."
    )
    chunk_policy_mcp_port: int = Field(
        default=8080,
        validation_alias=AliasChoices("CHUNK_POLICY_MCP_PORT"),
        description="Port of the MCP server exposing chunk policy tools."
    )
    chunk_policy_mcp_use_tls: bool = Field(
        default=False,
        validation_alias=AliasChoices("CHUNK_POLICY_MCP_USE_TLS"),
        description="Whether the MCP server connection requires TLS."
    )

    # Object storage / S3 for embeddings artifact persistence (optional)
    s3_embeddings_endpoint: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("S3_EMBEDDINGS_ENDPOINT"),
        description="Custom S3 endpoint (for MinIO/local)."
    )
    s3_embeddings_bucket_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("S3_EMBEDDINGS_BUCKET", "S3_EMBEDDINGS_BUCKET_NAME"),
        description="Target S3 bucket for embedding binary/object storage."
    )
    s3_embeddings_region: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("S3_EMBEDDINGS_REGION"),
        description="Region for S3 embeddings bucket (if required by provider)."
    )
    s3_embeddings_access_key_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("S3_EMBEDDINGS_ACCESS_KEY", "S3_EMBEDDINGS_ACCESS_KEY_ID"),
        description="Access key ID for S3 embeddings bucket."
    )
    s3_embeddings_secret_access_key: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices("S3_EMBEDDINGS_SECRET_KEY", "S3_EMBEDDINGS_SECRET_ACCESS_KEY"),
        description="Secret access key for S3 embeddings bucket."
    )
    s3_embeddings_force_path_style: bool = Field(
        default=False,
        validation_alias=AliasChoices("S3_EMBEDDINGS_FORCE_PATH_STYLE"),
        description="Force path-style addressing for S3 (true for many MinIO setups)."
    )

    # Generic embedding vector configuration (default dimension if unspecified)
    embedding_default_dim: int = Field(
        default=1536,
        validation_alias=AliasChoices("EMBEDDING_DEFAULT_DIM", "VECTOR_DIM", "EMBEDDINGS_DIM"),
        description="Default embedding vector dimension used when explicit collection config omits dim."
    )

    # Path to retrieval augmentation system prompt (can be overridden via env)
    retrieval_system_prompt_path: str = Field(
        default="src/versionminus/prompts/retrieval_system.txt",
        validation_alias=AliasChoices("RETRIEVAL_SYSTEM_PROMPT_PATH"),
        description="Filesystem path to system prompt injected before user message when retrieval context exists."
    )
    # ------------------------------------------------------------------
    # Auth / OIDC (Auth0)
    # ------------------------------------------------------------------
    # ⚠️ switch to True when running locally (.env or runtime)
    auth_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AUTH_ENABLED"),
        description="Enable OIDC bearer token verification (Auth0). When false, all routes are unauthenticated."
    )
    # ⚠️ switch to True when running locally (.env or runtime)
    auth0_domain: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_DOMAIN"),
        description="Auth0 issuer or domain (full https URL like 'https://{tenant}.eu.auth0.com/' or bare domain)."
    )
    auth0_api_audience: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_API_AUDIENCE"),
        description="Expected audience value for access tokens (API Identifier configured under Auth0 APIs)."
    )
    auth0_client_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_APPLICATION_CLIENT_ID"),
        description="Auth0 application client ID"
    )
    auth0_client_secret: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_APPLICATION_CLIENT_SECRET"),
        description="Auth0 application client secret (keep confidential)."
    )
    auth0_application_name: Optional[SecretStr] = Field(
        default="versionminus",
        validation_alias=AliasChoices("AUTH_APPLICATION_NAME"),
        description="Auth0 application name."
    )

    auth_algorithms: list[str] = Field(
        default=["RS256"],
        validation_alias=AliasChoices("AUTH_ALGORITHMS"),
        description="Allowed JWT signing algorithms."
    )
    auth_jwks_cache_ttl_seconds: int = Field(
        default=600,
        validation_alias=AliasChoices("AUTH_JWKS_CACHE_TTL", "AUTH_JWKS_CACHE_TTL_SECONDS"),
        description="JWKS cache TTL in seconds before refreshing from the Auth0 domain."
    )

    @property
    def auth0_issuer(self) -> Optional[str]:
        """Normalized issuer URL with trailing '/' regardless of input format."""
        raw = self.auth0_domain
        if not raw:
            return None
        # Be defensive: ensure we are handling a string-like value
        try:
            d = str(raw).strip()
        except Exception:
            return None
        if not d:
            return None
        # Remove any scheme if present
        if d.startswith("http://"):
            d = d[len("http://"):]
        elif d.startswith("https://"):
            d = d[len("https://"):]
        # Drop any path/query after the host if provided
        d = d.split("/", 1)[0]
        d = d.rstrip('/')
        return f"https://{d}/"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    def _build_base(self):
        """Compose a base PostgreSQL URL from individual components.

        Returns a plain sync URL without a driver suffix, e.g.
        postgresql://user:pass@host:port/db
        """
        user = str(self.db_user)
        password = str(self.db_password)
        host = str(self.db_host)
        port = int(self.db_port)
        name = str(self.db_name)

        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    @property
    def database_url_sync(self):
        """Sync driver URL (used by Alembic)."""
        if isinstance(self.database_url, str) and self.database_url.strip():
            # strip +asyncpg if present and coerce to psycopg driver unless user explicitly chose another
            base = self.database_url.strip().replace("+asyncpg", "")
            if "+psycopg" not in base and "+psycopg2" not in base:
                base = base.replace("postgresql://", "postgresql+psycopg://", 1)
            return base
        # Prefer psycopg (v3) driver; SQLAlchemy maps 'postgresql+psycopg'
        base = self._build_base()
        if "+" not in base:
            return base.replace("postgresql://", "postgresql+psycopg://", 1)
        return base

    @property
    def database_url_async(self):
        """Async driver URL (used by SQLAlchemy async engine)."""
        if isinstance(self.database_url, str) and self.database_url.strip():
            return self.database_url.strip()
        return self._build_base().replace("postgresql://", "postgresql+asyncpg://", 1)

@lru_cache
def get_settings():
    return Settings()
