"""
Heritage Victoria API integration.

Provides access to the Victorian Heritage Register for heritage place lookups.
"""

from .client import HeritageVictoriaClient, get_heritage_client
from .models import HeritagePlace, HeritageSearchResult

__all__ = [
    "HeritageVictoriaClient",
    "get_heritage_client",
    "HeritagePlace",
    "HeritageSearchResult"
]
