"""
Legal Clause Classifier using Isaacus IQL.

Provides high-level classification functions for property law documents.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from services.isaacus.client import (
    IsaacusClient, 
    ClassificationResult, 
    BatchClassificationResult,
    get_isaacus_client
)
from services.isaacus.iql_templates import IQLTemplates, IQLTemplate


@dataclass
class ClauseMatch:
    """A detected clause match with context."""
    template_name: str
    template_description: str
    risk_level: str
    score: float
    is_match: bool
    text_snippet: str
    category: str
    page_reference: Optional[str] = None


@dataclass
class DocumentClassification:
    """Complete classification result for a legal document."""
    document_type: str
    total_chunks_analyzed: int
    high_risk_matches: List[ClauseMatch] = field(default_factory=list)
    medium_risk_matches: List[ClauseMatch] = field(default_factory=list)
    low_risk_matches: List[ClauseMatch] = field(default_factory=list)
    info_matches: List[ClauseMatch] = field(default_factory=list)
    all_matches: List[ClauseMatch] = field(default_factory=list)
    
    # Specific flags
    cooling_off_waived: bool = False
    has_high_risk_clauses: bool = False
    as_is_condition: bool = False
    early_deposit_release: bool = False
    owner_builder_works: bool = False
    missing_final_inspection: bool = False
    
    def get_risk_summary(self) -> Dict[str, int]:
        """Get count of matches by risk level."""
        return {
            "HIGH": len(self.high_risk_matches),
            "MEDIUM": len(self.medium_risk_matches),
            "LOW": len(self.low_risk_matches),
            "INFO": len(self.info_matches)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "document_type": self.document_type,
            "total_chunks_analyzed": self.total_chunks_analyzed,
            "risk_summary": self.get_risk_summary(),
            "high_risk_matches": [
                {
                    "clause_type": m.template_name,
                    "description": m.template_description,
                    "confidence": m.score,
                    "text_preview": m.text_snippet
                }
                for m in self.high_risk_matches
            ],
            "flags": {
                "cooling_off_waived": self.cooling_off_waived,
                "has_high_risk_clauses": self.has_high_risk_clauses,
                "as_is_condition": self.as_is_condition,
                "early_deposit_release": self.early_deposit_release,
                "owner_builder_works": self.owner_builder_works,
                "missing_final_inspection": self.missing_final_inspection
            }
        }


class LegalClauseClassifier:
    """
    High-level classifier for legal documents using Isaacus IQL.
    
    Example usage:
        classifier = LegalClauseClassifier()
        
        # Classify a Section 32
        result = await classifier.classify_section32(chunks)
        
        if result.cooling_off_waived:
            print("WARNING: Cooling off period has been waived!")
        
        for match in result.high_risk_matches:
            print(f"HIGH RISK: {match.template_description}")
    """
    
    def __init__(self, client: Optional[IsaacusClient] = None):
        self.client = client or get_isaacus_client()
    
    async def classify_chunk(
        self,
        text: str,
        templates: List[IQLTemplate],
        page_reference: Optional[str] = None
    ) -> List[ClauseMatch]:
        """
        Classify a single text chunk against multiple templates.
        
        Args:
            text: Document text chunk
            templates: List of IQL templates to check
            page_reference: Optional page reference for context
        
        Returns:
            List of ClauseMatch for templates that matched
        """
        matches = []
        
        for template in templates:
            result = await self.client.classify(text, template.query)
            
            if result.is_match:
                matches.append(ClauseMatch(
                    template_name=template.name,
                    template_description=template.description,
                    risk_level=template.risk_level,
                    score=result.score,
                    is_match=True,
                    text_snippet=result.text_snippet,
                    category=template.category,
                    page_reference=page_reference
                ))
        
        return matches
    
    async def classify_section32(
        self,
        chunks: List[Dict[str, Any]],
        include_info_level: bool = False
    ) -> DocumentClassification:
        """
        Classify a Section 32 Vendor Statement (Victoria).
        
        Args:
            chunks: List of document chunks with 'text' and optional 'section', 'page_start'
            include_info_level: Whether to include INFO-level matches
        
        Returns:
            DocumentClassification with all detected clauses
        """
        templates = IQLTemplates.get_section32_templates()
        
        if not include_info_level:
            templates = [t for t in templates if t.risk_level != "INFO"]
        
        classification = DocumentClassification(
            document_type="Section 32 Vendor Statement (VIC)",
            total_chunks_analyzed=len(chunks)
        )
        
        for chunk in chunks:
            text = chunk.get("text", "")
            if not text.strip():
                continue
            
            page_ref = f"Page {chunk.get('page_start', '?')}"
            if chunk.get('section'):
                page_ref = f"{chunk.get('section')} ({page_ref})"
            
            matches = await self.classify_chunk(text, templates, page_ref)
            
            for match in matches:
                classification.all_matches.append(match)
                
                if match.risk_level == "HIGH":
                    classification.high_risk_matches.append(match)
                    classification.has_high_risk_clauses = True
                    
                    # Set specific flags
                    if match.template_name in ["cooling_off_waiver", "section_66w_waiver"]:
                        classification.cooling_off_waived = True
                    elif match.template_name == "as_is_condition":
                        classification.as_is_condition = True
                    elif match.template_name == "early_release_deposit":
                        classification.early_deposit_release = True
                    elif match.template_name == "no_final_inspection":
                        classification.missing_final_inspection = True
                        
                elif match.risk_level == "MEDIUM":
                    classification.medium_risk_matches.append(match)
                    
                    if match.template_name == "owner_builder":
                        classification.owner_builder_works = True
                        
                elif match.risk_level == "LOW":
                    classification.low_risk_matches.append(match)
                else:
                    classification.info_matches.append(match)
        
        return classification
    
    async def classify_contract_nsw(
        self,
        chunks: List[Dict[str, Any]],
        include_info_level: bool = False
    ) -> DocumentClassification:
        """
        Classify a NSW Contract for Sale.
        Similar to Section 32 but with NSW-specific considerations.
        """
        # Use same templates - NSW contracts have similar clause types
        templates = IQLTemplates.get_section32_templates()
        
        if not include_info_level:
            templates = [t for t in templates if t.risk_level != "INFO"]
        
        classification = DocumentClassification(
            document_type="Contract for Sale (NSW)",
            total_chunks_analyzed=len(chunks)
        )
        
        for chunk in chunks:
            text = chunk.get("text", "")
            if not text.strip():
                continue
            
            page_ref = f"Page {chunk.get('page_start', '?')}"
            matches = await self.classify_chunk(text, templates, page_ref)
            
            for match in matches:
                classification.all_matches.append(match)
                
                if match.risk_level == "HIGH":
                    classification.high_risk_matches.append(match)
                    classification.has_high_risk_clauses = True
                    
                    if match.template_name in ["cooling_off_waiver"]:
                        classification.cooling_off_waived = True
                    elif match.template_name == "as_is_condition":
                        classification.as_is_condition = True
                        
                elif match.risk_level == "MEDIUM":
                    classification.medium_risk_matches.append(match)
                elif match.risk_level == "LOW":
                    classification.low_risk_matches.append(match)
                else:
                    classification.info_matches.append(match)
        
        return classification
    
    async def classify_strata(
        self,
        chunks: List[Dict[str, Any]]
    ) -> DocumentClassification:
        """
        Classify a Strata Report or OC Minutes.
        """
        templates = IQLTemplates.get_strata_templates()
        
        classification = DocumentClassification(
            document_type="Strata Report / OC Certificate",
            total_chunks_analyzed=len(chunks)
        )
        
        for chunk in chunks:
            text = chunk.get("text", "")
            if not text.strip():
                continue
            
            page_ref = f"Page {chunk.get('page_start', '?')}"
            matches = await self.classify_chunk(text, templates, page_ref)
            
            for match in matches:
                classification.all_matches.append(match)
                
                if match.risk_level == "HIGH":
                    classification.high_risk_matches.append(match)
                    classification.has_high_risk_clauses = True
                elif match.risk_level == "MEDIUM":
                    classification.medium_risk_matches.append(match)
                elif match.risk_level == "LOW":
                    classification.low_risk_matches.append(match)
                else:
                    classification.info_matches.append(match)
        
        return classification
    
    async def quick_risk_scan(
        self,
        text: str
    ) -> Dict[str, bool]:
        """
        Quick scan for high-risk clauses in a single text.
        
        Returns dict of risk flags.
        """
        high_risk_templates = IQLTemplates.get_high_risk_templates()
        
        flags = {}
        
        for template in high_risk_templates:
            result = await self.client.classify(text, template.query)
            flags[template.name] = result.is_match
        
        return flags
    
    async def detect_cooling_off_waiver(self, text: str) -> bool:
        """Check if text contains cooling-off waiver."""
        result = await self.client.classify(
            text, 
            IQLTemplates.COOLING_OFF_WAIVER.query
        )
        return result.is_match
    
    async def detect_as_is_condition(self, text: str) -> bool:
        """Check if text contains as-is/where-is condition."""
        result = await self.client.classify(
            text,
            IQLTemplates.AS_IS_CONDITION.query
        )
        return result.is_match
    
    async def detect_encumbrances(self, text: str) -> Dict[str, bool]:
        """Check for various encumbrance types."""
        templates = IQLTemplates.get_by_category("encumbrances")
        
        results = {}
        for template in templates:
            result = await self.client.classify(text, template.query)
            results[template.name] = result.is_match
        
        return results


# Singleton classifier
_classifier: Optional[LegalClauseClassifier] = None


def get_legal_classifier() -> LegalClauseClassifier:
    """Get singleton classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = LegalClauseClassifier()
    return _classifier




