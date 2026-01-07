"""
Planning & Zoning Analysis Module.

Comprehensive analysis of:
- Zone-specific development limits
- Planning overlay impacts
- Building permit history cross-reference
- Development potential scoring
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ============================================================================
# VICTORIAN RESIDENTIAL ZONES
# ============================================================================

VICTORIAN_RESIDENTIAL_ZONES = {
    "NRZ": {
        "name": "Neighbourhood Residential Zone",
        "mandatory_height": "9m / 2 storeys",
        "mandatory_height_note": "MANDATORY - cannot be varied",
        "purpose": "Protect neighbourhood character, limit growth",
        "garden_area": "Minimum 35% of lot",
        "typical_density": "1-2 dwellings per lot",
        "subdivision_minimum": "Varies by schedule - check",
        "development_potential": "LIMITED",
        "granny_flat": "May be possible subject to schedule",
        "rooming_house": "Usually NOT permitted",
        "dual_occupancy": "Limited by schedule",
        "risk_score": 70
    },
    "GRZ": {
        "name": "General Residential Zone",
        "mandatory_height": "11m / 3 storeys",
        "mandatory_height_note": "MANDATORY - cannot be varied",
        "purpose": "Encourage moderate housing growth",
        "garden_area": "Minimum 35% of lot",
        "typical_density": "2-4 dwellings per lot",
        "development_potential": "MODERATE",
        "granny_flat": "Usually permitted",
        "rooming_house": "Permit required, usually achievable",
        "dual_occupancy": "Generally permitted",
        "risk_score": 40
    },
    "RGZ": {
        "name": "Residential Growth Zone",
        "mandatory_height": "13.5m / 4 storeys",
        "mandatory_height_note": "Default unless schedule specifies otherwise",
        "purpose": "Substantial housing change in appropriate locations",
        "garden_area": "Varies by schedule",
        "typical_density": "4+ dwellings per lot",
        "development_potential": "HIGH",
        "granny_flat": "Usually permitted",
        "rooming_house": "Usually permitted",
        "dual_occupancy": "Generally permitted",
        "risk_score": 20
    },
    "MUZ": {
        "name": "Mixed Use Zone",
        "mandatory_height": "None specified - discretionary",
        "purpose": "Mix of residential and commercial",
        "development_potential": "HIGH",
        "commercial_use": "Permitted",
        "risk_score": 25
    },
    "LDRZ": {
        "name": "Low Density Residential Zone",
        "minimum_lot_size": "Usually 2,000sqm - 4,000sqm",
        "purpose": "Rural-residential interface",
        "development_potential": "VERY LIMITED",
        "subdivision": "Rarely permitted",
        "sewerage": "Often unsewered - requires septic",
        "risk_score": 80
    },
    "TZ": {
        "name": "Township Zone",
        "purpose": "Rural townships",
        "development_potential": "LIMITED",
        "services": "May be limited",
        "risk_score": 60
    },
    "RZ": {
        "name": "Rural Zone",
        "purpose": "Agricultural and rural use",
        "development_potential": "VERY LIMITED",
        "residential": "Usually prohibited or conditional",
        "risk_score": 90
    }
}


# ============================================================================
# PLANNING OVERLAYS
# ============================================================================

PLANNING_OVERLAYS = {
    "HO": {
        "name": "Heritage Overlay",
        "impact": "Permit required for external changes, demolition restricted",
        "cost_impact": "10-30% higher construction costs",
        "approval_time": "2-6 months additional for heritage permit",
        "risk_score": 30,
        "affects_value": "Can increase value in prestige areas"
    },
    "DDO": {
        "name": "Design and Development Overlay",
        "impact": "Specific built form controls - height, setbacks, materials",
        "check": "Must read schedule for site-specific controls",
        "risk_score": 20,
        "common_requirements": ["height limits", "setback requirements", "materials"]
    },
    "SBO": {
        "name": "Special Building Overlay",
        "impact": "Overland flow path - flood risk from stormwater",
        "requires": "Floor levels above flood level",
        "insurance_impact": "May increase premiums",
        "risk_score": 35,
        "development_impact": "May limit basement/below-ground areas"
    },
    "LSIO": {
        "name": "Land Subject to Inundation Overlay",
        "impact": "Riverine flood risk - building restrictions apply",
        "requires": "Floor levels 600mm above flood level",
        "insurance_impact": "Significant premium increase or exclusion",
        "risk_score": 50,
        "development_impact": "Significant building restrictions"
    },
    "BMO": {
        "name": "Bushfire Management Overlay",
        "impact": "BAL assessment required, construction standards",
        "BAL_ratings": ["BAL-LOW", "BAL-12.5", "BAL-19", "BAL-29", "BAL-40", "BAL-FZ"],
        "cost_impact": {
            "BAL-12.5": "5-10% construction cost increase",
            "BAL-19": "10-20% construction cost increase",
            "BAL-29": "20-30% construction cost increase",
            "BAL-40": "30-50% construction cost increase",
            "BAL-FZ": "Very difficult to build, specialist design required"
        },
        "risk_score": 45,
        "insurance_impact": "Higher premiums, some insurers won't cover BAL-40+"
    },
    "EAO": {
        "name": "Environmental Audit Overlay",
        "impact": "Contamination risk - audit required before sensitive use",
        "sensitive_uses": ["residential", "childcare", "school"],
        "cost": "$20,000 - $100,000+ for audit",
        "risk_score": 60,
        "critical": "MUST check before purchasing for residential use"
    },
    "NCO": {
        "name": "Neighbourhood Character Overlay",
        "impact": "Additional design controls for character",
        "check": "Schedule specifies requirements",
        "risk_score": 15,
        "typical_controls": ["front setbacks", "building height", "landscaping"]
    },
    "VPO": {
        "name": "Vegetation Protection Overlay",
        "impact": "Permit required to remove vegetation",
        "cost_impact": "May limit buildable area",
        "risk_score": 20,
        "affects": ["tree removal", "site clearing"]
    },
    "PAO": {
        "name": "Public Acquisition Overlay",
        "impact": "Land may be compulsorily acquired for public purpose",
        "risk_score": 90,
        "risk_level": "CRITICAL - check acquisition timeline"
    },
    "SLO": {
        "name": "Significant Landscape Overlay",
        "impact": "Controls to protect landscape values",
        "risk_score": 25,
        "affects": ["building design", "vegetation", "colours"]
    },
    "ESO": {
        "name": "Environmental Significance Overlay",
        "impact": "Protect areas of environmental significance",
        "risk_score": 30,
        "affects": ["native vegetation", "waterways", "wildlife"]
    },
    "DPO": {
        "name": "Development Plan Overlay",
        "impact": "Development must accord with approved plan",
        "check": "Check if development plan approved for site",
        "risk_score": 25
    }
}


@dataclass
class ZoneAnalysis:
    """Analysis of property zoning."""
    zone_code: str
    zone_name: str
    zone_purpose: str
    development_potential: str
    mandatory_height: Optional[str] = None
    garden_area: Optional[str] = None
    typical_density: Optional[str] = None
    subdivision_rules: str = ""
    permitted_uses: List[str] = field(default_factory=list)
    prohibited_uses: List[str] = field(default_factory=list)
    risk_score: int = 0
    schedule_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_code": self.zone_code,
            "zone_name": self.zone_name,
            "purpose": self.zone_purpose,
            "development_potential": self.development_potential,
            "mandatory_height": self.mandatory_height,
            "garden_area": self.garden_area,
            "typical_density": self.typical_density,
            "subdivision_rules": self.subdivision_rules,
            "permitted_uses": self.permitted_uses,
            "prohibited_uses": self.prohibited_uses,
            "risk_score": self.risk_score,
            "schedule_notes": self.schedule_notes
        }


@dataclass
class OverlayAnalysis:
    """Analysis of a planning overlay."""
    overlay_code: str
    overlay_name: str
    impact: str
    cost_impact: Optional[str] = None
    approval_time: Optional[str] = None
    insurance_impact: Optional[str] = None
    risk_score: int = 0
    requirements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.overlay_code,
            "name": self.overlay_name,
            "impact": self.impact,
            "cost_impact": self.cost_impact,
            "approval_time": self.approval_time,
            "insurance_impact": self.insurance_impact,
            "risk_score": self.risk_score,
            "requirements": self.requirements,
            "recommendations": self.recommendations
        }


@dataclass
class DevelopmentPotentialResult:
    """Complete development potential analysis."""
    zone: ZoneAnalysis
    overlays: List[OverlayAnalysis] = field(default_factory=list)
    development_score: int = 0  # 0-100, higher = more potential
    development_rating: str = ""  # HIGH, MODERATE, LIMITED, BLOCKED
    restrictions: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    estimated_additional_cost_percent: float = 0.0
    estimated_approval_time_months: int = 0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone": self.zone.to_dict(),
            "overlays": [o.to_dict() for o in self.overlays],
            "development_score": self.development_score,
            "development_rating": self.development_rating,
            "restrictions": self.restrictions,
            "opportunities": self.opportunities,
            "estimated_additional_cost_percent": self.estimated_additional_cost_percent,
            "estimated_approval_time_months": self.estimated_approval_time_months,
            "recommendations": self.recommendations
        }


class ZoneDevelopmentAnalyzer:
    """
    Analyzes zone-specific development limits and overlay impacts.
    """

    def __init__(self):
        self.zones = VICTORIAN_RESIDENTIAL_ZONES
        self.overlays_config = PLANNING_OVERLAYS

    def analyze(
        self,
        zone_code: str,
        overlay_codes: List[str],
        intended_use: str = "owner_occupier",
        land_size_sqm: Optional[float] = None
    ) -> DevelopmentPotentialResult:
        """
        Analyze development potential.

        Args:
            zone_code: Zone code (e.g., 'GRZ', 'NRZ')
            overlay_codes: List of overlay codes (e.g., ['HO', 'DDO'])
            intended_use: 'owner_occupier', 'investor', 'developer', 'subdivider'
            land_size_sqm: Land size in square meters

        Returns:
            DevelopmentPotentialResult with full analysis
        """
        result = DevelopmentPotentialResult(
            zone=self._analyze_zone(zone_code, intended_use),
            overlays=[self._analyze_overlay(code) for code in overlay_codes]
        )

        # Calculate composite development score
        result.development_score = self._calculate_development_score(result, intended_use)
        result.development_rating = self._score_to_rating(result.development_score)

        # Identify restrictions
        result.restrictions = self._identify_restrictions(result, intended_use, land_size_sqm)

        # Identify opportunities
        result.opportunities = self._identify_opportunities(result, intended_use, land_size_sqm)

        # Estimate additional costs from overlays
        result.estimated_additional_cost_percent = self._estimate_additional_costs(result.overlays)

        # Estimate approval timeline
        result.estimated_approval_time_months = self._estimate_approval_time(result.overlays)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, intended_use)

        return result

    def _analyze_zone(self, zone_code: str, intended_use: str) -> ZoneAnalysis:
        """Analyze the property's zone."""
        # Normalize zone code (handle variations like GRZ1, GRZ2, etc.)
        base_zone = ''.join(c for c in zone_code.upper() if c.isalpha())

        config = self.zones.get(base_zone, {})

        analysis = ZoneAnalysis(
            zone_code=zone_code,
            zone_name=config.get("name", f"Unknown Zone ({zone_code})"),
            zone_purpose=config.get("purpose", "Unknown"),
            development_potential=config.get("development_potential", "UNKNOWN"),
            mandatory_height=config.get("mandatory_height"),
            garden_area=config.get("garden_area"),
            typical_density=config.get("typical_density"),
            risk_score=config.get("risk_score", 50)
        )

        # Determine permitted/prohibited uses based on intended use
        if intended_use == "subdivider":
            if base_zone == "NRZ":
                analysis.prohibited_uses.append("Subdivision may be prohibited or heavily restricted")
            elif base_zone == "LDRZ":
                analysis.prohibited_uses.append("Minimum lot sizes typically 2,000sqm+")

        if intended_use == "developer":
            if config.get("rooming_house") == "Usually NOT permitted":
                analysis.prohibited_uses.append("Rooming house not permitted")
            else:
                analysis.permitted_uses.append(config.get("rooming_house", "Unknown"))

        return analysis

    def _analyze_overlay(self, overlay_code: str) -> OverlayAnalysis:
        """Analyze a planning overlay."""
        config = self.overlays_config.get(overlay_code.upper(), {})

        analysis = OverlayAnalysis(
            overlay_code=overlay_code,
            overlay_name=config.get("name", f"Unknown Overlay ({overlay_code})"),
            impact=config.get("impact", "Unknown impact"),
            cost_impact=config.get("cost_impact"),
            approval_time=config.get("approval_time"),
            insurance_impact=config.get("insurance_impact"),
            risk_score=config.get("risk_score", 30)
        )

        # Add requirements
        if "requires" in config:
            analysis.requirements.append(config["requires"])

        if "check" in config:
            analysis.recommendations.append(f"MUST CHECK: {config['check']}")

        if config.get("critical"):
            analysis.recommendations.append(f"CRITICAL: {config['critical']}")

        return analysis

    def _calculate_development_score(
        self,
        result: DevelopmentPotentialResult,
        intended_use: str
    ) -> int:
        """Calculate composite development potential score."""
        # Base score from zone (inverted risk score)
        base_score = 100 - result.zone.risk_score

        # Reduce for each overlay
        overlay_reduction = sum(o.risk_score * 0.3 for o in result.overlays)
        base_score -= overlay_reduction

        # Check for blocking overlays
        blocking_codes = ["PAO", "EAO"]
        if any(o.overlay_code.upper() in blocking_codes for o in result.overlays):
            base_score = min(base_score, 20)

        return max(0, min(100, int(base_score)))

    def _score_to_rating(self, score: int) -> str:
        """Convert score to rating."""
        if score >= 70:
            return "HIGH"
        elif score >= 50:
            return "MODERATE"
        elif score >= 30:
            return "LIMITED"
        else:
            return "BLOCKED"

    def _identify_restrictions(
        self,
        result: DevelopmentPotentialResult,
        intended_use: str,
        land_size_sqm: Optional[float]
    ) -> List[str]:
        """Identify development restrictions."""
        restrictions = []

        # Zone restrictions
        if result.zone.mandatory_height:
            restrictions.append(f"Maximum height: {result.zone.mandatory_height}")

        if result.zone.garden_area:
            restrictions.append(f"Minimum garden area: {result.zone.garden_area}")

        # Overlay restrictions
        for overlay in result.overlays:
            if overlay.overlay_code.upper() == "HO":
                restrictions.append("Heritage: Permit required for external changes")
            elif overlay.overlay_code.upper() == "BMO":
                restrictions.append("Bushfire: BAL assessment required, increased construction costs")
            elif overlay.overlay_code.upper() in ["SBO", "LSIO"]:
                restrictions.append(f"{overlay.overlay_name}: Floor level requirements apply")
            elif overlay.overlay_code.upper() == "PAO":
                restrictions.append("PUBLIC ACQUISITION: Land may be compulsorily acquired")
            elif overlay.overlay_code.upper() == "EAO":
                restrictions.append("CONTAMINATION: Environmental audit required before residential use")

        # Land size restrictions
        if land_size_sqm and land_size_sqm < 300:
            restrictions.append("Small lot - may not meet subdivision minimum")

        return restrictions

    def _identify_opportunities(
        self,
        result: DevelopmentPotentialResult,
        intended_use: str,
        land_size_sqm: Optional[float]
    ) -> List[str]:
        """Identify development opportunities."""
        opportunities = []

        zone_potential = result.zone.development_potential

        if zone_potential in ["HIGH", "MODERATE"]:
            opportunities.append(f"{zone_potential} development potential")

        if result.zone.zone_code.upper().startswith("RGZ"):
            opportunities.append("Residential Growth Zone - multi-unit development supported")

        if result.zone.zone_code.upper().startswith("MUZ"):
            opportunities.append("Mixed Use Zone - commercial ground floor option")

        if land_size_sqm and land_size_sqm > 600:
            opportunities.append("Lot size may support subdivision (subject to zone rules)")

        if not any(o.overlay_code.upper() == "HO" for o in result.overlays):
            opportunities.append("No heritage overlay - greater design flexibility")

        return opportunities

    def _estimate_additional_costs(self, overlays: List[OverlayAnalysis]) -> float:
        """Estimate additional construction costs from overlays."""
        cost_increase = 0.0

        for overlay in overlays:
            if overlay.overlay_code.upper() == "HO":
                cost_increase += 20  # 20% increase
            elif overlay.overlay_code.upper() == "BMO":
                cost_increase += 25  # Average BAL increase
            elif overlay.overlay_code.upper() in ["SBO", "LSIO"]:
                cost_increase += 15
            elif overlay.overlay_code.upper() == "NCO":
                cost_increase += 5

        return cost_increase

    def _estimate_approval_time(self, overlays: List[OverlayAnalysis]) -> int:
        """Estimate approval timeline in months."""
        base_time = 3  # Base planning permit time

        for overlay in overlays:
            if overlay.overlay_code.upper() == "HO":
                base_time += 4  # Heritage adds time
            elif overlay.overlay_code.upper() == "EAO":
                base_time += 6  # Environmental audit
            elif overlay.overlay_code.upper() in ["SBO", "LSIO"]:
                base_time += 2  # Flood assessment
            elif overlay.overlay_code.upper() == "BMO":
                base_time += 2  # BAL assessment

        return base_time

    def _generate_recommendations(
        self,
        result: DevelopmentPotentialResult,
        intended_use: str
    ) -> List[str]:
        """Generate planning recommendations."""
        recommendations = []

        if result.development_rating == "BLOCKED":
            recommendations.append(
                "CRITICAL: Development potential severely limited. "
                "Reconsider if intending development."
            )

        if any(o.overlay_code.upper() == "PAO" for o in result.overlays):
            recommendations.append(
                "PUBLIC ACQUISITION OVERLAY: Contact council to confirm "
                "acquisition timeline and compensation process."
            )

        if any(o.overlay_code.upper() == "EAO" for o in result.overlays):
            recommendations.append(
                "ENVIRONMENTAL AUDIT REQUIRED before residential use. "
                "Budget $20,000-$100,000+ for audit costs."
            )

        if any(o.overlay_code.upper() == "HO" for o in result.overlays):
            recommendations.append(
                "Heritage Overlay: Engage heritage architect early. "
                "Allow 3-6 months additional for heritage permit."
            )

        if result.estimated_additional_cost_percent > 20:
            recommendations.append(
                f"Planning overlays may increase construction costs by "
                f"approximately {result.estimated_additional_cost_percent:.0f}%"
            )

        if not recommendations:
            recommendations.append(
                "Planning constraints appear manageable. "
                "Consult town planner for specific development requirements."
            )

        return recommendations


