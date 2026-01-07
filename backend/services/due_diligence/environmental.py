"""
Environmental & Contamination Risk Assessment Module.

Assesses contamination risk using:
- Victoria Unearthed data integration
- Historical land use analysis
- EPA site registers
- Environmental Audit Overlay detection
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


# High-risk historical land uses that indicate potential contamination
HIGH_RISK_HISTORICAL_USES = {
    "petrol_station": {
        "keywords": ["petrol station", "service station", "fuel depot", "servo", "fuel storage"],
        "contaminants": ["petroleum hydrocarbons", "BTEX", "heavy metals"],
        "risk_level": RiskLevel.HIGH,
        "typical_cleanup_cost": "$100,000 - $500,000+"
    },
    "dry_cleaner": {
        "keywords": ["dry cleaner", "laundry", "dry cleaning"],
        "contaminants": ["chlorinated solvents", "PCE", "TCE"],
        "risk_level": RiskLevel.HIGH,
        "typical_cleanup_cost": "$50,000 - $300,000"
    },
    "metal_works": {
        "keywords": ["metal plating", "electroplating", "metal finishing", "chrome plating"],
        "contaminants": ["heavy metals", "chromium", "nickel", "zinc"],
        "risk_level": RiskLevel.HIGH,
        "typical_cleanup_cost": "$100,000 - $1,000,000+"
    },
    "tannery": {
        "keywords": ["tannery", "leather works", "leather factory"],
        "contaminants": ["chromium", "heavy metals", "organic compounds"],
        "risk_level": RiskLevel.HIGH,
        "typical_cleanup_cost": "$200,000 - $1,000,000+"
    },
    "printing": {
        "keywords": ["printing works", "printer", "print shop"],
        "contaminants": ["solvents", "heavy metals", "inks"],
        "risk_level": RiskLevel.MEDIUM,
        "typical_cleanup_cost": "$20,000 - $100,000"
    },
    "chemical_manufacturing": {
        "keywords": ["chemical manufacturer", "paint manufacturer", "chemical factory"],
        "contaminants": ["various chemicals", "solvents", "heavy metals"],
        "risk_level": RiskLevel.CRITICAL,
        "typical_cleanup_cost": "$500,000 - $5,000,000+"
    },
    "gasworks": {
        "keywords": ["gasworks", "gas works", "coal gas"],
        "contaminants": ["PAHs", "coal tar", "cyanide", "heavy metals"],
        "risk_level": RiskLevel.CRITICAL,
        "typical_cleanup_cost": "$1,000,000 - $10,000,000+"
    },
    "landfill": {
        "keywords": ["landfill", "tip", "rubbish tip", "waste disposal"],
        "contaminants": ["methane", "leachate", "various contaminants"],
        "risk_level": RiskLevel.CRITICAL,
        "typical_cleanup_cost": "$500,000 - $5,000,000+"
    },
    "abattoir": {
        "keywords": ["abattoir", "meatworks", "slaughterhouse"],
        "contaminants": ["organic matter", "pathogens", "nutrients"],
        "risk_level": RiskLevel.MEDIUM,
        "typical_cleanup_cost": "$50,000 - $200,000"
    },
    "timber_treatment": {
        "keywords": ["timber treatment", "sawmill", "wood preservation"],
        "contaminants": ["CCA", "arsenic", "chromium", "copper"],
        "risk_level": RiskLevel.HIGH,
        "typical_cleanup_cost": "$100,000 - $500,000"
    },
    "factory": {
        "keywords": ["factory", "manufacturing", "industrial"],
        "contaminants": ["various - depends on industry"],
        "risk_level": RiskLevel.MEDIUM,
        "typical_cleanup_cost": "$50,000 - $500,000"
    },
    "automotive": {
        "keywords": ["mechanic", "panel beater", "auto repair", "car yard"],
        "contaminants": ["petroleum hydrocarbons", "heavy metals", "solvents"],
        "risk_level": RiskLevel.MEDIUM,
        "typical_cleanup_cost": "$30,000 - $150,000"
    }
}


@dataclass
class HistoricalUse:
    """A historical land use detected."""
    business_type: str
    year: Optional[str] = None
    address: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    contaminants: List[str] = field(default_factory=list)
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "business_type": self.business_type,
            "year": self.year,
            "address": self.address,
            "risk_level": self.risk_level.value,
            "contaminants": self.contaminants,
            "source": self.source
        }


@dataclass
class ContaminationAssessmentResult:
    """Complete contamination assessment result."""
    contamination_risk: str = "UNKNOWN"  # LOW, MEDIUM, HIGH, CRITICAL
    priority_sites_register: Optional[Dict[str, Any]] = None
    environmental_audits: List[Dict[str, Any]] = field(default_factory=list)
    epa_licensed_sites: List[Dict[str, Any]] = field(default_factory=list)
    historical_uses: List[HistoricalUse] = field(default_factory=list)
    eao_overlay: bool = False
    estimated_audit_cost: Optional[str] = None
    estimated_cleanup_cost: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contamination_risk": self.contamination_risk,
            "priority_sites_register": self.priority_sites_register,
            "environmental_audits": self.environmental_audits,
            "epa_licensed_sites": self.epa_licensed_sites,
            "historical_uses": [h.to_dict() for h in self.historical_uses],
            "eao_overlay": self.eao_overlay,
            "estimated_audit_cost": self.estimated_audit_cost,
            "estimated_cleanup_cost": self.estimated_cleanup_cost,
            "recommendations": self.recommendations
        }


class ContaminationAssessor:
    """
    Assesses contamination risk using Victoria Unearthed data and historical records.

    Victoria Unearthed consolidates:
    - Priority Sites Register (EPA notices)
    - EPA licensed sites
    - Environmental audits
    - Historical business listings (Sands & McDougall 1896-1974)
    """

    def __init__(self):
        self.high_risk_uses = HIGH_RISK_HISTORICAL_USES

    async def assess(
        self,
        address: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        planning_info: Optional[Dict[str, Any]] = None,
        section_32_text: Optional[str] = None
    ) -> ContaminationAssessmentResult:
        """
        Assess contamination risk.

        Args:
            address: Property address
            lat: Latitude (optional)
            lon: Longitude (optional)
            planning_info: Planning information including overlays
            section_32_text: Section 32 document text

        Returns:
            ContaminationAssessmentResult with assessment
        """
        result = ContaminationAssessmentResult()

        # Check for Environmental Audit Overlay in planning info
        if planning_info:
            overlays = planning_info.get("overlays", [])
            if any(o.get("code", "").upper() == "EAO" for o in overlays):
                result.eao_overlay = True
                result.contamination_risk = "HIGH"
                result.estimated_audit_cost = "$20,000 - $100,000+"
                result.recommendations.append(
                    "Environmental Audit Overlay applies. "
                    "Environmental audit REQUIRED before residential use."
                )

        # Check Section 32 for contamination mentions
        if section_32_text:
            contamination_mentions = self._check_section_32_contamination(section_32_text)
            if contamination_mentions:
                if result.contamination_risk != "HIGH":
                    result.contamination_risk = "MEDIUM"
                result.recommendations.extend(contamination_mentions)

        # Analyze address for historical use indicators
        historical_uses = self._analyze_address_history(address)
        result.historical_uses = historical_uses

        for use in historical_uses:
            if use.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                if result.contamination_risk not in ["HIGH", "CRITICAL"]:
                    result.contamination_risk = use.risk_level.value
                result.recommendations.append(
                    f"Historical {use.business_type} at this location. "
                    "Recommend contamination assessment before purchase."
                )

        # Estimate cleanup costs based on historical uses
        if result.historical_uses:
            highest_risk_use = max(
                result.historical_uses,
                key=lambda x: ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"].index(x.risk_level.value)
            )
            config = self.high_risk_uses.get(
                highest_risk_use.business_type.lower().replace(" ", "_"),
                {}
            )
            if config:
                result.estimated_cleanup_cost = config.get("typical_cleanup_cost")

        # Determine overall risk if not already set
        if result.contamination_risk == "UNKNOWN":
            if len(result.historical_uses) > 0:
                result.contamination_risk = "MEDIUM"
            else:
                result.contamination_risk = "LOW"

        # Final recommendations
        if not result.recommendations:
            if result.contamination_risk == "LOW":
                result.recommendations.append(
                    "No significant contamination indicators found. "
                    "Consider Victoria Unearthed search for comprehensive history."
                )

        return result

    def _check_section_32_contamination(self, text: str) -> List[str]:
        """Check Section 32 for contamination-related disclosures."""
        mentions = []
        text_lower = text.lower()

        contamination_keywords = [
            "contamination", "contaminated", "environmental audit",
            "EPA", "priority site", "remediation", "remediated",
            "hazardous", "asbestos", "lead paint", "underground tank"
        ]

        for keyword in contamination_keywords:
            if keyword in text_lower:
                # Extract context
                idx = text_lower.find(keyword)
                context_start = max(0, idx - 50)
                context_end = min(len(text_lower), idx + len(keyword) + 100)
                context = text[context_start:context_end]

                mentions.append(
                    f"Section 32 mentions '{keyword}': ...{context}..."
                )

        return mentions

    def _analyze_address_history(self, address: str) -> List[HistoricalUse]:
        """
        Analyze address for historical use indicators.

        In production, this would query Victoria Unearthed API.
        For now, returns empty list with recommendation to check manually.
        """
        # This is a placeholder - real implementation would query:
        # 1. Victoria Unearthed API
        # 2. Historical Sands & McDougall directories
        # 3. EPA databases

        historical_uses = []

        # Check if address contains known high-risk terms
        address_lower = address.lower()

        for use_type, config in self.high_risk_uses.items():
            for keyword in config["keywords"]:
                if keyword in address_lower:
                    historical_uses.append(HistoricalUse(
                        business_type=use_type.replace("_", " ").title(),
                        risk_level=config["risk_level"],
                        contaminants=config.get("contaminants", []),
                        source="Address analysis"
                    ))
                    break

        return historical_uses

    def assess_nearby_sites(
        self,
        lat: float,
        lon: float,
        radius_m: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Check for EPA licensed sites nearby.

        In production, this would query EPA databases.
        """
        # Placeholder - would query EPA licensed sites within radius
        return []


def assess_contamination_risk(
    address: str,
    has_eao_overlay: bool = False
) -> Dict[str, Any]:
    """
    Quick contamination risk assessment.

    Args:
        address: Property address
        has_eao_overlay: Whether EAO overlay applies

    Returns:
        Dict with contamination assessment
    """
    import asyncio

    assessor = ContaminationAssessor()

    # Create planning info with EAO if applicable
    planning_info = None
    if has_eao_overlay:
        planning_info = {"overlays": [{"code": "EAO"}]}

    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            assessor.assess(address=address, planning_info=planning_info)
        )
    finally:
        loop.close()

    return result.to_dict()
