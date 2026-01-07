"""
ABS Census Data Client.

Provides demographic data from Australian Bureau of Statistics Census data.

Data sources:
- ABS Census 2021 (latest available)
- ABS Census TableBuilder or data.gov.au
- QuickStats suburb profiles

Note: Full ABS API requires registration and has usage limits.
This module provides:
1. Mock data for development
2. Placeholder for ABS.Stat/DataPacks integration
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import httpx
import asyncio


class RentalDemand(str, Enum):
    """Rental demand classification."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class InvestorAppeal(str, Enum):
    """Investor appeal classification."""
    PREMIUM = "premium"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


@dataclass
class PopulationStats:
    """Population statistics."""
    total_population: int = 0
    population_growth_5_year: float = 0.0  # Percentage
    population_density: float = 0.0  # Per sq km

    # Age distribution
    median_age: float = 0.0
    age_0_14_percent: float = 0.0
    age_15_24_percent: float = 0.0
    age_25_44_percent: float = 0.0
    age_45_64_percent: float = 0.0
    age_65_plus_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_population": self.total_population,
            "population_growth_5_year": self.population_growth_5_year,
            "population_density": self.population_density,
            "median_age": self.median_age,
            "age_distribution": {
                "0_14": self.age_0_14_percent,
                "15_24": self.age_15_24_percent,
                "25_44": self.age_25_44_percent,
                "45_64": self.age_45_64_percent,
                "65_plus": self.age_65_plus_percent
            }
        }


@dataclass
class HouseholdStats:
    """Household composition statistics."""
    total_households: int = 0
    average_household_size: float = 0.0

    # Household types
    family_households_percent: float = 0.0
    lone_person_percent: float = 0.0
    group_households_percent: float = 0.0

    # Family types
    couples_with_children_percent: float = 0.0
    couples_no_children_percent: float = 0.0
    single_parent_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_households": self.total_households,
            "average_household_size": self.average_household_size,
            "household_types": {
                "family": self.family_households_percent,
                "lone_person": self.lone_person_percent,
                "group": self.group_households_percent
            },
            "family_composition": {
                "couples_with_children": self.couples_with_children_percent,
                "couples_no_children": self.couples_no_children_percent,
                "single_parent": self.single_parent_percent
            }
        }


@dataclass
class IncomeStats:
    """Income and employment statistics."""
    median_weekly_household_income: float = 0.0
    median_weekly_personal_income: float = 0.0

    # Income distribution
    low_income_percent: float = 0.0      # <$650/week
    middle_income_percent: float = 0.0    # $650-$2000/week
    high_income_percent: float = 0.0      # >$2000/week

    # Employment
    employment_rate: float = 0.0
    unemployment_rate: float = 0.0
    professional_occupation_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "median_weekly_household_income": self.median_weekly_household_income,
            "median_weekly_personal_income": self.median_weekly_personal_income,
            "income_distribution": {
                "low": self.low_income_percent,
                "middle": self.middle_income_percent,
                "high": self.high_income_percent
            },
            "employment": {
                "employment_rate": self.employment_rate,
                "unemployment_rate": self.unemployment_rate,
                "professional_percent": self.professional_occupation_percent
            }
        }


@dataclass
class HousingStats:
    """Housing tenure and type statistics."""
    total_dwellings: int = 0

    # Tenure
    owner_occupied_percent: float = 0.0
    owner_with_mortgage_percent: float = 0.0
    rented_percent: float = 0.0
    social_housing_percent: float = 0.0

    # Dwelling types
    houses_percent: float = 0.0
    townhouses_percent: float = 0.0
    apartments_percent: float = 0.0

    # Rental market
    median_weekly_rent: float = 0.0
    median_mortgage_payment: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_dwellings": self.total_dwellings,
            "tenure": {
                "owner_occupied": self.owner_occupied_percent,
                "owner_with_mortgage": self.owner_with_mortgage_percent,
                "rented": self.rented_percent,
                "social_housing": self.social_housing_percent
            },
            "dwelling_types": {
                "houses": self.houses_percent,
                "townhouses": self.townhouses_percent,
                "apartments": self.apartments_percent
            },
            "costs": {
                "median_weekly_rent": self.median_weekly_rent,
                "median_mortgage_payment": self.median_mortgage_payment
            }
        }


