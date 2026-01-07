"""
Data models for development feasibility analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class DevelopmentType(str, Enum):
    """Type of development."""
    SUBDIVISION = "subdivision"
    TOWNHOUSES = "townhouses"
    APARTMENTS = "apartments"
    MIXED_USE = "mixed_use"
    DUAL_OCCUPANCY = "dual_occupancy"


class SiteAnalysis(BaseModel):
    """Physical site analysis."""
    land_area_sqm: float
    frontage_meters: Optional[float] = None
    depth_meters: Optional[float] = None
    is_corner: bool = False
    slope_percentage: Optional[float] = None
    existing_buildings: bool = True
    demolition_required: bool = True

    # Services
    sewer_available: bool = True
    water_available: bool = True
    power_available: bool = True
    gas_available: bool = True
    nbn_available: bool = True

    # Access
    rear_access: bool = False
    crossover_width: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "land_area_sqm": self.land_area_sqm,
            "frontage_meters": self.frontage_meters,
            "depth_meters": self.depth_meters,
            "is_corner": self.is_corner,
            "slope_percentage": self.slope_percentage,
            "existing_buildings": self.existing_buildings,
            "demolition_required": self.demolition_required,
            "sewer_available": self.sewer_available,
            "water_available": self.water_available,
            "power_available": self.power_available,
            "gas_available": self.gas_available,
            "nbn_available": self.nbn_available,
            "rear_access": self.rear_access,
            "crossover_width": self.crossover_width
        }


class PlanningConstraints(BaseModel):
    """Planning scheme constraints."""
    zone_code: str
    zone_name: Optional[str] = None
    overlays: List[str] = []

    # Density controls
    min_lot_size_sqm: Optional[float] = None
    max_site_coverage: Optional[float] = None  # Percentage
    max_height_meters: Optional[float] = None
    max_stories: Optional[int] = None

    # Setbacks
    front_setback_meters: Optional[float] = None
    side_setback_meters: Optional[float] = None
    rear_setback_meters: Optional[float] = None

    # Parking
    parking_spaces_per_dwelling: float = 1.0

    # Other
    permit_required: bool = True
    heritage_constraints: bool = False
    vegetation_constraints: bool = False
    flooding_constraints: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_code": self.zone_code,
            "zone_name": self.zone_name,
            "overlays": self.overlays,
            "min_lot_size_sqm": self.min_lot_size_sqm,
            "max_site_coverage": self.max_site_coverage,
            "max_height_meters": self.max_height_meters,
            "max_stories": self.max_stories,
            "front_setback_meters": self.front_setback_meters,
            "side_setback_meters": self.side_setback_meters,
            "rear_setback_meters": self.rear_setback_meters,
            "parking_spaces_per_dwelling": self.parking_spaces_per_dwelling,
            "permit_required": self.permit_required,
            "heritage_constraints": self.heritage_constraints,
            "vegetation_constraints": self.vegetation_constraints,
            "flooding_constraints": self.flooding_constraints
        }


class FinancialModel(BaseModel):
    """Development financial model."""
    # Revenue
    gross_realization_value: float = 0.0
    revenue_per_dwelling: float = 0.0
    total_dwellings: int = 0

    # Costs
    land_cost: float = 0.0
    stamp_duty: float = 0.0
    demolition_cost: float = 0.0
    construction_cost: float = 0.0
    construction_per_sqm: float = 0.0
    professional_fees: float = 0.0
    statutory_costs: float = 0.0
    infrastructure_contributions: float = 0.0
    holding_costs: float = 0.0
    selling_costs: float = 0.0
    contingency: float = 0.0

    total_development_cost: float = 0.0

    # Returns
    gross_profit: float = 0.0
    development_margin_percent: float = 0.0
    return_on_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gross_realization_value": self.gross_realization_value,
            "revenue_per_dwelling": self.revenue_per_dwelling,
            "total_dwellings": self.total_dwellings,
            "land_cost": self.land_cost,
            "stamp_duty": self.stamp_duty,
            "demolition_cost": self.demolition_cost,
            "construction_cost": self.construction_cost,
            "construction_per_sqm": self.construction_per_sqm,
            "professional_fees": self.professional_fees,
            "statutory_costs": self.statutory_costs,
            "infrastructure_contributions": self.infrastructure_contributions,
            "holding_costs": self.holding_costs,
            "selling_costs": self.selling_costs,
            "contingency": self.contingency,
            "total_development_cost": self.total_development_cost,
            "gross_profit": self.gross_profit,
            "development_margin_percent": self.development_margin_percent,
            "return_on_cost": self.return_on_cost
        }


class FeasibilityAssessment(BaseModel):
    """Comprehensive development feasibility assessment."""
    property_address: str
    development_type: DevelopmentType
    site_analysis: SiteAnalysis
    planning: PlanningConstraints
    financial: FinancialModel

    # Yield
    maximum_dwellings: int = 0
    recommended_dwellings: int = 0
    yield_constrained_by: str = ""  # land area, height, parking, etc.

    # Feasibility
    is_feasible: bool = False
    feasibility_rating: str = "unknown"  # strong, marginal, unfeasible
    target_margin_achieved: bool = False

    # Risks
    risk_level: str = "medium"
    key_risks: List[str] = []

    # Planning
    permit_probability: str = "unknown"  # high, medium, low
    permit_considerations: List[str] = []

    # Timeline estimate
    permit_months: int = 6
    construction_months: int = 12
    total_project_months: int = 18

    # Recommendations
    recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_address": self.property_address,
            "development_type": self.development_type.value,
            "site_analysis": self.site_analysis.to_dict(),
            "planning": self.planning.to_dict(),
            "financial": self.financial.to_dict(),
            "maximum_dwellings": self.maximum_dwellings,
            "recommended_dwellings": self.recommended_dwellings,
            "yield_constrained_by": self.yield_constrained_by,
            "is_feasible": self.is_feasible,
            "feasibility_rating": self.feasibility_rating,
            "target_margin_achieved": self.target_margin_achieved,
            "risk_level": self.risk_level,
            "key_risks": self.key_risks,
            "permit_probability": self.permit_probability,
            "permit_considerations": self.permit_considerations,
            "permit_months": self.permit_months,
            "construction_months": self.construction_months,
            "total_project_months": self.total_project_months,
            "recommendations": self.recommendations
        }
