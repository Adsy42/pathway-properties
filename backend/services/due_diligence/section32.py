"""
Section 32 Vendor Statement Completeness Checker.

Validates that a Section 32 contains all legally required components
per the Sale of Land Act 1962 (Vic). Missing components may give the
purchaser rescission rights at any time before settlement.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class ComponentCheck:
    """Result of checking a single Section 32 component."""
    component_name: str
    description: str
    required: bool
    present: bool
    risk_if_missing: RiskLevel
    consequence: str
    page_reference: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Section32CompletenessResult:
    """Complete result of Section 32 analysis."""
    is_complete: bool
    rescission_risk: bool
    missing_critical: List[ComponentCheck] = field(default_factory=list)
    missing_high: List[ComponentCheck] = field(default_factory=list)
    missing_medium: List[ComponentCheck] = field(default_factory=list)
    present_components: List[ComponentCheck] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_complete": self.is_complete,
            "rescission_risk": self.rescission_risk,
            "missing_critical": [
                {
                    "component": c.component_name,
                    "description": c.description,
                    "consequence": c.consequence,
                    "page_reference": c.page_reference
                }
                for c in self.missing_critical
            ],
            "missing_high": [
                {
                    "component": c.component_name,
                    "description": c.description,
                    "consequence": c.consequence
                }
                for c in self.missing_high
            ],
            "missing_medium": [
                {
                    "component": c.component_name,
                    "description": c.description,
                    "consequence": c.consequence
                }
                for c in self.missing_medium
            ],
            "present_components": [c.component_name for c in self.present_components],
            "recommendations": self.recommendations,
            "confidence": self.confidence
        }


# Victorian Section 32 mandatory components per Sale of Land Act 1962
SECTION_32_MANDATORY_COMPONENTS = {
    "title_documents": {
        "required": True,
        "description": "Register Search Statement (copy of title)",
        "risk_if_missing": RiskLevel.CRITICAL,
        "consequence": "Contract may be voidable - purchaser cannot verify ownership",
        "search_terms": [
            "register search statement", "certificate of title", "title search",
            "volume", "folio", "registered proprietor"
        ]
    },
    "plan_of_subdivision": {
        "required": True,
        "description": "Registered plan showing lot boundaries",
        "risk_if_missing": RiskLevel.HIGH,
        "consequence": "Cannot verify property boundaries and easements",
        "search_terms": [
            "plan of subdivision", "lot", "plan number", "boundaries",
            "PS", "LP", "TP", "CP"
        ]
    },
    "council_certificate": {
        "required": True,
        "description": "Certificate from local council (rates, orders, notices, road widening)",
        "risk_if_missing": RiskLevel.CRITICAL,
        "consequence": "May have outstanding orders or notices affecting property",
        "search_terms": [
            "council certificate", "local council", "rates", "orders",
            "building orders", "road widening", "planning"
        ]
    },
    "water_authority_certificate": {
        "required": True,
        "description": "Certificate from water authority (water rates, sewerage, drainage)",
        "risk_if_missing": RiskLevel.HIGH,
        "consequence": "Unknown water/sewer liability and connection status",
        "search_terms": [
            "water authority", "water certificate", "sewerage", "drainage",
            "melbourne water", "yarra valley", "south east water"
        ]
    },
    "owners_corp_certificate": {
        "required_if": "strata",  # Required if property_type is apartment/townhouse/unit
        "description": "Section 151 Owners Corporation Certificate",
        "risk_if_missing": RiskLevel.CRITICAL,
        "consequence": "Unknown strata liabilities, levies, or legal proceedings",
        "cost_estimate": "$175-330",
        "search_terms": [
            "owners corporation", "section 151", "OC certificate",
            "strata", "body corporate", "levies", "sinking fund"
        ]
    },
    "building_permits_7_years": {
        "required": True,
        "description": "All building permits issued in preceding 7 years",
        "risk_if_missing": RiskLevel.HIGH,
        "consequence": "Potential illegal works or non-compliant structures",
        "search_terms": [
            "building permit", "building approval", "certificate of final inspection",
            "occupancy permit", "compliance certificate"
        ]
    },
    "owner_builder_disclosure": {
        "required_if": "owner_builder",  # Required if owner-builder work in 6.5 years
        "description": "Section 137B defect report + insurance certificate",
        "risk_if_missing": RiskLevel.CRITICAL,
        "consequence": "Contract voidable, significant warranty gaps for building defects",
        "search_terms": [
            "owner builder", "section 137B", "137B", "defects report",
            "domestic building insurance", "owner built"
        ]
    },
    "growth_areas_certificate": {
        "required_if": "growth_area",  # Required if property in growth area
        "description": "Growth Areas Infrastructure Contribution (GAIC) certificate",
        "risk_if_missing": RiskLevel.MEDIUM,
        "consequence": "Potential infrastructure levy of $100,000+ on development",
        "search_terms": [
            "growth areas", "GAIC", "infrastructure contribution",
            "growth area infrastructure"
        ]
    },
    "vendor_statement_form": {
        "required": True,
        "description": "Completed vendor statement form with required warranties",
        "risk_if_missing": RiskLevel.CRITICAL,
        "consequence": "Contract may be voidable without proper vendor disclosure",
        "search_terms": [
            "vendor statement", "section 32", "vendor's statement",
            "sale of land act"
        ]
    },
    "land_information": {
        "required": True,
        "description": "Details of the land being sold (address, lot, plan)",
        "risk_if_missing": RiskLevel.CRITICAL,
        "consequence": "Cannot identify the subject property",
        "search_terms": [
            "property address", "land description", "lot on plan",
            "crown allotment"
        ]
    },
    "zoning_information": {
        "required": True,
        "description": "Current zoning and any overlays affecting the property",
        "risk_if_missing": RiskLevel.HIGH,
        "consequence": "Unknown development restrictions or planning controls",
        "search_terms": [
            "zoning", "planning scheme", "overlay", "heritage",
            "flood", "bushfire", "NRZ", "GRZ", "RGZ"
        ]
    },
    "outgoings_disclosure": {
        "required": True,
        "description": "Annual outgoings (rates, taxes, charges)",
        "risk_if_missing": RiskLevel.MEDIUM,
        "consequence": "Cannot accurately assess holding costs",
        "search_terms": [
            "outgoings", "annual rates", "council rates", "water rates",
            "land tax"
        ]
    },
    "services_disclosure": {
        "required": True,
        "description": "Details of services connected to the property",
        "risk_if_missing": RiskLevel.MEDIUM,
        "consequence": "Unknown service connections and costs",
        "search_terms": [
            "services", "electricity", "gas", "water connected",
            "sewerage connected", "telephone"
        ]
    },
    "insurance_disclosure": {
        "required_if": "strata",
        "description": "Building insurance details for strata properties",
        "risk_if_missing": RiskLevel.HIGH,
        "consequence": "Unknown insurance coverage and potential exclusions",
        "search_terms": [
            "building insurance", "strata insurance", "sum insured",
            "public liability"
        ]
    }
}


class Section32CompletenessAnalyzer:
    """
    Validates Section 32 contains all legally required components.
    Missing components = rescission rights for purchaser.
    """

    def __init__(self):
        self.components = SECTION_32_MANDATORY_COMPONENTS

    def analyze(
        self,
        section_32_text: str,
        property_context: Dict[str, Any]
    ) -> Section32CompletenessResult:
        """
        Analyze Section 32 for completeness.

        Args:
            section_32_text: Full text content of Section 32 document
            property_context: Dict with keys:
                - property_type: 'house', 'apartment', 'townhouse', 'unit'
                - owner_builder_work_detected: bool
                - in_growth_area: bool (optional)

        Returns:
            Section32CompletenessResult with completeness assessment
        """
        result = Section32CompletenessResult(
            is_complete=True,
            rescission_risk=False
        )

        text_lower = section_32_text.lower()
        property_type = property_context.get("property_type", "house")
        is_strata = property_type in ["apartment", "townhouse", "unit"]
        is_owner_builder = property_context.get("owner_builder_work_detected", False)
        in_growth_area = property_context.get("in_growth_area", False)

        for component_name, config in self.components.items():
            # Check if required based on property context
            if not self._is_required(config, is_strata, is_owner_builder, in_growth_area):
                continue

            # Check if component is present
            present = self._component_present(text_lower, config["search_terms"])

            check = ComponentCheck(
                component_name=component_name,
                description=config["description"],
                required=True,
                present=present,
                risk_if_missing=config["risk_if_missing"],
                consequence=config["consequence"]
            )

            if present:
                result.present_components.append(check)
            else:
                risk_level = config["risk_if_missing"]

                if risk_level == RiskLevel.CRITICAL:
                    result.missing_critical.append(check)
                    result.rescission_risk = True
                    result.is_complete = False
                elif risk_level == RiskLevel.HIGH:
                    result.missing_high.append(check)
                    result.is_complete = False
                elif risk_level == RiskLevel.MEDIUM:
                    result.missing_medium.append(check)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, property_context)

        # Calculate confidence based on how thorough the check was
        total_required = len(result.present_components) + len(result.missing_critical) + \
                        len(result.missing_high) + len(result.missing_medium)
        if total_required > 0:
            result.confidence = len(result.present_components) / total_required

        return result

    def _is_required(
        self,
        config: Dict[str, Any],
        is_strata: bool,
        is_owner_builder: bool,
        in_growth_area: bool
    ) -> bool:
        """Determine if a component is required based on property context."""
        required = config.get("required", False)
        required_if = config.get("required_if")

        if required:
            return True

        if required_if == "strata" and is_strata:
            return True
        if required_if == "owner_builder" and is_owner_builder:
            return True
        if required_if == "growth_area" and in_growth_area:
            return True

        return False

    def _component_present(
        self,
        text_lower: str,
        search_terms: List[str]
    ) -> bool:
        """Check if component is present based on search terms."""
        # Component is present if at least 2 search terms are found
        # (to reduce false positives)
        matches = sum(1 for term in search_terms if term in text_lower)
        return matches >= 2

    def _generate_recommendations(
        self,
        result: Section32CompletenessResult,
        property_context: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        if result.rescission_risk:
            recommendations.append(
                "CRITICAL: Section 32 is incomplete. You may have rescission rights. "
                "Consult conveyancer immediately before signing contract."
            )

        if result.missing_critical:
            missing_names = [c.component_name for c in result.missing_critical]
            recommendations.append(
                f"Request the following critical documents from vendor: {', '.join(missing_names)}"
            )

        if result.missing_high:
            missing_names = [c.component_name for c in result.missing_high]
            recommendations.append(
                f"The following important documents appear missing: {', '.join(missing_names)}. "
                "Request copies before exchange."
            )

        # Specific recommendations based on missing components
        for missing in result.missing_critical + result.missing_high:
            if missing.component_name == "owners_corp_certificate":
                recommendations.append(
                    "Request Section 151 OC Certificate (cost ~$175-330). "
                    "This reveals special levies, litigation, and cladding issues."
                )
            elif missing.component_name == "owner_builder_disclosure":
                recommendations.append(
                    "URGENT: Owner-builder disclosure missing. Request s.137B defect report. "
                    "You have 7 years warranty rights for structural defects."
                )
            elif missing.component_name == "building_permits_7_years":
                recommendations.append(
                    "Request building permit history from council. "
                    "Check for missing Certificates of Final Inspection."
                )

        if not recommendations:
            recommendations.append(
                "Section 32 appears complete. Have conveyancer confirm all attachments."
            )

        return recommendations

    async def analyze_with_rag(
        self,
        property_id: str,
        property_context: Dict[str, Any]
    ) -> Section32CompletenessResult:
        """
        Analyze Section 32 using RAG queries for more accurate detection.

        This method queries the document store for each component,
        providing higher confidence results than text search alone.
        """
        from services.documents.rag import query_property_documents

        result = Section32CompletenessResult(
            is_complete=True,
            rescission_risk=False
        )

        property_type = property_context.get("property_type", "house")
        is_strata = property_type in ["apartment", "townhouse", "unit"]
        is_owner_builder = property_context.get("owner_builder_work_detected", False)
        in_growth_area = property_context.get("in_growth_area", False)

        # Query for each required component
        for component_name, config in self.components.items():
            if not self._is_required(config, is_strata, is_owner_builder, in_growth_area):
                continue

            # Build RAG query for this component
            query = f"Does this Section 32 contain {config['description']}? " \
                   f"Look for: {', '.join(config['search_terms'][:5])}"

            rag_result = await query_property_documents(
                property_id=property_id,
                question=query
            )

            # Analyze RAG response
            answer = rag_result.get("answer", "").lower()
            confidence = rag_result.get("confidence", 0.5)

            # Determine if component is present based on answer
            present = self._interpret_rag_answer(answer, confidence)

            check = ComponentCheck(
                component_name=component_name,
                description=config["description"],
                required=True,
                present=present,
                risk_if_missing=config["risk_if_missing"],
                consequence=config["consequence"],
                page_reference=self._extract_page_reference(rag_result.get("sources", []))
            )

            if present:
                result.present_components.append(check)
            else:
                risk_level = config["risk_if_missing"]

                if risk_level == RiskLevel.CRITICAL:
                    result.missing_critical.append(check)
                    result.rescission_risk = True
                    result.is_complete = False
                elif risk_level == RiskLevel.HIGH:
                    result.missing_high.append(check)
                    result.is_complete = False
                elif risk_level == RiskLevel.MEDIUM:
                    result.missing_medium.append(check)

        result.recommendations = self._generate_recommendations(result, property_context)

        total_required = len(result.present_components) + len(result.missing_critical) + \
                        len(result.missing_high) + len(result.missing_medium)
        if total_required > 0:
            result.confidence = len(result.present_components) / total_required

        return result

    def _interpret_rag_answer(self, answer: str, confidence: float) -> bool:
        """Interpret RAG answer to determine if component is present."""
        positive_indicators = ["yes", "contains", "includes", "present", "found", "attached"]
        negative_indicators = ["no", "not found", "missing", "absent", "not included", "does not"]

        for indicator in negative_indicators:
            if indicator in answer:
                return False

        for indicator in positive_indicators:
            if indicator in answer and confidence > 0.6:
                return True

        return confidence > 0.7

    def _extract_page_reference(self, sources: List[Dict]) -> Optional[str]:
        """Extract page reference from RAG sources."""
        if sources:
            pages = [str(s.get("page", "?")) for s in sources[:3]]
            return f"Pages: {', '.join(pages)}"
        return None


# Convenience function for quick checks
def check_section32_completeness(
    text: str,
    property_type: str = "house",
    owner_builder: bool = False
) -> Dict[str, Any]:
    """
    Quick check of Section 32 completeness.

    Args:
        text: Section 32 document text
        property_type: Type of property
        owner_builder: Whether owner-builder work detected

    Returns:
        Dict with completeness results
    """
    analyzer = Section32CompletenessAnalyzer()
    result = analyzer.analyze(
        section_32_text=text,
        property_context={
            "property_type": property_type,
            "owner_builder_work_detected": owner_builder
        }
    )
    return result.to_dict()
