import pytest
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from langchain.schema import Document
from app.services.document_service import DocumentService


class TestDocumentService:

    @pytest.fixture
    def document_service(self, mock_s3_client):
        return DocumentService()

    def test_get_file_extension(self, document_service):
        assert document_service.get_file_extension("test.pdf") == ".pdf"
        assert document_service.get_file_extension("document.docx") == ".docx"
        assert document_service.get_file_extension("data.xlsx") == ".xlsx"
        assert document_service.get_file_extension("notes.txt") == ".txt"

        assert document_service.get_file_extension("TEST.PDF") == ".pdf"

        assert document_service.get_file_extension("filename") == ""

    def test_is_supported_file(self, document_service):
        assert document_service.is_supported_file("test.pdf") is True
        assert document_service.is_supported_file("document.docx") is True
        assert document_service.is_supported_file("data.xlsx") is True
        assert document_service.is_supported_file("notes.txt") is True

        assert document_service.is_supported_file("image.jpg") is False
        assert document_service.is_supported_file("video.mp4") is False
        assert document_service.is_supported_file("archive.zip") is False

    def test_get_loader_for_file(self, document_service, temp_file):
        with patch("app.services.document_service.PyPDFLoader") as mock_pdf_loader:
            loader = document_service.get_loader_for_file(temp_file, "pdf")
            mock_pdf_loader.assert_called_once_with(temp_file)

        with patch("app.services.document_service.Docx2txtLoader") as mock_docx_loader:
            loader = document_service.get_loader_for_file(temp_file, "docx")
            mock_docx_loader.assert_called_once_with(temp_file)

        with patch(
            "app.services.document_service.UnstructuredExcelLoader"
        ) as mock_excel_loader:
            loader = document_service.get_loader_for_file(temp_file, "excel")
            mock_excel_loader.assert_called_once_with(temp_file)

        with patch("app.services.document_service.TextLoader") as mock_text_loader:
            loader = document_service.get_loader_for_file(temp_file, "text")
            mock_text_loader.assert_called_once_with(temp_file)

    def test_get_loader_for_file_unsupported_type(self, document_service, temp_file):
        with pytest.raises(Exception, match="Unsupported file type: invalid"):
            document_service.get_loader_for_file(temp_file, "invalid")

    def test_get_loader_for_file_error(self, document_service, temp_file):
        with patch(
            "app.services.document_service.PyPDFLoader",
            side_effect=Exception("Loader error"),
        ):
            with pytest.raises(
                Exception, match="Error creating loader for pdf: Loader error"
            ):
                document_service.get_loader_for_file(temp_file, "pdf")

    @pytest.mark.asyncio
    async def test_process_uploaded_file_success(self, document_service, temp_file):
        with patch("app.services.document_service.PyPDFLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_documents = [
                Document(page_content="Test content 1", metadata={}),
                Document(page_content="Test content 2", metadata={}),
            ]
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader

            result = await document_service.process_uploaded_file(
                file_path=temp_file, filename="test.pdf", upload_to_s3=False
            )

            assert result["document_id"] is not None
            assert result["filename"] == "test.pdf"
            assert result["file_type"] == "pdf"
            assert result["chunks_count"] == 2
            assert result["status"] == "processed"
            assert result["s3_key"] is None

            for doc in mock_documents:
                assert doc.metadata["document_id"] == result["document_id"]
                assert doc.metadata["filename"] == "test.pdf"
                assert doc.metadata["file_type"] == "pdf"
                assert "uploaded_at" in doc.metadata
                assert doc.metadata["source"] == "upload"

    @pytest.mark.asyncio
    async def test_process_uploaded_file_with_s3(self, document_service, temp_file):
        with patch("app.services.document_service.PyPDFLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_documents = [Document(page_content="Test content", metadata={})]
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader

            with patch.object(
                document_service, "upload_to_s3", return_value="s3://bucket/key"
            ) as mock_s3:
                result = await document_service.process_uploaded_file(
                    file_path=temp_file, filename="test.pdf", upload_to_s3=True
                )

                mock_s3.assert_called_once()
                assert result["s3_key"] == "s3://bucket/key"

    @pytest.mark.asyncio
    async def test_process_uploaded_file_unsupported_type(
        self, document_service, temp_file
    ):
        with pytest.raises(Exception, match="Unsupported file type: test.jpg"):
            await document_service.process_uploaded_file(
                file_path=temp_file, filename="test.jpg", upload_to_s3=False
            )

    @pytest.mark.asyncio
    async def test_process_uploaded_file_loader_error(
        self, document_service, temp_file
    ):
        with patch(
            "app.services.document_service.PyPDFLoader",
            side_effect=Exception("Loader failed"),
        ):
            with pytest.raises(
                Exception,
                match="Error processing file test.pdf: Error creating loader for pdf: Loader failed",
            ):
                await document_service.process_uploaded_file(
                    file_path=temp_file, filename="test.pdf", upload_to_s3=False
                )

    @pytest.mark.asyncio
    async def test_upload_to_s3_success(self, document_service, temp_file):
        with patch.object(document_service.s3_client, "upload_file") as mock_upload:
            result = await document_service.upload_to_s3(
                file_path=temp_file, filename="test.pdf", document_id="test-doc-123"
            )
            mock_upload.assert_called_once()
            assert result == "documents/test-doc-123/test.pdf"

    @pytest.mark.asyncio
    async def test_upload_to_s3_error(self, document_service, temp_file):
        with patch.object(
            document_service.s3_client, "upload_file", side_effect=Exception("S3 error")
        ):
            with pytest.raises(Exception, match="Error uploading to S3: S3 error"):
                await document_service.upload_to_s3(
                    file_path=temp_file, filename="test.pdf", document_id="test-doc-123"
                )

    def test_get_content_type(self, document_service):
        assert document_service._get_content_type("test.pdf") == "application/pdf"
        assert (
            document_service._get_content_type("document.docx")
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert (
            document_service._get_content_type("data.xlsx")
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert document_service._get_content_type("notes.txt") == "text/plain"
        assert (
            document_service._get_content_type("unknown.xyz")
            == "application/octet-stream"
        )

    @pytest.mark.asyncio
    async def test_get_document_from_s3_success(self, document_service):
        mock_body = MagicMock()
        mock_body.read.return_value = b"document content"
        mock_response = {"Body": mock_body}

        with patch.object(
            document_service.s3_client, "get_object", return_value=mock_response
        ):
            result = await document_service.get_document_from_s3(
                "documents/test-doc/test.pdf"
            )
            assert result == b"document content"

    @pytest.mark.asyncio
    async def test_get_document_from_s3_error(self, document_service):
        with patch.object(
            document_service.s3_client, "get_object", side_effect=Exception("S3 error")
        ):
            with pytest.raises(Exception, match="Error downloading from S3: S3 error"):
                await document_service.get_document_from_s3(
                    "documents/test-doc/test.pdf"
                )

    @pytest.mark.asyncio
    async def test_delete_document_from_s3_success(self, document_service):
        with patch.object(document_service.s3_client, "delete_object"):
            result = await document_service.delete_document_from_s3(
                "documents/test-doc/test.pdf"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_document_from_s3_error(self, document_service):
        with patch.object(
            document_service.s3_client,
            "delete_object",
            side_effect=Exception("S3 error"),
        ):
            with pytest.raises(Exception, match="Error deleting from S3: S3 error"):
                await document_service.delete_document_from_s3(
                    "documents/test-doc/test.pdf"
                )

    def test_supported_extensions(self, document_service):
        expected_extensions = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"}
        assert set(document_service.supported_extensions.keys()) == expected_extensions
