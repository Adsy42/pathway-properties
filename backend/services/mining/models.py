"""
Data models for mining tenement data.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class TenementType(str, Enum):
    """Types of mining tenements."""
    EXPLORATION_LICENSE = "exploration_license"
    MINING_LICENSE = "mining_license"
    RETENTION_LICENSE = "retention_license"
    PROSPECTING_LICENSE = "prospecting_license"
    EXTRACTIVE_INDUSTRY = "extractive_industry"  # Quarry
    PETROLEUM = "petroleum"
    GEOTHERMAL = "geothermal"
    UNKNOWN = "unknown"


class TenementStatus(str, Enum):
    """Tenement status."""
    ACTIVE = "active"
    APPLICATION = "application"
    EXPIRED = "expired"
    SURRENDERED = "surrendered"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class MiningTenement(BaseModel):
    """Mining tenement record."""
    tenement_id: str
    tenement_type: TenementType
    holder_name: Optional[str] = None
    status: TenementStatus = TenementStatus.UNKNOWN
    area_hectares: Optional[float] = None
    grant_date: Optional[str] = None
    expiry_date: Optional[str] = None
    commodities: List[str] = []  # Gold, Coal, Sand, etc.
    distance_meters: Optional[float] = None
    covers_property: bool = False
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenement_id": self.tenement_id,
            "tenement_type": self.tenement_type.value,
            "holder_name": self.holder_name,
            "status": self.status.value,
            "area_hectares": self.area_hectares,
            "grant_date": self.grant_date,
            "expiry_date": self.expiry_date,
            "commodities": self.commodities,
            "distance_meters": self.distance_meters,
            "covers_property": self.covers_property,
            "description": self.description
        }


class MiningRiskAssessment(BaseModel):
    """Mining risk assessment for a property."""
    property_address: str
    property_covered: bool = False
    covering_tenements: List[MiningTenement] = []
    nearby_tenements: List[MiningTenement] = []
    risk_level: str = "NONE"  # NONE, LOW, MODERATE, HIGH
    implications: List[str] = []
    recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_address": self.property_address,
            "property_covered": self.property_covered,
            "covering_tenements": [t.to_dict() for t in self.covering_tenements],
            "nearby_tenements": [t.to_dict() for t in self.nearby_tenements],
            "risk_level": self.risk_level,
            "implications": self.implications,
            "recommendations": self.recommendations
        }
