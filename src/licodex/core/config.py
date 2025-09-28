from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = Field(default="licodex-api", validation_alias=AliasChoices("APP_NAME", "LICODEX_APP_NAME"))
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