# ============================================================================
# BUILDING PERMIT HISTORY ANALYZER
# ============================================================================

@dataclass
class BuildingPermitCheck:
    """Analysis of a building permit."""
    permit_number: str
    description: str
    issue_date: Optional[str] = None
    final_inspection: bool = False
    occupancy_permit: bool = False
    status: str = "UNKNOWN"  # COMPLETE, INCOMPLETE, MISSING
    risk_level: RiskLevel = RiskLevel.INFO
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permit_number": self.permit_number,
            "description": self.description,
            "issue_date": self.issue_date,
            "final_inspection": self.final_inspection,
            "occupancy_permit": self.occupancy_permit,
            "status": self.status,
            "risk_level": self.risk_level.value,
            "notes": self.notes
        }


@dataclass
class PotentialIllegalWork:
    """Detection of potential illegal works."""
    structure_type: str
    detected_from: str  # 'inspection', 'photos', 'aerial'
    permit_found: bool = False
    final_inspection: bool = False
    estimated_age: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.HIGH
    consequence: str = ""
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure": self.structure_type,
            "detected_from": self.detected_from,
            "permit_found": self.permit_found,
            "final_inspection": self.final_inspection,
            "estimated_age": self.estimated_age,
            "risk_level": self.risk_level.value,
            "consequence": self.consequence,
            "recommendation": self.recommendation
        }