@dataclass
class DemographicProfile:
    """Complete demographic profile for a suburb."""
    suburb: str
    state: str = "VIC"
    postcode: str = ""
    census_year: int = 2021

    population: PopulationStats = field(default_factory=PopulationStats)
    households: HouseholdStats = field(default_factory=HouseholdStats)
    income: IncomeStats = field(default_factory=IncomeStats)
    housing: HousingStats = field(default_factory=HousingStats)

    # Derived insights
    rental_demand: RentalDemand = RentalDemand.MODERATE
    investor_appeal: InvestorAppeal = InvestorAppeal.MODERATE
    growth_potential: str = "moderate"

    key_insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suburb": self.suburb,
            "state": self.state,
            "postcode": self.postcode,
            "census_year": self.census_year,
            "population": self.population.to_dict(),
            "households": self.households.to_dict(),
            "income": self.income.to_dict(),
            "housing": self.housing.to_dict(),
            "analysis": {
                "rental_demand": self.rental_demand.value,
                "investor_appeal": self.investor_appeal.value,
                "growth_potential": self.growth_potential,
                "key_insights": self.key_insights
            }
        }


@dataclass
class DemographicScore:
    """Demographic scoring for investment analysis."""
    suburb: str
    overall_score: float = 50.0  # 0-100

    # Component scores
    income_score: float = 50.0
    employment_score: float = 50.0
    rental_demand_score: float = 50.0
    growth_score: float = 50.0
    stability_score: float = 50.0

    # Investment indicators
    renter_proportion: float = 0.0
    income_rental_ratio: float = 0.0  # Income vs rent
    young_professional_index: float = 0.0

    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    investment_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suburb": self.suburb,
            "overall_score": round(self.overall_score, 1),
            "component_scores": {
                "income": round(self.income_score, 1),
                "employment": round(self.employment_score, 1),
                "rental_demand": round(self.rental_demand_score, 1),
                "growth": round(self.growth_score, 1),
                "stability": round(self.stability_score, 1)
            },
            "investment_indicators": {
                "renter_proportion": round(self.renter_proportion, 1),
                "income_rental_ratio": round(self.income_rental_ratio, 2),
                "young_professional_index": round(self.young_professional_index, 1)
            },
            "strengths": self.strengths,
            "concerns": self.concerns,
            "investment_notes": self.investment_notes
        }


