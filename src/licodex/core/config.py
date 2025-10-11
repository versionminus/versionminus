from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, SecretStr
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # API
    app_name: str = Field(
        default="licodex",
        validation_alias=AliasChoices("APP_NAME"),
    )
    environment: str = Field(default="dev", validation_alias=AliasChoices("ENVIRONMENT", "ENV"))
    log_level: str = Field(default="INFO")
    api_prefix: str = "/api/v1"
    enable_cors: bool = True
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # Database components (primary source of truth)
    db_user: str = Field(default="licodex", validation_alias=AliasChoices("DB_USER", "POSTGRES_USER"))
    db_password: str = Field(default="licodexpwd", validation_alias=AliasChoices("DB_PASSWORD", "POSTGRES_PASSWORD"))
    db_host: str = Field(default="db", validation_alias=AliasChoices("DB_HOST", "POSTGRES_HOST"))
    db_port: int = Field(default=5432, validation_alias=AliasChoices("DB_PORT", "POSTGRES_PORT"))
    db_name: str = Field(default="licodex", validation_alias=AliasChoices("DB_NAME", "POSTGRES_DB"))

    # Optional full URL override (if set this wins)
    database_url: Optional[str] = None  # expects async driver form if provided

    # External model / AI marketplace configuration
    # The API key intentionally has no default and should only come from the environment (.env)
    modelhub_api_key: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices("MODELHUB_API_KEY"),
        description="Secret API key for external AI marketplace provider",
    )
    modelhub_base_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("MODELHUB_BASE_URL"),
        description="Base URL for model provider / marketplace",
    )
    modelhub: Optional[str] = Field(
        default=None,
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
        default="licodex-milvus",
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
        default="src/licodex/prompts/retrieval_system.txt",
        validation_alias=AliasChoices("RETRIEVAL_SYSTEM_PROMPT_PATH"),
        description="Filesystem path to system prompt injected before user message when retrieval context exists."
    )

    # ------------------------------------------------------------------
    # Auth / OIDC (Auth0)
    # ------------------------------------------------------------------
    auth_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AUTH_ENABLED"),
        description="Enable OIDC bearer token verification (Auth0). When false, all routes are unauthenticated."
    )
    auth_testing_mode: bool = Field(
        default=False,
        validation_alias=AliasChoices("AUTH_TESTING_MODE"),
        description="If true, middleware will bypass token signature verification when missing and inject dummy claims for tests.")
    auth0_domain: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_DOMAIN"),
        description="Auth0 issuer or domain (full https URL like 'https://tenant.eu.auth0.com/' or bare domain)."
    )
    auth0_api_audience: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_API_AUDIENCE"),
        description="Expected audience value for access tokens (API Identifier configured under Auth0 APIs)."
    )
    auth0_client_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_APPLICATION_CLIENT_ID"),
        description="Auth0 application client ID (for future client credentials or introspection)."
    )
    auth0_client_secret: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH_APPLICATION_CLIENT_SECRET"),
        description="Auth0 application client secret (keep confidential)."
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
        if not self.auth0_domain:
            return None
        d = self.auth0_domain.strip()
        if d.startswith("http://"):
            d = d[len("http://"):]
        elif d.startswith("https://"):
            d = d[len("https://"):]
        d = d.rstrip('/')
        return f"https://{d}/"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Derived / convenience
    @property
    def effective_db_user(self) -> str:
        if self.database_url:
            # If user supplied full URL we attempt to parse pieces lazily
            try:
                from sqlalchemy.engine import url as sa_url
                return sa_url.make_url(self.database_url).username or self.db_user
            except Exception:
                return self.db_user
        return self.db_user

    @property
    def effective_db_password(self) -> str:
        if self.database_url:
            try:
                from sqlalchemy.engine import url as sa_url
                return sa_url.make_url(self.database_url).password or self.db_password
            except Exception:
                return self.db_password
        return self.db_password

    @property
    def effective_db_host(self) -> str:
        if self.database_url:
            try:
                from sqlalchemy.engine import url as sa_url
                return sa_url.make_url(self.database_url).host or self.db_host
            except Exception:
                return self.db_host
        return self.db_host

    @property
    def effective_db_port(self) -> int:
        if self.database_url:
            try:
                from sqlalchemy.engine import url as sa_url
                return sa_url.make_url(self.database_url).port or self.db_port
            except Exception:
                return self.db_port
        return self.db_port

    @property
    def effective_db_name(self) -> str:
        if self.database_url:
            try:
                from sqlalchemy.engine import url as sa_url
                return sa_url.make_url(self.database_url).database or self.db_name
            except Exception:
                return self.db_name
        return self.db_name

    def _build_base(self) -> str:
        return f"postgresql://{self.effective_db_user}:{self.effective_db_password}@{self.effective_db_host}:{self.effective_db_port}/{self.effective_db_name}"

    @property
    def database_url_sync(self) -> str:
        """Sync driver URL (used by Alembic)."""
        if self.database_url:
            # strip +asyncpg if present and coerce to psycopg driver unless user explicitly chose another
            base = self.database_url.replace("+asyncpg", "")
            if "+psycopg" not in base and "+psycopg2" not in base:
                base = base.replace("postgresql://", "postgresql+psycopg://", 1)
            return base
        # Prefer psycopg (v3) driver; SQLAlchemy maps 'postgresql+psycopg'
        base = self._build_base()
        if "+" not in base:
            return base.replace("postgresql://", "postgresql+psycopg://", 1)
        return base

    @property
    def database_url_async(self) -> str:
        """Async driver URL (used by SQLAlchemy async engine)."""
        if self.database_url:
            return self.database_url
        return self._build_base().replace("postgresql://", "postgresql+asyncpg://", 1)

    def as_postgres_env_exports(self) -> str:
        """Produce shell export lines for Postgres official image from current settings."""
        import shlex
        def q(v: str) -> str:
            return shlex.quote(str(v))
        lines = [
            f"export POSTGRES_USER={q(self.effective_db_user)}",
            f"export POSTGRES_PASSWORD={q(self.effective_db_password)}",
            f"export POSTGRES_DB={q(self.effective_db_name)}",
        ]
        return "\n".join(lines)

@lru_cache
def get_settings() -> Settings:
    return Settings()
