"""
Strata & Owners Corporation Analysis Module.

Comprehensive analysis of:
- Cladding risk assessment
- Enhanced financial analysis
- By-law impact analysis
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import date


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ============================================================================
# CLADDING RISK ASSESSMENT
# ============================================================================

CLADDING_RISK_INDICATORS = {
    "building_age": {
        "high_risk_period": (1990, 2019),
        "reason": "Aluminium Composite Panels (ACP) widely used in this period"
    },
    "building_height": {
        "type_a": {"stories": (3, None), "risk": "Highest scrutiny"},
        "type_b": {"stories": (2, 2), "risk": "Moderate scrutiny"},
        "type_c": {"stories": (1, 1), "risk": "Lower scrutiny"}
    },
    "facade_materials": {
        "high_risk": ["ACP", "aluminium composite", "Alucobond", "Vitrabond", "Alpolic"],
        "moderate_risk": ["EPS", "expanded polystyrene", "EIFS", "render"]
    }
}


CLADDING_KEYWORDS = [
    "cladding", "facade", "fire safety", "combustible",
    "aluminium composite", "ACP", "rectification",
    "CSV", "Cladding Safety Victoria", "VBA notice",
    "external wall", "fire risk", "facade upgrade"
]


@dataclass
class CladdingRiskResult:
    """Complete cladding risk assessment."""
    cladding_risk_level: str = "UNKNOWN"  # LOW, MEDIUM, HIGH, CRITICAL
    csv_status: Optional[Dict[str, Any]] = None  # Cladding Safety Victoria status
    rectification_status: Optional[str] = None
    estimated_cost_per_lot: Optional[float] = None
    insurance_impact: Optional[str] = None
    agm_mentions: List[Dict[str, Any]] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.cladding_risk_level,
            "csv_status": self.csv_status,
            "rectification_status": self.rectification_status,
            "estimated_cost_per_lot": self.estimated_cost_per_lot,
            "estimated_cost_formatted": f"${self.estimated_cost_per_lot:,.0f}" if self.estimated_cost_per_lot else None,
            "insurance_impact": self.insurance_impact,
            "agm_mentions": self.agm_mentions,
            "risk_indicators": self.risk_indicators,
            "recommendations": self.recommendations
        }


class CladdingRiskAssessor:
    """
    Assesses combustible cladding risk for apartments.

    Background:
    - Lacrosse Building fire (2014) and Neo200 fire (2019) exposed widespread use
      of combustible cladding in Australian apartments
    - Cladding Safety Victoria managing $600M rectification program
    - 1,200+ private buildings identified as moderate-to-extreme risk
    - Rectification costs: $2,500 - $20,000+ per dwelling
    - Insurance premiums increased up to 4x for affected buildings
    """

    def __init__(self):
        self.keywords = CLADDING_KEYWORDS
        self.risk_indicators = CLADDING_RISK_INDICATORS

    def assess(
        self,
        building_year: Optional[int],
        building_stories: int,
        strata_report: Optional[Dict[str, Any]] = None,
        agm_minutes: Optional[List[Dict[str, Any]]] = None,
        insurance_certificate: Optional[Dict[str, Any]] = None
    ) -> CladdingRiskResult:
        """
        Assess cladding risk.

        Args:
            building_year: Year building constructed
            building_stories: Number of stories
            strata_report: OC Certificate data
            agm_minutes: List of AGM minutes
            insurance_certificate: Insurance policy details

        Returns:
            CladdingRiskResult with assessment
        """
        result = CladdingRiskResult()

        # Check building age risk
        if building_year:
            high_risk_start, high_risk_end = self.risk_indicators["building_age"]["high_risk_period"]
            if high_risk_start <= building_year <= high_risk_end:
                result.risk_indicators.append(
                    f"Building constructed {building_year} - within high-risk cladding period"
                )

        # Check building height
        if building_stories >= 3:
            result.risk_indicators.append(
                f"{building_stories}-storey building - Type A building, highest cladding scrutiny"
            )

        # Analyze strata report for cladding mentions
        if strata_report:
            strata_analysis = self._analyze_strata_for_cladding(strata_report)
            if strata_analysis.get("cladding_mentioned"):
                result.risk_indicators.append("Cladding mentioned in strata report")
                result.cladding_risk_level = "HIGH"

                if strata_analysis.get("rectification_planned"):
                    result.rectification_status = strata_analysis.get("rectification_details")
                    result.estimated_cost_per_lot = strata_analysis.get("estimated_cost")

        # Analyze AGM minutes
        if agm_minutes:
            minutes_analysis = self._analyze_minutes_for_cladding(agm_minutes)
            result.agm_mentions = minutes_analysis.get("mentions", [])

            if minutes_analysis.get("cladding_mentioned"):
                if result.cladding_risk_level != "HIGH":
                    result.cladding_risk_level = "MEDIUM"

                if minutes_analysis.get("works_planned"):
                    result.cladding_risk_level = "HIGH"
                    result.rectification_status = "Works planned or in progress"

                if minutes_analysis.get("cost_mentioned"):
                    result.estimated_cost_per_lot = minutes_analysis.get("estimated_cost")

        # Check insurance for cladding exclusions
        if insurance_certificate:
            insurance_analysis = self._analyze_insurance(insurance_certificate)
            result.insurance_impact = insurance_analysis.get("cladding_impact")

            if insurance_analysis.get("cladding_exclusion"):
                result.cladding_risk_level = "CRITICAL"
                result.risk_indicators.append("Insurance excludes cladding-related claims")

        # Determine overall risk level if not set
        if result.cladding_risk_level == "UNKNOWN":
            if len(result.risk_indicators) >= 2:
                result.cladding_risk_level = "MEDIUM"
            elif len(result.risk_indicators) >= 1:
                result.cladding_risk_level = "LOW"
            else:
                result.cladding_risk_level = "LOW"

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, building_stories)

        return result

    def _analyze_strata_for_cladding(self, strata_report: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze strata report for cladding mentions."""
        text = str(strata_report).lower()

        result = {
            "cladding_mentioned": False,
            "rectification_planned": False,
            "rectification_details": None,
            "estimated_cost": None
        }

        for keyword in self.keywords:
            if keyword.lower() in text:
                result["cladding_mentioned"] = True
                break

        # Check for rectification mentions
        rectification_terms = ["rectification", "remediation", "facade works", "cladding replacement"]
        for term in rectification_terms:
            if term in text:
                result["rectification_planned"] = True
                result["rectification_details"] = f"'{term}' mentioned in strata report"
                break

        # Try to extract cost estimates
        import re
        cost_matches = re.findall(r'\$[\d,]+(?:\.\d{2})?', text)
        if cost_matches and result["cladding_mentioned"]:
            # Take largest amount as potential cost
            amounts = []
            for match in cost_matches:
                try:
                    amount = float(match.replace("$", "").replace(",", ""))
                    amounts.append(amount)
                except ValueError:
                    pass
            if amounts:
                result["estimated_cost"] = max(amounts)

        return result

    def _analyze_minutes_for_cladding(self, agm_minutes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze AGM minutes for cladding discussions."""
        result = {
            "cladding_mentioned": False,
            "works_planned": False,
            "cost_mentioned": False,
            "estimated_cost": None,
            "mentions": []
        }

        for minutes in agm_minutes:
            text = str(minutes.get("text", "")).lower()

            for keyword in self.keywords:
                if keyword.lower() in text:
                    result["cladding_mentioned"] = True

                    # Extract context
                    idx = text.find(keyword.lower())
                    context_start = max(0, idx - 100)
                    context_end = min(len(text), idx + len(keyword) + 200)
                    context = text[context_start:context_end]

                    result["mentions"].append({
                        "date": minutes.get("date"),
                        "keyword": keyword,
                        "context": context
                    })
                    break

            # Check for rectification
            if "rectification" in text or "remediation" in text:
                result["works_planned"] = True

            # Check for cost mentions
            import re
            if result["cladding_mentioned"]:
                cost_matches = re.findall(r'\$[\d,]+', text)
                if cost_matches:
                    result["cost_mentioned"] = True
                    amounts = []
                    for match in cost_matches:
                        try:
                            amount = float(match.replace("$", "").replace(",", ""))
                            if amount > 1000:  # Filter small amounts
                                amounts.append(amount)
                        except ValueError:
                            pass
                    if amounts:
                        result["estimated_cost"] = max(amounts)

        return result

    def _analyze_insurance(self, insurance_certificate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze insurance for cladding exclusions."""
        result = {
            "cladding_exclusion": False,
            "cladding_impact": None
        }

        exclusions = insurance_certificate.get("exclusions", [])
        text = " ".join(str(e).lower() for e in exclusions)

        cladding_exclusion_terms = ["cladding", "combustible", "facade", "external wall"]
        for term in cladding_exclusion_terms:
            if term in text:
                result["cladding_exclusion"] = True
                result["cladding_impact"] = f"Policy excludes claims related to '{term}'"
                break

        return result

    def _generate_recommendations(self, result: CladdingRiskResult, building_stories: int) -> List[str]:
        """Generate cladding recommendations."""
        recommendations = []

        if result.cladding_risk_level == "CRITICAL":
            recommendations.append(
                "CRITICAL: Building has identified cladding issues with insurance exclusions. "
                "Obtain written confirmation of rectification timeline and cost allocation before proceeding."
            )
        elif result.cladding_risk_level == "HIGH":
            recommendations.append(
                "HIGH RISK: Cladding issues identified or suspected. "
                "Request full cladding audit report and special levy forecast."
            )
        elif result.cladding_risk_level == "MEDIUM" and building_stories >= 3:
            recommendations.append(
                "Building within high-risk period and height. "
                "Request confirmation of cladding type and any VBA notices."
            )

        if result.estimated_cost_per_lot:
            recommendations.append(
                f"Estimated rectification cost: ${result.estimated_cost_per_lot:,.0f} per lot. "
                "Verify with OC Manager and factor into purchase price."
            )

        if result.insurance_impact:
            recommendations.append(
                f"Insurance impact: {result.insurance_impact}. "
                "Consider personal liability exposure."
            )

        if not recommendations and building_stories >= 3:
            recommendations.append(
                "No cladding issues identified but building height triggers scrutiny. "
                "Request written confirmation from OC that no cladding concerns exist."
            )

        return recommendations


# ============================================================================
# ENHANCED STRATA FINANCIAL ANALYSIS
# ============================================================================

@dataclass
class StrataFinancialResult:
    """Complete strata financial health analysis."""
    financial_health_score: int = 0  # 0-100
    admin_fund: Dict[str, Any] = field(default_factory=dict)
    sinking_fund: Dict[str, Any] = field(default_factory=dict)
    arrears: Dict[str, Any] = field(default_factory=dict)
    special_levies: Dict[str, Any] = field(default_factory=dict)
    insurance: Dict[str, Any] = field(default_factory=dict)
    risks: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "financial_health_score": self.financial_health_score,
            "health_rating": self._score_to_rating(),
            "admin_fund": self.admin_fund,
            "sinking_fund": self.sinking_fund,
            "arrears": self.arrears,
            "special_levies": self.special_levies,
            "insurance": self.insurance,
            "risks": self.risks,
            "recommendations": self.recommendations
        }

    def _score_to_rating(self) -> str:
        if self.financial_health_score >= 80:
            return "EXCELLENT"
        elif self.financial_health_score >= 60:
            return "GOOD"
        elif self.financial_health_score >= 40:
            return "FAIR"
        elif self.financial_health_score >= 20:
            return "POOR"
        else:
            return "CRITICAL"


