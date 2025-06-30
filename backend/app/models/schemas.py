from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for context"
    )
    use_tools: bool = Field(True, description="Whether to use available tools")


class ConversationResponse(BaseModel):
    response: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[Dict[str, Any]] = Field(default=[], description="Source documents")
    tools_used: List[str] = Field(default=[], description="Tools used in response")
    confidence_score: float = Field(..., description="Confidence in the response")
    response_id: Optional[str] = Field(
        None, description="Response ID for metrics tracking"
    )


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    chunks_created: int = Field(..., description="Number of chunks created")
    loader_chunks: Optional[int] = Field(None, description="Chunks created by loader")
    vector_chunks: Optional[int] = Field(
        None, description="Chunks saved in vector store"
    )
    status: str = Field(..., description="Upload status")


class ConversationSummary(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID")
    summary: str = Field(..., description="Conversation summary")
    key_topics: List[str] = Field(..., description="Key topics discussed")
    created_at: datetime = Field(..., description="Summary creation time")


class IntentClassification(BaseModel):
    intent: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Confidence score")
    entities: List[Dict[str, Any]] = Field(default=[], description="Extracted entities")


class EscalationRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation to escalate")
    reason: str = Field(..., description="Escalation reason")
    priority: str = Field(..., description="Escalation priority")


class HealthCheck(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Check timestamp")
    components: Dict[str, str] = Field(..., description="Component status")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserRatingRequest(BaseModel):
    response_id: str = Field(..., description="Response ID to rate")
    rating: str = Field(..., description="User rating: 'like' or 'dislike'")


class MetricsResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")


class SystemMetricsResponse(BaseModel):
    total_queries: int = Field(..., description="Total number of queries")
    total_errors: int = Field(..., description="Total number of errors")
    average_response_time: float = Field(
        ..., description="Average response time in seconds"
    )
    like_percentage: float = Field(..., description="Percentage of liked responses")
    tool_effectiveness: Dict[str, float] = Field(
        ..., description="Tool effectiveness scores"
    )
    error_rate: float = Field(..., description="Error rate percentage")
    conversation_retention_rate: float = Field(
        ..., description="Conversation retention rate"
    )
    timestamp: datetime = Field(..., description="Metrics timestamp")


class ConversationMetricsResponse(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID")
    total_messages: int = Field(..., description="Total messages in conversation")
    follow_up_questions: int = Field(..., description="Number of follow-up questions")
    context_retention_score: float = Field(..., description="Context retention score")
    average_response_time: float = Field(..., description="Average response time")
    total_likes: int = Field(..., description="Total likes in conversation")
    total_dislikes: int = Field(..., description="Total dislikes in conversation")
    tools_usage_count: Dict[str, int] = Field(..., description="Tool usage count")
    created_at: datetime = Field(..., description="Conversation creation time")
    last_activity: datetime = Field(..., description="Last activity time")


class ResponseMetricsResponse(BaseModel):
    response_id: str = Field(..., description="Response ID")
    conversation_id: str = Field(..., description="Conversation ID")
    query: str = Field(..., description="User query")
    response: str = Field(..., description="Assistant response")
    response_time: float = Field(..., description="Response time in seconds")
    confidence_score: float = Field(..., description="Confidence score")
    tools_used: List[str] = Field(..., description="Tools used")
    sources_count: int = Field(..., description="Number of sources")
    timestamp: datetime = Field(..., description="Response timestamp")
    user_rating: Optional[str] = Field(None, description="User rating")
    error_occurred: bool = Field(..., description="Whether an error occurred")
    error_message: Optional[str] = Field(None, description="Error message if any")


class MetricsExportResponse(BaseModel):
    system_metrics: Dict[str, Any] = Field(..., description="System metrics")
    conversation_metrics: List[Dict[str, Any]] = Field(
        ..., description="Conversation metrics"
    )
    response_metrics: List[Dict[str, Any]] = Field(..., description="Response metrics")
    export_timestamp: str = Field(..., description="Export timestamp")
