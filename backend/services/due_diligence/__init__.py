"""
Due Diligence Enhancement Modules for Pathway Property.

This package contains comprehensive due diligence analysis tools for
Victorian (and NSW) property transactions, implementing professional
buyer's agency standards.

Modules:
- section32: Section 32 completeness and validity checking
- cooling_off: Cooling-off period calculation and tracking
- special_conditions: Contract special conditions analyzer
- title: Title, easement, covenant, and caveat analysis
- planning: Zoning, overlays, and development potential
- strata: Strata/OC financial health and cladding risk
- environmental: Contamination and environmental risk
- financial: Cash flow modeling and comparable sales
- risk_scoring: Weighted risk scoring framework
- compliance: Regulatory compliance tracking
- timeline: Due diligence process orchestration
"""

from .section32 import Section32CompletenessAnalyzer
from .cooling_off import CoolingOffCalculator
from .special_conditions import SpecialConditionsAnalyzer
from .title_analysis import (
    ProprietorMismatchDetector,
    EasementImpactAnalyzer,
    CovenantAnalyzer,
    CaveatClassifier,
    Section173Analyzer
)
from .stamp_duty import VictorianStampDutyCalculator
from .planning import (
    ZoneDevelopmentAnalyzer,
    BuildingPermitAnalyzer
)
from .strata import (
    CladdingRiskAssessor,
    StrataFinancialAnalyzer,
    ByLawAnalyzer
)
from .environmental import ContaminationAssessor
from .financial import (
    ComparableSalesAnalyzer,
    InvestorCashFlowModel
)
from .risk_scoring import PropertyRiskScorer
from .compliance import (
    StatementOfInformationAnalyzer,
    DueDiligenceComplianceTracker
)
from .timeline import DueDiligenceTimeline
from .specialist_referrals import SpecialistReferralEngine

__all__ = [
    # Section 32
    'Section32CompletenessAnalyzer',

    # Cooling Off
    'CoolingOffCalculator',

    # Special Conditions
    'SpecialConditionsAnalyzer',

    # Title Analysis
    'ProprietorMismatchDetector',
    'EasementImpactAnalyzer',
    'CovenantAnalyzer',
    'CaveatClassifier',
    'Section173Analyzer',

    # Stamp Duty
    'VictorianStampDutyCalculator',

    # Planning
    'ZoneDevelopmentAnalyzer',
    'BuildingPermitAnalyzer',

    # Strata
    'CladdingRiskAssessor',
    'StrataFinancialAnalyzer',
    'ByLawAnalyzer',

    # Environmental
    'ContaminationAssessor',

    # Financial
    'ComparableSalesAnalyzer',
    'InvestorCashFlowModel',

    # Risk Scoring
    'PropertyRiskScorer',

    # Compliance
    'StatementOfInformationAnalyzer',
    'DueDiligenceComplianceTracker',

    # Timeline
    'DueDiligenceTimeline',

    # Specialist Referrals
    'SpecialistReferralEngine',
]
