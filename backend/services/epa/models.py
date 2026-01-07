"""
Data models for EPA Victoria contamination data.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class ContaminationType(str, Enum):
    """Types of contamination."""
    INDUSTRIAL = "industrial"
    PETROLEUM = "petroleum"
    LANDFILL = "landfill"
    CHEMICAL = "chemical"
    ASBESTOS = "asbestos"
    HEAVY_METALS = "heavy_metals"
    PFAS = "pfas"  # Per- and polyfluoroalkyl substances
    UNKNOWN = "unknown"


class SiteStatus(str, Enum):
    """EPA site status."""
    ACTIVE = "active"
    UNDER_ASSESSMENT = "under_assessment"
    REMEDIATED = "remediated"
    MONITORING = "monitoring"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class ContaminatedSite(BaseModel):
    """EPA contaminated site record."""
    site_id: str
    site_name: str
    address: Optional[str] = None
    suburb: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_meters: Optional[float] = None  # Distance from property
    contamination_types: List[ContaminationType] = []
    status: SiteStatus = SiteStatus.UNKNOWN
    description: Optional[str] = None
    epa_reference: Optional[str] = None
    audit_date: Optional[str] = None
    restrictions: List[str] = []  # Land use restrictions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_id": self.site_id,
            "site_name": self.site_name,
            "address": self.address,
            "suburb": self.suburb,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_meters": self.distance_meters,
            "contamination_types": [c.value for c in self.contamination_types],
            "status": self.status.value,
            "description": self.description,
            "epa_reference": self.epa_reference,
            "audit_date": self.audit_date,
            "restrictions": self.restrictions
        }


class ContaminationRiskAssessment(BaseModel):
    """Contamination risk assessment for a property."""
    property_address: str
    is_on_psr: bool = False  # On Priority Sites Register
    psr_site: Optional[ContaminatedSite] = None
    nearby_sites: List[ContaminatedSite] = []
    historic_industrial_use: bool = False
    groundwater_restricted: bool = False
    risk_level: str = "LOW"  # LOW, MODERATE, ELEVATED, HIGH, CRITICAL
    risk_score: float = 0.0  # 0-100
    concerns: List[str] = []
    recommendations: List[str] = []
    environmental_audit_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_address": self.property_address,
            "is_on_psr": self.is_on_psr,
            "psr_site": self.psr_site.to_dict() if self.psr_site else None,
            "nearby_sites": [s.to_dict() for s in self.nearby_sites],
            "nearby_site_count": len(self.nearby_sites),
            "historic_industrial_use": self.historic_industrial_use,
            "groundwater_restricted": self.groundwater_restricted,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "concerns": self.concerns,
            "recommendations": self.recommendations,
            "environmental_audit_required": self.environmental_audit_required
        }
