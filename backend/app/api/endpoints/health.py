from fastapi import APIRouter, Depends
from datetime import datetime
from ...models.schemas import HealthCheck
from ...services.memory_service import MemoryService
from ...services.vector_store import VectorStoreService
from ...services.bedrock_service import BedrockService
from ...core.logging import logger


router = APIRouter()


def get_memory_service() -> MemoryService:
    from ...main import memory_service

    return memory_service


def get_vector_store_service() -> VectorStoreService:
    from ...main import vector_store_service

    return vector_store_service


def get_bedrock_service() -> BedrockService:
    from ...main import bedrock_service

    return bedrock_service


@router.get("/health", response_model=HealthCheck)
async def health_check(
    memory_service: MemoryService = Depends(get_memory_service),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
    bedrock_service: BedrockService = Depends(get_bedrock_service),
):
    logger.info("Performing comprehensive health check")
    components = {}

    try:
        memory_health = await memory_service.health_check()
        components["memory"] = memory_health["status"]
        logger.info(f"Memory service health: {memory_health['status']}")
    except (ConnectionError, TimeoutError, ValueError) as e:
        components["memory"] = "unhealthy"
        logger.error(f"Memory service health check failed: {str(e)}")

    try:
        vector_stats = vector_store_service.get_collection_stats()
        if "error" not in vector_stats:
            components["vector_store"] = "healthy"
            logger.info(f"Vector store health: healthy, stats: {vector_stats}")
        else:
            components["vector_store"] = "unhealthy"
            logger.warning(
                f"Vector store health: unhealthy, error: {vector_stats.get('error')}"
            )
    except (ConnectionError, TimeoutError, ValueError) as e:
        components["vector_store"] = "unhealthy"
        logger.error(f"Vector store health check failed: {str(e)}")

    try:
        test_response = await bedrock_service.generate_response(
            messages=[{"role": "user", "content": "Hello"}],
            system_prompt="You are a test assistant. Respond with 'OK'.",
        )
        if test_response:
            components["bedrock"] = "healthy"
            logger.info("Bedrock service health: healthy")
        else:
            components["bedrock"] = "unhealthy"
            logger.warning("Bedrock service health: unhealthy - no response")
    except (ConnectionError, TimeoutError, ValueError) as e:
        components["bedrock"] = "unhealthy"
        logger.error(f"Bedrock service health check failed: {str(e)}")

    overall_status = (
        "healthy"
        if all(status == "healthy" for status in components.values())
        else "unhealthy"
    )

    logger.info(f"Overall health status: {overall_status}, components: {components}")
    return HealthCheck(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        components=components,
    )


@router.get("/health/memory")
async def memory_health_check(
    memory_service: MemoryService = Depends(get_memory_service),
):
    return await memory_service.health_check()


@router.get("/health/vector-store")
async def vector_store_health_check(
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    try:
        stats = vector_store_service.get_collection_stats()
        return {"status": "healthy" if "error" not in stats else "unhealthy", **stats}
    except (ConnectionError, TimeoutError, ValueError) as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health/bedrock")
async def bedrock_health_check(
    bedrock_service: BedrockService = Depends(get_bedrock_service),
):
    try:
        test_response = await bedrock_service.generate_response(
            messages=[{"role": "user", "content": "Test"}],
            system_prompt="Respond with 'OK'.",
        )
        return {
            "status": "healthy" if test_response else "unhealthy",
            "response": test_response,
        }
    except (ConnectionError, TimeoutError, ValueError) as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/")
def health():
    return {"status": "ok"}
