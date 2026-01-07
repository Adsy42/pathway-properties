"""
Pydantic models for API request/response validation.
These define the shape of data flowing through the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# === ENUMS ===

class DocumentType(str, Enum):
    """All supported document types for upload."""
    # Legal - Victoria
    SECTION_32 = "Section 32 Vendor Statement (VIC)"
    TITLE_SEARCH = "Title Search / Certificate of Title"
    PLAN_OF_SUBDIVISION = "Plan of Subdivision"
    SECTION_137B = "Section 137B Owner-Builder Defect Report"
    
    # Legal - NSW
    CONTRACT_OF_SALE = "Contract for Sale (NSW)"
    SECTION_10_7 = "Section 10.7 Planning Certificate (NSW)"
    SEWER_DIAGRAM = "Sewer Service Diagram"
    SECTION_66W = "Section 66W Cooling-Off Waiver"
    
    # Strata
    STRATA_REPORT = "Strata Report / OC Certificate"
    STRATA_MINUTES = "Strata AGM Minutes"
    STRATA_BYLAWS = "Strata By-Laws / Model Rules"
    STRATA_INSURANCE = "Strata Insurance Certificate"
    
    # Inspection
    BUILDING_REPORT = "Building Inspection Report"
    PEST_REPORT = "Pest & Termite Inspection Report"
    POOL_COMPLIANCE = "Pool Compliance Certificate"
    ASBESTOS_REPORT = "Asbestos Inspection Report"
    
    # Rooming House
    ROOMING_REGISTRATION = "Rooming House Registration"
    AESMR = "Annual Essential Safety Measures Report"
    
    # Financial
    RENTAL_STATEMENT = "Rental Statement / Lease Agreement"
    RATES_NOTICE = "Council Rates Notice"
    WATER_RATES = "Water Rates Notice"
    
    # Visual
    FLOORPLAN = "Floorplan"
    MARKETING_PHOTOS = "Marketing Photos (ZIP)"
    
    # Other
    SURVEY_REPORT = "Survey / Subdivision Plan"
    GRANT_OF_PROBATE = "Grant of Probate"
    OTHER = "Other Document"


class Verdict(str, Enum):
    """Street level analysis verdict."""
    PROCEED = "PROCEED"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class RiskLevel(str, Enum):
    """Risk severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CheckScore(str, Enum):
    """Individual check result."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


# === REQUEST MODELS ===

class PropertyAnalyzeRequest(BaseModel):
    """Request to analyze a property from URL."""
    url: str = Field(..., description="Domain.com.au or RealEstate.com.au URL")


class PropertyManualRequest(BaseModel):
    """Request to manually add a property."""
    address: str = Field(..., description="Full address e.g. '122 Station Street, Pakenham VIC 3810'")
    suburb: str = Field(..., description="Suburb name")
    state: str = Field(default="VIC", description="State code (VIC, NSW, QLD, etc)")
    postcode: str = Field(..., description="Postcode")
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    parking: Optional[int] = None
    land_size: Optional[int] = Field(default=None, description="Land size in sqm")
    building_size: Optional[int] = Field(default=None, description="Building size in sqm")
    property_type: str = Field(default="house", description="house, townhouse, unit, apartment")
    price_display: Optional[str] = Field(default=None, description="Price as displayed e.g. '$590,000 - $630,000'")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    url: Optional[str] = Field(default=None, description="Original listing URL (optional)")


class DocumentUploadRequest(BaseModel):
    """Metadata for document upload (file sent separately as form data)."""
    property_id: str
    document_type: DocumentType


class DocumentQueryRequest(BaseModel):
    """Query a document using RAG."""
    question: str


class RunAnalysisRequest(BaseModel):
    """Request to run full asset analysis."""
    property_id: str


# === RESPONSE MODELS ===

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "0.1.0"


class SocialHousingCheck(BaseModel):
    """Social housing density check result."""
    score: CheckScore
    density_percent: float
    threshold: float = 15.0
    sa1_code: Optional[str] = None
    street_percent: Optional[float] = None
    details: str


class FlightPathCheck(BaseModel):
    """Flight path noise check result."""
    score: CheckScore
    anef: float
    n70: float
    details: str


class FloodRiskCheck(BaseModel):
    """Flood risk check result."""
    score: CheckScore
    aep_1_percent: bool
    building_at_risk: bool
    source: str
    details: str


class BushfireRiskCheck(BaseModel):
    """Bushfire risk check result."""
    score: CheckScore
    bal_rating: Optional[str] = None
    details: str


class ZoningCheck(BaseModel):
    """Zoning and overlay check result."""
    score: CheckScore
    code: str
    overlays: List[str] = []
    heritage_overlay: bool = False
    ddo_limits: Optional[dict] = None
    details: str


class StreetLevelAnalysis(BaseModel):
    """Complete street level analysis result."""
    social_housing: SocialHousingCheck
    flight_path: FlightPathCheck
    flood_risk: FloodRiskCheck
    bushfire_risk: BushfireRiskCheck
    zoning: ZoningCheck


class CoreLogicData(BaseModel):
    """Enrichment data from CoreLogic."""
    avm: Optional[int] = None
    avm_confidence: Optional[str] = None
    last_sold_price: Optional[int] = None
    last_sold_date: Optional[str] = None
    rental_estimate: Optional[dict] = None
    gross_yield_estimate: Optional[float] = None
    comparable_sales: Optional[List[dict]] = None


class PropertyDetails(BaseModel):
    """Property details from listing + enrichment."""
    address: str
    listing_price: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    parking: Optional[int] = None
    land_size: Optional[int] = None
    property_type: Optional[str] = None
    images: List[str] = []
    floorplan_url: Optional[str] = None
    description: Optional[str] = None
    agent: Optional[dict] = None
    corelogic: Optional[CoreLogicData] = None


class PropertyAnalyzeResponse(BaseModel):
    """Full response from property analysis."""
    id: str
    property: PropertyDetails
    street_level_analysis: StreetLevelAnalysis
    verdict: Verdict
    kill_reasons: List[str] = []
    created_at: datetime


class DocumentResponse(BaseModel):
    """Document upload/status response."""
    id: str
    property_id: str
    document_type: str
    status: str
    page_count: Optional[int] = None
    created_at: datetime


class DocumentQueryResponse(BaseModel):
    """Response from RAG query."""
    answer: str
    sources: List[dict] = []  # [{page: 1, section: "...", text: "..."}]
    confidence: float


# === ANALYSIS RESPONSE MODELS ===

class CaveatInfo(BaseModel):
    """Caveat extraction result."""
    caveator: str
    grounds_of_claim: str
    risk_level: RiskLevel
    risk_reason: str


class CovenantInfo(BaseModel):
    """Covenant extraction result."""
    text: str
    date_registered: Optional[str] = None
    development_impact: str  # NONE, MINOR, MAJOR, FATAL
    impact_reason: str


class EasementInfo(BaseModel):
    """Easement extraction result."""
    type: str
    beneficiary: str
    location: str
    building_conflict: bool


class TitleAnalysis(BaseModel):
    """Title verification result."""
    proprietor: str
    vendor_match: bool
    mismatch_reason: Optional[str] = None
    title_type: str
    volume_folio: Optional[str] = None


class LegalAnalysis(BaseModel):
    """Complete legal analysis."""
    title: Optional[TitleAnalysis] = None
    mortgages: List[dict] = []
    caveats: List[CaveatInfo] = []
    covenants: List[CovenantInfo] = []
    easements: List[EasementInfo] = []
    building_permits: List[dict] = []
    illegal_works_risk: Optional[dict] = None
    owner_builder: Optional[dict] = None
    special_conditions: List[dict] = []
    cooling_off_waived: bool = False
    planning: Optional[dict] = None


class DefectInfo(BaseModel):
    """Detected physical defect."""
    type: str
    location: str
    severity: str
    image_url: Optional[str] = None
    risk_implication: str


class PhysicalAnalysis(BaseModel):
    """Physical analysis results."""
    defects_detected: List[DefectInfo] = []
    termite_risk: Optional[dict] = None
    structural_concerns: List[str] = []


class FinancialAnalysis(BaseModel):
    """Financial analysis results."""
    purchase: Optional[dict] = None
    income: Optional[dict] = None
    outgoings: Optional[dict] = None
    yield_analysis: Optional[dict] = None
    gst_applicable: bool = False
    gst_reason: Optional[str] = None


class SweatEquityOpportunity(BaseModel):
    """Renovation/value-add opportunity."""
    type: str
    description: str
    estimated_cost: int
    value_add: int
    rent_increase_weekly: int
    roi_months: int
    feasibility: str


class SweatEquityAnalysis(BaseModel):
    """Sweat equity analysis results."""
    opportunities: List[SweatEquityOpportunity] = []
    total_value_add_potential: int = 0
    total_cost: int = 0
    overall_roi: float = 0.0


class AnalysisSummary(BaseModel):
    """Analysis summary and recommendation."""
    overall_risk: RiskLevel
    recommendation: str
    top_risks: List[dict] = []
    top_opportunities: List[dict] = []
    executive_summary: str


class FullAnalysisResponse(BaseModel):
    """Complete analysis response."""
    property_id: str
    timestamp: datetime
    street_level: StreetLevelAnalysis
    legal: Optional[LegalAnalysis] = None
    physical: Optional[PhysicalAnalysis] = None
    financial: Optional[FinancialAnalysis] = None
    sweat_equity: Optional[SweatEquityAnalysis] = None
    specialized: Optional[dict] = None
    summary: Optional[AnalysisSummary] = None


class PropertyListItem(BaseModel):
    """Property item for list view."""
    id: str
    address: str
    verdict: Optional[str] = None
    created_at: datetime


class PropertyListResponse(BaseModel):
    """List of properties."""
    properties: List[PropertyListItem]
    total: int


# === DUE DILIGENCE REQUEST/RESPONSE MODELS ===

class StampDutyRequest(BaseModel):
    """Request for stamp duty calculation."""
    purchase_price: float = Field(..., description="Purchase price in dollars")
    property_type: str = Field(default="house", description="house, apartment, townhouse, unit, land")
    is_first_home_buyer: bool = Field(default=False, description="Eligible for FHB concession")
    is_foreign_purchaser: bool = Field(default=False, description="Foreign purchaser surcharge applies")
    is_pensioner: bool = Field(default=False, description="Eligible for pensioner concession")
    is_off_the_plan: bool = Field(default=False, description="Off-the-plan purchase")


class StampDutyResponse(BaseModel):
    """Stamp duty calculation result."""
    duty_amount: float
    duty_formatted: str
    effective_rate: float
    concessions_applied: List[str] = []
    foreign_surcharge: float = 0
    premium_duty: float = 0
    total_duty: float
    calculation_breakdown: List[dict] = []


class CoolingOffRequest(BaseModel):
    """Request for cooling-off calculation."""
    contract_signed_date: str = Field(..., description="Date in YYYY-MM-DD format")
    purchase_price: float = Field(..., description="Purchase price in dollars")
    purchase_method: str = Field(default="private_sale", description="private_sale, auction, pre_auction, post_auction")
    purchaser_type: str = Field(default="individual", description="individual, corporation, trust, smsf")
    is_auction: bool = Field(default=False, description="Shorthand for purchase_method=auction")


class CoolingOffResponse(BaseModel):
    """Cooling-off calculation result."""
    has_cooling_off: bool
    deadline: Optional[str] = None
    deadline_formatted: Optional[str] = None
    days_remaining: Optional[int] = None
    penalty_to_exit: Optional[float] = None
    penalty_formatted: Optional[str] = None
    exemption_reason: Optional[str] = None
    status: str
    warnings: List[str] = []
    recommendations: List[str] = []


class TimelineRequest(BaseModel):
    """Request for due diligence timeline."""
    contract_signed_date: str = Field(..., description="Date in YYYY-MM-DD format")
    settlement_date: str = Field(..., description="Date in YYYY-MM-DD format")
    cooling_off_expires: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format")
    property_type: str = Field(default="house", description="house, apartment, townhouse, unit")
    is_investment: bool = Field(default=False, description="Is this an investment purchase")
    special_conditions: Optional[List[dict]] = Field(default=None, description="List of special conditions with type and deadline")


class TimelineDeadline(BaseModel):
    """A critical deadline in the timeline."""
    name: str
    date: str
    days_remaining: int
    urgency: str
    action: str
    condition_type: Optional[str] = None
    completed: bool = False
    notes: Optional[str] = None


class DelegatedTask(BaseModel):
    """A task delegated to a specialist."""
    task: str
    delegate_to: str
    deadline: str
    status: str
    estimated_cost: Optional[str] = None
    priority: int = 1
    notes: Optional[str] = None


class TimelineResponse(BaseModel):
    """Due diligence timeline result."""
    contract_signed: str
    cooling_off_expires: Optional[str] = None
    settlement_date: str
    critical_deadlines: List[TimelineDeadline] = []
    recommended_actions: List[dict] = []
    delegated_tasks: List[DelegatedTask] = []
    days_to_settlement: int
    overall_status: str
    warnings: List[str] = []


class SpecialistReferralRequest(BaseModel):
    """Request for specialist referral analysis."""
    building_year: int = Field(..., description="Year property was built")
    property_type: str = Field(default="house", description="house, apartment, townhouse, unit")
    overlays: Optional[List[str]] = Field(default=None, description="Planning overlays e.g. HO, EAO")
    building_inspection_findings: Optional[List[str]] = Field(default=None, description="Issues from building inspection")
    planned_works: Optional[List[str]] = Field(default=None, description="Planned renovations")
    has_pool: bool = Field(default=False, description="Property has swimming pool")
    is_investment: bool = Field(default=False, description="Is this an investment purchase")


class SpecialistReferral(BaseModel):
    """A specialist referral recommendation."""
    specialist_type: str
    specialist_name: str
    urgency: str
    triggers: List[dict] = []
    typical_cost: str
    expected_timeline: str
    benefit: Optional[str] = None
    notes: Optional[str] = None
    required_before: Optional[str] = None


class SpecialistReferralResponse(BaseModel):
    """Specialist referral analysis result."""
    critical_referrals: List[SpecialistReferral] = []
    high_priority_referrals: List[SpecialistReferral] = []
    recommended_referrals: List[SpecialistReferral] = []
    total_estimated_cost: str
    summary: str


class RiskScoreResponse(BaseModel):
    """Risk score calculation result."""
    score: float = Field(..., description="Overall risk score 0-100")
    rating: str = Field(..., description="LOW, MODERATE, ELEVATED, HIGH, CRITICAL")
    category_scores: dict = Field(default_factory=dict, description="Scores by category")
    top_risk_factors: List[dict] = []
    recommendations: List[str] = []


class CashFlowRequest(BaseModel):
    """Request for cash flow calculation."""
    purchase_price: float = Field(..., description="Purchase price in dollars")
    weekly_rent: float = Field(..., description="Expected weekly rent")
    deposit_percent: float = Field(default=20.0, description="Deposit as percentage")
    interest_rate: float = Field(default=6.5, description="Interest rate percentage")
    council_rates: float = Field(default=2400, description="Annual council rates")
    water_rates: float = Field(default=800, description="Annual water rates")
    strata_levies: float = Field(default=0, description="Annual strata levies")
    insurance: float = Field(default=1800, description="Annual building insurance")
    property_management_percent: float = Field(default=7.5, description="PM fee as percentage of rent")
    vacancy_rate: float = Field(default=3.0, description="Expected vacancy rate percentage")
    maintenance_percent: float = Field(default=1.0, description="Maintenance as percentage of value")
    building_year: int = Field(default=2000, description="Year property was built")


class CashFlowResponse(BaseModel):
    """Cash flow calculation result."""
    gross_rental_income: float
    vacancy_cost: float
    net_rental_income: float
    total_expenses: float
    cash_flow_before_tax: float
    depreciation_estimate: float
    tax_benefit_estimate: float
    cash_flow_after_tax: float
    gross_yield: float
    net_yield: float
    expense_breakdown: dict = {}
    sensitivity_analysis: dict = {}


class ComplianceStatus(BaseModel):
    """Due diligence compliance status."""
    completion_rate: float
    completed: List[str] = []
    pending: List[str] = []
    not_applicable: List[str] = []
    ready_for_purchase: bool
    recommendations: List[str] = []

