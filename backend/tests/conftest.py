import asyncio
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os
import pytest
import boto3
from moto import mock_s3
from langchain.schema import Document


@pytest.fixture(autouse=True)
def mock_settings():
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.s3_region = "us-east-1"
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.embedding_model = "amazon.titan-embed-text-v1"
        mock_settings.aws_region = "us-east-1"
        mock_settings.chunk_size = 1000
        mock_settings.chunk_overlap = 200
        mock_settings.top_k_retrieval = 3
        yield mock_settings


@pytest.fixture
def mock_s3_client():
    with mock_s3():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")
        yield s3


@pytest.fixture
def mock_bedrock_client():
    with patch("boto3.client") as mock_boto3:
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = {
            "body": Mock(read=lambda: b'{"completion": "Test response"}')
        }
        mock_boto3.return_value = mock_bedrock
        yield mock_bedrock


@pytest.fixture
def mock_chroma_client():
    with patch("chromadb.Client") as mock_client:
        mock_collection = Mock()
        mock_collection.count.return_value = 10
        mock_collection.get.return_value = {
            "metadatas": [
                {"document_id": "doc1", "filename": "test1.pdf"},
                {"document_id": "doc2", "filename": "test2.pdf"},
            ]
        }
        mock_client.return_value.get_collection.return_value = mock_collection
        mock_client.return_value.delete_collection.return_value = None
        yield mock_client


@pytest.fixture
def mock_embeddings():
    with patch("langchain_aws.BedrockEmbeddings") as mock_embeddings:
        mock_embeddings.return_value.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_embeddings.return_value.embed_documents.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]
        yield mock_embeddings


@pytest.fixture
def mock_bedrock_service():
    mock_service = Mock()
    mock_service.classify_intent = AsyncMock(
        return_value={"intent": "mexican_revolution", "confidence": 0.9}
    )
    mock_service.check_content_safety = AsyncMock(
        return_value={"is_safe": True, "confidence": 0.95}
    )
    mock_service.generate_response = AsyncMock(return_value="Test response")
    return mock_service


@pytest.fixture
def mock_vector_store_service():
    mock_service = Mock()
    mock_service.similarity_search.return_value = [
        Document(page_content="Test content", metadata={"source": "doc1"})
    ]
    mock_service.add_documents.return_value = ["chunk1", "chunk2"]
    mock_service.get_collection_stats.return_value = {
        "total_chunks": 10,
        "total_documents": 5,
        "collection_name": "mexican_revolution_docs",
        "embedding_model": "amazon.titan-embed-text-v1",
    }
    return mock_service


@pytest.fixture
def mock_memory_service():
    mock_service = Mock()
    mock_service.get_conversation_messages = AsyncMock(return_value=[])
    mock_service.add_message = AsyncMock()
    mock_service.get_conversation_summary = AsyncMock(return_value="Test summary")
    mock_service.delete_conversation = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def sample_documents():
    return [
        Document(
            page_content="This is a test document about the Mexican Revolution.",
            metadata={
                "document_id": "test-doc-1",
                "filename": "test1.pdf",
                "file_type": "pdf",
                "uploaded_at": "2024-01-01T00:00:00",
                "source": "upload",
            },
        ),
        Document(
            page_content="Another document about historical events in Mexico.",
            metadata={
                "document_id": "test-doc-2",
                "filename": "test2.pdf",
                "file_type": "pdf",
                "uploaded_at": "2024-01-01T00:00:00",
                "source": "upload",
            },
        ),
    ]


@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("This is a test file content for document processing.")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_logger():
    with patch("app.core.logging.logger") as mock_logger:
        yield mock_logger
