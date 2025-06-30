import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_aws import BedrockEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Dict, Any, Optional
import uuid
import os
from ..core.config import settings
from ..core.logging import logger


class VectorStoreService:
    def __init__(self):
        self.chroma_client = chromadb.Client(
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=False,
            )
        )

        try:
            self.embeddings = BedrockEmbeddings(
                model_id=settings.embedding_model, region_name=settings.aws_region
            )
            logger.info(f"Using Bedrock embeddings: {settings.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock embeddings: {e}")
            raise Exception(f"Bedrock embeddings initialization failed: {e}")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name="mexican_revolution_docs",
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: List[Document]) -> List[str]:
        try:
            chunks = self.text_splitter.split_documents(documents)

            ids = self.vector_store.add_documents(chunks)

            return ids

        except Exception as e:
            raise Exception(f"Error adding documents to vector store: {str(e)}")

    def similarity_search(
        self, query: str, k: int = None, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        if k is None:
            k = settings.top_k_retrieval

        try:
            results = self.vector_store.similarity_search(
                query=query, k=k, filter=filter_dict
            )

            return results

        except Exception as e:
            raise Exception(f"Error searching vector store: {str(e)}")

    def similarity_search_with_score(
        self, query: str, k: int = None, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        if k is None:
            k = settings.top_k_retrieval

        try:
            results = self.vector_store.similarity_search_with_score(
                query=query, k=k, filter=filter_dict
            )

            return results

        except Exception as e:
            raise Exception(f"Error searching vector store with scores: {str(e)}")

    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            collection = self.chroma_client.get_collection("mexican_revolution_docs")
            count_chunks = collection.count()

            all_data = collection.get(include=["metadatas"])
            all_metadatas = all_data["metadatas"]

            unique_documents = set()
            for meta in all_metadatas:
                if meta.get("document_id"):
                    unique_documents.add(meta["document_id"])
                elif meta.get("filename"):
                    unique_documents.add(meta["filename"])

            count_documents = len(unique_documents)

            return {
                "total_chunks": count_chunks,
                "total_chunks_real": len(all_metadatas),
                "total_documents": count_documents,
                "collection_name": "mexican_revolution_docs",
                "embedding_model": settings.embedding_model,
            }

        except Exception as e:
            return {
                "total_chunks": 0,
                "total_chunks_real": 0,
                "total_documents": 0,
                "collection_name": "mexican_revolution_docs",
                "embedding_model": settings.embedding_model,
                "error": str(e),
            }

    def delete_documents(self, ids: List[str]) -> bool:
        try:
            self.vector_store.delete(ids)
            return True

        except Exception as e:
            raise Exception(f"Error deleting documents: {str(e)}")

    def clear_collection(self) -> bool:
        try:
            self.chroma_client.delete_collection("mexican_revolution_docs")
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name="mexican_revolution_docs",
                embedding_function=self.embeddings,
            )
            return True

        except Exception as e:
            raise Exception(f"Error clearing collection: {str(e)}")
