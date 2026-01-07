"""
Crime Statistics Agency Victoria integration.

Provides suburb-level crime data for location risk assessment.
Data source: https://www.crimestatistics.vic.gov.au
"""

from .csa_vic import CrimeStatisticsClient, get_crime_client, get_suburb_crime_stats
from .models import SuburbCrimeStats, CrimeCategory, CrimeTrend

__all__ = [
    "CrimeStatisticsClient",
    "get_crime_client",
    "get_suburb_crime_stats",
    "SuburbCrimeStats",
    "CrimeCategory",
    "CrimeTrend"
]
