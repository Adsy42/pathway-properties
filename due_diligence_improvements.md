# Pathway Property Due Diligence Module: Comprehensive Enhancement Specification

## Executive Assessment

Your current MVP has strong architectural foundations—the two-phase Gatekeeper model, Isaacus legal AI integration, and cross-document reasoning are genuine differentiators. However, the due diligence coverage is approximately **40% complete** relative to what a professional buyer's agency actually needs. The gaps fall into nine categories that, if addressed, would make this production-ready for Pathway Property's operational workflow.

---

## Gap Analysis Summary

| Category | Current Coverage | Target Coverage | Priority |
|----------|------------------|-----------------|----------|
| Legal Document Analysis | 40% | 95% | CRITICAL |
| Title & Encumbrance | 35% | 90% | CRITICAL |
| Planning & Zoning | 30% | 85% | HIGH |
| Strata & Cladding | 25% | 90% | HIGH |
| Environmental | 10% | 75% | MEDIUM |
| Financial Deep-Dive | 45% | 85% | HIGH |
| Risk Scoring | 20% | 80% | CRITICAL |
| Regulatory Compliance | 15% | 70% | MEDIUM |
| Process Orchestration | 30% | 80% | HIGH |

---

## CATEGORY 1: LEGAL DOCUMENT ANALYSIS ENHANCEMENTS

### 1.1 Section 32 Completeness Checker

**Current Gap:** You extract data from Section 32 but don't verify if the Section 32 itself is legally complete. An incomplete Section 32 gives the purchaser rescission rights at any time before settlement.

**Required Checks:**

```python
SECTION_32_MANDATORY_COMPONENTS = {
    "victoria": {
        "title_documents": {
            "required": True,
            "description": "Register Search Statement (copy of title)",
            "risk_if_missing": "CRITICAL - Contract may be voidable"
        },
        "plan_of_subdivision": {
            "required": True,
            "description": "Registered plan showing lot boundaries",
            "risk_if_missing": "HIGH - Cannot verify boundaries/easements"
        },
        "council_certificate": {
            "required": True,
            "description": "Certificate from local council",
            "contains": ["rates", "orders", "notices", "road widening"],
            "risk_if_missing": "CRITICAL - May have outstanding orders"
        },
        "water_authority_certificate": {
            "required": True,
            "description": "Certificate from water authority",
            "contains": ["water rates", "sewerage", "drainage"],
            "risk_if_missing": "HIGH - Unknown water/sewer liability"
        },
        "owners_corp_certificate": {
            "required_if": "property_type IN ['apartment', 'townhouse', 'unit']",
            "description": "Section 151 Owners Corporation Certificate",
            "cost": "$175-330",
            "risk_if_missing": "CRITICAL - Unknown strata liabilities"
        },
        "building_permits_7_years": {
            "required": True,
            "description": "All building permits issued in preceding 7 years",
            "cross_reference": "physical_inspection_findings",
            "risk_if_missing": "HIGH - Potential illegal works"
        },
        "owner_builder_disclosure": {
            "required_if": "owner_builder_work_in_6_years",
            "description": "Section 137B defect report + insurance",
            "risk_if_missing": "CRITICAL - Contract voidable, warranty gaps"
        },
        "growth_areas_certificate": {
            "required_if": "property_in_growth_area",
            "description": "Growth Areas Infrastructure Contribution",
            "risk_if_missing": "MEDIUM - Potential infrastructure levy"
        }
    }
}
```

**Implementation:**

```python
class Section32CompletenessAnalyzer:
    """
    Validates Section 32 contains all legally required components.
    Missing components = rescission rights for purchaser.
    """
    
    def analyze(self, section_32_text: str, property_context: dict) -> dict:
        results = {
            "is_complete": True,
            "missing_critical": [],
            "missing_high": [],
            "missing_medium": [],
            "rescission_risk": False,
            "recommendations": []
        }
        
        for component, config in SECTION_32_MANDATORY_COMPONENTS["victoria"].items():
            # Check if required based on property context
            if self._is_required(config, property_context):
                if not self._component_present(section_32_text, component):
                    risk_level = config["risk_if_missing"].split(" - ")[0]
                    results[f"missing_{risk_level.lower()}"].append({
                        "component": component,
                        "description": config["description"],
                        "consequence": config["risk_if_missing"]
                    })
                    
                    if risk_level == "CRITICAL":
                        results["rescission_risk"] = True
                        results["is_complete"] = False
        
        return results
```

### 1.2 Cooling-Off Period Calculator & Tracker

**Current Gap:** You detect cooling-off waiver clauses but don't calculate deadlines, track expiry, or handle the complex rules around auctions.

**Victorian Cooling-Off Rules:**

```python
COOLING_OFF_RULES = {
    "standard_period": {
        "duration": "3 clear business days",
        "starts": "day after purchaser signs contract",
        "excludes": ["signing_day", "weekends", "victorian_public_holidays"],
        "penalty_to_exit": "max($100, 0.2% of purchase_price)"
    },
    "no_cooling_off_applies": [
        "purchased_at_auction",
        "purchased_within_3_clear_business_days_before_auction",
        "purchased_within_3_clear_business_days_after_auction",
        "land_exceeds_20_hectares_primarily_farming",
        "primarily_commercial_or_industrial_use",
        "purchaser_is_corporation",
        "section_31_certificate_signed"
    ],
    "section_31_certificate": {
        "effect": "Waives cooling-off rights",
        "must_be_signed_by": "purchaser's legal practitioner",
        "required_before": "purchaser signs contract",
        "consequence_if_signed": "NO cooling-off period"
    }
}
```

**Implementation:**

```python
class CoolingOffCalculator:
    """
    Calculates cooling-off deadlines and tracks expiry.
    Critical for buyers who need to complete due diligence in time.
    """
    
    def calculate_cooling_off(
        self,
        contract_signed_date: date,
        purchase_method: str,  # 'private_sale', 'auction', 'pre_auction', 'post_auction'
        auction_date: Optional[date],
        purchaser_type: str,  # 'individual', 'corporation'
        property_use: str,  # 'residential', 'commercial', 'farming'
        land_size_hectares: float,
        section_31_certificate: bool
    ) -> dict:
        
        # Check exemptions
        if self._is_exempt(purchase_method, auction_date, purchaser_type, 
                          property_use, land_size_hectares, section_31_certificate):
            return {
                "has_cooling_off": False,
                "exemption_reason": self._get_exemption_reason(...),
                "warning": "Due diligence MUST be complete before signing contract",
                "risk_level": "HIGH"
            }
        
        # Calculate deadline
        deadline = self._calculate_deadline(contract_signed_date)
        days_remaining = (deadline - date.today()).days
        
        return {
            "has_cooling_off": True,
            "deadline": deadline.isoformat(),
            "deadline_formatted": deadline.strftime("%A, %d %B %Y at 11:59 PM"),
            "days_remaining": days_remaining,
            "hours_remaining": days_remaining * 24,
            "penalty_to_exit": self._calculate_penalty(purchase_price),
            "status": "URGENT" if days_remaining <= 1 else "ACTIVE",
            "recommendations": self._get_recommendations(days_remaining)
        }
    
    def _calculate_deadline(self, signed_date: date) -> date:
        """
        3 CLEAR business days = excludes signing day, weekends, VIC public holidays.
        """
        vic_holidays = self._get_victorian_public_holidays(signed_date.year)
        
        clear_days = 0
        current_date = signed_date
        
        while clear_days < 3:
            current_date += timedelta(days=1)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Skip Victorian public holidays
            if current_date in vic_holidays:
                continue
            
            clear_days += 1
        
        return current_date
```

### 1.3 Vendor vs Registered Proprietor Mismatch Detection

**Current Gap:** You note this matters but don't automate detection.

**Risk Scenarios:**

```python
PROPRIETOR_MISMATCH_SCENARIOS = {
    "deceased_estate": {
        "indicators": [
            "registered_proprietor_different_from_vendor",
            "vendor_signing_as_executor",
            "vendor_signing_as_administrator",
            "probate_mentioned",
            "letters_of_administration_mentioned"
        ],
        "additional_checks": [
            "Verify Grant of Probate obtained",
            "Check executor has power to sell",
            "Confirm no caveats from beneficiaries",
            "Verify no pending family provision claims"
        ],
        "risk_level": "MEDIUM",
        "typical_delay": "Settlement may be delayed pending probate"
    },
    "company_sale": {
        "indicators": [
            "registered_proprietor_is_pty_ltd",
            "vendor_signing_as_director"
        ],
        "additional_checks": [
            "ASIC company search - is company still registered?",
            "Check for external administrators",
            "Verify director has authority to sign",
            "Check for any charges over property"
        ],
        "risk_level": "MEDIUM"
    },
    "power_of_attorney": {
        "indicators": [
            "vendor_signing_under_power_of_attorney",
            "attorney_mentioned"
        ],
        "additional_checks": [
            "Verify POA registered on title",
            "Confirm POA not revoked",
            "Check donor still alive (POA dies with donor)"
        ],
        "risk_level": "HIGH"
    },
    "trust_sale": {
        "indicators": [
            "registered_proprietor_includes_as_trustee",
            "trust_mentioned"
        ],
        "additional_checks": [
            "Verify trustee has power to sell under trust deed",
            "Check no breach of trust"
        ],
        "risk_level": "MEDIUM"
    }
}
```

### 1.4 Special Conditions Analyzer

