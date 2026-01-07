# Pathway Property MVP - Complete Feature Specification

## Philosophy

**Local-First, Production-Accurate**
- Runs entirely on localhost (no cloud infra complexity)
- Same premium APIs = same accuracy as production
- SQLite + local files = zero deployment overhead
- When ready for cloud: swap SQLite → Postgres, local files → S3

---

## Complete Feature Audit

### ✅ Implemented in This MVP | ❌ Gap to Fill

---

## STREET LEVEL ANALYSIS (Gatekeeper)

From `business-idea-extended.txt` - The "Fail Fast" filter before document processing.

| Feature | Status | Implementation |
|---------|--------|----------------|
| Social Housing Density Check | ✅ | ABS Census API → SA1 lookup → % state authority landlords |
| Flight Path Check (ANEF/N70) | ✅ | Airservices Australia WFS → point-in-polygon |
| Flood Risk (1% AEP) | ✅ | Geoscape Buildings API → building-level flood |
| Bushfire Risk (BAL Rating) | ✅ | Geoscape Buildings API → BAL-12.5 to FZ |
| Zoning Validation | ✅ | VicPlan/NSW ePlanning API → zone code match |
| Heritage Overlay Detection | ✅ | VicPlan API → HO overlay check |
| Design & Development Overlay | ✅ | VicPlan API → DDO height/setback limits |

### Kill Criteria (Hard-coded Business Logic)

| Rule | Threshold | Action |
|------|-----------|--------|
| **Social Housing Cluster** | >15% in SA1 | AUTO REVIEW |
| **Social Housing Street** | >20% on street | AUTO KILL |
| **Flight Path Noise** | ANEF >20 or N70 >20 flights/day | AUTO KILL |
| **Flood Risk** | 1% AEP building intersection | AUTO KILL |
| **Bushfire** | BAL-40 or Flame Zone | RED FLAG (cost buffer) |
| **Yield Floor** | Gross Yield <4% | WARNING (unless capital growth) |

---

## ASSET LEVEL ANALYSIS (Deep Dive)

### Legal Pillar - Section 32 / Contract Extraction

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Title Verification** | ✅ | Extract "Registered Proprietor" from Register Search Statement |
| **Vendor/Proprietor Mismatch** | ✅ | Flag if vendor ≠ proprietor (deceased estate, Grant of Probate) |
| **Mortgage Detection** | ✅ | List all registered mortgages |
| **Caveat Extraction** | ✅ | Extract Caveator name + Grounds of Claim |
| **Caveat Risk Classification** | ✅ | Commercial lender = low risk, Individual = HIGH RISK |
| **Restrictive Covenants** | ✅ | Extract + flag development-killing clauses ("one dwelling only") |
| **Easement Detection** | ✅ | List all easements + location from Plan of Subdivision |
| **Building Permit Validation** | ✅ | Extract permits from last 7 years |
| **Illegal Works Inference** | ✅ | CV detects structure (deck/pool) + no permit = HIGH RISK |
| **Owner-Builder Check** | ✅ | Section 137B Defect Report required? Flag if missing |
| **Special Conditions Extraction** | ✅ | Extract all special conditions verbatim |
| **Cooling-Off Waiver (66W)** | ✅ | Detect 66W certificate = due diligence must be pre-signed |
| **Planning Certificate Cross-Check** | ✅ | Compare stated zone vs VicPlan API (may be outdated) |

### Legal Pillar - NSW Specific

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Section 10.7 Certificate** | ✅ | Parse Part 2 for Bushfire/Flood Prone |
| **Complying Development Check** | ✅ | Can granny flat be fast-tracked? |
| **Sewer Diagram Analysis** | ✅ | Flag Sydney Water asset under building envelope |

### Legal Pillar - Title Issues

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Life Estate Detection** | ✅ | Flag "Life Estate" title = hard to finance |
| **Company Share Title** | ✅ | Flag company title = hard to finance |

---

### Strata / Owners Corporation Analysis

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Admin Fund Levy Extraction** | ✅ | Extract quarterly admin levy |
| **Capital Works Fund Extraction** | ✅ | Extract sinking fund balance |
| **Sinking Fund Ratio Check** | ✅ | Balance vs insured value → special levy risk |
| **AGM Minutes Keyword Search** | ✅ | Scan for: cladding, water ingress, legal action, VCAT/NCAT, defects |
| **Maintenance Pattern Detection** | ✅ | Frequent "pump failure", "lift breakdown" = chronic issues |
| **Pet Restriction Check** | ✅ | Check By-Laws for pet prohibitions |
| **Insurance Details** | ✅ | Extract building insurance coverage |

