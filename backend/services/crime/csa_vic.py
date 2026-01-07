"""
Crime Statistics Agency Victoria client.

Data is downloaded from crimestatistics.vic.gov.au and cached locally.
The data is updated quarterly.

Note: This uses pre-downloaded CSV/Excel data stored locally.
For production, implement scheduled data refresh.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import os

from .models import (
    SuburbCrimeStats,
    CrimeCategoryStats,
    CrimeCategory,
    CrimeTrend,
    CrimeRiskAssessment
)


class CrimeStatisticsClient:
    """
    Client for Victorian crime statistics data.

    Data is cached in a JSON file for fast lookups.
    The cache should be refreshed quarterly when CSA releases new data.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cache",
            "crime"
        )
        self._data: Optional[Dict[str, Any]] = None
        self._state_averages: Optional[Dict[str, float]] = None

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self) -> str:
        """Get path to crime data cache file."""
        return os.path.join(self.cache_dir, "crime_stats.json")

    def _load_data(self) -> Dict[str, Any]:
        """Load crime data from cache."""
        if self._data is not None:
            return self._data

        cache_path = self._get_cache_path()

        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    self._data = json.load(f)
                    return self._data
            except Exception as e:
                print(f"Error loading crime cache: {e}")

        # Return mock data if no cache exists
        self._data = self._get_mock_data()
        return self._data

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock crime data for common Victorian suburbs."""
        return {
            "metadata": {
                "year": 2024,
                "quarter": 3,
                "source": "Crime Statistics Agency Victoria (Mock)",
                "state_average_rate": 5800.0
            },
            "suburbs": {
                "MELBOURNE": {"total": 8500, "rate": 12500.0, "population": 68000},
                "SOUTHBANK": {"total": 2100, "rate": 9800.0, "population": 21500},
                "RICHMOND": {"total": 1850, "rate": 6200.0, "population": 29800},
                "SOUTH YARRA": {"total": 1400, "rate": 5100.0, "population": 27500},
                "ST KILDA": {"total": 2200, "rate": 8500.0, "population": 25900},
                "FITZROY": {"total": 980, "rate": 5800.0, "population": 16900},
                "CARLTON": {"total": 1100, "rate": 6100.0, "population": 18000},
                "BRUNSWICK": {"total": 1050, "rate": 4200.0, "population": 25000},
                "FOOTSCRAY": {"total": 1450, "rate": 7200.0, "population": 20100},
                "BOX HILL": {"total": 890, "rate": 4800.0, "population": 18500},
                "DONCASTER": {"total": 420, "rate": 2100.0, "population": 20000},
                "GLEN WAVERLEY": {"total": 580, "rate": 2400.0, "population": 24200},
                "BRIGHTON": {"total": 380, "rate": 1800.0, "population": 21100},
                "CAMBERWELL": {"total": 450, "rate": 2000.0, "population": 22500},
                "KEW": {"total": 520, "rate": 2300.0, "population": 22600},
                "HAWTHORN": {"total": 680, "rate": 2900.0, "population": 23400},
                "MALVERN": {"total": 410, "rate": 2100.0, "population": 19500},
                "TOORAK": {"total": 290, "rate": 1500.0, "population": 19300},
                "FRANKSTON": {"total": 2100, "rate": 5900.0, "population": 35600},
                "DANDENONG": {"total": 2800, "rate": 8200.0, "population": 34100},
                "WERRIBEE": {"total": 1650, "rate": 4100.0, "population": 40200},
                "CRAIGIEBURN": {"total": 980, "rate": 2800.0, "population": 35000},
                "POINT COOK": {"total": 620, "rate": 1400.0, "population": 44300},
                "TARNEIT": {"total": 850, "rate": 1600.0, "population": 53100},
                "GEELONG": {"total": 3200, "rate": 4500.0, "population": 71100},
                "BALLARAT": {"total": 2400, "rate": 4200.0, "population": 57100},
                "BENDIGO": {"total": 2100, "rate": 4000.0, "population": 52500}
            },
            "categories": {
                "crimes_against_person": 0.15,
                "property_damage": 0.35,
                "drug_offences": 0.12,
                "public_order": 0.18,
                "justice_procedures": 0.12,
                "other": 0.08
            }
        }

    def get_suburb_stats(self, suburb: str) -> Optional[SuburbCrimeStats]:
        """
        Get crime statistics for a suburb.

        Args:
            suburb: Suburb name (case insensitive)

        Returns:
            SuburbCrimeStats if found, None otherwise
        """
        data = self._load_data()
        suburb_upper = suburb.upper().strip()

        suburb_data = data.get("suburbs", {}).get(suburb_upper)
        if not suburb_data:
            return None

        metadata = data.get("metadata", {})
        categories_pct = data.get("categories", {})

        # Build category breakdowns
        total = suburb_data.get("total", 0)
        categories = []
        for cat_name, pct in categories_pct.items():
            try:
                cat_enum = CrimeCategory(cat_name)
                count = int(total * pct)
                categories.append(CrimeCategoryStats(
                    category=cat_enum,
                    incident_count=count,
                    rate_per_100k=suburb_data.get("rate", 0) * pct if suburb_data.get("rate") else None,
                    trend=CrimeTrend.STABLE
                ))
            except ValueError:
                pass

        # Determine risk level based on rate
        rate = suburb_data.get("rate", 0)
        state_avg = metadata.get("state_average_rate", 5800)

        if rate < state_avg * 0.5:
            risk_level = "LOW"
        elif rate < state_avg * 0.8:
            risk_level = "MODERATE"
        elif rate < state_avg * 1.2:
            risk_level = "ELEVATED"
        else:
            risk_level = "HIGH"

        vs_state = ((rate - state_avg) / state_avg * 100) if state_avg > 0 else None

        return SuburbCrimeStats(
            suburb=suburb,
            year=metadata.get("year", 2024),
            quarter=metadata.get("quarter"),
            population=suburb_data.get("population"),
            categories=categories,
            total_incidents=total,
            total_rate_per_100k=rate,
            overall_trend=CrimeTrend.STABLE,
            vs_state_average=vs_state,
            risk_level=risk_level
        )

    def assess_crime_risk(self, suburb: str) -> CrimeRiskAssessment:
        """
        Assess crime risk for a suburb.

        Args:
            suburb: Suburb name

        Returns:
            CrimeRiskAssessment with risk level and concerns
        """
        stats = self.get_suburb_stats(suburb)

        if not stats:
            return CrimeRiskAssessment(
                suburb=suburb,
                stats=None,
                risk_level="UNKNOWN",
                risk_score=50.0,
                key_concerns=["No crime data available for this suburb"],
                comparison_text="Crime statistics not available"
            )

        # Calculate risk score (0-100)
        # Based on rate per 100k compared to state average
        data = self._load_data()
        state_avg = data.get("metadata", {}).get("state_average_rate", 5800)

        if state_avg > 0 and stats.total_rate_per_100k:
            ratio = stats.total_rate_per_100k / state_avg
            # Convert to 0-100 scale where 50 = state average
            risk_score = min(100, max(0, ratio * 50))
        else:
            risk_score = 50.0

        # Identify key concerns
        concerns = []

        if stats.risk_level == "HIGH":
            concerns.append(f"Crime rate significantly above state average ({stats.vs_state_average:+.0f}%)")
        elif stats.risk_level == "ELEVATED":
            concerns.append(f"Crime rate above state average ({stats.vs_state_average:+.0f}%)")

        # Check specific category concerns
        for cat in stats.categories:
            if cat.category == CrimeCategory.CRIMES_AGAINST_PERSON:
                if cat.rate_per_100k and cat.rate_per_100k > 1000:
                    concerns.append("Elevated crimes against persons")
            elif cat.category == CrimeCategory.PROPERTY_DAMAGE:
                if cat.rate_per_100k and cat.rate_per_100k > 2500:
                    concerns.append("High property crime rate")

        # Generate comparison text
        if stats.vs_state_average:
            if stats.vs_state_average > 50:
                comparison = f"Crime rate is {stats.vs_state_average:.0f}% above Victorian average"
            elif stats.vs_state_average > 0:
                comparison = f"Crime rate is {stats.vs_state_average:.0f}% above Victorian average"
            elif stats.vs_state_average > -30:
                comparison = f"Crime rate is {abs(stats.vs_state_average):.0f}% below Victorian average"
            else:
                comparison = f"Crime rate is significantly below Victorian average ({abs(stats.vs_state_average):.0f}% lower)"
        else:
            comparison = "Comparison data not available"

        return CrimeRiskAssessment(
            suburb=suburb,
            stats=stats,
            risk_level=stats.risk_level,
            risk_score=risk_score,
            key_concerns=concerns if concerns else ["No significant concerns"],
            comparison_text=comparison
        )

    async def refresh_data(self):
        """
        Refresh crime data from CSA Victoria.

        In production, this would:
        1. Download latest Excel file from crimestatistics.vic.gov.au
        2. Parse and transform data
        3. Update local cache

        For now, this is a placeholder.
        """
        # TODO: Implement actual data download and parsing
        # The CSA website provides Excel files at:
        # https://www.crimestatistics.vic.gov.au/crime-statistics/latest-victorian-crime-data/download-data
        print("Crime data refresh not yet implemented - using cached/mock data")
        pass


# Singleton instance
_crime_client: Optional[CrimeStatisticsClient] = None


def get_crime_client() -> CrimeStatisticsClient:
    """Get or create crime statistics client instance."""
    global _crime_client
    if _crime_client is None:
        _crime_client = CrimeStatisticsClient()
    return _crime_client


async def get_suburb_crime_stats(suburb: str) -> CrimeRiskAssessment:
    """
    Convenience function to get crime risk assessment for a suburb.

    Args:
        suburb: Suburb name

    Returns:
        CrimeRiskAssessment
    """
    client = get_crime_client()
    return client.assess_crime_risk(suburb)