**Current Gap:** You only detect cooling-off waiver. Many other special conditions materially affect risk.

**Common Special Conditions to Detect:**

```python
SPECIAL_CONDITIONS_DETECTION = {
    "subject_to_finance": {
        "iql_query": "{IS clause that 'makes purchase conditional on finance approval'}",
        "extract_fields": ["lender_name", "loan_amount", "approval_deadline"],
        "risk_if_absent": "Purchase is unconditional - full deposit at risk",
        "typical_period": "14-21 days"
    },
    "subject_to_building_inspection": {
        "iql_query": "{IS clause that 'makes purchase conditional on satisfactory building inspection'}",
        "extract_fields": ["inspection_deadline", "defect_threshold"],
        "risk_if_absent": "Cannot terminate for defects discovered post-contract"
    },
    "subject_to_pest_inspection": {
        "iql_query": "{IS clause that 'makes purchase conditional on pest inspection'}",
        "risk_if_absent": "Termite damage discovered post-contract = your problem"
    },
    "subject_to_sale": {
        "iql_query": "{IS clause that 'makes purchase conditional on sale of another property'}",
        "extract_fields": ["property_to_sell", "sale_deadline"],
        "vendor_perspective": "Risky for vendor - may reject"
    },
    "early_deposit_release": {
        "iql_query": "{IS clause that 'allows vendor to access deposit before settlement'}",
        "risk_level": "HIGH",
        "consequence": "If settlement fails, deposit harder to recover"
    },
    "as_is_where_is": {
        "iql_query": "{IS clause that 'property sold in current condition' OR 'as is where is'}",
        "consequence": "No warranty on condition - inspection critical"
    },
    "vendor_warranty_exclusion": {
        "iql_query": "{IS clause that 'excludes vendor warranties'}",
        "consequence": "Limited recourse for defects"
    },
    "sunset_clause": {
        "iql_query": "{IS clause specifying 'sunset date' OR 'contract terminates if not settled by'}",
        "extract_fields": ["sunset_date"],
        "risk": "Off-the-plan purchases - developer can rescind if market rises"
    },
    "nomination_clause": {
        "iql_query": "{IS clause allowing 'nomination of substitute purchaser'}",
        "use_case": "Useful for SMSF purchases or development"
    },
    "gst_clause": {
        "iql_query": "{IS clause regarding 'GST' OR 'goods and services tax'}",
        "extract_fields": ["gst_inclusive", "margin_scheme"],
        "affects": "New properties, commercial, subdivisions"
    },
    "settlement_extension": {
        "iql_query": "{IS clause allowing 'extension of settlement' OR 'delayed settlement'}",
        "extract_fields": ["extension_fee", "max_extension_period"]
    }
}
```

### 1.5 Stamp Duty Calculator

**Current Gap:** No stamp duty calculation despite being a major transaction cost.

```python
class VictorianStampDutyCalculator:
    """
    Calculates stamp duty for Victorian property purchases.
    Source: State Revenue Office Victoria (sro.vic.gov.au)
    """
    
    DUTY_BRACKETS_2025 = [
        (0, 25000, 0.014, 0),           # 1.4%
        (25000, 130000, 0.024, 350),    # 2.4% + $350
        (130000, 960000, 0.06, 2870),   # 6% + $2,870
        (960000, float('inf'), 0.055, 52670)  # 5.5% + $52,670
    ]
    
    FOREIGN_PURCHASER_SURCHARGE = 0.08  # 8% additional
    
    def calculate(
        self,
        purchase_price: float,
        property_type: str,  # 'residential', 'commercial', 'primary_production'
        purchaser_status: str,  # 'citizen', 'pr', 'foreign'
        first_home_buyer: bool,
        principal_residence: bool,
        pensioner: bool = False
    ) -> dict:
        
        base_duty = self._calculate_base_duty(purchase_price)
        
        # Foreign purchaser surcharge
        foreign_surcharge = 0
        if purchaser_status == 'foreign' and property_type == 'residential':
            foreign_surcharge = purchase_price * self.FOREIGN_PURCHASER_SURCHARGE
        
        # First Home Buyer exemptions/concessions
        fhb_reduction = 0
        if first_home_buyer and principal_residence:
            fhb_reduction = self._calculate_fhb_concession(purchase_price, base_duty)
        
        # Pensioner concession
        pensioner_reduction = 0
        if pensioner and principal_residence:
            pensioner_reduction = self._calculate_pensioner_concession(purchase_price)
        
        total_duty = max(0, base_duty + foreign_surcharge - fhb_reduction - pensioner_reduction)
        
        return {
            "base_duty": base_duty,
            "foreign_surcharge": foreign_surcharge,
            "fhb_concession": fhb_reduction,
            "pensioner_concession": pensioner_reduction,
            "total_duty": total_duty,
            "effective_rate": (total_duty / purchase_price) * 100,
            "due_date": "Within 30 days of settlement",
            "notes": self._get_applicable_notes(...)
        }
    
    def _calculate_fhb_concession(self, price: float, base_duty: float) -> float:
        """
        First Home Buyer:
        - Full exemption: $0 - $600,000
        - Sliding scale: $600,001 - $750,000
        - No concession: $750,001+
        """
        if price <= 600000:
            return base_duty  # Full exemption
        elif price <= 750000:
            # Sliding scale reduction
            reduction_factor = (750000 - price) / 150000
            return base_duty * reduction_factor
        else:
            return 0  # No concession
```

---

## CATEGORY 2: TITLE & ENCUMBRANCE ENHANCEMENTS

### 2.1 Comprehensive Easement Analysis

**Current Gap:** You detect easements exist but don't analyze their practical impact.

```python
EASEMENT_TYPES = {
    "drainage_easement": {
        "typical_width": "1.5m - 3m",
        "impact": "Cannot build over - affects floor plan",
        "check": "Does building footprint intersect easement?"
    },
    "sewerage_easement": {
        "typical_width": "2m - 4m",
        "impact": "Cannot build over, authority access rights",
        "check": "Location of sewer line relative to proposed works"
    },
    "electricity_easement": {
        "typical_width": "Varies by voltage",
        "impact": "Height restrictions, cannot plant tall trees",
        "check": "Overhead or underground? Substation nearby?"
    },
    "carriageway_easement": {
        "impact": "Access rights for others over your land",
        "check": "Who benefits? How often used? Maintenance obligations?"
    },
    "party_wall_easement": {
        "impact": "Shared wall with neighbour",
        "check": "Repair obligations, modification restrictions"
    },
    "pipeline_easement": {
        "impact": "Gas, water, or oil pipeline",
        "check": "Setback requirements, excavation restrictions"
    }
}

class EasementImpactAnalyzer:
    """
    Analyzes practical impact of easements on property use and development.
    """
    
    def analyze(self, title_search: dict, building_footprint: dict, proposed_use: str) -> dict:
        results = {
            "easements_found": [],
            "building_conflicts": [],
            "development_restrictions": [],
            "risk_score": 0
        }
        
        for easement in title_search.get("easements", []):
            analysis = {
                "type": easement["type"],
                "beneficiary": easement["beneficiary"],
                "width": easement.get("width"),
                "location": easement["location"],
                "conflicts_with_building": self._check_footprint_conflict(
                    easement, building_footprint
                ),
                "affects_development": self._check_development_impact(
                    easement, proposed_use
                )
            }
            results["easements_found"].append(analysis)
        
        # Section 42(2)(d) warning - implied easements
        results["implied_easement_warning"] = {
            "applies": True,
            "explanation": "Under Section 42(2)(d) of the Transfer of Land Act 1958, "
                          "easements may exist that are NOT shown on title. "
                          "Physical inspection required to identify actual service locations."
        }
        
        return results
```

### 2.2 Restrictive Covenant Impact Scoring

**Current Gap:** You mention "One dwelling only" but don't systematically score covenant impacts.

```python
COVENANT_IMPACT_MATRIX = {
    "single_dwelling_only": {
        "impact_score": 9,  # Out of 10
        "affects": ["subdivision", "dual_occupancy", "granny_flat", "rooming_house"],
        "can_be_removed": "Section 60 application to VCAT - expensive, uncertain",
        "removal_cost": "$20,000 - $50,000",
        "removal_success_rate": "30-50%"
    },
    "building_materials": {
        "impact_score": 4,
        "common_restrictions": ["brick only", "no weatherboard", "tile roof only"],
        "affects": ["renovation_options", "extension_cost"],
        "can_be_removed": "Possible if neighbourhood character has changed"
    },
    "building_setbacks": {
        "impact_score": 5,
        "common_restrictions": ["10m front setback", "3m side setback"],
        "affects": ["buildable_area", "extension_potential"],
        "planning_interaction": "More restrictive than planning scheme = covenant prevails"
    },
    "no_business": {
        "impact_score": 3,
        "affects": ["home_office", "airbnb", "rooming_house"],
        "modern_interpretation": "Small home office usually OK, commercial not"
    },
    "height_restriction": {
        "impact_score": 6,
        "affects": ["second_storey", "extension"],
        "compare_to": "Planning scheme height limits"
    },
    "no_subdivision": {
        "impact_score": 8,
        "affects": ["subdivision", "development_potential"],
        "can_be_removed": "Difficult - usually upheld"
    },
    "fence_requirements": {
        "impact_score": 2,
        "common_restrictions": ["fence type", "fence height", "front fence prohibition"],
        "affects": ["privacy", "security"]
    },
    "outbuilding_restrictions": {
        "impact_score": 3,
        "affects": ["shed", "garage", "studio"]
    }
}

class CovenantAnalyzer:
    """
    Scores restrictive covenant impact based on buyer's intended use.
    """
    
    def analyze(self, covenants: list, intended_use: dict) -> dict:
        results = {
            "covenants_found": [],
            "total_impact_score": 0,
            "blocks_intended_use": False,
            "removal_feasibility": None,
            "recommendations": []
        }
        
        for covenant in covenants:
            covenant_type = self._classify_covenant(covenant["text"])
            config = COVENANT_IMPACT_MATRIX.get(covenant_type, {})
            
            # Check if covenant blocks intended use
            if intended_use.get("strategy") in config.get("affects", []):
                results["blocks_intended_use"] = True
                results["recommendations"].append({
                    "action": "CRITICAL REVIEW",
                    "reason": f"Covenant may prevent {intended_use['strategy']}",
                    "mitigation": config.get("can_be_removed")
                })
            
            results["covenants_found"].append({
                "text": covenant["text"],
                "type": covenant_type,
                "impact_score": config.get("impact_score", 5),
                "created_date": covenant.get("date"),
                "beneficiary": covenant.get("beneficiary"),
                "removal_cost": config.get("removal_cost"),
                "removal_success_rate": config.get("removal_success_rate")
            })
        
        results["total_impact_score"] = sum(
            c["impact_score"] for c in results["covenants_found"]
        )
        
        return results
```

