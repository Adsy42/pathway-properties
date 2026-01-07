"""
RAG (Retrieval-Augmented Generation) for document Q&A.
Uses OpenAI GPT-4o for reasoning over retrieved context.
"""

from typing import Dict, Any, List, Optional

from config import get_settings
from services.documents.vector_store import search_documents

settings = get_settings()


async def query_document_rag(
    document_id: str,
    property_id: str,
    question: str
) -> Dict[str, Any]:
    """
    Answer a question about a specific document using RAG.
    
    1. Retrieve relevant chunks from vector store
    2. Format context for LLM
    3. Query LLM with context + question
    4. Extract answer with citations
    """
    
    # Retrieve relevant chunks
    chunks = await search_documents(
        query=question,
        property_id=property_id,
        document_id=document_id,
        n_results=5
    )
    
    if not chunks:
        return {
            "answer": "No relevant information found in the document.",
            "sources": [],
            "confidence": 0.0
        }
    
    # Format context
    context = format_context(chunks)
    
    # Query LLM
    answer, sources, confidence = await query_llm(question, context, chunks)
    
    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence
    }


async def query_property_documents(
    property_id: str,
    question: str,
    document_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Answer a question across all documents for a property.
    """
    
    # Search across all documents
    chunks = await search_documents(
        query=question,
        property_id=property_id,
        n_results=10
    )
    
    # Optionally filter by document type
    if document_types:
        chunks = [c for c in chunks if c.get("metadata", {}).get("document_type") in document_types]
    
    if not chunks:
        return {
            "answer": "No relevant information found in the documents.",
            "sources": [],
            "confidence": 0.0
        }
    
    context = format_context(chunks)
    answer, sources, confidence = await query_llm(question, context, chunks)
    
    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence
    }


def format_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks as context for LLM."""
    
    context_parts = []
    
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        text = chunk.get("text", "")
        
        section = metadata.get("section", "Unknown Section")
        page_start = metadata.get("page_start", "?")
        page_end = metadata.get("page_end", "?")
        doc_type = metadata.get("document_type", "Document")
        
        if page_start == page_end:
            page_ref = f"Page {page_start}"
        else:
            page_ref = f"Pages {page_start}-{page_end}"
        
        context_parts.append(
            f"[Source {i}] {doc_type} - {section} ({page_ref}):\n{text}"
        )
    
    return "\n\n---\n\n".join(context_parts)


async def query_llm(
    question: str,
    context: str,
    chunks: List[Dict[str, Any]]
) -> tuple[str, List[Dict[str, Any]], float]:
    """
    Query LLM with context and question.
    Returns (answer, sources, confidence).
    """
    
    prompt = f"""You are a senior Australian property conveyancer analyzing legal documents.

Based ONLY on the provided context, answer the following question. 
If the information is not in the context, say "NOT FOUND in the provided documents."
Always cite the source number [Source X] for every claim you make.

CONTEXT:
{context}

QUESTION:
{question}

Provide a clear, concise answer with citations. Format:
ANSWER: [Your answer with [Source X] citations]
CONFIDENCE: [HIGH/MEDIUM/LOW based on how clearly the context answers the question]"""
    
    if settings.openai_api_key:
        return await query_openai(prompt, chunks)
    else:
        # Mock response for demo
        return mock_llm_response(question, chunks)


async def query_openai(
    prompt: str,
    chunks: List[Dict[str, Any]]
) -> tuple[str, List[Dict[str, Any]], float]:
    """Query OpenAI GPT-4."""
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024
        )
        
        answer_text = response.choices[0].message.content
        
        answer, confidence = parse_llm_response(answer_text)
        sources = extract_cited_sources(answer, chunks)
        
        return answer, sources, confidence
        
    except Exception as e:
        print(f"OpenAI query failed: {e}")
        return mock_llm_response("", chunks)


def parse_llm_response(response: str) -> tuple[str, float]:
    """Parse LLM response to extract answer and confidence."""
    
    answer = response
    confidence = 0.7  # Default medium
    
    # Try to extract structured parts
    if "ANSWER:" in response:
        parts = response.split("ANSWER:", 1)
        answer = parts[1].strip()
        
        if "CONFIDENCE:" in answer:
            answer_parts = answer.split("CONFIDENCE:", 1)
            answer = answer_parts[0].strip()
            conf_text = answer_parts[1].strip().upper()
            
            if "HIGH" in conf_text:
                confidence = 0.9
            elif "LOW" in conf_text:
                confidence = 0.4
            else:
                confidence = 0.7
    
    return answer, confidence


def extract_cited_sources(
    answer: str,
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Extract cited sources from answer."""
    
    import re
    
    sources = []
    cited_nums = set(re.findall(r'\[Source (\d+)\]', answer))
    
    for num_str in cited_nums:
        num = int(num_str)
        if 1 <= num <= len(chunks):
            chunk = chunks[num - 1]
            metadata = chunk.get("metadata", {})
            sources.append({
                "source_num": num,
                "page": metadata.get("page_start", 1),
                "section": metadata.get("section", ""),
                "text": chunk.get("text", "")[:200] + "..."
            })
    
    return sources


def mock_llm_response(
    question: str,
    chunks: List[Dict[str, Any]]
) -> tuple[str, List[Dict[str, Any]], float]:
    """Mock LLM response for demo."""
    
    if chunks:
        chunk = chunks[0]
        text_preview = chunk.get("text", "")[:100]
        return (
            f"[MOCK] Based on the document [Source 1], the relevant information is: '{text_preview}...'",
            [{
                "source_num": 1,
                "page": chunk.get("metadata", {}).get("page_start", 1),
                "section": chunk.get("metadata", {}).get("section", ""),
                "text": chunk.get("text", "")[:200]
            }],
            0.5
        )
    
    return ("No relevant information found.", [], 0.0)

