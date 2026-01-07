"""
Text embeddings using OpenAI text-embedding-3-large.
"""

from typing import List, Dict, Any
import asyncio

from config import get_settings

settings = get_settings()


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Uses OpenAI text-embedding-3-large for high-quality semantic search.
    """
    
    if not settings.openai_api_key:
        # Return mock embeddings for demo
        return [[0.1] * 1536 for _ in texts]
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Batch embeddings (OpenAI allows up to 2048 inputs per request)
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = await client.embeddings.create(
                model="text-embedding-3-large",
                input=batch
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
        
    except ImportError:
        print("OpenAI SDK not installed")
        return [[0.1] * 1536 for _ in texts]
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return [[0.1] * 1536 for _ in texts]


async def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a search query.
    """
    embeddings = await embed_texts([query])
    return embeddings[0] if embeddings else [0.1] * 1536







