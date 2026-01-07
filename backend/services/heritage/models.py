"""
Data models for Heritage Victoria API responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import date


class HeritagePlace(BaseModel):
    """Victorian Heritage Register place."""
    vhr_number: str
    name: str
    address: Optional[str] = None
    municipality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    significance: Optional[str] = None  # Statement of significance
    history: Optional[str] = None
    description: Optional[str] = None
    heritage_status: str = "Registered"  # Registered, Nominated, etc.
    registration_date: Optional[date] = None
    categories: List[str] = []  # Archaeological, Architectural, etc.
    images: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vhr_number": self.vhr_number,
            "name": self.name,
            "address": self.address,
            "municipality": self.municipality,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "significance": self.significance,
            "history": self.history,
            "description": self.description,
            "heritage_status": self.heritage_status,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "categories": self.categories,
            "images": self.images
        }


class HeritageSearchResult(BaseModel):
    """Result from heritage search."""
    places: List[HeritagePlace]
    total_count: int
    page: int
    page_size: int
    has_more: bool

    @property
    def is_heritage_listed(self) -> bool:
        """Check if any heritage places were found."""
        return len(self.places) > 0

    def get_primary_place(self) -> Optional[HeritagePlace]:
        """Get the most relevant heritage place (first result)."""
        return self.places[0] if self.places else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "places": [p.to_dict() for p in self.places],
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
            "has_more": self.has_more,
            "is_heritage_listed": self.is_heritage_listed
        }


class HeritageRiskAssessment(BaseModel):
    """Heritage risk assessment for a property."""
    is_vhr_listed: bool = False
    is_local_heritage: bool = False
    vhr_place: Optional[HeritagePlace] = None
    risk_level: str = "NONE"  # NONE, LOW, MEDIUM, HIGH
    implications: List[str] = []
    notification_required: bool = False
    permit_required_for_works: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_vhr_listed": self.is_vhr_listed,
            "is_local_heritage": self.is_local_heritage,
            "vhr_place": self.vhr_place.to_dict() if self.vhr_place else None,
            "risk_level": self.risk_level,
            "implications": self.implications,
            "notification_required": self.notification_required,
            "permit_required_for_works": self.permit_required_for_works
        }
