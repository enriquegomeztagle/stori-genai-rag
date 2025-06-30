import datetime
import uuid
import time

from fastapi import APIRouter, HTTPException, Depends
from ...models.schemas import (
    ConversationRequest,
    ConversationResponse,
    ConversationSummary,
    IntentClassification,
    EscalationRequest,
)
from ...services.rag_service import RAGService
from ...services.memory_service import MemoryService
from ...services.bedrock_service import BedrockService
from ...services.metrics_service import MetricsService
from ...core.logging import logger

router = APIRouter()


def get_rag_service() -> RAGService:
    from ...main import rag_service

    return rag_service


def get_memory_service() -> MemoryService:
    from ...main import memory_service

    return memory_service


def get_bedrock_service() -> BedrockService:
    from ...main import bedrock_service

    return bedrock_service


def get_metrics_service() -> MetricsService:
    from ...main import metrics_service

    return metrics_service


@router.post("/chat", response_model=ConversationResponse)
async def chat(
    request: ConversationRequest,
    rag_service: RAGService = Depends(get_rag_service),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    start_time = time.time()
    response_id = None

    try:
        logger.info(
            "Processing chat message",
            conversation_id=request.conversation_id,
            message_length=len(request.message),
        )

        result = await rag_service.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            use_tools=request.use_tools,
        )

        response_time = time.time() - start_time

        response = ConversationResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            sources=result.get("sources", []),
            tools_used=result.get("tools_used", []),
            confidence_score=result.get("confidence_score", 0.0),
        )

        response_id = await metrics_service.record_response(
            conversation_id=result["conversation_id"],
            query=request.message,
            response=result["response"],
            response_time=response_time,
            confidence_score=result.get("confidence_score", 0.0),
            tools_used=result.get("tools_used", []),
            sources_count=len(result.get("sources", [])),
            error_occurred=False,
        )

        response.response_id = response_id

        logger.info(
            "Chat response generated",
            conversation_id=response.conversation_id,
            tools_used=response.tools_used,
            response_time=response_time,
            response_id=response_id,
        )

        return response

    except Exception as e:
        response_time = time.time() - start_time

        if request.conversation_id and metrics_service:
            try:
                await metrics_service.record_response(
                    conversation_id=request.conversation_id,
                    query=request.message,
                    response="",
                    response_time=response_time,
                    confidence_score=0.0,
                    tools_used=[],
                    sources_count=0,
                    error_occurred=True,
                    error_message=str(e),
                )
            except Exception as metrics_error:
                logger.error("Error recording metrics", error=str(metrics_error))

        logger.error("Error processing chat message", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversation/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str, rag_service: RAGService = Depends(get_rag_service)
):
    try:
        messages = await rag_service.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "messages": messages}

    except Exception as e:
        logger.error("Error getting conversation history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str, rag_service: RAGService = Depends(get_rag_service)
):
    try:
        success = await rag_service.delete_conversation(conversation_id)
        if success:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")

    except Exception as e:
        logger.error("Error deleting conversation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/conversation/{conversation_id}/summary", response_model=ConversationSummary
)
async def generate_conversation_summary(
    conversation_id: str,
    rag_service: RAGService = Depends(get_rag_service),
    bedrock_service: BedrockService = Depends(get_bedrock_service),
):
    try:
        messages = await rag_service.get_conversation_history(conversation_id)

        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")

        summary = await bedrock_service.summarize_conversation(messages)

        key_topics = ["Mexican Revolution", "Historical figures", "Events"]

        response = ConversationSummary(
            conversation_id=conversation_id,
            summary=summary,
            key_topics=key_topics,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        return response

    except Exception as e:
        logger.error("Error generating conversation summary", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/intent/classify", response_model=IntentClassification)
async def classify_intent(
    request: ConversationRequest,
    bedrock_service: BedrockService = Depends(get_bedrock_service),
):
    try:
        intent_result = await bedrock_service.classify_intent(request.message)

        response = IntentClassification(
            intent=intent_result.get("intent", "unknown"),
            confidence=intent_result.get("confidence", 0.0),
            entities=intent_result.get("entities", []),
        )

        return response

    except Exception as e:
        logger.error("Error classifying intent", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/escalate")
async def escalate_conversation(
    request: EscalationRequest,
    memory_service: MemoryService = Depends(get_memory_service),
):
    try:
        escalation_id = str(uuid.uuid4())
        escalation_data = {
            "escalation_id": escalation_id,
            "conversation_id": request.conversation_id,
            "reason": request.reason,
            "priority": request.priority,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "pending",
        }

        await memory_service.store_user_preferences(
            f"escalation:{escalation_id}", escalation_data
        )

        return {
            "escalation_id": escalation_id,
            "status": "escalated",
            "message": "Conversation escalated successfully",
        }

    except Exception as e:
        logger.error("Error escalating conversation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversations")
async def list_conversations(
    memory_service: MemoryService = Depends(get_memory_service),
):
    try:
        conversations = []

        pattern = "conversation:*"
        keys = await memory_service.redis_client.keys(pattern)

        for key in keys[:10]:
            conversation_id = key.split(":")[1]
            conversation = await memory_service.get_conversation(conversation_id)
            if conversation:
                conversations.append(
                    {
                        "conversation_id": conversation_id,
                        "message_count": conversation.get("message_count", 0),
                        "last_updated": conversation.get("last_updated"),
                    }
                )

        return {"conversations": conversations}

    except Exception as e:
        logger.error("Error listing conversations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
