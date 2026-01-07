"""
Financial Analysis Module.

Comprehensive financial analysis for property investment:
- Comparable sales analysis
- Investor cash flow modeling
- Yield calculations
- Tax impact analysis
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics


class PricingAssessment(str, Enum):
    SIGNIFICANTLY_BELOW = "SIGNIFICANTLY_BELOW_MARKET"
    BELOW = "BELOW_MARKET"
    AT_MARKET = "AT_MARKET"
    ABOVE = "ABOVE_MARKET"
    SIGNIFICANTLY_ABOVE = "SIGNIFICANTLY_ABOVE_MARKET"


# ============================================================================
# COMPARABLE SALES ANALYSIS
# ============================================================================

@dataclass
class ComparableSale:
    """A comparable sale property."""
    address: str
    sale_price: float
    sale_date: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    land_size: Optional[float] = None
    building_size: Optional[float] = None
    distance_km: float = 0.0
    days_on_market: Optional[int] = None
    price_per_sqm_land: Optional[float] = None
    price_per_sqm_building: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "sale_price": self.sale_price,
            "sale_price_formatted": f"${self.sale_price:,.0f}",
            "sale_date": self.sale_date,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "land_size": self.land_size,
            "building_size": self.building_size,
            "distance_km": self.distance_km,
            "days_on_market": self.days_on_market,
            "price_per_sqm_land": self.price_per_sqm_land,
            "price_per_sqm_building": self.price_per_sqm_building
        }


@dataclass
class ComparableSalesResult:
    """Complete comparable sales analysis."""
    comparables_found: int = 0
    median_sale_price: Optional[float] = None
    mean_sale_price: Optional[float] = None
    min_sale_price: Optional[float] = None
    max_sale_price: Optional[float] = None
    price_per_sqm_land: Dict[str, Any] = field(default_factory=dict)
    price_per_sqm_building: Dict[str, Any] = field(default_factory=dict)
    subject_vs_comparables: Dict[str, Any] = field(default_factory=dict)
    comparables: List[ComparableSale] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparables_found": self.comparables_found,
            "median_sale_price": self.median_sale_price,
            "median_formatted": f"${self.median_sale_price:,.0f}" if self.median_sale_price else None,
            "mean_sale_price": self.mean_sale_price,
            "min_sale_price": self.min_sale_price,
            "max_sale_price": self.max_sale_price,
            "price_per_sqm_land": self.price_per_sqm_land,
            "price_per_sqm_building": self.price_per_sqm_building,
            "subject_vs_comparables": self.subject_vs_comparables,
            "comparables": [c.to_dict() for c in self.comparables],
            "recommendations": self.recommendations
        }


class ComparableSalesAnalyzer:
    """
    Analyzes comparable sales to validate asking price.
    More sophisticated than AVM alone.
    """

    def analyze(
        self,
        subject_property: Dict[str, Any],
        comparable_sales: List[Dict[str, Any]]
    ) -> ComparableSalesResult:
        """
        Analyze comparable sales against subject property.

        Args:
            subject_property: Dict with subject property details:
                - asking_price: float
                - land_size: float (sqm)
                - building_size: float (sqm, optional)
                - bedrooms: int
                - bathrooms: int
            comparable_sales: List of comparable sales from CoreLogic/PropTrack

        Returns:
            ComparableSalesResult with analysis
        """
        result = ComparableSalesResult()

        if not comparable_sales:
            result.recommendations.append(
                "No comparable sales data available. "
                "Recommend obtaining CoreLogic comparable sales report."
            )
            return result

        # Process comparables
        processed_comparables = []
        for sale in comparable_sales:
            comp = ComparableSale(
                address=sale.get("address", "Unknown"),
                sale_price=sale.get("sale_price", 0),
                sale_date=sale.get("sale_date", ""),
                bedrooms=sale.get("bedrooms"),
                bathrooms=sale.get("bathrooms"),
                land_size=sale.get("land_size"),
                building_size=sale.get("building_size"),
                distance_km=sale.get("distance_km", 0),
                days_on_market=sale.get("days_on_market")
            )

            # Calculate price per sqm
            if comp.land_size and comp.land_size > 0:
                comp.price_per_sqm_land = comp.sale_price / comp.land_size

            if comp.building_size and comp.building_size > 0:
                comp.price_per_sqm_building = comp.sale_price / comp.building_size

            processed_comparables.append(comp)

        # Sort by distance
        processed_comparables.sort(key=lambda x: x.distance_km)
        result.comparables = processed_comparables[:10]  # Top 10
        result.comparables_found = len(comparable_sales)

        # Calculate statistics
        prices = [c.sale_price for c in processed_comparables if c.sale_price > 0]

        if prices:
            result.median_sale_price = statistics.median(prices)
            result.mean_sale_price = statistics.mean(prices)
            result.min_sale_price = min(prices)
            result.max_sale_price = max(prices)

        # Price per sqm (land)
        land_sqm_prices = [
            c.price_per_sqm_land
            for c in processed_comparables
            if c.price_per_sqm_land and c.price_per_sqm_land > 0
        ]

        subject_land_size = subject_property.get("land_size", 0)
        subject_asking = subject_property.get("asking_price", 0)

        if land_sqm_prices:
            subject_price_per_sqm = (
                subject_asking / subject_land_size
                if subject_land_size > 0 else 0
            )

            result.price_per_sqm_land = {
                "median": statistics.median(land_sqm_prices),
                "mean": statistics.mean(land_sqm_prices),
                "subject": subject_price_per_sqm,
                "percentile": self._calculate_percentile(
                    subject_price_per_sqm, land_sqm_prices
                )
            }

        # Price per sqm (building)
        building_sqm_prices = [
            c.price_per_sqm_building
            for c in processed_comparables
            if c.price_per_sqm_building and c.price_per_sqm_building > 0
        ]

        subject_building_size = subject_property.get("building_size", 0)

        if building_sqm_prices:
            subject_building_price = (
                subject_asking / subject_building_size
                if subject_building_size > 0 else 0
            )

            result.price_per_sqm_building = {
                "median": statistics.median(building_sqm_prices),
                "mean": statistics.mean(building_sqm_prices),
                "subject": subject_building_price
            }

        # Compare subject to comparables
        if result.median_sale_price and subject_asking:
            premium_discount = (
                (subject_asking - result.median_sale_price) /
                result.median_sale_price * 100
            )

            assessment = self._assess_pricing(premium_discount)

            result.subject_vs_comparables = {
                "asking_price": subject_asking,
                "asking_formatted": f"${subject_asking:,.0f}",
                "median_comparable": result.median_sale_price,
                "median_formatted": f"${result.median_sale_price:,.0f}",
                "premium_discount_percent": round(premium_discount, 1),
                "assessment": assessment.value,
                "assessment_description": self._get_assessment_description(assessment)
            }

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, subject_property)

        return result

    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """Calculate percentile of value within values list."""
        if not values:
            return 50.0

        sorted_values = sorted(values)
        count_below = sum(1 for v in sorted_values if v < value)

        return (count_below / len(sorted_values)) * 100

    def _assess_pricing(self, premium_discount: float) -> PricingAssessment:
        """Assess pricing based on premium/discount percentage."""
        if premium_discount < -10:
            return PricingAssessment.SIGNIFICANTLY_BELOW
        elif premium_discount < -5:
            return PricingAssessment.BELOW
        elif premium_discount <= 5:
            return PricingAssessment.AT_MARKET
        elif premium_discount <= 10:
            return PricingAssessment.ABOVE
        else:
            return PricingAssessment.SIGNIFICANTLY_ABOVE

    def _get_assessment_description(self, assessment: PricingAssessment) -> str:
        """Get human-readable assessment description."""
        descriptions = {
            PricingAssessment.SIGNIFICANTLY_BELOW: "Significantly below market - investigate why",
            PricingAssessment.BELOW: "Below market - potential value opportunity",
            PricingAssessment.AT_MARKET: "At market - fair pricing",
            PricingAssessment.ABOVE: "Above market - negotiate",
            PricingAssessment.SIGNIFICANTLY_ABOVE: "Significantly above market - strong negotiation needed"
        }
        return descriptions.get(assessment, "Unknown")

    def _generate_recommendations(
        self,
        result: ComparableSalesResult,
        subject_property: Dict[str, Any]
    ) -> List[str]:
        """Generate pricing recommendations."""
        recommendations = []

        assessment = result.subject_vs_comparables.get("assessment", "")
        premium = result.subject_vs_comparables.get("premium_discount_percent", 0)

        if assessment == PricingAssessment.SIGNIFICANTLY_BELOW.value:
            recommendations.append(
                f"Asking price is {abs(premium):.1f}% below comparable sales. "
                "Investigate reason - possible motivated seller or undisclosed issues."
            )
        elif assessment == PricingAssessment.BELOW.value:
            recommendations.append(
                f"Asking price is {abs(premium):.1f}% below market. "
                "Potential value opportunity if no underlying issues."
            )
        elif assessment == PricingAssessment.AT_MARKET.value:
            recommendations.append(
                "Asking price is in line with comparable sales. "
                "Standard negotiation of 5-10% may be achievable."
            )
        elif assessment == PricingAssessment.ABOVE.value:
            recommendations.append(
                f"Asking price is {premium:.1f}% above comparable sales. "
                "Negotiate using comparable evidence."
            )
        elif assessment == PricingAssessment.SIGNIFICANTLY_ABOVE.value:
            recommendations.append(
                f"Asking price is {premium:.1f}% above comparable sales. "
                "Strong negotiation needed - use comparable sales as evidence."
            )

        if result.comparables_found < 5:
            recommendations.append(
                f"Only {result.comparables_found} comparables found. "
                "Consider expanding search criteria for more data."
            )

        return recommendations


# ============================================================================
# INVESTOR CASH FLOW MODEL
# ============================================================================

@dataclass
class CashFlowResult:
    """Complete cash flow analysis result."""
    summary: Dict[str, Any] = field(default_factory=dict)
    income: Dict[str, Any] = field(default_factory=dict)
    outgoings: Dict[str, Any] = field(default_factory=dict)
    finance: Dict[str, Any] = field(default_factory=dict)
    tax: Dict[str, Any] = field(default_factory=dict)
    acquisition_costs: Dict[str, Any] = field(default_factory=dict)
    sensitivity_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "income": self.income,
            "outgoings": self.outgoings,
            "finance": self.finance,
            "tax": self.tax,
            "acquisition_costs": self.acquisition_costs,
            "sensitivity_analysis": self.sensitivity_analysis,
            "recommendations": self.recommendations
        }


class InvestorCashFlowModel:
    """
    Comprehensive cash flow model for investment property analysis.
    """

    # Default assumptions
    DEFAULT_VACANCY_RATE = 0.02  # 2%
    DEFAULT_PM_RATE = 0.07  # 7% of rent
    DEFAULT_REPAIRS_PERCENT = 0.005  # 0.5% of property value
    DEFAULT_INTEREST_RATE = 0.065  # 6.5%
    DEFAULT_LVR = 0.80  # 80%

    def calculate(
        self,
        purchase_price: float,
        weekly_rent: float,
        outgoings: Dict[str, float],
        finance_params: Optional[Dict[str, Any]] = None,
        investor_params: Optional[Dict[str, Any]] = None
    ) -> CashFlowResult:
        """
        Calculate comprehensive cash flow.

        Args:
            purchase_price: Purchase price in dollars
            weekly_rent: Weekly rental income
            outgoings: Dict with:
                - council_rates: Annual council rates
                - water_rates: Annual water rates
                - strata_levies: Quarterly strata levies (if applicable)
                - land_value: Site value for land tax
                - building_year: Year built (for depreciation)
            finance_params: Optional financing parameters:
                - lvr: Loan to value ratio (default 0.80)
                - interest_rate: Annual interest rate (default 0.065)
                - loan_type: 'interest_only' or 'principal_and_interest'
            investor_params: Optional investor parameters:
                - vacancy_rate: Expected vacancy (default 0.02)
                - pm_rate: Property management fee (default 0.07)
                - marginal_tax_rate: Investor's marginal tax rate (default 0.37)
                - total_land_holdings: Total land value for land tax (default 0)

        Returns:
            CashFlowResult with comprehensive analysis
        """
        result = CashFlowResult()

        # Apply defaults
        finance = finance_params or {}
        investor = investor_params or {}

        lvr = finance.get("lvr", self.DEFAULT_LVR)
        interest_rate = finance.get("interest_rate", self.DEFAULT_INTEREST_RATE)
        loan_type = finance.get("loan_type", "interest_only")

        vacancy_rate = investor.get("vacancy_rate", self.DEFAULT_VACANCY_RATE)
        pm_rate = investor.get("pm_rate", self.DEFAULT_PM_RATE)
        marginal_tax_rate = investor.get("marginal_tax_rate", 0.37)
        total_land_holdings = investor.get("total_land_holdings", 0)

        # === INCOME ===
        annual_rent = weekly_rent * 52
        vacancy_allowance = annual_rent * vacancy_rate
        effective_rent = annual_rent - vacancy_allowance

        result.income = {
            "weekly_rent": weekly_rent,
            "weekly_rent_formatted": f"${weekly_rent:,.0f}",
            "annual_rent": annual_rent,
            "vacancy_rate_percent": vacancy_rate * 100,
            "vacancy_allowance": vacancy_allowance,
            "effective_rent": effective_rent,
            "effective_rent_formatted": f"${effective_rent:,.0f}"
        }

        # === OUTGOINGS ===
        council_rates = outgoings.get("council_rates", 2400)
        water_rates = outgoings.get("water_rates", 800)
        strata_levies = outgoings.get("strata_levies", 0) * 4  # Quarterly to annual
        landlord_insurance = outgoings.get("insurance", purchase_price * 0.002)
        property_management = effective_rent * pm_rate
        repairs_maintenance = purchase_price * self.DEFAULT_REPAIRS_PERCENT

        # Land tax calculation
        land_value = outgoings.get("land_value", purchase_price * 0.4)
        land_tax = self._calculate_land_tax(land_value, total_land_holdings)

        total_outgoings = (
            council_rates + water_rates + strata_levies +
            landlord_insurance + property_management + repairs_maintenance + land_tax
        )

        result.outgoings = {
            "council_rates": council_rates,
            "water_rates": water_rates,
            "strata_levies_annual": strata_levies,
            "landlord_insurance": landlord_insurance,
            "property_management": property_management,
            "pm_rate_percent": pm_rate * 100,
            "repairs_maintenance": repairs_maintenance,
            "land_tax": land_tax,
            "total_annual": total_outgoings,
            "total_formatted": f"${total_outgoings:,.0f}"
        }

        # === FINANCE ===
        loan_amount = purchase_price * lvr
        deposit_required = purchase_price * (1 - lvr)

        if loan_type == "interest_only":
            annual_interest = loan_amount * interest_rate
            annual_principal = 0
            monthly_payment = annual_interest / 12
        else:
            # P&I - 30 year amortization
            monthly_rate = interest_rate / 12
            num_payments = 360
            monthly_payment = loan_amount * (
                monthly_rate * (1 + monthly_rate) ** num_payments
            ) / ((1 + monthly_rate) ** num_payments - 1)
            annual_payment = monthly_payment * 12
            annual_interest = loan_amount * interest_rate  # First year approximation
            annual_principal = annual_payment - annual_interest

        result.finance = {
            "purchase_price": purchase_price,
            "purchase_price_formatted": f"${purchase_price:,.0f}",
            "loan_amount": loan_amount,
            "loan_amount_formatted": f"${loan_amount:,.0f}",
            "deposit_required": deposit_required,
            "deposit_formatted": f"${deposit_required:,.0f}",
            "lvr_percent": lvr * 100,
            "interest_rate_percent": interest_rate * 100,
            "loan_type": loan_type,
            "monthly_payment": monthly_payment,
            "monthly_payment_formatted": f"${monthly_payment:,.0f}",
            "annual_interest": annual_interest,
            "annual_principal": annual_principal
        }

        # === CASH FLOW ===
        net_operating_income = effective_rent - total_outgoings
        pre_tax_cash_flow = net_operating_income - annual_interest - annual_principal

        # === TAX ===
        # Depreciation estimate
        building_year = outgoings.get("building_year")
        if building_year:
            building_age = 2025 - building_year
            if building_age < 40:  # Post-1985 building
                building_value = purchase_price * 0.6
                annual_depreciation = building_value * 0.025  # 2.5% p.a.
            else:
                annual_depreciation = 5000  # Plant & equipment only
        else:
            annual_depreciation = 5000  # Conservative estimate

        total_deductions = total_outgoings + annual_interest + annual_depreciation
        taxable_income_impact = effective_rent - total_deductions

        if taxable_income_impact < 0:
            # Negative gearing
            tax_benefit = abs(taxable_income_impact) * marginal_tax_rate
            after_tax_cash_flow = pre_tax_cash_flow + tax_benefit
            gearing_status = "NEGATIVE"
        else:
            # Positive gearing
            tax_liability = taxable_income_impact * marginal_tax_rate
            after_tax_cash_flow = pre_tax_cash_flow - tax_liability
            gearing_status = "POSITIVE"
            tax_benefit = -tax_liability

        result.tax = {
            "annual_depreciation": annual_depreciation,
            "depreciation_note": "Estimate only - obtain QS report for accuracy",
            "total_deductions": total_deductions,
            "taxable_income_impact": taxable_income_impact,
            "marginal_tax_rate_percent": marginal_tax_rate * 100,
            "tax_benefit_or_liability": tax_benefit,
            "gearing_status": gearing_status
        }

        # === YIELDS ===
        gross_yield = (annual_rent / purchase_price) * 100
        net_yield = (net_operating_income / purchase_price) * 100

        # === ACQUISITION COSTS ===
        stamp_duty = self._estimate_stamp_duty(purchase_price)
        acquisition_costs = self._calculate_acquisition_costs(purchase_price, stamp_duty)
        equity_invested = deposit_required + acquisition_costs["total"]

        result.acquisition_costs = acquisition_costs

        # Cash-on-cash return
        cash_on_cash_return = (after_tax_cash_flow / equity_invested) * 100

        # === SUMMARY ===
        result.summary = {
            "gross_yield_percent": round(gross_yield, 2),
            "net_yield_percent": round(net_yield, 2),
            "cash_on_cash_return_percent": round(cash_on_cash_return, 2),
            "gearing_status": gearing_status,
            "weekly_cash_flow": round(after_tax_cash_flow / 52, 2),
            "weekly_cash_flow_formatted": f"${after_tax_cash_flow / 52:,.0f}",
            "monthly_cash_flow": round(after_tax_cash_flow / 12, 2),
            "monthly_cash_flow_formatted": f"${after_tax_cash_flow / 12:,.0f}",
            "annual_cash_flow": round(after_tax_cash_flow, 2),
            "annual_cash_flow_formatted": f"${after_tax_cash_flow:,.0f}",
            "total_equity_required": equity_invested,
            "total_equity_formatted": f"${equity_invested:,.0f}"
        }

        # === SENSITIVITY ANALYSIS ===
        result.sensitivity_analysis = self._run_sensitivity(
            purchase_price, weekly_rent, outgoings,
            finance_params, investor_params
        )

        # === RECOMMENDATIONS ===
        result.recommendations = self._generate_recommendations(result)

        return result

    def _calculate_land_tax(self, land_value: float, total_holdings: float) -> float:
        """
        Calculate Victorian land tax.

        Uses 2024-25 general rates.
        """
        total_land = land_value + total_holdings

        if total_land <= 50000:
            total_tax = 0
        elif total_land <= 100000:
            total_tax = (total_land - 50000) * 0.0002
        elif total_land <= 300000:
            total_tax = 100 + (total_land - 100000) * 0.0005
        elif total_land <= 600000:
            total_tax = 1100 + (total_land - 300000) * 0.001
        elif total_land <= 1000000:
            total_tax = 4100 + (total_land - 600000) * 0.0015
        elif total_land <= 1800000:
            total_tax = 10100 + (total_land - 1000000) * 0.002
        elif total_land <= 3000000:
            total_tax = 26100 + (total_land - 1800000) * 0.0025
        else:
            total_tax = 56100 + (total_land - 3000000) * 0.0055

        # Return proportional amount for this property
        if total_land > 0:
            return (land_value / total_land) * total_tax
        return 0

    def _estimate_stamp_duty(self, price: float) -> float:
        """Quick stamp duty estimate for investment property."""
        if price <= 25000:
            return price * 0.014
        elif price <= 130000:
            return 350 + (price - 25000) * 0.024
        elif price <= 440000:
            return 2870 + (price - 130000) * 0.05
        elif price <= 550000:
            return 18370 + (price - 440000) * 0.06
        elif price <= 960000:
            return 25070 + (price - 550000) * 0.06
        else:
            return 49670 + (price - 960000) * 0.055

    def _calculate_acquisition_costs(
        self,
        purchase_price: float,
        stamp_duty: float
    ) -> Dict[str, Any]:
        """Calculate all acquisition costs."""
        conveyancing = 1500
        title_search = 150
        building_inspection = 500
        pest_inspection = 300
        settlement_fee = 300
        mortgage_registration = 200

        total = (
            stamp_duty + conveyancing + title_search +
            building_inspection + pest_inspection +
            settlement_fee + mortgage_registration
        )

        return {
            "stamp_duty": stamp_duty,
            "stamp_duty_formatted": f"${stamp_duty:,.0f}",
            "conveyancing": conveyancing,
            "title_search": title_search,
            "building_inspection": building_inspection,
            "pest_inspection": pest_inspection,
            "settlement_fee": settlement_fee,
            "mortgage_registration": mortgage_registration,
            "total": total,
            "total_formatted": f"${total:,.0f}"
        }

    def _run_sensitivity(
        self,
        purchase_price: float,
        weekly_rent: float,
        outgoings: Dict[str, float],
        finance_params: Optional[Dict[str, Any]],
        investor_params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run sensitivity analysis on key variables."""
        scenarios = {}

        # Interest rate sensitivity
        for rate_delta in [-0.01, 0, 0.01, 0.02]:
            params = (finance_params or {}).copy()
            new_rate = params.get("interest_rate", self.DEFAULT_INTEREST_RATE) + rate_delta
            params["interest_rate"] = new_rate

            # Quick recalc
            loan = purchase_price * params.get("lvr", self.DEFAULT_LVR)
            annual_interest = loan * new_rate

            net_income = (weekly_rent * 52 * 0.98) - sum([
                outgoings.get("council_rates", 2400),
                outgoings.get("water_rates", 800),
                outgoings.get("strata_levies", 0) * 4,
                purchase_price * 0.002,
                (weekly_rent * 52 * 0.98) * 0.07,
                purchase_price * 0.005
            ])

            cash_flow = net_income - annual_interest

            scenarios[f"rate_{new_rate * 100:.1f}"] = {
                "interest_rate": new_rate * 100,
                "annual_cash_flow": round(cash_flow, 0),
                "monthly_cash_flow": round(cash_flow / 12, 0)
            }

        return {
            "interest_rate_scenarios": scenarios,
            "note": "Shows impact of interest rate changes on cash flow"
        }

    def _generate_recommendations(self, result: CashFlowResult) -> List[str]:
        """Generate investment recommendations."""
        recommendations = []

        gross_yield = result.summary.get("gross_yield_percent", 0)
        cash_flow = result.summary.get("monthly_cash_flow", 0)
        gearing = result.summary.get("gearing_status", "")

        if gross_yield < 4:
            recommendations.append(
                f"Gross yield of {gross_yield:.1f}% is below typical threshold. "
                "Property relies heavily on capital growth."
            )
        elif gross_yield > 6:
            recommendations.append(
                f"Gross yield of {gross_yield:.1f}% is attractive. "
                "Strong rental income relative to price."
            )

        if cash_flow < 0:
            recommendations.append(
                f"Negative cash flow of ${abs(cash_flow):,.0f}/month. "
                "Ensure you have buffer for vacancy and repairs."
            )
        elif cash_flow > 500:
            recommendations.append(
                f"Positive cash flow of ${cash_flow:,.0f}/month. "
                "Self-funding investment from day one."
            )

        if gearing == "NEGATIVE":
            recommendations.append(
                "Negatively geared - tax benefits offset some holding costs. "
                "Review impact on serviceability for future borrowing."
            )

        recommendations.append(
            "Recommend obtaining Quantity Surveyor depreciation schedule. "
            "Can significantly improve after-tax cash flow."
        )

        return recommendations


# Convenience functions
def analyze_comparables(
    asking_price: float,
    land_size: float,
    comparable_sales: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Quick comparable sales analysis.
    """
    analyzer = ComparableSalesAnalyzer()
    result = analyzer.analyze(
        subject_property={
            "asking_price": asking_price,
            "land_size": land_size
        },
        comparable_sales=comparable_sales
    )
    return result.to_dict()


def calculate_investor_cash_flow(
    purchase_price: float,
    weekly_rent: float,
    council_rates: float = 2400,
    water_rates: float = 800,
    strata_quarterly: float = 0
) -> Dict[str, Any]:
    """
    Quick investor cash flow calculation.
    """
    model = InvestorCashFlowModel()
    result = model.calculate(
        purchase_price=purchase_price,
        weekly_rent=weekly_rent,
        outgoings={
            "council_rates": council_rates,
            "water_rates": water_rates,
            "strata_levies": strata_quarterly
        }
    )
    return result.to_dict()