# Melbourne suburb demographic profiles (2021 Census approximations)
# Source: ABS QuickStats
MELBOURNE_SUBURB_DATA = {
    "richmond": {
        "population": 30000, "growth": 15.2, "median_age": 33,
        "median_income": 2100, "rented_percent": 52, "median_rent": 450,
        "unemployment": 4.5, "professionals": 58
    },
    "brunswick": {
        "population": 28000, "growth": 12.8, "median_age": 32,
        "median_income": 1850, "rented_percent": 48, "median_rent": 420,
        "unemployment": 5.2, "professionals": 52
    },
    "south yarra": {
        "population": 26000, "growth": 8.5, "median_age": 34,
        "median_income": 2400, "rented_percent": 55, "median_rent": 520,
        "unemployment": 3.8, "professionals": 62
    },
    "footscray": {
        "population": 18000, "growth": 18.5, "median_age": 31,
        "median_income": 1450, "rented_percent": 46, "median_rent": 380,
        "unemployment": 6.8, "professionals": 42
    },
    "carlton": {
        "population": 18500, "growth": 5.2, "median_age": 28,
        "median_income": 1200, "rented_percent": 68, "median_rent": 400,
        "unemployment": 7.5, "professionals": 38
    },
    "fitzroy": {
        "population": 12000, "growth": 6.8, "median_age": 35,
        "median_income": 2200, "rented_percent": 48, "median_rent": 480,
        "unemployment": 4.2, "professionals": 60
    },
    "collingwood": {
        "population": 10000, "growth": 12.5, "median_age": 33,
        "median_income": 1900, "rented_percent": 50, "median_rent": 440,
        "unemployment": 5.0, "professionals": 55
    },
    "northcote": {
        "population": 25000, "growth": 10.2, "median_age": 36,
        "median_income": 2050, "rented_percent": 38, "median_rent": 450,
        "unemployment": 4.0, "professionals": 55
    },
    "thornbury": {
        "population": 19000, "growth": 11.5, "median_age": 35,
        "median_income": 1900, "rented_percent": 35, "median_rent": 420,
        "unemployment": 4.5, "professionals": 50
    },
    "preston": {
        "population": 35000, "growth": 14.8, "median_age": 34,
        "median_income": 1650, "rented_percent": 32, "median_rent": 400,
        "unemployment": 5.5, "professionals": 45
    },
    "box hill": {
        "population": 13000, "growth": 22.5, "median_age": 32,
        "median_income": 1350, "rented_percent": 58, "median_rent": 380,
        "unemployment": 6.0, "professionals": 42
    },
    "glen waverley": {
        "population": 42000, "growth": 8.5, "median_age": 40,
        "median_income": 2100, "rented_percent": 22, "median_rent": 450,
        "unemployment": 4.2, "professionals": 55
    },
    "brighton": {
        "population": 24000, "growth": 3.2, "median_age": 42,
        "median_income": 2800, "rented_percent": 18, "median_rent": 650,
        "unemployment": 3.0, "professionals": 68
    },
    "st kilda": {
        "population": 22000, "growth": 6.5, "median_age": 35,
        "median_income": 1750, "rented_percent": 58, "median_rent": 420,
        "unemployment": 5.5, "professionals": 52
    },
    "coburg": {
        "population": 28000, "growth": 12.0, "median_age": 35,
        "median_income": 1700, "rented_percent": 35, "median_rent": 400,
        "unemployment": 5.8, "professionals": 48
    },
    "yarraville": {
        "population": 15000, "growth": 8.8, "median_age": 36,
        "median_income": 2000, "rented_percent": 32, "median_rent": 450,
        "unemployment": 4.5, "professionals": 55
    },
    "seddon": {
        "population": 6500, "growth": 10.2, "median_age": 35,
        "median_income": 1950, "rented_percent": 30, "median_rent": 440,
        "unemployment": 4.2, "professionals": 54
    },
    "williamstown": {
        "population": 14000, "growth": 5.5, "median_age": 40,
        "median_income": 2200, "rented_percent": 25, "median_rent": 480,
        "unemployment": 3.8, "professionals": 58
    },
    "werribee": {
        "population": 45000, "growth": 25.5, "median_age": 32,
        "median_income": 1400, "rented_percent": 28, "median_rent": 350,
        "unemployment": 7.2, "professionals": 35
    },
    "point cook": {
        "population": 62000, "growth": 35.0, "median_age": 31,
        "median_income": 1800, "rented_percent": 25, "median_rent": 400,
        "unemployment": 5.5, "professionals": 48
    },
    "craigieburn": {
        "population": 58000, "growth": 28.5, "median_age": 30,
        "median_income": 1550, "rented_percent": 22, "median_rent": 380,
        "unemployment": 6.5, "professionals": 38
    },
    "frankston": {
        "population": 38000, "growth": 8.2, "median_age": 38,
        "median_income": 1350, "rented_percent": 35, "median_rent": 380,
        "unemployment": 7.0, "professionals": 35
    },
    "dandenong": {
        "population": 32000, "growth": 10.5, "median_age": 34,
        "median_income": 1150, "rented_percent": 38, "median_rent": 350,
        "unemployment": 8.5, "professionals": 28
    },
    "toorak": {
        "population": 14000, "growth": 2.5, "median_age": 45,
        "median_income": 3500, "rented_percent": 22, "median_rent": 750,
        "unemployment": 2.5, "professionals": 72
    },
    "hawthorn": {
        "population": 24000, "growth": 5.8, "median_age": 38,
        "median_income": 2400, "rented_percent": 35, "median_rent": 520,
        "unemployment": 3.5, "professionals": 65
    },
    "kew": {
        "population": 26000, "growth": 4.5, "median_age": 40,
        "median_income": 2600, "rented_percent": 25, "median_rent": 550,
        "unemployment": 3.2, "professionals": 66
    },
    "camberwell": {
        "population": 22000, "growth": 3.8, "median_age": 42,
        "median_income": 2500, "rented_percent": 22, "median_rent": 520,
        "unemployment": 3.0, "professionals": 65
    },
    "malvern": {
        "population": 12000, "growth": 4.2, "median_age": 43,
        "median_income": 2700, "rented_percent": 28, "median_rent": 580,
        "unemployment": 2.8, "professionals": 68
    },
    "armadale": {
        "population": 10000, "growth": 5.5, "median_age": 41,
        "median_income": 2600, "rented_percent": 32, "median_rent": 560,
        "unemployment": 3.0, "professionals": 66
    },
    "elwood": {
        "population": 16000, "growth": 4.8, "median_age": 36,
        "median_income": 2100, "rented_percent": 45, "median_rent": 480,
        "unemployment": 4.0, "professionals": 58
    },
    "port melbourne": {
        "population": 18000, "growth": 15.5, "median_age": 34,
        "median_income": 2300, "rented_percent": 48, "median_rent": 500,
        "unemployment": 4.2, "professionals": 60
    },
    "south melbourne": {
        "population": 12000, "growth": 12.0, "median_age": 35,
        "median_income": 2200, "rented_percent": 52, "median_rent": 480,
        "unemployment": 4.5, "professionals": 58
    },
    "albert park": {
        "population": 6500, "growth": 5.2, "median_age": 38,
        "median_income": 2500, "rented_percent": 38, "median_rent": 550,
        "unemployment": 3.5, "professionals": 64
    },
    "middle park": {
        "population": 5000, "growth": 3.8, "median_age": 40,
        "median_income": 2600, "rented_percent": 35, "median_rent": 580,
        "unemployment": 3.2, "professionals": 65
    }
}


