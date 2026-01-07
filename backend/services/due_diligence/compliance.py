"""
Regulatory Compliance Module.

- Statement of Information (SOI) Analyzer for underquoting detection
- Consumer Affairs Victoria Due Diligence Checklist tracker
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics


class ComplianceStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PENDING = "PENDING"
    NOT_APPLICABLE = "N/A"
    MISSING = "MISSING"


# ============================================================================
# STATEMENT OF INFORMATION ANALYZER
# ============================================================================

@dataclass
class UnderquotingIndicator:
    """An indicator of potential underquoting."""
    indicator_type: str
    description: str
    detail: str
    severity: str = "INFO"  # INFO, WARNING, CONCERN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.indicator_type,
            "description": self.description,
            "detail": self.detail,
            "severity": self.severity
        }


@dataclass
class SOIAnalysisResult:
    """Statement of Information analysis result."""
    quoted_price_range: Dict[str, Any] = field(default_factory=dict)
    price_range_valid: bool = True
    comparable_sales_provided: List[Dict[str, Any]] = field(default_factory=list)
    underquoting_indicators: List[UnderquotingIndicator] = field(default_factory=list)
    cherry_picking_indicators: List[UnderquotingIndicator] = field(default_factory=list)
    compliance_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quoted_price_range": self.quoted_price_range,
            "price_range_valid": self.price_range_valid,
            "comparable_sales_provided": self.comparable_sales_provided,
            "underquoting_indicators": [i.to_dict() for i in self.underquoting_indicators],
            "cherry_picking_indicators": [i.to_dict() for i in self.cherry_picking_indicators],
            "compliance_issues": self.compliance_issues,
            "recommendations": self.recommendations
        }


class StatementOfInformationAnalyzer:
    """
    Analyzes Victorian Statement of Information for underquoting indicators.

    Background:
    - Since 2017, Victorian agents must provide:
      - Single advertised price OR price range (max 10% spread)
      - Three comparable sales within 2km and 6 months

    - 2025 laws require publishing vendor's actual reserve 7 days before auction
    - Consumer Affairs Victoria has issued $2.3M+ in fines since 2022

    Source: Estate Agents (Professional Conduct) Regulations 2018
    """

    MAX_PRICE_RANGE_SPREAD = 0.10  # 10%

    def analyze(
        self,
        soi: Dict[str, Any],
        actual_comparables: Optional[List[Dict[str, Any]]] = None,
        final_sale_price: Optional[float] = None
    ) -> SOIAnalysisResult:
        """
        Analyze Statement of Information.

        Args:
            soi: Statement of Information data:
                - price_range: {low: float, high: float}
                - comparable_sales: [{address, sale_price, sale_date, distance_km}]
            actual_comparables: Independent comparable sales for comparison
            final_sale_price: Final sale price if known (for post-sale analysis)

        Returns:
            SOIAnalysisResult with compliance analysis
        """
        result = SOIAnalysisResult()

        price_range = soi.get("price_range", {})
        result.quoted_price_range = price_range
        result.comparable_sales_provided = soi.get("comparable_sales", [])

        # Check price range spread
        if price_range:
            low = price_range.get("low", 0)
            high = price_range.get("high", 0)

            if low > 0:
                spread = (high - low) / low

                if spread > self.MAX_PRICE_RANGE_SPREAD:
                    result.price_range_valid = False
                    result.underquoting_indicators.append(UnderquotingIndicator(
                        indicator_type="EXCESSIVE_RANGE",
                        description="Price range exceeds legal maximum",
                        detail=f"Price range spread of {spread * 100:.1f}% exceeds legal maximum of 10%",
                        severity="CONCERN"
                    ))
                    result.compliance_issues.append(
                        f"Price range spread ({spread * 100:.1f}%) exceeds 10% legal maximum"
                    )

        # Check number of comparables provided
        comparables_provided = len(result.comparable_sales_provided)
        if comparables_provided < 3:
            result.compliance_issues.append(
                f"Only {comparables_provided} comparable(s) provided. "
                "Victorian regulations require minimum 3 comparables."
            )

        # Compare agent's comparables to actual market
        if actual_comparables and result.comparable_sales_provided:
            self._compare_comparables(result, actual_comparables)

        # If final sale price known, check against quoted range
        if final_sale_price and price_range:
            self._check_final_price(result, final_sale_price, price_range)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _compare_comparables(
        self,
        result: SOIAnalysisResult,
        actual_comparables: List[Dict[str, Any]]
    ):
        """Compare agent's comparables to independent comparables."""
        agent_prices = [
            c.get("sale_price", 0)
            for c in result.comparable_sales_provided
            if c.get("sale_price", 0) > 0
        ]
        actual_prices = [
            c.get("sale_price", 0)
            for c in actual_comparables
            if c.get("sale_price", 0) > 0
        ]

        if agent_prices and actual_prices:
            agent_median = statistics.median(agent_prices)
            actual_median = statistics.median(actual_prices)

            # Agent comparables significantly below market
            if agent_median < actual_median * 0.9:
                difference = ((actual_median - agent_median) / actual_median) * 100

                result.cherry_picking_indicators.append(UnderquotingIndicator(
                    indicator_type="LOW_COMPARABLES",
                    description="Agent's comparables below market median",
                    detail=(
                        f"Agent's comparables median ${agent_median:,.0f} is "
                        f"{difference:.1f}% below actual market median ${actual_median:,.0f}"
                    ),
                    severity="WARNING"
                ))

            # Check if agent chose lowest sales
            agent_max = max(agent_prices)
            actual_high_sales = [p for p in actual_prices if p > agent_max]

            if len(actual_high_sales) > len(actual_prices) * 0.5:
                result.cherry_picking_indicators.append(UnderquotingIndicator(
                    indicator_type="SELECTIVE_COMPARABLES",
                    description="Agent may have selected lower comparables",
                    detail=(
                        f"More than 50% of actual comparables are higher than "
                        f"agent's highest comparable (${agent_max:,.0f})"
                    ),
                    severity="WARNING"
                ))

    def _check_final_price(
        self,
        result: SOIAnalysisResult,
        final_price: float,
        price_range: Dict[str, float]
    ):
        """Check final sale price against quoted range."""
        high = price_range.get("high", 0)

        if final_price > high * 1.1:
            premium = ((final_price - high) / high) * 100
            result.underquoting_indicators.append(UnderquotingIndicator(
                indicator_type="SALE_EXCEEDED_QUOTE",
                description="Sale price significantly exceeded quoted range",
                detail=(
                    f"Final sale price ${final_price:,.0f} exceeded quoted "
                    f"high of ${high:,.0f} by {premium:.1f}%"
                ),
                severity="CONCERN"
            ))

    def _generate_recommendations(self, result: SOIAnalysisResult) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.compliance_issues:
            recommendations.append(
                "Potential compliance issues identified. "
                "Consider reporting to Consumer Affairs Victoria if concerned."
            )

        if result.underquoting_indicators:
            recommendations.append(
                "Underquoting indicators present. Conduct independent "
                "price research before making offers."
            )

        if result.cherry_picking_indicators:
            recommendations.append(
                "Agent's comparables appear selectively chosen. "
                "Obtain independent comparable sales report."
            )

        if not recommendations:
            recommendations.append(
                "Statement of Information appears compliant. "
                "Verify comparables are relevant to subject property."
            )

        return recommendations