---

### Specialized Investment Vehicles

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Rooming House Registration** | ✅ | Verify on Public Register of Rooming Houses |
| **Class 1b Building Classification** | ✅ | Required if >12 residents or >300m² |
| **Essential Safety Measures Report** | ✅ | Flag missing AESMR (fire safety compliance) |
| **SMSF Arm's Length Check** | ✅ | Flag if vendor surname = purchaser surname |
| **SMSF Borrowing Restriction** | ✅ | Flag vacant land for development (SMSF can't borrow to build) |

---

### Physical Pillar - Defect Detection

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Crack Detection** | ✅ | GPT-4o Vision on listing photos + building report |
| **Water Stain Detection** | ✅ | GPT-4o Vision → "Roof Leak Risk" |
| **Mould Detection** | ✅ | GPT-4o Vision |
| **Salt Damp / Efflorescence** | ✅ | GPT-4o Vision |
| **Termite Damage Cross-Check** | ✅ | Pest report + missing termite barrier in S32 = HIGH RISK |
| **Illegal Works Visual Check** | ✅ | CV detects modern deck/pool + no permit |

---

### Financial Pillar

| Feature | Status | Implementation |
|---------|--------|----------------|
| **AVM (Automated Valuation)** | ✅ | CoreLogic Trestle API |
| **Comparable Sales** | ✅ | CoreLogic transaction history |
| **Rental Estimate** | ✅ | CoreLogic RentalAVM |
| **Gross Yield Calculation** | ✅ | (Annual Rent / Purchase Price) × 100 |
| **Net Yield Calculation** | ✅ | (Rent - Outgoings) / Price × 100 |
| **Council Rates Extraction** | ✅ | From Section 32 tables (Azure OCR) |
| **Water Rates Extraction** | ✅ | From Section 32 tables |
| **Strata Levies** | ✅ | From Strata Report |
| **Insurance Estimate** | ✅ | Flag if flood/bushfire = higher premium |
| **Land Tax Estimate** | ✅ | Calculate based on land value + state thresholds |
| **GST Implications** | ✅ | Flag if "new residential" or "commercial" |

---

### Sweat Equity / Value-Add Detection

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Floorplan "Lazy Space" Detection** | ✅ | GPT-4o Vision: laundries >5sqm, oversized hallways |
| **Bedroom Conversion Potential** | ✅ | Identify rooms that could become bedrooms |
| **Bathroom Addition Potential** | ✅ | Identify space for additional bathroom |
| **Renovation Cost Matrix** | ✅ | Apply cost estimates (bathroom=$25k, bedroom=$18k) |
| **Rent Increase Projection** | ✅ | Calculate $/week increase per added bedroom |
| **ROI Calculation** | ✅ | Months to recoup renovation cost |

---

## DOCUMENT TYPES (Dropdown)

```typescript
enum DocumentType {
  // === LEGAL - VICTORIA ===
  SECTION_32 = "Section 32 Vendor Statement (VIC)",
  TITLE_SEARCH = "Title Search / Certificate of Title",
  PLAN_OF_SUBDIVISION = "Plan of Subdivision",
  SECTION_137B = "Section 137B Owner-Builder Defect Report",
  
  // === LEGAL - NSW ===
  CONTRACT_OF_SALE = "Contract for Sale (NSW)",
  SECTION_10_7 = "Section 10.7 Planning Certificate (NSW)",
  SEWER_DIAGRAM = "Sewer Service Diagram",
  SECTION_66W = "Section 66W Cooling-Off Waiver",
  
  // === STRATA / BODY CORPORATE ===
  STRATA_REPORT = "Strata Report / OC Certificate",
  STRATA_MINUTES = "Strata AGM Minutes",
  STRATA_BYLAWS = "Strata By-Laws / Model Rules",
  STRATA_INSURANCE = "Strata Insurance Certificate",
  
  // === INSPECTION REPORTS ===
  BUILDING_REPORT = "Building Inspection Report",
  PEST_REPORT = "Pest & Termite Inspection Report",
  POOL_COMPLIANCE = "Pool Compliance Certificate",
  ASBESTOS_REPORT = "Asbestos Inspection Report",
  
  // === ROOMING HOUSE ===
  ROOMING_REGISTRATION = "Rooming House Registration",
  AESMR = "Annual Essential Safety Measures Report",
  
  // === FINANCIAL ===
  RENTAL_STATEMENT = "Rental Statement / Lease Agreement",
  RATES_NOTICE = "Council Rates Notice",
  WATER_RATES = "Water Rates Notice",
  
  // === VISUAL ===
  FLOORPLAN = "Floorplan",
  MARKETING_PHOTOS = "Marketing Photos (ZIP)",
  
  // === OTHER ===
  SURVEY_REPORT = "Survey / Subdivision Plan",
  GRANT_OF_PROBATE = "Grant of Probate",
  OTHER = "Other Document"
}
```

---

## LOCAL-FIRST ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                  (Next.js 14 + shadcn/ui)                       │
│                   http://localhost:3000                         │
│                                                                  │
│  • Property URL input                                           │
│  • Document upload + type dropdown                              │
│  • Interactive Mapbox with risk layers                          │
│  • Three-column analysis dashboard                              │
│  • PDF viewer with AI-highlighted sections                      │
│  • Executive report generator                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                    (Python FastAPI)                             │
│                   http://localhost:8000                         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LOCAL STORAGE                         │   │
│  │  • SQLite (pathway.db) - properties, documents, analysis │   │
│  │  • ./uploads/ - uploaded PDFs                            │   │
│  │  • ./cache/ - API response cache                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │  ENRICHMENT   │  │  GATEKEEPER   │  │   ANALYZER    │       │
│  │               │  │               │  │               │       │
│  │ • CoreLogic   │  │ • Geoscape    │  │ • Azure OCR   │       │
│  │ • Domain      │  │ • ABS Census  │  │ • Claude 3.5  │       │
│  │ • School Zones│  │ • VicPlan     │  │ • GPT-4o Vis  │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL APIs (Same as Production)          │
├─────────────────────────────────────────────────────────────────┤
│  PROPERTY DATA          │  AI SERVICES            │  MAPS       │
│  • CoreLogic Trestle    │  • Azure Doc Intel      │  • Mapbox   │
│  • Domain API           │  • Anthropic Claude     │             │
│  • Geoscape             │  • OpenAI GPT-4o        │             │
│  • VicPlan              │  • OpenAI Embeddings    │             │
│  • Airservices AU       │                         │             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack (Local-First)

| Layer | Local MVP | Production (Later) |
|-------|-----------|-------------------|
| **Frontend** | Next.js 14 @ localhost:3000 | Vercel |
| **Backend** | FastAPI @ localhost:8000 | AWS Lambda / Railway |
| **Database** | SQLite (pathway.db) | PostgreSQL + PostGIS |
| **File Storage** | ./uploads/ folder | Supabase Storage / S3 |
| **Vector DB** | Chroma (local) OR Pinecone | Pinecone |
| **Cache** | SQLite cache table | Redis |
| **Auth** | None (local demo) | Supabase Auth |

### Why This Works

- **SQLite** handles everything for demo (properties, documents, analysis results)
- **Chroma** is a local vector DB that's API-compatible with Pinecone
- **Same external APIs** = identical accuracy to production
- **Zero deployment** = run `npm run dev` + `uvicorn main:app`

---

## File Structure

```
pathway-properties/
├── frontend/                    # Next.js 14
│   ├── app/
│   │   ├── page.tsx            # Property URL input
│   │   ├── analysis/[id]/      # Analysis dashboard
│   │   └── api/                # API routes (proxy to backend)
│   ├── components/
│   │   ├── PropertyInput.tsx
│   │   ├── StreetLevelCard.tsx
│   │   ├── DocumentUpload.tsx
│   │   ├── AnalysisDashboard.tsx
│   │   ├── RiskMap.tsx
│   │   ├── PDFViewer.tsx
│   │   └── ExecutiveReport.tsx
│   └── lib/
│       └── api.ts              # Backend client
│
├── backend/                     # Python FastAPI
│   ├── main.py                 # FastAPI app
│   ├── database.py             # SQLite setup
│   ├── models.py               # Pydantic models
│   │
│   ├── services/
│   │   ├── property/
│   │   │   ├── scraper.py      # Domain/REA scraping
│   │   │   ├── corelogic.py    # CoreLogic Trestle client
│   │   │   └── enrichment.py   # Combine all property data
│   │   │
│   │   ├── gatekeeper/
│   │   │   ├── social_housing.py   # ABS Census lookup
│   │   │   ├── flight_paths.py     # Airservices ANEF
│   │   │   ├── flood_fire.py       # Geoscape risk
│   │   │   ├── zoning.py           # VicPlan/ePlanning
│   │   │   └── kill_criteria.py    # Business logic rules
│   │   │
│   │   ├── documents/
│   │   │   ├── ocr.py              # Azure Document Intelligence
│   │   │   ├── chunking.py         # Structure-aware chunking
│   │   │   ├── embeddings.py       # OpenAI embeddings
│   │   │   └── vector_store.py     # Chroma/Pinecone
│   │   │
│   │   ├── analysis/
│   │   │   ├── legal/
│   │   │   │   ├── section32.py        # VIC Section 32 extraction
│   │   │   │   ├── contract_nsw.py     # NSW Contract extraction
│   │   │   │   ├── title.py            # Title verification
│   │   │   │   ├── encumbrances.py     # Caveats, covenants, easements
│   │   │   │   └── strata.py           # Strata analysis
│   │   │   │
│   │   │   ├── physical/
│   │   │   │   ├── defects.py          # GPT-4o Vision defect detection
│   │   │   │   ├── illegal_works.py    # CV + permit cross-check
│   │   │   │   └── floorplan.py        # Sweat equity detection
│   │   │   │
│   │   │   ├── financial/
│   │   │   │   ├── yield.py            # Yield calculations
│   │   │   │   ├── outgoings.py        # Rates, levies extraction
│   │   │   │   └── tax.py              # Land tax, GST flags
│   │   │   │
│   │   │   └── specialized/
│   │   │       ├── rooming_house.py    # Rooming house checks
│   │   │       └── smsf.py             # SMSF compliance
│   │   │
│   │   └── reports/
│   │       └── executive.py        # PDF report generation
│   │
│   ├── prompts/                    # LLM prompt templates
│   │   ├── section32_extraction.py
│   │   ├── strata_analysis.py
│   │   ├── defect_detection.py
│   │   ├── sweat_equity.py
│   │   └── risk_summary.py
│   │
│   └── data/                       # Static reference data
│       ├── abs_sa1_social_housing.parquet
│       ├── anef_contours.geojson
│       └── renovation_costs.json
│
├── uploads/                        # Uploaded PDFs (gitignored)
├── cache/                          # API response cache (gitignored)
├── pathway.db                      # SQLite database (gitignored)
│
├── .env.local                      # API keys
├── requirements.txt                # Python deps
├── package.json                    # Node deps
└── README.md
```

---

## API Endpoints (Complete)

### Property Flow

```
POST /api/property/analyze
Body: { url: "https://domain.com.au/..." }
→ Scrapes listing, enriches with CoreLogic, runs Gatekeeper
→ Returns: property details + street level verdict

GET /api/property/{id}
→ Returns full property record

GET /api/property/{id}/street-level
→ Returns Gatekeeper analysis only
```

### Document Flow

```
POST /api/documents/upload
Body: FormData { file, documentType, propertyId }
→ OCRs document, chunks, embeds, stores
→ Returns: documentId, pageCount, status

GET /api/documents/{id}/status
→ Returns processing status

POST /api/documents/{id}/query
Body: { question: "Is there a caveat?" }
→ RAG query against single document
```

### Analysis Flow

```
POST /api/analysis/run
Body: { propertyId }
→ Runs full asset-level analysis on all documents
→ Returns: comprehensive analysis object

GET /api/analysis/{propertyId}
→ Returns cached analysis

POST /api/analysis/{propertyId}/report
→ Generates executive PDF report
→ Returns: PDF file
```

---

## Analysis Response Schema (Complete)

```typescript
interface FullAnalysis {
  propertyId: string;
  timestamp: string;
  
  // === STREET LEVEL ===
  streetLevel: {
    verdict: "PROCEED" | "REVIEW" | "REJECT";
    killReasons: string[];
    
    socialHousing: {
      score: "PASS" | "WARNING" | "FAIL";
      densityPercent: number;
      sa1Code: string;
      streetPercent?: number;
    };
    
    flightPath: {
      score: "PASS" | "FAIL";
      anef: number;
      n70: number;
    };
    
    floodRisk: {
      score: "PASS" | "WARNING" | "FAIL";
      aep1Percent: boolean;
      buildingAtRisk: boolean;
      source: string;
    };
    
    bushfireRisk: {
      score: "PASS" | "WARNING" | "FAIL";
      balRating: "BAL-LOW" | "BAL-12.5" | "BAL-19" | "BAL-29" | "BAL-40" | "BAL-FZ" | null;
    };
    
    zoning: {
      score: "PASS" | "WARNING";
      code: string;
      overlays: string[];
      heritageOverlay: boolean;
      ddoLimits?: { height?: number; setback?: number };
    };
  };
  
  // === LEGAL ANALYSIS ===
  legal: {
    // Title
    title: {
      proprietor: string;
      vendorMatch: boolean;
      mismatchReason?: string; // "Deceased estate", "Company", etc.
      titleType: "Torrens" | "Company" | "Strata" | "Community";
      volumeFolio: string;
    };
    
    // Encumbrances
    mortgages: Array<{ holder: string; dealingNumber: string }>;
    
    caveats: Array<{
      caveator: string;
      groundsOfClaim: string;
      riskLevel: "LOW" | "MEDIUM" | "HIGH";
      riskReason: string;
    }>;
    
    covenants: Array<{
      text: string;
      dateRegistered: string;
      developmentImpact: "NONE" | "MINOR" | "MAJOR" | "FATAL";
      impactReason: string;
    }>;
    
    easements: Array<{
      type: string; // "Drainage", "Right of Way", etc.
      beneficiary: string;
      location: string; // From Plan of Subdivision
      buildingConflict: boolean;
    }>;
    
    // Permits & Works
    buildingPermits: Array<{
      permitNumber: string;
      dateIssued: string;
      description: string;
      finalInspection: boolean;
    }>;
    
    illegalWorksRisk: {
      detected: boolean;
      structures: string[]; // ["deck", "pool"]
      missingPermits: string[];
      confidence: number;
    };
    
    ownerBuilder: {
      isOwnerBuilder: boolean;
      section137BProvided: boolean;
      defectsListed: string[];
    };
    
    // Special Conditions
    specialConditions: Array<{
      number: number;
      text: string;
      riskLevel: "LOW" | "MEDIUM" | "HIGH";
      riskReason: string;
    }>;
    
    coolingOffWaived: boolean;
    
    // Planning
    planning: {
      statedZone: string;
      verifiedZone: string;
      zoneMismatch: boolean;
      complyingDevelopmentPossible: boolean;
    };
  };
  
  // === STRATA ANALYSIS ===
  strata?: {
    schemeName: string;
    lotNumber: number;
    totalLots: number;
    
    financial: {
      adminFundQuarterly: number;
      capitalWorksFundBalance: number;
      insuredValue: number;
      sinkingFundRatio: number; // balance / insuredValue
      specialLevyRisk: "LOW" | "MEDIUM" | "HIGH";
    };
    
    issues: {
      keywords: string[]; // Found in minutes: "cladding", "water ingress"
      chronicMaintenance: string[]; // "lift", "pump"
      legalActions: boolean;
      defectsDisclosed: string[];
    };
    
    rules: {
      petsAllowed: boolean;
      shortTermLettingAllowed: boolean;
      renovationRestrictions: string[];
    };
  };
  
  // === PHYSICAL ANALYSIS ===
  physical: {
    defectsDetected: Array<{
      type: "Crack" | "WaterStain" | "Mould" | "SaltDamp" | "PeelingPaint" | "TermiteDamage";
      location: string; // "Bedroom 2 ceiling"
      severity: "Minor" | "Moderate" | "Major";
      imageUrl: string;
      riskImplication: string;
    }>;
    
    termiteRisk: {
      barrierPresent: boolean;
      damageDetected: boolean;
      riskLevel: "LOW" | "MEDIUM" | "HIGH";
    };
    
    structuralConcerns: string[];
  };
  
  // === FINANCIAL ANALYSIS ===
  financial: {
    purchase: {
      listingPrice: string;
      avmValue: number;
      avmConfidence: "Low" | "Medium" | "High";
      lastSoldPrice?: number;
      lastSoldDate?: string;
      priceDelta?: number; // % change from last sale
    };
    
    income: {
      currentRent?: number;
      estimatedRent: { low: number; mid: number; high: number };
      rentalYieldGross: number;
    };
    
    outgoings: {
      councilRatesAnnual: number;
      waterRatesAnnual: number;
      strataLeviesAnnual?: number;
      insuranceEstimate: number;
      landTaxEstimate: number;
      totalAnnual: number;
    };
    
    yield: {
      gross: number;
      net: number;
      cashflowMonthly: number; // After 80% LVR mortgage
    };
    
    gstApplicable: boolean;
    gstReason?: string;
  };
  
  // === SWEAT EQUITY ===
  sweatEquity: {
    opportunities: Array<{
      type: "BedroomConversion" | "BathroomAddition" | "DeckExtension" | "GrannyFlat" | "Subdivision";
      description: string;
      estimatedCost: number;
      valueAdd: number;
      rentIncreaseWeekly: number;
      roiMonths: number;
      feasibility: "Easy" | "Moderate" | "Complex";
    }>;
    
    totalValueAddPotential: number;
    totalCost: number;
    overallROI: number;
  };
  
  // === SPECIALIZED ===
  specialized?: {
    roomingHouse?: {
      isRegistered: boolean;
      registrationNumber?: string;
      class1bRequired: boolean;
      class1bCompliant: boolean;
      aesmrProvided: boolean;
      aesmrCurrent: boolean;
      complianceRisk: "LOW" | "MEDIUM" | "HIGH";
    };
    
    smsf?: {
      armsLengthConcern: boolean;
      concernReason?: string;
      borrowingRestriction: boolean;
      restrictionReason?: string;
    };
  };
  
  // === SUMMARY ===
  summary: {
    overallRisk: "LOW" | "MEDIUM" | "HIGH";
    recommendation: "STRONG_BUY" | "BUY" | "PROCEED_WITH_CAUTION" | "AVOID";
    
    topRisks: Array<{
      category: string;
      issue: string;
      severity: "LOW" | "MEDIUM" | "HIGH";
      mitigation?: string;
    }>;
    
    topOpportunities: Array<{
      type: string;
      description: string;
      value: number;
    }>;
    
    executiveSummary: string; // AI-generated paragraph
  };
}
```

---

## LLM Prompts (Key Examples)

### Section 32 Legal Extraction

```python
SECTION_32_PROMPT = """
You are a senior Australian Conveyancer with 20 years of experience in Victorian Property Law.

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

DOCUMENT:
{document_text}
"""
```

### Sweat Equity Detection

```python
SWEAT_EQUITY_PROMPT = """
You are a property renovation expert analyzing a floorplan for value-add opportunities.

Analyze this floorplan image and identify:

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
```

---

## Environment Variables

```bash
# .env.local

# === PROPERTY DATA APIs ===
CORELOGIC_CLIENT_ID=
CORELOGIC_CLIENT_SECRET=
CORELOGIC_BASE_URL=https://api.trestle.corelogic.com.au

DOMAIN_API_KEY=
DOMAIN_CLIENT_ID=
DOMAIN_CLIENT_SECRET=

GEOSCAPE_API_KEY=
GEOSCAPE_BASE_URL=https://api.geoscape.com.au

# === AI SERVICES ===
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=

ANTHROPIC_API_KEY=

OPENAI_API_KEY=

# === VECTOR DB (choose one) ===
# Local development:
VECTOR_DB=chroma
CHROMA_PERSIST_DIR=./chroma_data

# Production:
# VECTOR_DB=pinecone
# PINECONE_API_KEY=
# PINECONE_INDEX_NAME=pathway-properties

# === MAPS ===
NEXT_PUBLIC_MAPBOX_TOKEN=

# === LOCAL CONFIG ===
DATABASE_URL=sqlite:///./pathway.db
UPLOAD_DIR=./uploads
CACHE_DIR=./cache
```

---

## Running Locally

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download static data
python scripts/download_abs_data.py
python scripts/download_anef_data.py

# Run server
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 3. Test Flow

1. Open http://localhost:3000
2. Paste a Domain.com.au property URL
3. Watch Street Level analysis run
4. Upload Section 32 PDF, select type
5. Click "Run Analysis"
6. Review dashboard
7. Generate executive report

---

## API Costs (Same as Production)

| Service | Monthly Est. | Notes |
|---------|-------------|-------|
| CoreLogic Trestle | $1,700 | ~$20k/yr |
| Domain API | $600 | ~$7k/yr |
| Geoscape | $1,000 | ~$12k/yr |
| Azure Doc Intelligence | $100 | ~100 docs/mo |
| Anthropic Claude | $300 | ~50 analyses/mo |
| OpenAI (Vision + Embed) | $200 | |
| Mapbox | $50 | Free tier covers dev |
| **TOTAL** | **~$4,000/mo** | |

---

## Migration to Production

When ready to deploy:

1. **Database**: `sqlite:///./pathway.db` → `postgresql://...`
2. **Files**: `./uploads/` → Supabase Storage / S3
3. **Vector DB**: `chroma` → `pinecone`
4. **Backend**: `uvicorn` → Railway / AWS Lambda
5. **Frontend**: `npm run dev` → Vercel
6. **Auth**: Add Supabase Auth

The code stays the same - just swap environment variables.
