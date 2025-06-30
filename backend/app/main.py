import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.router import api_router
from app.core.logging import logger
from app.services.bedrock_service import BedrockService
from app.services.vector_store import VectorStoreService
from app.services.memory_service import MemoryService
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.tools.agent_tools import get_agent_tools

sys.path.append("/app")

bedrock_service = None
vector_store_service = None
memory_service = None
document_service = None
rag_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bedrock_service, vector_store_service, memory_service, document_service, rag_service

    logger.info("Starting up Stori GenAI RAG application")

    try:
        bedrock_service = BedrockService()
        vector_store_service = VectorStoreService()
        memory_service = MemoryService()
        document_service = DocumentService()

        tools = get_agent_tools(memory_service, bedrock_service, vector_store_service)

        rag_service = RAGService(
            bedrock_service=bedrock_service,
            vector_store_service=vector_store_service,
            memory_service=memory_service,
            tools=tools,
        )

        stats = vector_store_service.get_collection_stats()
        if stats.get("total_documents", 0) == 0:
            logger.info("No documents found")

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error("Error during startup", error=str(e))
        raise

    yield

    logger.info("Shutting down Stori GenAI RAG application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Stori GenAI RAG Challenge - Conversational Agent for Mexican Revolution",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_endpoint():
    return {"status": "ok", "message": "Service is running"}


@app.get("/health")
async def health_root():
    return {"status": "ok", "message": "Service is running"}


@app.get("/")
async def root():
    return {
        "message": "Welcome to Stori GenAI RAG Challenge",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(status_code=204, content=None)


@app.get("/apple-touch-icon.png")
async def apple_touch_icon():
    return JSONResponse(status_code=204, content=None)


@app.get("/apple-touch-icon-precomposed.png")
async def apple_touch_icon_precomposed():
    return JSONResponse(status_code=204, content=None)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning("HTTP exception", status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


def get_bedrock_service() -> BedrockService:
    return bedrock_service


def get_vector_store_service() -> VectorStoreService:
    return vector_store_service


def get_memory_service() -> MemoryService:
    return memory_service


def get_document_service() -> DocumentService:
    return document_service


def get_rag_service() -> RAGService:
    return rag_service


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
