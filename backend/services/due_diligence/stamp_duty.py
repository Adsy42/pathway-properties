"""
Victorian Stamp Duty Calculator.

Calculates stamp duty (land transfer duty) for Victorian property purchases
including:
- Standard duty rates
- Foreign purchaser surcharge
- First Home Buyer exemptions and concessions
- Pensioner concessions
- Off-the-plan concessions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import date


class PurchaserStatus(str, Enum):
    CITIZEN = "citizen"  # Australian citizen
    PERMANENT_RESIDENT = "pr"  # Permanent resident
    FOREIGN = "foreign"  # Foreign purchaser
    TEMPORARY_VISA = "temporary"  # Temporary visa holder (treated as foreign)


class PropertyType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    PRIMARY_PRODUCTION = "primary_production"
    MIXED = "mixed"


@dataclass
class StampDutyResult:
    """Complete stamp duty calculation result."""
    purchase_price: float
    base_duty: float = 0.0
    foreign_surcharge: float = 0.0
    fhb_concession: float = 0.0
    pensioner_concession: float = 0.0
    off_the_plan_concession: float = 0.0
    total_duty: float = 0.0
    effective_rate: float = 0.0
    due_date: str = "Within 30 days of settlement"
    concessions_applied: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    breakdown: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "purchase_price": self.purchase_price,
            "base_duty": self.base_duty,
            "foreign_surcharge": self.foreign_surcharge,
            "fhb_concession": self.fhb_concession,
            "pensioner_concession": self.pensioner_concession,
            "off_the_plan_concession": self.off_the_plan_concession,
            "total_duty": self.total_duty,
            "total_duty_formatted": f"${self.total_duty:,.2f}",
            "effective_rate_percent": round(self.effective_rate, 2),
            "due_date": self.due_date,
            "concessions_applied": self.concessions_applied,
            "notes": self.notes,
            "breakdown": self.breakdown
        }


class VictorianStampDutyCalculator:
    """
    Calculates stamp duty for Victorian property purchases.
    Source: State Revenue Office Victoria (sro.vic.gov.au)

    Last updated: 2025 rates
    """

    # 2024-25 duty brackets for contracts entered into on or after 1 July 2024
    # Note: These are marginal rates
    DUTY_BRACKETS = [
        # (threshold_from, threshold_to, marginal_rate, fixed_amount_at_threshold)
        (0, 25000, 0.014, 0),           # 1.4%
        (25000, 130000, 0.024, 350),    # 2.4% + $350
        (130000, 440000, 0.05, 2870),   # 5% + $2,870
        (440000, 550000, 0.06, 18370),  # 6% + $18,370
        (550000, 960000, 0.06, 25070),  # 6% + $25,070
        (960000, 2000000, 0.055, 49670),  # 5.5% + $49,670 (premium property)
        (2000000, float('inf'), 0.065, 106870)  # 6.5% + $106,870
    ]

    # Foreign purchaser additional duty (FPAD)
    FOREIGN_PURCHASER_SURCHARGE = 0.08  # 8% additional

    # First Home Buyer thresholds
    FHB_FULL_EXEMPTION_THRESHOLD = 600000
    FHB_CONCESSION_UPPER_THRESHOLD = 750000

    # Pensioner thresholds
    PENSIONER_EXEMPTION_THRESHOLD = 330000
    PENSIONER_CONCESSION_UPPER_THRESHOLD = 750000

    # Off-the-plan concession (for eligible properties)
    OFF_THE_PLAN_THRESHOLD = 550000  # Below this = full concession

    def __init__(self):
        pass

    def calculate(
        self,
        purchase_price: float,
        property_type: PropertyType = PropertyType.RESIDENTIAL,
        purchaser_status: PurchaserStatus = PurchaserStatus.CITIZEN,
        first_home_buyer: bool = False,
        principal_residence: bool = False,
        pensioner: bool = False,
        off_the_plan: bool = False,
        contract_date: Optional[date] = None
    ) -> StampDutyResult:
        """
        Calculate Victorian stamp duty.

        Args:
            purchase_price: Purchase price in dollars
            property_type: Type of property
            purchaser_status: Residency status of purchaser
            first_home_buyer: Whether eligible for FHB concession
            principal_residence: Whether will be principal place of residence
            pensioner: Whether eligible for pensioner concession
            off_the_plan: Whether off-the-plan purchase
            contract_date: Date of contract (for rate determination)

        Returns:
            StampDutyResult with complete calculation
        """
        result = StampDutyResult(purchase_price=purchase_price)

        # Calculate base duty
        result.base_duty = self._calculate_base_duty(purchase_price)
        result.breakdown["base_calculation"] = self._get_base_calculation_breakdown(purchase_price)

        # Foreign purchaser surcharge
        if purchaser_status in [PurchaserStatus.FOREIGN, PurchaserStatus.TEMPORARY_VISA]:
            if property_type == PropertyType.RESIDENTIAL:
                result.foreign_surcharge = purchase_price * self.FOREIGN_PURCHASER_SURCHARGE
                result.notes.append(
                    f"Foreign purchaser surcharge of 8% applies: ${result.foreign_surcharge:,.2f}"
                )

        # First Home Buyer exemption/concession
        if first_home_buyer and principal_residence:
            if purchaser_status in [PurchaserStatus.CITIZEN, PurchaserStatus.PERMANENT_RESIDENT]:
                result.fhb_concession = self._calculate_fhb_concession(
                    purchase_price, result.base_duty
                )
                if result.fhb_concession > 0:
                    result.concessions_applied.append("First Home Buyer")

        # Pensioner concession
        if pensioner and principal_residence:
            if purchaser_status in [PurchaserStatus.CITIZEN, PurchaserStatus.PERMANENT_RESIDENT]:
                result.pensioner_concession = self._calculate_pensioner_concession(
                    purchase_price, result.base_duty
                )
                if result.pensioner_concession > 0:
                    result.concessions_applied.append("Pensioner")

        # Off-the-plan concession
        if off_the_plan and principal_residence:
            result.off_the_plan_concession = self._calculate_off_the_plan_concession(
                purchase_price, result.base_duty
            )
            if result.off_the_plan_concession > 0:
                result.concessions_applied.append("Off-the-plan")

        # Calculate total
        result.total_duty = max(0,
            result.base_duty +
            result.foreign_surcharge -
            result.fhb_concession -
            result.pensioner_concession -
            result.off_the_plan_concession
        )

        # Calculate effective rate
        result.effective_rate = (result.total_duty / purchase_price) * 100 if purchase_price > 0 else 0

        # Add general notes
        result.notes.extend(self._get_applicable_notes(
            purchase_price, property_type, purchaser_status,
            first_home_buyer, principal_residence
        ))

        return result

    def _calculate_base_duty(self, price: float) -> float:
        """Calculate base duty using tiered bracket system."""
        for threshold_from, threshold_to, rate, fixed_amount in self.DUTY_BRACKETS:
            if price <= threshold_to:
                return fixed_amount + (price - threshold_from) * rate

        # Above highest bracket
        last_bracket = self.DUTY_BRACKETS[-1]
        return last_bracket[3] + (price - last_bracket[0]) * last_bracket[2]

    def _get_base_calculation_breakdown(self, price: float) -> Dict[str, Any]:
        """Get detailed breakdown of base duty calculation."""
        breakdown = {
            "price": price,
            "brackets": []
        }

        remaining = price
        cumulative_duty = 0

        for threshold_from, threshold_to, rate, _ in self.DUTY_BRACKETS:
            if remaining <= 0:
                break

            bracket_amount = min(remaining, threshold_to - threshold_from)
            bracket_duty = bracket_amount * rate

            breakdown["brackets"].append({
                "from": threshold_from,
                "to": min(threshold_from + bracket_amount, threshold_to),
                "rate_percent": rate * 100,
                "amount_in_bracket": bracket_amount,
                "duty_in_bracket": bracket_duty
            })

            cumulative_duty += bracket_duty
            remaining -= bracket_amount

        breakdown["total_duty"] = cumulative_duty
        return breakdown

    def _calculate_fhb_concession(self, price: float, base_duty: float) -> float:
        """
        Calculate First Home Buyer concession.

        - Full exemption: $0 - $600,000
        - Sliding scale: $600,001 - $750,000
        - No concession: $750,001+
        """
        if price <= self.FHB_FULL_EXEMPTION_THRESHOLD:
            return base_duty  # Full exemption

        elif price <= self.FHB_CONCESSION_UPPER_THRESHOLD:
            # Sliding scale reduction
            # Concession reduces linearly from 100% to 0% between $600,001 and $750,000
            threshold_range = self.FHB_CONCESSION_UPPER_THRESHOLD - self.FHB_FULL_EXEMPTION_THRESHOLD
            amount_over = price - self.FHB_FULL_EXEMPTION_THRESHOLD
            reduction_factor = 1 - (amount_over / threshold_range)
            return base_duty * reduction_factor

        else:
            return 0  # No concession for properties over $750,000

    def _calculate_pensioner_concession(self, price: float, base_duty: float) -> float:
        """
        Calculate pensioner concession.

        Eligible pensioners get a concession on principal residence purchases.
        """
        if price <= self.PENSIONER_EXEMPTION_THRESHOLD:
            return base_duty  # Full exemption up to $330,000

        elif price <= self.PENSIONER_CONCESSION_UPPER_THRESHOLD:
            # Partial concession - reduces linearly
            threshold_range = self.PENSIONER_CONCESSION_UPPER_THRESHOLD - self.PENSIONER_EXEMPTION_THRESHOLD
            amount_over = price - self.PENSIONER_EXEMPTION_THRESHOLD
            reduction_factor = 1 - (amount_over / threshold_range)
            return base_duty * reduction_factor * 0.5  # 50% of sliding scale

        return 0

    def _calculate_off_the_plan_concession(self, price: float, base_duty: float) -> float:
        """
        Calculate off-the-plan concession.

        Duty calculated on construction value at time of contract,
        not final value at settlement.
        """
        # Simplified - in reality this is based on construction %
        if price <= self.OFF_THE_PLAN_THRESHOLD:
            # Assume average 25% of value is land at contract
            land_value_ratio = 0.25
            land_value = price * land_value_ratio
            land_duty = self._calculate_base_duty(land_value)
            concession = base_duty - land_duty
            return max(0, concession)

        return 0

    def _get_applicable_notes(
        self,
        price: float,
        property_type: PropertyType,
        purchaser_status: PurchaserStatus,
        first_home_buyer: bool,
        principal_residence: bool
    ) -> List[str]:
        """Get notes applicable to this calculation."""
        notes = []

        if price > 2000000:
            notes.append(
                "Premium property rate of 6.5% applies to portion over $2M"
            )

        if first_home_buyer and price > self.FHB_CONCESSION_UPPER_THRESHOLD:
            notes.append(
                f"Purchase price exceeds FHB concession threshold of ${self.FHB_CONCESSION_UPPER_THRESHOLD:,}. "
                "No FHB concession available."
            )

        if first_home_buyer and not principal_residence:
            notes.append(
                "FHB concession requires property to be principal residence for 12 months"
            )

        if purchaser_status == PurchaserStatus.FOREIGN:
            notes.append(
                "Foreign purchasers also subject to FIRB approval requirements"
            )

        if property_type == PropertyType.COMMERCIAL:
            notes.append(
                "Commercial property may be subject to different GST treatment"
            )

        return notes

    def estimate_total_acquisition_costs(
        self,
        purchase_price: float,
        purchaser_status: PurchaserStatus = PurchaserStatus.CITIZEN,
        first_home_buyer: bool = False,
        is_investment: bool = False
    ) -> Dict[str, Any]:
        """
        Estimate total acquisition costs including stamp duty.

        Returns comprehensive cost breakdown for budgeting.
        """
        # Calculate stamp duty
        stamp_duty_result = self.calculate(
            purchase_price=purchase_price,
            purchaser_status=purchaser_status,
            first_home_buyer=first_home_buyer,
            principal_residence=not is_investment
        )

        # Estimate other costs
        conveyancing = 1500  # Average conveyancing fee
        title_search = 150
        settlement_fee = 300
        building_inspection = 500
        pest_inspection = 300
        mortgage_registration = 150 if purchase_price < 1000000 else 250
        transfer_registration = 150

        # First Home Owner Grant (if applicable)
        fhog = 0
        if first_home_buyer and not is_investment:
            if purchase_price <= 750000:  # FHOG threshold for established homes
                fhog = 10000  # Victoria FHOG for new homes (less for established)

        costs = {
            "purchase_price": purchase_price,
            "stamp_duty": stamp_duty_result.total_duty,
            "conveyancing": conveyancing,
            "title_search": title_search,
            "settlement_fee": settlement_fee,
            "building_inspection": building_inspection,
            "pest_inspection": pest_inspection,
            "mortgage_registration": mortgage_registration,
            "transfer_registration": transfer_registration,
            "first_home_owner_grant": -fhog if fhog > 0 else 0,
            "total_acquisition_costs": (
                stamp_duty_result.total_duty +
                conveyancing +
                title_search +
                settlement_fee +
                building_inspection +
                pest_inspection +
                mortgage_registration +
                transfer_registration -
                fhog
            ),
            "deposit_at_10_percent": purchase_price * 0.10,
            "total_funds_required": (
                purchase_price * 0.10 +  # 10% deposit
                stamp_duty_result.total_duty +
                conveyancing +
                title_search +
                settlement_fee +
                building_inspection +
                pest_inspection +
                mortgage_registration +
                transfer_registration -
                fhog
            ),
            "notes": stamp_duty_result.notes
        }

        return costs


# Convenience functions
def calculate_stamp_duty(
    price: float,
    first_home_buyer: bool = False,
    is_foreign: bool = False
) -> Dict[str, Any]:
    """
    Quick stamp duty calculation.

    Args:
        price: Purchase price
        first_home_buyer: Whether FHB
        is_foreign: Whether foreign purchaser

    Returns:
        Dict with stamp duty result
    """
    calculator = VictorianStampDutyCalculator()
    result = calculator.calculate(
        purchase_price=price,
        first_home_buyer=first_home_buyer,
        principal_residence=first_home_buyer,  # Assume PPR if FHB
        purchaser_status=PurchaserStatus.FOREIGN if is_foreign else PurchaserStatus.CITIZEN
    )
    return result.to_dict()


def estimate_acquisition_costs(
    price: float,
    first_home_buyer: bool = False,
    is_investment: bool = False
) -> Dict[str, Any]:
    """
    Quick estimate of total acquisition costs.

    Returns comprehensive cost breakdown.
    """
    calculator = VictorianStampDutyCalculator()
    return calculator.estimate_total_acquisition_costs(
        purchase_price=price,
        first_home_buyer=first_home_buyer,
        is_investment=is_investment
    )
