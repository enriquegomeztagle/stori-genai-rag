import pytest
from unittest.mock import Mock, patch, AsyncMock
from langchain.schema import Document
from app.services.rag_service import RAGService
from app.services.bedrock_service import BedrockService
from app.services.vector_store import VectorStoreService
from app.services.memory_service import MemoryService


class TestRAGService:

    @pytest.fixture
    def rag_service(
        self, mock_bedrock_service, mock_vector_store_service, mock_memory_service
    ):
        return RAGService(
            bedrock_service=mock_bedrock_service,
            vector_store_service=mock_vector_store_service,
            memory_service=mock_memory_service,
            tools=[],
        )

    @pytest.fixture
    def sample_documents(self):
        return [
            Document(
                page_content="The Mexican Revolution was a major armed struggle that began in 1910.",
                metadata={"document_id": "doc1", "source": "test"},
            ),
            Document(
                page_content="Emiliano Zapata was a leading figure in the Mexican Revolution.",
                metadata={"document_id": "doc2", "source": "test"},
            ),
        ]

    @pytest.mark.asyncio
    async def test_process_message_success(self, rag_service):
        message = "Tell me about the Mexican Revolution"

        result = await rag_service.process_message(message)

        assert result["conversation_id"] is not None
        assert result["response"] is not None
        assert result["sources"] == []
        assert result["tools_used"] == ["document_search"]

    @pytest.mark.asyncio
    async def test_process_message_with_conversation_id(self, rag_service):
        message = "Tell me about the Mexican Revolution"
        conversation_id = "existing-conversation-123"

        result = await rag_service.process_message(message, conversation_id)

        assert result["conversation_id"] == conversation_id
        assert result["response"] is not None

    @pytest.mark.asyncio
    async def test_process_message_content_safety_violation(
        self, rag_service, mock_bedrock_service
    ):
        mock_bedrock_service.check_content_safety = AsyncMock(
            return_value={
                "is_safe": False,
                "confidence": 0.8,
                "reason": "Inappropriate content",
            }
        )

        message = "Inappropriate content"

        result = await rag_service.process_message(message)

        assert "No puedo procesar este mensaje" in result["response"]
        assert result["tools_used"] == ["content_safety_check"]

    @pytest.mark.asyncio
    async def test_process_message_off_topic(self, rag_service, mock_bedrock_service):
        mock_bedrock_service.classify_intent = AsyncMock(
            return_value={"intent": "off_topic", "confidence": 0.7}
        )
        mock_bedrock_service.generate_response = AsyncMock(
            return_value="Solo puedo responder preguntas sobre la Revolución Mexicana"
        )

        message = "What's the weather like?"

        result = await rag_service.process_message(message)

        assert (
            "Solo puedo responder preguntas sobre la Revolución Mexicana"
            in result["response"]
        )

    @pytest.mark.asyncio
    async def test_process_message_processing_error(
        self, rag_service, mock_bedrock_service
    ):
        mock_bedrock_service.check_content_safety = AsyncMock(
            side_effect=Exception("Processing error")
        )

        message = "Tell me about the Mexican Revolution"

        result = await rag_service.process_message(message)

        assert "Ocurrió un error al procesar tu mensaje" in result["response"]

    @pytest.mark.asyncio
    async def test_generate_rag_response_success(self, rag_service):
        message = "Tell me about the Mexican Revolution"

        response, tools_used = await rag_service._generate_rag_response(
            message, [], True
        )

        assert response is not None
        assert tools_used == ["document_search"]

    @pytest.mark.asyncio
    async def test_generate_rag_response_no_documents(
        self, rag_service, mock_vector_store_service
    ):
        mock_vector_store_service.similarity_search.side_effect = Exception(
            "No documents found"
        )

        message = "Tell me about the Mexican Revolution"

        response, tools_used = await rag_service._generate_rag_response(
            message, [], True
        )

        assert response is not None
        assert tools_used == []

    @pytest.mark.asyncio
    async def test_generate_rag_response_with_conversation_history(self, rag_service):
        conversation_messages = [
            {"role": "user", "content": "What happened in 1910?"},
            {"role": "assistant", "content": "The Mexican Revolution began in 1910."},
            {"role": "user", "content": "Who was involved?"},
            {
                "role": "assistant",
                "content": "Many revolutionary leaders were involved.",
            },
        ]

        message = "Tell me more about the leaders"

        response, tools_used = await rag_service._generate_rag_response(
            message, conversation_messages, True
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_generate_rag_response_without_tools(self, rag_service):
        message = "Tell me about the Mexican Revolution"

        response, tools_used = await rag_service._generate_rag_response(
            message, [], False
        )

        assert response is not None
        assert tools_used == ["document_search"]

    @pytest.mark.asyncio
    async def test_generate_rag_response_error_handling(
        self, rag_service, mock_bedrock_service
    ):
        mock_bedrock_service.generate_response = AsyncMock(
            side_effect=Exception("Generation error")
        )

        message = "Tell me about the Mexican Revolution"

        with pytest.raises(Exception, match="Generation error"):
            await rag_service._generate_rag_response(message, [], True)

    @pytest.mark.asyncio
    async def test_process_message_with_tools(self, rag_service):
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.run = AsyncMock(return_value="Tool result")
        rag_service.tools = [mock_tool]

        message = "Use the test tool"

        result = await rag_service.process_message(message, use_tools=True)

        assert result["response"] is not None
        assert result["tools_used"] == ["document_search"]

    @pytest.mark.asyncio
    async def test_process_message_without_tools(self, rag_service):
        message = "Tell me about the Mexican Revolution"

        result = await rag_service.process_message(message, use_tools=False)

        assert result["response"] is not None
        assert result["tools_used"] == ["document_search"]

    @pytest.mark.asyncio
    async def test_process_message_off_topic_with_relevant_docs(
        self,
        rag_service,
        mock_bedrock_service,
        mock_vector_store_service,
        mock_memory_service,
    ):
        rag_service.bedrock_service = mock_bedrock_service
        rag_service.vector_store_service = mock_vector_store_service
        rag_service.memory_service = mock_memory_service

        mock_bedrock_service.classify_intent = AsyncMock(
            return_value={"intent": "off_topic", "confidence": 0.7}
        )
        mock_bedrock_service.check_content_safety = AsyncMock(
            return_value={"is_safe": True, "confidence": 0.95}
        )
        mock_bedrock_service.generate_response = AsyncMock(
            return_value="The Mexican Revolution was a major armed struggle."
        )

        mock_vector_store_service.similarity_search.return_value = [
            Document(page_content="Mexican Revolution content", metadata={})
        ]

        mock_memory_service.add_message = AsyncMock()
        mock_memory_service.get_conversation_messages = AsyncMock(return_value=[])

        message = "What's the weather like?"

        result = await rag_service.process_message(message)

        assert result["tools_used"] == ["document_search"]

    @pytest.mark.asyncio
    async def test_generate_rag_response_with_sources(
        self,
        rag_service,
        mock_vector_store_service,
        mock_memory_service,
        sample_documents,
    ):
        rag_service.vector_store_service = mock_vector_store_service
        rag_service.memory_service = mock_memory_service
        rag_service.bedrock_service = Mock()
        rag_service.bedrock_service.generate_response = AsyncMock(
            return_value="The Mexican Revolution was a major armed struggle."
        )

        mock_vector_store_service.similarity_search.return_value = sample_documents

        message = "Tell me about the Mexican Revolution"

        response, tools_used = await rag_service._generate_rag_response(
            message, [], True
        )

        assert response is not None
        assert tools_used == ["document_search"]
