"""
Portfolio Alignment Module.

Matches properties against client briefs to determine suitability.
Used by Pathway Property for client matching and property shortlisting.

Features:
- Client brief matching
- Portfolio diversification analysis
- Risk tolerance alignment
- Investment strategy fit
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import date


class InvestorProfile(str, Enum):
    """Investor risk profile."""
    CONSERVATIVE = "conservative"      # Low risk, stable yield
    MODERATE = "moderate"              # Balanced risk/return
    GROWTH = "growth"                  # Higher risk, higher return
    AGGRESSIVE = "aggressive"          # Maximum growth potential


class PropertyPreference(str, Enum):
    """Property type preferences."""
    HOUSE = "house"
    TOWNHOUSE = "townhouse"
    APARTMENT = "apartment"
    COMMERCIAL = "commercial"
    DEVELOPMENT_SITE = "development_site"
    ANY = "any"


class LocationPreference(str, Enum):
    """Location preference tiers."""
    INNER_CITY = "inner_city"          # <10km from CBD
    INNER_METRO = "inner_metro"        # 10-20km
    OUTER_METRO = "outer_metro"        # 20-40km
    REGIONAL = "regional"              # >40km
    ANY = "any"


@dataclass
class ClientBrief:
    """
    Client investment brief specification.

    Captures client's investment criteria for matching.
    """
    # Client identification
    client_id: str
    client_name: str
    brief_date: str = ""

    # Investment profile
    investor_profile: InvestorProfile = InvestorProfile.MODERATE
    investment_strategy: str = "balanced"  # yield, growth, balanced, value_add

    # Budget
    budget_min: float = 0
    budget_max: float = 0
    deposit_available: float = 0
    borrowing_capacity: float = 0

    # Property preferences
    property_types: List[PropertyPreference] = field(default_factory=list)
    location_preference: LocationPreference = LocationPreference.ANY
    preferred_suburbs: List[str] = field(default_factory=list)
    excluded_suburbs: List[str] = field(default_factory=list)

    # Yield requirements
    minimum_yield: float = 0.0       # Gross yield %
    minimum_cashflow: float = 0.0    # Monthly cash flow
    accepts_negative_gearing: bool = True

    # Physical requirements
    min_bedrooms: int = 0
    min_bathrooms: int = 0
    min_land_size: float = 0         # sqm
    min_building_size: float = 0     # sqm
    requires_parking: bool = False
    parking_spaces: int = 0

    # Location requirements
    max_cbd_distance: float = 0      # km (0 = no preference)
    requires_public_transport: bool = False
    max_transport_distance: float = 0  # km

    # Deal breakers
    no_heritage_overlay: bool = False
    no_flood_overlay: bool = False
    no_bushfire_zone: bool = False
    no_strata: bool = False
    no_high_density: bool = False

    # Special requirements
    development_potential: bool = False
    smsf_compliant: bool = False
    suitable_for_rooming_house: bool = False

    # Portfolio considerations
    existing_portfolio_suburbs: List[str] = field(default_factory=list)
    existing_portfolio_types: List[str] = field(default_factory=list)
    diversification_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "client_name": self.client_name,
            "brief_date": self.brief_date,
            "investor_profile": self.investor_profile.value,
            "investment_strategy": self.investment_strategy,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "property_types": [p.value for p in self.property_types],
            "location_preference": self.location_preference.value,
            "preferred_suburbs": self.preferred_suburbs,
            "excluded_suburbs": self.excluded_suburbs,
            "minimum_yield": self.minimum_yield,
            "minimum_cashflow": self.minimum_cashflow,
            "min_bedrooms": self.min_bedrooms,
            "min_land_size": self.min_land_size,
            "development_potential": self.development_potential,
            "smsf_compliant": self.smsf_compliant
        }


@dataclass
class CriterionMatch:
    """Individual criterion matching result."""
    criterion: str
    met: bool
    importance: str  # critical, high, medium, low
    score: float     # 0-100
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion": self.criterion,
            "met": self.met,
            "importance": self.importance,
            "score": round(self.score, 1),
            "details": self.details
        }


@dataclass
class AlignmentResult:
    """Portfolio alignment analysis result."""
    overall_alignment_score: float = 0.0
    alignment_grade: str = "C"         # A-F
    recommendation: str = ""

    # Match summary
    critical_criteria_met: int = 0
    critical_criteria_total: int = 0
    high_criteria_met: int = 0
    high_criteria_total: int = 0

    # Individual matches
    criterion_matches: List[CriterionMatch] = field(default_factory=list)

    # Deal breakers
    deal_breakers_triggered: List[str] = field(default_factory=list)
    has_deal_breakers: bool = False

    # Fit analysis
    budget_fit: str = ""
    yield_fit: str = ""
    location_fit: str = ""
    property_type_fit: str = ""
    strategy_fit: str = ""

    # Portfolio diversification
    diversification_score: float = 0.0
    diversification_notes: List[str] = field(default_factory=list)

    # Recommendations
    strengths_for_client: List[str] = field(default_factory=list)
    concerns_for_client: List[str] = field(default_factory=list)
    conditions_to_negotiate: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_alignment_score": round(self.overall_alignment_score, 1),
            "alignment_grade": self.alignment_grade,
            "recommendation": self.recommendation,
            "critical_criteria_met": self.critical_criteria_met,
            "critical_criteria_total": self.critical_criteria_total,
            "high_criteria_met": self.high_criteria_met,
            "high_criteria_total": self.high_criteria_total,
            "criterion_matches": [c.to_dict() for c in self.criterion_matches],
            "deal_breakers_triggered": self.deal_breakers_triggered,
            "has_deal_breakers": self.has_deal_breakers,
            "budget_fit": self.budget_fit,
            "yield_fit": self.yield_fit,
            "location_fit": self.location_fit,
            "property_type_fit": self.property_type_fit,
            "strategy_fit": self.strategy_fit,
            "diversification_score": round(self.diversification_score, 1),
            "diversification_notes": self.diversification_notes,
            "strengths_for_client": self.strengths_for_client,
            "concerns_for_client": self.concerns_for_client,
            "conditions_to_negotiate": self.conditions_to_negotiate
        }


class PortfolioAligner:
    """
    Matches properties against client briefs.

    Used by buyer's advocates to quickly assess property suitability
    for specific client requirements.
    """

    def __init__(self):
        # Criterion weights
        self.weights = {
            "critical": 3.0,
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5
        }

    def calculate_alignment(
        self,
        client_brief: ClientBrief,
        property_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        location_data: Dict[str, Any],
        investment_score: Optional[Dict[str, Any]] = None
    ) -> AlignmentResult:
        """
        Calculate how well a property aligns with client brief.

        Args:
            client_brief: Client's investment requirements
            property_data: Property details
            financial_data: Financial analysis results
            location_data: Location analysis
            investment_score: Optional investment scoring results

        Returns:
            AlignmentResult with comprehensive matching analysis
        """
        result = AlignmentResult()
        matches = []
        deal_breakers = []

        # =====================================================================
        # CRITICAL CRITERIA (Must meet)
        # =====================================================================

        # Budget alignment
        price = property_data.get("purchase_price", 0) or property_data.get("asking_price", 0)
        budget_match = self._check_budget(client_brief, price)
        matches.append(budget_match)
        if not budget_match.met and budget_match.importance == "critical":
            deal_breakers.append(budget_match.details)

        # Property type alignment
        type_match = self._check_property_type(client_brief, property_data)
        matches.append(type_match)
        if not type_match.met and type_match.importance == "critical":
            deal_breakers.append(type_match.details)

        # Location alignment
        location_match = self._check_location(client_brief, property_data, location_data)
        matches.append(location_match)
        if not location_match.met and location_match.importance == "critical":
            deal_breakers.append(location_match.details)

        # Deal breaker overlays
        overlay_match = self._check_deal_breaker_overlays(client_brief, property_data)
        matches.append(overlay_match)
        if not overlay_match.met:
            deal_breakers.append(overlay_match.details)

        # =====================================================================
        # HIGH IMPORTANCE CRITERIA
        # =====================================================================

        # Yield requirements
        yield_match = self._check_yield(client_brief, financial_data)
        matches.append(yield_match)

        # Cash flow requirements
        cashflow_match = self._check_cashflow(client_brief, financial_data)
        matches.append(cashflow_match)

        # Bedrooms
        bedroom_match = self._check_bedrooms(client_brief, property_data)
        matches.append(bedroom_match)

        # Land size
        land_match = self._check_land_size(client_brief, property_data)
        matches.append(land_match)

        # =====================================================================
        # MEDIUM IMPORTANCE CRITERIA
        # =====================================================================

        # Transport access
        transport_match = self._check_transport(client_brief, location_data)
        matches.append(transport_match)

        # Parking
        parking_match = self._check_parking(client_brief, property_data)
        matches.append(parking_match)

        # Development potential
        dev_match = self._check_development_potential(client_brief, property_data)
        matches.append(dev_match)

        # =====================================================================
        # LOW IMPORTANCE CRITERIA (Nice to have)
        # =====================================================================

        # Building size
        building_match = self._check_building_size(client_brief, property_data)
        matches.append(building_match)

        # Investment strategy fit
        strategy_match = self._check_strategy_fit(
            client_brief, investment_score or {}
        )
        matches.append(strategy_match)

        # Store all matches
        result.criterion_matches = matches

        # Count criticals and highs
        critical_matches = [m for m in matches if m.importance == "critical"]
        high_matches = [m for m in matches if m.importance == "high"]

        result.critical_criteria_total = len(critical_matches)
        result.critical_criteria_met = sum(1 for m in critical_matches if m.met)
        result.high_criteria_total = len(high_matches)
        result.high_criteria_met = sum(1 for m in high_matches if m.met)

        # Deal breakers
        result.deal_breakers_triggered = deal_breakers
        result.has_deal_breakers = len(deal_breakers) > 0

        # Calculate overall score
        result.overall_alignment_score = self._calculate_overall_score(matches)

        # Determine grade
        result.alignment_grade = self._score_to_grade(
            result.overall_alignment_score,
            result.has_deal_breakers
        )

        # Generate fit summaries
        result.budget_fit = budget_match.details
        result.yield_fit = yield_match.details
        result.location_fit = location_match.details
        result.property_type_fit = type_match.details
        result.strategy_fit = strategy_match.details

        # Portfolio diversification
        result.diversification_score, result.diversification_notes = \
            self._check_diversification(client_brief, property_data)

        # Generate recommendation
        result.recommendation = self._generate_recommendation(result)

        # Strengths and concerns
        result.strengths_for_client = [
            m.details for m in matches
            if m.met and m.score >= 70
        ][:5]

        result.concerns_for_client = [
            m.details for m in matches
            if not m.met and m.importance in ["critical", "high"]
        ]

        # Negotiation conditions
        result.conditions_to_negotiate = self._identify_negotiation_points(
            matches, property_data, financial_data
        )

        return result

    def _check_budget(self, brief: ClientBrief, price: float) -> CriterionMatch:
        """Check if property is within budget."""
        if price == 0:
            return CriterionMatch(
                criterion="Budget",
                met=False,
                importance="critical",
                score=0,
                details="Price not available"
            )

        # Allow 5% buffer above max
        effective_max = brief.budget_max * 1.05 if brief.budget_max else float('inf')

        if brief.budget_min <= price <= effective_max:
            # Calculate how centered in budget
            if brief.budget_max > brief.budget_min:
                mid_budget = (brief.budget_min + brief.budget_max) / 2
                deviation = abs(price - mid_budget) / mid_budget
                score = max(50, 100 - (deviation * 100))
            else:
                score = 80

            return CriterionMatch(
                criterion="Budget",
                met=True,
                importance="critical",
                score=score,
                details=f"Within budget (${price:,.0f} in ${brief.budget_min:,.0f}-${brief.budget_max:,.0f} range)"
            )
        elif price < brief.budget_min:
            return CriterionMatch(
                criterion="Budget",
                met=True,  # Under budget is OK
                importance="critical",
                score=70,
                details=f"Below minimum budget (${price:,.0f} < ${brief.budget_min:,.0f})"
            )
        else:
            over_percent = ((price - brief.budget_max) / brief.budget_max) * 100
            return CriterionMatch(
                criterion="Budget",
                met=False,
                importance="critical",
                score=max(0, 50 - over_percent),
                details=f"Over budget by {over_percent:.1f}% (${price:,.0f} > ${brief.budget_max:,.0f})"
            )

    def _check_property_type(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check property type alignment."""
        prop_type = property_data.get("property_type", "").lower()

        if not brief.property_types or PropertyPreference.ANY in brief.property_types:
            return CriterionMatch(
                criterion="Property Type",
                met=True,
                importance="critical",
                score=80,
                details=f"Property type ({prop_type}) - no preference specified"
            )

        # Map property type to preference
        type_mapping = {
            "house": PropertyPreference.HOUSE,
            "townhouse": PropertyPreference.TOWNHOUSE,
            "apartment": PropertyPreference.APARTMENT,
            "unit": PropertyPreference.APARTMENT,
            "commercial": PropertyPreference.COMMERCIAL,
            "land": PropertyPreference.DEVELOPMENT_SITE
        }

        mapped_type = type_mapping.get(prop_type)

        if mapped_type and mapped_type in brief.property_types:
            return CriterionMatch(
                criterion="Property Type",
                met=True,
                importance="critical",
                score=100,
                details=f"Property type ({prop_type}) matches preference"
            )
        else:
            return CriterionMatch(
                criterion="Property Type",
                met=False,
                importance="critical",
                score=0,
                details=f"Property type ({prop_type}) not in preferred list"
            )

    def _check_location(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any],
        location_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check location alignment."""
        suburb = property_data.get("suburb", "").lower()
        cbd_distance = location_data.get("cbd_distance_km", 0)

        # Check excluded suburbs first
        if suburb and suburb in [s.lower() for s in brief.excluded_suburbs]:
            return CriterionMatch(
                criterion="Location",
                met=False,
                importance="critical",
                score=0,
                details=f"Suburb ({suburb}) is in excluded list"
            )

        # Check preferred suburbs
        if brief.preferred_suburbs:
            if suburb in [s.lower() for s in brief.preferred_suburbs]:
                return CriterionMatch(
                    criterion="Location",
                    met=True,
                    importance="critical",
                    score=100,
                    details=f"Suburb ({suburb}) is in preferred list"
                )
            else:
                return CriterionMatch(
                    criterion="Location",
                    met=False,
                    importance="high",
                    score=40,
                    details=f"Suburb ({suburb}) not in preferred list"
                )

        # Check location tier preference
        if brief.location_preference != LocationPreference.ANY:
            tier_ranges = {
                LocationPreference.INNER_CITY: (0, 10),
                LocationPreference.INNER_METRO: (10, 20),
                LocationPreference.OUTER_METRO: (20, 40),
                LocationPreference.REGIONAL: (40, 200)
            }

            min_dist, max_dist = tier_ranges.get(brief.location_preference, (0, 200))

            if min_dist <= cbd_distance <= max_dist:
                return CriterionMatch(
                    criterion="Location",
                    met=True,
                    importance="high",
                    score=85,
                    details=f"Location ({cbd_distance:.1f}km from CBD) matches {brief.location_preference.value} preference"
                )
            else:
                return CriterionMatch(
                    criterion="Location",
                    met=False,
                    importance="high",
                    score=40,
                    details=f"Location ({cbd_distance:.1f}km from CBD) outside preferred {brief.location_preference.value}"
                )

        # Check max distance
        if brief.max_cbd_distance > 0:
            if cbd_distance <= brief.max_cbd_distance:
                return CriterionMatch(
                    criterion="Location",
                    met=True,
                    importance="high",
                    score=80,
                    details=f"Within max distance ({cbd_distance:.1f}km <= {brief.max_cbd_distance}km)"
                )
            else:
                return CriterionMatch(
                    criterion="Location",
                    met=False,
                    importance="high",
                    score=30,
                    details=f"Exceeds max distance ({cbd_distance:.1f}km > {brief.max_cbd_distance}km)"
                )

        return CriterionMatch(
            criterion="Location",
            met=True,
            importance="medium",
            score=70,
            details=f"Location ({suburb}) - no specific preference"
        )

    def _check_deal_breaker_overlays(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check for deal-breaker overlays."""
        overlays = property_data.get("overlays", [])
        overlay_str = " ".join(str(o) for o in overlays).upper()
        triggered = []

        if brief.no_heritage_overlay and "HO" in overlay_str:
            triggered.append("Heritage Overlay")

        if brief.no_flood_overlay and ("LSIO" in overlay_str or "SBO" in overlay_str):
            triggered.append("Flood Overlay")

        if brief.no_bushfire_zone and ("BMO" in overlay_str or "WMO" in overlay_str):
            triggered.append("Bushfire Zone")

        if brief.no_strata and property_data.get("is_strata", False):
            triggered.append("Strata Title")

        zone = property_data.get("zone_code", "").upper()
        if brief.no_high_density and zone[:3] in ["RGZ", "MUZ", "ACZ"]:
            triggered.append(f"High Density Zone ({zone})")

        if triggered:
            return CriterionMatch(
                criterion="Deal Breakers",
                met=False,
                importance="critical",
                score=0,
                details=f"Deal breakers triggered: {', '.join(triggered)}"
            )
        else:
            return CriterionMatch(
                criterion="Deal Breakers",
                met=True,
                importance="critical",
                score=100,
                details="No deal breakers triggered"
            )

    def _check_yield(
        self,
        brief: ClientBrief,
        financial_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check yield requirements."""
        if brief.minimum_yield == 0:
            return CriterionMatch(
                criterion="Yield",
                met=True,
                importance="medium",
                score=80,
                details="No minimum yield specified"
            )

        gross_yield = financial_data.get("summary", {}).get("gross_yield_percent", 0)

        if gross_yield >= brief.minimum_yield:
            excess = gross_yield - brief.minimum_yield
            score = min(100, 70 + (excess * 10))
            return CriterionMatch(
                criterion="Yield",
                met=True,
                importance="high",
                score=score,
                details=f"Yield {gross_yield:.1f}% meets minimum {brief.minimum_yield:.1f}%"
            )
        else:
            shortfall = brief.minimum_yield - gross_yield
            score = max(0, 60 - (shortfall * 15))
            return CriterionMatch(
                criterion="Yield",
                met=False,
                importance="high",
                score=score,
                details=f"Yield {gross_yield:.1f}% below minimum {brief.minimum_yield:.1f}%"
            )

    def _check_cashflow(
        self,
        brief: ClientBrief,
        financial_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check cash flow requirements."""
        monthly_cf = financial_data.get("summary", {}).get("monthly_cash_flow", 0)

        if brief.minimum_cashflow == 0 and brief.accepts_negative_gearing:
            return CriterionMatch(
                criterion="Cash Flow",
                met=True,
                importance="medium",
                score=70 if monthly_cf >= 0 else 50,
                details=f"Cash flow ${monthly_cf:,.0f}/month (negative gearing accepted)"
            )

        if not brief.accepts_negative_gearing and monthly_cf < 0:
            return CriterionMatch(
                criterion="Cash Flow",
                met=False,
                importance="high",
                score=20,
                details=f"Negative cash flow ${monthly_cf:,.0f}/month (not accepted by client)"
            )

        if monthly_cf >= brief.minimum_cashflow:
            return CriterionMatch(
                criterion="Cash Flow",
                met=True,
                importance="high",
                score=85,
                details=f"Cash flow ${monthly_cf:,.0f}/month meets minimum ${brief.minimum_cashflow:,.0f}"
            )
        else:
            return CriterionMatch(
                criterion="Cash Flow",
                met=False,
                importance="high",
                score=40,
                details=f"Cash flow ${monthly_cf:,.0f}/month below minimum ${brief.minimum_cashflow:,.0f}"
            )

    def _check_bedrooms(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check bedroom requirements."""
        bedrooms = property_data.get("bedrooms", 0)

        if brief.min_bedrooms == 0:
            return CriterionMatch(
                criterion="Bedrooms",
                met=True,
                importance="low",
                score=80,
                details=f"{bedrooms} bedrooms - no minimum specified"
            )

        if bedrooms >= brief.min_bedrooms:
            return CriterionMatch(
                criterion="Bedrooms",
                met=True,
                importance="high",
                score=90 if bedrooms == brief.min_bedrooms else 100,
                details=f"{bedrooms} bedrooms meets minimum {brief.min_bedrooms}"
            )
        else:
            return CriterionMatch(
                criterion="Bedrooms",
                met=False,
                importance="high",
                score=30,
                details=f"{bedrooms} bedrooms below minimum {brief.min_bedrooms}"
            )

    def _check_land_size(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check land size requirements."""
        land_size = property_data.get("land_size", 0)

        if brief.min_land_size == 0:
            return CriterionMatch(
                criterion="Land Size",
                met=True,
                importance="low",
                score=75,
                details=f"{land_size}sqm land - no minimum specified"
            )

        if land_size >= brief.min_land_size:
            excess_pct = ((land_size - brief.min_land_size) / brief.min_land_size) * 100
            score = min(100, 70 + min(30, excess_pct / 2))
            return CriterionMatch(
                criterion="Land Size",
                met=True,
                importance="high",
                score=score,
                details=f"{land_size}sqm meets minimum {brief.min_land_size}sqm"
            )
        else:
            shortfall = ((brief.min_land_size - land_size) / brief.min_land_size) * 100
            score = max(0, 60 - shortfall)
            return CriterionMatch(
                criterion="Land Size",
                met=False,
                importance="high",
                score=score,
                details=f"{land_size}sqm below minimum {brief.min_land_size}sqm"
            )

    def _check_transport(
        self,
        brief: ClientBrief,
        location_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check transport access requirements."""
        if not brief.requires_public_transport:
            transport_score = location_data.get("transport_score", 50)
            return CriterionMatch(
                criterion="Transport",
                met=True,
                importance="low",
                score=transport_score,
                details=f"Transport score: {transport_score}/100"
            )

        nearest_station = location_data.get("nearest_train_km", 99)
        nearest_tram = location_data.get("nearest_tram_km", 99)

        if brief.max_transport_distance > 0:
            if nearest_station <= brief.max_transport_distance or \
               nearest_tram <= brief.max_transport_distance:
                return CriterionMatch(
                    criterion="Transport",
                    met=True,
                    importance="high",
                    score=85,
                    details=f"Public transport within {brief.max_transport_distance}km"
                )
            else:
                return CriterionMatch(
                    criterion="Transport",
                    met=False,
                    importance="high",
                    score=30,
                    details=f"Public transport beyond {brief.max_transport_distance}km"
                )

        transport_score = location_data.get("transport_score", 50)
        return CriterionMatch(
            criterion="Transport",
            met=transport_score >= 60,
            importance="medium",
            score=transport_score,
            details=f"Transport score: {transport_score}/100"
        )

    def _check_parking(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check parking requirements."""
        if not brief.requires_parking:
            return CriterionMatch(
                criterion="Parking",
                met=True,
                importance="low",
                score=80,
                details="No parking requirement"
            )

        parking = property_data.get("parking_spaces", 0)

        if parking >= brief.parking_spaces:
            return CriterionMatch(
                criterion="Parking",
                met=True,
                importance="medium",
                score=90,
                details=f"{parking} parking spaces meets requirement"
            )
        else:
            return CriterionMatch(
                criterion="Parking",
                met=False,
                importance="medium",
                score=40,
                details=f"{parking} parking spaces below requirement of {brief.parking_spaces}"
            )

    def _check_development_potential(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check development potential if required."""
        if not brief.development_potential:
            return CriterionMatch(
                criterion="Development Potential",
                met=True,
                importance="low",
                score=70,
                details="Development potential not required"
            )

        land_size = property_data.get("land_size", 0)
        zone = property_data.get("zone_code", "").upper()

        # Development-friendly zones
        dev_zones = ["RGZ", "GRZ", "MUZ", "ACZ", "C1Z", "C2Z"]
        zone_prefix = zone[:3] if len(zone) >= 3 else zone

        has_potential = (
            zone_prefix in dev_zones and
            land_size >= 400 and
            not any("HO" in str(o) for o in property_data.get("overlays", []))
        )

        if has_potential:
            score = min(100, 60 + (land_size - 400) / 20)
            return CriterionMatch(
                criterion="Development Potential",
                met=True,
                importance="high",
                score=score,
                details=f"Development potential in {zone} with {land_size}sqm"
            )
        else:
            return CriterionMatch(
                criterion="Development Potential",
                met=False,
                importance="high",
                score=25,
                details="Limited development potential"
            )

    def _check_building_size(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> CriterionMatch:
        """Check building size requirements."""
        building_size = property_data.get("building_size", 0)

        if brief.min_building_size == 0:
            return CriterionMatch(
                criterion="Building Size",
                met=True,
                importance="low",
                score=75,
                details=f"{building_size}sqm building - no minimum specified"
            )

        if building_size >= brief.min_building_size:
            return CriterionMatch(
                criterion="Building Size",
                met=True,
                importance="medium",
                score=85,
                details=f"{building_size}sqm meets minimum {brief.min_building_size}sqm"
            )
        else:
            return CriterionMatch(
                criterion="Building Size",
                met=False,
                importance="medium",
                score=40,
                details=f"{building_size}sqm below minimum {brief.min_building_size}sqm"
            )

    def _check_strategy_fit(
        self,
        brief: ClientBrief,
        investment_score: Dict[str, Any]
    ) -> CriterionMatch:
        """Check investment strategy fit."""
        if not investment_score:
            return CriterionMatch(
                criterion="Strategy Fit",
                met=True,
                importance="low",
                score=60,
                details="Investment scoring not available"
            )

        recommended = investment_score.get("recommended_strategy", "")
        client_strategy = brief.investment_strategy.lower()

        strategy_mapping = {
            "yield": "yield_focused",
            "growth": "growth_focused",
            "balanced": "balanced",
            "value_add": "value_add"
        }

        client_mapped = strategy_mapping.get(client_strategy, "balanced")

        if recommended == client_mapped:
            return CriterionMatch(
                criterion="Strategy Fit",
                met=True,
                importance="medium",
                score=95,
                details=f"Property suits {client_strategy} strategy"
            )
        elif recommended == "balanced":
            return CriterionMatch(
                criterion="Strategy Fit",
                met=True,
                importance="medium",
                score=75,
                details=f"Property suits balanced strategy (client: {client_strategy})"
            )
        else:
            # Get fit scores
            fit_scores = {
                "yield_focused": investment_score.get("yield_fit_score", 50),
                "growth_focused": investment_score.get("growth_fit_score", 50),
                "value_add": investment_score.get("value_add_fit_score", 50)
            }
            client_fit = fit_scores.get(client_mapped, 50)

            return CriterionMatch(
                criterion="Strategy Fit",
                met=client_fit >= 60,
                importance="medium",
                score=client_fit,
                details=f"Property better suited to {recommended} (client: {client_strategy})"
            )

    def _check_diversification(
        self,
        brief: ClientBrief,
        property_data: Dict[str, Any]
    ) -> tuple:
        """Check portfolio diversification."""
        notes = []
        score = 80  # Base score

        suburb = property_data.get("suburb", "").lower()
        prop_type = property_data.get("property_type", "").lower()

        if not brief.diversification_required:
            return 80, ["Diversification not required"]

        # Check suburb concentration
        if suburb in [s.lower() for s in brief.existing_portfolio_suburbs]:
            score -= 20
            notes.append(f"Already have property in {suburb}")
        else:
            notes.append(f"New suburb ({suburb}) adds diversification")

        # Check property type concentration
        if prop_type in [t.lower() for t in brief.existing_portfolio_types]:
            score -= 10
            notes.append(f"Already have {prop_type} in portfolio")
        else:
            notes.append(f"New property type ({prop_type}) adds diversification")

        return max(0, min(100, score)), notes

    def _calculate_overall_score(self, matches: List[CriterionMatch]) -> float:
        """Calculate weighted overall alignment score."""
        total_weighted = 0
        total_weight = 0

        for match in matches:
            weight = self.weights.get(match.importance, 1.0)
            total_weighted += match.score * weight
            total_weight += weight

        return (total_weighted / total_weight) if total_weight > 0 else 50

    def _score_to_grade(self, score: float, has_deal_breakers: bool) -> str:
        """Convert score to letter grade."""
        if has_deal_breakers:
            return "F"

        if score >= 85:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 45:
            return "D"
        else:
            return "F"

    def _generate_recommendation(self, result: AlignmentResult) -> str:
        """Generate recommendation based on alignment."""
        if result.has_deal_breakers:
            return f"NOT RECOMMENDED - Deal breakers: {', '.join(result.deal_breakers_triggered)}"

        if result.alignment_grade == "A":
            return "HIGHLY RECOMMENDED - Strong match with client brief"
        elif result.alignment_grade == "B":
            return "RECOMMENDED - Good match with minor gaps"
        elif result.alignment_grade == "C":
            return "CONSIDER - Acceptable match, some criteria not met"
        elif result.alignment_grade == "D":
            return "MARGINAL - Significant gaps from client requirements"
        else:
            return "NOT RECOMMENDED - Poor match with client brief"

    def _identify_negotiation_points(
        self,
        matches: List[CriterionMatch],
        property_data: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> List[str]:
        """Identify potential negotiation points."""
        points = []

        # Price negotiation
        budget_match = next((m for m in matches if m.criterion == "Budget"), None)
        if budget_match and "Over budget" in budget_match.details:
            points.append("Negotiate price reduction to bring within budget")

        # Yield improvement
        yield_match = next((m for m in matches if m.criterion == "Yield"), None)
        if yield_match and not yield_match.met:
            points.append("Negotiate lower purchase price to improve yield")
            points.append("Explore rent increase potential at settlement")

        # If strata, check levies
        if property_data.get("is_strata"):
            points.append("Request full strata financials before commitment")

        # Settlement terms
        points.append("Consider extended settlement for due diligence")

        return points[:5]


# Convenience function
def calculate_alignment_score(
    client_brief: Dict[str, Any],
    property_data: Dict[str, Any],
    financial_data: Dict[str, Any],
    location_data: Dict[str, Any],
    investment_score: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Quick alignment score calculation.

    Args:
        client_brief: Dict with client requirements (will be converted to ClientBrief)
        property_data: Property details
        financial_data: Financial analysis
        location_data: Location analysis
        investment_score: Optional investment scoring

    Returns:
        Dict with alignment analysis
    """
    # Convert dict to ClientBrief
    brief = ClientBrief(
        client_id=client_brief.get("client_id", "unknown"),
        client_name=client_brief.get("client_name", "Unknown"),
        budget_min=client_brief.get("budget_min", 0),
        budget_max=client_brief.get("budget_max", 0),
        minimum_yield=client_brief.get("minimum_yield", 0),
        minimum_cashflow=client_brief.get("minimum_cashflow", 0),
        min_bedrooms=client_brief.get("min_bedrooms", 0),
        min_land_size=client_brief.get("min_land_size", 0),
        preferred_suburbs=client_brief.get("preferred_suburbs", []),
        excluded_suburbs=client_brief.get("excluded_suburbs", []),
        no_heritage_overlay=client_brief.get("no_heritage_overlay", False),
        no_flood_overlay=client_brief.get("no_flood_overlay", False),
        no_strata=client_brief.get("no_strata", False),
        development_potential=client_brief.get("development_potential", False)
    )

    aligner = PortfolioAligner()
    result = aligner.calculate_alignment(
        brief, property_data, financial_data, location_data, investment_score
    )
    return result.to_dict()
