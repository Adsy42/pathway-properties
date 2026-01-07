"""
LLM prompt templates for document analysis.
"""

SECTION_32_EXTRACTION_PROMPT = """
Analyze this Section 32 Vendor Statement and extract the following:

1. TITLE DETAILS
   - Registered Proprietor name
   - Does vendor name match proprietor? If no, explain why (deceased, company, etc.)
   - Volume/Folio reference

2. ENCUMBRANCES
   - List all mortgages (holder + dealing number)
   - List all caveats with:
     - Caveator name
     - Grounds of claim (verbatim)
     - Risk level (LOW if commercial lender, HIGH if individual)
   - List all restrictive covenants with:
     - Full text
     - Date registered
     - Impact on development (can this block a subdivision or multi-dwelling?)

3. EASEMENTS
   - List each easement with type, beneficiary, and location
   - Flag if any easement crosses the building footprint

4. BUILDING PERMITS
   - List all permits from past 7 years
   - Note if Certificate of Final Inspection is missing

5. OWNER-BUILDER
   - Was the vendor an owner-builder for any works?
   - Is Section 137B Defect Report provided?

6. SPECIAL CONDITIONS
   - List each special condition with:
     - Condition number and full text
     - Risk assessment
   - Flag if cooling-off period is waived (66W)

For each finding, cite the PAGE NUMBER.
If information is not found, output "NOT FOUND" - do not guess.
"""

STRATA_ANALYSIS_PROMPT = """
Analyze this Strata Report and/or AGM Minutes and extract:

1. FINANCIAL HEALTH
   - Quarterly Admin Fund levy amount
   - Capital Works Fund (Sinking Fund) balance
   - Total insured value of the building
   - Calculate ratio: Sinking Fund / Insured Value (low ratio = special levy risk)

2. ISSUES & CONCERNS
   - Search for these keywords: cladding, water ingress, legal action, VCAT, NCAT, noise, defects
   - List any chronic maintenance issues (pump failures, lift breakdowns)
   - Note any ongoing disputes or litigation

3. BY-LAWS / RULES
   - Are pets allowed?
   - Is short-term letting (Airbnb) allowed?
   - Any renovation restrictions?

4. UPCOMING WORKS
   - List any planned capital works
   - Estimated costs and timing

Provide a summary risk assessment for this strata scheme.
"""

DEFECT_DETECTION_PROMPT = """
Analyze these property photos and identify any visible defects:

1. STRUCTURAL ISSUES
   - Cracks (note if >2mm, step cracking, or around windows/doors)
   - Signs of foundation movement
   - Sagging rooflines or floors

2. WATER DAMAGE
   - Water stains on ceilings or walls
   - Signs of rising damp (tide marks, salt deposits)
   - Mould or mildew

3. MAINTENANCE ISSUES
   - Peeling paint
   - Damaged gutters or fascia
   - Weathered windows or doors

4. SAFETY CONCERNS
   - Electrical issues visible
   - Handrail problems
   - Deck or balcony concerns

For each defect:
- Describe what you see
- Note the location (which room/area)
- Rate severity: Minor, Moderate, or Major
- Suggest if further investigation is needed
"""

SWEAT_EQUITY_PROMPT = """
Analyze this floorplan for value-add opportunities:

1. LAZY SPACE
   - Laundries larger than 5sqm (could become bathroom)
   - Oversized hallways (could add storage/study nook)
   - Enclosed sunrooms/verandahs (could become bedroom)
   - Single large living areas (could split into living + bedroom)

2. CONVERSION OPPORTUNITIES
   - Spaces that could become an additional bedroom
   - Spaces that could fit a bathroom (need 2.5m x 2m minimum)
   - Potential for granny flat (check rear yard space)

3. FOR EACH OPPORTUNITY:
   - Describe the current space and proposed conversion
   - Estimate cost using these benchmarks:
     - Bedroom addition: $15,000-25,000
     - Bathroom addition: $20,000-35,000
     - Laundry relocation: $8,000-15,000
     - Wall removal: $2,000-5,000
   - Estimate rent increase (typically $40-80/week per bedroom in Melbourne)
   - Calculate ROI in months

Be realistic. Only suggest conversions that are structurally feasible.
"""

RISK_SUMMARY_PROMPT = """
Based on all the analysis provided, generate an executive summary:

1. OVERALL RISK RATING
   - LOW: Minor issues only, strong investment
   - MEDIUM: Some concerns requiring attention
   - HIGH: Significant risks may outweigh benefits

2. TOP 3 RISKS
   For each risk:
   - Category (Legal, Physical, Financial, Location)
   - Specific issue
   - Potential impact
   - Suggested mitigation

3. TOP 3 OPPORTUNITIES
   For each opportunity:
   - Type (Renovation, Development, Rental Upside)
   - Description
   - Estimated value add

4. RECOMMENDATION
   - STRONG_BUY: Excellent investment, move quickly
   - BUY: Good investment with minor considerations
   - PROCEED_WITH_CAUTION: Investigate issues before committing
   - AVOID: Risks outweigh potential returns

5. EXECUTIVE SUMMARY
   A 2-3 sentence summary suitable for an investment committee.
"""