# ============================================================================
# DUE DILIGENCE COMPLIANCE TRACKER
# ============================================================================

# Consumer Affairs Victoria Section 33B mandatory checklist items
CAV_DUE_DILIGENCE_CHECKLIST = {
    "property_information": {
        "description": "Property Information",
        "items": [
            {"id": "title_search", "name": "Certificate of Title search", "required": True},
            {"id": "company_search", "name": "Company/business name search", "required_if": "corporate_vendor"},
            {"id": "plan_subdivision", "name": "Plan of subdivision / strata plan", "required": True},
            {"id": "body_corp_records", "name": "Body corporate records", "required_if": "strata"},
            {"id": "building_permits", "name": "Building approvals and permits", "required": True},
            {"id": "council_zoning", "name": "Council zoning certificate", "required": True}
        ]
    },
    "financial_information": {
        "description": "Financial Information",
        "items": [
            {"id": "outstanding_rates", "name": "Outstanding rates, taxes, charges", "required": True},
            {"id": "land_tax", "name": "Land tax status", "required": True},
            {"id": "body_corp_fees", "name": "Outstanding body corporate fees", "required_if": "strata"}
        ]
    },
    "physical_information": {
        "description": "Physical Information",
        "items": [
            {"id": "building_inspection", "name": "Building inspection report", "required": True},
            {"id": "pest_inspection", "name": "Pest inspection report", "required": True},
            {"id": "pool_compliance", "name": "Swimming pool compliance", "required_if": "pool"}
        ]
    },
    "planning_information": {
        "description": "Planning Information",
        "items": [
            {"id": "current_zoning", "name": "Current zoning", "required": True},
            {"id": "planning_overlays", "name": "Planning overlays", "required": True},
            {"id": "nearby_developments", "name": "Proposed developments nearby", "required": False}
        ]
    },
    "safety_information": {
        "description": "Safety Information",
        "items": [
            {"id": "flood_risk", "name": "Flood risk", "required": True},
            {"id": "bushfire_risk", "name": "Bushfire risk", "required": True},
            {"id": "contamination_risk", "name": "Contamination risk", "required": True}
        ]
    }
}


@dataclass
class ChecklistItem:
    """A single checklist item with status."""
    item_id: str
    name: str
    category: str
    status: ComplianceStatus
    required: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "required": self.required,
            "notes": self.notes
        }


@dataclass
class ComplianceTrackerResult:
    """Due diligence compliance tracking result."""
    completion_rate: float = 0.0
    completed_items: List[ChecklistItem] = field(default_factory=list)
    pending_items: List[ChecklistItem] = field(default_factory=list)
    not_applicable_items: List[ChecklistItem] = field(default_factory=list)
    ready_for_purchase: bool = False
    priority_actions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completion_rate_percent": round(self.completion_rate, 1),
            "completed_items": [i.to_dict() for i in self.completed_items],
            "completed_count": len(self.completed_items),
            "pending_items": [i.to_dict() for i in self.pending_items],
            "pending_count": len(self.pending_items),
            "not_applicable_items": [i.to_dict() for i in self.not_applicable_items],
            "ready_for_purchase": self.ready_for_purchase,
            "priority_actions": self.priority_actions,
            "recommendations": self.recommendations
        }


