"""Milvus + Embeddings integration layer.

This module centralizes any Milvus-related helpers plus an optional
EmbeddingsService abstraction used for storing / retrieving raw embedding
payloads from S3-compatible object storage.

The user indicated the EmbeddingsService may only be *optionally* required.
We provide a lightweight implementation here so other parts of the codebase
can import from `licodex.core.milvus` without depending on the historical
`siphonn.utils.service` package.

Environment / settings are driven exclusively by `licodex.core.config.Settings`.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import boto3
from botocore.config import Config as BotoConfig
from .config import get_settings


@dataclass
class EmbeddingsService:  # Minimal interface required by existing milvus scripts
    endpoint: Optional[str]
    bucket: str
    region: Optional[str]
    access_key: Optional[str]
    secret_key: Optional[str]
    force_path_style: bool = False

    def _client(self):  # lazy boto3 client
        session = boto3.session.Session()
        cfg = {}
        if self.region:
            cfg["region_name"] = self.region
        extra = {}
        if self.endpoint:
            extra["endpoint_url"] = self.endpoint
        if self.force_path_style:
            extra["config"] = BotoConfig(s3={"addressing_style": "path"})
        return session.client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            **cfg,
            **extra,
        )

    def put_embedding(self, key: str, data: bytes, content_type: str = "application/octet-stream"):
        self._client().put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def get_embedding(self, key: str) -> bytes:
        obj = self._client().get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()


def get_embeddings_service() -> Optional[EmbeddingsService]:
    settings = get_settings()
    if not settings.s3_embeddings_bucket_name:
        return None
    return EmbeddingsService(
        endpoint=settings.s3_embeddings_endpoint,
        bucket=settings.s3_embeddings_bucket_name,
        region=settings.s3_embeddings_region,
        access_key=settings.s3_embeddings_access_key_id,
        secret_key=settings.s3_embeddings_secret_access_key.get_secret_value() if settings.s3_embeddings_secret_access_key else None,
        force_path_style=settings.s3_embeddings_force_path_style,
    )


__all__ = [
    "EmbeddingsService",
    "get_embeddings_service",
]
