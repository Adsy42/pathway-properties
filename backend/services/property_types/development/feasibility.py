"""
Development feasibility analyzer.

Calculates development feasibility including:
- Maximum dwelling yield
- Construction costs
- Development margin
- Return on cost
"""

from typing import Optional, List, Dict, Any

from .models import (
    FeasibilityAssessment,
    SiteAnalysis,
    PlanningConstraints,
    FinancialModel,
    DevelopmentType
)


class DevelopmentFeasibilityAnalyzer:
    """
    Analyzer for development site feasibility.

    Uses Victorian planning scheme standards and current construction costs.
    """

    # Construction costs per sqm (2024 Melbourne estimates)
    CONSTRUCTION_COSTS = {
        "townhouse": {"low": 1800, "mid": 2200, "high": 2800},
        "apartment_lowrise": {"low": 2500, "mid": 3000, "high": 3800},
        "apartment_midrise": {"low": 3200, "mid": 3800, "high": 4500},
        "apartment_highrise": {"low": 4000, "mid": 4800, "high": 5500},
    }

    # Average dwelling sizes (sqm)
    DWELLING_SIZES = {
        "1bed_apt": 50,
        "2bed_apt": 75,
        "3bed_apt": 100,
        "2bed_townhouse": 120,
        "3bed_townhouse": 150,
        "4bed_townhouse": 180,
    }

    # Zone-based density (dwellings per hectare)
    ZONE_DENSITY = {
        "RGZ": {"min": 50, "max": 100},   # Residential Growth Zone
        "GRZ": {"min": 25, "max": 40},    # General Residential Zone
        "NRZ": {"min": 15, "max": 25},    # Neighbourhood Residential Zone
        "MUZ": {"min": 80, "max": 150},   # Mixed Use Zone
        "ACZ": {"min": 100, "max": 200},  # Activity Centre Zone
    }

    # Minimum lot sizes per dwelling
    MIN_LOT_SIZES = {
        "RGZ": 150,
        "GRZ": 300,
        "NRZ": 500,
        "MUZ": 100,
        "C1Z": 100,  # Commercial 1 Zone
    }

    # Target development margin (industry standard: 20%)
    TARGET_MARGIN = 20.0

    def analyze(
        self,
        address: str,
        land_area_sqm: float,
        purchase_price: float,
        zone_code: str,
        overlays: Optional[List[str]] = None,
        frontage_meters: Optional[float] = None,
        existing_dwellings: int = 1,
        suburb_median_price: Optional[float] = None,
        development_type: Optional[DevelopmentType] = None,
        proposed_dwellings: Optional[int] = None
    ) -> FeasibilityAssessment:
        """
        Perform development feasibility analysis.

        Args:
            address: Property address
            land_area_sqm: Land area in square meters
            purchase_price: Purchase price
            zone_code: Planning zone code (e.g., GRZ1, RGZ1)
            overlays: List of overlay codes
            frontage_meters: Site frontage
            existing_dwellings: Current number of dwellings
            suburb_median_price: Suburb median price for revenue estimation
            development_type: Type of development proposed
            proposed_dwellings: Specific dwelling count to model

        Returns:
            FeasibilityAssessment
        """
        overlays = overlays or []
        risks = []
        recommendations = []
        permit_considerations = []

        # Determine development type based on zone and size
        if not development_type:
            development_type = self._suggest_development_type(
                land_area_sqm, zone_code, frontage_meters
            )

        # Create site analysis
        site = SiteAnalysis(
            land_area_sqm=land_area_sqm,
            frontage_meters=frontage_meters,
            demolition_required=existing_dwellings > 0
        )

        # Create planning constraints
        planning = self._create_planning_constraints(zone_code, overlays)

        # Calculate maximum yield
        max_dwellings = self._calculate_max_yield(
            land_area_sqm, zone_code, frontage_meters, planning
        )

        # Use proposed dwellings or recommended amount
        if proposed_dwellings:
            dwellings = min(proposed_dwellings, max_dwellings)
        else:
            # Recommend 80% of max for approval probability
            dwellings = max(2, int(max_dwellings * 0.8))

        # Determine constraint
        yield_constraint = self._determine_yield_constraint(
            land_area_sqm, zone_code, frontage_meters, dwellings
        )

        # Calculate financial model
        financial = self._calculate_financials(
            land_cost=purchase_price,
            dwellings=dwellings,
            development_type=development_type,
            land_area_sqm=land_area_sqm,
            suburb_median=suburb_median_price or 700000,
            demolition_required=site.demolition_required
        )

        # Assess feasibility
        is_feasible = financial.development_margin_percent >= 15
        target_achieved = financial.development_margin_percent >= self.TARGET_MARGIN

        if financial.development_margin_percent >= 25:
            feasibility_rating = "strong"
        elif financial.development_margin_percent >= 20:
            feasibility_rating = "good"
        elif financial.development_margin_percent >= 15:
            feasibility_rating = "marginal"
        else:
            feasibility_rating = "unfeasible"

        # Assess planning risk
        permit_probability = self._assess_permit_probability(
            zone_code, overlays, dwellings, max_dwellings
        )

        # Identify risks
        if "HO" in str(overlays):
            risks.append("Heritage Overlay - design constraints likely")
            permit_considerations.append("Heritage impact assessment required")

        if "SLO" in str(overlays) or "VPO" in str(overlays):
            risks.append("Vegetation overlay - tree removal restrictions")
            permit_considerations.append("Vegetation assessment required")

        if "LSIO" in str(overlays) or "SBO" in str(overlays):
            risks.append("Flood overlay - may restrict building footprint")
            permit_considerations.append("Flood study may be required")

        if zone_code.upper().startswith("NRZ"):
            risks.append("NRZ limits development to 2 dwellings unless larger site")
            permit_considerations.append("Mandatory 2-dwelling limit in NRZ")

        if financial.development_margin_percent < 15:
            risks.append("Development margin below viable threshold")
            recommendations.append("Consider negotiating lower purchase price")

        if dwellings == max_dwellings:
            risks.append("At maximum yield - approval risk")
            recommendations.append("Consider reducing yield for smoother approval")

        # Timeline estimates
        permit_months = 6 if permit_probability == "high" else (9 if permit_probability == "medium" else 12)
        construction_months = 12 + (dwellings * 2)  # Rough estimate
        total_months = permit_months + construction_months + 3  # +3 for pre/post

        # Determine risk level
        if not is_feasible or permit_probability == "low":
            risk_level = "high"
        elif feasibility_rating == "marginal" or permit_probability == "medium":
            risk_level = "medium"
        else:
            risk_level = "low"

        # Add recommendations
        if not recommendations:
            if is_feasible and permit_probability in ["high", "medium"]:
                recommendations.append("Site appears viable for development")
            recommendations.append("Engage town planner for pre-application meeting")

        return FeasibilityAssessment(
            property_address=address,
            development_type=development_type,
            site_analysis=site,
            planning=planning,
            financial=financial,
            maximum_dwellings=max_dwellings,
            recommended_dwellings=dwellings,
            yield_constrained_by=yield_constraint,
            is_feasible=is_feasible,
            feasibility_rating=feasibility_rating,
            target_margin_achieved=target_achieved,
            risk_level=risk_level,
            key_risks=risks,
            permit_probability=permit_probability,
            permit_considerations=permit_considerations,
            permit_months=permit_months,
            construction_months=construction_months,
            total_project_months=total_months,
            recommendations=recommendations
        )

    def _suggest_development_type(
        self,
        land_area_sqm: float,
        zone_code: str,
        frontage: Optional[float]
    ) -> DevelopmentType:
        """Suggest appropriate development type."""
        zone_upper = zone_code.upper()

        if land_area_sqm < 400:
            return DevelopmentType.DUAL_OCCUPANCY
        elif land_area_sqm < 800:
            return DevelopmentType.TOWNHOUSES
        elif zone_upper.startswith(("RGZ", "MUZ", "ACZ", "C")):
            if land_area_sqm > 1500:
                return DevelopmentType.APARTMENTS
            return DevelopmentType.TOWNHOUSES
        else:
            return DevelopmentType.TOWNHOUSES

    def _create_planning_constraints(
        self,
        zone_code: str,
        overlays: List[str]
    ) -> PlanningConstraints:
        """Create planning constraints from zone and overlays."""
        zone_upper = zone_code.upper()[:3]

        # Default constraints
        constraints = PlanningConstraints(
            zone_code=zone_code,
            overlays=overlays,
            permit_required=True
        )

        # Zone-specific constraints
        if zone_upper == "GRZ":
            constraints.max_height_meters = 11
            constraints.max_stories = 3
            constraints.min_lot_size_sqm = 300
        elif zone_upper == "NRZ":
            constraints.max_height_meters = 9
            constraints.max_stories = 2
            constraints.min_lot_size_sqm = 500
        elif zone_upper == "RGZ":
            constraints.max_height_meters = 13.5
            constraints.max_stories = 4
            constraints.min_lot_size_sqm = 150
        elif zone_upper == "MUZ":
            constraints.max_height_meters = None  # DDO dependent
            constraints.min_lot_size_sqm = 100

        # Overlay impacts
        if any("HO" in o for o in overlays):
            constraints.heritage_constraints = True
        if any(o in overlays for o in ["SLO", "VPO", "ESO"]):
            constraints.vegetation_constraints = True
        if any(o in overlays for o in ["LSIO", "SBO", "FO"]):
            constraints.flooding_constraints = True

        return constraints

    def _calculate_max_yield(
        self,
        land_area_sqm: float,
        zone_code: str,
        frontage: Optional[float],
        planning: PlanningConstraints
    ) -> int:
        """Calculate maximum dwelling yield."""
        zone_upper = zone_code.upper()[:3]

        # Get minimum lot size
        min_lot = self.MIN_LOT_SIZES.get(zone_upper, 300)
        if planning.min_lot_size_sqm:
            min_lot = max(min_lot, planning.min_lot_size_sqm)

        # Base yield from land area
        base_yield = int(land_area_sqm / min_lot)

        # NRZ special rule - max 2 unless large site
        if zone_upper == "NRZ" and land_area_sqm < 650:
            base_yield = min(base_yield, 2)

        # Frontage constraint (need ~6m per dwelling for townhouses)
        if frontage:
            frontage_yield = int(frontage / 6)
            base_yield = min(base_yield, frontage_yield)

        return max(1, base_yield)

    def _determine_yield_constraint(
        self,
        land_area_sqm: float,
        zone_code: str,
        frontage: Optional[float],
        dwellings: int
    ) -> str:
        """Determine what's constraining yield."""
        zone_upper = zone_code.upper()[:3]
        min_lot = self.MIN_LOT_SIZES.get(zone_upper, 300)

        if zone_upper == "NRZ":
            return "NRZ 2-dwelling limit"

        area_yield = int(land_area_sqm / min_lot)
        if frontage:
            frontage_yield = int(frontage / 6)
            if frontage_yield < area_yield:
                return "frontage width"

        return "land area / minimum lot size"

    def _calculate_financials(
        self,
        land_cost: float,
        dwellings: int,
        development_type: DevelopmentType,
        land_area_sqm: float,
        suburb_median: float,
        demolition_required: bool
    ) -> FinancialModel:
        """Calculate development financial model."""
        # Revenue estimation
        if development_type == DevelopmentType.TOWNHOUSES:
            revenue_per_dwelling = suburb_median * 0.85  # Townhouses ~85% of median house
            build_sqm = 140  # Average townhouse size
            build_cost_sqm = self.CONSTRUCTION_COSTS["townhouse"]["mid"]
        elif development_type == DevelopmentType.APARTMENTS:
            revenue_per_dwelling = suburb_median * 0.5  # Apartments ~50% of median house
            build_sqm = 75  # Average apartment size
            build_cost_sqm = self.CONSTRUCTION_COSTS["apartment_lowrise"]["mid"]
        elif development_type == DevelopmentType.DUAL_OCCUPANCY:
            revenue_per_dwelling = suburb_median * 0.75
            build_sqm = 130
            build_cost_sqm = self.CONSTRUCTION_COSTS["townhouse"]["mid"]
        else:
            revenue_per_dwelling = suburb_median * 0.7
            build_sqm = 100
            build_cost_sqm = self.CONSTRUCTION_COSTS["townhouse"]["mid"]

        grv = revenue_per_dwelling * dwellings

        # Costs
        stamp_duty = land_cost * 0.055  # ~5.5% for investment
        demolition = 30000 if demolition_required else 0
        construction = build_cost_sqm * build_sqm * dwellings
        professional_fees = (land_cost + construction) * 0.08  # ~8%
        statutory = 15000 + (dwellings * 5000)  # Permits, contributions
        icp = dwellings * 10000  # Infrastructure contribution (varies)
        holding = land_cost * 0.06 * 1.5  # 18 months interest
        selling = grv * 0.025  # Agent fees ~2.5%
        contingency = construction * 0.05  # 5% contingency

        total_cost = (land_cost + stamp_duty + demolition + construction +
                     professional_fees + statutory + icp + holding +
                     selling + contingency)

        gross_profit = grv - total_cost
        margin = (gross_profit / grv * 100) if grv > 0 else 0
        roc = (gross_profit / total_cost * 100) if total_cost > 0 else 0

        return FinancialModel(
            gross_realization_value=grv,
            revenue_per_dwelling=revenue_per_dwelling,
            total_dwellings=dwellings,
            land_cost=land_cost,
            stamp_duty=stamp_duty,
            demolition_cost=demolition,
            construction_cost=construction,
            construction_per_sqm=build_cost_sqm,
            professional_fees=professional_fees,
            statutory_costs=statutory,
            infrastructure_contributions=icp,
            holding_costs=holding,
            selling_costs=selling,
            contingency=contingency,
            total_development_cost=total_cost,
            gross_profit=gross_profit,
            development_margin_percent=margin,
            return_on_cost=roc
        )

    def _assess_permit_probability(
        self,
        zone_code: str,
        overlays: List[str],
        proposed: int,
        maximum: int
    ) -> str:
        """Assess probability of planning permit approval."""
        zone_upper = zone_code.upper()[:3]

        # Start with base probability based on zone
        if zone_upper in ["RGZ", "MUZ", "ACZ"]:
            base = "high"
        elif zone_upper == "GRZ":
            base = "medium"
        else:
            base = "low"

        # Reduce for overlays
        if any("HO" in o for o in overlays):
            if base == "high":
                base = "medium"
            elif base == "medium":
                base = "low"

        # Reduce if at max yield
        if proposed >= maximum and base == "high":
            base = "medium"

        return base