class DueDiligenceComplianceTracker:
    """
    Tracks completion of due diligence against CAV checklist.
    """

    def __init__(self):
        self.checklist = CAV_DUE_DILIGENCE_CHECKLIST

    def get_completion_status(
        self,
        property_analysis: Dict[str, Any],
        property_context: Optional[Dict[str, Any]] = None
    ) -> ComplianceTrackerResult:
        """
        Get due diligence completion status.

        Args:
            property_analysis: Results from all analysis modules
            property_context: Context about property:
                - property_type: 'house', 'apartment', etc.
                - has_pool: bool
                - corporate_vendor: bool

        Returns:
            ComplianceTrackerResult with completion tracking
        """
        result = ComplianceTrackerResult()
        context = property_context or {}

        property_type = context.get("property_type", "house")
        has_pool = context.get("has_pool", False)
        corporate_vendor = context.get("corporate_vendor", False)

        for category_key, category_data in self.checklist.items():
            category_name = category_data["description"]

            for item in category_data["items"]:
                # Check if item applies
                required_if = item.get("required_if")
                applies = True

                if required_if == "strata" and property_type not in ["apartment", "townhouse", "unit"]:
                    applies = False
                elif required_if == "pool" and not has_pool:
                    applies = False
                elif required_if == "corporate_vendor" and not corporate_vendor:
                    applies = False

                if not applies:
                    result.not_applicable_items.append(ChecklistItem(
                        item_id=item["id"],
                        name=item["name"],
                        category=category_name,
                        status=ComplianceStatus.NOT_APPLICABLE,
                        required=False
                    ))
                    continue

                # Check if item is complete
                status = self._check_item_status(item["id"], property_analysis)

                checklist_item = ChecklistItem(
                    item_id=item["id"],
                    name=item["name"],
                    category=category_name,
                    status=status,
                    required=item.get("required", True)
                )

                if status == ComplianceStatus.COMPLETE:
                    result.completed_items.append(checklist_item)
                else:
                    result.pending_items.append(checklist_item)

        # Calculate completion rate
        total_applicable = len(result.completed_items) + len(result.pending_items)
        if total_applicable > 0:
            result.completion_rate = (len(result.completed_items) / total_applicable) * 100

        # Determine if ready for purchase
        result.ready_for_purchase = result.completion_rate >= 90

        # Generate priority actions
        result.priority_actions = self._get_priority_actions(result.pending_items)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _check_item_status(
        self,
        item_id: str,
        property_analysis: Dict[str, Any]
    ) -> ComplianceStatus:
        """Check completion status of a checklist item."""
        # Map item IDs to analysis data
        status_checks = {
            "title_search": lambda a: bool(a.get("title_analysis")),
            "company_search": lambda a: bool(a.get("company_search_done")),
            "plan_subdivision": lambda a: bool(a.get("section_32_analysis", {}).get("present_components")),
            "body_corp_records": lambda a: bool(a.get("strata_analysis")),
            "building_permits": lambda a: bool(a.get("building_permits")),
            "council_zoning": lambda a: bool(a.get("planning_analysis")),
            "outstanding_rates": lambda a: bool(a.get("financial_analysis", {}).get("outgoings")),
            "land_tax": lambda a: bool(a.get("financial_analysis", {}).get("outgoings", {}).get("land_tax") is not None),
            "body_corp_fees": lambda a: bool(a.get("strata_analysis", {}).get("financial")),
            "building_inspection": lambda a: bool(a.get("physical_analysis", {}).get("defects_detected") is not None),
            "pest_inspection": lambda a: bool(a.get("physical_analysis", {}).get("termite_risk")),
            "pool_compliance": lambda a: bool(a.get("pool_compliance")),
            "current_zoning": lambda a: bool(a.get("planning_analysis", {}).get("zone")),
            "planning_overlays": lambda a: bool(a.get("planning_analysis", {}).get("overlays") is not None),
            "nearby_developments": lambda a: bool(a.get("nearby_developments_checked")),
            "flood_risk": lambda a: bool(a.get("street_level_analysis", {}).get("flood_risk")),
            "bushfire_risk": lambda a: bool(a.get("street_level_analysis", {}).get("bushfire_risk")),
            "contamination_risk": lambda a: bool(a.get("environmental_analysis"))
        }

        check_fn = status_checks.get(item_id)
        if check_fn:
            try:
                return ComplianceStatus.COMPLETE if check_fn(property_analysis) else ComplianceStatus.PENDING
            except Exception:
                pass

        return ComplianceStatus.PENDING

    def _get_priority_actions(self, pending_items: List[ChecklistItem]) -> List[str]:
        """Get prioritized actions for pending items."""
        priorities = []

        # Critical items first
        critical_items = ["title_search", "building_inspection", "pest_inspection", "current_zoning"]

        for item in pending_items:
            if item.item_id in critical_items:
                priorities.append(f"PRIORITY: Complete {item.name}")

        # Then other required items
        for item in pending_items:
            if item.required and item.item_id not in critical_items:
                priorities.append(f"Complete {item.name}")

        return priorities[:5]  # Top 5 priorities

    def _generate_recommendations(self, result: ComplianceTrackerResult) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.completion_rate < 50:
            recommendations.append(
                "Due diligence less than 50% complete. "
                "Not ready for unconditional purchase."
            )
        elif result.completion_rate < 90:
            recommendations.append(
                f"Due diligence {result.completion_rate:.0f}% complete. "
                "Complete priority items before exchange."
            )
        else:
            recommendations.append(
                "Due diligence substantially complete. "
                "Final review by conveyancer recommended."
            )

        if result.priority_actions:
            recommendations.append(
                "Top priority: " + result.priority_actions[0]
            )

        return recommendations


