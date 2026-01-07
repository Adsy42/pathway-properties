"""
Isaacus API Client.

Wraps the Isaacus API for Universal Classification with IQL queries.
https://docs.isaacus.com/capabilities/universal-classification
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from config import get_settings

settings = get_settings()

# Track if we've already logged the API error (avoid log spam)
_api_error_logged = False


@dataclass
class ClassificationResult:
    """Result from Isaacus classification."""
    score: float  # 0.0 to 1.0, >0.5 indicates positive match
    query: str
    text_snippet: str
    is_match: bool  # True if score > 0.5
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class BatchClassificationResult:
    """Result from batch classification of multiple texts."""
    results: List[ClassificationResult]
    query: str
    match_count: int
    highest_score: float
    matched_texts: List[str]


class IsaacusClient:
    """
    Client for Isaacus Legal AI API.
    
    Supports:
    - Universal Classification with IQL queries
    - Batch processing for multiple document chunks
    - Score interpretation (>50% = positive match)
    
    IQL Query Syntax:
    - Statements: {This is a confidentiality clause.}
    - Templates: {IS confidentiality clause}
    - Template with arg: {IS clause that "waives cooling off"}
    - Operators: AND, OR, NOT, >, <, +
    
    Example:
        client = IsaacusClient()
        result = await client.classify(
            text="The purchaser waives their cooling off rights under s.66W.",
            query="{IS clause that 'waives cooling off period'}"
        )
        if result.is_match:
            print("Cooling off waiver detected!")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        self.api_key = api_key or settings.isaacus_api_key
        self._isaacus_client = None
        self._fallback_mode = False  # Set to True after first API failure
    
    @property
    def is_configured(self) -> bool:
        """Check if Isaacus API is configured."""
        return bool(self.api_key)
    
    def _get_isaacus_client(self):
        """Get or create Isaacus SDK client."""
        if self._isaacus_client is None:
            try:
                from isaacus import Isaacus
                self._isaacus_client = Isaacus(api_key=self.api_key)
            except ImportError:
                global _api_error_logged
                if not _api_error_logged:
                    print("[Isaacus] SDK not installed. Run: pip install isaacus")
                    _api_error_logged = True
                return None
        return self._isaacus_client
    
    async def close(self):
        """Close the client (no-op for SDK client)."""
        pass
    
    async def classify(
        self,
        text: str,
        query: str,
        model: str = "kanon-universal-classifier"
    ) -> ClassificationResult:
        """
        Classify a text using an IQL query.
        
        Args:
            text: The legal document text to classify
            query: IQL query (e.g., "{IS confidentiality clause}")
            model: Isaacus model to use (default: "kanon-universal-classifier")
        
        Returns:
            ClassificationResult with score and match status
        """
        global _api_error_logged
        
        # Skip API if not configured or already in fallback mode
        if not self.is_configured or self._fallback_mode:
            return self._mock_classify(text, query)
        
        try:
            from isaacus import Isaacus, APIError
            
            client = self._get_isaacus_client()
            if client is None:
                return self._mock_classify(text, query)
            
            # Use the official SDK method
            response = client.classifications.universal.create(
                model=model,
                query=query,
                texts=[text]
            )
            
            # Extract score from response (uses .classifications not .data)
            if response.classifications and len(response.classifications) > 0:
                score = response.classifications[0].score
            else:
                score = 0.0
            
            return ClassificationResult(
                score=score,
                query=query,
                text_snippet=text[:200] + "..." if len(text) > 200 else text,
                is_match=score > 0.5,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except ImportError:
            if not _api_error_logged:
                print("[Isaacus] SDK not installed. Run: pip install isaacus. Using mock fallback.")
                _api_error_logged = True
            self._fallback_mode = True
            return self._mock_classify(text, query)
        except Exception as e:
            # Only log once, then switch to fallback mode
            if not _api_error_logged:
                print(f"[Isaacus] API error (switching to mock fallback): {e}")
                _api_error_logged = True
            self._fallback_mode = True
            return self._mock_classify(text, query)
    
    async def batch_classify(
        self,
        texts: List[str],
        query: str,
        model: str = "kanon"
    ) -> BatchClassificationResult:
        """
        Classify multiple texts using the same IQL query.
        
        Args:
            texts: List of text chunks to classify
            query: IQL query to apply to all texts
            model: Isaacus model to use
        
        Returns:
            BatchClassificationResult with aggregated results
        """
        results = []
        
        for text in texts:
            result = await self.classify(text, query, model)
            results.append(result)
        
        matched_texts = [r.text_snippet for r in results if r.is_match]
        
        return BatchClassificationResult(
            results=results,
            query=query,
            match_count=sum(1 for r in results if r.is_match),
            highest_score=max(r.score for r in results) if results else 0.0,
            matched_texts=matched_texts
        )
    
    async def multi_query_classify(
        self,
        text: str,
        queries: Dict[str, str],
        model: str = "kanon"
    ) -> Dict[str, ClassificationResult]:
        """
        Run multiple IQL queries against the same text.
        
        Args:
            text: The legal document text to classify
            queries: Dict of {label: iql_query} pairs
            model: Isaacus model to use
        
        Returns:
            Dict of {label: ClassificationResult}
        """
        results = {}
        
        for label, query in queries.items():
            result = await self.classify(text, query, model)
            results[label] = result
        
        return results
    
    def _mock_classify(self, text: str, query: str) -> ClassificationResult:
        """
        Generate mock classification when API is not configured.
        Uses keyword matching as a fallback.
        """
        text_lower = text.lower()
        score = 0.0
        
        # Extract keywords from query for basic matching
        keywords = self._extract_keywords_from_query(query)
        
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            score = min(matches / len(keywords), 1.0) * 0.8  # Cap at 0.8 for mock
        
        return ClassificationResult(
            score=score,
            query=query,
            text_snippet=text[:200] + "..." if len(text) > 200 else text,
            is_match=score > 0.5,
            raw_response={"_mock": True, "keywords_matched": keywords}
        )
    
    def _extract_keywords_from_query(self, query: str) -> List[str]:
        """Extract keywords from IQL query for mock matching."""
        import re
        
        # Remove IQL syntax
        cleaned = re.sub(r'\{IS\s+', '', query)
        cleaned = re.sub(r'\{|\}', '', cleaned)
        cleaned = re.sub(r'clause that\s+', '', cleaned)
        cleaned = re.sub(r'["\']', '', cleaned)
        
        # Split into words
        words = cleaned.split()
        
        # Filter common words
        stopwords = {'the', 'a', 'an', 'is', 'that', 'which', 'or', 'and', 'of', 'to', 'in'}
        keywords = [w for w in words if w.lower() not in stopwords and len(w) > 2]
        
        return keywords


# Singleton instance
_client: Optional[IsaacusClient] = None


def get_isaacus_client() -> IsaacusClient:
    """Get singleton Isaacus client instance."""
    global _client
    if _client is None:
        _client = IsaacusClient()
    return _client


