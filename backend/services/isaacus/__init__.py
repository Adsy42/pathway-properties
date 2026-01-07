"""
Isaacus Legal AI Integration.

Provides legal document classification using Isaacus Query Language (IQL).
https://docs.isaacus.com/
"""

from services.isaacus.client import IsaacusClient, ClassificationResult
from services.isaacus.classifier import LegalClauseClassifier
from services.isaacus.iql_templates import IQLTemplates

__all__ = [
    "IsaacusClient",
    "ClassificationResult",
    "LegalClauseClassifier",
    "IQLTemplates",
]




