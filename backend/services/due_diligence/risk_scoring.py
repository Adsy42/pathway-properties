"""
Weighted Risk Scoring Framework.

Comprehensive property risk scoring system that produces a quantified,
weighted score across multiple risk categories.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class RiskRating(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Risk scoring weights and factors
RISK_WEIGHTS = {
    "legal": {
        "weight": 0.25,
        "description": "Legal document and title risks",
        "factors": {
            "caveat_risk": {"weight": 0.20, "description": "Caveats on title"},
            "covenant_impact": {"weight": 0.15, "description": "Restrictive covenant impact"},
            "easement_building_conflict": {"weight": 0.15, "description": "Easement conflicts with building"},
            "section_32_completeness": {"weight": 0.20, "description": "Section 32 completeness"},
            "special_conditions_risk": {"weight": 0.15, "description": "Risky special conditions"},
            "proprietor_mismatch": {"weight": 0.15, "description": "Vendor/proprietor mismatch"}
        }
    },
    "title_encumbrance": {
        "weight": 0.15,
        "description": "Title and encumbrance burden",
        "factors": {
            "caveat_severity": {"weight": 0.30, "description": "Severity of caveats"},
            "covenant_blocks_use": {"weight": 0.30, "description": "Covenant blocks intended use"},
            "section_173_obligations": {"weight": 0.20, "description": "Section 173 agreement obligations"},
            "easement_extent": {"weight": 0.20, "description": "Extent of easement burden"}
        }
    },
    "planning": {
        "weight": 0.15,
        "description": "Planning and development risks",
        "factors": {
            "development_potential_mismatch": {"weight": 0.25, "description": "Zone vs intended development"},
            "overlay_restrictions": {"weight": 0.25, "description": "Planning overlay impacts"},
            "illegal_works_detected": {"weight": 0.30, "description": "Potential illegal works"},
            "heritage_impact": {"weight": 0.20, "description": "Heritage overlay impact"}
        }
    },
    "physical": {
        "weight": 0.15,
        "description": "Physical condition risks",
        "factors": {
            "structural_defects": {"weight": 0.35, "description": "Structural concerns"},
            "termite_risk": {"weight": 0.20, "description": "Termite damage/risk"},
            "asbestos_risk": {"weight": 0.15, "description": "Asbestos presence"},
            "roof_condition": {"weight": 0.15, "description": "Roof condition"},
            "illegal_works": {"weight": 0.15, "description": "Unpermitted works"}
        }
    },
    "strata": {
        "weight": 0.10,
        "description": "Strata/OC risks (apartments only)",
        "factors": {
            "financial_health": {"weight": 0.30, "description": "OC financial health"},
            "cladding_risk": {"weight": 0.30, "description": "Combustible cladding risk"},
            "special_levy_history": {"weight": 0.20, "description": "Special levy history"},
            "bylaw_conflicts": {"weight": 0.20, "description": "By-law conflicts with use"}
        },
        "applies_to": ["apartment", "townhouse", "unit"]
    },
    "environmental": {
        "weight": 0.10,
        "description": "Environmental and location risks",
        "factors": {
            "flood_risk": {"weight": 0.25, "description": "Flood overlay/risk"},
            "bushfire_risk": {"weight": 0.25, "description": "Bushfire overlay/risk"},
            "contamination_risk": {"weight": 0.25, "description": "Contamination/EAO"},
            "flight_path": {"weight": 0.15, "description": "Aircraft noise exposure"},
            "social_housing_density": {"weight": 0.10, "description": "Social housing concentration"}
        }
    },
    "financial": {
        "weight": 0.10,
        "description": "Financial and market risks",
        "factors": {
            "price_vs_comparables": {"weight": 0.40, "description": "Price vs market"},
            "yield_adequacy": {"weight": 0.30, "description": "Rental yield adequacy"},
            "cash_flow_viability": {"weight": 0.30, "description": "Cash flow sustainability"}
        }
    }
}


@dataclass
class FactorScore:
    """Score for a single risk factor."""
    factor_name: str
    description: str
    raw_score: float  # 0-100
    weight: float
    weighted_score: float
    source: str = ""
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor_name,
            "description": self.description,
            "raw_score": self.raw_score,
            "weight": self.weight,
            "weighted_score": self.weighted_score,
            "source": self.source,
            "details": self.details
        }


@dataclass
class CategoryScore:
    """Score for a risk category."""
    category: str
    description: str
    score: float
    weight: float
    weighted_contribution: float
    factors: List[FactorScore] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "score": self.score,
            "weight": self.weight,
            "weighted_contribution": self.weighted_contribution,
            "factors": [f.to_dict() for f in self.factors]
        }


@dataclass
class RiskScoreResult:
    """Complete risk scoring result."""
    overall_risk_score: float  # 0-100, higher = more risky
    risk_rating: RiskRating
    category_breakdown: Dict[str, CategoryScore] = field(default_factory=dict)
    top_risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    confidence_level: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_risk_score": round(self.overall_risk_score, 1),
            "risk_rating": self.risk_rating.value,
            "risk_rating_description": self._get_rating_description(),
            "category_breakdown": {
                k: v.to_dict() for k, v in self.category_breakdown.items()
            },
            "top_risk_factors": self.top_risk_factors,
            "confidence_level": round(self.confidence_level, 2),
            "recommendations": self.recommendations
        }

    def _get_rating_description(self) -> str:
        descriptions = {
            RiskRating.LOW: "Low risk - proceed with standard due diligence",
            RiskRating.MODERATE: "Moderate risk - some issues require attention",
            RiskRating.ELEVATED: "Elevated risk - careful evaluation recommended",
            RiskRating.HIGH: "High risk - significant concerns identified",
            RiskRating.CRITICAL: "Critical risk - major red flags present"
        }
        return descriptions.get(self.risk_rating, "Unknown")


class PropertyRiskScorer:
    """
    Quantified risk scoring with weighted categories.
    Produces a 0-100 risk score where higher = more risky.
    """

    def __init__(self):
        self.risk_weights = RISK_WEIGHTS

    def calculate_risk_score(
        self,
        all_analyses: Dict[str, Any]
    ) -> RiskScoreResult:
        """
        Calculate composite risk score from all analysis components.

        Args:
            all_analyses: Dict containing results from all analyzers:
                - property_type: 'house', 'apartment', etc.
                - section_32_analysis: Section 32 completeness result
                - special_conditions: Special conditions analysis
                - title_analysis: Title/encumbrance analysis
                - planning_analysis: Planning/zoning analysis
                - physical_analysis: Building/pest inspection results
                - strata_analysis: Strata financial/cladding analysis
                - environmental_analysis: Contamination/flood/fire analysis
                - financial_analysis: Comparable sales/cash flow analysis
                - street_level_analysis: Gatekeeper check results

        Returns:
            RiskScoreResult with comprehensive scoring
        """
        result = RiskScoreResult(
            overall_risk_score=0,
            risk_rating=RiskRating.LOW
        )

        property_type = all_analyses.get("property_type", "house")
        category_scores = {}

        for category, config in self.risk_weights.items():
            # Check if category applies to this property type
            if "applies_to" in config:
                if property_type not in config["applies_to"]:
                    continue

            category_score = 0
            factor_details = []

            for factor_name, factor_config in config["factors"].items():
                factor_score = self._get_factor_score(
                    all_analyses, category, factor_name
                )
                factor_weight = factor_config["weight"]
                weighted_score = factor_score * factor_weight

                category_score += weighted_score

                factor_details.append(FactorScore(
                    factor_name=factor_name,
                    description=factor_config["description"],
                    raw_score=factor_score,
                    weight=factor_weight,
                    weighted_score=weighted_score
                ))

            weighted_contribution = category_score * config["weight"]

            category_scores[category] = CategoryScore(
                category=category,
                description=config["description"],
                score=round(category_score, 1),
                weight=config["weight"],
                weighted_contribution=round(weighted_contribution, 1),
                factors=factor_details
            )

        result.category_breakdown = category_scores

        # Calculate total weighted score
        total_score = sum(cat.weighted_contribution for cat in category_scores.values())

        # Normalize to 0-100
        max_possible = sum(
            config["weight"] * 100
            for cat, config in self.risk_weights.items()
            if "applies_to" not in config or
               property_type in config.get("applies_to", [])
        )

        result.overall_risk_score = (total_score / max_possible * 100) if max_possible > 0 else 50

        # Determine rating
        result.risk_rating = self._score_to_rating(result.overall_risk_score)

        # Get top risk factors
        result.top_risk_factors = self._get_top_risks(category_scores)

        # Calculate confidence
        result.confidence_level = self._calculate_confidence(all_analyses)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, all_analyses)

        return result

    def _get_factor_score(
        self,
        all_analyses: Dict[str, Any],
        category: str,
        factor: str
    ) -> float:
        """
        Get score (0-100) for a specific factor from analysis results.

        Returns higher scores for higher risk.
        """
        # Legal factors
        if category == "legal":
            if factor == "caveat_risk":
                caveats = all_analyses.get("title_analysis", {}).get("caveats", [])
                critical = sum(1 for c in caveats if c.get("risk_level") == "CRITICAL")
                high = sum(1 for c in caveats if c.get("risk_level") == "HIGH")
                return min(100, critical * 50 + high * 25 + len(caveats) * 5)

            elif factor == "covenant_impact":
                covenants = all_analyses.get("title_analysis", {}).get("covenants", {})
                if covenants.get("blocks_intended_use"):
                    return 90
                return min(100, covenants.get("total_impact_score", 0) * 3)

            elif factor == "easement_building_conflict":
                easements = all_analyses.get("title_analysis", {}).get("easements", {})
                conflicts = len(easements.get("building_conflicts", []))
                return min(100, conflicts * 40)

            elif factor == "section_32_completeness":
                s32 = all_analyses.get("section_32_analysis", {})
                if s32.get("rescission_risk"):
                    return 100
                missing_critical = len(s32.get("missing_critical", []))
                missing_high = len(s32.get("missing_high", []))
                return min(100, missing_critical * 30 + missing_high * 15)

            elif factor == "special_conditions_risk":
                conditions = all_analyses.get("special_conditions", {})
                return min(100, conditions.get("total_risk_score", 0))

            elif factor == "proprietor_mismatch":
                mismatch = all_analyses.get("title_analysis", {}).get("proprietor_mismatch", {})
                if mismatch.get("mismatch_detected"):
                    risk = mismatch.get("risk_level", "MEDIUM")
                    return {"CRITICAL": 100, "HIGH": 70, "MEDIUM": 40, "LOW": 20}.get(risk, 40)
                return 0

        # Title encumbrance factors
        elif category == "title_encumbrance":
            if factor == "caveat_severity":
                caveats = all_analyses.get("title_analysis", {}).get("caveat_classification", {})
                return min(100, caveats.get("critical_caveats", 0) * 50 + caveats.get("high_risk_caveats", 0) * 25)

            elif factor == "covenant_blocks_use":
                covenants = all_analyses.get("title_analysis", {}).get("covenants", {})
                return 100 if covenants.get("blocks_intended_use") else 0

            elif factor == "section_173_obligations":
                s173 = all_analyses.get("title_analysis", {}).get("section_173", {})
                exposure = s173.get("total_financial_exposure", 0)
                return min(100, exposure / 1000)  # $100k = 100 risk

            elif factor == "easement_extent":
                easements = all_analyses.get("title_analysis", {}).get("easements", {})
                return min(100, easements.get("total_risk_score", 0))

        # Planning factors
        elif category == "planning":
            planning = all_analyses.get("planning_analysis", {})

            if factor == "development_potential_mismatch":
                rating = planning.get("development_rating", "MODERATE")
                return {"BLOCKED": 100, "LIMITED": 60, "MODERATE": 30, "HIGH": 10}.get(rating, 30)

            elif factor == "overlay_restrictions":
                overlays = planning.get("overlays", [])
                critical = ["PAO", "EAO"]
                has_critical = any(o.get("code", "").upper() in critical for o in overlays)
                return 100 if has_critical else min(100, len(overlays) * 15)

            elif factor == "illegal_works_detected":
                permits = all_analyses.get("building_permits", {})
                illegal = len(permits.get("potential_illegal_works", []))
                return min(100, illegal * 40)

            elif factor == "heritage_impact":
                overlays = planning.get("overlays", [])
                has_heritage = any(o.get("code", "").upper() == "HO" for o in overlays)
                return 30 if has_heritage else 0

        # Physical factors
        elif category == "physical":
            physical = all_analyses.get("physical_analysis", {})

            if factor == "structural_defects":
                defects = physical.get("defects_detected", [])
                major = sum(1 for d in defects if d.get("severity") == "Major")
                return min(100, major * 40 + len(defects) * 5)

            elif factor == "termite_risk":
                termite = physical.get("termite_risk") or {}
                if termite.get("damage_detected"):
                    return 80
                return 20 if not termite.get("barrier_present") else 0

            elif factor == "asbestos_risk":
                # Based on building age
                building_year = all_analyses.get("building_year", 2000)
                if building_year < 1990:
                    return 50
                elif building_year < 2000:
                    return 20
                return 0

            elif factor == "roof_condition":
                defects = physical.get("defects_detected", [])
                roof_issues = sum(1 for d in defects if "roof" in d.get("type", "").lower())
                return min(100, roof_issues * 30)

            elif factor == "illegal_works":
                permits = all_analyses.get("building_permits", {})
                return min(100, permits.get("risk_score", 0))

        # Strata factors
        elif category == "strata":
            strata = all_analyses.get("strata_analysis", {})

            if factor == "financial_health":
                score = strata.get("financial", {}).get("financial_health_score", 50)
                return 100 - score  # Invert: low health = high risk

            elif factor == "cladding_risk":
                cladding = strata.get("cladding", {})
                risk = cladding.get("risk_level", "LOW")
                return {"CRITICAL": 100, "HIGH": 70, "MEDIUM": 40, "LOW": 10}.get(risk, 20)

            elif factor == "special_levy_history":
                levies = strata.get("financial", {}).get("special_levies", {})
                count = levies.get("count_5_years", 0)
                return min(100, count * 30)

            elif factor == "bylaw_conflicts":
                bylaws = strata.get("bylaws", {})
                conflicts = len(bylaws.get("conflicts_with_intended_use", []))
                return min(100, conflicts * 40)

        # Environmental factors
        elif category == "environmental":
            env = all_analyses.get("environmental_analysis", {})
            street = all_analyses.get("street_level_analysis", {})

            if factor == "flood_risk":
                flood = street.get("flood_risk", {})
                if flood.get("building_at_risk"):
                    return 80
                elif flood.get("aep_1_percent"):
                    return 50
                return 0

            elif factor == "bushfire_risk":
                bushfire = street.get("bushfire_risk", {})
                bal = bushfire.get("bal_rating", "")
                bal_scores = {"BAL-FZ": 100, "BAL-40": 80, "BAL-29": 60, "BAL-19": 40, "BAL-12.5": 20}
                return bal_scores.get(bal, 0)

            elif factor == "contamination_risk":
                risk = env.get("contamination_risk", "LOW")
                return {"CRITICAL": 100, "HIGH": 70, "MEDIUM": 40, "LOW": 10}.get(risk, 20)

            elif factor == "flight_path":
                flight = street.get("flight_path", {})
                anef = flight.get("anef", 0)
                if anef > 25:
                    return 80
                elif anef > 20:
                    return 50
                return max(0, anef * 2)

            elif factor == "social_housing_density":
                social = street.get("social_housing", {})
                density = social.get("density_percent", 0)
                return min(100, density * 5)  # 20% density = 100 risk

        # Financial factors
        elif category == "financial":
            financial = all_analyses.get("financial_analysis", {})

            if factor == "price_vs_comparables":
                comparables = financial.get("comparables", {})
                premium = comparables.get("premium_discount_percent", 0)
                if premium > 15:
                    return 80
                elif premium > 10:
                    return 50
                elif premium < -15:
                    return 60  # Investigate why so cheap
                return max(0, premium * 3)

            elif factor == "yield_adequacy":
                yield_pct = financial.get("yield_analysis", {}).get("gross", 5)
                if yield_pct < 3:
                    return 80
                elif yield_pct < 4:
                    return 50
                elif yield_pct < 5:
                    return 20
                return 0

            elif factor == "cash_flow_viability":
                cashflow = financial.get("cashflow", {})
                monthly = cashflow.get("monthly_cash_flow", 0)
                if monthly < -500:
                    return 70
                elif monthly < 0:
                    return 40
                return 0

        # Default
        return 30

    def _score_to_rating(self, score: float) -> RiskRating:
        """Convert numeric score to risk rating."""
        if score < 20:
            return RiskRating.LOW
        elif score < 40:
            return RiskRating.MODERATE
        elif score < 60:
            return RiskRating.ELEVATED
        elif score < 80:
            return RiskRating.HIGH
        else:
            return RiskRating.CRITICAL

    def _get_top_risks(self, category_scores: Dict[str, CategoryScore], n: int = 5) -> List[Dict[str, Any]]:
        """Get top N risk factors across all categories."""
        all_factors = []

        for category, data in category_scores.items():
            for factor in data.factors:
                all_factors.append({
                    "category": category,
                    "factor": factor.factor_name,
                    "description": factor.description,
                    "score": factor.raw_score,
                    "impact": factor.weighted_score
                })

        return sorted(all_factors, key=lambda x: x["score"], reverse=True)[:n]

    def _calculate_confidence(self, all_analyses: Dict[str, Any]) -> float:
        """Calculate confidence level based on data completeness."""
        total_checks = 0
        complete_checks = 0

        data_sources = [
            "section_32_analysis",
            "special_conditions",
            "title_analysis",
            "planning_analysis",
            "physical_analysis",
            "strata_analysis",
            "environmental_analysis",
            "financial_analysis",
            "street_level_analysis"
        ]

        for source in data_sources:
            total_checks += 1
            if all_analyses.get(source):
                complete_checks += 1

        return complete_checks / total_checks if total_checks > 0 else 0

    def _generate_recommendations(
        self,
        result: RiskScoreResult,
        all_analyses: Dict[str, Any]
    ) -> List[str]:
        """Generate risk-based recommendations."""
        recommendations = []

        if result.risk_rating == RiskRating.CRITICAL:
            recommendations.append(
                "CRITICAL RISK: Multiple major red flags identified. "
                "Strongly recommend further investigation before proceeding."
            )
        elif result.risk_rating == RiskRating.HIGH:
            recommendations.append(
                "HIGH RISK: Significant concerns identified. "
                "Careful evaluation and risk mitigation required."
            )

        # Add recommendations for top risk factors
        for factor in result.top_risk_factors[:3]:
            if factor["score"] >= 50:
                recommendations.append(
                    f"{factor['category'].title()}: {factor['description']} - Score: {factor['score']:.0f}/100"
                )

        if result.confidence_level < 0.5:
            recommendations.append(
                "Limited data available for comprehensive scoring. "
                "Recommend additional due diligence reports."
            )

        return recommendations


# Convenience function
def calculate_property_risk_score(
    analyses: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Quick risk score calculation.

    Returns comprehensive risk assessment.
    """
    scorer = PropertyRiskScorer()
    result = scorer.calculate_risk_score(analyses)
    return result.to_dict()
