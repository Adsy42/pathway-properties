"""
IQL (Isaacus Query Language) Templates for Australian Property Law.

Pre-built queries for common clause types in:
- Section 32 Vendor Statements (Victoria)
- Contracts for Sale (NSW and other states)
- Strata/OC documents

IQL Syntax Reference (from https://docs.isaacus.com/iql/introduction):
- Statements: {This is a confidentiality clause.}
- Templates: {IS confidentiality clause}
- Template with arg: {IS clause that "description"} - NOTE: DOUBLE QUOTES required!
- Operators: AND, OR, NOT, >, <, +
- Precedence: () > + > >, < > NOT > AND > OR

Available Templates (from https://docs.isaacus.com/iql/templates):
- {IS clause that "<description>"}
- {IS clause obligating "<party name>"}
- {IS clause entitling "<party name>"}
- {IS clause called "<clause name>"}
- {IS termination clause}
- {IS indemnity clause}
- {IS liability limitation clause}
- {IS confidentiality clause}
- {IS representation or warranty clause}
- And more...
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class IQLTemplate:
    """An IQL query template with metadata."""
    name: str
    query: str
    description: str
    risk_level: str  # "HIGH", "MEDIUM", "LOW", "INFO"
    category: str
    
    def format(self, **kwargs) -> str:
        """Format the query with dynamic values if needed."""
        return self.query.format(**kwargs) if kwargs else self.query


class IQLTemplates:
    """
    Collection of IQL templates for Australian property law analysis.
    
    Uses official Isaacus templates with DOUBLE QUOTES for arguments.
    See: https://docs.isaacus.com/iql/templates
    
    Categories:
    - cooling_off: Cooling-off period related clauses
    - special_conditions: Contract special conditions
    - encumbrances: Title encumbrances (easements, covenants, caveats)
    - compliance: Building permits, owner-builder, compliance
    - strata: Strata/OC specific clauses
    - risk: High-risk clause detection
    """
    
    # === COOLING OFF PERIOD ===
    
    COOLING_OFF_WAIVER = IQLTemplate(
        name="cooling_off_waiver",
        query='{IS clause that "waives the purchaser cooling off period or statutory cooling off rights"}',
        description="Detects clauses waiving statutory cooling-off rights (e.g., s.66W in Victoria)",
        risk_level="HIGH",
        category="cooling_off"
    )
    
    COOLING_OFF_REDUCED = IQLTemplate(
        name="cooling_off_reduced",
        query='{IS clause that "reduces or shortens the cooling off period"}',
        description="Detects clauses reducing the standard cooling-off period",
        risk_level="MEDIUM",
        category="cooling_off"
    )
    
    SECTION_66W_WAIVER = IQLTemplate(
        name="section_66w_waiver",
        query='{IS clause that "references section 66W or waives cooling off rights under the Sale of Land Act"}',
        description="Specific detection of Victorian s.66W cooling-off waiver",
        risk_level="HIGH",
        category="cooling_off"
    )
    
    # === SPECIAL CONDITIONS ===
    
    SPECIAL_CONDITION = IQLTemplate(
        name="special_condition",
        query='{IS clause called "special condition"}',
        description="Identifies special conditions in contract",
        risk_level="INFO",
        category="special_conditions"
    )
    
    AS_IS_CONDITION = IQLTemplate(
        name="as_is_condition",
        query='{IS clause that "sells the property in its current condition or as-is where-is basis"}',
        description="Detects as-is/where-is sale conditions",
        risk_level="HIGH",
        category="special_conditions"
    )
    
    SUBJECT_TO_FINANCE = IQLTemplate(
        name="subject_to_finance",
        query='{IS clause that "makes the sale subject to the purchaser obtaining finance approval"}',
        description="Finance approval condition",
        risk_level="INFO",
        category="special_conditions"
    )
    
    SUBJECT_TO_BUILDING_INSPECTION = IQLTemplate(
        name="subject_to_building_inspection",
        query='{IS clause that "makes the sale subject to a satisfactory building or pest inspection"}',
        description="Building inspection condition",
        risk_level="INFO",
        category="special_conditions"
    )
    
    EARLY_RELEASE_DEPOSIT = IQLTemplate(
        name="early_release_deposit",
        query='{IS clause that "allows the deposit to be released to the vendor before settlement"}',
        description="Early deposit release clause (risk if vendor defaults)",
        risk_level="HIGH",
        category="special_conditions"
    )
    
    SUNSET_CLAUSE = IQLTemplate(
        name="sunset_clause",
        query='{IS termination clause} AND {IS clause that "allows termination if settlement is not completed by a specific date"}',
        description="Sunset/rescission clause for delayed settlement",
        risk_level="MEDIUM",
        category="special_conditions"
    )
    
    NOMINATION_CLAUSE = IQLTemplate(
        name="nomination_clause",
        query='{IS clause entitling "purchaser"} AND {IS clause that "allows nomination of another party to complete the purchase"}',
        description="Nomination rights clause",
        risk_level="INFO",
        category="special_conditions"
    )
    
    # === ENCUMBRANCES ===
    
    EASEMENT_CLAUSE = IQLTemplate(
        name="easement_clause",
        query='{IS clause that "discloses an easement or right of way affecting the property"}',
        description="Detects easement disclosures",
        risk_level="INFO",
        category="encumbrances"
    )
    
    RESTRICTIVE_COVENANT = IQLTemplate(
        name="restrictive_covenant",
        query='{IS clause that "discloses a restrictive covenant limiting the use or development of the land"}',
        description="Detects restrictive covenants that may limit development",
        risk_level="MEDIUM",
        category="encumbrances"
    )
    
    CAVEAT = IQLTemplate(
        name="caveat",
        query='{IS clause that "discloses a caveat or third party interest registered on the property title"}',
        description="Detects caveats on title",
        risk_level="HIGH",
        category="encumbrances"
    )
    
    MORTGAGE_ENCUMBRANCE = IQLTemplate(
        name="mortgage_encumbrance",
        query='{IS clause that "discloses an existing mortgage or registered charge on the property"}',
        description="Detects existing mortgages/charges",
        risk_level="INFO",
        category="encumbrances"
    )
    
    DEVELOPMENT_RESTRICTION = IQLTemplate(
        name="development_restriction",
        query='{IS clause that "restricts subdivision or multi-dwelling development on the property"}',
        description="Detects covenants blocking subdivision or multi-dwelling",
        risk_level="HIGH",
        category="encumbrances"
    )
    
    # === BUILDING & COMPLIANCE ===
    
    OWNER_BUILDER = IQLTemplate(
        name="owner_builder",
        query='{IS clause that "discloses owner-builder works or states domestic building insurance was not required"}',
        description="Detects owner-builder works (warranty implications)",
        risk_level="MEDIUM",
        category="compliance"
    )
    
    BUILDING_PERMIT = IQLTemplate(
        name="building_permit",
        query='{IS clause that "references building permits or building approvals for works on the property"}',
        description="Building permit disclosures",
        risk_level="INFO",
        category="compliance"
    )
    
    NO_FINAL_INSPECTION = IQLTemplate(
        name="no_final_inspection",
        query='{IS clause that "states certificate of final inspection or occupancy permit was not issued"}',
        description="Missing final inspection (potential illegal works)",
        risk_level="HIGH",
        category="compliance"
    )
    
    ILLEGAL_WORKS = IQLTemplate(
        name="illegal_works",
        query='{IS clause that "discloses unpermitted works or works done without council approval"}',
        description="Disclosure of illegal/unpermitted works",
        risk_level="HIGH",
        category="compliance"
    )
    
    SECTION_137B = IQLTemplate(
        name="section_137b",
        query='{IS clause that "references section 137B or defects report for owner-builder works"}',
        description="Victorian s.137B owner-builder defect report requirement",
        risk_level="INFO",
        category="compliance"
    )
    
    # === STRATA / OC ===
    
    SPECIAL_LEVY = IQLTemplate(
        name="special_levy",
        query='{IS clause that "discloses a special levy or additional contribution required from owners"}',
        description="Special levy disclosure or risk",
        risk_level="HIGH",
        category="strata"
    )
    
    STRATA_LITIGATION = IQLTemplate(
        name="strata_litigation",
        query='{IS clause that "references VCAT or NCAT proceedings or legal action against the owners corporation"}',
        description="Strata litigation or disputes",
        risk_level="HIGH",
        category="strata"
    )
    
    CLADDING_ISSUE = IQLTemplate(
        name="cladding_issue",
        query='{IS clause that "discloses combustible cladding or external wall cladding issues"}',
        description="Combustible cladding issues",
        risk_level="HIGH",
        category="strata"
    )
    
    PET_RESTRICTIONS = IQLTemplate(
        name="pet_restrictions",
        query='{IS clause that "prohibits or restricts keeping pets in the building"}',
        description="Pet restriction by-laws",
        risk_level="INFO",
        category="strata"
    )
    
    SHORT_TERM_LETTING = IQLTemplate(
        name="short_term_letting",
        query='{IS clause that "prohibits short-term letting or Airbnb style rentals"}',
        description="Short-term letting restrictions",
        risk_level="INFO",
        category="strata"
    )
    
    # === RISK DETECTION (using Isaacus operators) ===
    
    HIGH_RISK_CLAUSE = IQLTemplate(
        name="high_risk_clause",
        query='{IS clause that "waives cooling off rights"} OR {IS clause that "sells property as-is"} OR {IS clause that "releases deposit to vendor before settlement"}',
        description="Compound query for any high-risk clause",
        risk_level="HIGH",
        category="risk"
    )
    
    BUYER_UNFAVORABLE = IQLTemplate(
        name="buyer_unfavorable",
        query='{IS clause obligating "purchaser"} > {IS clause obligating "vendor"}',
        description="Clauses disproportionately obligating buyer vs seller (uses Isaacus comparison operator)",
        risk_level="MEDIUM",
        category="risk"
    )
    
    # === TITLE ===
    
    TITLE_MISMATCH = IQLTemplate(
        name="title_mismatch",
        query='{IS clause that "states vendor is not the registered proprietor"} OR {IS clause that "references a deceased estate or power of attorney sale"}',
        description="Title/vendor mismatch disclosure",
        risk_level="MEDIUM",
        category="title"
    )
    
    LIFE_ESTATE = IQLTemplate(
        name="life_estate",
        query='{IS clause that "discloses a life estate or life interest in the property"}',
        description="Life estate interest (finance difficulties)",
        risk_level="HIGH",
        category="title"
    )
    
    # === STANDARD CONTRACT CLAUSES (using built-in Isaacus templates) ===
    
    INDEMNITY = IQLTemplate(
        name="indemnity",
        query='{IS indemnity clause}',
        description="Detects indemnity clauses",
        risk_level="MEDIUM",
        category="standard"
    )
    
    LIABILITY_LIMITATION = IQLTemplate(
        name="liability_limitation",
        query='{IS liability limitation clause}',
        description="Detects liability limitation clauses",
        risk_level="INFO",
        category="standard"
    )
    
    TERMINATION = IQLTemplate(
        name="termination",
        query='{IS termination clause}',
        description="Detects termination clauses",
        risk_level="INFO",
        category="standard"
    )
    
    WARRANTY = IQLTemplate(
        name="warranty",
        query='{IS representation or warranty clause}',
        description="Detects warranty and representation clauses",
        risk_level="INFO",
        category="standard"
    )
    
    # === UTILITY METHODS ===
    
    @classmethod
    def get_all_templates(cls) -> List[IQLTemplate]:
        """Get all defined templates."""
        templates = []
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, IQLTemplate):
                templates.append(attr)
        return templates
    
    @classmethod
    def get_by_category(cls, category: str) -> List[IQLTemplate]:
        """Get templates by category."""
        return [t for t in cls.get_all_templates() if t.category == category]
    
    @classmethod
    def get_high_risk_templates(cls) -> List[IQLTemplate]:
        """Get all high-risk templates."""
        return [t for t in cls.get_all_templates() if t.risk_level == "HIGH"]
    
    @classmethod
    def get_section32_templates(cls) -> List[IQLTemplate]:
        """Get templates relevant for Section 32 Vendor Statements."""
        relevant_categories = ["cooling_off", "special_conditions", "encumbrances", 
                               "compliance", "title", "risk"]
        return [t for t in cls.get_all_templates() if t.category in relevant_categories]
    
    @classmethod
    def get_strata_templates(cls) -> List[IQLTemplate]:
        """Get templates relevant for Strata/OC documents."""
        return cls.get_by_category("strata")
    
    @classmethod
    def get_queries_dict(cls, templates: List[IQLTemplate] = None) -> Dict[str, str]:
        """
        Get templates as a dict for batch classification.
        
        Returns:
            Dict of {template_name: iql_query}
        """
        if templates is None:
            templates = cls.get_all_templates()
        return {t.name: t.query for t in templates}


# === DYNAMIC TEMPLATE BUILDERS (using proper Isaacus syntax) ===

def clause_that(description: str) -> str:
    """Build IQL query using the 'clause that' template with DOUBLE QUOTES."""
    return f'{{IS clause that "{description}"}}'


def clause_obligating(party: str) -> str:
    """Build IQL query for clauses obligating a specific party."""
    return f'{{IS clause obligating "{party}"}}'


def clause_entitling(party: str) -> str:
    """Build IQL query for clauses entitling a specific party."""
    return f'{{IS clause entitling "{party}"}}'


def clause_called(name: str) -> str:
    """Build IQL query for clause with a specific name."""
    return f'{{IS clause called "{name}"}}'


def combine_or(*queries: str) -> str:
    """Combine multiple IQL queries with OR (returns max score)."""
    return " OR ".join(queries)


def combine_and(*queries: str) -> str:
    """Combine multiple IQL queries with AND (returns min score)."""
    return " AND ".join(queries)


def compare_greater(query1: str, query2: str) -> str:
    """Compare two queries - returns query1 score if > query2, else 0."""
    return f"{query1} > {query2}"
