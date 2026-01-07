"""
Data models for school catchment data.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class SchoolType(str, Enum):
    """Types of schools."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    P12 = "p12"  # Combined primary and secondary
    SPECIAL = "special"
    UNKNOWN = "unknown"


class SchoolSector(str, Enum):
    """School sector."""
    GOVERNMENT = "government"
    CATHOLIC = "catholic"
    INDEPENDENT = "independent"
    UNKNOWN = "unknown"


class School(BaseModel):
    """School information."""
    school_id: str
    name: str
    school_type: SchoolType = SchoolType.UNKNOWN
    sector: SchoolSector = SchoolSector.UNKNOWN
    address: Optional[str] = None
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_meters: Optional[float] = None
    enrolments: Optional[int] = None
    icsea: Optional[int] = None  # Index of Community Socio-Educational Advantage
    year_levels: Optional[str] = None  # e.g., "Prep-6", "7-12"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "school_id": self.school_id,
            "name": self.name,
            "school_type": self.school_type.value,
            "sector": self.sector.value,
            "address": self.address,
            "suburb": self.suburb,
            "postcode": self.postcode,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_meters": self.distance_meters,
            "enrolments": self.enrolments,
            "icsea": self.icsea,
            "year_levels": self.year_levels
        }


class SchoolCatchment(BaseModel):
    """School catchment zone information."""
    school: School
    in_catchment: bool = False
    catchment_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "school": self.school.to_dict(),
            "in_catchment": self.in_catchment,
            "catchment_name": self.catchment_name
        }


class SchoolsAssessment(BaseModel):
    """Schools assessment for a property location."""
    property_address: str
    primary_catchment: Optional[SchoolCatchment] = None
    secondary_catchment: Optional[SchoolCatchment] = None
    nearby_primary: List[School] = []
    nearby_secondary: List[School] = []
    nearby_private: List[School] = []
    desirability_score: float = 50.0  # 0-100
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_address": self.property_address,
            "primary_catchment": self.primary_catchment.to_dict() if self.primary_catchment else None,
            "secondary_catchment": self.secondary_catchment.to_dict() if self.secondary_catchment else None,
            "nearby_primary": [s.to_dict() for s in self.nearby_primary],
            "nearby_secondary": [s.to_dict() for s in self.nearby_secondary],
            "nearby_private": [s.to_dict() for s in self.nearby_private],
            "desirability_score": self.desirability_score,
            "summary": self.summary
        }