class ABSCensusClient:
    """
    Client for ABS Census demographic data.

    Uses pre-cached data for Melbourne suburbs with option to
    extend to ABS API integration.
    """

    def __init__(self, use_mock: bool = True):
        """
        Initialize ABS Census client.

        Args:
            use_mock: Use mock data (default True for development)
        """
        self.use_mock = use_mock
        self.suburb_data = MELBOURNE_SUBURB_DATA
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_suburb_profile(
        self,
        suburb: str,
        state: str = "VIC"
    ) -> DemographicProfile:
        """
        Get demographic profile for a suburb.

        Args:
            suburb: Suburb name
            state: State code (default VIC)

        Returns:
            DemographicProfile with census data
        """
        suburb_key = suburb.lower().strip()

        # Check for cached data
        if suburb_key in self.suburb_data:
            return self._build_profile_from_cached(suburb, suburb_key)

        # Return default profile for unknown suburbs
        return self._build_default_profile(suburb)

    def _build_profile_from_cached(
        self,
        suburb: str,
        suburb_key: str
    ) -> DemographicProfile:
        """Build profile from cached suburb data."""
        data = self.suburb_data[suburb_key]

        # Build population stats
        population = PopulationStats(
            total_population=data["population"],
            population_growth_5_year=data["growth"],
            median_age=data["median_age"],
            age_25_44_percent=35.0,  # Typical estimate
            age_45_64_percent=25.0
        )

        # Build household stats
        households = HouseholdStats(
            total_households=int(data["population"] / 2.4),
            average_household_size=2.4
        )

        # Build income stats
        income = IncomeStats(
            median_weekly_household_income=data["median_income"],
            median_weekly_personal_income=data["median_income"] * 0.6,
            unemployment_rate=data["unemployment"],
            employment_rate=100 - data["unemployment"] - 35,  # Approx participation
            professional_occupation_percent=data["professionals"]
        )

        # Build housing stats
        housing = HousingStats(
            total_dwellings=int(data["population"] / 2.4),
            rented_percent=data["rented_percent"],
            owner_occupied_percent=100 - data["rented_percent"] - 5,
            median_weekly_rent=data["median_rent"]
        )

        # Derive rental demand
        if data["rented_percent"] > 45:
            rental_demand = RentalDemand.HIGH
        elif data["rented_percent"] > 30:
            rental_demand = RentalDemand.MODERATE
        else:
            rental_demand = RentalDemand.LOW

        # Derive investor appeal
        if data["median_income"] > 2000 and data["growth"] > 10:
            investor_appeal = InvestorAppeal.PREMIUM
        elif data["median_income"] > 1600 or data["growth"] > 8:
            investor_appeal = InvestorAppeal.STRONG
        elif data["unemployment"] > 7:
            investor_appeal = InvestorAppeal.WEAK
        else:
            investor_appeal = InvestorAppeal.MODERATE

        # Growth potential
        if data["growth"] > 15:
            growth_potential = "high"
        elif data["growth"] > 8:
            growth_potential = "moderate"
        else:
            growth_potential = "low"

        # Key insights
        insights = []
        if data["growth"] > 10:
            insights.append(f"Strong population growth ({data['growth']:.1f}% over 5 years)")
        if data["professionals"] > 50:
            insights.append(f"High professional workforce ({data['professionals']}%)")
        if data["rented_percent"] > 40:
            insights.append(f"Strong rental market ({data['rented_percent']}% renting)")
        if data["unemployment"] < 4:
            insights.append(f"Low unemployment ({data['unemployment']}%)")
        if data["unemployment"] > 7:
            insights.append(f"Higher unemployment ({data['unemployment']}%)")
        if data["median_income"] > 2000:
            insights.append(f"Above average household income (${data['median_income']}/week)")

        return DemographicProfile(
            suburb=suburb,
            state="VIC",
            census_year=2021,
            population=population,
            households=households,
            income=income,
            housing=housing,
            rental_demand=rental_demand,
            investor_appeal=investor_appeal,
            growth_potential=growth_potential,
            key_insights=insights
        )

    def _build_default_profile(self, suburb: str) -> DemographicProfile:
        """Build default profile for unknown suburbs."""
        # Use Melbourne metro averages
        population = PopulationStats(
            total_population=20000,
            population_growth_5_year=8.0,
            median_age=36,
            age_25_44_percent=30.0,
            age_45_64_percent=25.0
        )

        households = HouseholdStats(
            total_households=8000,
            average_household_size=2.5
        )

        income = IncomeStats(
            median_weekly_household_income=1700,
            median_weekly_personal_income=950,
            unemployment_rate=5.5,
            employment_rate=60,
            professional_occupation_percent=45
        )

        housing = HousingStats(
            total_dwellings=8000,
            rented_percent=32,
            owner_occupied_percent=63,
            median_weekly_rent=420
        )

        return DemographicProfile(
            suburb=suburb,
            state="VIC",
            census_year=2021,
            population=population,
            households=households,
            income=income,
            housing=housing,
            rental_demand=RentalDemand.MODERATE,
            investor_appeal=InvestorAppeal.MODERATE,
            growth_potential="moderate",
            key_insights=["Using Melbourne metro averages - specific data not available"]
        )

    async def calculate_demographic_score(
        self,
        suburb: str,
        investment_type: str = "residential"
    ) -> DemographicScore:
        """
        Calculate investment-focused demographic score.

        Args:
            suburb: Suburb name
            investment_type: residential, commercial, or development

        Returns:
            DemographicScore with investment analysis
        """
        profile = await self.get_suburb_profile(suburb)

        score = DemographicScore(suburb=suburb)

        # Income score (0-100)
        median_income = profile.income.median_weekly_household_income
        if median_income > 2500:
            score.income_score = 95
        elif median_income > 2000:
            score.income_score = 80
        elif median_income > 1500:
            score.income_score = 65
        elif median_income > 1200:
            score.income_score = 50
        else:
            score.income_score = 35

        # Employment score
        unemployment = profile.income.unemployment_rate
        if unemployment < 4:
            score.employment_score = 90
        elif unemployment < 5:
            score.employment_score = 75
        elif unemployment < 6:
            score.employment_score = 60
        elif unemployment < 7:
            score.employment_score = 45
        else:
            score.employment_score = 30

        # Rental demand score
        rented_pct = profile.housing.rented_percent
        if investment_type == "residential":
            # Higher rental % = higher demand
            if rented_pct > 50:
                score.rental_demand_score = 90
            elif rented_pct > 40:
                score.rental_demand_score = 80
            elif rented_pct > 30:
                score.rental_demand_score = 65
            elif rented_pct > 20:
                score.rental_demand_score = 50
            else:
                score.rental_demand_score = 35

        # Growth score
        growth = profile.population.population_growth_5_year
        if growth > 20:
            score.growth_score = 95
        elif growth > 12:
            score.growth_score = 80
        elif growth > 8:
            score.growth_score = 65
        elif growth > 5:
            score.growth_score = 50
        else:
            score.growth_score = 40

        # Stability score (inverse of volatility indicators)
        # High owner-occupation = more stable
        owner_pct = profile.housing.owner_occupied_percent
        professional_pct = profile.income.professional_occupation_percent

        stability = (owner_pct * 0.4 + professional_pct * 0.6)
        score.stability_score = min(100, stability * 1.5)

        # Calculate overall score
        weights = {
            "income": 0.25,
            "employment": 0.20,
            "rental_demand": 0.25,
            "growth": 0.15,
            "stability": 0.15
        }

        score.overall_score = (
            score.income_score * weights["income"] +
            score.employment_score * weights["employment"] +
            score.rental_demand_score * weights["rental_demand"] +
            score.growth_score * weights["growth"] +
            score.stability_score * weights["stability"]
        )

        # Investment indicators
        score.renter_proportion = rented_pct
        score.income_rental_ratio = (
            median_income / profile.housing.median_weekly_rent
            if profile.housing.median_weekly_rent > 0 else 0
        )

        # Young professional index (25-44 age group * professional %)
        young_adult_pct = profile.population.age_25_44_percent
        score.young_professional_index = (
            young_adult_pct * professional_pct / 100
        ) if young_adult_pct > 0 else 0

        # Strengths and concerns
        if score.income_score >= 75:
            score.strengths.append("Strong household incomes")
        if score.employment_score >= 75:
            score.strengths.append("Low unemployment")
        if score.rental_demand_score >= 75:
            score.strengths.append("Strong rental demand")
        if score.growth_score >= 75:
            score.strengths.append("Strong population growth")

        if score.income_score < 50:
            score.concerns.append("Below average incomes")
        if score.employment_score < 50:
            score.concerns.append("Higher unemployment")
        if score.rental_demand_score < 50 and investment_type == "residential":
            score.concerns.append("Lower rental demand")

        # Investment notes
        if score.overall_score >= 75:
            score.investment_notes.append(
                "Demographics strongly support investment"
            )
        elif score.overall_score >= 60:
            score.investment_notes.append(
                "Demographics moderately support investment"
            )
        else:
            score.investment_notes.append(
                "Demographics present some challenges"
            )

        if score.income_rental_ratio > 4:
            score.investment_notes.append(
                "Good income-to-rent ratio supports rental affordability"
            )
        elif score.income_rental_ratio < 3:
            score.investment_notes.append(
                "Tight income-to-rent ratio may impact tenant quality"
            )

        return score


# Singleton instance
_abs_client: Optional[ABSCensusClient] = None


def get_abs_client() -> ABSCensusClient:
    """Get or create ABS Census client singleton."""
    global _abs_client
    if _abs_client is None:
        _abs_client = ABSCensusClient()
    return _abs_client


# Convenience functions
async def get_suburb_demographics(suburb: str) -> Dict[str, Any]:
    """
    Get demographic profile for a suburb.

    Args:
        suburb: Suburb name

    Returns:
        Dict with demographic data
    """
    client = get_abs_client()
    profile = await client.get_suburb_profile(suburb)
    return profile.to_dict()


async def get_demographics_score(
    suburb: str,
    investment_type: str = "residential"
) -> Dict[str, Any]:
    """
    Get investment-focused demographic score.

    Args:
        suburb: Suburb name
        investment_type: Type of investment

    Returns:
        Dict with demographic score analysis
    """
    client = get_abs_client()
    score = await client.calculate_demographic_score(suburb, investment_type)
    return score.to_dict()
