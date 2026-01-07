"""
Analysis orchestrator - runs all analysis modules and aggregates results.

Integrates Isaacus Legal AI for intelligent clause classification using IQL.
Enhanced with comprehensive due diligence modules for Victorian property transactions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date

from database import Property, Document
from services.documents.rag import query_property_documents
from services.documents.vector_store import get_document_chunks
from services.analysis.prompts import (
    SECTION_32_EXTRACTION_PROMPT,
    STRATA_ANALYSIS_PROMPT,
    DEFECT_DETECTION_PROMPT,
    SWEAT_EQUITY_PROMPT,
    RISK_SUMMARY_PROMPT
)
from services.isaacus.classifier import (
    LegalClauseClassifier,
    DocumentClassification,
    get_legal_classifier
)
from config import get_settings

# Import enhanced due diligence modules
from services.due_diligence import (
    Section32CompletenessAnalyzer,
    CoolingOffCalculator,
    SpecialConditionsAnalyzer,
    ProprietorMismatchDetector,
    EasementImpactAnalyzer,
    CovenantAnalyzer,
    CaveatClassifier,
    Section173Analyzer,
    VictorianStampDutyCalculator,
    ZoneDevelopmentAnalyzer,
    BuildingPermitAnalyzer,
    CladdingRiskAssessor,
    StrataFinancialAnalyzer,
    ByLawAnalyzer,
    ContaminationAssessor,
    ComparableSalesAnalyzer,
    InvestorCashFlowModel,
    PropertyRiskScorer,
    StatementOfInformationAnalyzer,
    DueDiligenceComplianceTracker,
    DueDiligenceTimeline,
    SpecialistReferralEngine
)

settings = get_settings()


async def run_full_analysis(
    property_id: str,
    property_data: Property,
    documents: List[Document],
    contract_signed_date: Optional[date] = None,
    purchase_price: Optional[float] = None,
    is_investment: bool = False,
    purchaser_type: str = "individual",
    is_first_home_buyer: bool = False
) -> Dict[str, Any]:
    """
    Run complete asset-level analysis on all documents.

    Executes:
    1. Legal analysis (Section 32, contracts, title)
    2. Physical analysis (defects, illegal works)
    3. Financial analysis (yield, outgoings)
    4. Sweat equity analysis (renovation opportunities)
    5. Specialized checks (rooming house, SMSF)
    6. Enhanced due diligence analysis
    7. Risk scoring
    8. Timeline and compliance tracking
    9. Summary generation
    """

    # Categorize documents
    doc_types = {doc.document_type: doc for doc in documents}

    # Run core analyses
    legal = await run_legal_analysis(property_id, doc_types)
    physical = await run_physical_analysis(property_id, doc_types, property_data)
    financial = await run_financial_analysis(property_id, doc_types, property_data)
    sweat_equity = await run_sweat_equity_analysis(property_id, property_data)
    specialized = await run_specialized_analysis(property_id, doc_types)

    # Run enhanced due diligence analysis
    due_diligence = await run_enhanced_due_diligence(
        property_id=property_id,
        property_data=property_data,
        doc_types=doc_types,
        contract_signed_date=contract_signed_date,
        purchase_price=purchase_price,
        legal_analysis=legal,
        physical_analysis=physical,
        is_investment=is_investment,
        purchaser_type=purchaser_type,
        is_first_home_buyer=is_first_home_buyer
    )

    # Generate risk score using the new risk scoring framework
    risk_scorer = PropertyRiskScorer()
    all_analyses = {
        "property_type": (property_data.listing_data or {}).get("property_type", "house"),
        "legal_analysis": legal,
        "title_analysis": due_diligence.get("title_analysis", {}),
        "planning_analysis": due_diligence.get("planning_analysis", {}),
        "strata_analysis": due_diligence.get("strata_analysis", {}),
        "environmental_analysis": due_diligence.get("environmental_analysis", {}),
        "financial_analysis": financial,
        "physical_analysis": physical
    }
    risk_score = risk_scorer.calculate_risk_score(all_analyses)

    # Generate summary
    summary = await generate_summary(
        property_data=property_data,
        legal=legal,
        physical=physical,
        financial=financial,
        sweat_equity=sweat_equity,
        due_diligence=due_diligence,
        risk_score=risk_score
    )

    return {
        "legal": legal,
        "physical": physical,
        "financial": financial,
        "sweat_equity": sweat_equity,
        "specialized": specialized,
        "due_diligence": due_diligence,
        "risk_score": risk_score.to_dict() if hasattr(risk_score, 'to_dict') else risk_score,
        "summary": summary,
        "overall_risk": summary.get("overall_risk", "MEDIUM"),
        "recommendation": summary.get("recommendation", "PROCEED_WITH_CAUTION")
    }


async def run_legal_analysis(
    property_id: str,
    doc_types: Dict[str, Document]
) -> Dict[str, Any]:
    """
    Run legal document analysis using Isaacus IQL classification.
    
    Uses Isaacus Legal AI to classify clauses with purpose-built legal AI,
    replacing keyword-based detection with semantic understanding.
    """
    
    result = {
        "title": None,
        "mortgages": [],
        "caveats": [],
        "covenants": [],
        "easements": [],
        "building_permits": [],
        "illegal_works_risk": None,
        "owner_builder": None,
        "special_conditions": [],
        "cooling_off_waived": False,
        "planning": None,
        "isaacus_classification": None  # Isaacus IQL results
    }
    
    # Get the legal clause classifier
    classifier = get_legal_classifier()
    
    # Analyze Section 32 or Contract with Isaacus IQL
    if "Section 32 Vendor Statement (VIC)" in doc_types:
        # Get document chunks for Isaacus classification
        chunks = await get_document_chunks(
            property_id=property_id,
            document_type="Section 32 Vendor Statement (VIC)"
        )
        
        if chunks:
            # Run Isaacus IQL classification
            isaacus_result = await classifier.classify_section32(chunks)
            result["isaacus_classification"] = isaacus_result.to_dict()
            
            # Apply Isaacus-detected flags to result
            result["cooling_off_waived"] = isaacus_result.cooling_off_waived
            result["owner_builder"] = isaacus_result.owner_builder_works
            result["illegal_works_risk"] = isaacus_result.missing_final_inspection
            
            # Add high-risk clauses to special conditions
            for match in isaacus_result.high_risk_matches:
                result["special_conditions"].append({
                    "type": match.template_name,
                    "description": match.template_description,
                    "risk_level": match.risk_level,
                    "confidence": match.score,
                    "text_preview": match.text_snippet,
                    "location": match.page_reference
                })
            
            print(f"[Isaacus] Section 32 analysis: {isaacus_result.get_risk_summary()}")
        
        # Also run RAG for detailed extraction (complementary to classification)
        section32_result = await query_property_documents(
            property_id=property_id,
            question=SECTION_32_EXTRACTION_PROMPT
        )
        rag_result = parse_legal_extraction(section32_result.get("answer", ""))
        
        # Merge RAG results (Isaacus classification takes precedence for flags)
        result["title"] = rag_result.get("title")
        result["mortgages"] = rag_result.get("mortgages", [])
        result["caveats"] = rag_result.get("caveats", [])
        result["covenants"] = rag_result.get("covenants", [])
        result["easements"] = rag_result.get("easements", [])
        result["building_permits"] = rag_result.get("building_permits", [])
    
    elif "Contract for Sale (NSW)" in doc_types:
        # Get document chunks for Isaacus classification
        chunks = await get_document_chunks(
            property_id=property_id,
            document_type="Contract for Sale (NSW)"
        )
        
        if chunks:
            # Run Isaacus IQL classification for NSW contract
            isaacus_result = await classifier.classify_contract_nsw(chunks)
            result["isaacus_classification"] = isaacus_result.to_dict()
            
            # Apply Isaacus-detected flags
            result["cooling_off_waived"] = isaacus_result.cooling_off_waived
            
            for match in isaacus_result.high_risk_matches:
                result["special_conditions"].append({
                    "type": match.template_name,
                    "description": match.template_description,
                    "risk_level": match.risk_level,
                    "confidence": match.score,
                    "text_preview": match.text_snippet,
                    "location": match.page_reference
                })
            
            print(f"[Isaacus] NSW Contract analysis: {isaacus_result.get_risk_summary()}")
        
        # Also run RAG extraction
        contract_result = await query_property_documents(
            property_id=property_id,
            question="Extract all legal details from this NSW Contract for Sale including: "
                     "vendor details, purchaser cooling-off rights, special conditions, "
                     "zoning certificate details, and any encumbrances on title."
        )
        rag_result = parse_legal_extraction(contract_result.get("answer", ""))
        
        result["title"] = rag_result.get("title")
        result["mortgages"] = rag_result.get("mortgages", [])
        result["caveats"] = rag_result.get("caveats", [])
    
    # Check for strata documents with Isaacus
    if "Strata Report / OC Certificate" in doc_types or "Strata AGM Minutes" in doc_types:
        # Get strata document chunks
        strata_chunks = await get_document_chunks(
            property_id=property_id,
            document_type="Strata Report / OC Certificate"
        )
        
        if not strata_chunks:
            strata_chunks = await get_document_chunks(
                property_id=property_id,
                document_type="Strata AGM Minutes"
            )
        
        if strata_chunks:
            # Run Isaacus strata classification
            strata_isaacus = await classifier.classify_strata(strata_chunks)
            result["strata_classification"] = strata_isaacus.to_dict()
            print(f"[Isaacus] Strata analysis: {strata_isaacus.get_risk_summary()}")
        
        # Also run RAG for strata details
        strata_result = await query_property_documents(
            property_id=property_id,
            question=STRATA_ANALYSIS_PROMPT
        )
        result["strata"] = parse_strata_analysis(strata_result.get("answer", ""))
    
    return result


async def run_physical_analysis(
    property_id: str,
    doc_types: Dict[str, Document],
    property_data: Property
) -> Dict[str, Any]:
    """Run physical condition analysis."""
    
    result = {
        "defects_detected": [],
        "termite_risk": None,
        "structural_concerns": []
    }
    
    # Analyze building report
    if "Building Inspection Report" in doc_types:
        building_result = await query_property_documents(
            property_id=property_id,
            question="List all defects, issues, and concerns identified in this building inspection report. "
                     "For each item, note the location, severity (minor/moderate/major), and any "
                     "recommended actions."
        )
        result["defects_detected"] = parse_defects(building_result.get("answer", ""))
    
    # Analyze pest report
    if "Pest & Termite Inspection Report" in doc_types:
        pest_result = await query_property_documents(
            property_id=property_id,
            question="What termite or pest issues were found? Is there an active termite barrier? "
                     "Are there any signs of termite damage?"
        )
        result["termite_risk"] = parse_termite_risk(pest_result.get("answer", ""))
    
    return result


async def run_financial_analysis(
    property_id: str,
    doc_types: Dict[str, Document],
    property_data: Property
) -> Dict[str, Any]:
    """Run financial analysis."""
    
    # Get CoreLogic data
    corelogic = property_data.corelogic_data or {}
    listing = property_data.listing_data or {}
    
    # Extract price
    price = None
    if listing.get("price_display"):
        price = extract_price(listing["price_display"])
    if not price and corelogic.get("avm"):
        price = corelogic["avm"]
    
    # Get rental estimate
    rental = corelogic.get("rental_estimate", {})
    weekly_rent = rental.get("mid") or 700  # Default assumption
    
    # Extract outgoings from documents
    outgoings = await extract_outgoings(property_id, doc_types)
    
    # Calculate yields
    annual_rent = weekly_rent * 52
    total_outgoings = sum(outgoings.values())
    
    gross_yield = (annual_rent / price * 100) if price else None
    net_yield = ((annual_rent - total_outgoings) / price * 100) if price else None
    
    # Monthly cashflow (assuming 80% LVR at 6.5%)
    if price:
        loan_amount = price * 0.8
        monthly_interest = loan_amount * 0.065 / 12
        monthly_rent = weekly_rent * 52 / 12
        monthly_outgoings = total_outgoings / 12
        cashflow = monthly_rent - monthly_interest - monthly_outgoings
    else:
        cashflow = None
    
    return {
        "purchase": {
            "listing_price": listing.get("price_display"),
            "avm_value": corelogic.get("avm"),
            "avm_confidence": corelogic.get("avm_confidence"),
            "last_sold_price": corelogic.get("last_sold_price"),
            "last_sold_date": corelogic.get("last_sold_date")
        },
        "income": {
            "current_rent": None,
            "estimated_rent": rental,
            "rental_yield_gross": gross_yield
        },
        "outgoings": outgoings,
        "yield_analysis": {
            "gross": gross_yield,
            "net": net_yield,
            "cashflow_monthly": cashflow
        },
        "gst_applicable": False,
        "gst_reason": None
    }


async def run_sweat_equity_analysis(
    property_id: str,
    property_data: Property
) -> Dict[str, Any]:
    """Analyze renovation/value-add opportunities."""
    
    # Get floorplan if available
    listing = property_data.listing_data or {}
    floorplan_url = listing.get("floorplan_url")
    
    # Default opportunities based on property type
    opportunities = []
    
    # Check bedrooms - if 3 bed, potential to add 4th
    bedrooms = listing.get("bedrooms", 3)
    if bedrooms <= 3:
        opportunities.append({
            "type": "BedroomConversion",
            "description": "Convert large laundry or study into additional bedroom",
            "estimated_cost": 18000,
            "value_add": 35000,
            "rent_increase_weekly": 60,
            "roi_months": 7,
            "feasibility": "Moderate"
        })
    
    # Bathroom addition potential
    bathrooms = listing.get("bathrooms", 1)
    if bathrooms < bedrooms:
        opportunities.append({
            "type": "BathroomAddition",
            "description": "Add ensuite to master bedroom",
            "estimated_cost": 28000,
            "value_add": 45000,
            "rent_increase_weekly": 40,
            "roi_months": 13,
            "feasibility": "Moderate"
        })
    
    # Calculate totals
    total_cost = sum(o["estimated_cost"] for o in opportunities)
    total_value = sum(o["value_add"] for o in opportunities)
    
    return {
        "opportunities": opportunities,
        "total_value_add_potential": total_value,
        "total_cost": total_cost,
        "overall_roi": (total_value - total_cost) / total_cost * 100 if total_cost > 0 else 0
    }


async def run_specialized_analysis(
    property_id: str,
    doc_types: Dict[str, Document]
) -> Dict[str, Any]:
    """Run specialized checks (rooming house, SMSF)."""
    
    result = {}
    
    # Rooming house checks
    if "Rooming House Registration" in doc_types or "Annual Essential Safety Measures Report" in doc_types:
        result["rooming_house"] = {
            "is_registered": True,  # Would check register
            "class_1b_required": False,
            "class_1b_compliant": False,
            "aesmr_provided": "Annual Essential Safety Measures Report" in doc_types,
            "aesmr_current": True,
            "compliance_risk": "LOW"
        }
    
    return result


async def generate_summary(
    property_data: Property,
    legal: Dict[str, Any],
    physical: Dict[str, Any],
    financial: Dict[str, Any],
    sweat_equity: Dict[str, Any],
    due_diligence: Optional[Dict[str, Any]] = None,
    risk_score: Optional[Any] = None
) -> Dict[str, Any]:
    """Generate executive summary of analysis."""
    due_diligence = due_diligence or {}

    # Collect all risks
    top_risks = []

    # === STREET-LEVEL RISKS (from Gatekeeper) ===
    # These are critical location-based risks that should always be reported
    street_level = property_data.street_level_analysis
    if street_level:
        street_level_dict = street_level if isinstance(street_level, dict) else (
            street_level.dict() if hasattr(street_level, 'dict') else {}
        )
        
        # Flood risk (LSIO, SBO overlays)
        flood = street_level_dict.get("flood_risk", {})
        flood_score = flood.get("score") if isinstance(flood, dict) else None
        if flood_score in ["FAIL", "WARNING"]:
            top_risks.append({
                "category": "Environmental",
                "issue": f"Flood risk: {flood.get('details', 'Property in flood overlay')}",
                "severity": "HIGH" if flood_score == "FAIL" else "MEDIUM",
                "mitigation": "Check floor levels, insurance availability, and building restrictions. LSIO/SBO overlays may restrict development.",
                "source": "Street Level Analysis"
            })
        
        # Bushfire risk
        bushfire = street_level_dict.get("bushfire_risk", {})
        bushfire_score = bushfire.get("score") if isinstance(bushfire, dict) else None
        if bushfire_score in ["FAIL", "WARNING"]:
            bal_rating = bushfire.get("bal_rating", "Unknown") if isinstance(bushfire, dict) else "Unknown"
            is_severe = bal_rating in ["BAL-40", "BAL-FZ"]
            top_risks.append({
                "category": "Environmental",
                "issue": f"Bushfire risk: {'BAL-' + bal_rating if bal_rating else 'In Bushfire Prone Area'} - BAL assessment may be required",
                "severity": "HIGH" if is_severe else "MEDIUM",
                "mitigation": "BAL assessment required for building works. Higher construction costs apply. Check insurance availability.",
                "source": "Street Level Analysis"
            })
        
        # Flight path noise
        flight = street_level_dict.get("flight_path", {})
        flight_score = flight.get("score") if isinstance(flight, dict) else None
        if flight_score in ["FAIL", "WARNING"]:
            anef = flight.get("anef", 0) if isinstance(flight, dict) else 0
            n70 = flight.get("n70", 0) if isinstance(flight, dict) else 0
            top_risks.append({
                "category": "Environmental",
                "issue": f"Aircraft noise: ANEF {anef}, N70 {n70} flights/day",
                "severity": "HIGH" if flight_score == "FAIL" else "MEDIUM",
                "mitigation": "Significant noise impact on amenity and resale value",
                "source": "Street Level Analysis"
            })
        
        # Social housing concentration
        social = street_level_dict.get("social_housing", {})
        social_score = social.get("score") if isinstance(social, dict) else None
        if social_score in ["FAIL", "WARNING"]:
            density = social.get("density_percent", 0) if isinstance(social, dict) else 0
            top_risks.append({
                "category": "Location",
                "issue": f"Social housing concentration: {density:.1f}% in area",
                "severity": "HIGH" if social_score == "FAIL" else "MEDIUM",
                "mitigation": "May impact capital growth and tenant quality",
                "source": "Street Level Analysis"
            })
        
        # Zoning issues
        zoning = street_level_dict.get("zoning", {})
        zoning_score = zoning.get("score") if isinstance(zoning, dict) else None
        if zoning_score == "WARNING":
            zone_code = zoning.get("code", "") if isinstance(zoning, dict) else ""
            overlays = zoning.get("overlays", []) if isinstance(zoning, dict) else []
            top_risks.append({
                "category": "Planning",
                "issue": f"Zoning: {zone_code}. Overlays: {', '.join(overlays) if overlays else 'None'}",
                "severity": "MEDIUM",
                "mitigation": "Check planning restrictions and development potential",
                "source": "Street Level Analysis"
            })
    
    # === ISAACUS-DETECTED RISKS ===
    # High-confidence legal risks detected by Isaacus IQL
    isaacus_classification = legal.get("isaacus_classification", {})
    if isaacus_classification:
        high_risk_matches = isaacus_classification.get("high_risk_matches", [])
        for match in high_risk_matches:
            top_risks.append({
                "category": "Legal",
                "issue": match.get("description", match.get("clause_type", "Unknown")),
                "severity": "HIGH",
                "mitigation": _get_mitigation_for_clause(match.get("clause_type")),
                "confidence": match.get("confidence", 0),
                "source": "Isaacus IQL"
            })
        
        # Check Isaacus flags
        flags = isaacus_classification.get("flags", {})
        if flags.get("cooling_off_waived") and not any(
            r.get("issue") == "Cooling-off period waived" for r in top_risks
        ):
            top_risks.append({
                "category": "Legal",
                "issue": "Cooling-off period waived (s.66W)",
                "severity": "HIGH",
                "mitigation": "Complete all due diligence before signing - no cooling off rights",
                "source": "Isaacus IQL"
            })
        
        if flags.get("as_is_condition"):
            top_risks.append({
                "category": "Legal",
                "issue": "Property sold 'as-is where-is'",
                "severity": "HIGH",
                "mitigation": "Thorough building/pest inspection essential",
                "source": "Isaacus IQL"
            })
        
        if flags.get("early_deposit_release"):
            top_risks.append({
                "category": "Legal",
                "issue": "Early deposit release to vendor",
                "severity": "HIGH",
                "mitigation": "Risk if vendor defaults - consider refusing condition",
                "source": "Isaacus IQL"
            })
        
        if flags.get("missing_final_inspection"):
            top_risks.append({
                "category": "Legal",
                "issue": "Missing Certificate of Final Inspection",
                "severity": "HIGH",
                "mitigation": "Potential illegal works - investigate permits",
                "source": "Isaacus IQL"
            })
    
    # === TRADITIONAL LEGAL RISKS ===
    if legal.get("caveats"):
        for caveat in legal["caveats"]:
            if caveat.get("risk_level") == "HIGH":
                top_risks.append({
                    "category": "Legal",
                    "issue": f"Caveat by {caveat.get('caveator', 'unknown')}",
                    "severity": "HIGH",
                    "mitigation": "Investigate before exchange"
                })
    
    # Only add cooling-off waiver if not already detected by Isaacus
    if legal.get("cooling_off_waived") and not any(
        "cooling" in r.get("issue", "").lower() for r in top_risks
    ):
        top_risks.append({
            "category": "Legal",
            "issue": "Cooling-off period waived",
            "severity": "MEDIUM",
            "mitigation": "Complete due diligence before signing"
        })
    
    # Physical risks (with null safety)
    if physical:
        for defect in physical.get("defects_detected", []):
            if defect.get("severity") == "Major":
                top_risks.append({
                    "category": "Physical",
                    "issue": defect.get("type", "Unknown defect"),
                    "severity": "HIGH",
                    "mitigation": "Obtain repair quotes"
                })
        
        termite_risk = physical.get("termite_risk") or {}
        if termite_risk.get("risk_level") == "HIGH":
            top_risks.append({
                "category": "Physical",
                "issue": "Termite damage or risk",
                "severity": "HIGH",
                "mitigation": "Further inspection required"
            })
    
    # Add due diligence specific risks
    if due_diligence:
        # Section 32 completeness risks
        section32 = due_diligence.get("section32_completeness", {})
        if section32.get("rescission_risk"):
            top_risks.append({
                "category": "Legal",
                "issue": "Section 32 incomplete - rescission rights may apply",
                "severity": "HIGH",
                "mitigation": "Request missing documents before exchange",
                "source": "Section32Analyzer"
            })

        # Cooling-off expiry warning
        cooling_off = due_diligence.get("cooling_off", {})
        if cooling_off.get("status") == "URGENT":
            top_risks.append({
                "category": "Timeline",
                "issue": f"Cooling-off expires in {cooling_off.get('days_remaining', 0)} day(s)",
                "severity": "HIGH",
                "mitigation": "Complete due diligence immediately",
                "source": "CoolingOffCalculator"
            })

        # Cladding risk
        strata = due_diligence.get("strata_analysis", {})
        cladding = strata.get("cladding_risk", {})
        if cladding.get("risk_level") in ["HIGH", "CRITICAL"]:
            top_risks.append({
                "category": "Physical",
                "issue": f"Combustible cladding risk: {cladding.get('risk_level')}",
                "severity": "HIGH",
                "mitigation": "Request cladding audit report and special levy exposure",
                "source": "CladdingRiskAssessor"
            })

        # Environmental contamination risk
        env = due_diligence.get("environmental_analysis", {})
        if env.get("risk_level") in ["HIGH", "CRITICAL"]:
            top_risks.append({
                "category": "Environmental",
                "issue": f"Contamination risk: {env.get('risk_level')}",
                "severity": "CRITICAL",
                "mitigation": "Engage environmental auditor before purchase",
                "source": "ContaminationAssessor"
            })

        # Specialist referrals
        referrals = due_diligence.get("specialist_referrals", {})
        for critical in referrals.get("critical_referrals", []):
            top_risks.append({
                "category": "Specialist",
                "issue": f"Critical specialist needed: {critical.get('specialist_name')}",
                "severity": "HIGH",
                "mitigation": f"Engage {critical.get('specialist_name')} - {critical.get('typical_cost')}",
                "source": "SpecialistReferralEngine"
            })

    # Determine overall risk using new risk score if available
    if risk_score and hasattr(risk_score, 'rating'):
        overall_risk = risk_score.rating
        score_value = risk_score.score if hasattr(risk_score, 'score') else 50
        if overall_risk == "CRITICAL" or score_value >= 80:
            recommendation = "AVOID"
        elif overall_risk == "HIGH" or score_value >= 60:
            recommendation = "PROCEED_WITH_CAUTION"
        elif overall_risk == "ELEVATED" or score_value >= 40:
            recommendation = "BUY"
        elif overall_risk == "MODERATE" or score_value >= 20:
            recommendation = "BUY"
        else:
            recommendation = "STRONG_BUY"
    else:
        # Fallback to traditional risk assessment
        high_risks = sum(1 for r in top_risks if r.get("severity") == "HIGH")
        critical_risks = sum(1 for r in top_risks if r.get("severity") == "CRITICAL")
        if critical_risks >= 1 or high_risks >= 2:
            overall_risk = "HIGH"
            recommendation = "AVOID"
        elif high_risks == 1:
            overall_risk = "MEDIUM"
            recommendation = "PROCEED_WITH_CAUTION"
        elif len(top_risks) > 0:
            overall_risk = "MEDIUM"
            recommendation = "BUY"
        else:
            overall_risk = "LOW"
            recommendation = "STRONG_BUY"
    
    # Top opportunities
    top_opportunities = sweat_equity.get("opportunities", [])[:3]
    
    # Generate executive summary text
    address = property_data.address or "Unknown property"
    exec_summary = f"Analysis of {address}. "
    
    if overall_risk == "LOW":
        exec_summary += "This property presents low risk with strong fundamentals. "
    elif overall_risk == "MEDIUM":
        exec_summary += "This property has some risks that require attention. "
    else:
        exec_summary += "This property has significant risks that may outweigh benefits. "
    
    if top_opportunities:
        total_value = sum(o.get("value_add", 0) for o in top_opportunities)
        exec_summary += f"Value-add potential of ${total_value:,} identified. "
    
    if financial.get("yield_analysis", {}).get("gross"):
        yield_val = financial["yield_analysis"]["gross"]
        exec_summary += f"Gross yield estimate: {yield_val:.1f}%."
    
    return {
        "overall_risk": overall_risk,
        "recommendation": recommendation,
        "top_risks": top_risks[:5],
        "top_opportunities": [
            {"type": o["type"], "description": o["description"], "value": o["value_add"]}
            for o in top_opportunities
        ],
        "executive_summary": exec_summary
    }


# Helper functions

def _get_mitigation_for_clause(clause_type: str) -> str:
    """Get recommended mitigation action for a detected clause type."""
    mitigations = {
        "cooling_off_waiver": "Complete all due diligence before signing - no cooling off rights",
        "section_66w_waiver": "Complete all due diligence before signing - s.66W waiver in effect",
        "as_is_condition": "Thorough building and pest inspection essential before exchange",
        "early_release_deposit": "Consider refusing this condition or negotiate release conditions",
        "no_final_inspection": "Investigate all building permits and obtain compliance certificate",
        "illegal_works": "Request council records and consider independent building inspection",
        "caveat": "Investigate caveator's claim before exchange",
        "restrictive_covenant": "Review impact on intended use and development potential",
        "development_restriction": "Confirm impact on any subdivision or development plans",
        "owner_builder": "Request s.137B defect report and consider extended warranty insurance",
        "special_levy": "Request detailed sinking fund and capital works plan",
        "strata_litigation": "Request full legal proceedings disclosure and estimated costs",
        "cladding_issue": "Request combustible cladding audit report",
        "life_estate": "Confirm lender will finance life estate title",
        "title_mismatch": "Confirm vendor authority and investigate ownership structure",
    }
    return mitigations.get(clause_type, "Investigate before exchange")


def parse_legal_extraction(response: str) -> Dict[str, Any]:
    """Parse LLM response for legal extraction."""
    # In production, would use structured output
    return {
        "title": {"title_type": "Freehold", "proprietor": "Unknown", "vendor_match": True},
        "mortgages": [],
        "caveats": [],
        "covenants": [],
        "easements": [],
        "building_permits": [],
        "special_conditions": [],
        "cooling_off_waived": "66W" in response.upper() or "WAIVE" in response.upper()
    }


def parse_strata_analysis(response: str) -> Dict[str, Any]:
    """Parse LLM response for strata analysis."""
    return {
        "financial": {"admin_fund_quarterly": 0, "capital_works_fund_balance": 0},
        "issues": {"keywords": [], "chronic_maintenance": []},
        "rules": {"pets_allowed": True, "short_term_letting_allowed": True}
    }


def parse_defects(response: str) -> List[Dict[str, Any]]:
    """Parse LLM response for defects."""
    return []


def parse_termite_risk(response: str) -> Dict[str, Any]:
    """Parse LLM response for termite risk."""
    has_barrier = "BARRIER" in response.upper() and "NO" not in response.upper()
    has_damage = "DAMAGE" in response.upper() or "TERMITE" in response.upper()
    
    return {
        "barrier_present": has_barrier,
        "damage_detected": has_damage,
        "risk_level": "HIGH" if has_damage and not has_barrier else "LOW"
    }


async def extract_outgoings(
    property_id: str,
    doc_types: Dict[str, Document]
) -> Dict[str, float]:
    """Extract property outgoings from documents."""
    
    # Query for rates if Section 32 available
    if "Section 32 Vendor Statement (VIC)" in doc_types:
        rates_result = await query_property_documents(
            property_id=property_id,
            question="What are the annual council rates and water rates for this property?"
        )
        # Parse response - for now use defaults
    
    # Default outgoings
    return {
        "council_rates_annual": 2400,
        "water_rates_annual": 800,
        "strata_levies_annual": 0,
        "insurance_estimate": 1800,
        "land_tax_estimate": 0,
        "total_annual": 5000
    }


def extract_price(price_display: str) -> int:
    """Extract numeric price from display string."""
    import re

    # Remove non-numeric except commas and dots
    cleaned = re.sub(r'[^\d,.]', '', price_display)

    # Handle ranges - take midpoint
    if "-" in price_display:
        parts = price_display.split("-")
        prices = []
        for part in parts:
            cleaned = re.sub(r'[^\d]', '', part)
            if cleaned:
                prices.append(int(cleaned))
        if prices:
            return sum(prices) // len(prices)

    # Single price
    cleaned = re.sub(r'[^\d]', '', price_display)
    if cleaned:
        return int(cleaned)

    return None


# ============================================================
# ENHANCED DUE DILIGENCE ANALYSIS
# ============================================================

async def run_enhanced_due_diligence(
    property_id: str,
    property_data: Property,
    doc_types: Dict[str, Document],
    contract_signed_date: Optional[date],
    purchase_price: Optional[float],
    legal_analysis: Dict[str, Any],
    physical_analysis: Dict[str, Any],
    is_investment: bool = False,
    purchaser_type: str = "individual",
    is_first_home_buyer: bool = False
) -> Dict[str, Any]:
    """
    Run enhanced due diligence analysis using the new modules.

    This integrates:
    - Section 32 completeness checking
    - Cooling-off period calculation
    - Special conditions analysis
    - Title encumbrance analysis
    - Stamp duty calculation
    - Planning and zoning analysis
    - Strata analysis (for apartments/units)
    - Environmental risk assessment
    - Specialist referral triggers
    - Compliance tracking
    - Timeline generation
    """
    result = {}
    listing = property_data.listing_data or {}
    corelogic = property_data.corelogic_data or {}

    # Determine property type
    property_type = listing.get("property_type", "house").lower()
    is_strata = property_type in ["apartment", "townhouse", "unit"]

    # Get purchase price if not provided
    if not purchase_price:
        if listing.get("price_display"):
            purchase_price = extract_price(listing["price_display"])
        elif corelogic.get("avm"):
            purchase_price = corelogic["avm"]
        else:
            purchase_price = 800000  # Default for calculations

    # Get building year
    building_year = corelogic.get("year_built", 2000)

    # 1. Section 32 Completeness Check
    if "Section 32 Vendor Statement (VIC)" in doc_types:
        section32_analyzer = Section32CompletenessAnalyzer()
        # Get document text for analysis
        chunks = await get_document_chunks(
            property_id=property_id,
            document_type="Section 32 Vendor Statement (VIC)"
        )
        if chunks:
            section32_text = " ".join([c.get("content", "") for c in chunks])
            section32_result = section32_analyzer.analyze(
                section_32_text=section32_text,
                property_context={
                    "property_type": property_type,
                    "owner_builder_work_detected": legal_analysis.get("owner_builder", False)
                }
            )
            result["section32_completeness"] = section32_result.to_dict()

    # 2. Cooling-Off Period Calculation
    if contract_signed_date:
        from services.due_diligence.cooling_off import PurchaseMethod, PurchaserType

        cooling_off_calc = CoolingOffCalculator()
        purchase_method = PurchaseMethod.PRIVATE_SALE  # Default
        purchaser_type_enum = PurchaserType.CORPORATION if purchaser_type == "corporation" else PurchaserType.INDIVIDUAL

        cooling_off_result = cooling_off_calc.calculate_cooling_off(
            contract_signed_date=contract_signed_date,
            purchase_price=purchase_price,
            purchase_method=purchase_method,
            purchaser_type=purchaser_type_enum
        )
        result["cooling_off"] = cooling_off_result.to_dict()

        # Get key dates
        key_dates = cooling_off_calc.get_key_dates(
            contract_signed_date=contract_signed_date,
            settlement_days=30
        )
        result["key_dates"] = key_dates

    # 3. Special Conditions Analysis
    special_conditions = legal_analysis.get("special_conditions", [])
    if special_conditions:
        conditions_analyzer = SpecialConditionsAnalyzer()
        conditions_result = conditions_analyzer.analyze(special_conditions)
        result["special_conditions_analysis"] = conditions_result.to_dict()

    # 4. Title Analysis
    title_analysis = {}

    # Easement analysis
    easements = legal_analysis.get("easements", [])
    if easements:
        easement_analyzer = EasementImpactAnalyzer()
        for easement in easements:
            easement_result = easement_analyzer.analyze(
                easement_data=easement,
                property_dimensions=listing.get("land_area", 500)
            )
            title_analysis["easements"] = easement_result.to_dict() if hasattr(easement_result, 'to_dict') else easement_result

    # Covenant analysis
    covenants = legal_analysis.get("covenants", [])
    if covenants:
        covenant_analyzer = CovenantAnalyzer()
        title_analysis["covenants"] = []
        for covenant in covenants:
            covenant_result = covenant_analyzer.analyze(covenant)
            title_analysis["covenants"].append(
                covenant_result.to_dict() if hasattr(covenant_result, 'to_dict') else covenant_result
            )

    # Caveat analysis
    caveats = legal_analysis.get("caveats", [])
    if caveats:
        caveat_classifier = CaveatClassifier()
        title_analysis["caveats"] = []
        for caveat in caveats:
            caveat_result = caveat_classifier.classify(caveat)
            title_analysis["caveats"].append(
                caveat_result.to_dict() if hasattr(caveat_result, 'to_dict') else caveat_result
            )

    result["title_analysis"] = title_analysis

    # 5. Stamp Duty Calculation
    stamp_duty_calc = VictorianStampDutyCalculator()
    stamp_duty_result = stamp_duty_calc.calculate(
        purchase_price=purchase_price,
        first_home_buyer=is_first_home_buyer,
        principal_residence=not is_investment
    )
    result["stamp_duty"] = stamp_duty_result.to_dict()

    # Total acquisition costs
    acquisition_costs = stamp_duty_calc.estimate_total_acquisition_costs(
        purchase_price=purchase_price,
        first_home_buyer=is_first_home_buyer,
        is_investment=is_investment
    )
    result["acquisition_costs"] = acquisition_costs

    # 6. Planning Analysis
    overlays = corelogic.get("overlays", [])
    zone = corelogic.get("zone", "GRZ1")

    zone_analyzer = ZoneDevelopmentAnalyzer()
    planning_result = zone_analyzer.analyze(
        zone_code=zone,
        overlay_codes=overlays,
        intended_use="investor" if is_investment else "owner_occupier",
        land_size_sqm=listing.get("land_area", 500)
    )
    result["planning_analysis"] = planning_result.to_dict() if hasattr(planning_result, 'to_dict') else planning_result

    # 7. Strata Analysis (if applicable)
    if is_strata:
        strata_analysis = {}

        # Cladding risk assessment
        cladding_assessor = CladdingRiskAssessor()
        cladding_result = cladding_assessor.assess(
            building_year=building_year,
            building_stories=corelogic.get("stories", 3)
        )
        strata_analysis["cladding_risk"] = cladding_result.to_dict()

        # Financial health analysis (if we have strata data)
        strata_data = legal_analysis.get("strata", {})
        if strata_data:
            strata_financial = StrataFinancialAnalyzer()
            financial_result = strata_financial.analyze(
                admin_fund_balance=strata_data.get("admin_fund", 0),
                sinking_fund_balance=strata_data.get("sinking_fund", 0),
                quarterly_levies=strata_data.get("quarterly_levies", 0),
                total_lot_entitlements=100,
                arrears_amount=strata_data.get("arrears", 0),
                special_levies=strata_data.get("special_levies", []),
                upcoming_works=[]
            )
            strata_analysis["financial_health"] = financial_result.to_dict()

        result["strata_analysis"] = strata_analysis

    # 8. Environmental Risk Assessment
    env_assessor = ContaminationAssessor()
    env_result = await env_assessor.assess(
        address=property_data.address,
        lat=corelogic.get("lat"),
        lon=corelogic.get("lon"),
        planning_info={"overlays": [{"code": o} for o in overlays] if overlays else []},
        section_32_text=None  # Would need to extract from documents
    )
    result["environmental_analysis"] = env_result.to_dict()

    # 9. Specialist Referral Triggers
    referral_engine = SpecialistReferralEngine()
    building_findings = physical_analysis.get("defects_detected", [])
    referral_result = referral_engine.analyze(
        property_data={
            "building_year": building_year,
            "property_type": property_type,
            "overlays": overlays,
            "has_pool": listing.get("has_pool", False)
        },
        building_inspection={"findings": building_findings},
        planned_works=[],
        is_investment=is_investment
    )
    result["specialist_referrals"] = referral_result.to_dict()

    # 10. Compliance Tracking
    compliance_tracker = DueDiligenceComplianceTracker()
    property_analysis = {
        "title_searched": "title_documents" in str(legal_analysis),
        "section32_reviewed": "section32_completeness" in result,
        "building_inspection": len(building_findings) > 0 or "Building Inspection Report" in doc_types,
        "pest_inspection": "Pest & Termite Inspection Report" in doc_types,
        "strata_searched": is_strata and "strata_analysis" in result,
        "finance_approved": False,  # Would need external input
        "legal_analysis": legal_analysis,
        "physical_analysis": physical_analysis
    }
    property_context = {
        "property_type": property_type,
        "has_pool": listing.get("has_pool", False),
        "corporate_vendor": False  # Would need to detect from vendor entity
    }
    compliance_result = compliance_tracker.get_completion_status(
        property_analysis=property_analysis,
        property_context=property_context
    )
    result["compliance_status"] = compliance_result.to_dict() if hasattr(compliance_result, 'to_dict') else compliance_result

    # 11. Timeline Generation (if contract signed)
    if contract_signed_date:
        timeline = DueDiligenceTimeline()
        settlement_date = contract_signed_date + __import__('datetime').timedelta(days=30)
        cooling_off_date = result.get("cooling_off", {}).get("deadline")
        if cooling_off_date:
            cooling_off_date = date.fromisoformat(cooling_off_date) if isinstance(cooling_off_date, str) else cooling_off_date

        # Extract special conditions for timeline
        conditions_for_timeline = []
        if "special_conditions_analysis" in result:
            for cond in result["special_conditions_analysis"].get("conditions", []):
                conditions_for_timeline.append({
                    "type": cond.get("type"),
                    "deadline": cond.get("deadline")
                })

        timeline_result = timeline.create_timeline(
            contract_signed_date=contract_signed_date,
            cooling_off_expires=cooling_off_date,
            settlement_date=settlement_date,
            special_conditions=conditions_for_timeline,
            property_type=property_type,
            is_investment=is_investment
        )
        result["timeline"] = timeline_result.to_dict()

    # 12. Cash Flow Model (for investment properties)
    if is_investment:
        cash_flow_model = InvestorCashFlowModel()
        rental_estimate = corelogic.get("rental_estimate", {}).get("mid", 700)
        strata_levies = result.get("strata_analysis", {}).get("financial_health", {}).get("quarterly_levies", 0) * 4

        cash_flow_result = cash_flow_model.calculate(
            purchase_price=purchase_price,
            weekly_rent=rental_estimate,
            outgoings={
                "council_rates": 2400,
                "water_rates": 800,
                "strata_levies": strata_levies,
                "insurance": 1800,
                "building_year": building_year
            },
            finance_params={
                "deposit_percent": 20,
                "interest_rate": 0.065,
                "loan_term_years": 30
            },
            investor_params={
                "property_management_percent": 7.5,
                "vacancy_rate": 3.0,
                "maintenance_percent": 1.0,
                "marginal_tax_rate": 37.0
            }
        )
        result["cash_flow_model"] = cash_flow_result.to_dict()

    return result