class StrataFinancialAnalyzer:
    """
    Comprehensive financial health analysis of Owners Corporation.
    """

    # Benchmarks
    SINKING_FUND_RATIO_TARGET = 0.5  # 0.5% of insured value
    ARREARS_RATE_CONCERN = 10  # 10% of lots in arrears
    ARREARS_RATE_HIGH = 15  # 15% of lots in arrears

    def analyze(
        self,
        oc_certificate: Dict[str, Any],
        agm_minutes: Optional[List[Dict[str, Any]]] = None,
        financial_statements: Optional[Dict[str, Any]] = None
    ) -> StrataFinancialResult:
        """
        Analyze strata financial health.

        Args:
            oc_certificate: Section 151 OC Certificate data
            agm_minutes: List of AGM minutes
            financial_statements: Annual financial statements

        Returns:
            StrataFinancialResult with comprehensive analysis
        """
        result = StrataFinancialResult()

        # 1. Admin Fund Analysis
        result.admin_fund = self._analyze_admin_fund(oc_certificate)

        # 2. Sinking Fund Analysis
        result.sinking_fund = self._analyze_sinking_fund(oc_certificate, agm_minutes)

        # 3. Arrears Analysis
        result.arrears = self._analyze_arrears(oc_certificate)

        # 4. Special Levy History
        result.special_levies = self._analyze_special_levies(agm_minutes, financial_statements)

        # 5. Insurance Analysis
        result.insurance = self._analyze_insurance(oc_certificate)

        # Identify risks
        result.risks = self._identify_risks(result)

        # Calculate overall health score
        result.financial_health_score = self._calculate_health_score(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _analyze_admin_fund(self, oc_certificate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze administrative fund."""
        admin_fund = oc_certificate.get("admin_fund", {})
        balance = admin_fund.get("balance", 0)
        budget = admin_fund.get("budget", admin_fund.get("annual_budget", 0))

        months_reserve = (balance / (budget / 12)) if budget > 0 else 0

        return {
            "balance": balance,
            "balance_formatted": f"${balance:,.0f}",
            "annual_budget": budget,
            "budget_formatted": f"${budget:,.0f}",
            "months_reserve": round(months_reserve, 1),
            "health": "GOOD" if months_reserve >= 3 else ("CONCERN" if months_reserve >= 1 else "POOR"),
            "note": "Admin fund covers day-to-day expenses"
        }

    def _analyze_sinking_fund(
        self,
        oc_certificate: Dict[str, Any],
        agm_minutes: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze sinking/capital works fund."""
        sinking_fund = oc_certificate.get("sinking_fund", oc_certificate.get("capital_works_fund", {}))
        balance = sinking_fund.get("balance", 0)
        building_value = oc_certificate.get("insured_value", 0)

        ratio = (balance / building_value * 100) if building_value > 0 else 0

        # Extract planned works from minutes
        planned_works = []
        if agm_minutes:
            for minutes in agm_minutes:
                text = str(minutes.get("text", "")).lower()
                if "capital works" in text or "major works" in text or "maintenance plan" in text:
                    planned_works.append({
                        "date": minutes.get("date"),
                        "mentioned": True
                    })

        return {
            "balance": balance,
            "balance_formatted": f"${balance:,.0f}",
            "insured_value": building_value,
            "ratio_percent": round(ratio, 2),
            "target_ratio_percent": self.SINKING_FUND_RATIO_TARGET * 100,
            "health": self._assess_sinking_health(ratio),
            "planned_works_mentioned": len(planned_works) > 0,
            "note": "Sinking fund should be 0.25-0.5% of insured value"
        }

    def _assess_sinking_health(self, ratio: float) -> str:
        """Assess sinking fund health based on ratio."""
        if ratio >= 0.5:
            return "EXCELLENT"
        elif ratio >= 0.35:
            return "GOOD"
        elif ratio >= 0.25:
            return "FAIR"
        elif ratio >= 0.15:
            return "CONCERN"
        else:
            return "POOR"

    def _analyze_arrears(self, oc_certificate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze levy arrears."""
        arrears = oc_certificate.get("arrears", {})
        total_amount = arrears.get("total_amount", 0)
        lots_in_arrears = arrears.get("lots_in_arrears", 0)
        total_lots = oc_certificate.get("total_lots", 1)

        arrears_rate = (lots_in_arrears / total_lots * 100) if total_lots > 0 else 0

        return {
            "total_amount": total_amount,
            "total_amount_formatted": f"${total_amount:,.0f}",
            "lots_in_arrears": lots_in_arrears,
            "total_lots": total_lots,
            "arrears_rate_percent": round(arrears_rate, 1),
            "health": "CONCERN" if arrears_rate > self.ARREARS_RATE_CONCERN else "GOOD",
            "note": f"Arrears above {self.ARREARS_RATE_CONCERN}% indicate cash flow issues"
        }

    def _analyze_special_levies(
        self,
        agm_minutes: Optional[List[Dict[str, Any]]],
        financial_statements: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze special levy history."""
        special_levies = []

        # Extract from AGM minutes
        if agm_minutes:
            for minutes in agm_minutes:
                text = str(minutes.get("text", "")).lower()
                if "special levy" in text or "additional levy" in text:
                    # Try to extract amount
                    import re
                    amounts = re.findall(r'\$[\d,]+', text)
                    special_levies.append({
                        "date": minutes.get("date"),
                        "amount": amounts[0] if amounts else "Unknown",
                        "source": "AGM minutes"
                    })

        # Extract from financial statements
        if financial_statements:
            levies = financial_statements.get("special_levies", [])
            for levy in levies:
                special_levies.append({
                    "date": levy.get("date"),
                    "amount": levy.get("amount"),
                    "reason": levy.get("reason"),
                    "source": "Financial statements"
                })

        return {
            "history": special_levies,
            "count_5_years": len(special_levies),  # Simplified
            "health": "CONCERN" if len(special_levies) > 2 else "GOOD",
            "note": "Frequent special levies may indicate underfunded sinking fund"
        }

    def _analyze_insurance(self, oc_certificate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze OC insurance."""
        insurance = oc_certificate.get("insurance", {})

        exclusions = insurance.get("exclusions", [])
        concerning_exclusions = []

        concerning_terms = ["cladding", "combustible", "defect", "subsidence", "flood"]
        for exclusion in exclusions:
            if any(term in str(exclusion).lower() for term in concerning_terms):
                concerning_exclusions.append(exclusion)

        return {
            "building_sum_insured": insurance.get("building"),
            "public_liability": insurance.get("public_liability"),
            "office_bearers": insurance.get("office_bearers"),
            "excess": insurance.get("excess"),
            "exclusions": exclusions,
            "concerning_exclusions": concerning_exclusions,
            "health": "CONCERN" if concerning_exclusions else "GOOD",
            "note": "Check for exclusions that may affect claims"
        }

    def _identify_risks(self, result: StrataFinancialResult) -> List[Dict[str, Any]]:
        """Identify financial risks."""
        risks = []

        # Low sinking fund
        if result.sinking_fund.get("ratio_percent", 0) < 0.25:
            risks.append({
                "type": "LOW_SINKING_FUND",
                "severity": "HIGH",
                "detail": f"Sinking fund ratio of {result.sinking_fund['ratio_percent']:.2f}% is below recommended 0.25%",
                "consequence": "Special levy likely for major works"
            })

        # High arrears
        if result.arrears.get("arrears_rate_percent", 0) > self.ARREARS_RATE_HIGH:
            risks.append({
                "type": "HIGH_ARREARS",
                "severity": "HIGH",
                "detail": f"{result.arrears['arrears_rate_percent']:.1f}% of lots in arrears",
                "consequence": "Cash flow issues for OC, may affect maintenance"
            })
        elif result.arrears.get("arrears_rate_percent", 0) > self.ARREARS_RATE_CONCERN:
            risks.append({
                "type": "ELEVATED_ARREARS",
                "severity": "MEDIUM",
                "detail": f"{result.arrears['arrears_rate_percent']:.1f}% of lots in arrears",
                "consequence": "May affect OC cash flow"
            })

        # Special levy frequency
        if result.special_levies.get("count_5_years", 0) > 2:
            risks.append({
                "type": "FREQUENT_SPECIAL_LEVIES",
                "severity": "MEDIUM",
                "detail": f"{result.special_levies['count_5_years']} special levies in recent years",
                "consequence": "Indicates underfunded reserves"
            })

        # Insurance exclusions
        if result.insurance.get("concerning_exclusions"):
            risks.append({
                "type": "INSURANCE_EXCLUSIONS",
                "severity": "HIGH",
                "detail": f"Insurance excludes: {', '.join(str(e) for e in result.insurance['concerning_exclusions'][:2])}",
                "consequence": "Owners may be personally liable for excluded claims"
            })

        return risks

    def _calculate_health_score(self, result: StrataFinancialResult) -> int:
        """Calculate overall financial health score."""
        score = 100

        # Deduct for admin fund issues
        if result.admin_fund.get("health") == "POOR":
            score -= 20
        elif result.admin_fund.get("health") == "CONCERN":
            score -= 10

        # Deduct for sinking fund issues
        sinking_health = result.sinking_fund.get("health", "FAIR")
        health_deductions = {
            "POOR": 30,
            "CONCERN": 20,
            "FAIR": 10,
            "GOOD": 5,
            "EXCELLENT": 0
        }
        score -= health_deductions.get(sinking_health, 15)

        # Deduct for arrears
        arrears_rate = result.arrears.get("arrears_rate_percent", 0)
        if arrears_rate > 15:
            score -= 25
        elif arrears_rate > 10:
            score -= 15
        elif arrears_rate > 5:
            score -= 5

        # Deduct for special levies
        levy_count = result.special_levies.get("count_5_years", 0)
        score -= min(levy_count * 5, 20)

        # Deduct for insurance issues
        if result.insurance.get("concerning_exclusions"):
            score -= 15

        return max(0, min(100, score))

    def _generate_recommendations(self, result: StrataFinancialResult) -> List[str]:
        """Generate financial recommendations."""
        recommendations = []

        if result.financial_health_score < 40:
            recommendations.append(
                "CAUTION: Poor strata financial health. "
                "Factor potential special levies into purchase decision."
            )

        for risk in result.risks:
            if risk["severity"] == "HIGH":
                recommendations.append(f"{risk['type']}: {risk['consequence']}")

        if result.sinking_fund.get("health") in ["POOR", "CONCERN"]:
            recommendations.append(
                "Request 10-year maintenance plan and capital works forecast. "
                "Underfunded sinking fund = future special levies."
            )

        if result.insurance.get("concerning_exclusions"):
            recommendations.append(
                "Insurance has concerning exclusions. Consider personal liability exposure."
            )

        if not recommendations:
            recommendations.append(
                "Strata finances appear healthy. Verify with OC Manager."
            )

        return recommendations


# ============================================================================
# BY-LAW IMPACT ANALYSIS
# ============================================================================

COMMON_BYLAWS_TO_CHECK = {
    "pets": {
        "check_for": ["no pets", "pet approval", "pet size", "no dogs", "no cats"],
        "impact": "May prevent keeping pets",
        "common_restrictions": ["no dogs over 10kg", "approval required", "one pet only"]
    },
    "renovations": {
        "check_for": ["renovation approval", "modification approval", "works approval", "floor covering"],
        "impact": "May delay or prevent internal changes",
        "common_restrictions": ["OC approval for floor changes", "no hard floors above ground"]
    },
    "short_term_letting": {
        "check_for": ["short term", "airbnb", "minimum lease", "holiday letting", "short stay"],
        "impact": "May prevent Airbnb/short-stay use",
        "common_restrictions": ["minimum 6 month lease", "no short term letting"]
    },
    "parking": {
        "check_for": ["parking allocation", "visitor parking", "car space", "bicycle"],
        "impact": "Parking availability and visitor access",
        "common_restrictions": ["one space per lot", "no visitor parking"]
    },
    "moving": {
        "check_for": ["moving hours", "removalist", "lift booking", "move in"],
        "impact": "Logistics for move-in",
        "common_restrictions": ["weekday moves only", "lift deposit required"]
    },
    "smoking": {
        "check_for": ["no smoking", "smoke free", "balcony smoking", "smoking prohibited"],
        "impact": "Smoking restrictions",
        "common_restrictions": ["smoke-free building", "no balcony smoking"]
    },
    "noise": {
        "check_for": ["noise", "quiet hours", "music", "loud"],
        "impact": "Noise restrictions",
        "common_restrictions": ["quiet hours 10pm-8am", "no audible music"]
    },
    "common_areas": {
        "check_for": ["common area", "bbq", "gym", "pool", "rooftop"],
        "impact": "Common facility usage",
        "common_restrictions": ["booking required", "guest limits"]
    }
}


@dataclass
class ByLawRestriction:
    """A by-law restriction found."""
    category: str
    restriction: str
    impact: str
    conflicts_with_intended_use: bool = False
    severity: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "restriction": self.restriction,
            "impact": self.impact,
            "conflicts_with_intended_use": self.conflicts_with_intended_use,
            "severity": self.severity
        }


@dataclass
class ByLawAnalysisResult:
    """Complete by-law analysis result."""
    bylaws_analyzed: int = 0
    restrictions_found: List[ByLawRestriction] = field(default_factory=list)
    conflicts_with_intended_use: List[ByLawRestriction] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bylaws_analyzed": self.bylaws_analyzed,
            "restrictions_found": [r.to_dict() for r in self.restrictions_found],
            "restrictions_count": len(self.restrictions_found),
            "conflicts_with_intended_use": [c.to_dict() for c in self.conflicts_with_intended_use],
            "conflicts_count": len(self.conflicts_with_intended_use),
            "recommendations": self.recommendations
        }


class ByLawAnalyzer:
    """
    Analyzes Owners Corporation by-laws for restrictions affecting property use.
    """

    def __init__(self):
        self.bylaws_config = COMMON_BYLAWS_TO_CHECK

    def analyze(
        self,
        bylaws_text: str,
        intended_use: Dict[str, Any]
    ) -> ByLawAnalysisResult:
        """
        Analyze by-laws for restrictions.

        Args:
            bylaws_text: Full text of by-laws
            intended_use: Dict with usage intentions, e.g.:
                {
                    "pets": True,
                    "short_term_letting": True,
                    "renovation_planned": True
                }

        Returns:
            ByLawAnalysisResult with analysis
        """
        result = ByLawAnalysisResult()
        text_lower = bylaws_text.lower()
        result.bylaws_analyzed = 1  # Simplified

        for category, config in self.bylaws_config.items():
            restriction = self._check_bylaw_category(text_lower, config)

            if restriction:
                bylaw_restriction = ByLawRestriction(
                    category=category,
                    restriction=restriction,
                    impact=config["impact"]
                )

                # Check if conflicts with intended use
                if category in intended_use and intended_use[category]:
                    bylaw_restriction.conflicts_with_intended_use = True
                    bylaw_restriction.severity = "HIGH"
                    result.conflicts_with_intended_use.append(bylaw_restriction)

                result.restrictions_found.append(bylaw_restriction)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, intended_use)

        return result

    def _check_bylaw_category(self, text_lower: str, config: Dict[str, Any]) -> Optional[str]:
        """Check for restrictions in a by-law category."""
        search_terms = config["check_for"]

        for term in search_terms:
            if term in text_lower:
                # Found a restriction - try to extract context
                idx = text_lower.find(term)
                context_start = max(0, idx - 50)
                context_end = min(len(text_lower), idx + len(term) + 100)
                context = text_lower[context_start:context_end]

                return context

        return None

    def _generate_recommendations(
        self,
        result: ByLawAnalysisResult,
        intended_use: Dict[str, Any]
    ) -> List[str]:
        """Generate by-law recommendations."""
        recommendations = []

        if result.conflicts_with_intended_use:
            recommendations.append(
                f"CONFLICT: {len(result.conflicts_with_intended_use)} by-law(s) conflict with your intended use"
            )

            for conflict in result.conflicts_with_intended_use:
                if conflict.category == "pets":
                    recommendations.append(
                        "Pet restrictions may prevent keeping pets. "
                        "Note: Recent Supreme Court ruling (Cooper v Aussie OC) supports pet ownership - consult lawyer."
                    )
                elif conflict.category == "short_term_letting":
                    recommendations.append(
                        "Short-term letting restrictions apply. "
                        "Cannot use for Airbnb without OC approval/rule change."
                    )
                elif conflict.category == "renovations":
                    recommendations.append(
                        "Renovation restrictions apply. "
                        "May need OC approval for planned works."
                    )

        if not recommendations:
            recommendations.append("By-laws appear compatible with your intended use.")

        return recommendations


# Convenience functions
def assess_cladding_risk(
    building_year: int,
    building_stories: int,
    strata_report: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Quick cladding risk assessment.
    """
    assessor = CladdingRiskAssessor()
    result = assessor.assess(
        building_year=building_year,
        building_stories=building_stories,
        strata_report=strata_report
    )
    return result.to_dict()


def analyze_strata_finances(
    oc_certificate: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Quick strata financial analysis.
    """
    analyzer = StrataFinancialAnalyzer()
    result = analyzer.analyze(oc_certificate=oc_certificate)
    return result.to_dict()


def analyze_bylaws(
    bylaws_text: str,
    wants_pets: bool = False,
    wants_airbnb: bool = False
) -> Dict[str, Any]:
    """
    Quick by-law analysis.
    """
    analyzer = ByLawAnalyzer()
    result = analyzer.analyze(
        bylaws_text=bylaws_text,
        intended_use={
            "pets": wants_pets,
            "short_term_letting": wants_airbnb
        }
    )
    return result.to_dict()
