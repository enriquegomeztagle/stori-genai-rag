from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class ConversationSummaryInput(BaseModel):
    conversation_id: str = Field(..., description="ID of the conversation to summarize")


class IntentClassificationInput(BaseModel):
    message: str = Field(..., description="User message to classify")


class EscalationInput(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID to escalate")
    reason: str = Field(..., description="Reason for escalation")


class ContentSafetyInput(BaseModel):
    text: str = Field(..., description="Text to check for safety")


class DocumentSearchInput(BaseModel):
    query: str = Field(..., description="Search query for documents")


class CustomTool:
    def __init__(self, name: str, description: str, func: Callable, args_schema=None):
        self.name = name
        self.description = description
        self.func = func
        self.args_schema = args_schema


class ConversationSummaryTool:
    name = "conversation_summary"
    description = "Generate a summary of the current conversation"
    args_schema = ConversationSummaryInput

    def __init__(self, memory_service, bedrock_service):
        self.memory_service = memory_service
        self.bedrock_service = bedrock_service

    async def run(self, conversation_id: str) -> str:
        try:
            messages = await self.memory_service.get_conversation_messages(
                conversation_id
            )

            if not messages:
                return "No conversation found to summarize."

            existing_summary = await self.memory_service.get_conversation_summary(
                conversation_id
            )
            if existing_summary:
                return f"Existing summary: {existing_summary}"

            summary = await self.bedrock_service.summarize_conversation(messages)

            await self.memory_service.store_conversation_summary(
                conversation_id, summary
            )

            return f"Conversation summary generated: {summary}"

        except Exception as e:
            return f"Error generating summary: {str(e)}"


class IntentClassificationTool:
    name = "intent_classification"
    description = "Classify the intent of a user message"
    args_schema = IntentClassificationInput

    def __init__(self, bedrock_service):
        self.bedrock_service = bedrock_service

    async def run(self, message: str) -> str:
        try:
            intent_result = await self.bedrock_service.classify_intent(message)

            result = {
                "intent": intent_result.get("intent", "unknown"),
                "confidence": intent_result.get("confidence", 0.0),
                "entities": intent_result.get("entities", []),
            }

            return f"Intent classified: {result['intent']} (confidence: {result['confidence']:.2f})"

        except Exception as e:
            return f"Error classifying intent: {str(e)}"


class HumanEscalationTool:
    name = "human_escalation"
    description = "Escalate conversation to human agent"
    args_schema = EscalationInput

    def __init__(self, memory_service):
        self.memory_service = memory_service

    async def run(self, conversation_id: str, reason: str) -> str:
        try:
            escalation_id = str(uuid.uuid4())
            escalation_data = {
                "escalation_id": escalation_id,
                "conversation_id": conversation_id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "pending",
            }

            await self.memory_service.store_user_preferences(
                f"escalation:{escalation_id}", escalation_data
            )

            escalation_message = f"Conversation escalated to human agent. Reason: {reason}. Escalation ID: {escalation_id}"
            await self.memory_service.add_message(
                conversation_id, "system", escalation_message
            )

            return (
                f"Conversation escalated successfully. Escalation ID: {escalation_id}"
            )

        except Exception as e:
            return f"Error escalating conversation: {str(e)}"


class ContentSafetyTool:
    name = "content_safety_check"
    description = "Check if content is safe and appropriate"
    args_schema = ContentSafetyInput

    def __init__(self, bedrock_service):
        self.bedrock_service = bedrock_service

    async def run(self, text: str) -> str:
        try:
            safety_result = await self.bedrock_service.check_content_safety(text)

            is_safe = safety_result.get("is_safe", True)
            confidence = safety_result.get("confidence", 0.0)
            flags = safety_result.get("flags", [])

            if is_safe:
                return f"Content is safe (confidence: {confidence:.2f})"
            else:
                return f"Content flagged as unsafe (confidence: {confidence:.2f}). Flags: {flags}"

        except Exception as e:
            return f"Error checking content safety: {str(e)}"


class DocumentSearchTool:
    name = "document_search"
    description = "Search for relevant documents in the knowledge base"
    args_schema = DocumentSearchInput

    def __init__(self, vector_store_service):
        self.vector_store_service = vector_store_service

    async def run(self, query: str) -> str:
        try:
            results = self.vector_store_service.similarity_search(query, k=3)

            if not results:
                return "No relevant documents found."

            document_summaries = []
            for i, doc in enumerate(results, 1):
                content_preview = (
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                )
                document_summaries.append(f"Document {i}: {content_preview}")

            return f"Found {len(results)} relevant documents:\n" + "\n".join(
                document_summaries
            )

        except Exception as e:
            return f"Error searching documents: {str(e)}"


def get_agent_tools(memory_service, bedrock_service, vector_store_service) -> List[Any]:
    return [
        ConversationSummaryTool(memory_service, bedrock_service),
        IntentClassificationTool(bedrock_service),
        HumanEscalationTool(memory_service),
        ContentSafetyTool(bedrock_service),
        DocumentSearchTool(vector_store_service),
    ]
