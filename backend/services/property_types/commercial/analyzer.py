"""
Commercial property analyzer.

Provides analysis for commercial property investments including:
- Cap rate calculation
- WALE (Weighted Average Lease Expiry)
- Tenant covenant assessment
- Net yield calculation
"""

from typing import Optional, List, Dict, Any
from datetime import date

from .models import (
    CommercialAssessment,
    LeaseDetails,
    TenantProfile,
    TenantStrength,
    LeaseType
)


class CommercialPropertyAnalyzer:
    """
    Analyzer for commercial property investments.

    Calculates key metrics including cap rate, WALE, and tenant risk.
    """

    # Market cap rates by property type and location (Melbourne 2024)
    MARKET_CAP_RATES = {
        "retail": {
            "prime": {"min": 4.5, "mid": 5.5, "max": 6.5},
            "secondary": {"min": 5.5, "mid": 6.5, "max": 8.0},
            "regional": {"min": 6.0, "mid": 7.5, "max": 9.0}
        },
        "office": {
            "prime": {"min": 5.0, "mid": 6.0, "max": 7.0},
            "secondary": {"min": 6.0, "mid": 7.5, "max": 9.0},
            "regional": {"min": 7.0, "mid": 8.5, "max": 10.0}
        },
        "industrial": {
            "prime": {"min": 4.0, "mid": 5.0, "max": 6.0},
            "secondary": {"min": 5.0, "mid": 6.0, "max": 7.5},
            "regional": {"min": 6.0, "mid": 7.0, "max": 8.5}
        }
    }

    # Tenant strength risk factors
    TENANT_RISK_SCORES = {
        TenantStrength.NATIONAL: 90,
        TenantStrength.REGIONAL: 70,
        TenantStrength.LOCAL: 50,
        TenantStrength.STARTUP: 30,
        TenantStrength.UNKNOWN: 40
    }

    def analyze(
        self,
        address: str,
        property_type: str,
        purchase_price: float,
        leases: Optional[List[LeaseDetails]] = None,
        building_area_sqm: Optional[float] = None,
        land_area_sqm: Optional[float] = None,
        annual_outgoings: Optional[float] = None,
        zone_code: Optional[str] = None,
        location_grade: str = "secondary"  # prime, secondary, regional
    ) -> CommercialAssessment:
        """
        Perform comprehensive commercial property analysis.

        Args:
            address: Property address
            property_type: Type (retail, office, industrial, mixed)
            purchase_price: Purchase price
            leases: List of lease details
            building_area_sqm: Building area
            land_area_sqm: Land area
            annual_outgoings: Annual outgoings if known
            zone_code: Planning zone code
            location_grade: prime, secondary, or regional

        Returns:
            CommercialAssessment
        """
        leases = leases or []
        strengths = []
        weaknesses = []
        recommendations = []
        tenant_risks = []

        # Calculate income
        total_rent = sum(l.current_rent_annual for l in leases)
        total_outgoings = annual_outgoings or sum(l.outgoings_annual or 0 for l in leases)

        # Estimate outgoings if not provided
        if not total_outgoings and building_area_sqm:
            outgoings_per_sqm = {"retail": 80, "office": 100, "industrial": 40}
            total_outgoings = building_area_sqm * outgoings_per_sqm.get(property_type.lower(), 70)

        net_income = total_rent - total_outgoings

        # Calculate vacancy
        if building_area_sqm and leases:
            leased_area = sum(getattr(l, 'area_sqm', 0) or 0 for l in leases)
            if leased_area > 0:
                vacancy_rate = max(0, (building_area_sqm - leased_area) / building_area_sqm * 100)
            else:
                vacancy_rate = 0 if leases else 100
        else:
            vacancy_rate = 0 if leases else 100

        is_fully_leased = vacancy_rate == 0 and len(leases) > 0

        # Calculate yields
        cap_rate = (net_income / purchase_price * 100) if purchase_price > 0 else None
        passing_yield = (total_rent / purchase_price * 100) if purchase_price > 0 else None

        # Calculate WALE
        wale = self._calculate_wale(leases)
        wale_by_income = self._calculate_wale_by_income(leases)

        # Tenant risk analysis
        tenant_score, tenant_risks = self._assess_tenant_risk(leases)

        # Get market cap rate for comparison
        market_cap = self._get_market_cap_rate(property_type.lower(), location_grade)

        if cap_rate and market_cap:
            cap_diff = cap_rate - market_cap["mid"]
            if cap_diff > 1:
                cap_comparison = f"Cap rate {cap_rate:.1f}% is {cap_diff:.1f}% above market ({market_cap['mid']:.1f}%) - potential value opportunity or risk premium"
            elif cap_diff < -0.5:
                cap_comparison = f"Cap rate {cap_rate:.1f}% is below market ({market_cap['mid']:.1f}%) - premium pricing"
            else:
                cap_comparison = f"Cap rate {cap_rate:.1f}% is in line with market ({market_cap['mid']:.1f}%)"
        else:
            cap_comparison = "Unable to compare to market"

        # Assess strengths and weaknesses
        if is_fully_leased:
            strengths.append("Fully leased property")
        elif vacancy_rate > 20:
            weaknesses.append(f"High vacancy rate ({vacancy_rate:.1f}%)")

        if wale and wale > 5:
            strengths.append(f"Strong WALE of {wale:.1f} years")
        elif wale and wale < 2:
            weaknesses.append(f"Short WALE of {wale:.1f} years - re-leasing risk")
            recommendations.append("Budget for tenant incentives at lease expiry")

        if tenant_score >= 70:
            strengths.append("Strong tenant covenant")
        elif tenant_score < 40:
            weaknesses.append("Weak tenant covenant - default risk")
            recommendations.append("Consider rent guarantee or additional security")

        # Check for national tenants
        national_tenants = [l for l in leases if l.tenant.tenant_strength == TenantStrength.NATIONAL]
        if national_tenants:
            strengths.append(f"{len(national_tenants)} national tenant(s)")

        # Lease expiry concentration
        if leases:
            expiry_years = [l.years_remaining() for l in leases if l.years_remaining()]
            expiries_within_2_years = sum(1 for y in expiry_years if y and y < 2)
            if expiries_within_2_years > len(leases) * 0.5:
                weaknesses.append("Multiple leases expiring within 2 years")
                recommendations.append("Negotiate lease renewals early")

        # Determine risk level
        if vacancy_rate > 30 or tenant_score < 30 or (wale and wale < 1):
            risk_level = "high"
        elif vacancy_rate > 10 or tenant_score < 50 or (wale and wale < 2):
            risk_level = "medium"
        else:
            risk_level = "low"

        # Add general recommendations
        if not recommendations:
            recommendations.append("Property presents as sound commercial investment")

        return CommercialAssessment(
            property_address=address,
            property_type=property_type,
            leases=leases,
            is_fully_leased=is_fully_leased,
            vacancy_rate=vacancy_rate,
            total_annual_rent=total_rent,
            total_annual_outgoings=total_outgoings,
            net_annual_income=net_income,
            cap_rate=cap_rate,
            net_yield=cap_rate,  # Same as cap rate for net income
            passing_yield=passing_yield,
            wale_years=wale,
            wale_by_income=wale_by_income,
            tenant_risk_score=tenant_score,
            key_tenant_risks=tenant_risks,
            current_use_permitted=True,  # Would check against zone
            zoning_issues=[],
            market_cap_rate=market_cap["mid"] if market_cap else None,
            cap_rate_comparison=cap_comparison,
            risk_level=risk_level,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _calculate_wale(self, leases: List[LeaseDetails]) -> Optional[float]:
        """
        Calculate simple WALE (years).

        Simple average of remaining lease terms.
        """
        if not leases:
            return None

        remaining_years = []
        for lease in leases:
            years = lease.years_remaining()
            if years is not None:
                remaining_years.append(years)

        if not remaining_years:
            return None

        return sum(remaining_years) / len(remaining_years)

    def _calculate_wale_by_income(self, leases: List[LeaseDetails]) -> Optional[float]:
        """
        Calculate income-weighted WALE (years).

        Weights each lease by its contribution to total income.
        """
        if not leases:
            return None

        total_rent = sum(l.current_rent_annual for l in leases)
        if total_rent == 0:
            return None

        weighted_sum = 0
        for lease in leases:
            years = lease.years_remaining()
            if years is not None:
                weight = lease.current_rent_annual / total_rent
                weighted_sum += years * weight

        return weighted_sum

    def _assess_tenant_risk(self, leases: List[LeaseDetails]) -> tuple:
        """
        Assess tenant risk across all leases.

        Returns:
            (risk_score, list of risk factors)
        """
        if not leases:
            return 0, ["No tenants - vacant property"]

        risks = []
        scores = []
        total_rent = sum(l.current_rent_annual for l in leases)

        for lease in leases:
            tenant = lease.tenant
            strength = tenant.tenant_strength

            # Base score from tenant strength
            score = self.TENANT_RISK_SCORES.get(strength, 40)

            # Adjust for lease security
            if lease.bank_guarantee_months >= 6:
                score += 5
            if lease.personal_guarantee:
                score += 5

            # Adjust for lease term
            years_remaining = lease.years_remaining()
            if years_remaining and years_remaining < 1:
                score -= 10
                risks.append(f"{tenant.name}: Lease expires in <1 year")
            elif years_remaining and years_remaining < 2:
                score -= 5

            # Weight by income contribution
            if total_rent > 0:
                weight = lease.current_rent_annual / total_rent
                scores.append(score * weight)
            else:
                scores.append(score)

            # Add specific risks
            if strength == TenantStrength.STARTUP:
                risks.append(f"{tenant.name}: Startup tenant - higher default risk")
            if strength == TenantStrength.UNKNOWN:
                risks.append(f"{tenant.name}: Unknown tenant covenant")

        final_score = sum(scores) if scores else 0
        return min(100, max(0, final_score)), risks

    def _get_market_cap_rate(
        self,
        property_type: str,
        location_grade: str
    ) -> Optional[Dict[str, float]]:
        """Get market cap rate range for property type and location."""
        type_rates = self.MARKET_CAP_RATES.get(property_type.lower())
        if not type_rates:
            type_rates = self.MARKET_CAP_RATES.get("retail")  # Default

        return type_rates.get(location_grade, type_rates.get("secondary"))
