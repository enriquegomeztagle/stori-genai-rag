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
