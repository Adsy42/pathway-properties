"""
Enhanced Investment Analysis Module.

Comprehensive investment scoring that goes beyond risk assessment to include:
- Capital growth potential
- Yield optimization scoring
- Development upside
- Holding cost efficiency
- Risk-adjusted returns
- Investment type suitability
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics


class InvestmentStrategy(str, Enum):
    """Investment strategy profiles."""
    YIELD_FOCUSED = "yield_focused"         # Maximize cash flow
    GROWTH_FOCUSED = "growth_focused"       # Maximize capital growth
    BALANCED = "balanced"                   # Balance yield and growth
    VALUE_ADD = "value_add"                 # Renovation/development potential
    PASSIVE = "passive"                     # Low maintenance


class InvestmentGrade(str, Enum):
    """Overall investment grade."""
    PREMIUM = "A"       # Score 80-100
    STRONG = "B"        # Score 65-79
    ACCEPTABLE = "C"    # Score 50-64
    MARGINAL = "D"      # Score 35-49
    AVOID = "F"         # Score 0-34


@dataclass
class ScoreComponent:
    """Individual scoring component."""
    name: str
    score: float          # 0-100
    weight: float         # Weight in overall score
    weighted_score: float
    reasoning: str
    data_quality: str = "good"  # good, limited, estimated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 1),
            "weight": self.weight,
            "weighted_score": round(self.weighted_score, 2),
            "reasoning": self.reasoning,
            "data_quality": self.data_quality
        }


@dataclass
class InvestmentScore:
    """Complete investment scoring result."""
    overall_score: float = 0.0
    investment_grade: InvestmentGrade = InvestmentGrade.ACCEPTABLE

    # Strategy fit scores
    yield_fit_score: float = 0.0
    growth_fit_score: float = 0.0
    value_add_fit_score: float = 0.0
    recommended_strategy: InvestmentStrategy = InvestmentStrategy.BALANCED

    # Component scores
    yield_score: ScoreComponent = None
    capital_growth_score: ScoreComponent = None
    holding_cost_score: ScoreComponent = None
    development_upside_score: ScoreComponent = None
    risk_adjusted_score: ScoreComponent = None
    location_score: ScoreComponent = None

    # Derived metrics
    score_components: List[ScoreComponent] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)

    recommendations: List[str] = field(default_factory=list)
    confidence_level: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "investment_grade": self.investment_grade.value,
            "investment_grade_description": self._grade_description(),
            "yield_fit_score": round(self.yield_fit_score, 1),
            "growth_fit_score": round(self.growth_fit_score, 1),
            "value_add_fit_score": round(self.value_add_fit_score, 1),
            "recommended_strategy": self.recommended_strategy.value,
            "score_components": [c.to_dict() for c in self.score_components if c],
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "opportunities": self.opportunities,
            "threats": self.threats,
            "recommendations": self.recommendations,
            "confidence_level": round(self.confidence_level, 2)
        }

    def _grade_description(self) -> str:
        descriptions = {
            InvestmentGrade.PREMIUM: "Premium investment - exceptional opportunity",
            InvestmentGrade.STRONG: "Strong investment - above average fundamentals",
            InvestmentGrade.ACCEPTABLE: "Acceptable investment - meets basic criteria",
            InvestmentGrade.MARGINAL: "Marginal investment - significant concerns",
            InvestmentGrade.AVOID: "Avoid - does not meet investment criteria"
        }
        return descriptions.get(self.investment_grade, "Unknown")


# Scoring weights by category
INVESTMENT_WEIGHTS = {
    "yield": {
        "weight": 0.25,
        "description": "Rental yield and cash flow potential"
    },
    "capital_growth": {
        "weight": 0.25,
        "description": "Capital appreciation potential"
    },
    "holding_cost": {
        "weight": 0.15,
        "description": "Holding cost efficiency"
    },
    "development_upside": {
        "weight": 0.10,
        "description": "Value-add and development potential"
    },
    "risk_adjusted": {
        "weight": 0.15,
        "description": "Risk-adjusted return quality"
    },
    "location": {
        "weight": 0.10,
        "description": "Location fundamentals"
    }
}


class InvestmentScorer:
    """
    Comprehensive investment scoring engine.

    Produces an investment score (0-100) with grade (A-F) considering:
    - Yield potential
    - Capital growth indicators
    - Holding costs
    - Development upside
    - Risk-adjusted returns
    - Location fundamentals
    """

    # Melbourne suburb tier classification (simplified)
    PREMIUM_SUBURBS = [
        "toorak", "south yarra", "brighton", "malvern", "armadale",
        "hawthorn", "kew", "camberwell", "albert park", "middle park"
    ]

    GROWTH_SUBURBS = [
        "brunswick", "northcote", "thornbury", "coburg", "preston",
        "footscray", "yarraville", "seddon", "newport", "williamstown",
        "richmond", "cremorne", "collingwood", "fitzroy", "carlton"
    ]

    # Infrastructure proximity (km) - impacts growth potential
    INFRASTRUCTURE_WEIGHTS = {
        "train_station": {"distance_good": 0.8, "distance_ok": 1.5, "weight": 0.3},
        "tram_stop": {"distance_good": 0.3, "distance_ok": 0.6, "weight": 0.2},
        "shops": {"distance_good": 0.5, "distance_ok": 1.0, "weight": 0.2},
        "schools": {"distance_good": 1.0, "distance_ok": 2.0, "weight": 0.2},
        "parks": {"distance_good": 0.5, "distance_ok": 1.0, "weight": 0.1}
    }

    def __init__(self):
        self.weights = INVESTMENT_WEIGHTS

    def calculate_investment_score(
        self,
        property_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        location_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None
    ) -> InvestmentScore:
        """
        Calculate comprehensive investment score.

        Args:
            property_data: Property details (address, type, land_size, etc.)
            financial_data: Financial analysis (yields, cash flow, comparables)
            risk_data: Risk assessment results
            location_data: Location analysis (amenities, transport, demographics)
            market_data: Market indicators (suburb growth, vacancy rates)

        Returns:
            InvestmentScore with comprehensive analysis
        """
        result = InvestmentScore()
        components = []

        # Calculate each component
        yield_score = self._score_yield(financial_data, property_data)
        components.append(yield_score)
        result.yield_score = yield_score

        growth_score = self._score_capital_growth(
            property_data, location_data, market_data or {}
        )
        components.append(growth_score)
        result.capital_growth_score = growth_score

        holding_score = self._score_holding_costs(financial_data, property_data)
        components.append(holding_score)
        result.holding_cost_score = holding_score

        dev_score = self._score_development_upside(property_data, location_data)
        components.append(dev_score)
        result.development_upside_score = dev_score

        risk_adj_score = self._score_risk_adjusted(financial_data, risk_data)
        components.append(risk_adj_score)
        result.risk_adjusted_score = risk_adj_score

        loc_score = self._score_location(location_data, property_data)
        components.append(loc_score)
        result.location_score = loc_score

        result.score_components = components

        # Calculate overall score
        total_weighted = sum(c.weighted_score for c in components)
        total_weight = sum(c.weight for c in components)

        result.overall_score = (total_weighted / total_weight) if total_weight > 0 else 50

        # Determine grade
        result.investment_grade = self._score_to_grade(result.overall_score)

        # Calculate strategy fit scores
        result.yield_fit_score = self._calculate_yield_fit(components, financial_data)
        result.growth_fit_score = self._calculate_growth_fit(components, location_data)
        result.value_add_fit_score = self._calculate_value_add_fit(
            components, property_data
        )

        # Recommend strategy
        result.recommended_strategy = self._recommend_strategy(
            result.yield_fit_score,
            result.growth_fit_score,
            result.value_add_fit_score
        )

        # SWOT analysis
        result.strengths, result.weaknesses = self._identify_strengths_weaknesses(
            components
        )
        result.opportunities, result.threats = self._identify_opportunities_threats(
            property_data, location_data, market_data or {}
        )

        # Generate recommendations
        result.recommendations = self._generate_recommendations(
            result, property_data, financial_data
        )

        # Calculate confidence
        result.confidence_level = self._calculate_confidence(components)

        return result

    def _score_yield(
        self,
        financial_data: Dict[str, Any],
        property_data: Dict[str, Any]
    ) -> ScoreComponent:
        """Score based on rental yield potential."""
        score = 50  # Default
        reasoning_parts = []
        data_quality = "good"

        # Get yield data
        summary = financial_data.get("summary", {})
        gross_yield = summary.get("gross_yield_percent", 0)
        net_yield = summary.get("net_yield_percent", 0)
        cash_flow = summary.get("monthly_cash_flow", 0)

        if not gross_yield:
            # Try to calculate from rent and price
            rent = property_data.get("weekly_rent", 0)
            price = property_data.get("purchase_price", 0) or property_data.get("asking_price", 0)
            if rent and price:
                gross_yield = (rent * 52 / price) * 100
                data_quality = "estimated"

        # Score gross yield (Melbourne benchmark ~3-5%)
        if gross_yield >= 6:
            score = 90
            reasoning_parts.append(f"Excellent gross yield of {gross_yield:.1f}%")
        elif gross_yield >= 5:
            score = 75
            reasoning_parts.append(f"Strong gross yield of {gross_yield:.1f}%")
        elif gross_yield >= 4:
            score = 60
            reasoning_parts.append(f"Acceptable gross yield of {gross_yield:.1f}%")
        elif gross_yield >= 3:
            score = 40
            reasoning_parts.append(f"Below average yield of {gross_yield:.1f}%")
        elif gross_yield > 0:
            score = 25
            reasoning_parts.append(f"Low yield of {gross_yield:.1f}%")
        else:
            score = 30
            reasoning_parts.append("Yield data unavailable")
            data_quality = "limited"

        # Adjust for cash flow
        if cash_flow > 0:
            score = min(100, score + 10)
            reasoning_parts.append(f"Positive cash flow ${cash_flow:,.0f}/month")
        elif cash_flow < -500:
            score = max(0, score - 10)
            reasoning_parts.append(f"Negative cash flow ${cash_flow:,.0f}/month")

        weight = self.weights["yield"]["weight"]

        return ScoreComponent(
            name="Yield Potential",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            reasoning="; ".join(reasoning_parts),
            data_quality=data_quality
        )

    def _score_capital_growth(
        self,
        property_data: Dict[str, Any],
        location_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> ScoreComponent:
        """Score based on capital growth potential."""
        score = 50
        reasoning_parts = []
        data_quality = "good"

        suburb = property_data.get("suburb", "").lower()

        # Suburb tier scoring
        if suburb in self.PREMIUM_SUBURBS:
            score = 70
            reasoning_parts.append("Premium suburb with consistent growth")
        elif suburb in self.GROWTH_SUBURBS:
            score = 75
            reasoning_parts.append("High-growth gentrifying suburb")
        else:
            score = 55
            reasoning_parts.append("Standard suburb growth profile")

        # Historical growth from market data
        hist_growth = market_data.get("5_year_growth_percent", 0)
        if hist_growth > 50:
            score = min(100, score + 15)
            reasoning_parts.append(f"Strong historical growth ({hist_growth:.0f}% over 5 years)")
        elif hist_growth > 30:
            score = min(100, score + 10)
            reasoning_parts.append(f"Good historical growth ({hist_growth:.0f}% over 5 years)")
        elif hist_growth < 10:
            score = max(0, score - 10)
            reasoning_parts.append(f"Weak historical growth ({hist_growth:.0f}% over 5 years)")

        # Infrastructure proximity
        transport_score = location_data.get("transport_score", 0)
        if transport_score > 80:
            score = min(100, score + 10)
            reasoning_parts.append("Excellent transport connectivity")
        elif transport_score > 60:
            score = min(100, score + 5)
            reasoning_parts.append("Good transport access")

        # Planned infrastructure
        planned_infra = location_data.get("planned_infrastructure", [])
        if planned_infra:
            score = min(100, score + 5 * len(planned_infra[:3]))
            reasoning_parts.append(f"{len(planned_infra)} planned infrastructure projects nearby")

        # Land component (higher land-to-value ratio = better growth)
        land_size = property_data.get("land_size", 0)
        price = property_data.get("purchase_price", 0)
        if land_size and price:
            land_value_estimate = land_size * market_data.get("land_price_sqm", 2000)
            land_ratio = (land_value_estimate / price) if price > 0 else 0
            if land_ratio > 0.5:
                score = min(100, score + 5)
                reasoning_parts.append("Strong land component")

        if not reasoning_parts:
            data_quality = "limited"
            reasoning_parts.append("Limited growth data available")

        weight = self.weights["capital_growth"]["weight"]

        return ScoreComponent(
            name="Capital Growth Potential",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            reasoning="; ".join(reasoning_parts),
            data_quality=data_quality
        )

    def _score_holding_costs(
        self,
        financial_data: Dict[str, Any],
        property_data: Dict[str, Any]
    ) -> ScoreComponent:
        """Score based on holding cost efficiency."""
        score = 50
        reasoning_parts = []
        data_quality = "good"

        outgoings = financial_data.get("outgoings", {})
        price = property_data.get("purchase_price", 0)

        total_outgoings = outgoings.get("total_annual", 0)

        if price > 0 and total_outgoings > 0:
            outgoing_ratio = (total_outgoings / price) * 100

            # Lower is better
            if outgoing_ratio < 1.0:
                score = 90
                reasoning_parts.append(f"Low outgoings ratio ({outgoing_ratio:.1f}%)")
            elif outgoing_ratio < 1.5:
                score = 75
                reasoning_parts.append(f"Moderate outgoings ratio ({outgoing_ratio:.1f}%)")
            elif outgoing_ratio < 2.0:
                score = 55
                reasoning_parts.append(f"Average outgoings ratio ({outgoing_ratio:.1f}%)")
            else:
                score = 35
                reasoning_parts.append(f"High outgoings ratio ({outgoing_ratio:.1f}%)")
        else:
            data_quality = "limited"
            reasoning_parts.append("Outgoings data unavailable")

        # Check for strata
        strata = outgoings.get("strata_levies_annual", 0)
        if strata > 8000:
            score = max(0, score - 15)
            reasoning_parts.append(f"High strata levies (${strata:,.0f}/year)")
        elif strata > 5000:
            score = max(0, score - 5)
            reasoning_parts.append(f"Moderate strata levies (${strata:,.0f}/year)")
        elif strata > 0:
            reasoning_parts.append(f"Standard strata levies (${strata:,.0f}/year)")

        # Land tax consideration
        land_tax = outgoings.get("land_tax", 0)
        if land_tax > 5000:
            score = max(0, score - 10)
            reasoning_parts.append(f"Significant land tax (${land_tax:,.0f}/year)")

        weight = self.weights["holding_cost"]["weight"]

        return ScoreComponent(
            name="Holding Cost Efficiency",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            reasoning="; ".join(reasoning_parts),
            data_quality=data_quality
        )

    def _score_development_upside(
        self,
        property_data: Dict[str, Any],
        location_data: Dict[str, Any]
    ) -> ScoreComponent:
        """Score based on development/value-add potential."""
        score = 40  # Base score for properties without development potential
        reasoning_parts = []
        data_quality = "good"

        land_size = property_data.get("land_size", 0)
        zone = property_data.get("zone_code", "").upper()
        property_type = property_data.get("property_type", "").lower()

        # Zone-based development potential
        high_density_zones = ["RGZ", "MUZ", "ACZ", "C1Z", "C2Z"]
        medium_density_zones = ["GRZ"]
        low_density_zones = ["NRZ"]

        zone_prefix = zone[:3] if len(zone) >= 3 else zone

        if zone_prefix in high_density_zones:
            score += 20
            reasoning_parts.append(f"{zone} allows higher density development")
        elif zone_prefix in medium_density_zones:
            score += 10
            reasoning_parts.append(f"{zone} allows medium density development")
        elif zone_prefix in low_density_zones:
            score -= 10
            reasoning_parts.append(f"{zone} restricts development (2 dwelling limit)")

        # Land size potential
        if land_size >= 1000:
            score += 20
            reasoning_parts.append(f"Large site ({land_size}sqm) - multi-unit potential")
        elif land_size >= 600:
            score += 15
            reasoning_parts.append(f"Good site size ({land_size}sqm) - development potential")
        elif land_size >= 400:
            score += 5
            reasoning_parts.append(f"Moderate site ({land_size}sqm) - dual occupancy potential")
        elif land_size > 0:
            reasoning_parts.append(f"Small site ({land_size}sqm) - limited development")

        # Check for renovation potential
        building_year = property_data.get("building_year", 2000)
        if building_year and building_year < 1980:
            score += 10
            reasoning_parts.append("Older building - renovation/rebuild potential")

        # Heritage overlay restricts
        overlays = property_data.get("overlays", [])
        if any("HO" in str(o) for o in overlays):
            score = max(0, score - 20)
            reasoning_parts.append("Heritage overlay restricts development")

        # Corner site bonus
        if property_data.get("is_corner", False):
            score += 10
            reasoning_parts.append("Corner site - better development flexibility")

        if not reasoning_parts:
            data_quality = "limited"
            reasoning_parts.append("Limited development data available")

        score = max(0, min(100, score))
        weight = self.weights["development_upside"]["weight"]

        return ScoreComponent(
            name="Development Upside",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            reasoning="; ".join(reasoning_parts),
            data_quality=data_quality
        )

    def _score_risk_adjusted(
        self,
        financial_data: Dict[str, Any],
        risk_data: Dict[str, Any]
    ) -> ScoreComponent:
        """Score based on risk-adjusted returns."""
        score = 50
        reasoning_parts = []
        data_quality = "good"

        # Get risk score (0-100, higher = more risky)
        risk_score = risk_data.get("overall_risk_score", 50)
        risk_rating = risk_data.get("risk_rating", "MODERATE")

        # Get return metrics
        summary = financial_data.get("summary", {})
        net_yield = summary.get("net_yield_percent", 0)
        cash_on_cash = summary.get("cash_on_cash_return_percent", 0)

        # Calculate risk-adjusted score (higher return + lower risk = better)
        if risk_score < 30:
            # Low risk
            risk_bonus = 20
            reasoning_parts.append(f"Low risk profile (score: {risk_score:.0f})")
        elif risk_score < 50:
            risk_bonus = 10
            reasoning_parts.append(f"Moderate risk profile (score: {risk_score:.0f})")
        elif risk_score < 70:
            risk_bonus = 0
            reasoning_parts.append(f"Elevated risk profile (score: {risk_score:.0f})")
        else:
            risk_bonus = -20
            reasoning_parts.append(f"High risk profile (score: {risk_score:.0f})")

        # Return component
        if net_yield > 5:
            return_score = 70
            reasoning_parts.append(f"Strong net yield ({net_yield:.1f}%)")
        elif net_yield > 4:
            return_score = 55
            reasoning_parts.append(f"Acceptable net yield ({net_yield:.1f}%)")
        elif net_yield > 3:
            return_score = 40
            reasoning_parts.append(f"Below average net yield ({net_yield:.1f}%)")
        else:
            return_score = 30
            reasoning_parts.append(f"Low net yield ({net_yield:.1f}%)")
            data_quality = "estimated" if net_yield == 0 else data_quality

        score = max(0, min(100, return_score + risk_bonus))

        weight = self.weights["risk_adjusted"]["weight"]

        return ScoreComponent(
            name="Risk-Adjusted Return",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            reasoning="; ".join(reasoning_parts),
            data_quality=data_quality
        )

    def _score_location(
        self,
        location_data: Dict[str, Any],
        property_data: Dict[str, Any]
    ) -> ScoreComponent:
        """Score based on location fundamentals."""
        score = 50
        reasoning_parts = []
        data_quality = "good"

        # Transport score
        transport = location_data.get("transport_score", 0)
        if transport > 80:
            score += 15
            reasoning_parts.append("Excellent transport access")
        elif transport > 60:
            score += 10
            reasoning_parts.append("Good transport access")
        elif transport > 40:
            score += 5
            reasoning_parts.append("Moderate transport access")
        else:
            reasoning_parts.append("Limited transport access")

        # Walkability/amenities
        amenity_score = location_data.get("amenity_score", 0)
        if amenity_score > 80:
            score += 15
            reasoning_parts.append("Excellent local amenities")
        elif amenity_score > 60:
            score += 10
            reasoning_parts.append("Good local amenities")

        # School catchments
        schools = location_data.get("school_catchments", [])
        good_schools = [s for s in schools if s.get("icsea_score", 0) > 1050]
        if good_schools:
            score += 10
            reasoning_parts.append(f"{len(good_schools)} high-performing school(s) nearby")

        # Crime rate
        crime_rate = location_data.get("crime_rate_per_1000", 0)
        if crime_rate > 0:
            if crime_rate < 50:
                score += 10
                reasoning_parts.append("Low crime area")
            elif crime_rate > 100:
                score -= 15
                reasoning_parts.append("High crime area")

        # Distance to CBD
        cbd_distance = location_data.get("cbd_distance_km", 0)
        if cbd_distance > 0:
            if cbd_distance < 10:
                score += 10
                reasoning_parts.append(f"Inner suburb ({cbd_distance:.1f}km to CBD)")
            elif cbd_distance < 20:
                score += 5
                reasoning_parts.append(f"Middle ring ({cbd_distance:.1f}km to CBD)")
            elif cbd_distance > 30:
                score -= 5
                reasoning_parts.append(f"Outer suburb ({cbd_distance:.1f}km to CBD)")

        if not reasoning_parts:
            data_quality = "limited"
            reasoning_parts.append("Limited location data available")

        score = max(0, min(100, score))
        weight = self.weights["location"]["weight"]

        return ScoreComponent(
            name="Location Fundamentals",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            reasoning="; ".join(reasoning_parts),
            data_quality=data_quality
        )

    def _score_to_grade(self, score: float) -> InvestmentGrade:
        """Convert numeric score to investment grade."""
        if score >= 80:
            return InvestmentGrade.PREMIUM
        elif score >= 65:
            return InvestmentGrade.STRONG
        elif score >= 50:
            return InvestmentGrade.ACCEPTABLE
        elif score >= 35:
            return InvestmentGrade.MARGINAL
        else:
            return InvestmentGrade.AVOID

    def _calculate_yield_fit(
        self,
        components: List[ScoreComponent],
        financial_data: Dict[str, Any]
    ) -> float:
        """Calculate fit score for yield-focused strategy."""
        yield_component = next((c for c in components if "Yield" in c.name), None)
        holding_component = next((c for c in components if "Holding" in c.name), None)

        score = 50
        if yield_component:
            score = yield_component.score * 0.6
        if holding_component:
            score += holding_component.score * 0.4

        # Cash flow is critical for yield strategy
        cash_flow = financial_data.get("summary", {}).get("monthly_cash_flow", 0)
        if cash_flow > 0:
            score = min(100, score + 15)
        elif cash_flow < -300:
            score = max(0, score - 20)

        return score

    def _calculate_growth_fit(
        self,
        components: List[ScoreComponent],
        location_data: Dict[str, Any]
    ) -> float:
        """Calculate fit score for growth-focused strategy."""
        growth_component = next((c for c in components if "Growth" in c.name), None)
        location_component = next((c for c in components if "Location" in c.name), None)

        score = 50
        if growth_component:
            score = growth_component.score * 0.6
        if location_component:
            score += location_component.score * 0.4

        # Infrastructure is key for growth
        transport = location_data.get("transport_score", 0)
        if transport > 70:
            score = min(100, score + 10)

        return score

    def _calculate_value_add_fit(
        self,
        components: List[ScoreComponent],
        property_data: Dict[str, Any]
    ) -> float:
        """Calculate fit score for value-add strategy."""
        dev_component = next((c for c in components if "Development" in c.name), None)

        score = 50
        if dev_component:
            score = dev_component.score * 0.7

        # Land size matters
        land_size = property_data.get("land_size", 0)
        if land_size > 600:
            score = min(100, score + 20)
        elif land_size > 400:
            score = min(100, score + 10)

        return score

    def _recommend_strategy(
        self,
        yield_fit: float,
        growth_fit: float,
        value_add_fit: float
    ) -> InvestmentStrategy:
        """Recommend investment strategy based on fit scores."""
        scores = {
            InvestmentStrategy.YIELD_FOCUSED: yield_fit,
            InvestmentStrategy.GROWTH_FOCUSED: growth_fit,
            InvestmentStrategy.VALUE_ADD: value_add_fit
        }

        best = max(scores, key=scores.get)
        best_score = scores[best]

        # Check if balanced is better
        avg = (yield_fit + growth_fit) / 2
        if abs(yield_fit - growth_fit) < 10 and avg > best_score - 5:
            return InvestmentStrategy.BALANCED

        return best

    def _identify_strengths_weaknesses(
        self,
        components: List[ScoreComponent]
    ) -> tuple:
        """Identify strengths and weaknesses from component scores."""
        strengths = []
        weaknesses = []

        for component in components:
            if component.score >= 70:
                strengths.append(f"{component.name}: {component.reasoning}")
            elif component.score <= 40:
                weaknesses.append(f"{component.name}: {component.reasoning}")

        return strengths, weaknesses

    def _identify_opportunities_threats(
        self,
        property_data: Dict[str, Any],
        location_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> tuple:
        """Identify opportunities and threats."""
        opportunities = []
        threats = []

        # Opportunities
        if property_data.get("land_size", 0) > 600:
            zone = property_data.get("zone_code", "")
            if zone and not zone.upper().startswith("NRZ"):
                opportunities.append("Development potential for subdivision or multi-unit")

        if location_data.get("planned_infrastructure"):
            opportunities.append("Planned infrastructure may boost values")

        if market_data.get("vacancy_rate", 0) < 2:
            opportunities.append("Low vacancy rate supports rental demand")

        # Threats
        if market_data.get("days_on_market", 0) > 60:
            threats.append("Extended selling times in current market")

        if market_data.get("supply_pipeline", 0) > 1000:
            threats.append("High development pipeline may impact values")

        overlays = property_data.get("overlays", [])
        if any("LSIO" in str(o) or "SBO" in str(o) for o in overlays):
            threats.append("Flood overlay may impact insurance and value")

        return opportunities, threats

    def _generate_recommendations(
        self,
        result: InvestmentScore,
        property_data: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if result.investment_grade == InvestmentGrade.PREMIUM:
            recommendations.append(
                "Premium investment opportunity - act quickly in competitive market"
            )
        elif result.investment_grade == InvestmentGrade.STRONG:
            recommendations.append(
                "Strong investment - proceed with standard due diligence"
            )
        elif result.investment_grade == InvestmentGrade.ACCEPTABLE:
            recommendations.append(
                "Acceptable investment - consider negotiating on price"
            )
        elif result.investment_grade == InvestmentGrade.MARGINAL:
            recommendations.append(
                "Marginal investment - proceed only if specific strategic fit"
            )
        else:
            recommendations.append(
                "Does not meet investment criteria - recommend pass"
            )

        # Strategy-specific recommendations
        if result.recommended_strategy == InvestmentStrategy.YIELD_FOCUSED:
            recommendations.append(
                "Best suited for yield-focused investors seeking cash flow"
            )
        elif result.recommended_strategy == InvestmentStrategy.GROWTH_FOCUSED:
            recommendations.append(
                "Best suited for growth investors with longer time horizon"
            )
        elif result.recommended_strategy == InvestmentStrategy.VALUE_ADD:
            recommendations.append(
                "Best suited for value-add investors with development capability"
            )

        # Address weaknesses
        for weakness in result.weaknesses[:2]:
            if "Yield" in weakness:
                recommendations.append("Consider rent reviews or value-add to improve yield")
            elif "Risk" in weakness:
                recommendations.append("Additional due diligence recommended to mitigate risks")

        return recommendations

    def _calculate_confidence(self, components: List[ScoreComponent]) -> float:
        """Calculate confidence level based on data quality."""
        qualities = [c.data_quality for c in components]

        good_count = qualities.count("good")
        limited_count = qualities.count("limited")

        return good_count / len(qualities) if qualities else 0.5


# Convenience functions
def calculate_investment_score(
    property_data: Dict[str, Any],
    financial_data: Dict[str, Any],
    risk_data: Dict[str, Any],
    location_data: Dict[str, Any],
    market_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Quick investment score calculation.

    Returns comprehensive investment analysis.
    """
    scorer = InvestmentScorer()
    result = scorer.calculate_investment_score(
        property_data, financial_data, risk_data, location_data, market_data
    )
    return result.to_dict()
