"""
Data models for crime statistics.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class CrimeCategory(str, Enum):
    """Crime categories from CSA Victoria."""
    CRIMES_AGAINST_PERSON = "crimes_against_person"
    PROPERTY_DAMAGE = "property_damage"
    DRUG_OFFENCES = "drug_offences"
    PUBLIC_ORDER = "public_order"
    JUSTICE_PROCEDURES = "justice_procedures"
    OTHER = "other"
    TOTAL = "total"


class CrimeTrend(str, Enum):
    """Crime trend direction."""
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    UNKNOWN = "unknown"


class CrimeCategoryStats(BaseModel):
    """Statistics for a single crime category."""
    category: CrimeCategory
    incident_count: int
    rate_per_100k: Optional[float] = None
    year_over_year_change: Optional[float] = None  # Percentage change
    trend: CrimeTrend = CrimeTrend.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "incident_count": self.incident_count,
            "rate_per_100k": self.rate_per_100k,
            "year_over_year_change": self.year_over_year_change,
            "trend": self.trend.value
        }


class SuburbCrimeStats(BaseModel):
    """Crime statistics for a suburb."""
    suburb: str
    postcode: Optional[str] = None
    lga: Optional[str] = None  # Local Government Area
    year: int
    quarter: Optional[int] = None
    population: Optional[int] = None

    # Category breakdowns
    categories: List[CrimeCategoryStats] = []

    # Summary stats
    total_incidents: int = 0
    total_rate_per_100k: Optional[float] = None
    overall_trend: CrimeTrend = CrimeTrend.UNKNOWN

    # Comparison to state average
    vs_state_average: Optional[float] = None  # Percentage difference
    risk_level: str = "UNKNOWN"  # LOW, MODERATE, ELEVATED, HIGH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suburb": self.suburb,
            "postcode": self.postcode,
            "lga": self.lga,
            "year": self.year,
            "quarter": self.quarter,
            "population": self.population,
            "categories": [c.to_dict() for c in self.categories],
            "total_incidents": self.total_incidents,
            "total_rate_per_100k": self.total_rate_per_100k,
            "overall_trend": self.overall_trend.value,
            "vs_state_average": self.vs_state_average,
            "risk_level": self.risk_level
        }


class CrimeRiskAssessment(BaseModel):
    """Crime risk assessment for a property location."""
    suburb: str
    stats: Optional[SuburbCrimeStats] = None
    risk_level: str = "UNKNOWN"
    risk_score: float = 50.0  # 0-100 scale
    key_concerns: List[str] = []
    comparison_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suburb": self.suburb,
            "stats": self.stats.to_dict() if self.stats else None,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "key_concerns": self.key_concerns,
            "comparison_text": self.comparison_text
        }
