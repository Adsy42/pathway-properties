"""
Data models for rooming house analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_ASSESSMENT = "requires_assessment"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class ComplianceItem(BaseModel):
    """Individual compliance check item."""
    requirement: str
    status: ComplianceStatus
    details: Optional[str] = None
    cost_to_remedy: Optional[float] = None
    priority: str = "medium"  # high, medium, low

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement": self.requirement,
            "status": self.status.value,
            "details": self.details,
            "cost_to_remedy": self.cost_to_remedy,
            "priority": self.priority
        }


class RoomYield(BaseModel):
    """Per-room yield calculation."""
    room_number: int
    room_type: str  # bedroom, study, converted
    size_sqm: Optional[float] = None
    weekly_rent: float
    annual_rent: float
    occupancy_rate: float = 0.92  # 8% vacancy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_number": self.room_number,
            "room_type": self.room_type,
            "size_sqm": self.size_sqm,
            "weekly_rent": self.weekly_rent,
            "annual_rent": self.annual_rent,
            "occupancy_rate": self.occupancy_rate
        }


class RoomingHouseAssessment(BaseModel):
    """Comprehensive rooming house assessment."""
    property_address: str

    # Building classification
    current_classification: str = "unknown"  # Class 1a, 1b, 3
    required_classification: str = "unknown"
    classification_upgrade_required: bool = False
    upgrade_cost_estimate: Optional[float] = None

    # Compliance
    compliance_items: List[ComplianceItem] = []
    overall_compliance: ComplianceStatus = ComplianceStatus.UNKNOWN
    compliance_score: float = 0.0  # 0-100

    # Registration
    is_registered: bool = False
    registration_required: bool = True
    registration_number: Optional[str] = None

    # Room details
    room_count: int = 0
    compliant_room_count: int = 0
    rooms: List[RoomYield] = []

    # Yield analysis
    total_weekly_rent: float = 0.0
    total_annual_rent: float = 0.0
    gross_yield: Optional[float] = None
    net_yield: Optional[float] = None
    yield_comparison: str = ""  # vs standard rental

    # Costs
    annual_compliance_costs: float = 0.0
    fire_safety_upgrade_cost: Optional[float] = None
    remediation_costs: float = 0.0

    # Risks
    risk_level: str = "unknown"  # low, medium, high, critical
    key_risks: List[str] = []
    council_attitude: str = "unknown"  # supportive, neutral, restrictive

    # Recommendations
    recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_address": self.property_address,
            "current_classification": self.current_classification,
            "required_classification": self.required_classification,
            "classification_upgrade_required": self.classification_upgrade_required,
            "upgrade_cost_estimate": self.upgrade_cost_estimate,
            "compliance_items": [c.to_dict() for c in self.compliance_items],
            "overall_compliance": self.overall_compliance.value,
            "compliance_score": self.compliance_score,
            "is_registered": self.is_registered,
            "registration_required": self.registration_required,
            "registration_number": self.registration_number,
            "room_count": self.room_count,
            "compliant_room_count": self.compliant_room_count,
            "rooms": [r.to_dict() for r in self.rooms],
            "total_weekly_rent": self.total_weekly_rent,
            "total_annual_rent": self.total_annual_rent,
            "gross_yield": self.gross_yield,
            "net_yield": self.net_yield,
            "yield_comparison": self.yield_comparison,
            "annual_compliance_costs": self.annual_compliance_costs,
            "fire_safety_upgrade_cost": self.fire_safety_upgrade_cost,
            "remediation_costs": self.remediation_costs,
            "risk_level": self.risk_level,
            "key_risks": self.key_risks,
            "council_attitude": self.council_attitude,
            "recommendations": self.recommendations
        }