### 2.3 Caveat Classification & Risk Scoring

**Current Gap:** Binary "individual = HIGH RISK, commercial = LOW RISK" is too simplistic.

```python
CAVEAT_RISK_MATRIX = {
    "commercial_lender": {
        "risk_level": "LOW",
        "typical_entities": ["bank", "credit union", "mortgage provider"],
        "reason": "Standard security for mortgage - will be removed at settlement",
        "action": "Verify discharge arranged for settlement"
    },
    "private_lender": {
        "risk_level": "MEDIUM",
        "typical_entities": ["private individual", "family trust"],
        "reason": "May indicate financial stress, harder to coordinate discharge",
        "action": "Verify lender agrees to discharge"
    },
    "family_member": {
        "risk_level": "HIGH",
        "reason": "Often indicates family dispute or divorce proceedings",
        "action": "Investigate underlying dispute, may delay settlement"
    },
    "builder_contractor": {
        "risk_level": "HIGH",
        "typical_entities": ["builder", "contractor", "tradesperson"],
        "reason": "Unpaid building work - may indicate defects or dispute",
        "action": "Investigate works done, payment status, defect claims"
    },
    "family_court": {
        "risk_level": "CRITICAL",
        "reason": "Property subject to family law proceedings",
        "action": "Cannot proceed until family court orders resolved"
    },
    "deceased_estate_beneficiary": {
        "risk_level": "HIGH",
        "reason": "Beneficiary claiming interest - estate dispute",
        "action": "Verify probate complete, no contested claims"
    },
    "ato_state_revenue": {
        "risk_level": "CRITICAL",
        "typical_entities": ["ATO", "State Revenue Office"],
        "reason": "Tax debt - vendor may be in financial distress",
        "action": "Verify debt will be cleared at settlement"
    },
    "owners_corporation": {
        "risk_level": "MEDIUM",
        "reason": "Unpaid strata levies",
        "action": "Verify arrears and who pays at settlement"
    }
}
```

### 2.4 Section 173 Agreement Detection

**Current Gap:** Not mentioned in your current system.

```python
class Section173Analyzer:
    """
    Section 173 Agreements are binding agreements between landowner and 
    responsible authority (council) that run with the land.
    
    These are CRITICAL because they:
    1. Bind future owners
    2. May require specific works/contributions
    3. May restrict use beyond planning scheme
    4. Are often missed by inexperienced buyers
    """
    
    COMMON_SECTION_173_OBLIGATIONS = {
        "development_contributions": {
            "description": "Payment required before certain permits",
            "typical_amount": "$5,000 - $100,000+",
            "trigger": "Building permit or subdivision"
        },
        "affordable_housing": {
            "description": "Percentage of units must be affordable housing",
            "impact": "Rental restrictions, sale restrictions"
        },
        "car_parking_waiver": {
            "description": "Reduced parking provided, no future requests",
            "impact": "Cannot add parking spaces"
        },
        "heritage_works": {
            "description": "Required restoration/maintenance works",
            "typical_cost": "$50,000 - $500,000+"
        },
        "landscaping_maintenance": {
            "description": "Maintain specific landscaping",
            "ongoing_cost": "Annual maintenance requirement"
        },
        "noise_attenuation": {
            "description": "Maintain noise barriers/double glazing",
            "impact": "Cannot modify certain features"
        },
        "environmental_audit": {
            "description": "Must complete environmental audit before certain uses",
            "trigger": "Change of use to sensitive use"
        }
    }
    
    def analyze(self, title_search: dict) -> dict:
        agreements = self._extract_section_173(title_search)
        
        results = {
            "agreements_found": len(agreements),
            "total_financial_exposure": 0,
            "ongoing_obligations": [],
            "triggered_by_purchase": [],
            "recommendations": []
        }
        
        for agreement in agreements:
            analysis = self._analyze_agreement(agreement)
            results["total_financial_exposure"] += analysis.get("cost_estimate", 0)
            
            if analysis.get("triggered_by_purchase"):
                results["triggered_by_purchase"].append(analysis)
        
        if results["agreements_found"] > 0:
            results["recommendations"].append(
                "MUST obtain copy of Section 173 Agreement from council "
                "and have conveyancer review BEFORE signing contract"
            )
        
        return results
```

---

## CATEGORY 3: PLANNING & ZONING ENHANCEMENTS

### 3.1 Zone-Specific Development Limits

**Current Gap:** You check "heritage overlay" but don't provide the specific mandatory limits that actually matter for development feasibility.

```python
VICTORIAN_RESIDENTIAL_ZONES = {
    "NRZ": {
        "name": "Neighbourhood Residential Zone",
        "mandatory_height": "9m / 2 storeys",
        "mandatory_height_note": "MANDATORY - cannot be varied",
        "purpose": "Protect neighbourhood character, limit growth",
        "garden_area": "Minimum 35% of lot",
        "typical_density": "1-2 dwellings per lot",
        "subdivision_minimum": "Varies by schedule - check",
        "development_potential": "LIMITED",
        "granny_flat": "May be possible subject to schedule",
        "rooming_house": "Usually NOT permitted"
    },
    "GRZ": {
        "name": "General Residential Zone",
        "mandatory_height": "11m / 3 storeys",
        "mandatory_height_note": "MANDATORY - cannot be varied",
        "purpose": "Encourage moderate housing growth",
        "garden_area": "Minimum 35% of lot",
        "typical_density": "2-4 dwellings per lot",
        "development_potential": "MODERATE",
        "granny_flat": "Usually permitted",
        "rooming_house": "Permit required, usually achievable"
    },
    "RGZ": {
        "name": "Residential Growth Zone",
        "mandatory_height": "13.5m / 4 storeys",
        "mandatory_height_note": "Default unless schedule specifies otherwise",
        "purpose": "Substantial housing change in appropriate locations",
        "garden_area": "Varies by schedule",
        "typical_density": "4+ dwellings per lot",
        "development_potential": "HIGH",
        "granny_flat": "Usually permitted",
        "rooming_house": "Usually permitted"
    },
    "MUZ": {
        "name": "Mixed Use Zone",
        "mandatory_height": "None specified - discretionary",
        "purpose": "Mix of residential and commercial",
        "development_potential": "HIGH",
        "commercial_use": "Permitted"
    },
    "LDRZ": {
        "name": "Low Density Residential Zone",
        "minimum_lot_size": "Usually 2,000sqm - 4,000sqm",
        "purpose": "Rural-residential interface",
        "development_potential": "VERY LIMITED",
        "subdivision": "Rarely permitted"
    }
}

PLANNING_OVERLAYS = {
    "HO": {
        "name": "Heritage Overlay",
        "impact": "Permit required for external changes, demolition restricted",
        "cost_impact": "10-30% higher construction costs",
        "approval_time": "2-6 months additional for heritage permit"
    },
    "DDO": {
        "name": "Design and Development Overlay",
        "impact": "Specific built form controls - height, setbacks, materials",
        "check": "Must read schedule for site-specific controls"
    },
    "SBO": {
        "name": "Special Building Overlay",
        "impact": "Overland flow path - flood risk from stormwater",
        "requires": "Floor levels above flood level",
        "insurance_impact": "May increase premiums"
    },
    "LSIO": {
        "name": "Land Subject to Inundation Overlay",
        "impact": "Riverine flood risk - building restrictions apply",
        "requires": "Floor levels 600mm above flood level",
        "insurance_impact": "Significant premium increase or exclusion"
    },
    "BMO": {
        "name": "Bushfire Management Overlay",
        "impact": "BAL assessment required, construction standards",
        "BAL_ratings": ["BAL-LOW", "BAL-12.5", "BAL-19", "BAL-29", "BAL-40", "BAL-FZ"],
        "cost_impact": {
            "BAL-40": "30-50% construction cost increase",
            "BAL-FZ": "Very difficult to build, specialist design required"
        }
    },
    "EAO": {
        "name": "Environmental Audit Overlay",
        "impact": "Contamination risk - audit required before sensitive use",
        "sensitive_uses": ["residential", "childcare", "school"],
        "cost": "$20,000 - $100,000+ for audit",
        "critical": "MUST check before purchasing for residential use"
    },
    "NCO": {
        "name": "Neighbourhood Character Overlay",
        "impact": "Additional design controls for character",
        "check": "Schedule specifies requirements"
    },
    "VPO": {
        "name": "Vegetation Protection Overlay",
        "impact": "Permit required to remove vegetation",
        "cost_impact": "May limit buildable area"
    },
    "PAO": {
        "name": "Public Acquisition Overlay",
        "impact": "Land may be compulsorily acquired for public purpose",
        "risk_level": "CRITICAL - check acquisition timeline"
    }
}
```

