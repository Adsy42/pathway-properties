"""
EPA Victoria contamination and environmental risk services.

Data sources:
- Priority Sites Register (PSR)
- Victoria Unearthed portal
- Environmental audits database
"""

from .priority_sites import EPAClient, get_epa_client, check_contamination_risk
from .models import ContaminatedSite, ContaminationRiskAssessment

__all__ = [
    "EPAClient",
    "get_epa_client",
    "check_contamination_risk",
    "ContaminatedSite",
    "ContaminationRiskAssessment"
]