@dataclass
class BuildingPermitAnalysisResult:
    """Complete building permit analysis."""
    permits_found: List[BuildingPermitCheck] = field(default_factory=list)
    permits_without_final_inspection: List[str] = field(default_factory=list)
    potential_illegal_works: List[PotentialIllegalWork] = field(default_factory=list)
    risk_score: int = 0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permits_found": [p.to_dict() for p in self.permits_found],
            "permits_count": len(self.permits_found),
            "permits_without_final_inspection": self.permits_without_final_inspection,
            "potential_illegal_works": [w.to_dict() for w in self.potential_illegal_works],
            "illegal_works_count": len(self.potential_illegal_works),
            "risk_score": self.risk_score,
            "recommendations": self.recommendations
        }


# Structures that typically require permits
PERMIT_REQUIRED_STRUCTURES = {
    "extension": {
        "permit_required": True,
        "final_inspection_required": True,
        "consequence": "May need to be demolished or retrospective approval sought"
    },
    "deck": {
        "permit_required": "If over certain size/height",
        "final_inspection_required": True,
        "consequence": "Safety risk, insurance implications"
    },
    "pergola": {
        "permit_required": "If attached to dwelling or enclosed",
        "final_inspection_required": True
    },
    "carport": {
        "permit_required": True,
        "final_inspection_required": True
    },
    "garage": {
        "permit_required": True,
        "final_inspection_required": True
    },
    "swimming_pool": {
        "permit_required": True,
        "final_inspection_required": True,
        "additional": "Pool fence compliance required"
    },
    "spa": {
        "permit_required": True,
        "final_inspection_required": True,
        "additional": "Pool fence compliance required"
    },
    "shed_over_10sqm": {
        "permit_required": True,
        "final_inspection_required": True
    },
    "granny_flat": {
        "permit_required": True,
        "final_inspection_required": True,
        "consequence": "Major compliance issue if unpermitted"
    },
    "second_storey": {
        "permit_required": True,
        "final_inspection_required": True,
        "consequence": "Structural safety concern"
    },
    "basement": {
        "permit_required": True,
        "final_inspection_required": True
    },
    "retaining_wall_over_1m": {
        "permit_required": True,
        "final_inspection_required": True,
        "consequence": "Structural and safety risk"
    },
    "bathroom_renovation": {
        "permit_required": "Plumbing permit required",
        "final_inspection_required": "Plumbing compliance"
    },
    "kitchen_renovation": {
        "permit_required": "If structural changes",
        "final_inspection_required": True
    }
}


