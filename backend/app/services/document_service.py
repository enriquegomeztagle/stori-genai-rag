import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import boto3
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    TextLoader,
)
from ..core.config import settings


class DocumentService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.supported_extensions = {
            ".pdf": "pdf",
            ".docx": "docx",
            ".doc": "docx",
            ".xlsx": "excel",
            ".xls": "excel",
            ".txt": "text",
        }

    def get_file_extension(self, filename: str) -> str:
        return os.path.splitext(filename.lower())[1]

    def is_supported_file(self, filename: str) -> bool:
        extension = self.get_file_extension(filename)
        return extension in self.supported_extensions

    def get_loader_for_file(self, file_path: str, file_type: str):
        try:
            if file_type == "pdf":
                return PyPDFLoader(file_path)
            elif file_type == "docx":
                return Docx2txtLoader(file_path)
            elif file_type == "excel":
                return UnstructuredExcelLoader(file_path)
            elif file_type == "text":
                return TextLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise Exception(f"Error creating loader for {file_type}: {str(e)}")

    async def process_uploaded_file(
        self, file_path: str, filename: str, upload_to_s3: bool = True
    ) -> Dict[str, Any]:
        try:
            if not self.is_supported_file(filename):
                raise ValueError(f"Unsupported file type: {filename}")

            extension = self.get_file_extension(filename)
            file_type = self.supported_extensions[extension]

            document_id = str(uuid.uuid4())

            loader = self.get_loader_for_file(file_path, file_type)
            documents = loader.load()

            for doc in documents:
                doc.metadata.update(
                    {
                        "document_id": document_id,
                        "filename": filename,
                        "file_type": file_type,
                        "uploaded_at": datetime.utcnow().isoformat(),
                        "source": "upload",
                    }
                )

            s3_key = None
            if upload_to_s3:
                s3_key = await self.upload_to_s3(file_path, filename, document_id)

            return {
                "document_id": document_id,
                "filename": filename,
                "file_type": file_type,
                "documents": documents,
                "chunks_count": len(documents),
                "s3_key": s3_key,
                "status": "processed",
            }

        except Exception as e:
            raise Exception(f"Error processing file {filename}: {str(e)}")

    async def upload_to_s3(
        self, file_path: str, filename: str, document_id: str
    ) -> str:
        try:
            s3_key = f"documents/{document_id}/{filename}"

            self.s3_client.upload_file(
                file_path,
                settings.s3_bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": self._get_content_type(filename),
                    "Metadata": {
                        "document_id": document_id,
                        "uploaded_at": datetime.utcnow().isoformat(),
                    },
                },
            )

            return s3_key

        except Exception as e:
            raise Exception(f"Error uploading to S3: {str(e)}")

    def _get_content_type(self, filename: str) -> str:
        extension = self.get_file_extension(filename)
        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".txt": "text/plain",
        }
        return content_types.get(extension, "application/octet-stream")

    async def get_document_from_s3(self, s3_key: str) -> bytes:
        try:
            response = self.s3_client.get_object(
                Bucket=settings.s3_bucket_name, Key=s3_key
            )
            return response["Body"].read()

        except Exception as e:
            raise Exception(f"Error downloading from S3: {str(e)}")

    async def delete_document_from_s3(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
            return True

        except Exception as e:
            raise Exception(f"Error deleting from S3: {str(e)}")
