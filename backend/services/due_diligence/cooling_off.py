"""
Cooling-Off Period Calculator for Victorian Property Purchases.

Calculates cooling-off deadlines, tracks expiry, and handles complex
rules around auctions and exemptions per Sale of Land Act 1962 (Vic).
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PurchaseMethod(str, Enum):
    PRIVATE_SALE = "private_sale"
    AUCTION = "auction"
    PRE_AUCTION = "pre_auction"  # Within 3 clear business days before auction
    POST_AUCTION = "post_auction"  # Within 3 clear business days after auction
    EXPRESSION_OF_INTEREST = "expression_of_interest"


class PurchaserType(str, Enum):
    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    TRUST = "trust"
    SMSF = "smsf"


class PropertyUse(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    FARMING = "farming"
    MIXED = "mixed"


@dataclass
class CoolingOffResult:
    """Result of cooling-off calculation."""
    has_cooling_off: bool
    deadline: Optional[date] = None
    deadline_formatted: Optional[str] = None
    days_remaining: Optional[int] = None
    hours_remaining: Optional[int] = None
    penalty_to_exit: Optional[float] = None
    penalty_formatted: Optional[str] = None
    exemption_reason: Optional[str] = None
    status: str = "UNKNOWN"  # ACTIVE, URGENT, EXPIRED, EXEMPT
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_cooling_off": self.has_cooling_off,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "deadline_formatted": self.deadline_formatted,
            "days_remaining": self.days_remaining,
            "hours_remaining": self.hours_remaining,
            "penalty_to_exit": self.penalty_to_exit,
            "penalty_formatted": self.penalty_formatted,
            "exemption_reason": self.exemption_reason,
            "status": self.status,
            "warnings": self.warnings,
            "recommendations": self.recommendations
        }


# Victorian public holidays (static list, would need annual updates)
def get_victorian_public_holidays(year: int) -> List[date]:
    """Get Victorian public holidays for a given year."""
    # Standard holidays
    holidays = [
        date(year, 1, 1),   # New Year's Day
        date(year, 1, 26),  # Australia Day
        date(year, 4, 25),  # ANZAC Day
        date(year, 12, 25), # Christmas Day
        date(year, 12, 26), # Boxing Day
    ]

    # Easter dates (need to calculate - simplified here)
    # In production, use a proper Easter calculation library
    easter_dates = _calculate_easter_dates(year)
    holidays.extend(easter_dates)

    # Melbourne Cup Day (first Tuesday of November)
    first_nov = date(year, 11, 1)
    days_until_tuesday = (1 - first_nov.weekday()) % 7
    melbourne_cup = first_nov + timedelta(days=days_until_tuesday)
    holidays.append(melbourne_cup)

    # Queen's Birthday (second Monday of June)
    first_june = date(year, 6, 1)
    days_until_monday = (7 - first_june.weekday()) % 7
    queens_birthday = first_june + timedelta(days=days_until_monday + 7)
    holidays.append(queens_birthday)

    # AFL Grand Final Friday (last Friday before last Saturday in September)
    # Simplified - would need actual date each year

    return holidays


def _calculate_easter_dates(year: int) -> List[date]:
    """Calculate Easter-related dates using Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    easter_sunday = date(year, month, day)
    good_friday = easter_sunday - timedelta(days=2)
    easter_saturday = easter_sunday - timedelta(days=1)
    easter_monday = easter_sunday + timedelta(days=1)

    return [good_friday, easter_saturday, easter_monday]


