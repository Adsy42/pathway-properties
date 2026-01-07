"""
Special Conditions Analyzer for Property Contracts.

Detects and analyzes special conditions in Victorian Section 32s
and NSW Contracts for Sale. Extracts key fields and assesses risk.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import date


class ConditionType(str, Enum):
    SUBJECT_TO_FINANCE = "subject_to_finance"
    SUBJECT_TO_BUILDING_INSPECTION = "subject_to_building_inspection"
    SUBJECT_TO_PEST_INSPECTION = "subject_to_pest_inspection"
    SUBJECT_TO_SALE = "subject_to_sale"
    EARLY_DEPOSIT_RELEASE = "early_deposit_release"
    AS_IS_WHERE_IS = "as_is_where_is"
    VENDOR_WARRANTY_EXCLUSION = "vendor_warranty_exclusion"
    SUNSET_CLAUSE = "sunset_clause"
    NOMINATION_CLAUSE = "nomination_clause"
    GST_CLAUSE = "gst_clause"
    SETTLEMENT_EXTENSION = "settlement_extension"
    FIXTURES_EXCLUSION = "fixtures_exclusion"
    TENANT_IN_OCCUPATION = "tenant_in_occupation"
    DELAYED_POSSESSION = "delayed_possession"
    BUILDING_WORKS_CONDITION = "building_works_condition"
    POOL_COMPLIANCE = "pool_compliance"
    OTHER = "other"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    BENEFICIAL = "BENEFICIAL"  # Conditions that benefit purchaser


@dataclass
class ExtractedCondition:
    """A detected special condition with extracted details."""
    condition_type: ConditionType
    text: str
    risk_level: RiskLevel
    description: str
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[date] = None
    financial_impact: Optional[float] = None
    consequence: str = ""
    mitigation: str = ""
    page_reference: Optional[str] = None
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_type": self.condition_type.value,
            "text_preview": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "extracted_fields": self.extracted_fields,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "financial_impact": self.financial_impact,
            "consequence": self.consequence,
            "mitigation": self.mitigation,
            "page_reference": self.page_reference,
            "confidence": self.confidence
        }


@dataclass
class SpecialConditionsResult:
    """Result of special conditions analysis."""
    conditions_found: List[ExtractedCondition] = field(default_factory=list)
    critical_conditions: List[ExtractedCondition] = field(default_factory=list)
    protective_conditions_present: Dict[str, bool] = field(default_factory=dict)
    missing_protections: List[str] = field(default_factory=list)
    total_risk_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conditions_found": [c.to_dict() for c in self.conditions_found],
            "critical_conditions": [c.to_dict() for c in self.critical_conditions],
            "protective_conditions_present": self.protective_conditions_present,
            "missing_protections": self.missing_protections,
            "total_risk_score": self.total_risk_score,
            "recommendations": self.recommendations,
            "summary": self.summary
        }


# Detection patterns for special conditions
SPECIAL_CONDITIONS_CONFIG = {
    ConditionType.SUBJECT_TO_FINANCE: {
        "search_terms": [
            "subject to finance", "conditional on finance", "finance approval",
            "loan approval", "mortgage approval", "conditional upon the purchaser obtaining"
        ],
        "extract_fields": ["lender_name", "loan_amount", "approval_deadline"],
        "risk_level": RiskLevel.BENEFICIAL,
        "description": "Purchase conditional on finance approval",
        "consequence": "If condition present, can exit if finance not approved",
        "typical_period": "14-21 days",
        "if_absent": "Purchase is unconditional - full deposit at risk if finance fails"
    },
    ConditionType.SUBJECT_TO_BUILDING_INSPECTION: {
        "search_terms": [
            "subject to building inspection", "satisfactory building inspection",
            "building and pest", "structural inspection", "conditional on inspection"
        ],
        "extract_fields": ["inspection_deadline", "defect_threshold"],
        "risk_level": RiskLevel.BENEFICIAL,
        "description": "Purchase conditional on satisfactory building inspection",
        "consequence": "Can exit if major defects found",
        "typical_period": "7-14 days",
        "if_absent": "Cannot terminate for defects discovered post-contract"
    },
    ConditionType.SUBJECT_TO_PEST_INSPECTION: {
        "search_terms": [
            "subject to pest inspection", "pest and termite", "termite inspection",
            "satisfactory pest"
        ],
        "extract_fields": ["inspection_deadline"],
        "risk_level": RiskLevel.BENEFICIAL,
        "description": "Purchase conditional on pest inspection",
        "consequence": "Can exit if pest damage found",
        "if_absent": "Termite damage discovered post-contract = your problem"
    },
    ConditionType.SUBJECT_TO_SALE: {
        "search_terms": [
            "subject to sale", "conditional on sale", "purchaser's property",
            "sale of purchaser"
        ],
        "extract_fields": ["property_to_sell", "sale_deadline"],
        "risk_level": RiskLevel.MEDIUM,
        "description": "Purchase conditional on sale of another property",
        "consequence": "Must sell existing property to proceed",
        "vendor_perspective": "Risky for vendor - may reject or request sunset clause"
    },
    ConditionType.EARLY_DEPOSIT_RELEASE: {
        "search_terms": [
            "early release", "release of deposit", "deposit to be released",
            "deposit released to vendor", "stakeholder to release"
        ],
        "extract_fields": ["release_conditions", "release_date"],
        "risk_level": RiskLevel.HIGH,
        "description": "Deposit may be released to vendor before settlement",
        "consequence": "If settlement fails, deposit harder to recover - must sue vendor",
        "mitigation": "Negotiate removal or ensure vendor's financial stability verified"
    },
    ConditionType.AS_IS_WHERE_IS: {
        "search_terms": [
            "as is", "where is", "current condition", "present state",
            "no warranty as to condition", "sold as inspected"
        ],
        "risk_level": RiskLevel.HIGH,
        "description": "Property sold in current condition with no warranties",
        "consequence": "No recourse for undisclosed defects - inspection critical",
        "mitigation": "Thorough building and pest inspection essential before exchange"
    },
    ConditionType.VENDOR_WARRANTY_EXCLUSION: {
        "search_terms": [
            "excludes all warranties", "no warranty", "warranty is excluded",
            "vendor makes no representation", "purchaser acknowledges"
        ],
        "risk_level": RiskLevel.HIGH,
        "description": "Vendor warranties excluded or limited",
        "consequence": "Limited recourse for defects or misrepresentation",
        "mitigation": "Independent due diligence critical"
    },
    ConditionType.SUNSET_CLAUSE: {
        "search_terms": [
            "sunset date", "sunset clause", "rescission date",
            "contract terminates if", "either party may rescind"
        ],
        "extract_fields": ["sunset_date", "who_can_rescind"],
        "risk_level": RiskLevel.MEDIUM,
        "description": "Contract may be terminated if not settled by date",
        "consequence": "For off-the-plan: developer can rescind if market rises",
        "mitigation": "Check recent legislative changes limiting developer rescission"
    },
    ConditionType.NOMINATION_CLAUSE: {
        "search_terms": [
            "nomination", "nominate", "substitute purchaser",
            "and/or nominee", "assigns", "purchaser may direct"
        ],
        "extract_fields": ["nomination_deadline", "nomination_fee"],
        "risk_level": RiskLevel.INFO,
        "description": "Purchaser can nominate another party to complete",
        "consequence": "Useful for SMSF purchases or development syndication"
    },
    ConditionType.GST_CLAUSE: {
        "search_terms": [
            "GST", "goods and services tax", "margin scheme",
            "going concern", "taxable supply"
        ],
        "extract_fields": ["gst_inclusive", "margin_scheme", "going_concern"],
        "risk_level": RiskLevel.MEDIUM,
        "description": "GST treatment of the transaction",
        "consequence": "Affects total cost for new properties, commercial, subdivisions"
    },
    ConditionType.SETTLEMENT_EXTENSION: {
        "search_terms": [
            "extension of settlement", "delayed settlement", "settlement may be extended",
            "extension fee", "penalty interest"
        ],
        "extract_fields": ["extension_fee", "max_extension_period", "penalty_rate"],
        "risk_level": RiskLevel.LOW,
        "description": "Settlement may be extended with penalty",
        "consequence": "Provides flexibility but at a cost"
    },
    ConditionType.FIXTURES_EXCLUSION: {
        "search_terms": [
            "fixtures", "exclusions", "chattels", "not included",
            "vendor to remove", "excluded from sale"
        ],
        "extract_fields": ["excluded_items"],
        "risk_level": RiskLevel.LOW,
        "description": "Certain items excluded from sale",
        "consequence": "Verify what's included before exchange"
    },
    ConditionType.TENANT_IN_OCCUPATION: {
        "search_terms": [
            "tenant", "lease", "tenancy", "rental agreement",
            "subject to existing lease", "current tenancy"
        ],
        "extract_fields": ["lease_expiry", "weekly_rent", "tenant_notice"],
        "risk_level": RiskLevel.MEDIUM,
        "description": "Property sold with existing tenancy",
        "consequence": "Must honour existing lease - affects vacant possession timing"
    },
    ConditionType.DELAYED_POSSESSION: {
        "search_terms": [
            "delayed possession", "vendor to remain", "licence to occupy",
            "vendor occupation", "rent back"
        ],
        "extract_fields": ["occupation_period", "licence_fee"],
        "risk_level": RiskLevel.MEDIUM,
        "description": "Vendor retains possession after settlement",
        "consequence": "Delays your access to property - ensure adequate insurance"
    },
    ConditionType.POOL_COMPLIANCE: {
        "search_terms": [
            "pool compliance", "swimming pool", "spa compliance",
            "pool barrier", "pool fence"
        ],
        "extract_fields": ["compliance_status", "certificate_date"],
        "risk_level": RiskLevel.LOW,
        "description": "Pool/spa compliance requirements",
        "consequence": "Non-compliant pool is vendor's responsibility to rectify"
    }
}


class SpecialConditionsAnalyzer:
    """
    Analyzes special conditions in property contracts.
    Extracts key details and assesses risk impact.
    """

    def __init__(self):
        self.config = SPECIAL_CONDITIONS_CONFIG

    def analyze(
        self,
        contract_text: str,
        is_investor: bool = False,
        intended_use: str = "owner_occupier"
    ) -> SpecialConditionsResult:
        """
        Analyze contract text for special conditions.

        Args:
            contract_text: Full contract/Section 32 text
            is_investor: Whether purchaser is an investor
            intended_use: 'owner_occupier', 'investor', 'developer'

        Returns:
            SpecialConditionsResult with all findings
        """
        result = SpecialConditionsResult()
        text_lower = contract_text.lower()

        # Detect each type of condition
        for condition_type, config in self.config.items():
            detected = self._detect_condition(text_lower, config)

            if detected:
                condition = ExtractedCondition(
                    condition_type=condition_type,
                    text=detected["matched_text"],
                    risk_level=config["risk_level"],
                    description=config["description"],
                    consequence=config.get("consequence", ""),
                    mitigation=config.get("mitigation", ""),
                    confidence=detected["confidence"]
                )

                # Extract specific fields
                condition.extracted_fields = self._extract_fields(
                    detected["matched_text"],
                    config.get("extract_fields", [])
                )

                result.conditions_found.append(condition)

                if config["risk_level"] in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                    result.critical_conditions.append(condition)

        # Check for missing protective conditions
        result.protective_conditions_present = {
            "finance": any(c.condition_type == ConditionType.SUBJECT_TO_FINANCE
                         for c in result.conditions_found),
            "building_inspection": any(c.condition_type == ConditionType.SUBJECT_TO_BUILDING_INSPECTION
                                      for c in result.conditions_found),
            "pest_inspection": any(c.condition_type == ConditionType.SUBJECT_TO_PEST_INSPECTION
                                  for c in result.conditions_found),
        }

        # Identify missing protections
        if not result.protective_conditions_present["finance"]:
            result.missing_protections.append(
                "No finance condition - purchase is unconditional regarding finance"
            )
        if not result.protective_conditions_present["building_inspection"]:
            result.missing_protections.append(
                "No building inspection condition - cannot exit for defects"
            )
        if not result.protective_conditions_present["pest_inspection"]:
            result.missing_protections.append(
                "No pest inspection condition - cannot exit for termite damage"
            )

        # Calculate risk score
        result.total_risk_score = self._calculate_risk_score(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(
            result, is_investor, intended_use
        )

        # Generate summary
        result.summary = self._generate_summary(result)

        return result

    def _detect_condition(
        self,
        text_lower: str,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Detect if a condition type is present in text."""
        search_terms = config["search_terms"]
        matches = []

        for term in search_terms:
            if term in text_lower:
                # Find surrounding context
                idx = text_lower.find(term)
                start = max(0, idx - 100)
                end = min(len(text_lower), idx + len(term) + 200)
                context = text_lower[start:end]
                matches.append({
                    "term": term,
                    "context": context
                })

        if matches:
            # Calculate confidence based on number of matching terms
            confidence = min(1.0, len(matches) / len(search_terms) * 2)
            return {
                "matched_text": matches[0]["context"],
                "confidence": confidence,
                "terms_matched": [m["term"] for m in matches]
            }

        return None

    def _extract_fields(
        self,
        text: str,
        field_names: List[str]
    ) -> Dict[str, Any]:
        """Extract specific fields from condition text."""
        extracted = {}

        # Common extraction patterns
        import re

        for field in field_names:
            if field == "loan_amount":
                # Look for dollar amounts
                amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', text)
                if amounts:
                    extracted[field] = amounts[0]

            elif field in ["approval_deadline", "inspection_deadline", "sale_deadline", "sunset_date"]:
                # Look for dates
                date_patterns = [
                    r'\d{1,2}/\d{1,2}/\d{2,4}',
                    r'\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}',
                    r'\d{1,2}\s+days?(?:\s+from)?'
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        extracted[field] = match.group()
                        break

            elif field == "weekly_rent":
                rent_match = re.search(r'\$[\d,]+(?:\.\d{2})?\s*(?:per\s*week|pw|/week)', text, re.IGNORECASE)
                if rent_match:
                    extracted[field] = rent_match.group()

            elif field == "penalty_rate":
                rate_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                if rate_match:
                    extracted[field] = rate_match.group()

        return extracted

    def _calculate_risk_score(self, result: SpecialConditionsResult) -> float:
        """Calculate overall risk score from conditions."""
        risk_weights = {
            RiskLevel.CRITICAL: 25,
            RiskLevel.HIGH: 15,
            RiskLevel.MEDIUM: 8,
            RiskLevel.LOW: 3,
            RiskLevel.INFO: 0,
            RiskLevel.BENEFICIAL: -5  # Reduces risk
        }

        score = 0
        for condition in result.conditions_found:
            score += risk_weights.get(condition.risk_level, 0)

        # Add points for missing protections
        score += len(result.missing_protections) * 10

        return max(0, min(100, score))

    def _generate_recommendations(
        self,
        result: SpecialConditionsResult,
        is_investor: bool,
        intended_use: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Critical conditions
        for condition in result.critical_conditions:
            if condition.condition_type == ConditionType.EARLY_DEPOSIT_RELEASE:
                recommendations.append(
                    "NEGOTIATE: Request removal of early deposit release clause, "
                    "or ensure deposit held in trust until settlement"
                )
            elif condition.condition_type == ConditionType.AS_IS_WHERE_IS:
                recommendations.append(
                    "CRITICAL: Property sold 'as-is'. Complete building and pest "
                    "inspection BEFORE signing contract"
                )
            elif condition.condition_type == ConditionType.VENDOR_WARRANTY_EXCLUSION:
                recommendations.append(
                    "Vendor warranties excluded - independent due diligence essential. "
                    "Consider structural engineer report"
                )

        # Missing protections
        if result.missing_protections:
            recommendations.append(
                "Consider adding protective conditions: " +
                ", ".join([p.split(" - ")[0] for p in result.missing_protections])
            )

        # Investor-specific
        if is_investor:
            tenant_condition = next(
                (c for c in result.conditions_found
                 if c.condition_type == ConditionType.TENANT_IN_OCCUPATION),
                None
            )
            if tenant_condition:
                recommendations.append(
                    "Existing tenancy: Verify lease terms, rent amount, and "
                    "tenant payment history before exchange"
                )
            else:
                recommendations.append(
                    "No existing tenant. Factor in vacancy period for cash flow"
                )

        # GST for new properties
        gst_condition = next(
            (c for c in result.conditions_found
             if c.condition_type == ConditionType.GST_CLAUSE),
            None
        )
        if gst_condition:
            recommendations.append(
                "GST applies: Verify if price is GST-inclusive and check margin scheme"
            )

        if not recommendations:
            recommendations.append(
                "Contract appears standard. Have conveyancer confirm all conditions"
            )

        return recommendations

    def _generate_summary(self, result: SpecialConditionsResult) -> str:
        """Generate executive summary of conditions analysis."""
        num_conditions = len(result.conditions_found)
        num_critical = len(result.critical_conditions)
        num_missing = len(result.missing_protections)

        if num_critical > 0:
            return (
                f"ATTENTION: {num_critical} high-risk condition(s) detected. "
                f"Total {num_conditions} special conditions found. "
                f"Risk score: {result.total_risk_score:.0f}/100. "
                "Review critical conditions before signing."
            )
        elif num_missing > 0:
            return (
                f"{num_conditions} special conditions found. "
                f"{num_missing} protective condition(s) missing. "
                f"Risk score: {result.total_risk_score:.0f}/100. "
                "Consider adding subject to finance/inspection conditions."
            )
        else:
            return (
                f"Contract has {num_conditions} special conditions including "
                "standard purchaser protections. "
                f"Risk score: {result.total_risk_score:.0f}/100."
            )

    async def analyze_with_rag(
        self,
        property_id: str,
        is_investor: bool = False
    ) -> SpecialConditionsResult:
        """
        Analyze special conditions using RAG for more accurate extraction.
        """
        from services.documents.rag import query_property_documents

        result = SpecialConditionsResult()

        # Query for each condition type
        for condition_type, config in self.config.items():
            query = (
                f"Does this contract contain a {config['description'].lower()}? "
                f"Look for terms like: {', '.join(config['search_terms'][:3])}. "
                "If found, extract any dates, amounts, or specific terms."
            )

            rag_result = await query_property_documents(
                property_id=property_id,
                question=query
            )

            answer = rag_result.get("answer", "").lower()
            confidence = rag_result.get("confidence", 0.5)

            # Check if condition was found
            if self._interpret_positive_answer(answer) and confidence > 0.5:
                condition = ExtractedCondition(
                    condition_type=condition_type,
                    text=answer,
                    risk_level=config["risk_level"],
                    description=config["description"],
                    consequence=config.get("consequence", ""),
                    mitigation=config.get("mitigation", ""),
                    confidence=confidence,
                    page_reference=self._extract_page_reference(
                        rag_result.get("sources", [])
                    )
                )
                result.conditions_found.append(condition)

                if config["risk_level"] in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                    result.critical_conditions.append(condition)

        # Check protective conditions
        result.protective_conditions_present = {
            "finance": any(c.condition_type == ConditionType.SUBJECT_TO_FINANCE
                         for c in result.conditions_found),
            "building_inspection": any(c.condition_type == ConditionType.SUBJECT_TO_BUILDING_INSPECTION
                                      for c in result.conditions_found),
            "pest_inspection": any(c.condition_type == ConditionType.SUBJECT_TO_PEST_INSPECTION
                                  for c in result.conditions_found),
        }

        # Identify missing protections
        if not result.protective_conditions_present["finance"]:
            result.missing_protections.append(
                "No finance condition - purchase is unconditional regarding finance"
            )
        if not result.protective_conditions_present["building_inspection"]:
            result.missing_protections.append(
                "No building inspection condition - cannot exit for defects"
            )

        result.total_risk_score = self._calculate_risk_score(result)
        result.recommendations = self._generate_recommendations(result, is_investor, "")
        result.summary = self._generate_summary(result)

        return result

    def _interpret_positive_answer(self, answer: str) -> bool:
        """Determine if RAG answer indicates condition is present."""
        positive = ["yes", "contains", "includes", "present", "found", "clause"]
        negative = ["no", "not found", "does not", "no mention", "absent"]

        for neg in negative:
            if neg in answer:
                return False

        for pos in positive:
            if pos in answer:
                return True

        return False

    def _extract_page_reference(self, sources: List[Dict]) -> Optional[str]:
        """Extract page reference from RAG sources."""
        if sources:
            pages = [str(s.get("page", "?")) for s in sources[:3]]
            return f"Pages: {', '.join(pages)}"
        return None


# Convenience function
def analyze_special_conditions(
    contract_text: str,
    is_investor: bool = False
) -> Dict[str, Any]:
    """
    Quick analysis of special conditions.

    Returns:
        Dict with all special conditions and recommendations
    """
    analyzer = SpecialConditionsAnalyzer()
    result = analyzer.analyze(contract_text, is_investor=is_investor)
    return result.to_dict()
