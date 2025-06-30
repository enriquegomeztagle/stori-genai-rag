from pydantic_settings import BaseSettings
from typing import Optional
import os
import json
import dotenv

dotenv.load_dotenv()


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "Stori GenAI RAG")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-west-2")

    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID")
    bedrock_max_tokens: int = 4096
    bedrock_temperature: float = 0.1

    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    embedding_model: str = os.getenv("EMBEDDING_MODEL")

    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    s3_bucket_name: Optional[str] = os.getenv("S3_BUCKET_NAME")
    s3_region: str = os.getenv("AWS_REGION", "us-west-2")

    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_retrieval: int = 5

    max_conversation_turns: int = 10
    content_filter_threshold: float = 0.8

    cors_origins: list = json.loads(
        os.getenv("CORS_ORIGINS", '["http://localhost:3000"]')
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