### 3.2 VicPlan API Integration

**Current Gap:** You mention VicPlan but don't show integration details.

```python
class VicPlanIntegration:
    """
    Integrates with VicPlan/Planning Maps Online API.
    Provides zone, overlay, and planning scheme information.
    """
    
    BASE_URL = "https://maps.land.vic.gov.au/lvis/services"
    
    async def get_planning_info(self, lat: float, lon: float) -> dict:
        """
        Returns all planning information for a coordinate.
        """
        results = {
            "zone": await self._get_zone(lat, lon),
            "overlays": await self._get_overlays(lat, lon),
            "responsible_authority": await self._get_council(lat, lon),
            "planning_scheme": await self._get_scheme(lat, lon)
        }
        
        # Enrich with zone-specific rules
        zone_code = results["zone"]["code"]
        if zone_code in VICTORIAN_RESIDENTIAL_ZONES:
            results["zone"]["rules"] = VICTORIAN_RESIDENTIAL_ZONES[zone_code]
        
        # Enrich overlays with impact analysis
        for overlay in results["overlays"]:
            if overlay["code"] in PLANNING_OVERLAYS:
                overlay["impact"] = PLANNING_OVERLAYS[overlay["code"]]
        
        # Calculate composite development potential
        results["development_potential"] = self._calculate_development_potential(results)
        
        return results
    
    def _calculate_development_potential(self, planning_info: dict) -> dict:
        """
        Scores overall development potential based on zone + overlays.
        """
        base_potential = planning_info["zone"]["rules"].get("development_potential", "UNKNOWN")
        
        # Overlays that reduce potential
        restrictive_overlays = ["HO", "NCO", "SBO", "LSIO", "BMO", "EAO"]
        restrictions = [o for o in planning_info["overlays"] if o["code"] in restrictive_overlays]
        
        # Overlays that block development
        blocking_overlays = ["PAO"]  # Public Acquisition
        blockers = [o for o in planning_info["overlays"] if o["code"] in blocking_overlays]
        
        if blockers:
            return {"score": 0, "rating": "BLOCKED", "reason": "Public acquisition overlay"}
        
        score_reduction = len(restrictions) * 15  # Each restrictive overlay reduces score
        
        base_scores = {"HIGH": 80, "MODERATE": 60, "LIMITED": 40, "VERY LIMITED": 20}
        final_score = max(0, base_scores.get(base_potential, 50) - score_reduction)
        
        return {
            "score": final_score,
            "rating": self._score_to_rating(final_score),
            "restrictions": restrictions,
            "recommendations": self._get_development_recommendations(planning_info)
        }
```

### 3.3 Building Permit History Cross-Reference

**Current Gap:** You mention "missing Certificate of Final Inspection" but don't show systematic permit analysis.

```python
class BuildingPermitAnalyzer:
    """
    Cross-references building permits from Section 32 against:
    1. Physical inspection findings
    2. Aerial imagery history
    3. Real estate listing photos
    
    Detects potential illegal works.
    """
    
    def analyze(
        self,
        section_32_permits: list,
        physical_inspection: dict,
        aerial_imagery: list,  # Historical imagery from NearMap/Google
        listing_photos: list
    ) -> dict:
        
        results = {
            "permits_found": section_32_permits,
            "structures_detected": [],
            "potential_illegal_works": [],
            "risk_score": 0
        }
        
        # Detect structures from photos and inspection
        detected_structures = self._detect_structures(
            physical_inspection, aerial_imagery, listing_photos
        )
        results["structures_detected"] = detected_structures
        
        # Cross-reference: structures that should have permits
        permit_required_structures = [
            "extension", "deck", "pergola", "carport", "garage",
            "swimming_pool", "spa", "shed_over_10sqm", "granny_flat",
            "second_storey", "basement", "retaining_wall_over_1m"
        ]
        
        for structure in detected_structures:
            if structure["type"] in permit_required_structures:
                # Check if permit exists
                matching_permit = self._find_matching_permit(
                    structure, section_32_permits
                )
                
                if not matching_permit:
                    results["potential_illegal_works"].append({
                        "structure": structure["type"],
                        "detected_from": structure["source"],
                        "estimated_age": structure.get("estimated_age"),
                        "permit_found": False,
                        "risk_level": "HIGH",
                        "consequence": "Council may issue building notice, "
                                      "insurance may not cover, "
                                      "disclosure required on resale"
                    })
                elif not matching_permit.get("final_inspection"):
                    results["potential_illegal_works"].append({
                        "structure": structure["type"],
                        "permit_number": matching_permit["permit_number"],
                        "permit_found": True,
                        "final_inspection": False,
                        "risk_level": "MEDIUM",
                        "consequence": "Works may not comply with permit, "
                                      "occupancy certificate may be required"
                    })
        
        results["risk_score"] = len(results["potential_illegal_works"]) * 20
        
        return results
```

---

## CATEGORY 4: STRATA & CLADDING ENHANCEMENTS

### 4.1 Cladding Risk Assessment

**Current Gap:** You scan for "cladding" keyword but don't integrate with Cladding Safety Victoria data or estimate rectification costs.

```python
class CladdingRiskAssessor:
    """
    Assesses combustible cladding risk for apartments.
    
    Background:
    - Lacrosse Building fire (2014) and Neo200 fire (2019) exposed widespread use
      of combustible cladding in Australian apartments
    - Cladding Safety Victoria managing $600M rectification program
    - 1,200+ private buildings identified as moderate-to-extreme risk
    - Rectification costs: $2,500 - $20,000+ per dwelling
    - Insurance premiums increased up to 4x for affected buildings
    """
    
    RISK_INDICATORS = {
        "building_age": {
            "high_risk_period": (1990, 2019),  # Peak use of ACP
            "reason": "Aluminium Composite Panels (ACP) widely used in this period"
        },
        "building_height": {
            "type_a": {"stories": (3, None), "risk": "Highest scrutiny"},
            "type_b": {"stories": (2, 2), "risk": "Moderate scrutiny"},
            "type_c": {"stories": (1, 1), "risk": "Lower scrutiny"}
        },
        "facade_materials": {
            "high_risk": ["ACP", "aluminium composite", "Alucobond", "Vitrabond"],
            "moderate_risk": ["EPS", "expanded polystyrene", "EIFS"]
        }
    }
    
    async def assess(
        self,
        building_address: str,
        strata_report: dict,
        agm_minutes: list,
        building_photos: list
    ) -> dict:
        
        results = {
            "cladding_risk_level": "UNKNOWN",
            "csv_status": None,  # Cladding Safety Victoria status
            "rectification_status": None,
            "estimated_cost_per_lot": None,
            "insurance_impact": None,
            "recommendations": []
        }
        
        # 1. Check Cladding Safety Victoria database (if accessible)
        csv_status = await self._check_cladding_safety_victoria(building_address)
        if csv_status:
            results["csv_status"] = csv_status
        
        # 2. Analyze strata report for cladding mentions
        strata_cladding = self._analyze_strata_for_cladding(strata_report)
        
        # 3. Analyze AGM minutes for cladding discussions
        minutes_cladding = self._analyze_minutes_for_cladding(agm_minutes)
        
        # 4. Visual assessment from photos (GPT-4o Vision)
        visual_assessment = await self._visual_cladding_assessment(building_photos)
        
        # 5. Check insurance documents for cladding exclusions
        insurance_analysis = self._analyze_insurance(strata_report)
        
        # Combine assessments
        if any([
            csv_status and csv_status["risk_rating"] in ["HIGH", "EXTREME"],
            minutes_cladding["cladding_mentioned"] and minutes_cladding["works_planned"],
            insurance_analysis["cladding_exclusion"]
        ]):
            results["cladding_risk_level"] = "HIGH"
            results["estimated_cost_per_lot"] = self._estimate_rectification_cost(
                strata_report, csv_status
            )
            results["recommendations"].append(
                "CRITICAL: Building has identified cladding issues. "
                "Obtain written confirmation of rectification timeline and "
                "cost allocation before proceeding."
            )
        
        return results
    
    def _analyze_minutes_for_cladding(self, agm_minutes: list) -> dict:
        """
        Scans AGM minutes for cladding-related discussions.
        """
        keywords = [
            "cladding", "facade", "fire safety", "combustible",
            "aluminium composite", "ACP", "rectification",
            "CSV", "Cladding Safety Victoria", "VBA notice"
        ]
        
        mentions = []
        for minutes in agm_minutes:
            text = minutes.get("text", "").lower()
            for keyword in keywords:
                if keyword.lower() in text:
                    mentions.append({
                        "date": minutes["date"],
                        "keyword": keyword,
                        "context": self._extract_context(text, keyword)
                    })
        
        return {
            "cladding_mentioned": len(mentions) > 0,
            "mentions": mentions,
            "works_planned": any("rectification" in m["context"] for m in mentions),
            "cost_mentioned": self._extract_costs(mentions)
        }
```