class BuildingPermitAnalyzer:
    """
    Cross-references building permits from Section 32 against:
    1. Physical inspection findings
    2. Aerial imagery history
    3. Real estate listing photos

    Detects potential illegal works.
    """

    def __init__(self):
        self.permit_requirements = PERMIT_REQUIRED_STRUCTURES

    def analyze(
        self,
        section_32_permits: List[Dict[str, Any]],
        detected_structures: List[Dict[str, Any]],
        building_report_findings: Optional[Dict[str, Any]] = None
    ) -> BuildingPermitAnalysisResult:
        """
        Analyze building permits and detect potential illegal works.

        Args:
            section_32_permits: Permits disclosed in Section 32
            detected_structures: Structures detected from photos/inspection
            building_report_findings: Findings from building inspection report

        Returns:
            BuildingPermitAnalysisResult with analysis
        """
        result = BuildingPermitAnalysisResult()

        # Analyze disclosed permits
        for permit in section_32_permits:
            check = self._analyze_permit(permit)
            result.permits_found.append(check)

            if not check.final_inspection:
                result.permits_without_final_inspection.append(
                    f"{check.permit_number}: {check.description}"
                )

        # Cross-reference detected structures
        for structure in detected_structures:
            structure_type = structure.get("type", "").lower().replace(" ", "_")

            # Check if this structure type requires permit
            if structure_type in self.permit_requirements:
                # Look for matching permit
                matching_permit = self._find_matching_permit(structure, section_32_permits)

                if not matching_permit:
                    # No permit found - potential illegal work
                    illegal = PotentialIllegalWork(
                        structure_type=structure.get("type", "Unknown"),
                        detected_from=structure.get("source", "inspection"),
                        permit_found=False,
                        estimated_age=structure.get("estimated_age"),
                        risk_level=RiskLevel.HIGH,
                        consequence=(
                            "Council may issue building notice. "
                            "Insurance may not cover. "
                            "Disclosure required on resale."
                        ),
                        recommendation="Request council building permit records"
                    )
                    result.potential_illegal_works.append(illegal)

                elif not matching_permit.get("final_inspection"):
                    # Permit found but no final inspection
                    illegal = PotentialIllegalWork(
                        structure_type=structure.get("type", "Unknown"),
                        detected_from=structure.get("source", "inspection"),
                        permit_found=True,
                        final_inspection=False,
                        risk_level=RiskLevel.MEDIUM,
                        consequence=(
                            "Works may not comply with permit. "
                            "Occupancy certificate may be required."
                        ),
                        recommendation="Request Certificate of Final Inspection from council"
                    )
                    result.potential_illegal_works.append(illegal)

        # Calculate risk score
        result.risk_score = self._calculate_risk_score(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _analyze_permit(self, permit: Dict[str, Any]) -> BuildingPermitCheck:
        """Analyze a single building permit."""
        return BuildingPermitCheck(
            permit_number=permit.get("permit_number", "Unknown"),
            description=permit.get("description", ""),
            issue_date=permit.get("issue_date"),
            final_inspection=permit.get("final_inspection", False),
            occupancy_permit=permit.get("occupancy_permit", False),
            status="COMPLETE" if permit.get("final_inspection") else "INCOMPLETE"
        )

    def _find_matching_permit(
        self,
        structure: Dict[str, Any],
        permits: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find permit matching a detected structure."""
        structure_type = structure.get("type", "").lower()
        structure_age = structure.get("estimated_age")

        for permit in permits:
            permit_desc = permit.get("description", "").lower()

            # Simple matching - in production would be more sophisticated
            if structure_type in permit_desc or permit_desc in structure_type:
                return permit

            # Check common variations
            variations = {
                "extension": ["addition", "alterations", "reno"],
                "carport": ["car port", "car shed"],
                "granny_flat": ["dependent person", "secondary dwelling"],
            }

            for key, alts in variations.items():
                if structure_type == key and any(alt in permit_desc for alt in alts):
                    return permit

        return None

    def _calculate_risk_score(self, result: BuildingPermitAnalysisResult) -> int:
        """Calculate overall risk score."""
        score = 0

        # Each potential illegal work adds significant risk
        score += len(result.potential_illegal_works) * 20

        # Permits without final inspection add moderate risk
        score += len(result.permits_without_final_inspection) * 10

        return min(100, score)

    def _generate_recommendations(
        self,
        result: BuildingPermitAnalysisResult
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if result.potential_illegal_works:
            recommendations.append(
                f"CRITICAL: {len(result.potential_illegal_works)} potential illegal work(s) detected. "
                "Request building permit records from council before exchange."
            )

            for work in result.potential_illegal_works:
                recommendations.append(
                    f"  - {work.structure_type}: {work.recommendation}"
                )

        if result.permits_without_final_inspection:
            recommendations.append(
                f"{len(result.permits_without_final_inspection)} permit(s) missing Certificate of Final Inspection. "
                "Request from council or building surveyor."
            )

        if result.risk_score > 30:
            recommendations.append(
                "Consider making contract subject to satisfactory building permit records"
            )

        if not recommendations:
            recommendations.append(
                "Building permit records appear in order. "
                "Verify with council for complete history."
            )

        return recommendations


# Convenience functions
def analyze_planning(
    zone_code: str,
    overlays: List[str],
    intended_use: str = "owner_occupier"
) -> Dict[str, Any]:
    """
    Quick planning analysis.

    Returns development potential assessment.
    """
    analyzer = ZoneDevelopmentAnalyzer()
    result = analyzer.analyze(
        zone_code=zone_code,
        overlay_codes=overlays,
        intended_use=intended_use
    )
    return result.to_dict()


def check_building_permits(
    permits: List[Dict[str, Any]],
    structures: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Quick building permit cross-reference.

    Returns potential illegal works assessment.
    """
    analyzer = BuildingPermitAnalyzer()
    result = analyzer.analyze(
        section_32_permits=permits,
        detected_structures=structures
    )
    return result.to_dict()
