"""
ABS Census Demographics Module.

Provides demographic data for property investment analysis including:
- Population statistics
- Age distribution
- Household composition
- Income levels
- Employment statistics
- Housing tenure (renters vs owners)
"""

from .abs_census import (
    ABSCensusClient,
    get_abs_client,
    get_suburb_demographics,
    get_demographics_score,
    DemographicProfile,
    DemographicScore
)

__all__ = [
    "ABSCensusClient",
    "get_abs_client",
    "get_suburb_demographics",
    "get_demographics_score",
    "DemographicProfile",
    "DemographicScore"
]
