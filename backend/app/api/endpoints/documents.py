import os
import tempfile

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from ...models.schemas import DocumentUploadResponse
from ...services.document_service import DocumentService
from ...services.vector_store import VectorStoreService
from ...core.logging import logger


router = APIRouter()


def get_document_service() -> DocumentService:
    from ...main import document_service

    return document_service


def get_vector_store_service() -> VectorStoreService:
    from ...main import vector_store_service

    return vector_store_service


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    try:
        logger.info(f"Processing document upload: {file.filename}")

        if not document_service.is_supported_file(file.filename):
            logger.warning(f"Unsupported file type attempted: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {list(document_service.supported_extensions.keys())}",
            )

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            result = await document_service.process_uploaded_file(
                file_path=temp_file_path,
                filename=file.filename,
                upload_to_s3=False,
            )

            loader_chunks = len(result["documents"])
            vector_chunks = None
            if result["documents"]:
                chunk_ids = vector_store_service.add_documents(result["documents"])
                vector_chunks = len(chunk_ids)

            response = DocumentUploadResponse(
                document_id=result["document_id"],
                filename=result["filename"],
                chunks_created=result["chunks_count"],
                loader_chunks=loader_chunks,
                vector_chunks=vector_chunks,
                status=result["status"],
            )

            logger.success(
                f"Document uploaded successfully: {file.filename}, chunks: {vector_chunks}"
            )
            return response

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Error uploading document {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats")
async def get_document_stats(
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    try:
        logger.info("Retrieving document collection stats")
        stats = vector_store_service.get_collection_stats()
        logger.info(f"Document stats retrieved: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error retrieving document stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/clear")
async def clear_documents(
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    try:
        logger.warning("Clearing all documents from vector store")
        success = vector_store_service.clear_collection()
        if success:
            logger.success("All documents cleared successfully")
            return {"message": "All documents cleared successfully"}
        else:
            logger.error("Failed to clear documents")
            raise HTTPException(status_code=500, detail="Failed to clear documents")

    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/search")
async def search_documents(
    query: str,
    k: int = 3,
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    try:
        logger.info(f"Searching documents with query: '{query}', k={k}")
        results = vector_store_service.similarity_search(query, k=k)

        documents = []
        for i, doc in enumerate(results):
            documents.append(
                {
                    "id": i + 1,
                    "content": (
                        doc.page_content[:500] + "..."
                        if len(doc.page_content) > 500
                        else doc.page_content
                    ),
                    "metadata": doc.metadata,
                }
            )

        logger.info(f"Document search completed, found {len(results)} results")
        return {"query": query, "results_count": len(results), "documents": documents}

    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
