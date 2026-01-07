"""
Vector store for document embeddings using Chroma (local) or Pinecone.
"""

from typing import List, Dict, Any, Optional
import os

# Disable ChromaDB telemetry to avoid spam errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from config import get_settings
from services.documents.chunking import chunk_document
from services.documents.embeddings import embed_texts, embed_query

settings = get_settings()


class VectorStore:
    """Abstract vector store interface."""
    
    async def upsert(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        texts: List[str]
    ) -> None:
        raise NotImplementedError
    
    async def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    async def delete(self, ids: List[str]) -> None:
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    """Local Chroma vector store."""
    
    def __init__(self):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        self.client = chromadb.Client(ChromaSettings(
            persist_directory=settings.chroma_persist_dir,
            anonymized_telemetry=False
        ))
        
        self.collection = self.client.get_or_create_collection(
            name="pathway_documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    async def upsert(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        texts: List[str]
    ) -> None:
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
    
    async def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter
        )
        
        # Format results
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0
                })
        
        return formatted
    
    async def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)


# Singleton instance
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get vector store instance."""
    global _store
    if _store is None:
        if settings.vector_db == "chroma":
            _store = ChromaVectorStore()
        else:
            # Default to Chroma for local development
            _store = ChromaVectorStore()
    return _store


async def embed_document(
    document_id: str,
    property_id: str,
    document_type: str,
    ocr_result: Dict[str, Any]
) -> None:
    """
    Chunk, embed, and store a document in the vector store.
    """
    
    # Chunk the document
    chunks = chunk_document(ocr_result, document_type)
    
    if not chunks:
        print(f"No chunks generated for document {document_id}")
        return
    
    # Generate embeddings
    texts = [chunk["text"] for chunk in chunks]
    embeddings = await embed_texts(texts)
    
    # Prepare for storage
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "property_id": property_id,
            "document_type": document_type,
            "section": chunk.get("section", ""),
            "page_start": chunk.get("page_start", 1),
            "page_end": chunk.get("page_end", 1),
            "chunk_type": chunk.get("chunk_type", "generic")
        }
        for chunk in chunks
    ]
    
    # Store in vector store
    store = get_vector_store()
    await store.upsert(ids, embeddings, metadatas, texts)
    
    print(f"Stored {len(chunks)} chunks for document {document_id}")


async def search_documents(
    query: str,
    property_id: str,
    document_id: Optional[str] = None,
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for relevant document chunks.
    """
    
    # Generate query embedding
    query_embedding = await embed_query(query)
    
    # Build filter using ChromaDB's $and operator for multiple conditions
    conditions = [{"property_id": {"$eq": property_id}}]
    if document_id:
        conditions.append({"document_id": {"$eq": document_id}})
    
    filter_dict = {"$and": conditions} if len(conditions) > 1 else {"property_id": {"$eq": property_id}}
    
    # Search
    store = get_vector_store()
    results = await store.query(
        query_embedding=query_embedding,
        n_results=n_results,
        filter=filter_dict
    )
    
    return results


async def get_document_chunks(
    property_id: str,
    document_type: Optional[str] = None,
    document_id: Optional[str] = None,
    max_chunks: int = 100
) -> List[Dict[str, Any]]:
    """
    Get all chunks for a document or document type (for Isaacus classification).
    
    Unlike search_documents which uses semantic search, this retrieves all
    chunks matching the filter criteria for comprehensive classification.
    
    Args:
        property_id: The property ID
        document_type: Optional document type filter (e.g., "Section 32 Vendor Statement (VIC)")
        document_id: Optional specific document ID
        max_chunks: Maximum number of chunks to retrieve
    
    Returns:
        List of chunk dicts with 'text', 'section', 'page_start', etc.
    """
    store = get_vector_store()
    
    # For Chroma, we can use the get method if we know the IDs
    # But since we don't, we'll use a semantic search with a generic query
    # and retrieve many results. This is a workaround for Chroma's limitations.
    
    # Use a very generic query to get all related chunks
    generic_query = "legal document clause contract property"
    query_embedding = await embed_query(generic_query)
    
    # Build filter using ChromaDB's $and operator for multiple conditions
    conditions = [{"property_id": {"$eq": property_id}}]
    if document_type:
        conditions.append({"document_type": {"$eq": document_type}})
    if document_id:
        conditions.append({"document_id": {"$eq": document_id}})
    
    filter_dict = {"$and": conditions} if len(conditions) > 1 else {"property_id": {"$eq": property_id}}
    
    # Get chunks - request more than needed and deduplicate
    try:
        results = await store.query(
            query_embedding=query_embedding,
            n_results=max_chunks,
            filter=filter_dict
        )
        
        # Convert to chunk format expected by Isaacus classifier
        chunks = []
        seen_texts = set()
        
        for result in results:
            text = result.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                chunks.append({
                    "text": text,
                    "section": result.get("metadata", {}).get("section", ""),
                    "page_start": result.get("metadata", {}).get("page_start", 1),
                    "page_end": result.get("metadata", {}).get("page_end", 1),
                    "chunk_type": result.get("metadata", {}).get("chunk_type", "generic"),
                    "document_id": result.get("metadata", {}).get("document_id", "")
                })
        
        return chunks
        
    except Exception as e:
        print(f"Error getting document chunks: {e}")
        return []