class CoolingOffCalculator:
    """
    Calculates cooling-off deadlines and tracks expiry.
    Critical for buyers who need to complete due diligence in time.
    """

    # Victorian cooling-off rules
    STANDARD_PERIOD_DAYS = 3  # 3 CLEAR business days
    PENALTY_FLAT = 100.0
    PENALTY_PERCENTAGE = 0.002  # 0.2% of purchase price

    def __init__(self):
        self.holidays_cache: Dict[int, List[date]] = {}

    def calculate_cooling_off(
        self,
        contract_signed_date: date,
        purchase_price: float,
        purchase_method: PurchaseMethod,
        auction_date: Optional[date] = None,
        purchaser_type: PurchaserType = PurchaserType.INDIVIDUAL,
        property_use: PropertyUse = PropertyUse.RESIDENTIAL,
        land_size_hectares: float = 0.0,
        section_31_certificate: bool = False,
        section_66w_waiver: bool = False
    ) -> CoolingOffResult:
        """
        Calculate cooling-off period and deadline.

        Args:
            contract_signed_date: Date purchaser signed contract
            purchase_price: Purchase price in dollars
            purchase_method: How property was purchased
            auction_date: Date of auction (if applicable)
            purchaser_type: Type of purchaser entity
            property_use: Primary use of property
            land_size_hectares: Land size in hectares
            section_31_certificate: Whether s.31 certificate was signed
            section_66w_waiver: Whether s.66W waiver was signed

        Returns:
            CoolingOffResult with all relevant information
        """
        result = CoolingOffResult(has_cooling_off=True)

        # Check exemptions
        exemption = self._check_exemptions(
            purchase_method=purchase_method,
            auction_date=auction_date,
            contract_signed_date=contract_signed_date,
            purchaser_type=purchaser_type,
            property_use=property_use,
            land_size_hectares=land_size_hectares,
            section_31_certificate=section_31_certificate,
            section_66w_waiver=section_66w_waiver
        )

        if exemption:
            result.has_cooling_off = False
            result.exemption_reason = exemption
            result.status = "EXEMPT"
            result.warnings.append(
                "No cooling-off period applies. Due diligence MUST be complete before signing contract."
            )
            result.recommendations.append(
                "Since there is no cooling-off period, ensure all inspections, searches, and "
                "finance approval are complete before signing."
            )
            return result

        # Calculate deadline
        deadline = self._calculate_deadline(contract_signed_date)
        result.deadline = deadline
        result.deadline_formatted = deadline.strftime("%A, %d %B %Y at 11:59 PM")

        # Calculate time remaining
        today = date.today()
        result.days_remaining = (deadline - today).days
        result.hours_remaining = result.days_remaining * 24

        # Calculate penalty to exit
        penalty = max(self.PENALTY_FLAT, purchase_price * self.PENALTY_PERCENTAGE)
        result.penalty_to_exit = penalty
        result.penalty_formatted = f"${penalty:,.2f} (max of $100 or 0.2% of ${purchase_price:,.0f})"

        # Set status
        if result.days_remaining < 0:
            result.status = "EXPIRED"
            result.warnings.append("Cooling-off period has EXPIRED. Contract is now binding.")
        elif result.days_remaining <= 1:
            result.status = "URGENT"
            result.warnings.append(
                f"URGENT: Only {result.days_remaining} day(s) remaining. "
                "Complete due diligence immediately or exercise cooling-off rights."
            )
        else:
            result.status = "ACTIVE"

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, purchase_price)

        return result

    def _check_exemptions(
        self,
        purchase_method: PurchaseMethod,
        auction_date: Optional[date],
        contract_signed_date: date,
        purchaser_type: PurchaserType,
        property_use: PropertyUse,
        land_size_hectares: float,
        section_31_certificate: bool,
        section_66w_waiver: bool
    ) -> Optional[str]:
        """Check if any cooling-off exemption applies."""

        # Auction exemptions
        if purchase_method == PurchaseMethod.AUCTION:
            return "Property purchased at auction - no cooling-off applies"

        if purchase_method == PurchaseMethod.PRE_AUCTION and auction_date:
            days_before = (auction_date - contract_signed_date).days
            if days_before <= 3:
                return f"Contract signed within 3 clear business days before auction ({days_before} days)"

        if purchase_method == PurchaseMethod.POST_AUCTION and auction_date:
            days_after = (contract_signed_date - auction_date).days
            if days_after <= 3:
                return f"Contract signed within 3 clear business days after auction ({days_after} days)"

        # Purchaser type exemption
        if purchaser_type == PurchaserType.CORPORATION:
            return "Purchaser is a corporation (company) - no cooling-off for corporate purchasers"

        # Property use exemption
        if property_use == PropertyUse.COMMERCIAL:
            return "Property is primarily for commercial use - no cooling-off applies"

        if property_use == PropertyUse.INDUSTRIAL:
            return "Property is primarily for industrial use - no cooling-off applies"

        # Farm exemption
        if property_use == PropertyUse.FARMING and land_size_hectares > 20:
            return f"Property exceeds 20 hectares ({land_size_hectares:.1f}ha) and primarily for farming"

        # Certificate/waiver exemptions
        if section_31_certificate:
            return "Section 31 certificate signed by purchaser's lawyer - cooling-off waived"

        if section_66w_waiver:
            return "Section 66W cooling-off waiver signed - cooling-off expressly waived"

        return None

    def _calculate_deadline(self, signed_date: date) -> date:
        """
        Calculate cooling-off deadline.

        3 CLEAR business days means:
        - Excludes the day contract was signed
        - Excludes weekends
        - Excludes Victorian public holidays
        """
        year = signed_date.year
        if year not in self.holidays_cache:
            self.holidays_cache[year] = get_victorian_public_holidays(year)
            # Also cache next year in case deadline crosses year boundary
            self.holidays_cache[year + 1] = get_victorian_public_holidays(year + 1)

        holidays = self.holidays_cache[year] + self.holidays_cache.get(year + 1, [])

        clear_days = 0
        current_date = signed_date

        while clear_days < 3:
            current_date += timedelta(days=1)

            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() >= 5:
                continue

            # Skip Victorian public holidays
            if current_date in holidays:
                continue

            clear_days += 1

        return current_date

    def _generate_recommendations(
        self,
        result: CoolingOffResult,
        purchase_price: float
    ) -> List[str]:
        """Generate recommendations based on cooling-off status."""
        recommendations = []

        if result.status == "EXPIRED":
            recommendations.append(
                "Contract is now unconditional (subject to any special conditions). "
                "Negotiate with vendor if issues discovered."
            )
        elif result.status == "URGENT":
            recommendations.extend([
                "PRIORITY 1: Complete building and pest inspection TODAY",
                "PRIORITY 2: Confirm finance pre-approval status",
                "PRIORITY 3: Review Section 32 with conveyancer",
                f"If exiting, provide written notice and {result.penalty_formatted} penalty"
            ])
        elif result.status == "ACTIVE":
            days = result.days_remaining
            recommendations.extend([
                f"You have {days} days to complete due diligence",
                "Day 1: Building and pest inspection",
                f"Day 2: Review Section 32, confirm finance",
                f"Day 3: Final review and decision",
                "To exit: written notice + penalty required before deadline"
            ])

        return recommendations

    def get_key_dates(
        self,
        contract_signed_date: date,
        settlement_days: int = 30,
        finance_deadline_days: int = 14
    ) -> Dict[str, Any]:
        """
        Get all key dates for a property transaction.

        Returns a timeline of important dates.
        """
        cooling_off = self._calculate_deadline(contract_signed_date)
        settlement = contract_signed_date + timedelta(days=settlement_days)
        finance_deadline = contract_signed_date + timedelta(days=finance_deadline_days)

        return {
            "contract_signed": contract_signed_date.isoformat(),
            "cooling_off_expires": cooling_off.isoformat(),
            "finance_deadline": finance_deadline.isoformat(),
            "settlement_date": settlement.isoformat(),
            "timeline": [
                {
                    "date": contract_signed_date.isoformat(),
                    "event": "Contract signed",
                    "description": "Cooling-off period begins"
                },
                {
                    "date": cooling_off.isoformat(),
                    "event": "Cooling-off expires",
                    "description": "Last day to exit contract with penalty"
                },
                {
                    "date": finance_deadline.isoformat(),
                    "event": "Finance deadline",
                    "description": "Typical deadline for finance approval condition"
                },
                {
                    "date": settlement.isoformat(),
                    "event": "Settlement",
                    "description": "Transfer of ownership and keys"
                }
            ]
        }


