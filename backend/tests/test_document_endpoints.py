import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.usefixtures("client")
class TestDocumentEndpoints:

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_document_service(self):
        mock_service = Mock()
        mock_service.is_supported_file.return_value = True
        mock_service.process_uploaded_file = AsyncMock(
            return_value={
                "document_id": "test-doc-123",
                "filename": "test.pdf",
                "file_type": "pdf",
                "documents": [
                    Mock(page_content="Test content 1", metadata={}),
                    Mock(page_content="Test content 2", metadata={}),
                ],
                "chunks_count": 2,
                "s3_key": None,
                "status": "processed",
            }
        )
        return mock_service

    @pytest.fixture
    def mock_vector_store_service(self):
        mock_service = Mock()
        mock_service.add_documents.return_value = ["chunk1", "chunk2"]
        mock_service.get_collection_stats.return_value = {
            "total_chunks": 10,
            "total_documents": 5,
            "collection_name": "mexican_revolution_docs",
            "embedding_model": "amazon.titan-embed-text-v1",
        }
        mock_service.clear_collection.return_value = True
        mock_service.similarity_search.return_value = [
            Mock(page_content="Test document content", metadata={"source": "doc1"})
        ]
        return mock_service

    @pytest.fixture
    def temp_pdf_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pdf") as f:
            f.write("Test PDF content")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @patch("app.api.endpoints.documents.get_document_service")
    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_upload_document_success(
        self,
        mock_get_vector_service,
        mock_get_doc_service,
        client,
        mock_document_service,
        mock_vector_store_service,
    ):
        mock_get_doc_service.return_value = mock_document_service
        mock_get_vector_service.return_value = mock_vector_store_service

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pdf") as f:
            f.write("Test PDF content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as file:
                files = {"file": ("test.pdf", file, "application/pdf")}

                response = client.post("/api/v1/documents/upload", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == "test-doc-123"
            assert data["filename"] == "test.pdf"
            assert data["chunks_created"] == 2
            assert data["loader_chunks"] == 2
            assert data["vector_chunks"] == 2
            assert data["status"] == "processed"

            mock_document_service.is_supported_file.assert_called_once_with("test.pdf")
            mock_document_service.process_uploaded_file.assert_called_once()
            mock_vector_store_service.add_documents.assert_called_once()

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("app.api.endpoints.documents.get_document_service")
    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_upload_document_unsupported_file(
        self,
        mock_get_vector_service,
        mock_get_doc_service,
        client,
        mock_document_service,
        mock_vector_store_service,
    ):
        mock_get_doc_service.return_value = mock_document_service
        mock_document_service.is_supported_file.return_value = False

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jpg") as f:
            f.write("Test image content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as file:
                files = {"file": ("test.jpg", file, "image/jpeg")}

                response = client.post("/api/v1/documents/upload", files=files)

            assert response.status_code == 400
            data = response.json()
            assert "Unsupported file type" in data["detail"]

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("app.api.endpoints.documents.get_document_service")
    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_upload_document_processing_error(
        self,
        mock_get_vector_service,
        mock_get_doc_service,
        client,
        mock_document_service,
        mock_vector_store_service,
    ):
        mock_get_doc_service.return_value = mock_document_service
        mock_document_service.process_uploaded_file.side_effect = Exception(
            "Processing failed"
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pdf") as f:
            f.write("Test PDF content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as file:
                files = {"file": ("test.pdf", file, "application/pdf")}

                response = client.post("/api/v1/documents/upload", files=files)

            assert response.status_code == 500
            data = response.json()
            assert "Processing failed" in data["detail"]

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_get_document_stats_success(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service

        response = client.get("/api/v1/documents/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_chunks"] == 10
        assert data["total_documents"] == 5
        assert data["collection_name"] == "mexican_revolution_docs"
        assert data["embedding_model"] == "amazon.titan-embed-text-v1"

        mock_vector_store_service.get_collection_stats.assert_called_once()

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_get_document_stats_error(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service
        mock_vector_store_service.get_collection_stats.side_effect = Exception(
            "Stats error"
        )

        response = client.get("/api/v1/documents/stats")

        assert response.status_code == 500
        data = response.json()
        assert "Stats error" in data["detail"]

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_clear_documents_success(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service

        response = client.delete("/api/v1/documents/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "All documents cleared successfully"

        mock_vector_store_service.clear_collection.assert_called_once()

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_clear_documents_error(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service
        mock_vector_store_service.clear_collection.return_value = False

        response = client.delete("/api/v1/documents/clear")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to clear documents" in data["detail"]

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_clear_documents_exception(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service
        mock_vector_store_service.clear_collection.side_effect = Exception(
            "Clear error"
        )

        response = client.delete("/api/v1/documents/clear")

        assert response.status_code == 500
        data = response.json()
        assert "Clear error" in data["detail"]

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_search_documents_success(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service

        response = client.get("/api/v1/documents/search?query=Mexican Revolution&k=5")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Mexican Revolution"
        assert data["results_count"] == 1
        assert len(data["documents"]) == 1
        assert data["documents"][0]["content"] == "Test document content"
        assert data["documents"][0]["metadata"]["source"] == "doc1"

        mock_vector_store_service.similarity_search.assert_called_once_with(
            "Mexican Revolution", k=5
        )

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_search_documents_with_default_k(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service

        response = client.get("/api/v1/documents/search?query=Mexican Revolution")

        assert response.status_code == 200

        mock_vector_store_service.similarity_search.assert_called_once_with(
            "Mexican Revolution", k=3
        )

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_search_documents_error(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service
        mock_vector_store_service.similarity_search.side_effect = Exception(
            "Search error"
        )

        response = client.get("/api/v1/documents/search?query=Mexican Revolution")

        assert response.status_code == 500
        data = response.json()
        assert "Search error" in data["detail"]

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_search_documents_long_content_truncation(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service

        long_content = "A" * 600
        mock_document = Mock()
        mock_document.page_content = long_content
        mock_document.metadata = {"source": "doc1"}
        mock_vector_store_service.similarity_search.return_value = [mock_document]

        response = client.get("/api/v1/documents/search?query=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"][0]["content"]) == 503
        assert data["documents"][0]["content"].endswith("...")

    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_search_documents_short_content_no_truncation(
        self, mock_get_vector_service, client, mock_vector_store_service
    ):
        mock_get_vector_service.return_value = mock_vector_store_service

        short_content = "Short content"
        mock_document = Mock()
        mock_document.page_content = short_content
        mock_document.metadata = {"source": "doc1"}
        mock_vector_store_service.similarity_search.return_value = [mock_document]

        response = client.get("/api/v1/documents/search?query=test")

        assert response.status_code == 200
        data = response.json()
        assert data["documents"][0]["content"] == short_content
        assert not data["documents"][0]["content"].endswith("...")

    def test_upload_document_missing_file(self, client):
        response = client.post("/api/v1/documents/upload")

        assert response.status_code == 422

    def test_search_documents_missing_query(self, client):
        response = client.get("/api/v1/documents/search")

        assert response.status_code == 422

    @patch("app.api.endpoints.documents.get_document_service")
    @patch("app.api.endpoints.documents.get_vector_store_service")
    def test_upload_document_vector_store_error(
        self,
        mock_get_vector_service,
        mock_get_doc_service,
        client,
        mock_document_service,
        mock_vector_store_service,
    ):
        mock_get_doc_service.return_value = mock_document_service
        mock_get_vector_service.return_value = mock_vector_store_service
        mock_vector_store_service.add_documents.side_effect = Exception(
            "Vector store error"
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pdf") as f:
            f.write("Test PDF content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as file:
                files = {"file": ("test.pdf", file, "application/pdf")}

                response = client.post("/api/v1/documents/upload", files=files)

            assert response.status_code == 500
            data = response.json()
            assert "Vector store error" in data["detail"]

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