### 4.2 Enhanced Strata Financial Analysis

**Current Gap:** Basic sinking fund ratio. Need comprehensive financial health scoring.

```python
class StrataFinancialAnalyzer:
    """
    Comprehensive financial health analysis of Owners Corporation.
    """
    
    def analyze(self, oc_certificate: dict, agm_minutes: list, financial_statements: dict) -> dict:
        
        results = {
            "financial_health_score": 0,  # 0-100
            "admin_fund": {},
            "sinking_fund": {},
            "arrears": {},
            "special_levies": {},
            "insurance": {},
            "risks": [],
            "recommendations": []
        }
        
        # 1. Admin Fund Analysis
        admin_fund = oc_certificate.get("admin_fund", {})
        results["admin_fund"] = {
            "balance": admin_fund.get("balance"),
            "annual_budget": admin_fund.get("budget"),
            "months_reserve": admin_fund.get("balance", 0) / max(admin_fund.get("budget", 1) / 12, 1),
            "health": "GOOD" if admin_fund.get("balance", 0) > admin_fund.get("budget", 0) / 4 else "CONCERN"
        }
        
        # 2. Sinking Fund Analysis
        sinking_fund = oc_certificate.get("sinking_fund", {})
        building_value = oc_certificate.get("insured_value", 0)
        
        sinking_ratio = sinking_fund.get("balance", 0) / max(building_value, 1) * 100
        
        results["sinking_fund"] = {
            "balance": sinking_fund.get("balance"),
            "insured_value": building_value,
            "ratio_percent": round(sinking_ratio, 2),
            "health": self._assess_sinking_health(sinking_ratio, oc_certificate),
            "10_year_plan": sinking_fund.get("forecast"),
            "major_works_planned": self._extract_planned_works(sinking_fund, agm_minutes)
        }
        
        # Sinking fund benchmarks
        if sinking_ratio < 0.25:
            results["risks"].append({
                "type": "LOW_SINKING_FUND",
                "severity": "HIGH",
                "detail": f"Sinking fund ratio of {sinking_ratio:.2f}% is below recommended 0.5%",
                "consequence": "Special levy likely for major works"
            })
        
        # 3. Arrears Analysis
        arrears = oc_certificate.get("arrears", {})
        total_lots = oc_certificate.get("total_lots", 1)
        arrears_rate = arrears.get("lots_in_arrears", 0) / total_lots * 100
        
        results["arrears"] = {
            "total_amount": arrears.get("total_amount"),
            "lots_in_arrears": arrears.get("lots_in_arrears"),
            "arrears_rate_percent": round(arrears_rate, 1),
            "health": "CONCERN" if arrears_rate > 10 else "GOOD"
        }
        
        if arrears_rate > 15:
            results["risks"].append({
                "type": "HIGH_ARREARS",
                "severity": "MEDIUM",
                "detail": f"{arrears_rate:.1f}% of lots in arrears",
                "consequence": "Cash flow issues for OC, may affect maintenance"
            })
        
        # 4. Special Levy History
        special_levies = self._extract_special_levies(agm_minutes, financial_statements)
        results["special_levies"] = {
            "history": special_levies,
            "total_5_years": sum(l["amount"] for l in special_levies if l["years_ago"] <= 5),
            "frequency": len(special_levies),
            "health": "CONCERN" if len(special_levies) > 2 else "GOOD"
        }
        
        # 5. Insurance Analysis
        insurance = oc_certificate.get("insurance", {})
        results["insurance"] = {
            "building_sum_insured": insurance.get("building"),
            "public_liability": insurance.get("public_liability"),
            "office_bearers": insurance.get("office_bearers"),
            "excess": insurance.get("excess"),
            "exclusions": insurance.get("exclusions", []),
            "premium_trend": self._analyze_premium_trend(agm_minutes)
        }
        
        # Check for concerning exclusions
        concerning_exclusions = ["cladding", "combustible", "defect", "subsidence"]
        for exclusion in insurance.get("exclusions", []):
            if any(ce in exclusion.lower() for ce in concerning_exclusions):
                results["risks"].append({
                    "type": "INSURANCE_EXCLUSION",
                    "severity": "HIGH",
                    "detail": f"Insurance excludes: {exclusion}",
                    "consequence": "Owners may be personally liable for claims"
                })
        
        # Calculate overall score
        results["financial_health_score"] = self._calculate_health_score(results)
        
        return results
```

### 4.3 By-Law Impact Analysis

**Current Gap:** Not mentioned in your current system.

```python
class ByLawAnalyzer:
    """
    Analyzes Owners Corporation by-laws for restrictions affecting property use.
    """
    
    COMMON_BYLAWS_TO_CHECK = {
        "pets": {
            "check_for": ["no pets", "pet approval required", "pet size limit"],
            "impact": "May prevent keeping pets",
            "common_restrictions": ["no dogs over 10kg", "approval required", "one pet only"]
        },
        "renovations": {
            "check_for": ["renovation approval", "modification approval", "works approval"],
            "impact": "May delay or prevent internal changes",
            "common_restrictions": ["OC approval for floor changes", "no hard floors above ground"]
        },
        "short_term_letting": {
            "check_for": ["short term", "airbnb", "minimum lease", "holiday letting"],
            "impact": "May prevent Airbnb/short-stay use",
            "common_restrictions": ["minimum 6 month lease", "no short term letting"]
        },
        "parking": {
            "check_for": ["parking allocation", "visitor parking", "car space"],
            "impact": "Parking availability and visitor access",
            "common_restrictions": ["one space per lot", "no visitor parking"]
        },
        "moving": {
            "check_for": ["moving hours", "removalist", "lift booking"],
            "impact": "Logistics for move-in",
            "common_restrictions": ["weekday moves only", "lift deposit required"]
        },
        "smoking": {
            "check_for": ["no smoking", "smoke free", "balcony smoking"],
            "impact": "Smoking restrictions",
            "common_restrictions": ["smoke-free building", "no balcony smoking"]
        },
        "noise": {
            "check_for": ["noise", "quiet hours", "music"],
            "impact": "Noise restrictions",
            "common_restrictions": ["quiet hours 10pm-8am", "no audible music"]
        }
    }
    
    def analyze(self, bylaws: list, intended_use: dict) -> dict:
        results = {
            "bylaws_analyzed": len(bylaws),
            "restrictions_found": [],
            "conflicts_with_intended_use": [],
            "recommendations": []
        }
        
        for bylaw_category, config in self.COMMON_BYLAWS_TO_CHECK.items():
            restriction = self._check_bylaw_category(bylaws, config)
            if restriction:
                results["restrictions_found"].append({
                    "category": bylaw_category,
                    "restriction": restriction,
                    "impact": config["impact"]
                })
                
                # Check if conflicts with intended use
                if self._conflicts_with_use(bylaw_category, restriction, intended_use):
                    results["conflicts_with_intended_use"].append({
                        "category": bylaw_category,
                        "restriction": restriction,
                        "intended_use": intended_use.get(bylaw_category),
                        "severity": "HIGH"
                    })
        
        return results
```

---

## CATEGORY 5: ENVIRONMENTAL & CONTAMINATION

### 5.1 Victoria Unearthed Integration

**Current Gap:** Not mentioned in your system.

```python
class ContaminationAssessor:
    """
    Assesses contamination risk using Victoria Unearthed and historical records.
    
    Victoria Unearthed consolidates:
    - Priority Sites Register (EPA notices)
    - EPA licensed sites
    - Environmental audits
    - Historical business listings (Sands & McDougall 1896-1974)
    """
    
    HIGH_RISK_HISTORICAL_USES = [
        "petrol station", "service station", "fuel depot",
        "dry cleaner", "laundry", "metal plating",
        "tannery", "leather works",
        "printing works", "printer",
        "chemical manufacturer", "paint manufacturer",
        "factory", "manufacturing",
        "gasworks",
        "landfill", "tip",
        "abattoir", "meatworks",
        "timber treatment", "sawmill"
    ]
    
    async def assess(self, lat: float, lon: float, address: str) -> dict:
        results = {
            "contamination_risk": "UNKNOWN",
            "priority_sites_register": None,
            "environmental_audits": [],
            "epa_licensed_sites": [],
            "historical_uses": [],
            "eao_overlay": False,
            "recommendations": []
        }
        
        # 1. Check Priority Sites Register
        psr = await self._check_priority_sites_register(lat, lon)
        if psr:
            results["priority_sites_register"] = psr
            results["contamination_risk"] = "HIGH"
            results["recommendations"].append(
                "CRITICAL: Property on Priority Sites Register. "
                "Active contamination management required."
            )
        
        # 2. Check for Environmental Audits
        audits = await self._check_environmental_audits(lat, lon)
        results["environmental_audits"] = audits
        
        # 3. Check EPA licensed sites nearby
        epa_sites = await self._check_epa_licensed_sites(lat, lon, radius_m=500)
        results["epa_licensed_sites"] = epa_sites
        
        # 4. Check historical uses (Sands & McDougall directories)
        historical = await self._check_historical_uses(address)
        results["historical_uses"] = historical
        
        for use in historical:
            if any(risk in use["business_type"].lower() for risk in self.HIGH_RISK_HISTORICAL_USES):
                results["contamination_risk"] = max(
                    results["contamination_risk"], 
                    "MEDIUM" if results["contamination_risk"] == "UNKNOWN" else results["contamination_risk"]
                )
                results["recommendations"].append(
                    f"Historical {use['business_type']} at this location ({use['year']}). "
                    "Recommend contamination assessment before purchase."
                )
        
        # 5. Check for Environmental Audit Overlay
        eao = await self._check_planning_overlay(lat, lon, "EAO")
        if eao:
            results["eao_overlay"] = True
            results["contamination_risk"] = "HIGH"
            results["recommendations"].append(
                "Environmental Audit Overlay applies. "
                "Environmental audit REQUIRED before residential use. "
                "Cost: $20,000 - $100,000+"
            )
        
        return results
```

