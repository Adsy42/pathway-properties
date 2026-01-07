"""
Mining and Earth Resources (GeoVic) integration.

Provides access to mining tenements, exploration licenses, and quarry data.
Data source: GeoVic (Earth Resources)
"""

from .geovic import GeoVicClient, get_geovic_client, check_mining_tenements
from .models import MiningTenement, MiningRiskAssessment

__all__ = [
    "GeoVicClient",
    "get_geovic_client",
    "check_mining_tenements",
    "MiningTenement",
    "MiningRiskAssessment"
]
