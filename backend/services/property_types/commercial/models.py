"""
Data models for commercial property analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum
from datetime import date


class TenantStrength(str, Enum):
    """Tenant covenant strength."""
    NATIONAL = "national"       # ASX listed, national chain
    REGIONAL = "regional"       # Multi-location business
    LOCAL = "local"            # Single location business
    STARTUP = "startup"        # New business <2 years
    UNKNOWN = "unknown"


class LeaseType(str, Enum):
    """Type of commercial lease."""
    GROSS = "gross"            # Landlord pays outgoings
    NET = "net"               # Tenant pays some outgoings
    TRIPLE_NET = "triple_net"  # Tenant pays all outgoings
    PERCENTAGE = "percentage"  # Base rent + percentage of sales


class TenantProfile(BaseModel):
    """Tenant information and covenant strength."""
    name: str
    business_type: str
    tenant_strength: TenantStrength = TenantStrength.UNKNOWN
    years_in_business: Optional[int] = None
    abn: Optional[str] = None
    is_franchisee: bool = False
    franchisor: Optional[str] = None
    credit_rating: Optional[str] = None  # If available

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "business_type": self.business_type,
            "tenant_strength": self.tenant_strength.value,
            "years_in_business": self.years_in_business,
            "abn": self.abn,
            "is_franchisee": self.is_franchisee,
            "franchisor": self.franchisor,
            "credit_rating": self.credit_rating
        }


class LeaseDetails(BaseModel):
    """Commercial lease details."""
    tenant: TenantProfile
    lease_type: LeaseType = LeaseType.NET
    commencement_date: Optional[date] = None
    expiry_date: Optional[date] = None
    term_years: Optional[int] = None
    options_remaining: int = 0
    option_term_years: int = 0

    # Rent details
    current_rent_annual: float = 0.0
    rent_per_sqm: Optional[float] = None
    rent_review_type: str = "CPI"  # CPI, Fixed %, Market
    rent_review_percentage: Optional[float] = None
    rent_review_frequency_months: int = 12

    # Outgoings
    outgoings_recoverable: bool = True
    outgoings_annual: Optional[float] = None

    # Other terms
    make_good_required: bool = False
    bank_guarantee_months: int = 0
    personal_guarantee: bool = False
    assignment_rights: bool = True
    sublease_rights: bool = False

    def years_remaining(self) -> Optional[float]:
        """Calculate years remaining on lease."""
        if not self.expiry_date:
            return None
        today = date.today()
        if self.expiry_date <= today:
            return 0
        delta = self.expiry_date - today
        return delta.days / 365.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant": self.tenant.to_dict(),
            "lease_type": self.lease_type.value,
            "commencement_date": self.commencement_date.isoformat() if self.commencement_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "term_years": self.term_years,
            "years_remaining": self.years_remaining(),
            "options_remaining": self.options_remaining,
            "option_term_years": self.option_term_years,
            "current_rent_annual": self.current_rent_annual,
            "rent_per_sqm": self.rent_per_sqm,
            "rent_review_type": self.rent_review_type,
            "rent_review_percentage": self.rent_review_percentage,
            "rent_review_frequency_months": self.rent_review_frequency_months,
            "outgoings_recoverable": self.outgoings_recoverable,
            "outgoings_annual": self.outgoings_annual,
            "make_good_required": self.make_good_required,
            "bank_guarantee_months": self.bank_guarantee_months,
            "personal_guarantee": self.personal_guarantee,
            "assignment_rights": self.assignment_rights,
            "sublease_rights": self.sublease_rights
        }


class CommercialAssessment(BaseModel):
    """Comprehensive commercial property assessment."""
    property_address: str
    property_type: str  # Retail, Office, Industrial, Mixed

    # Lease summary
    leases: List[LeaseDetails] = []
    is_fully_leased: bool = False
    vacancy_rate: float = 0.0

    # Income analysis
    total_annual_rent: float = 0.0
    total_annual_outgoings: float = 0.0
    net_annual_income: float = 0.0

    # Yield metrics
    cap_rate: Optional[float] = None
    net_yield: Optional[float] = None
    passing_yield: Optional[float] = None
    market_rent_yield: Optional[float] = None

    # WALE
    wale_years: Optional[float] = None
    wale_by_income: Optional[float] = None

    # Tenant analysis
    tenant_risk_score: float = 50.0  # 0-100, higher is better
    key_tenant_risks: List[str] = []

    # Zoning
    current_use_permitted: bool = True
    zoning_issues: List[str] = []

    # Comparable analysis
    market_cap_rate: Optional[float] = None
    cap_rate_comparison: str = ""

    # Overall
    risk_level: str = "medium"
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_address": self.property_address,
            "property_type": self.property_type,
            "leases": [l.to_dict() for l in self.leases],
            "is_fully_leased": self.is_fully_leased,
            "vacancy_rate": self.vacancy_rate,
            "total_annual_rent": self.total_annual_rent,
            "total_annual_outgoings": self.total_annual_outgoings,
            "net_annual_income": self.net_annual_income,
            "cap_rate": self.cap_rate,
            "net_yield": self.net_yield,
            "passing_yield": self.passing_yield,
            "market_rent_yield": self.market_rent_yield,
            "wale_years": self.wale_years,
            "wale_by_income": self.wale_by_income,
            "tenant_risk_score": self.tenant_risk_score,
            "key_tenant_risks": self.key_tenant_risks,
            "current_use_permitted": self.current_use_permitted,
            "zoning_issues": self.zoning_issues,
            "market_cap_rate": self.market_cap_rate,
            "cap_rate_comparison": self.cap_rate_comparison,
            "risk_level": self.risk_level,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations
        }
