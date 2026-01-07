"""
Portfolio alignment module.

Matches properties against client briefs and portfolio criteria.
"""

from .alignment import (
    PortfolioAligner,
    ClientBrief,
    AlignmentResult,
    calculate_alignment_score
)

__all__ = [
    "PortfolioAligner",
    "ClientBrief",
    "AlignmentResult",
    "calculate_alignment_score"
]
