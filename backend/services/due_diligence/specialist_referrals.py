"""
Specialist Referral Engine.

Determines when to recommend specialist reports based on property
analysis findings. Triggers referrals to structural engineers,
asbestos assessors, environmental auditors, and other specialists.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class SpecialistType(str, Enum):
    STRUCTURAL_ENGINEER = "structural_engineer"
    RISING_DAMP_SPECIALIST = "rising_damp_specialist"
    ELECTRICAL_INSPECTOR = "electrical_inspector"
    ASBESTOS_ASSESSOR = "asbestos_assessor"
    ENVIRONMENTAL_AUDITOR = "environmental_auditor"
    QUANTITY_SURVEYOR = "quantity_surveyor"
    HERITAGE_ARCHITECT = "heritage_architect"
    PLUMBER = "plumber"
    ROOF_SPECIALIST = "roof_specialist"
    GEOTECHNICAL_ENGINEER = "geotechnical_engineer"
    ARBORIST = "arborist"
    POOL_INSPECTOR = "pool_inspector"
    CONVEYANCER = "conveyancer"
    MORTGAGE_BROKER = "mortgage_broker"


class ReferralUrgency(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    RECOMMENDED = "RECOMMENDED"


@dataclass
class TriggerCondition:
    """A condition that triggers a specialist referral."""
    condition: str
    description: str
    triggered: bool = False
    evidence: Optional[str] = None


@dataclass
class SpecialistReferral:
    """A referral to a specialist."""
    specialist_type: SpecialistType
    specialist_name: str
    urgency: ReferralUrgency
    triggers: List[TriggerCondition]
    typical_cost: str
    expected_timeline: str
    benefit: Optional[str] = None
    notes: Optional[str] = None
    required_before: Optional[str] = None  # e.g., "settlement", "cooling_off", "renovation"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialist_type": self.specialist_type.value,
            "specialist_name": self.specialist_name,
            "urgency": self.urgency.value,
            "triggers": [
                {
                    "condition": t.condition,
                    "description": t.description,
                    "triggered": t.triggered,
                    "evidence": t.evidence
                }
                for t in self.triggers
            ],
            "typical_cost": self.typical_cost,
            "expected_timeline": self.expected_timeline,
            "benefit": self.benefit,
            "notes": self.notes,
            "required_before": self.required_before
        }


@dataclass
class ReferralResult:
    """Complete result of referral analysis."""
    critical_referrals: List[SpecialistReferral] = field(default_factory=list)
    high_priority_referrals: List[SpecialistReferral] = field(default_factory=list)
    recommended_referrals: List[SpecialistReferral] = field(default_factory=list)
    total_estimated_cost: str = "$0"
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "critical_referrals": [r.to_dict() for r in self.critical_referrals],
            "high_priority_referrals": [r.to_dict() for r in self.high_priority_referrals],
            "recommended_referrals": [r.to_dict() for r in self.recommended_referrals],
            "total_estimated_cost": self.total_estimated_cost,
            "summary": self.summary
        }


# Specialist referral trigger definitions
SPECIALIST_REFERRAL_TRIGGERS = {
    SpecialistType.STRUCTURAL_ENGINEER: {
        "name": "Structural Engineer",
        "triggers": [
            {"condition": "crack_width_mm > 2", "description": "Cracks exceed 2mm width"},
            {"condition": "foundation_movement_detected", "description": "Signs of foundation movement"},
            {"condition": "floor_unevenness > 10mm_per_meter", "description": "Significant floor slope detected"},
            {"condition": "wall_bulging_detected", "description": "Bulging or bowing walls"},
            {"condition": "reactive_soil_area", "description": "Property in reactive soil area"},
            {"condition": "retaining_wall_issues", "description": "Retaining wall showing distress"},
            {"condition": "load_bearing_wall_removal_planned", "description": "Planning to remove walls"}
        ],
        "typical_cost": "$500 - $1,500",
        "expected_timeline": "3-7 business days",
        "urgency": ReferralUrgency.HIGH,
        "required_before": "settlement"
    },
    SpecialistType.RISING_DAMP_SPECIALIST: {
        "name": "Rising Damp Specialist",
        "triggers": [
            {"condition": "efflorescence_detected", "description": "Salt deposits on walls"},
            {"condition": "peeling_paint_lower_walls", "description": "Paint peeling at base of walls"},
            {"condition": "musty_smell_detected", "description": "Persistent musty odor"},
            {"condition": "damp_patches_walls", "description": "Visible damp patches on walls"},
            {"condition": "moisture_readings_high", "description": "High moisture meter readings"}
        ],
        "typical_cost": "$300 - $800 for assessment",
        "expected_timeline": "2-5 business days",
        "urgency": ReferralUrgency.MEDIUM,
        "required_before": "settlement"
    },
    SpecialistType.ELECTRICAL_INSPECTOR: {
        "name": "Licensed Electrical Inspector",
        "triggers": [
            {"condition": "building_age > 30", "description": "Property over 30 years old"},
            {"condition": "switchboard_type == 'ceramic_fuses'", "description": "Old ceramic fuse switchboard"},
            {"condition": "wiring_visible_deterioration", "description": "Visible wiring deterioration"},
            {"condition": "no_safety_switch", "description": "No RCD/safety switch installed"},
            {"condition": "aluminium_wiring", "description": "Aluminium wiring detected (fire risk)"},
            {"condition": "renovation_planned", "description": "Electrical upgrades planned"}
        ],
        "typical_cost": "$200 - $500",
        "expected_timeline": "1-3 business days",
        "urgency": ReferralUrgency.HIGH,
        "required_before": "settlement"
    },
    SpecialistType.ASBESTOS_ASSESSOR: {
        "name": "Licensed Asbestos Assessor",
        "triggers": [
            {"condition": "building_year < 1990", "description": "Built before 1990 (asbestos era)"},
            {"condition": "suspected_asbestos_materials", "description": "Materials that may contain asbestos"},
            {"condition": "renovation_planned", "description": "Planning renovations on older property"},
            {"condition": "eaves_fibro_detected", "description": "Fibro eaves or cladding detected"},
            {"condition": "vinyl_flooring_pre_1980", "description": "Pre-1980 vinyl flooring"}
        ],
        "typical_cost": "$300 - $800 for inspection, $50-100 per sample tested",
        "expected_timeline": "3-5 business days (including lab results)",
        "urgency": ReferralUrgency.HIGH,
        "required_before": "renovation",
        "notes": "Critical if any renovation or demolition planned"
    },
    SpecialistType.ENVIRONMENTAL_AUDITOR: {
        "name": "EPA-Appointed Environmental Auditor",
        "triggers": [
            {"condition": "eao_overlay", "description": "Environmental Audit Overlay applies"},
            {"condition": "contamination_risk_high", "description": "High contamination risk identified"},
            {"condition": "historical_industrial_use", "description": "Former industrial use"},
            {"condition": "former_petrol_station", "description": "Former petrol station site"},
            {"condition": "former_dry_cleaner", "description": "Former dry cleaner site"},
            {"condition": "listed_on_priority_sites", "description": "Listed on EPA Priority Sites Register"}
        ],
        "typical_cost": "$20,000 - $100,000+",
        "expected_timeline": "3-6 months for full audit",
        "urgency": ReferralUrgency.CRITICAL,
        "required_before": "settlement",
        "notes": "CRITICAL for residential use - contamination can cost millions to remediate"
    },
    SpecialistType.QUANTITY_SURVEYOR: {
        "name": "Quantity Surveyor",
        "triggers": [
            {"condition": "investment_property", "description": "Purchasing as investment"},
            {"condition": "building_age < 40", "description": "Built after 1985 (eligible for building depreciation)"},
            {"condition": "recent_renovations", "description": "Recent renovations may have depreciable items"}
        ],
        "typical_cost": "$500 - $800",
        "expected_timeline": "2-3 weeks for full report",
        "urgency": ReferralUrgency.RECOMMENDED,
        "benefit": "Depreciation schedule can save $5,000-15,000+ in tax over holding period",
        "required_before": None  # Can be done post-settlement
    },
    SpecialistType.HERITAGE_ARCHITECT: {
        "name": "Heritage Architect",
        "triggers": [
            {"condition": "heritage_overlay", "description": "Heritage overlay (HO) applies"},
            {"condition": "heritage_register_listed", "description": "Listed on Heritage Register"},
            {"condition": "planning_external_changes", "description": "Planning external modifications"},
            {"condition": "neighbourhood_character_overlay", "description": "NCO applies with strict controls"}
        ],
        "typical_cost": "$2,000 - $10,000 for heritage impact statement",
        "expected_timeline": "2-4 weeks",
        "urgency": ReferralUrgency.HIGH,
        "required_before": "renovation",
        "notes": "Required before council will approve external works"
    },
    SpecialistType.PLUMBER: {
        "name": "Licensed Plumber",
        "triggers": [
            {"condition": "sewer_issues_detected", "description": "Sewer or drainage issues"},
            {"condition": "hot_water_system_age > 10", "description": "Hot water system over 10 years"},
            {"condition": "galvanized_pipes", "description": "Old galvanized pipes (rust/low pressure)"},
            {"condition": "tree_roots_risk", "description": "Large trees near sewer lines"}
        ],
        "typical_cost": "$150 - $400 for inspection, $300+ for CCTV drain camera",
        "expected_timeline": "1-3 business days",
        "urgency": ReferralUrgency.MEDIUM,
        "required_before": "settlement"
    },
    SpecialistType.ROOF_SPECIALIST: {
        "name": "Roof Specialist/Plumber",
        "triggers": [
            {"condition": "roof_age > 25", "description": "Roof over 25 years old"},
            {"condition": "terracotta_tiles_cracked", "description": "Cracked terracotta tiles"},
            {"condition": "metal_roof_rust", "description": "Rust on metal roof"},
            {"condition": "sagging_roof_line", "description": "Visible sag in roof line"},
            {"condition": "water_stains_ceiling", "description": "Water stains on ceiling"}
        ],
        "typical_cost": "$200 - $500 for inspection",
        "expected_timeline": "1-3 business days",
        "urgency": ReferralUrgency.MEDIUM,
        "required_before": "settlement"
    },
    SpecialistType.GEOTECHNICAL_ENGINEER: {
        "name": "Geotechnical Engineer",
        "triggers": [
            {"condition": "slope_steep", "description": "Property on steep slope"},
            {"condition": "landslip_overlay", "description": "Landslip overlay applies"},
            {"condition": "fill_site_suspected", "description": "Possible fill site"},
            {"condition": "major_excavation_planned", "description": "Planning significant excavation"}
        ],
        "typical_cost": "$2,000 - $5,000 for report",
        "expected_timeline": "1-2 weeks",
        "urgency": ReferralUrgency.HIGH,
        "required_before": "settlement"
    },
    SpecialistType.ARBORIST: {
        "name": "Consulting Arborist",
        "triggers": [
            {"condition": "significant_trees_present", "description": "Large trees on or near property"},
            {"condition": "tree_protection_overlay", "description": "Vegetation/tree protection overlay"},
            {"condition": "trees_near_structure", "description": "Trees within 3m of building"},
            {"condition": "tree_removal_planned", "description": "Planning to remove trees"}
        ],
        "typical_cost": "$300 - $800 for assessment",
        "expected_timeline": "3-7 business days",
        "urgency": ReferralUrgency.MEDIUM,
        "required_before": "renovation"
    },
    SpecialistType.POOL_INSPECTOR: {
        "name": "Pool Safety Inspector",
        "triggers": [
            {"condition": "swimming_pool_present", "description": "Property has swimming pool"},
            {"condition": "spa_present", "description": "Property has spa"}
        ],
        "typical_cost": "$150 - $300",
        "expected_timeline": "1-3 business days",
        "urgency": ReferralUrgency.HIGH,
        "required_before": "settlement",
        "notes": "Pool barrier compliance certificate required for sale in Victoria"
    }
}


class SpecialistReferralEngine:
    """
    Determines when to recommend specialist reports based on property findings.

    Analyzes building inspection reports, property characteristics, and
    planned works to trigger appropriate specialist referrals.
    """

    def __init__(self):
        self.trigger_definitions = SPECIALIST_REFERRAL_TRIGGERS

    def analyze(
        self,
        property_data: Dict[str, Any],
        building_inspection: Optional[Dict[str, Any]] = None,
        planned_works: Optional[List[str]] = None,
        is_investment: bool = False
    ) -> ReferralResult:
        """
        Analyze property and determine required specialist referrals.

        Args:
            property_data: Property characteristics including:
                - building_year: Year built
                - property_type: house, apartment, etc.
                - has_pool: bool
                - overlays: List of planning overlays
                - historical_use: Previous land use
            building_inspection: Building inspection findings
            planned_works: List of planned renovations/works
            is_investment: Whether this is an investment purchase

        Returns:
            ReferralResult with categorized specialist referrals
        """
        result = ReferralResult()
        all_referrals = []

        for specialist_type, config in self.trigger_definitions.items():
            referral = self._check_specialist_triggers(
                specialist_type=specialist_type,
                config=config,
                property_data=property_data,
                building_inspection=building_inspection or {},
                planned_works=planned_works or [],
                is_investment=is_investment
            )

            if referral and any(t.triggered for t in referral.triggers):
                all_referrals.append(referral)

        # Categorize referrals by urgency
        for referral in all_referrals:
            if referral.urgency == ReferralUrgency.CRITICAL:
                result.critical_referrals.append(referral)
            elif referral.urgency in [ReferralUrgency.HIGH, ReferralUrgency.MEDIUM]:
                result.high_priority_referrals.append(referral)
            else:
                result.recommended_referrals.append(referral)

        # Calculate estimated total cost
        result.total_estimated_cost = self._estimate_total_cost(all_referrals)

        # Generate summary
        result.summary = self._generate_summary(result)

        return result

    def _check_specialist_triggers(
        self,
        specialist_type: SpecialistType,
        config: Dict[str, Any],
        property_data: Dict[str, Any],
        building_inspection: Dict[str, Any],
        planned_works: List[str],
        is_investment: bool
    ) -> Optional[SpecialistReferral]:
        """Check if any triggers are met for a specialist type."""
        triggers = []
        building_year = property_data.get("building_year", 2000)
        overlays = property_data.get("overlays", [])

        for trigger_def in config["triggers"]:
            condition = trigger_def["condition"]
            triggered = False
            evidence = None

            # Evaluate condition
            triggered, evidence = self._evaluate_condition(
                condition=condition,
                property_data=property_data,
                building_inspection=building_inspection,
                building_year=building_year,
                overlays=overlays,
                planned_works=planned_works,
                is_investment=is_investment
            )

            triggers.append(TriggerCondition(
                condition=condition,
                description=trigger_def["description"],
                triggered=triggered,
                evidence=evidence
            ))

        return SpecialistReferral(
            specialist_type=specialist_type,
            specialist_name=config["name"],
            urgency=config["urgency"],
            triggers=triggers,
            typical_cost=config["typical_cost"],
            expected_timeline=config["expected_timeline"],
            benefit=config.get("benefit"),
            notes=config.get("notes"),
            required_before=config.get("required_before")
        )

    def _evaluate_condition(
        self,
        condition: str,
        property_data: Dict[str, Any],
        building_inspection: Dict[str, Any],
        building_year: int,
        overlays: List[str],
        planned_works: List[str],
        is_investment: bool
    ) -> tuple[bool, Optional[str]]:
        """Evaluate a trigger condition against property data."""
        # Building age conditions
        if "building_age" in condition or "building_year" in condition:
            current_year = 2026
            building_age = current_year - building_year

            if "> 30" in condition and building_age > 30:
                return True, f"Building is {building_age} years old"
            if "< 40" in condition and building_age < 40:
                return True, f"Building is {building_age} years old (eligible for depreciation)"
            if "< 1990" in condition and building_year < 1990:
                return True, f"Built in {building_year} (asbestos era)"

        # Overlay conditions
        if "eao_overlay" in condition:
            if any("EAO" in o or "Environmental Audit" in o for o in overlays):
                return True, "Environmental Audit Overlay applies"

        if "heritage_overlay" in condition:
            if any("HO" in o or "Heritage" in o for o in overlays):
                return True, "Heritage Overlay applies"

        if "landslip_overlay" in condition:
            if any("LSO" in o or "Landslip" in o for o in overlays):
                return True, "Landslip Overlay applies"

        if "tree_protection_overlay" in condition or "neighbourhood_character" in condition:
            if any("VPO" in o or "SLO" in o or "NCO" in o for o in overlays):
                return True, "Vegetation/Character overlay applies"

        # Investment conditions
        if "investment_property" in condition and is_investment:
            return True, "Purchasing as investment property"

        # Planned works conditions
        if "renovation_planned" in condition:
            if planned_works and len(planned_works) > 0:
                return True, f"Planned works: {', '.join(planned_works[:3])}"

        if "planning_external_changes" in condition:
            external_works = ["facade", "extension", "addition", "roof", "external", "deck", "carport"]
            if any(w.lower() in " ".join(planned_works).lower() for w in external_works):
                return True, "External modifications planned"

        # Building inspection findings
        if building_inspection:
            findings = building_inspection.get("findings", [])
            finding_text = " ".join(str(f) for f in findings).lower()

            if "crack" in condition and any("crack" in str(f).lower() for f in findings):
                return True, "Cracking noted in building inspection"

            if "foundation_movement" in condition:
                if any(term in finding_text for term in ["foundation", "settlement", "subsidence", "movement"]):
                    return True, "Foundation issues noted in inspection"

            if "floor_unevenness" in condition:
                if any(term in finding_text for term in ["uneven floor", "floor slope", "floor level"]):
                    return True, "Floor unevenness noted in inspection"

            if "wall_bulging" in condition:
                if any(term in finding_text for term in ["bulg", "bow", "lean"]):
                    return True, "Wall issues noted in inspection"

            if "efflorescence" in condition or "damp" in condition:
                if any(term in finding_text for term in ["damp", "moisture", "efflorescence", "salt"]):
                    return True, "Moisture issues noted in inspection"

            if "switchboard" in condition:
                if any(term in finding_text for term in ["ceramic fuse", "old switchboard", "rewire"]):
                    return True, "Electrical issues noted in inspection"

            if "asbestos" in condition or "fibro" in condition:
                if any(term in finding_text for term in ["asbestos", "fibro", "cement sheet"]):
                    return True, "Possible asbestos materials noted"

            if "roof" in condition:
                if any(term in finding_text for term in ["roof", "tile", "leak", "gutter"]):
                    return True, "Roof issues noted in inspection"

        # Property features
        if "swimming_pool" in condition and property_data.get("has_pool"):
            return True, "Property has swimming pool"

        if "spa_present" in condition and property_data.get("has_spa"):
            return True, "Property has spa"

        # Historical use
        if "historical_industrial_use" in condition:
            historical = property_data.get("historical_use", "").lower()
            if any(term in historical for term in ["industrial", "factory", "warehouse", "workshop"]):
                return True, f"Historical use: {property_data.get('historical_use')}"

        if "former_petrol_station" in condition:
            if "petrol" in property_data.get("historical_use", "").lower():
                return True, "Former petrol station"

        if "contamination_risk_high" in condition:
            if property_data.get("contamination_risk") == "HIGH":
                return True, "High contamination risk identified"

        return False, None

    def _estimate_total_cost(self, referrals: List[SpecialistReferral]) -> str:
        """Estimate total cost of all triggered referrals."""
        total_low = 0
        total_high = 0

        for referral in referrals:
            if any(t.triggered for t in referral.triggers):
                cost_str = referral.typical_cost
                # Parse cost range like "$500 - $1,500"
                try:
                    parts = cost_str.replace("$", "").replace(",", "").split("-")
                    if len(parts) >= 2:
                        low = int(parts[0].strip().split()[0])
                        high = int(parts[1].strip().split()[0])
                        total_low += low
                        total_high += high
                    elif len(parts) == 1:
                        val = int(parts[0].strip().split()[0])
                        total_low += val
                        total_high += val
                except (ValueError, IndexError):
                    pass

        if total_low == 0 and total_high == 0:
            return "$0"
        return f"${total_low:,} - ${total_high:,}"

    def _generate_summary(self, result: ReferralResult) -> str:
        """Generate a summary of referral recommendations."""
        total = len(result.critical_referrals) + len(result.high_priority_referrals) + len(result.recommended_referrals)

        if total == 0:
            return "No specialist referrals triggered. Standard building and pest inspection should be sufficient."

        parts = []
        if result.critical_referrals:
            names = [r.specialist_name for r in result.critical_referrals]
            parts.append(f"CRITICAL: {', '.join(names)}")

        if result.high_priority_referrals:
            names = [r.specialist_name for r in result.high_priority_referrals]
            parts.append(f"High Priority: {', '.join(names)}")

        if result.recommended_referrals:
            names = [r.specialist_name for r in result.recommended_referrals]
            parts.append(f"Recommended: {', '.join(names)}")

        summary = ". ".join(parts)
        summary += f". Estimated total cost: {result.total_estimated_cost}"

        return summary

    def get_referrals_for_condition(
        self,
        condition_type: str
    ) -> List[Dict[str, Any]]:
        """Get all specialists relevant to a specific condition type."""
        relevant = []

        condition_mapping = {
            "structural": [SpecialistType.STRUCTURAL_ENGINEER, SpecialistType.GEOTECHNICAL_ENGINEER],
            "moisture": [SpecialistType.RISING_DAMP_SPECIALIST, SpecialistType.PLUMBER],
            "electrical": [SpecialistType.ELECTRICAL_INSPECTOR],
            "asbestos": [SpecialistType.ASBESTOS_ASSESSOR],
            "environmental": [SpecialistType.ENVIRONMENTAL_AUDITOR],
            "heritage": [SpecialistType.HERITAGE_ARCHITECT],
            "roof": [SpecialistType.ROOF_SPECIALIST],
            "trees": [SpecialistType.ARBORIST],
            "pool": [SpecialistType.POOL_INSPECTOR],
            "investment": [SpecialistType.QUANTITY_SURVEYOR]
        }

        specialist_types = condition_mapping.get(condition_type.lower(), [])

        for spec_type in specialist_types:
            if spec_type in self.trigger_definitions:
                config = self.trigger_definitions[spec_type]
                relevant.append({
                    "specialist_type": spec_type.value,
                    "name": config["name"],
                    "typical_cost": config["typical_cost"],
                    "expected_timeline": config["expected_timeline"]
                })

        return relevant


# Convenience function
def get_specialist_referrals(
    building_year: int,
    property_type: str = "house",
    overlays: Optional[List[str]] = None,
    building_inspection_findings: Optional[List[str]] = None,
    planned_works: Optional[List[str]] = None,
    has_pool: bool = False,
    is_investment: bool = False
) -> Dict[str, Any]:
    """
    Quick specialist referral check.

    Args:
        building_year: Year property was built
        property_type: Type of property
        overlays: List of planning overlays
        building_inspection_findings: List of issues from building inspection
        planned_works: List of planned works
        has_pool: Whether property has pool
        is_investment: Whether investment purchase

    Returns:
        Dict with specialist referrals
    """
    engine = SpecialistReferralEngine()

    property_data = {
        "building_year": building_year,
        "property_type": property_type,
        "overlays": overlays or [],
        "has_pool": has_pool
    }

    building_inspection = {
        "findings": building_inspection_findings or []
    }

    result = engine.analyze(
        property_data=property_data,
        building_inspection=building_inspection,
        planned_works=planned_works,
        is_investment=is_investment
    )

    return result.to_dict()
