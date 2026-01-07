"""
Title & Encumbrance Analysis Module.

Comprehensive analysis of:
- Vendor vs Registered Proprietor mismatch detection
- Easement impact analysis
- Restrictive covenant impact scoring
- Caveat risk classification
- Section 173 Agreement detection
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ============================================================================
# PROPRIETOR MISMATCH DETECTION
# ============================================================================

PROPRIETOR_MISMATCH_SCENARIOS = {
    "deceased_estate": {
        "indicators": [
            "executor", "administrator", "probate", "grant of probate",
            "letters of administration", "deceased", "estate of", "late"
        ],
        "additional_checks": [
            "Verify Grant of Probate obtained",
            "Check executor has power to sell",
            "Confirm no caveats from beneficiaries",
            "Verify no pending family provision claims"
        ],
        "risk_level": RiskLevel.MEDIUM,
        "typical_delay": "Settlement may be delayed pending probate",
        "description": "Property sold by executor/administrator of deceased estate"
    },
    "company_sale": {
        "indicators": [
            "pty ltd", "pty. ltd.", "proprietary limited", "limited",
            "company", "director", "corporation"
        ],
        "additional_checks": [
            "ASIC company search - is company still registered?",
            "Check for external administrators (liquidator/receiver)",
            "Verify director has authority to sign",
            "Check for any charges over property"
        ],
        "risk_level": RiskLevel.MEDIUM,
        "description": "Company-owned property - verify company status"
    },
    "power_of_attorney": {
        "indicators": [
            "power of attorney", "attorney", "POA", "as attorney for",
            "enduring power", "acting under"
        ],
        "additional_checks": [
            "Verify POA registered on title",
            "Confirm POA not revoked",
            "Check donor still alive (POA dies with donor)",
            "Verify POA grants power to sell real property"
        ],
        "risk_level": RiskLevel.HIGH,
        "description": "Sale by attorney under Power of Attorney"
    },
    "trust_sale": {
        "indicators": [
            "trustee", "trust", "as trustee for", "trustee of",
            "family trust", "discretionary trust", "unit trust"
        ],
        "additional_checks": [
            "Verify trustee has power to sell under trust deed",
            "Check no breach of trust",
            "Confirm beneficiaries notified if required"
        ],
        "risk_level": RiskLevel.MEDIUM,
        "description": "Property held by trustee of a trust"
    },
    "mortgagee_sale": {
        "indicators": [
            "mortgagee", "mortgagee in possession", "power of sale",
            "bank", "lender", "receiver"
        ],
        "additional_checks": [
            "Verify mortgagee has exercised power of sale correctly",
            "Check for any injunctions or stays",
            "Confirm no redemption by mortgagor"
        ],
        "risk_level": RiskLevel.HIGH,
        "description": "Mortgagee exercising power of sale (distressed sale)"
    },
    "multiple_proprietors": {
        "indicators": [
            "joint tenants", "tenants in common", "co-owners",
            "and", "&"
        ],
        "additional_checks": [
            "Verify ALL proprietors are vendors",
            "Check for any deceased joint tenant (survivorship)",
            "Confirm no family law proceedings"
        ],
        "risk_level": RiskLevel.LOW,
        "description": "Multiple registered proprietors"
    }
}


@dataclass
class MismatchResult:
    """Result of proprietor mismatch analysis."""
    mismatch_detected: bool
    scenario: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    description: str = ""
    vendor_name: str = ""
    proprietor_name: str = ""
    additional_checks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mismatch_detected": self.mismatch_detected,
            "scenario": self.scenario,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "vendor_name": self.vendor_name,
            "proprietor_name": self.proprietor_name,
            "additional_checks": self.additional_checks,
            "recommendations": self.recommendations
        }


class ProprietorMismatchDetector:
    """
    Detects mismatches between vendor name and registered proprietor.
    Identifies scenarios requiring additional investigation.
    """

    def __init__(self):
        self.scenarios = PROPRIETOR_MISMATCH_SCENARIOS

    def analyze(
        self,
        vendor_name: str,
        proprietor_name: str,
        contract_text: Optional[str] = None
    ) -> MismatchResult:
        """
        Analyze for vendor/proprietor mismatch.

        Args:
            vendor_name: Name of vendor signing contract
            proprietor_name: Registered proprietor on title
            contract_text: Full contract text for additional context

        Returns:
            MismatchResult with scenario identification
        """
        result = MismatchResult(
            mismatch_detected=False,
            vendor_name=vendor_name,
            proprietor_name=proprietor_name
        )

        # Normalize names for comparison
        vendor_normalized = self._normalize_name(vendor_name)
        proprietor_normalized = self._normalize_name(proprietor_name)

        # Check for exact match (no mismatch)
        if vendor_normalized == proprietor_normalized:
            result.description = "Vendor matches registered proprietor"
            return result

        # Check for name variations that are acceptable
        if self._is_acceptable_variation(vendor_normalized, proprietor_normalized):
            result.description = "Minor name variation - likely same person"
            return result

        # Mismatch detected - identify scenario
        result.mismatch_detected = True

        # Check contract text for scenario indicators
        context = (contract_text or "").lower() + " " + vendor_name.lower()

        for scenario_name, config in self.scenarios.items():
            if any(indicator in context for indicator in config["indicators"]):
                result.scenario = scenario_name
                result.risk_level = config["risk_level"]
                result.description = config["description"]
                result.additional_checks = config["additional_checks"]
                break

        if not result.scenario:
            result.scenario = "unknown_mismatch"
            result.risk_level = RiskLevel.HIGH
            result.description = "Vendor does not match registered proprietor - investigate"
            result.additional_checks = [
                "Verify vendor's authority to sell",
                "Request explanation from vendor's solicitor",
                "Consider title insurance"
            ]

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        import re
        name = name.lower().strip()
        # Remove common suffixes
        name = re.sub(r'\b(pty ltd|pty\. ltd\.|limited|ltd)\b', '', name)
        # Remove titles
        name = re.sub(r'\b(mr|mrs|ms|miss|dr|prof)\b', '', name)
        # Remove extra whitespace
        name = ' '.join(name.split())
        return name

    def _is_acceptable_variation(self, name1: str, name2: str) -> bool:
        """Check if names are acceptable variations of each other."""
        # Check if one is substring of other
        if name1 in name2 or name2 in name1:
            return True

        # Check word overlap (at least 2 words in common)
        words1 = set(name1.split())
        words2 = set(name2.split())
        common = words1.intersection(words2)

        return len(common) >= 2

    def _generate_recommendations(self, result: MismatchResult) -> List[str]:
        """Generate recommendations based on mismatch scenario."""
        recommendations = []

        if result.risk_level == RiskLevel.HIGH:
            recommendations.append(
                "HIGH RISK: Verify vendor's authority to sell before exchange"
            )

        if result.scenario == "deceased_estate":
            recommendations.extend([
                "Request certified copy of Grant of Probate",
                "Verify executor named in contract matches probate",
                "Consider delay provisions in contract for probate issues"
            ])
        elif result.scenario == "power_of_attorney":
            recommendations.extend([
                "Request copy of registered POA",
                "Verify POA grants power to deal with real property",
                "Confirm donor is still alive at settlement"
            ])
        elif result.scenario == "company_sale":
            recommendations.extend([
                "Request current ASIC company extract",
                "Verify directors signing match ASIC records",
                "Check company is not under external administration"
            ])
        elif result.scenario == "mortgagee_sale":
            recommendations.extend([
                "Request evidence of valid exercise of power of sale",
                "Check for any court orders affecting sale",
                "Consider shorter settlement period to reduce risk"
            ])
        else:
            recommendations.append(
                "Consult conveyancer to investigate mismatch before exchange"
            )

        return recommendations


# ============================================================================
# EASEMENT IMPACT ANALYSIS
# ============================================================================

EASEMENT_TYPES = {
    "drainage_easement": {
        "typical_width": "1.5m - 3m",
        "impact": "Cannot build over - affects floor plan",
        "check": "Does building footprint intersect easement?",
        "risk_score": 6
    },
    "sewerage_easement": {
        "typical_width": "2m - 4m",
        "impact": "Cannot build over, authority access rights",
        "check": "Location of sewer line relative to proposed works",
        "risk_score": 6
    },
    "electricity_easement": {
        "typical_width": "Varies by voltage",
        "impact": "Height restrictions, cannot plant tall trees",
        "check": "Overhead or underground? Substation nearby?",
        "risk_score": 5
    },
    "carriageway_easement": {
        "typical_width": "3m - 6m",
        "impact": "Access rights for others over your land",
        "check": "Who benefits? How often used? Maintenance obligations?",
        "risk_score": 7
    },
    "party_wall_easement": {
        "typical_width": "N/A",
        "impact": "Shared wall with neighbour",
        "check": "Repair obligations, modification restrictions",
        "risk_score": 4
    },
    "pipeline_easement": {
        "typical_width": "3m - 10m",
        "impact": "Gas, water, or oil pipeline",
        "check": "Setback requirements, excavation restrictions",
        "risk_score": 8
    },
    "telecommunications_easement": {
        "typical_width": "1m - 2m",
        "impact": "Cable/fibre routes",
        "check": "Location relative to building",
        "risk_score": 3
    },
    "right_of_way": {
        "typical_width": "3m - 4m",
        "impact": "Access for neighbouring properties",
        "check": "Frequency of use, who maintains?",
        "risk_score": 6
    }
}


@dataclass
class EasementAnalysis:
    """Analysis of a single easement."""
    easement_type: str
    location: str
    width: Optional[str] = None
    beneficiary: str = ""
    impact_description: str = ""
    conflicts_with_building: bool = False
    affects_development: bool = False
    risk_score: int = 0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.easement_type,
            "location": self.location,
            "width": self.width,
            "beneficiary": self.beneficiary,
            "impact": self.impact_description,
            "conflicts_with_building": self.conflicts_with_building,
            "affects_development": self.affects_development,
            "risk_score": self.risk_score,
            "recommendations": self.recommendations
        }


@dataclass
class EasementImpactResult:
    """Complete easement analysis result."""
    easements_found: List[EasementAnalysis] = field(default_factory=list)
    building_conflicts: List[str] = field(default_factory=list)
    development_restrictions: List[str] = field(default_factory=list)
    total_risk_score: int = 0
    implied_easement_warning: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "easements_found": [e.to_dict() for e in self.easements_found],
            "easements_count": len(self.easements_found),
            "building_conflicts": self.building_conflicts,
            "development_restrictions": self.development_restrictions,
            "total_risk_score": self.total_risk_score,
            "implied_easement_warning": self.implied_easement_warning,
            "recommendations": self.recommendations
        }


class EasementImpactAnalyzer:
    """
    Analyzes practical impact of easements on property use and development.
    """

    def __init__(self):
        self.easement_config = EASEMENT_TYPES

    def analyze(
        self,
        easements: List[Dict[str, Any]],
        building_footprint: Optional[Dict[str, Any]] = None,
        proposed_use: str = "residential"
    ) -> EasementImpactResult:
        """
        Analyze easement impacts.

        Args:
            easements: List of easements from title search
            building_footprint: Building location data (optional)
            proposed_use: 'residential', 'development', 'subdivision'

        Returns:
            EasementImpactResult with all analysis
        """
        result = EasementImpactResult()

        for easement in easements:
            analysis = self._analyze_single_easement(
                easement, building_footprint, proposed_use
            )
            result.easements_found.append(analysis)

            if analysis.conflicts_with_building:
                result.building_conflicts.append(
                    f"{analysis.easement_type} at {analysis.location}"
                )

            if analysis.affects_development:
                result.development_restrictions.append(
                    f"{analysis.easement_type}: {analysis.impact_description}"
                )

            result.total_risk_score += analysis.risk_score

        # Add implied easement warning
        result.implied_easement_warning = {
            "applies": True,
            "section": "Section 42(2)(d) Transfer of Land Act 1958",
            "explanation": (
                "Easements may exist that are NOT shown on title. "
                "Physical inspection required to identify actual service locations."
            ),
            "recommendation": "Walk property with surveyor to identify all services"
        }

        # Generate overall recommendations
        result.recommendations = self._generate_recommendations(result, proposed_use)

        return result

    def _analyze_single_easement(
        self,
        easement: Dict[str, Any],
        building_footprint: Optional[Dict[str, Any]],
        proposed_use: str
    ) -> EasementAnalysis:
        """Analyze a single easement."""
        easement_type = self._classify_easement_type(easement)
        config = self.easement_config.get(easement_type, {})

        analysis = EasementAnalysis(
            easement_type=easement_type,
            location=easement.get("location", "Unknown"),
            width=easement.get("width") or config.get("typical_width"),
            beneficiary=easement.get("beneficiary", "Unknown"),
            impact_description=config.get("impact", "May restrict use"),
            risk_score=config.get("risk_score", 5)
        )

        # Check building conflict
        if building_footprint and easement.get("coordinates"):
            analysis.conflicts_with_building = self._check_footprint_conflict(
                easement, building_footprint
            )
            if analysis.conflicts_with_building:
                analysis.risk_score += 10

        # Check development impact
        if proposed_use in ["development", "subdivision"]:
            analysis.affects_development = True
            analysis.risk_score += 5
            analysis.recommendations.append(
                f"Check {easement_type} impact on proposed {proposed_use}"
            )

        return analysis

    def _classify_easement_type(self, easement: Dict[str, Any]) -> str:
        """Classify easement type from text description."""
        text = (easement.get("type", "") + " " + easement.get("purpose", "")).lower()

        type_keywords = {
            "drainage_easement": ["drainage", "stormwater", "drain"],
            "sewerage_easement": ["sewer", "sewerage", "sanitary"],
            "electricity_easement": ["electricity", "power", "electrical", "substation"],
            "carriageway_easement": ["carriageway", "carriage", "vehicle access"],
            "party_wall_easement": ["party wall", "common wall"],
            "pipeline_easement": ["pipeline", "gas", "oil"],
            "telecommunications_easement": ["telco", "cable", "nbn", "fibre"],
            "right_of_way": ["right of way", "row", "access"]
        }

        for easement_type, keywords in type_keywords.items():
            if any(kw in text for kw in keywords):
                return easement_type

        return "unknown_easement"

    def _check_footprint_conflict(
        self,
        easement: Dict[str, Any],
        building_footprint: Dict[str, Any]
    ) -> bool:
        """Check if easement conflicts with building footprint."""
        # In production, use proper GIS intersection
        # Simplified: assume conflict if both have coordinates
        return bool(easement.get("coordinates") and building_footprint.get("coordinates"))

    def _generate_recommendations(
        self,
        result: EasementImpactResult,
        proposed_use: str
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.building_conflicts:
            recommendations.append(
                f"CRITICAL: {len(result.building_conflicts)} easement(s) may conflict "
                "with existing building. Verify with surveyor before purchase."
            )

        if result.development_restrictions and proposed_use == "development":
            recommendations.append(
                "Development restrictions apply. Consult town planner before purchase."
            )

        if result.total_risk_score > 20:
            recommendations.append(
                "High easement burden. Consider impact on resale value."
            )

        if not recommendations:
            recommendations.append("Easement burden appears manageable for intended use.")

        return recommendations


# ============================================================================
# RESTRICTIVE COVENANT ANALYSIS
# ============================================================================

COVENANT_IMPACT_MATRIX = {
    "single_dwelling_only": {
        "impact_score": 9,
        "affects": ["subdivision", "dual_occupancy", "granny_flat", "rooming_house"],
        "can_be_removed": "Section 60 application to VCAT - expensive, uncertain",
        "removal_cost": "$20,000 - $50,000",
        "removal_success_rate": "30-50%"
    },
    "building_materials": {
        "impact_score": 4,
        "common_restrictions": ["brick only", "no weatherboard", "tile roof only"],
        "affects": ["renovation_options", "extension_cost"],
        "can_be_removed": "Possible if neighbourhood character has changed"
    },
    "building_setbacks": {
        "impact_score": 5,
        "common_restrictions": ["10m front setback", "3m side setback"],
        "affects": ["buildable_area", "extension_potential"],
        "planning_interaction": "More restrictive than planning scheme = covenant prevails"
    },
    "no_business": {
        "impact_score": 3,
        "affects": ["home_office", "airbnb", "rooming_house"],
        "modern_interpretation": "Small home office usually OK, commercial not"
    },
    "height_restriction": {
        "impact_score": 6,
        "affects": ["second_storey", "extension"],
        "compare_to": "Planning scheme height limits"
    },
    "no_subdivision": {
        "impact_score": 8,
        "affects": ["subdivision", "development_potential"],
        "can_be_removed": "Difficult - usually upheld"
    },
    "fence_requirements": {
        "impact_score": 2,
        "common_restrictions": ["fence type", "fence height", "front fence prohibition"],
        "affects": ["privacy", "security"]
    },
    "outbuilding_restrictions": {
        "impact_score": 3,
        "affects": ["shed", "garage", "studio"]
    }
}


@dataclass
class CovenantAnalysis:
    """Analysis of a single covenant."""
    text: str
    covenant_type: str
    impact_score: int
    created_date: Optional[str] = None
    beneficiary: str = ""
    blocks_intended_use: bool = False
    blocked_uses: List[str] = field(default_factory=list)
    removal_feasibility: str = ""
    removal_cost: str = ""
    removal_success_rate: str = ""
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "type": self.covenant_type,
            "impact_score": self.impact_score,
            "created_date": self.created_date,
            "beneficiary": self.beneficiary,
            "blocks_intended_use": self.blocks_intended_use,
            "blocked_uses": self.blocked_uses,
            "removal": {
                "feasibility": self.removal_feasibility,
                "estimated_cost": self.removal_cost,
                "success_rate": self.removal_success_rate
            },
            "recommendations": self.recommendations
        }


@dataclass
class CovenantImpactResult:
    """Complete covenant analysis result."""
    covenants_found: List[CovenantAnalysis] = field(default_factory=list)
    total_impact_score: int = 0
    blocks_intended_use: bool = False
    development_impact: str = ""  # NONE, MINOR, MAJOR, FATAL
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "covenants_found": [c.to_dict() for c in self.covenants_found],
            "covenants_count": len(self.covenants_found),
            "total_impact_score": self.total_impact_score,
            "blocks_intended_use": self.blocks_intended_use,
            "development_impact": self.development_impact,
            "recommendations": self.recommendations
        }


class CovenantAnalyzer:
    """
    Scores restrictive covenant impact based on buyer's intended use.
    """

    def __init__(self):
        self.impact_matrix = COVENANT_IMPACT_MATRIX

    def analyze(
        self,
        covenants: List[Dict[str, Any]],
        intended_use: Dict[str, Any]
    ) -> CovenantImpactResult:
        """
        Analyze covenant impacts.

        Args:
            covenants: List of covenants from title search
            intended_use: Dict with 'strategy' key (e.g., 'subdivision', 'granny_flat')

        Returns:
            CovenantImpactResult with impact assessment
        """
        result = CovenantImpactResult()
        strategy = intended_use.get("strategy", "owner_occupier")

        for covenant in covenants:
            covenant_type = self._classify_covenant(covenant.get("text", ""))
            config = self.impact_matrix.get(covenant_type, {})

            analysis = CovenantAnalysis(
                text=covenant.get("text", ""),
                covenant_type=covenant_type,
                impact_score=config.get("impact_score", 5),
                created_date=covenant.get("date"),
                beneficiary=covenant.get("beneficiary", "Unknown"),
                removal_feasibility=config.get("can_be_removed", "Unknown"),
                removal_cost=config.get("removal_cost", "Unknown"),
                removal_success_rate=config.get("removal_success_rate", "Unknown")
            )

            # Check if covenant blocks intended use
            affected_uses = config.get("affects", [])
            if strategy in affected_uses:
                analysis.blocks_intended_use = True
                analysis.blocked_uses = [strategy]
                result.blocks_intended_use = True
                analysis.recommendations.append(
                    f"CRITICAL: This covenant may prevent {strategy}"
                )

            result.covenants_found.append(analysis)
            result.total_impact_score += analysis.impact_score

        # Determine development impact
        if result.blocks_intended_use:
            result.development_impact = "FATAL"
        elif result.total_impact_score > 15:
            result.development_impact = "MAJOR"
        elif result.total_impact_score > 8:
            result.development_impact = "MINOR"
        else:
            result.development_impact = "NONE"

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, strategy)

        return result

    def _classify_covenant(self, text: str) -> str:
        """Classify covenant type from text."""
        text_lower = text.lower()

        classifications = {
            "single_dwelling_only": ["single dwelling", "one dwelling", "only one", "not more than one"],
            "no_subdivision": ["not subdivide", "no subdivision", "shall not subdivide"],
            "building_materials": ["brick", "masonry", "weatherboard", "tile roof"],
            "building_setbacks": ["setback", "front boundary", "side boundary"],
            "height_restriction": ["height", "storey", "stories", "not exceed"],
            "no_business": ["no business", "not conduct", "residential purposes only"],
            "fence_requirements": ["fence", "fencing", "front fence"],
            "outbuilding_restrictions": ["outbuilding", "shed", "garage"]
        }

        for covenant_type, keywords in classifications.items():
            if any(kw in text_lower for kw in keywords):
                return covenant_type

        return "other"

    def _generate_recommendations(
        self,
        result: CovenantImpactResult,
        strategy: str
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.blocks_intended_use:
            recommendations.append(
                f"CRITICAL: Restrictive covenant(s) may prevent {strategy}. "
                "Consult planning lawyer before purchase."
            )

            # Find removal options
            for covenant in result.covenants_found:
                if covenant.blocks_intended_use and covenant.removal_feasibility:
                    recommendations.append(
                        f"Covenant removal option: {covenant.removal_feasibility}. "
                        f"Cost: {covenant.removal_cost}, Success rate: {covenant.removal_success_rate}"
                    )

        if result.development_impact == "MAJOR":
            recommendations.append(
                "Significant covenant restrictions. Factor into development feasibility."
            )

        if not result.covenants_found:
            recommendations.append("No restrictive covenants detected.")

        return recommendations


# ============================================================================
# CAVEAT RISK CLASSIFICATION
# ============================================================================

CAVEAT_RISK_MATRIX = {
    "commercial_lender": {
        "risk_level": RiskLevel.LOW,
        "typical_entities": ["bank", "credit union", "mortgage", "westpac", "cba", "anz", "nab"],
        "reason": "Standard security for mortgage - will be removed at settlement",
        "action": "Verify discharge arranged for settlement"
    },
    "private_lender": {
        "risk_level": RiskLevel.MEDIUM,
        "typical_entities": ["private loan", "personal loan", "family trust"],
        "reason": "May indicate financial stress, harder to coordinate discharge",
        "action": "Verify lender agrees to discharge"
    },
    "family_member": {
        "risk_level": RiskLevel.HIGH,
        "typical_entities": ["family", "spouse", "husband", "wife", "partner"],
        "reason": "Often indicates family dispute or divorce proceedings",
        "action": "Investigate underlying dispute, may delay settlement"
    },
    "builder_contractor": {
        "risk_level": RiskLevel.HIGH,
        "typical_entities": ["builder", "contractor", "construction", "building works"],
        "reason": "Unpaid building work - may indicate defects or dispute",
        "action": "Investigate works done, payment status, defect claims"
    },
    "family_court": {
        "risk_level": RiskLevel.CRITICAL,
        "typical_entities": ["family court", "family law", "matrimonial", "de facto"],
        "reason": "Property subject to family law proceedings",
        "action": "Cannot proceed until family court orders resolved"
    },
    "deceased_estate_beneficiary": {
        "risk_level": RiskLevel.HIGH,
        "typical_entities": ["beneficiary", "estate", "inheritance", "will"],
        "reason": "Beneficiary claiming interest - estate dispute",
        "action": "Verify probate complete, no contested claims"
    },
    "ato_state_revenue": {
        "risk_level": RiskLevel.CRITICAL,
        "typical_entities": ["ATO", "Australian Taxation Office", "State Revenue", "tax", "duty"],
        "reason": "Tax debt - vendor may be in financial distress",
        "action": "Verify debt will be cleared at settlement"
    },
    "owners_corporation": {
        "risk_level": RiskLevel.MEDIUM,
        "typical_entities": ["owners corporation", "body corporate", "strata"],
        "reason": "Unpaid strata levies",
        "action": "Verify arrears and who pays at settlement"
    }
}


@dataclass
class CaveatAnalysis:
    """Analysis of a single caveat."""
    caveator: str
    grounds: str
    classification: str
    risk_level: RiskLevel
    reason: str
    recommended_action: str
    blocks_settlement: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "caveator": self.caveator,
            "grounds": self.grounds,
            "classification": self.classification,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "recommended_action": self.recommended_action,
            "blocks_settlement": self.blocks_settlement
        }


@dataclass
class CaveatClassificationResult:
    """Complete caveat analysis result."""
    caveats_found: List[CaveatAnalysis] = field(default_factory=list)
    critical_caveats: int = 0
    high_risk_caveats: int = 0
    settlement_blockers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "caveats_found": [c.to_dict() for c in self.caveats_found],
            "caveats_count": len(self.caveats_found),
            "critical_caveats": self.critical_caveats,
            "high_risk_caveats": self.high_risk_caveats,
            "settlement_blockers": self.settlement_blockers,
            "recommendations": self.recommendations
        }


class CaveatClassifier:
    """
    Classifies caveats by type and assesses risk level.
    """

    def __init__(self):
        self.risk_matrix = CAVEAT_RISK_MATRIX

    def classify(self, caveats: List[Dict[str, Any]]) -> CaveatClassificationResult:
        """
        Classify and assess caveat risks.

        Args:
            caveats: List of caveats from title search

        Returns:
            CaveatClassificationResult with risk assessment
        """
        result = CaveatClassificationResult()

        for caveat in caveats:
            classification = self._classify_caveat(caveat)
            config = self.risk_matrix.get(classification, {})

            analysis = CaveatAnalysis(
                caveator=caveat.get("caveator", "Unknown"),
                grounds=caveat.get("grounds", ""),
                classification=classification,
                risk_level=config.get("risk_level", RiskLevel.MEDIUM),
                reason=config.get("reason", "Unknown caveat type"),
                recommended_action=config.get("action", "Investigate before exchange")
            )

            # Check if blocks settlement
            if analysis.risk_level == RiskLevel.CRITICAL:
                analysis.blocks_settlement = True
                result.settlement_blockers.append(analysis.caveator)
                result.critical_caveats += 1

            if analysis.risk_level == RiskLevel.HIGH:
                result.high_risk_caveats += 1

            result.caveats_found.append(analysis)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _classify_caveat(self, caveat: Dict[str, Any]) -> str:
        """Classify caveat by caveator type."""
        text = (
            caveat.get("caveator", "") + " " +
            caveat.get("grounds", "")
        ).lower()

        for classification, config in self.risk_matrix.items():
            if any(entity in text for entity in config.get("typical_entities", [])):
                return classification

        return "unknown"

    def _generate_recommendations(
        self,
        result: CaveatClassificationResult
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.settlement_blockers:
            recommendations.append(
                f"CRITICAL: {len(result.settlement_blockers)} caveat(s) may block settlement. "
                "Resolve before exchange."
            )

        if result.high_risk_caveats > 0:
            recommendations.append(
                f"{result.high_risk_caveats} high-risk caveat(s). "
                "Investigate underlying claims before exchange."
            )

        for caveat in result.caveats_found:
            if caveat.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                recommendations.append(
                    f"{caveat.caveator}: {caveat.recommended_action}"
                )

        if not result.caveats_found:
            recommendations.append("No caveats on title.")

        return recommendations


# ============================================================================
# SECTION 173 AGREEMENT DETECTION
# ============================================================================

SECTION_173_OBLIGATIONS = {
    "development_contributions": {
        "description": "Payment required before certain permits",
        "typical_amount": "$5,000 - $100,000+",
        "trigger": "Building permit or subdivision"
    },
    "affordable_housing": {
        "description": "Percentage of units must be affordable housing",
        "impact": "Rental restrictions, sale restrictions"
    },
    "car_parking_waiver": {
        "description": "Reduced parking provided, no future requests",
        "impact": "Cannot add parking spaces"
    },
    "heritage_works": {
        "description": "Required restoration/maintenance works",
        "typical_cost": "$50,000 - $500,000+"
    },
    "landscaping_maintenance": {
        "description": "Maintain specific landscaping",
        "ongoing_cost": "Annual maintenance requirement"
    },
    "noise_attenuation": {
        "description": "Maintain noise barriers/double glazing",
        "impact": "Cannot modify certain features"
    },
    "environmental_audit": {
        "description": "Must complete environmental audit before certain uses",
        "trigger": "Change of use to sensitive use"
    }
}


@dataclass
class Section173Agreement:
    """Analysis of a Section 173 Agreement."""
    parties: str
    date_registered: Optional[str] = None
    obligations: List[str] = field(default_factory=list)
    financial_exposure: float = 0.0
    triggered_by_purchase: bool = False
    ongoing_requirements: bool = False
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parties": self.parties,
            "date_registered": self.date_registered,
            "obligations": self.obligations,
            "financial_exposure": self.financial_exposure,
            "triggered_by_purchase": self.triggered_by_purchase,
            "ongoing_requirements": self.ongoing_requirements,
            "summary": self.summary
        }


@dataclass
class Section173Result:
    """Complete Section 173 analysis result."""
    agreements_found: List[Section173Agreement] = field(default_factory=list)
    total_financial_exposure: float = 0.0
    ongoing_obligations: List[str] = field(default_factory=list)
    triggered_by_purchase: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agreements_found": [a.to_dict() for a in self.agreements_found],
            "agreements_count": len(self.agreements_found),
            "total_financial_exposure": self.total_financial_exposure,
            "ongoing_obligations": self.ongoing_obligations,
            "triggered_by_purchase": self.triggered_by_purchase,
            "recommendations": self.recommendations
        }


class Section173Analyzer:
    """
    Detects and analyzes Section 173 Agreements.

    Section 173 Agreements are binding agreements between landowner and
    responsible authority (council) that run with the land.

    CRITICAL because they:
    1. Bind future owners
    2. May require specific works/contributions
    3. May restrict use beyond planning scheme
    4. Are often missed by inexperienced buyers
    """

    def __init__(self):
        self.obligations_config = SECTION_173_OBLIGATIONS

    def analyze(
        self,
        title_search: Dict[str, Any],
        section_32_text: Optional[str] = None
    ) -> Section173Result:
        """
        Analyze for Section 173 Agreements.

        Args:
            title_search: Title search data
            section_32_text: Section 32 text for additional context

        Returns:
            Section173Result with analysis
        """
        result = Section173Result()

        # Check title for s.173 references
        encumbrances = title_search.get("encumbrances", [])
        instruments = title_search.get("instruments", [])

        all_items = encumbrances + instruments
        for item in all_items:
            if self._is_section_173(item):
                agreement = self._analyze_agreement(item)
                result.agreements_found.append(agreement)
                result.total_financial_exposure += agreement.financial_exposure

                if agreement.triggered_by_purchase:
                    result.triggered_by_purchase.append(agreement.summary)

                if agreement.ongoing_requirements:
                    result.ongoing_obligations.extend(agreement.obligations)

        # Also check Section 32 text
        if section_32_text:
            additional = self._scan_section_32(section_32_text)
            if additional and not any(
                a.parties == additional.parties for a in result.agreements_found
            ):
                result.agreements_found.append(additional)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _is_section_173(self, item: Dict[str, Any]) -> bool:
        """Check if item is a Section 173 Agreement."""
        text = str(item).lower()
        indicators = [
            "section 173", "s.173", "s173",
            "planning and environment act",
            "agreement with council"
        ]
        return any(ind in text for ind in indicators)

    def _analyze_agreement(self, item: Dict[str, Any]) -> Section173Agreement:
        """Analyze a Section 173 Agreement."""
        text = str(item).lower()

        agreement = Section173Agreement(
            parties=item.get("parties", "Council / Landowner"),
            date_registered=item.get("date")
        )

        # Identify obligation types
        for obligation_type, config in self.obligations_config.items():
            keywords = obligation_type.replace("_", " ")
            if keywords in text or config["description"].lower() in text:
                agreement.obligations.append(config["description"])

                # Estimate financial exposure
                if "typical_amount" in config:
                    amount = config["typical_amount"]
                    # Parse range and take midpoint
                    if "-" in amount:
                        try:
                            parts = amount.replace("$", "").replace(",", "").replace("+", "").split("-")
                            low = float(parts[0].strip())
                            high = float(parts[1].strip())
                            agreement.financial_exposure += (low + high) / 2
                        except (ValueError, IndexError):
                            agreement.financial_exposure += 25000  # Default

                if "trigger" in config:
                    agreement.triggered_by_purchase = "purchase" in config["trigger"].lower()

                if "ongoing" in config.get("impact", "").lower():
                    agreement.ongoing_requirements = True

        agreement.summary = ", ".join(agreement.obligations) or "Unknown obligations"

        return agreement

    def _scan_section_32(self, text: str) -> Optional[Section173Agreement]:
        """Scan Section 32 text for s.173 references."""
        text_lower = text.lower()

        if "section 173" in text_lower or "s.173" in text_lower:
            # Extract context around mention
            idx = text_lower.find("section 173")
            if idx == -1:
                idx = text_lower.find("s.173")

            context = text_lower[max(0, idx-100):idx+300]

            agreement = Section173Agreement(
                parties="Council / Landowner",
                summary="Section 173 Agreement mentioned in Section 32 - obtain full copy"
            )
            return agreement

        return None

    def _generate_recommendations(self, result: Section173Result) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.agreements_found:
            recommendations.append(
                f"MUST obtain copy of Section 173 Agreement(s) from council "
                "and have conveyancer review BEFORE signing contract"
            )

            if result.total_financial_exposure > 0:
                recommendations.append(
                    f"Estimated financial exposure: ${result.total_financial_exposure:,.0f}. "
                    "Verify exact obligations with council."
                )

            if result.triggered_by_purchase:
                recommendations.append(
                    "Some obligations may be triggered by purchase. "
                    "Factor into acquisition costs."
                )

            if result.ongoing_obligations:
                recommendations.append(
                    f"Ongoing obligations: {', '.join(result.ongoing_obligations[:3])}"
                )
        else:
            recommendations.append("No Section 173 Agreements detected on title.")

        return recommendations