---

## CATEGORY 6: FINANCIAL ANALYSIS ENHANCEMENTS

### 6.1 Comparable Sales Analysis

**Current Gap:** You use CoreLogic AVM but don't show comparable sales or price per sqm analysis.

```python
class ComparableSalesAnalyzer:
    """
    Analyzes comparable sales to validate asking price.
    More sophisticated than AVM alone.
    """
    
    async def analyze(
        self,
        subject_property: dict,
        corelogic_client: CoreLogicClient
    ) -> dict:
        
        # Define search parameters
        search_params = {
            "suburb": subject_property["suburb"],
            "property_type": subject_property["property_type"],
            "bedrooms_range": (
                subject_property["bedrooms"] - 1,
                subject_property["bedrooms"] + 1
            ),
            "land_size_range": (
                subject_property["land_size"] * 0.8,
                subject_property["land_size"] * 1.2
            ),
            "sold_within_months": 6,
            "distance_km": 2
        }
        
        # Get comparable sales
        comparables = await corelogic_client.get_comparable_sales(search_params)
        
        results = {
            "comparables_found": len(comparables),
            "median_sale_price": None,
            "price_per_sqm_land": {},
            "price_per_sqm_building": {},
            "subject_vs_comparables": {},
            "recommendations": []
        }
        
        if comparables:
            # Calculate metrics
            prices = [c["sale_price"] for c in comparables]
            results["median_sale_price"] = statistics.median(prices)
            results["mean_sale_price"] = statistics.mean(prices)
            results["min_sale_price"] = min(prices)
            results["max_sale_price"] = max(prices)
            
            # Price per sqm (land)
            land_sqm_prices = [
                c["sale_price"] / c["land_size"] 
                for c in comparables 
                if c.get("land_size", 0) > 0
            ]
            if land_sqm_prices:
                results["price_per_sqm_land"] = {
                    "median": statistics.median(land_sqm_prices),
                    "subject": subject_property["asking_price"] / subject_property["land_size"],
                    "percentile": self._calculate_percentile(
                        subject_property["asking_price"] / subject_property["land_size"],
                        land_sqm_prices
                    )
                }
            
            # Compare subject to comparables
            asking_price = subject_property["asking_price"]
            median_price = results["median_sale_price"]
            
            premium_discount = ((asking_price - median_price) / median_price) * 100
            
            results["subject_vs_comparables"] = {
                "asking_price": asking_price,
                "median_comparable": median_price,
                "premium_discount_percent": round(premium_discount, 1),
                "assessment": self._assess_pricing(premium_discount)
            }
            
            # Add each comparable with details
            results["comparables"] = [
                {
                    "address": c["address"],
                    "sale_price": c["sale_price"],
                    "sale_date": c["sale_date"],
                    "days_on_market": c.get("days_on_market"),
                    "bedrooms": c["bedrooms"],
                    "bathrooms": c["bathrooms"],
                    "land_size": c["land_size"],
                    "building_size": c.get("building_size"),
                    "distance_km": c["distance_km"],
                    "price_per_sqm_land": c["sale_price"] / c["land_size"] if c.get("land_size") else None
                }
                for c in sorted(comparables, key=lambda x: x["distance_km"])[:10]
            ]
        
        return results
    
    def _assess_pricing(self, premium_discount: float) -> str:
        if premium_discount < -10:
            return "SIGNIFICANTLY BELOW MARKET - investigate why"
        elif premium_discount < -5:
            return "BELOW MARKET - potential value"
        elif premium_discount < 5:
            return "AT MARKET - fair pricing"
        elif premium_discount < 10:
            return "ABOVE MARKET - negotiate"
        else:
            return "SIGNIFICANTLY ABOVE MARKET - strong negotiation needed"
```

### 6.2 Enhanced Cash Flow Model

**Current Gap:** Basic yield calculation. Need comprehensive investor cash flow model.

```python
class InvestorCashFlowModel:
    """
    Comprehensive cash flow model for investment property analysis.
    """
    
    def calculate(
        self,
        purchase_price: float,
        weekly_rent: float,
        outgoings: dict,  # From Section 32 / strata report
        finance_params: dict,
        investor_params: dict
    ) -> dict:
        
        # === INCOME ===
        annual_rent = weekly_rent * 52
        vacancy_rate = investor_params.get("vacancy_rate", 0.02)  # 2% default
        effective_rent = annual_rent * (1 - vacancy_rate)
        
        # === OUTGOINGS ===
        council_rates = outgoings.get("council_rates", 0)
        water_rates = outgoings.get("water_rates", 0)
        strata_levies = outgoings.get("strata_levies", 0) * 4  # Quarterly to annual
        insurance = outgoings.get("landlord_insurance", purchase_price * 0.002)  # Estimate if not provided
        property_management = effective_rent * investor_params.get("pm_rate", 0.07)  # 7% default
        repairs_maintenance = purchase_price * 0.005  # 0.5% rule of thumb
        
        # Land tax (Victoria tiered system)
        land_tax = self._calculate_land_tax(
            outgoings.get("land_value", purchase_price * 0.4),
            investor_params.get("total_land_holdings", 0)
        )
        
        total_outgoings = (
            council_rates + water_rates + strata_levies + 
            insurance + property_management + repairs_maintenance + land_tax
        )
        
        # === FINANCE ===
        lvr = finance_params.get("lvr", 0.8)
        interest_rate = finance_params.get("interest_rate", 0.065)
        loan_type = finance_params.get("loan_type", "interest_only")
        
        loan_amount = purchase_price * lvr
        deposit_required = purchase_price * (1 - lvr)
        
        if loan_type == "interest_only":
            annual_interest = loan_amount * interest_rate
            annual_principal = 0
        else:  # principal_and_interest
            # 30 year P&I calculation
            monthly_rate = interest_rate / 12
            num_payments = 360
            monthly_payment = loan_amount * (
                monthly_rate * (1 + monthly_rate)**num_payments
            ) / ((1 + monthly_rate)**num_payments - 1)
            annual_payment = monthly_payment * 12
            annual_interest = loan_amount * interest_rate  # Approximate first year
            annual_principal = annual_payment - annual_interest
        
        # === CASH FLOW ===
        net_operating_income = effective_rent - total_outgoings
        pre_tax_cash_flow = net_operating_income - annual_interest - annual_principal
        
        # === TAX IMPACT ===
        # Depreciation (simplified - recommend QS report)
        if outgoings.get("building_year"):
            building_age = 2025 - outgoings["building_year"]
            if building_age < 40:  # Post-1985 building
                building_value = purchase_price * 0.6  # Estimate building component
                annual_depreciation = building_value * 0.025  # 2.5% p.a.
            else:
                annual_depreciation = 5000  # Plant & equipment only
        else:
            annual_depreciation = 5000  # Conservative estimate
        
        # Deductions
        total_deductions = (
            total_outgoings + annual_interest + annual_depreciation
        )
        
        # Taxable income impact
        taxable_income_impact = effective_rent - total_deductions
        
        marginal_tax_rate = investor_params.get("marginal_tax_rate", 0.37)
        
        if taxable_income_impact < 0:
            # Negative gearing benefit
            tax_benefit = abs(taxable_income_impact) * marginal_tax_rate
            after_tax_cash_flow = pre_tax_cash_flow + tax_benefit
            gearing_status = "NEGATIVE"
        else:
            tax_liability = taxable_income_impact * marginal_tax_rate
            after_tax_cash_flow = pre_tax_cash_flow - tax_liability
            gearing_status = "POSITIVE"
        
        # === YIELDS ===
        gross_yield = (annual_rent / purchase_price) * 100
        net_yield = (net_operating_income / purchase_price) * 100
        
        # === RETURNS ===
        equity_invested = deposit_required + self._calculate_acquisition_costs(purchase_price)
        cash_on_cash_return = (after_tax_cash_flow / equity_invested) * 100
        
        return {
            "summary": {
                "gross_yield": round(gross_yield, 2),
                "net_yield": round(net_yield, 2),
                "cash_on_cash_return": round(cash_on_cash_return, 2),
                "gearing_status": gearing_status,
                "weekly_cash_flow": round(after_tax_cash_flow / 52, 2),
                "monthly_cash_flow": round(after_tax_cash_flow / 12, 2),
                "annual_cash_flow": round(after_tax_cash_flow, 2)
            },
            "income": {
                "weekly_rent": weekly_rent,
                "annual_rent": annual_rent,
                "vacancy_allowance": annual_rent * vacancy_rate,
                "effective_rent": effective_rent
            },
            "outgoings": {
                "council_rates": council_rates,
                "water_rates": water_rates,
                "strata_levies": strata_levies * 4 if strata_levies else 0,
                "insurance": insurance,
                "property_management": property_management,
                "repairs_maintenance": repairs_maintenance,
                "land_tax": land_tax,
                "total": total_outgoings
            },
            "finance": {
                "purchase_price": purchase_price,
                "loan_amount": loan_amount,
                "deposit_required": deposit_required,
                "lvr": lvr * 100,
                "interest_rate": interest_rate * 100,
                "annual_interest": annual_interest,
                "annual_principal": annual_principal
            },
            "tax": {
                "annual_depreciation": annual_depreciation,
                "total_deductions": total_deductions,
                "taxable_income_impact": taxable_income_impact,
                "marginal_tax_rate": marginal_tax_rate * 100,
                "tax_benefit_or_liability": tax_benefit if gearing_status == "NEGATIVE" else -tax_liability
            },
            "acquisition_costs": self._get_acquisition_costs_breakdown(purchase_price)
        }
    
    def _calculate_land_tax(self, land_value: float, total_holdings: float) -> float:
        """
        Victorian land tax (2024-25 rates).
        Calculated on total taxable land holdings.
        """
        total_land = land_value + total_holdings
        
        # General rates (not principal residence, not trust)
        if total_land <= 50000:
            return 0
        elif total_land <= 100000:
            return (total_land - 50000) * 0.0002
        elif total_land <= 300000:
            return 500 + (total_land - 100000) * 0.0005
        elif total_land <= 600000:
            return 1500 + (total_land - 300000) * 0.001
        elif total_land <= 1000000:
            return 4500 + (total_land - 600000) * 0.0015
        elif total_land <= 1800000:
            return 10500 + (total_land - 1000000) * 0.002
        elif total_land <= 3000000:
            return 26500 + (total_land - 1800000) * 0.0025
        else:
            return 56500 + (total_land - 3000000) * 0.0055
        
        # Return proportional amount for this property
        return (land_value / total_land) * total_tax if total_land > 0 else 0
```

