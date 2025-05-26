import secrets
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge Graph System"

    PROJECT_DESCRIPTION: str = "A system for managing and querying knowledge graphs."
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS settings
    CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = []

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Supabase
    SUPABASE_URL: str = "https://your-supabase-url.supabase.co"
    SUPABASE_KEY: str = "your-supabase-key"
    ENCRYPTION_KEY: str = (
        "fe2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0"
    )

    # Neo4j
    NEO4J_URI: str = "bolt://0.0.0.0:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "123456789"

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "local"
    S3_BUCKET_NAME: str = "knowledge-graph-files"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Pipeline Configuration
    PIPELINE_MAX_EXECUTION_TIME: int = 3600
    PIPELINE_STEP_TIMEOUT: int = 300
    PIPELINE_MAX_RETRIES: int = 3

    # File Processing Configuration
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    SUPPORTED_FILE_TYPES: list = ["pdf", "docx", "txt", "csv", "json", "xml"]

    # Custom Python Code Configuration
    CUSTOM_PYTHON_TIMEOUT: int = 120
    CUSTOM_PYTHON_MAX_MEMORY: str = "512M"

    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_COMPLETION_MODEL: str = "gpt-4o-mini"  # or gpt-3.5-turbo
    OPENAI_EMBEDDING_MODEL: str = (
        "text-embedding-ada-002"  # or text-embedding-3-small, text-embedding-3-large
    )

    # Fallback model settings
    SPACY_MODEL: str = "xx_ent_wiki_sm"
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"

    FLOWER_UNAUTHENTICATED_API: str = "true"

    class Config:
        env_file = ".env"
        from_attributes = True


settings = Settings()
