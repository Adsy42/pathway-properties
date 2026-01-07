"""
Rooming house compliance analyzer.

Checks compliance with Victorian Building Regulations Part 13
and Residential Tenancies (Rooming House Standards) Regulations 2012.

Key requirements:
- Minimum room sizes
- Fire safety systems
- Amenity ratios
- Registration
- Annual Essential Safety Measures Report (AESMR)
"""

from typing import Optional, List, Dict, Any

from .models import (
    RoomingHouseAssessment,
    ComplianceItem,
    ComplianceStatus,
    RoomYield
)


# Victorian rooming house requirements
MINIMUM_ROOM_SIZE_SQM = 7.5  # Minimum bedroom size
MINIMUM_LIVING_SPACE_SQM = 12.5  # Living space per resident
MAX_RESIDENTS_PER_BATHROOM = 5
MAX_RESIDENTS_PER_TOILET = 10
MAX_RESIDENTS_PER_KITCHEN = 12

# Building classification thresholds
CLASS_1B_MAX_OCCUPANTS = 12
CLASS_3_MIN_OCCUPANTS = 13


class RoomingHouseAnalyzer:
    """
    Analyzer for rooming house compliance and yield.

    Implements Victorian Building Regulations Part 13 checks
    and Residential Tenancies requirements.
    """

    def __init__(self):
        # Council attitudes database (simplified)
        self.council_attitudes = {
            "YARRA": "restrictive",
            "MELBOURNE": "restrictive",
            "PORT PHILLIP": "restrictive",
            "STONNINGTON": "restrictive",
            "MORELAND": "neutral",
            "DAREBIN": "neutral",
            "BRIMBANK": "supportive",
            "WYNDHAM": "supportive",
            "CASEY": "supportive",
            "HUME": "supportive",
            "GREATER DANDENONG": "neutral",
            "WHITEHORSE": "neutral",
            "MONASH": "neutral",
            "KINGSTON": "restrictive",
        }

        # Typical weekly rents by suburb type
        self.rent_benchmarks = {
            "inner": {"min": 180, "mid": 220, "max": 280},
            "middle": {"min": 150, "mid": 180, "max": 220},
            "outer": {"min": 120, "mid": 150, "max": 180},
        }

    def analyze(
        self,
        address: str,
        suburb: str,
        lga: Optional[str] = None,
        purchase_price: Optional[float] = None,
        bedrooms: int = 4,
        bathrooms: int = 1,
        building_year: Optional[int] = None,
        land_size_sqm: Optional[float] = None,
        room_sizes: Optional[List[float]] = None,
        has_planning_permit: bool = False,
        is_registered: bool = False,
        has_aesmr: bool = False
    ) -> RoomingHouseAssessment:
        """
        Perform comprehensive rooming house analysis.

        Args:
            address: Property address
            suburb: Suburb name
            lga: Local Government Area (council)
            purchase_price: Purchase price for yield calculation
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            building_year: Year built (for fire safety requirements)
            land_size_sqm: Land size
            room_sizes: List of room sizes in sqm
            has_planning_permit: Whether rooming house permit exists
            is_registered: Whether registered as rooming house
            has_aesmr: Whether AESMR is current

        Returns:
            RoomingHouseAssessment
        """
        compliance_items = []
        risks = []
        recommendations = []

        # Determine council attitude
        council_attitude = self._get_council_attitude(lga or suburb)

        # Estimate room count (assume each bedroom can be rented)
        room_count = bedrooms
        max_occupants = room_count  # 1 person per room assumption

        # Determine building classification required
        if max_occupants <= CLASS_1B_MAX_OCCUPANTS:
            required_class = "Class 1b"
        else:
            required_class = "Class 3"
            risks.append("Property may require Class 3 building classification (>12 occupants)")

        # Planning permit check
        compliance_items.append(ComplianceItem(
            requirement="Planning permit for rooming house use",
            status=ComplianceStatus.COMPLIANT if has_planning_permit else ComplianceStatus.REQUIRES_ASSESSMENT,
            details="Planning permit required in most Victorian zones" if not has_planning_permit else "Permit obtained",
            cost_to_remedy=5000 if not has_planning_permit else None,
            priority="high"
        ))

        if not has_planning_permit:
            risks.append("No planning permit for rooming house use")
            recommendations.append("Verify planning permit status with council before purchase")

        # Registration check
        compliance_items.append(ComplianceItem(
            requirement="Rooming house registration",
            status=ComplianceStatus.COMPLIANT if is_registered else ComplianceStatus.NON_COMPLIANT,
            details="Registration with council is mandatory" if not is_registered else "Registered",
            cost_to_remedy=500 if not is_registered else None,
            priority="high"
        ))

        if not is_registered:
            risks.append("Rooming house not registered - operating illegally")
            recommendations.append("Complete registration with council immediately")

        # AESMR check
        compliance_items.append(ComplianceItem(
            requirement="Annual Essential Safety Measures Report (AESMR)",
            status=ComplianceStatus.COMPLIANT if has_aesmr else ComplianceStatus.NON_COMPLIANT,
            details="Annual fire safety inspection required" if not has_aesmr else "Current AESMR provided",
            cost_to_remedy=2500 if not has_aesmr else None,
            priority="high"
        ))

        if not has_aesmr:
            risks.append("No current AESMR - fire safety compliance unknown")
            recommendations.append("Obtain AESMR before purchase")

        # Room size compliance
        compliant_rooms = 0
        if room_sizes:
            for i, size in enumerate(room_sizes):
                if size >= MINIMUM_ROOM_SIZE_SQM:
                    compliant_rooms += 1
                else:
                    compliance_items.append(ComplianceItem(
                        requirement=f"Room {i+1} minimum size ({MINIMUM_ROOM_SIZE_SQM}sqm)",
                        status=ComplianceStatus.NON_COMPLIANT,
                        details=f"Room is {size}sqm, minimum is {MINIMUM_ROOM_SIZE_SQM}sqm",
                        priority="medium"
                    ))
        else:
            # Assume compliance without specific data
            compliant_rooms = room_count
            compliance_items.append(ComplianceItem(
                requirement="Minimum room sizes",
                status=ComplianceStatus.REQUIRES_ASSESSMENT,
                details="Room sizes not provided - manual verification required",
                priority="medium"
            ))

        # Amenity ratio checks
        bathroom_ratio_ok = bathrooms >= (max_occupants / MAX_RESIDENTS_PER_BATHROOM)
        compliance_items.append(ComplianceItem(
            requirement=f"Bathroom ratio (1:{MAX_RESIDENTS_PER_BATHROOM} max)",
            status=ComplianceStatus.COMPLIANT if bathroom_ratio_ok else ComplianceStatus.NON_COMPLIANT,
            details=f"{bathrooms} bathrooms for {max_occupants} occupants" if bathroom_ratio_ok else f"Need {int(max_occupants/MAX_RESIDENTS_PER_BATHROOM)+1} bathrooms minimum",
            cost_to_remedy=25000 if not bathroom_ratio_ok else None,
            priority="high" if not bathroom_ratio_ok else "low"
        ))

        if not bathroom_ratio_ok:
            risks.append("Insufficient bathrooms for occupant count")
            recommendations.append("Budget for bathroom addition")

        # Fire safety assessment (based on building age)
        building_year = building_year or 1980
        fire_upgrade_cost = 0

        if building_year < 1994:
            # Pre-1994 buildings likely need significant upgrades
            fire_upgrade_cost = 15000
            compliance_items.append(ComplianceItem(
                requirement="Fire safety systems (Part 13 compliance)",
                status=ComplianceStatus.REQUIRES_ASSESSMENT,
                details="Pre-1994 building - likely requires fire safety upgrades",
                cost_to_remedy=fire_upgrade_cost,
                priority="high"
            ))
            risks.append("Pre-1994 building may need significant fire safety upgrades")
        elif building_year < 2012:
            fire_upgrade_cost = 8000
            compliance_items.append(ComplianceItem(
                requirement="Fire safety systems (Part 13 compliance)",
                status=ComplianceStatus.REQUIRES_ASSESSMENT,
                details="Building may need fire safety upgrades to current standards",
                cost_to_remedy=fire_upgrade_cost,
                priority="medium"
            ))

        # Calculate compliance score
        compliant_count = sum(1 for c in compliance_items if c.status == ComplianceStatus.COMPLIANT)
        total_checks = len(compliance_items)
        compliance_score = (compliant_count / total_checks * 100) if total_checks > 0 else 0

        # Determine overall compliance
        high_priority_issues = [c for c in compliance_items
                                if c.status == ComplianceStatus.NON_COMPLIANT and c.priority == "high"]
        if high_priority_issues:
            overall_compliance = ComplianceStatus.NON_COMPLIANT
        elif any(c.status == ComplianceStatus.REQUIRES_ASSESSMENT for c in compliance_items):
            overall_compliance = ComplianceStatus.REQUIRES_ASSESSMENT
        else:
            overall_compliance = ComplianceStatus.COMPLIANT

        # Calculate yield
        rooms, total_weekly, total_annual = self._calculate_room_yields(
            room_count=compliant_rooms,
            suburb=suburb
        )

        gross_yield = None
        net_yield = None
        yield_comparison = ""

        if purchase_price and purchase_price > 0:
            gross_yield = (total_annual / purchase_price) * 100

            # Estimate annual costs
            annual_compliance_costs = 2500  # AESMR
            annual_compliance_costs += 1500  # Extra insurance
            annual_compliance_costs += 2000  # Additional maintenance
            annual_compliance_costs += 3000  # Property management premium

            standard_rental = self._estimate_standard_rental(bedrooms, suburb)
            standard_yield = (standard_rental * 52 / purchase_price) * 100

            net_annual = total_annual - annual_compliance_costs
            net_yield = (net_annual / purchase_price) * 100

            yield_premium = gross_yield - standard_yield
            yield_comparison = f"Rooming house yield {gross_yield:.1f}% vs standard {standard_yield:.1f}% ({yield_premium:+.1f}% premium)"

        # Calculate remediation costs
        remediation_costs = sum(c.cost_to_remedy or 0 for c in compliance_items)

        # Determine risk level
        if len(high_priority_issues) >= 3:
            risk_level = "critical"
        elif len(high_priority_issues) >= 1:
            risk_level = "high"
        elif overall_compliance == ComplianceStatus.REQUIRES_ASSESSMENT:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Add general recommendations
        if council_attitude == "restrictive":
            risks.append(f"Council ({lga or 'Local'}) is restrictive toward rooming houses")
            recommendations.append("Verify council's current policy before proceeding")

        if not recommendations:
            recommendations.append("Property appears suitable for rooming house investment")

        return RoomingHouseAssessment(
            property_address=address,
            current_classification="Class 1a (assumed)",
            required_classification=required_class,
            classification_upgrade_required=required_class == "Class 3",
            upgrade_cost_estimate=50000 if required_class == "Class 3" else None,
            compliance_items=compliance_items,
            overall_compliance=overall_compliance,
            compliance_score=compliance_score,
            is_registered=is_registered,
            registration_required=True,
            registration_number=None,
            room_count=room_count,
            compliant_room_count=compliant_rooms,
            rooms=rooms,
            total_weekly_rent=total_weekly,
            total_annual_rent=total_annual,
            gross_yield=gross_yield,
            net_yield=net_yield,
            yield_comparison=yield_comparison,
            annual_compliance_costs=9000,  # Typical annual compliance overhead
            fire_safety_upgrade_cost=fire_upgrade_cost if fire_upgrade_cost > 0 else None,
            remediation_costs=remediation_costs,
            risk_level=risk_level,
            key_risks=risks,
            council_attitude=council_attitude,
            recommendations=recommendations
        )

    def _get_council_attitude(self, lga_or_suburb: str) -> str:
        """Get council attitude toward rooming houses."""
        lga_upper = lga_or_suburb.upper().strip()
        return self.council_attitudes.get(lga_upper, "unknown")

    def _calculate_room_yields(
        self,
        room_count: int,
        suburb: str
    ) -> tuple:
        """Calculate per-room yields."""
        # Determine suburb type
        inner_suburbs = ["MELBOURNE", "RICHMOND", "FITZROY", "CARLTON", "SOUTH YARRA",
                        "ST KILDA", "PRAHRAN", "COLLINGWOOD", "ABBOTSFORD"]
        outer_suburbs = ["WERRIBEE", "TARNEIT", "POINT COOK", "CRAIGIEBURN",
                        "CRANBOURNE", "PAKENHAM", "MELTON"]

        suburb_upper = suburb.upper()
        if suburb_upper in inner_suburbs:
            rent_range = self.rent_benchmarks["inner"]
        elif suburb_upper in outer_suburbs:
            rent_range = self.rent_benchmarks["outer"]
        else:
            rent_range = self.rent_benchmarks["middle"]

        rooms = []
        total_weekly = 0

        for i in range(room_count):
            weekly_rent = rent_range["mid"]
            annual_rent = weekly_rent * 52 * 0.92  # 8% vacancy

            rooms.append(RoomYield(
                room_number=i + 1,
                room_type="bedroom",
                weekly_rent=weekly_rent,
                annual_rent=annual_rent,
                occupancy_rate=0.92
            ))
            total_weekly += weekly_rent

        total_annual = total_weekly * 52 * 0.92

        return rooms, total_weekly, total_annual

    def _estimate_standard_rental(self, bedrooms: int, suburb: str) -> float:
        """Estimate standard whole-house rental for comparison."""
        # Base rent by bedroom count
        base_rents = {
            1: 350,
            2: 450,
            3: 550,
            4: 650,
            5: 750,
            6: 850
        }

        base = base_rents.get(bedrooms, 550)

        # Suburb adjustment
        inner_suburbs = ["MELBOURNE", "RICHMOND", "FITZROY", "CARLTON", "SOUTH YARRA"]
        outer_suburbs = ["WERRIBEE", "TARNEIT", "CRAIGIEBURN", "CRANBOURNE"]

        if suburb.upper() in inner_suburbs:
            return base * 1.3
        elif suburb.upper() in outer_suburbs:
            return base * 0.8
        else:
            return base