---

## CATEGORY 7: RISK SCORING ENHANCEMENTS

### 7.1 Weighted Risk Scoring Framework

**Current Gap:** Binary/categorical ratings. Need quantified, weighted scoring.

```python
class PropertyRiskScorer:
    """
    Quantified risk scoring with weighted categories.
    Produces a 0-100 risk score where higher = more risky.
    """
    
    RISK_WEIGHTS = {
        "legal": {
            "weight": 0.25,
            "factors": {
                "caveat_risk": 0.20,
                "covenant_impact": 0.15,
                "easement_building_conflict": 0.15,
                "section_32_completeness": 0.20,
                "special_conditions_risk": 0.15,
                "proprietor_mismatch": 0.15
            }
        },
        "title_encumbrance": {
            "weight": 0.15,
            "factors": {
                "caveat_severity": 0.30,
                "covenant_blocks_use": 0.30,
                "section_173_obligations": 0.20,
                "easement_extent": 0.20
            }
        },
        "planning": {
            "weight": 0.15,
            "factors": {
                "development_potential_mismatch": 0.25,
                "overlay_restrictions": 0.25,
                "illegal_works_detected": 0.30,
                "heritage_impact": 0.20
            }
        },
        "physical": {
            "weight": 0.15,
            "factors": {
                "structural_defects": 0.35,
                "termite_risk": 0.20,
                "asbestos_risk": 0.15,
                "roof_condition": 0.15,
                "illegal_works": 0.15
            }
        },
        "strata": {
            "weight": 0.10,
            "factors": {
                "financial_health": 0.30,
                "cladding_risk": 0.30,
                "special_levy_history": 0.20,
                "bylaw_conflicts": 0.20
            },
            "applies_to": ["apartment", "townhouse", "unit"]
        },
        "environmental": {
            "weight": 0.10,
            "factors": {
                "flood_risk": 0.25,
                "bushfire_risk": 0.25,
                "contamination_risk": 0.25,
                "flight_path": 0.15,
                "social_housing_density": 0.10
            }
        },
        "financial": {
            "weight": 0.10,
            "factors": {
                "price_vs_comparables": 0.40,
                "yield_adequacy": 0.30,
                "cash_flow_viability": 0.30
            }
        }
    }
    
    def calculate_risk_score(self, all_analyses: dict) -> dict:
        """
        Calculates composite risk score from all analysis components.
        """
        category_scores = {}
        
        for category, config in self.RISK_WEIGHTS.items():
            # Check if category applies to this property type
            if "applies_to" in config:
                if all_analyses.get("property_type") not in config["applies_to"]:
                    continue
            
            category_score = 0
            factor_details = []
            
            for factor, factor_weight in config["factors"].items():
                factor_score = self._get_factor_score(all_analyses, category, factor)
                weighted_score = factor_score * factor_weight
                category_score += weighted_score
                
                factor_details.append({
                    "factor": factor,
                    "raw_score": factor_score,
                    "weight": factor_weight,
                    "weighted_score": weighted_score
                })
            
            category_scores[category] = {
                "score": round(category_score, 1),
                "weight": config["weight"],
                "weighted_contribution": round(category_score * config["weight"], 1),
                "factors": factor_details
            }
        
        # Calculate total weighted score
        total_score = sum(
            cat["weighted_contribution"] 
            for cat in category_scores.values()
        )
        
        # Normalize to 0-100
        max_possible = sum(
            config["weight"] * 100 
            for cat, config in self.RISK_WEIGHTS.items()
            if "applies_to" not in config or 
               all_analyses.get("property_type") in config.get("applies_to", [])
        )
        
        normalized_score = (total_score / max_possible) * 100 if max_possible > 0 else 50
        
        return {
            "overall_risk_score": round(normalized_score, 1),
            "risk_rating": self._score_to_rating(normalized_score),
            "category_breakdown": category_scores,
            "top_risk_factors": self._get_top_risks(category_scores),
            "confidence_level": self._calculate_confidence(all_analyses)
        }
    
    def _score_to_rating(self, score: float) -> str:
        if score < 20:
            return "LOW"
        elif score < 40:
            return "MODERATE"
        elif score < 60:
            return "ELEVATED"
        elif score < 80:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _get_top_risks(self, category_scores: dict, n: int = 5) -> list:
        """
        Returns the top N risk factors across all categories.
        """
        all_factors = []
        for category, data in category_scores.items():
            for factor in data["factors"]:
                all_factors.append({
                    "category": category,
                    "factor": factor["factor"],
                    "score": factor["raw_score"],
                    "impact": factor["weighted_score"]
                })
        
        return sorted(all_factors, key=lambda x: x["score"], reverse=True)[:n]
```

---

## CATEGORY 8: REGULATORY COMPLIANCE

### 8.1 Statement of Information Analyzer (Underquoting Detection)

**Current Gap:** Not mentioned. Victorian law requires agents to provide Statement of Information with pricing.

```python
class StatementOfInformationAnalyzer:
    """
    Analyzes Victorian Statement of Information for underquoting indicators.
    
    Since 2017, Victorian agents must provide:
    - Single advertised price OR price range (max 10% spread)
    - Three comparable sales within 2km and 6 months
    
    New 2025 laws require publishing vendor's actual reserve 7 days before auction.
    Consumer Affairs Victoria has issued $2.3M+ in fines since 2022.
    """
    
    def analyze(
        self,
        soi: dict,  # Statement of Information
        actual_comparables: list,  # Our independent comparable sales
        final_sale_price: Optional[float] = None
    ) -> dict:
        
        results = {
            "quoted_price_range": soi.get("price_range"),
            "comparable_sales_provided": soi.get("comparable_sales", []),
            "underquoting_indicators": [],
            "cherry_picking_indicators": [],
            "recommendations": []
        }
        
        # Check price range spread
        price_range = soi.get("price_range", {})
        if price_range:
            low = price_range.get("low")
            high = price_range.get("high")
            spread = ((high - low) / low) * 100 if low else 0
            
            if spread > 10:
                results["underquoting_indicators"].append({
                    "type": "EXCESSIVE_RANGE",
                    "detail": f"Price range spread of {spread:.1f}% exceeds legal maximum of 10%"
                })
        
        # Compare agent's comparables to actual market
        if actual_comparables and soi.get("comparable_sales"):
            agent_median = statistics.median([
                c["sale_price"] for c in soi["comparable_sales"]
            ])
            actual_median = statistics.median([
                c["sale_price"] for c in actual_comparables
            ])
            
            # Agent comparables significantly below market
            if agent_median < actual_median * 0.9:  # >10% below
                results["cherry_picking_indicators"].append({
                    "type": "LOW_COMPARABLES",
                    "detail": f"Agent's comparables median ${agent_median:,.0f} is "
                             f"{((actual_median - agent_median) / actual_median) * 100:.1f}% "
                             f"below actual market median ${actual_median:,.0f}",
                    "interpretation": "Agent may have selected lower comparables to justify "
                                     "lower quoted price range"
                })
        
        # If we know final sale price, check against quoted range
        if final_sale_price and price_range:
            if final_sale_price > price_range.get("high", 0) * 1.1:
                results["underquoting_indicators"].append({
                    "type": "SALE_EXCEEDED_QUOTE",
                    "detail": f"Sale price ${final_sale_price:,.0f} exceeded quoted range "
                             f"by {((final_sale_price - price_range['high']) / price_range['high']) * 100:.1f}%"
                })
        
        return results
```

### 8.2 Consumer Affairs Victoria Due Diligence Checklist

**Current Gap:** Not implementing the mandatory checklist.

