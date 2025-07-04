from fastapi import APIRouter
from app.api.endpoints import conversation, documents, health, metrics

api_router = APIRouter()

api_router.include_router(
    conversation.router, prefix="/conversation", tags=["conversation"]
)

api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

api_router.include_router(health.router, prefix="/health", tags=["health"])

api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