class CoolingOffTracker:
    """
    Tracks multiple properties and their cooling-off status.
    Useful for buyer's agents managing multiple transactions.
    """

    def __init__(self):
        self.calculator = CoolingOffCalculator()
        self.tracked_properties: Dict[str, CoolingOffResult] = {}

    def track_property(
        self,
        property_id: str,
        contract_signed_date: date,
        purchase_price: float,
        purchase_method: PurchaseMethod = PurchaseMethod.PRIVATE_SALE,
        **kwargs
    ) -> CoolingOffResult:
        """Add a property to tracking."""
        result = self.calculator.calculate_cooling_off(
            contract_signed_date=contract_signed_date,
            purchase_price=purchase_price,
            purchase_method=purchase_method,
            **kwargs
        )
        self.tracked_properties[property_id] = result
        return result

    def get_urgent_properties(self) -> List[Tuple[str, CoolingOffResult]]:
        """Get all properties with URGENT status."""
        return [
            (pid, result)
            for pid, result in self.tracked_properties.items()
            if result.status == "URGENT"
        ]

    def get_active_properties(self) -> List[Tuple[str, CoolingOffResult]]:
        """Get all properties with active cooling-off periods."""
        return [
            (pid, result)
            for pid, result in self.tracked_properties.items()
            if result.has_cooling_off and result.status in ["ACTIVE", "URGENT"]
        ]


# Convenience functions
def calculate_cooling_off(
    contract_signed: str,
    purchase_price: float,
    is_auction: bool = False,
    is_company_buyer: bool = False
) -> Dict[str, Any]:
    """
    Quick cooling-off calculation.

    Args:
        contract_signed: Date string in YYYY-MM-DD format
        purchase_price: Purchase price in dollars
        is_auction: Whether purchased at auction
        is_company_buyer: Whether purchaser is a company

    Returns:
        Dict with cooling-off details
    """
    signed_date = date.fromisoformat(contract_signed)

    purchase_method = PurchaseMethod.AUCTION if is_auction else PurchaseMethod.PRIVATE_SALE
    purchaser_type = PurchaserType.CORPORATION if is_company_buyer else PurchaserType.INDIVIDUAL

    calculator = CoolingOffCalculator()
    result = calculator.calculate_cooling_off(
        contract_signed_date=signed_date,
        purchase_price=purchase_price,
        purchase_method=purchase_method,
        purchaser_type=purchaser_type
    )

    return result.to_dict()
