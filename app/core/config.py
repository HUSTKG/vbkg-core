import os
import secrets
from typing import List, Union, Optional, Dict, Any
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge Graph System"
    PROJECT_DESCRIPTION: str = "A system for managing and querying knowledge graphs."
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS settings
    CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = [] 
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Neo4j
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-southeast-1"
    S3_BUCKET_NAME: str = "knowledge-graph-files"
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_COMPLETION_MODEL: str = "gpt-4-turbo"  # or gpt-3.5-turbo
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"  # or text-embedding-3-small, text-embedding-3-large
    
    # Fallback model settings
    SPACY_MODEL: str = "xx_ent_wiki_sm"
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    
    class Config:
        env_file = ".env"
        from_attributes = True 

settings = Settings()