```python
CAV_DUE_DILIGENCE_CHECKLIST = {
    """
    Consumer Affairs Victoria Section 33B mandatory checklist items.
    Agents must provide this checklist to prospective buyers.
    """
    
    "property_information": [
        "Certificate of Title search",
        "Company or business name search (if applicable)",
        "Plan of subdivision / strata plan",
        "Body corporate records (if applicable)",
        "Building approvals and permits",
        "Council zoning certificate"
    ],
    "financial_information": [
        "Outstanding rates, taxes, charges",
        "Land tax status",
        "Outstanding body corporate fees (if applicable)"
    ],
    "physical_information": [
        "Building inspection report",
        "Pest inspection report",
        "Swimming pool compliance (if applicable)"
    ],
    "planning_information": [
        "Current zoning",
        "Planning overlays",
        "Proposed developments nearby"
    ],
    "safety_information": [
        "Flood risk",
        "Bushfire risk",
        "Contamination risk"
    ]
}

class DueDiligenceComplianceTracker:
    """
    Tracks completion of due diligence against CAV checklist.
    """
    
    def get_completion_status(self, property_analysis: dict) -> dict:
        completed = []
        pending = []
        not_applicable = []
        
        for category, items in CAV_DUE_DILIGENCE_CHECKLIST.items():
            for item in items:
                status = self._check_item_status(item, property_analysis)
                if status == "COMPLETE":
                    completed.append(item)
                elif status == "N/A":
                    not_applicable.append(item)
                else:
                    pending.append(item)
        
        total_applicable = len(completed) + len(pending)
        completion_rate = len(completed) / total_applicable * 100 if total_applicable > 0 else 0
        
        return {
            "completion_rate": round(completion_rate, 1),
            "completed": completed,
            "pending": pending,
            "not_applicable": not_applicable,
            "ready_for_purchase": completion_rate >= 90,
            "recommendations": self._get_priority_actions(pending)
        }
```

---

## CATEGORY 9: PROCESS ORCHESTRATION

### 9.1 Due Diligence Timeline Tracker

**Current Gap:** No deadline tracking or workflow orchestration.

```python
class DueDiligenceTimeline:
    """
    Tracks critical deadlines and orchestrates due diligence workflow.
    """
    
    def create_timeline(
        self,
        contract_signed_date: date,
        cooling_off_expires: Optional[date],
        settlement_date: date,
        special_conditions: list
    ) -> dict:
        
        timeline = {
            "critical_deadlines": [],
            "recommended_actions": [],
            "delegated_tasks": []
        }
        
        # Cooling-off deadline
        if cooling_off_expires:
            days_to_cooling_off = (cooling_off_expires - date.today()).days
            timeline["critical_deadlines"].append({
                "name": "Cooling-Off Expires",
                "date": cooling_off_expires,
                "days_remaining": days_to_cooling_off,
                "urgency": "CRITICAL" if days_to_cooling_off <= 1 else "HIGH",
                "action": "Complete all critical due diligence before this date"
            })
        
        # Finance approval deadline
        finance_condition = next(
            (c for c in special_conditions if c["type"] == "subject_to_finance"),
            None
        )
        if finance_condition:
            timeline["critical_deadlines"].append({
                "name": "Finance Approval Due",
                "date": finance_condition["deadline"],
                "days_remaining": (finance_condition["deadline"] - date.today()).days,
                "action": "Obtain formal loan approval or invoke condition"
            })
        
        # Building inspection deadline
        building_condition = next(
            (c for c in special_conditions if c["type"] == "subject_to_building_inspection"),
            None
        )
        if building_condition:
            timeline["critical_deadlines"].append({
                "name": "Building Inspection Due",
                "date": building_condition["deadline"],
                "days_remaining": (building_condition["deadline"] - date.today()).days,
                "action": "Complete building inspection and review report"
            })
        
        # Settlement
        days_to_settlement = (settlement_date - date.today()).days
        timeline["critical_deadlines"].append({
            "name": "Settlement",
            "date": settlement_date,
            "days_remaining": days_to_settlement,
            "urgency": "HIGH" if days_to_settlement <= 14 else "NORMAL"
        })
        
        # Recommended action sequence
        timeline["recommended_actions"] = self._generate_action_sequence(
            date.today(),
            cooling_off_expires,
            settlement_date,
            special_conditions
        )
        
        # Tasks to delegate
        timeline["delegated_tasks"] = [
            {
                "task": "Contract review and advice",
                "delegate_to": "Conveyancer/Solicitor",
                "deadline": cooling_off_expires or settlement_date - timedelta(days=30),
                "status": "PENDING"
            },
            {
                "task": "Building and pest inspection",
                "delegate_to": "Registered Building Inspector",
                "deadline": building_condition["deadline"] if building_condition else settlement_date - timedelta(days=21),
                "status": "PENDING"
            },
            {
                "task": "Finance application",
                "delegate_to": "Mortgage Broker",
                "deadline": finance_condition["deadline"] if finance_condition else settlement_date - timedelta(days=21),
                "status": "PENDING"
            },
            {
                "task": "Strata search",
                "delegate_to": "Conveyancer",
                "deadline": cooling_off_expires or settlement_date - timedelta(days=21),
                "status": "PENDING",
                "applies_if": "property_type IN ['apartment', 'townhouse', 'unit']"
            }
        ]
        
        return timeline
```

### 9.2 Specialist Referral Triggers

**Current Gap:** System doesn't know when to recommend specialist reports.

```python
SPECIALIST_REFERRAL_TRIGGERS = {
    "structural_engineer": {
        "triggers": [
            {"condition": "crack_width_mm > 2", "description": "Cracks exceed 2mm"},
            {"condition": "foundation_movement_detected", "description": "Signs of foundation movement"},
            {"condition": "floor_unevenness > 10mm_per_meter", "description": "Significant floor slope"},
            {"condition": "wall_bulging_detected", "description": "Bulging or bowing walls"}
        ],
        "typical_cost": "$500 - $1,500",
        "urgency": "HIGH"
    },
    "rising_damp_specialist": {
        "triggers": [
            {"condition": "efflorescence_detected", "description": "Salt deposits on walls"},
            {"condition": "peeling_paint_lower_walls", "description": "Paint peeling at base of walls"},
            {"condition": "musty_smell_detected", "description": "Persistent musty odor"}
        ],
        "typical_cost": "$300 - $800 for assessment",
        "urgency": "MEDIUM"
    },
    "electrical_inspector": {
        "triggers": [
            {"condition": "building_age > 30", "description": "Property over 30 years old"},
            {"condition": "switchboard_type == 'ceramic_fuses'", "description": "Old ceramic fuse switchboard"},
            {"condition": "wiring_visible_deterioration", "description": "Visible wiring deterioration"}
        ],
        "typical_cost": "$200 - $500",
        "urgency": "HIGH"
    },
    "asbestos_assessor": {
        "triggers": [
            {"condition": "building_age < 1990", "description": "Built before 1990"},
            {"condition": "suspected_asbestos_materials", "description": "Materials that may contain asbestos"},
            {"condition": "renovation_planned", "description": "Planning renovations on older property"}
        ],
        "typical_cost": "$300 - $800 for inspection, $50-100 per sample tested",
        "urgency": "HIGH before renovation"
    },
    "environmental_auditor": {
        "triggers": [
            {"condition": "eao_overlay", "description": "Environmental Audit Overlay applies"},
            {"condition": "contamination_risk_high", "description": "High contamination risk identified"},
            {"condition": "historical_industrial_use", "description": "Former industrial use"}
        ],
        "typical_cost": "$20,000 - $100,000+",
        "urgency": "CRITICAL for residential use"
    },
    "quantity_surveyor": {
        "triggers": [
            {"condition": "investment_property", "description": "Purchasing as investment"},
            {"condition": "building_age < 40", "description": "Built after 1985 for building depreciation"}
        ],
        "typical_cost": "$500 - $800",
        "benefit": "Depreciation schedule can save $5,000-15,000+ in tax over holding period"
    },
    "heritage_architect": {
        "triggers": [
            {"condition": "heritage_overlay", "description": "Heritage overlay applies"},
            {"condition": "planning_external_changes", "description": "Planning external modifications"}
        ],
        "typical_cost": "$2,000 - $10,000 for heritage impact statement",
        "urgency": "Required before works"
    }
}
```

---

## IMPLEMENTATION PRIORITY

### Phase 1: Critical (Week 1-2)
1. Section 32 Completeness Checker
2. Cooling-Off Calculator
3. Weighted Risk Scoring Framework
4. Due Diligence Timeline Tracker

### Phase 2: High (Week 3-4)
5. Special Conditions Analyzer
6. Comprehensive Easement Analysis
7. Restrictive Covenant Impact Scoring
8. Enhanced Strata Financial Analysis

### Phase 3: Medium (Week 5-6)
9. Stamp Duty Calculator
10. Comparable Sales Analysis
11. Cladding Risk Assessment
12. VicPlan API deep integration

### Phase 4: Enhancement (Week 7-8)
13. Victoria Unearthed Integration
14. Statement of Information Analyzer
15. Investor Cash Flow Model enhancements
16. Specialist Referral Automation

---

## Quick Wins for Pathway Demo

If you need to impress Pathway Property quickly, focus on:

1. **Section 32 Completeness Checker** - Immediate risk identification
2. **Cooling-Off Deadline Calculator** - Operational value
3. **Weighted Risk Score** - Professional-looking dashboard output
4. **Cladding Risk Flag** - Shows market awareness
5. **Stamp Duty Calculator** - Every buyer needs this

These five features demonstrate deep Victorian market knowledge and immediate practical value.
