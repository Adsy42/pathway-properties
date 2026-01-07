"""
Victorian school catchments and education data.

Data source: data.vic.gov.au - Victorian government school zones
"""

from .catchments import SchoolCatchmentClient, get_school_client, get_school_catchments
from .models import School, SchoolCatchment, SchoolsAssessment

__all__ = [
    "SchoolCatchmentClient",
    "get_school_client",
    "get_school_catchments",
    "School",
    "SchoolCatchment",
    "SchoolsAssessment"
]
