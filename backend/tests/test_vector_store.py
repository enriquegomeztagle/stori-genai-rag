import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.schema import Document
from app.services.vector_store import VectorStoreService


class TestVectorStoreService:

    @pytest.fixture
    def vector_store_service(self):
        with patch(
            "app.services.vector_store.BedrockEmbeddings"
        ) as mock_embeddings, patch(
            "app.services.vector_store.Chroma"
        ) as mock_chroma, patch(
            "chromadb.PersistentClient"
        ) as mock_client:

            mock_embeddings.return_value = Mock()
            mock_client.return_value = Mock()
            mock_chroma.return_value = Mock()

            service = VectorStoreService()
            service.vector_store = mock_chroma.return_value
            return service

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

    @patch("app.services.vector_store.BedrockEmbeddings")
    @patch("chromadb.PersistentClient")
    def test_initialization(self, mock_chroma_client, mock_embeddings):
        with patch("app.services.vector_store.Chroma") as mock_chroma:
            service = VectorStoreService()

            mock_embeddings.assert_called_once()

            mock_chroma.assert_called_once()

            assert isinstance(service.chroma_client, MagicMock)

    def test_add_documents_success(self, vector_store_service, sample_documents):
        vector_store_service.vector_store.add_documents.return_value = [
            "chunk1",
            "chunk2",
        ]

        result = vector_store_service.add_documents(sample_documents)

        assert result == ["chunk1", "chunk2"]
        vector_store_service.vector_store.add_documents.assert_called_once_with(
            sample_documents
        )

    def test_add_documents_error(self, vector_store_service, sample_documents):
        vector_store_service.vector_store.add_documents.side_effect = Exception(
            "Add error"
        )

        with pytest.raises(Exception, match="Add error"):
            vector_store_service.add_documents(sample_documents)

    def test_similarity_search_success(self, vector_store_service):
        expected_results = [
            Document(page_content="Test result 1", metadata={"source": "doc1"}),
            Document(page_content="Test result 2", metadata={"source": "doc2"}),
        ]
        vector_store_service.vector_store.similarity_search.return_value = (
            expected_results
        )

        query = "Mexican Revolution"
        k = 5

        result = vector_store_service.similarity_search(query, k)

        assert result == expected_results
        vector_store_service.vector_store.similarity_search.assert_called_once_with(
            query=query, k=k, filter=None
        )

    def test_similarity_search_with_default_k(self, vector_store_service):
        query = "Mexican Revolution"

        result = vector_store_service.similarity_search(query)

        vector_store_service.vector_store.similarity_search.assert_called_once_with(
            query=query, k=5, filter=None
        )

    def test_similarity_search_with_filter(self, vector_store_service):
        expected_results = [Document(page_content="Filtered result", metadata={})]
        vector_store_service.vector_store.similarity_search.return_value = (
            expected_results
        )

        query = "Mexican Revolution"
        k = 3
        filter_dict = {"document_id": "doc1"}

        result = vector_store_service.similarity_search(query, k, filter_dict)

        assert result == expected_results
        vector_store_service.vector_store.similarity_search.assert_called_once_with(
            query=query, k=k, filter=filter_dict
        )

    def test_similarity_search_error(self, vector_store_service):
        vector_store_service.vector_store.similarity_search.side_effect = Exception(
            "Search error"
        )

        query = "Mexican Revolution"

        with pytest.raises(Exception, match="Search error"):
            vector_store_service.similarity_search(query)

    def test_get_collection_stats_success(self, vector_store_service):
        vector_store_service.vector_store.get.return_value = {
            "metadatas": [{"document_id": f"doc{i}"} for i in range(5)]
        }
        vector_store_service.vector_store.count.return_value = 10

        result = vector_store_service.get_collection_stats()

        assert result["total_chunks"] == 10
        assert result["total_documents"] == 5
        assert result["collection_name"] == "mexican_revolution_docs"
        assert result["embedding_model"] == "amazon.titan-embed-text-v1"

    def test_get_collection_stats_error(self, vector_store_service):
        vector_store_service.vector_store.count.side_effect = Exception("Stats error")

        result = vector_store_service.get_collection_stats()
        assert result["total_chunks"] == 0
        assert result["error"] == "Stats error"

    def test_delete_documents_success(self, vector_store_service):
        vector_store_service.vector_store.delete.return_value = True

        document_ids = ["doc1", "doc2"]

        result = vector_store_service.delete_documents(document_ids)

        assert result is True
        vector_store_service.vector_store.delete.assert_called_once_with(
            ids=document_ids
        )

    def test_delete_documents_error(self, vector_store_service):
        vector_store_service.vector_store.delete.side_effect = Exception("Delete error")

        document_ids = ["doc1", "doc2"]

        with pytest.raises(Exception, match="Delete error"):
            vector_store_service.delete_documents(document_ids)

    def test_clear_collection_success(self, vector_store_service):
        with patch("app.services.vector_store.Chroma") as mock_chroma:
            mocked_vector_store = MagicMock()
            mocked_vector_store.delete_collection.return_value = True
            vector_store_service.vector_store = mocked_vector_store

            result = vector_store_service.clear_collection()

            assert result is True
            mocked_vector_store.delete_collection.assert_called_once()
            mock_chroma.assert_called_once()

    def test_clear_collection_error(self, vector_store_service):
        vector_store_service.vector_store.delete_collection.side_effect = Exception(
            "Clear error"
        )

        with pytest.raises(Exception, match="Clear error"):
            vector_store_service.clear_collection()

    def test_get_document_by_id_success(self, vector_store_service):
        vector_store_service.vector_store.get.return_value = {
            "documents": ["Test document content"],
            "metadatas": [{"document_id": "doc1", "source": "test"}],
        }

        document_id = "doc1"

        result = vector_store_service.get_document_by_id(document_id)

        assert result["document"] == "Test document content"
        assert result["metadata"]["document_id"] == "doc1"

    def test_get_document_by_id_not_found(self, vector_store_service):
        vector_store_service.vector_store.get.return_value = {
            "documents": [],
            "metadatas": [],
        }

        document_id = "non-existent"

        result = vector_store_service.get_document_by_id(document_id)

        assert result is None

    def test_get_document_by_id_error(self, vector_store_service):
        vector_store_service.vector_store.get.side_effect = Exception("Get error")

        document_id = "doc1"

        with pytest.raises(Exception, match="Get error"):
            vector_store_service.get_document_by_id(document_id)