# Convenience functions
def analyze_soi(
    price_range_low: float,
    price_range_high: float,
    comparables: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Quick SOI analysis.
    """
    analyzer = StatementOfInformationAnalyzer()
    result = analyzer.analyze(
        soi={
            "price_range": {"low": price_range_low, "high": price_range_high},
            "comparable_sales": comparables
        }
    )
    return result.to_dict()


def get_dd_completion(
    analyses: Dict[str, Any],
    property_type: str = "house"
) -> Dict[str, Any]:
    """
    Get due diligence completion status.
    """
    tracker = DueDiligenceComplianceTracker()
    result = tracker.get_completion_status(
        property_analysis=analyses,
        property_context={"property_type": property_type}
    )
    return result.to_dict()


# ============================================================================
# SECTION 33B - SALE OF LAND ACT COMPLIANCE
# ============================================================================

"""
Consumer Victoria Due Diligence Checklist mapping to automated checks.

Reference: Sale of Land Act 1962 (Vic) Section 32 & 33B
          Consumer Affairs Victoria Due Diligence Checklist

This module maps the official CAV checklist requirements to our automated
analysis capabilities, ensuring comprehensive coverage.
"""

# Official Consumer Victoria Due Diligence Categories
# Source: https://www.consumer.vic.gov.au/housing/buying-and-selling-property/
#         checklists/due-diligence-checklist

SECTION_33B_REQUIREMENTS = {
    "title_encumbrances": {
        "category": "Title & Encumbrances",
        "legal_reference": "Sale of Land Act s32(2)(a)",
        "description": "Verify title is clear and understand any encumbrances",
        "items": [
            {
                "id": "s33b_title_search",
                "name": "Certificate of Title search",
                "description": "Verify ownership, dimensions, and registered encumbrances",
                "mandatory": True,
                "automated_check": "title_analysis",
                "data_source": "LANDATA",
                "typical_cost": "$25-35"
            },
            {
                "id": "s33b_caveats",
                "name": "Caveats on title",
                "description": "Check for any caveats preventing sale or transfer",
                "mandatory": True,
                "automated_check": "title_analysis.caveats",
                "data_source": "LANDATA",
                "risk_if_present": "May prevent settlement"
            },
            {
                "id": "s33b_easements",
                "name": "Easements and rights of way",
                "description": "Understand any easements affecting the property",
                "mandatory": True,
                "automated_check": "title_analysis.easements",
                "data_source": "LANDATA/Section 32",
                "risk_if_present": "May restrict building/use"
            },
            {
                "id": "s33b_covenants",
                "name": "Restrictive covenants",
                "description": "Check for covenants restricting use or development",
                "mandatory": True,
                "automated_check": "title_analysis.covenants",
                "data_source": "LANDATA/Section 32",
                "risk_if_present": "May restrict intended use"
            },
            {
                "id": "s33b_section_173",
                "name": "Section 173 agreements",
                "description": "Check for planning agreements with ongoing obligations",
                "mandatory": True,
                "automated_check": "title_analysis.section_173",
                "data_source": "LANDATA/VicPlan",
                "risk_if_present": "Financial/maintenance obligations"
            },
            {
                "id": "s33b_proprietor",
                "name": "Verify vendor is registered proprietor",
                "description": "Ensure vendor has legal right to sell",
                "mandatory": True,
                "automated_check": "title_analysis.proprietor_mismatch",
                "data_source": "LANDATA vs Contract",
                "risk_if_present": "Potential fraud or complications"
            }
        ]
    },
    "planning_zoning": {
        "category": "Planning & Zoning",
        "legal_reference": "Sale of Land Act s32(2)(d)",
        "description": "Understand what you can and cannot do with the property",
        "items": [
            {
                "id": "s33b_zone",
                "name": "Planning zone",
                "description": "Verify current planning zone and permitted uses",
                "mandatory": True,
                "automated_check": "planning_analysis.zone",
                "data_source": "VicPlan WFS",
                "typical_cost": "Free via VicPlan"
            },
            {
                "id": "s33b_overlays",
                "name": "Planning overlays",
                "description": "Identify all planning overlays affecting the property",
                "mandatory": True,
                "automated_check": "planning_analysis.overlays",
                "data_source": "VicPlan WFS",
                "typical_cost": "Free via VicPlan"
            },
            {
                "id": "s33b_heritage",
                "name": "Heritage controls",
                "description": "Check for heritage overlay or heritage listing",
                "mandatory": True,
                "automated_check": "heritage_analysis",
                "data_source": "Heritage Victoria VHD",
                "risk_if_present": "Restrictions on alterations"
            },
            {
                "id": "s33b_building_permits",
                "name": "Building permits and approvals",
                "description": "Verify all works have proper permits",
                "mandatory": True,
                "automated_check": "planning_analysis.permits",
                "data_source": "Council records",
                "risk_if_present": "Unpermitted works"
            },
            {
                "id": "s33b_illegal_works",
                "name": "Potential illegal structures",
                "description": "Check for structures without permits",
                "mandatory": True,
                "automated_check": "planning_analysis.illegal_works",
                "data_source": "Council records vs inspection",
                "risk_if_present": "Demolition/rectification orders"
            }
        ]
    },
    "environmental_hazards": {
        "category": "Environmental & Natural Hazards",
        "legal_reference": "Sale of Land Act s32(2)(e)",
        "description": "Understand natural hazard risks and environmental issues",
        "items": [
            {
                "id": "s33b_flood_risk",
                "name": "Flood risk assessment",
                "description": "Check if property is in flood overlay or flood zone",
                "mandatory": True,
                "automated_check": "street_level_analysis.flood_risk",
                "data_source": "VicPlan LSIO/SBO layers",
                "risk_if_present": "Insurance/building restrictions"
            },
            {
                "id": "s33b_bushfire_risk",
                "name": "Bushfire risk assessment",
                "description": "Check bushfire overlay and BAL rating",
                "mandatory": True,
                "automated_check": "street_level_analysis.bushfire_risk",
                "data_source": "VicPlan BMO/WMO layers",
                "risk_if_present": "Building standards/insurance"
            },
            {
                "id": "s33b_contamination",
                "name": "Land contamination",
                "description": "Check EPA Priority Sites Register and historical use",
                "mandatory": True,
                "automated_check": "environmental_analysis.contamination",
                "data_source": "EPA Victoria Priority Sites",
                "risk_if_present": "Remediation costs/health risks"
            },
            {
                "id": "s33b_mining",
                "name": "Mining or extraction history",
                "description": "Check for mining tenements or extraction operations",
                "mandatory": True,
                "automated_check": "mining_analysis",
                "data_source": "GeoVic Mining Tenements",
                "risk_if_present": "Subsidence/access issues"
            },
            {
                "id": "s33b_asbestos",
                "name": "Asbestos risk",
                "description": "Assess asbestos risk based on building age",
                "mandatory": True,
                "automated_check": "physical_analysis.asbestos",
                "data_source": "Building inspection",
                "risk_if_present": "Removal costs"
            }
        ]
    },
    "physical_condition": {
        "category": "Physical Condition",
        "legal_reference": "Sale of Land Act s32(2)(f)",
        "description": "Understand the physical condition of the property",
        "items": [
            {
                "id": "s33b_building_inspection",
                "name": "Building/structural inspection",
                "description": "Professional inspection for structural defects",
                "mandatory": True,
                "automated_check": "physical_analysis.defects_detected",
                "data_source": "Professional inspection",
                "typical_cost": "$400-800"
            },
            {
                "id": "s33b_pest_inspection",
                "name": "Pest and termite inspection",
                "description": "Check for termite damage and active infestations",
                "mandatory": True,
                "automated_check": "physical_analysis.termite_risk",
                "data_source": "Professional inspection",
                "typical_cost": "$250-400"
            },
            {
                "id": "s33b_pool_compliance",
                "name": "Swimming pool compliance",
                "description": "Verify pool barrier compliance certificate",
                "mandatory_if": "has_pool",
                "automated_check": "pool_compliance",
                "data_source": "Council records",
                "risk_if_present": "Fines/rectification required"
            },
            {
                "id": "s33b_services",
                "name": "Services and utilities",
                "description": "Verify connection to essential services",
                "mandatory": True,
                "automated_check": "utilities_analysis",
                "data_source": "NBN/utility providers",
                "typical_cost": "Free checks"
            }
        ]
    },
    "strata_body_corporate": {
        "category": "Strata/Body Corporate",
        "legal_reference": "Sale of Land Act s32(3)",
        "description": "For units/apartments - understand strata situation",
        "applies_to": ["apartment", "unit", "townhouse"],
        "items": [
            {
                "id": "s33b_strata_search",
                "name": "Owners Corporation certificate",
                "description": "Obtain OC certificate with financial details",
                "mandatory": True,
                "automated_check": "strata_analysis.financial",
                "data_source": "Strata manager/OC",
                "typical_cost": "$150-300"
            },
            {
                "id": "s33b_strata_financials",
                "name": "OC financial statements",
                "description": "Review OC financial health and reserves",
                "mandatory": True,
                "automated_check": "strata_analysis.financial.financial_health_score",
                "data_source": "OC records",
                "risk_if_present": "Special levies"
            },
            {
                "id": "s33b_special_levies",
                "name": "Pending/planned special levies",
                "description": "Check for known upcoming special levies",
                "mandatory": True,
                "automated_check": "strata_analysis.financial.special_levies",
                "data_source": "OC records",
                "risk_if_present": "Unexpected costs"
            },
            {
                "id": "s33b_cladding",
                "name": "Combustible cladding audit",
                "description": "Check cladding status for buildings 2+ stories",
                "mandatory_if": "multi_story",
                "automated_check": "strata_analysis.cladding.risk_level",
                "data_source": "Cladding Safety Victoria",
                "risk_if_present": "Rectification costs"
            },
            {
                "id": "s33b_bylaws",
                "name": "OC rules and by-laws",
                "description": "Understand restrictions on use",
                "mandatory": True,
                "automated_check": "strata_analysis.bylaws",
                "data_source": "OC records",
                "risk_if_present": "Use restrictions"
            }
        ]
    },
    "financial_obligations": {
        "category": "Financial Obligations",
        "legal_reference": "Sale of Land Act s32(2)(g)",
        "description": "Understand ongoing and outstanding financial obligations",
        "items": [
            {
                "id": "s33b_council_rates",
                "name": "Outstanding council rates",
                "description": "Check for unpaid council rates",
                "mandatory": True,
                "automated_check": "financial_analysis.outgoings.council_rates",
                "data_source": "Section 32/Council",
                "typical_cost": "$2,000-4,000/year"
            },
            {
                "id": "s33b_water_rates",
                "name": "Outstanding water rates",
                "description": "Check for unpaid water rates",
                "mandatory": True,
                "automated_check": "financial_analysis.outgoings.water_rates",
                "data_source": "Section 32/Water authority",
                "typical_cost": "$700-1,200/year"
            },
            {
                "id": "s33b_land_tax",
                "name": "Land tax status",
                "description": "Verify land tax is current",
                "mandatory": True,
                "automated_check": "financial_analysis.outgoings.land_tax",
                "data_source": "State Revenue Office",
                "typical_cost": "Varies by value"
            }
        ]
    },
    "contract_documents": {
        "category": "Contract & Documents",
        "legal_reference": "Sale of Land Act s32",
        "description": "Review all contract documents thoroughly",
        "items": [
            {
                "id": "s33b_section_32",
                "name": "Section 32 statement",
                "description": "Review vendor disclosure statement",
                "mandatory": True,
                "automated_check": "section_32_analysis",
                "data_source": "Contract of Sale",
                "risk_if_present": "Rescission rights if defective"
            },
            {
                "id": "s33b_special_conditions",
                "name": "Special conditions of sale",
                "description": "Review and understand all special conditions",
                "mandatory": True,
                "automated_check": "special_conditions",
                "data_source": "Contract of Sale",
                "risk_if_present": "Unfavorable terms"
            },
            {
                "id": "s33b_cooling_off",
                "name": "Cooling off rights",
                "description": "Understand cooling off period and exceptions",
                "mandatory": True,
                "automated_check": "cooling_off_analysis",
                "data_source": "Contract of Sale",
                "typical_cost": "3 business days"
            }
        ]
    }
}


@dataclass
class Section33BItem:
    """Individual Section 33B checklist item."""
    item_id: str
    name: str
    category: str
    description: str
    legal_reference: str
    mandatory: bool
    status: ComplianceStatus
    automated_check: str
    data_source: str
    findings: str = ""
    risk_level: str = "none"  # none, low, medium, high, critical
    action_required: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "legal_reference": self.legal_reference,
            "mandatory": self.mandatory,
            "status": self.status.value,
            "automated_check": self.automated_check,
            "data_source": self.data_source,
            "findings": self.findings,
            "risk_level": self.risk_level,
            "action_required": self.action_required
        }


@dataclass
class Section33BResult:
    """Complete Section 33B compliance result."""
    overall_compliance: float = 0.0    # Percentage
    mandatory_complete: bool = False
    ready_for_exchange: bool = False

    # Category summaries
    category_scores: Dict[str, float] = field(default_factory=dict)

    # Items by status
    completed_items: List[Section33BItem] = field(default_factory=list)
    pending_items: List[Section33BItem] = field(default_factory=list)
    not_applicable: List[Section33BItem] = field(default_factory=list)

    # Risk items
    high_risk_items: List[Section33BItem] = field(default_factory=list)
    medium_risk_items: List[Section33BItem] = field(default_factory=list)

    # Actions and recommendations
    immediate_actions: List[str] = field(default_factory=list)
    pre_exchange_actions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Specialist referrals
    specialists_required: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_compliance_percent": round(self.overall_compliance, 1),
            "mandatory_complete": self.mandatory_complete,
            "ready_for_exchange": self.ready_for_exchange,
            "category_scores": {k: round(v, 1) for k, v in self.category_scores.items()},
            "completed_items": [i.to_dict() for i in self.completed_items],
            "completed_count": len(self.completed_items),
            "pending_items": [i.to_dict() for i in self.pending_items],
            "pending_count": len(self.pending_items),
            "not_applicable": [i.to_dict() for i in self.not_applicable],
            "high_risk_items": [i.to_dict() for i in self.high_risk_items],
            "medium_risk_items": [i.to_dict() for i in self.medium_risk_items],
            "immediate_actions": self.immediate_actions,
            "pre_exchange_actions": self.pre_exchange_actions,
            "recommendations": self.recommendations,
            "specialists_required": self.specialists_required
        }


class Section33BComplianceChecker:
    """
    Comprehensive Section 33B (Sale of Land Act) compliance checker.

    Maps all automated analysis results to the official Consumer Victoria
    due diligence checklist requirements.
    """

    def __init__(self):
        self.requirements = SECTION_33B_REQUIREMENTS

    def check_compliance(
        self,
        all_analyses: Dict[str, Any],
        property_context: Optional[Dict[str, Any]] = None
    ) -> Section33BResult:
        """
        Check compliance with Section 33B requirements.

        Args:
            all_analyses: Dict containing all analysis results:
                - title_analysis
                - planning_analysis
                - environmental_analysis
                - physical_analysis
                - strata_analysis
                - financial_analysis
                - section_32_analysis
                - special_conditions
                - cooling_off_analysis
                - street_level_analysis
                - heritage_analysis
                - mining_analysis
                - utilities_analysis

            property_context: Property details:
                - property_type: 'house', 'apartment', etc.
                - has_pool: bool
                - multi_story: bool

        Returns:
            Section33BResult with comprehensive compliance status
        """
        result = Section33BResult()
        context = property_context or {}

        property_type = context.get("property_type", "house").lower()
        has_pool = context.get("has_pool", False)
        multi_story = context.get("multi_story", False)

        all_items = []

        for category_key, category_data in self.requirements.items():
            category_name = category_data["category"]
            legal_ref = category_data.get("legal_reference", "")

            # Check if category applies
            applies_to = category_data.get("applies_to")
            if applies_to and property_type not in applies_to:
                continue

            category_items = []

            for item_config in category_data["items"]:
                # Check mandatory_if conditions
                mandatory_if = item_config.get("mandatory_if")
                is_mandatory = item_config.get("mandatory", True)

                if mandatory_if == "has_pool" and not has_pool:
                    result.not_applicable.append(Section33BItem(
                        item_id=item_config["id"],
                        name=item_config["name"],
                        category=category_name,
                        description=item_config["description"],
                        legal_reference=legal_ref,
                        mandatory=False,
                        status=ComplianceStatus.NOT_APPLICABLE,
                        automated_check=item_config.get("automated_check", ""),
                        data_source=item_config.get("data_source", ""),
                        findings="Not applicable - no pool"
                    ))
                    continue

                if mandatory_if == "multi_story" and not multi_story:
                    result.not_applicable.append(Section33BItem(
                        item_id=item_config["id"],
                        name=item_config["name"],
                        category=category_name,
                        description=item_config["description"],
                        legal_reference=legal_ref,
                        mandatory=False,
                        status=ComplianceStatus.NOT_APPLICABLE,
                        automated_check=item_config.get("automated_check", ""),
                        data_source=item_config.get("data_source", ""),
                        findings="Not applicable - single story"
                    ))
                    continue

                # Check status and get findings
                status, findings, risk_level = self._check_item(
                    item_config, all_analyses
                )

                item = Section33BItem(
                    item_id=item_config["id"],
                    name=item_config["name"],
                    category=category_name,
                    description=item_config["description"],
                    legal_reference=legal_ref,
                    mandatory=is_mandatory,
                    status=status,
                    automated_check=item_config.get("automated_check", ""),
                    data_source=item_config.get("data_source", ""),
                    findings=findings,
                    risk_level=risk_level
                )

                if risk_level in ["high", "critical"]:
                    item.action_required = f"Investigate: {findings}"
                    result.high_risk_items.append(item)
                elif risk_level == "medium":
                    result.medium_risk_items.append(item)

                if status == ComplianceStatus.COMPLETE:
                    result.completed_items.append(item)
                else:
                    result.pending_items.append(item)

                category_items.append(item)
                all_items.append(item)

            # Calculate category score
            if category_items:
                completed = sum(1 for i in category_items if i.status == ComplianceStatus.COMPLETE)
                result.category_scores[category_name] = (completed / len(category_items)) * 100

        # Calculate overall compliance
        applicable_items = result.completed_items + result.pending_items
        if applicable_items:
            result.overall_compliance = (len(result.completed_items) / len(applicable_items)) * 100

        # Check if all mandatory items complete
        mandatory_items = [i for i in applicable_items if i.mandatory]
        mandatory_complete = [i for i in mandatory_items if i.status == ComplianceStatus.COMPLETE]
        result.mandatory_complete = len(mandatory_complete) == len(mandatory_items)

        # Ready for exchange if 90%+ complete and no critical risks
        critical_risks = [i for i in result.high_risk_items if i.risk_level == "critical"]
        result.ready_for_exchange = (
            result.overall_compliance >= 90 and
            result.mandatory_complete and
            len(critical_risks) == 0
        )

        # Generate actions
        result.immediate_actions = self._get_immediate_actions(result)
        result.pre_exchange_actions = self._get_pre_exchange_actions(result)
        result.recommendations = self._generate_recommendations(result)
        result.specialists_required = self._get_specialists_required(result)

        return result

    def _check_item(
        self,
        item_config: Dict[str, Any],
        all_analyses: Dict[str, Any]
    ) -> tuple:
        """
        Check status of a single item.

        Returns: (status, findings, risk_level)
        """
        automated_check = item_config.get("automated_check", "")

        if not automated_check:
            return ComplianceStatus.PENDING, "Manual check required", "none"

        # Navigate to the data
        parts = automated_check.split(".")
        data = all_analyses

        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return ComplianceStatus.PENDING, "Data not available", "none"

        # Determine findings and risk
        findings = ""
        risk_level = "none"

        if data is None:
            return ComplianceStatus.PENDING, "Not yet assessed", "none"

        # Item-specific interpretations
        item_id = item_config["id"]

        if item_id == "s33b_caveats":
            if isinstance(data, list) and len(data) > 0:
                findings = f"{len(data)} caveat(s) on title"
                risk_level = "high" if len(data) > 0 else "none"
            else:
                findings = "No caveats found"

        elif item_id == "s33b_flood_risk":
            if isinstance(data, dict):
                if data.get("in_flood_zone") or data.get("building_at_risk"):
                    findings = "Property in flood zone"
                    risk_level = "high"
                else:
                    findings = "No flood risk identified"
            elif data:
                findings = "Flood risk data available"

        elif item_id == "s33b_bushfire_risk":
            if isinstance(data, dict):
                bal = data.get("bal_rating", "")
                if "BAL" in str(bal) and bal not in ["BAL-LOW", ""]:
                    findings = f"Bushfire zone - {bal}"
                    risk_level = "high" if "FZ" in bal or "40" in bal else "medium"
                else:
                    findings = "No significant bushfire risk"

        elif item_id == "s33b_contamination":
            if isinstance(data, dict):
                risk = data.get("contamination_risk", "")
                if risk in ["HIGH", "CRITICAL"]:
                    findings = "Contamination risk identified"
                    risk_level = "critical"
                elif risk == "MEDIUM":
                    findings = "Potential contamination - investigation recommended"
                    risk_level = "medium"
                else:
                    findings = "No contamination risk identified"
            elif data:
                findings = "Contamination data available"

        elif item_id == "s33b_heritage":
            if isinstance(data, dict):
                if data.get("is_listed") or data.get("in_heritage_overlay"):
                    findings = "Heritage controls apply"
                    risk_level = "medium"
                else:
                    findings = "No heritage controls"
            elif data:
                findings = "Heritage data checked"

        elif item_id == "s33b_strata_financials":
            if isinstance(data, dict):
                score = data.get("financial_health_score", 50)
                if score < 30:
                    findings = f"Poor OC financial health (score: {score})"
                    risk_level = "high"
                elif score < 50:
                    findings = f"Moderate OC financial health (score: {score})"
                    risk_level = "medium"
                else:
                    findings = f"Good OC financial health (score: {score})"
            elif isinstance(data, (int, float)):
                findings = f"Financial health score: {data}"

        elif item_id == "s33b_cladding":
            if isinstance(data, str):
                if data in ["HIGH", "CRITICAL"]:
                    findings = "Combustible cladding risk identified"
                    risk_level = "critical"
                elif data == "MEDIUM":
                    findings = "Potential cladding concerns"
                    risk_level = "medium"
                else:
                    findings = "No cladding concerns"

        elif item_id == "s33b_section_32":
            if isinstance(data, dict):
                if data.get("rescission_risk"):
                    findings = "Section 32 has defects - rescission risk"
                    risk_level = "high"
                elif data.get("missing_critical"):
                    findings = f"Missing critical items: {len(data.get('missing_critical', []))}"
                    risk_level = "medium"
                else:
                    findings = "Section 32 appears complete"

        else:
            # Generic check
            if isinstance(data, dict):
                findings = "Data reviewed"
            elif isinstance(data, bool):
                findings = "Checked" if data else "Issue identified"
                risk_level = "medium" if not data else "none"
            elif isinstance(data, list):
                findings = f"{len(data)} item(s) found"
            else:
                findings = str(data)[:100]

        return ComplianceStatus.COMPLETE, findings, risk_level

    def _get_immediate_actions(self, result: Section33BResult) -> List[str]:
        """Get immediate actions required."""
        actions = []

        # Critical risk items
        for item in result.high_risk_items:
            if item.risk_level == "critical":
                actions.append(f"URGENT: {item.name} - {item.findings}")

        # Key missing mandatory items
        critical_ids = [
            "s33b_title_search", "s33b_section_32",
            "s33b_flood_risk", "s33b_bushfire_risk"
        ]

        for item in result.pending_items:
            if item.mandatory and item.item_id in critical_ids:
                actions.append(f"Complete: {item.name}")

        return actions[:5]

    def _get_pre_exchange_actions(self, result: Section33BResult) -> List[str]:
        """Get actions required before exchange."""
        actions = []

        for item in result.pending_items:
            if item.mandatory:
                actions.append(f"{item.name} ({item.data_source})")

        for item in result.high_risk_items:
            actions.append(f"Resolve: {item.name}")

        return actions[:10]

    def _generate_recommendations(self, result: Section33BResult) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.ready_for_exchange:
            recommendations.append(
                "Due diligence substantially complete. "
                "Final review with conveyancer before exchange."
            )
        elif result.overall_compliance >= 70:
            recommendations.append(
                f"Due diligence {result.overall_compliance:.0f}% complete. "
                "Complete remaining items before exchange."
            )
        else:
            recommendations.append(
                f"Due diligence only {result.overall_compliance:.0f}% complete. "
                "Significant work required before exchange."
            )

        if result.high_risk_items:
            recommendations.append(
                f"{len(result.high_risk_items)} high-risk item(s) identified. "
                "Consider impact on purchase decision."
            )

        if not result.mandatory_complete:
            recommendations.append(
                "Mandatory checks incomplete. "
                "Do not proceed to exchange until resolved."
            )

        return recommendations

    def _get_specialists_required(self, result: Section33BResult) -> List[Dict[str, str]]:
        """Identify specialists required based on findings."""
        specialists = []

        # Check for specific risks requiring specialists
        pending_ids = {i.item_id for i in result.pending_items}
        risk_ids = {i.item_id for i in result.high_risk_items + result.medium_risk_items}

        if "s33b_building_inspection" in pending_ids:
            specialists.append({
                "type": "Building Inspector",
                "reason": "Building inspection not completed",
                "typical_cost": "$400-800"
            })

        if "s33b_pest_inspection" in pending_ids:
            specialists.append({
                "type": "Pest Inspector",
                "reason": "Pest inspection not completed",
                "typical_cost": "$250-400"
            })

        if "s33b_contamination" in risk_ids:
            specialists.append({
                "type": "Environmental Consultant",
                "reason": "Contamination risk identified",
                "typical_cost": "$1,000-5,000"
            })

        if any(i.item_id == "s33b_heritage" for i in result.high_risk_items):
            specialists.append({
                "type": "Heritage Consultant",
                "reason": "Heritage controls apply",
                "typical_cost": "$500-2,000"
            })

        if any(i.item_id == "s33b_cladding" for i in result.high_risk_items):
            specialists.append({
                "type": "Building Surveyor",
                "reason": "Cladding risk identified",
                "typical_cost": "Varies"
            })

        return specialists


# Convenience function
def check_section_33b_compliance(
    all_analyses: Dict[str, Any],
    property_type: str = "house",
    has_pool: bool = False
) -> Dict[str, Any]:
    """
    Check Section 33B compliance.

    Args:
        all_analyses: All analysis results
        property_type: Property type
        has_pool: Whether property has pool

    Returns:
        Dict with comprehensive compliance status
    """
    checker = Section33BComplianceChecker()
    result = checker.check_compliance(
        all_analyses=all_analyses,
        property_context={
            "property_type": property_type,
            "has_pool": has_pool,
            "multi_story": property_type == "apartment"
        }
    )
    return result.to_dict()
