import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from ...models.schemas import (
    MetricsResponse,
    UserRatingRequest,
    SystemMetricsResponse,
    ConversationMetricsResponse,
    ResponseMetricsResponse,
    MetricsExportResponse,
)
from ...services.metrics_service import MetricsService
from ...core.logging import logger

router = APIRouter()


def get_metrics_service() -> MetricsService:
    from ...main import metrics_service

    return metrics_service


@router.post("/rating", response_model=MetricsResponse)
async def record_user_rating(
    request: UserRatingRequest,
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    try:
        success = await metrics_service.record_user_rating(
            response_id=request.response_id, rating=request.rating
        )

        if not success:
            raise HTTPException(status_code=404, detail="Response not found")

        return MetricsResponse(
            success=True,
            message="Rating recorded successfully",
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error("Error recording user rating", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/system", response_model=SystemMetricsResponse)
async def get_system_metrics(
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    try:
        system_metrics = await metrics_service.get_system_metrics()

        return SystemMetricsResponse(
            total_queries=system_metrics.total_queries,
            total_errors=system_metrics.total_errors,
            average_response_time=system_metrics.average_response_time,
            like_percentage=system_metrics.like_percentage,
            tool_effectiveness=system_metrics.tool_effectiveness,
            error_rate=system_metrics.error_rate,
            conversation_retention_rate=system_metrics.conversation_retention_rate,
            timestamp=system_metrics.timestamp,
        )

    except Exception as e:
        logger.error("Error getting system metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/conversation/{conversation_id}", response_model=ConversationMetricsResponse
)
async def get_conversation_metrics(
    conversation_id: str, metrics_service: MetricsService = Depends(get_metrics_service)
):
    try:
        conv_metrics = await metrics_service.get_conversation_metrics(conversation_id)

        if not conv_metrics:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ConversationMetricsResponse(
            conversation_id=conv_metrics.conversation_id,
            total_messages=conv_metrics.total_messages,
            follow_up_questions=conv_metrics.follow_up_questions,
            context_retention_score=conv_metrics.context_retention_score,
            average_response_time=conv_metrics.average_response_time,
            total_likes=conv_metrics.total_likes,
            total_dislikes=conv_metrics.total_dislikes,
            tools_usage_count=conv_metrics.tools_usage_count,
            created_at=conv_metrics.created_at,
            last_activity=conv_metrics.last_activity,
        )

    except Exception as e:
        logger.error("Error getting conversation metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversations", response_model=List[ConversationMetricsResponse])
async def get_all_conversation_metrics(
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    try:
        conv_metrics_list = await metrics_service.get_all_conversation_metrics()

        return [
            ConversationMetricsResponse(
                conversation_id=cm.conversation_id,
                total_messages=cm.total_messages,
                follow_up_questions=cm.follow_up_questions,
                context_retention_score=cm.context_retention_score,
                average_response_time=cm.average_response_time,
                total_likes=cm.total_likes,
                total_dislikes=cm.total_dislikes,
                tools_usage_count=cm.tools_usage_count,
                created_at=cm.created_at,
                last_activity=cm.last_activity,
            )
            for cm in conv_metrics_list
        ]

    except Exception as e:
        logger.error("Error getting all conversation metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/response/{response_id}", response_model=ResponseMetricsResponse)
async def get_response_metrics(
    response_id: str, metrics_service: MetricsService = Depends(get_metrics_service)
):
    try:
        response_metrics = await metrics_service.get_response_metrics(response_id)

        if not response_metrics:
            raise HTTPException(status_code=404, detail="Response not found")

        return ResponseMetricsResponse(
            response_id=response_metrics.response_id,
            conversation_id=response_metrics.conversation_id,
            query=response_metrics.query,
            response=response_metrics.response,
            response_time=response_metrics.response_time,
            confidence_score=response_metrics.confidence_score,
            tools_used=response_metrics.tools_used,
            sources_count=response_metrics.sources_count,
            timestamp=response_metrics.timestamp,
            user_rating=response_metrics.user_rating,
            error_occurred=response_metrics.error_occurred,
            error_message=response_metrics.error_message,
        )

    except Exception as e:
        logger.error("Error getting response metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/recent", response_model=List[ResponseMetricsResponse])
async def get_recent_metrics(
    hours: int = 24, metrics_service: MetricsService = Depends(get_metrics_service)
):
    try:
        recent_metrics = await metrics_service.get_recent_metrics(hours)

        return [
            ResponseMetricsResponse(
                response_id=rm.response_id,
                conversation_id=rm.conversation_id,
                query=rm.query,
                response=rm.response,
                response_time=rm.response_time,
                confidence_score=rm.confidence_score,
                tools_used=rm.tools_used,
                sources_count=rm.sources_count,
                timestamp=rm.timestamp,
                user_rating=rm.user_rating,
                error_occurred=rm.error_occurred,
                error_message=rm.error_message,
            )
            for rm in recent_metrics
        ]

    except Exception as e:
        logger.error("Error getting recent metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/export", response_model=MetricsExportResponse)
async def export_metrics(
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    try:
        export_data = await metrics_service.export_metrics()

        return MetricsExportResponse(
            system_metrics=export_data["system_metrics"],
            conversation_metrics=export_data["conversation_metrics"],
            response_metrics=export_data["response_metrics"],
            export_timestamp=export_data["export_timestamp"],
        )

    except Exception as e:
        logger.error("Error exporting metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/clear")
async def clear_old_metrics(
    days: int = 30, metrics_service: MetricsService = Depends(get_metrics_service)
):
    try:
        await metrics_service.clear_old_metrics(days)

        if days == 0:
            message = "Cleared all metrics"
        else:
            message = f"Cleared metrics older than {days} days"

        return MetricsResponse(
            success=True, message=message, timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error("Error clearing metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
