# Pathway Property - Business Logic & Technical Overview

## Executive Summary

**Pathway Property** is an AI-powered property due diligence platform designed specifically for the Australian real estate market. It automates the traditionally time-consuming process of evaluating investment properties, reducing analysis time from hours to minutes.

### The Core Problem Being Solved

When an Australian property buyer (especially investor or buyer's agency) considers purchasing a property, they must:
1. Review hundreds of pages of legal documents (Section 32 statements, contracts)
2. Check for location-based risks (flood, fire, flight paths, public housing)
3. Verify zoning and planning compliance
4. Assess physical condition from inspection reports
5. Calculate financial viability (yield, cashflow)
6. Identify value-add opportunities (renovations, conversions)

This process typically takes 4-8 hours per property. **Pathway Property automates this to ~10 minutes**.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
│                       http://localhost:3000                         │
│                                                                     │
│  Stage 1: Property Input → Stage 2: Street Level → Stage 3: Docs → │
│  Stage 4: Full Analysis Dashboard                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                           │
│                       http://localhost:8000                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  PROPERTY   │  │ GATEKEEPER  │  │  DOCUMENTS  │  │ ANALYSIS  │  │
│  │  SERVICES   │  │  (Kill      │  │  (OCR +     │  │ (Legal,   │  │
│  │  (Scraper,  │  │  Criteria)  │  │   RAG)      │  │ Physical, │  │
│  │  CoreLogic) │  │             │  │             │  │ Financial)│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    LOCAL STORAGE                             │   │
│  │  • SQLite (pathway.db) - properties, documents, analyses    │   │
│  │  • ./uploads/ - uploaded PDFs and documents                 │   │
│  │  • ./cache/ - API response cache                            │   │
│  │  • Chroma - local vector database for document embeddings   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL APIs                                  │
├─────────────────────────────────────────────────────────────────────┤
│  PROPERTY DATA         AI SERVICES              SPATIAL DATA        │
│  • CoreLogic Trestle   • OpenAI GPT-4o          • Geoscape          │
│  • Domain.com.au       • Azure Document Intel   • VicPlan           │
│  • RealEstate.com.au   • Isaacus Legal AI       • Airservices AU    │
│                                                  • ABS Census        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Two-Phase Analysis Model

### Phase 1: Street Level Analysis (The "Gatekeeper")

**Purpose:** Fast, low-cost filtering to eliminate bad properties before spending resources on document analysis.

**Philosophy:** "Fail Fast" - Don't waste GPU cycles or API credits analyzing contracts for a property under a flight path.

#### Kill Criteria (Auto-Reject)

| Rule | Threshold | Action |
|------|-----------|--------|
| **Social Housing Cluster** | >20% of street owned by state authority | AUTO KILL |
| **Flight Path Noise** | ANEF >20 or N70 >20 flights/day | AUTO KILL |
| **Flood Risk** | Building footprint intersects 1% AEP flood extent | AUTO KILL |

#### Warning Criteria (Proceed with Caution)

| Rule | Threshold | Action |
|------|-----------|--------|
| **Social Housing Density** | >15% in SA1 statistical area | MANUAL REVIEW |
| **Bushfire Risk** | BAL-40 or Flame Zone rating | RED FLAG - cost buffer required |
| **Heritage Overlay** | Property in heritage zone | WARNING - restrictions apply |
| **Low Yield** | Gross yield <4% | WARNING - unless capital growth play |

#### Data Sources for Street Level

```python
# services/gatekeeper/ folder structure
├── social_housing.py   # ABS Census API → SA1 lookup → % state authority landlords
├── flight_paths.py     # Airservices Australia WFS → point-in-polygon against ANEF contours
├── flood_fire.py       # Geoscape API → building-level flood/bushfire risk
├── zoning.py           # VicPlan/NSW ePlanning API → zone code + overlay check
└── kill_criteria.py    # Business rules engine - combines all checks
```

### Phase 2: Asset Level Analysis (The "Deep Dive")

**Purpose:** Comprehensive analysis of property documents, physical condition, and financials.

**Only runs if:** Property passes (or is overridden through) the Gatekeeper.

---

## Legal Document Analysis

### Supported Document Types (State-Specific)

#### Victoria
- **Section 32 Vendor Statement** - The core disclosure document
- **Title Search / Certificate of Title** - Ownership verification
- **Plan of Subdivision** - Easement and boundary details
- **Section 137B Owner-Builder Defect Report** - If vendor was owner-builder

#### New South Wales
- **Contract for Sale** - The NSW equivalent legal package
- **Section 10.7 Planning Certificate** - Zoning and hazard disclosures
- **Sewer Service Diagram** - Sydney Water infrastructure
- **Section 66W Certificate** - Cooling-off period waiver

#### Universal
- **Strata Report / OC Certificate** - For apartments/townhouses
- **Building Inspection Report** - Physical condition
- **Pest & Termite Inspection Report** - Pest damage/risk

### Document Processing Pipeline

```
Upload PDF/DOCX
      │
      ▼
┌─────────────────┐
│  Azure OCR or   │  Extracts text + tables with structure preservation
│  pypdf fallback │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Structure-Aware│  Chunks by legal clause/section, not arbitrary character count
│  Chunking       │  Tags with metadata: {source, page, section}
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Embedding +    │  OpenAI text-embedding-3-large → Chroma vector store
│  Vector Store   │  Isolated namespace per property
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RAG Query      │  Retrieves relevant chunks + LLM reasoning
│  (GPT-4o)       │  Requires page citations for every claim
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Isaacus IQL    │  Semantic legal clause classification
│  Classification │  (Cooling-off waiver, As-is clause, etc.)
└─────────────────┘
```

### Key Legal Extractions

| Extraction | Why It Matters |
|------------|----------------|
| **Registered Proprietor** | Must match vendor - mismatch indicates deceased estate or company ownership |
| **Caveats** | Individual caveator = HIGH RISK (dispute), Commercial lender = LOW RISK |
| **Restrictive Covenants** | "One dwelling only" can destroy townhouse feasibility |
| **Easements** | Check if building crosses easement boundary |
| **Building Permits (7 years)** | Missing Certificate of Final Inspection = potential illegal works |
| **Owner-Builder Works** | Section 137B Defect Report is mandatory - absence makes contract voidable |
| **Special Conditions** | Cooling-off waiver (s66W) means due diligence must be complete before signing |

### Isaacus Legal AI Integration

**What is Isaacus?** A purpose-built legal AI that uses IQL (Isaacus Query Language) for semantic classification of legal clauses.

**Why use it?** Standard keyword matching fails on legal documents. "Waives cooling off" vs "Cooling off period of 5 days" require semantic understanding.

```python
# Example IQL queries in iql_templates.py
IQL_QUERIES = {
    "cooling_off_waiver": "{IS clause that 'waives cooling off period'}",
    "as_is_condition": "{IS clause that 'property sold as is'}",
    "early_deposit_release": "{IS clause that 'allows early release of deposit'}",
    "missing_inspection": "{IS clause indicating 'no certificate of final inspection'}",
}
```

The system runs these queries against document chunks and returns confidence scores (>0.5 = match detected).

---

## Physical Analysis

### Defect Detection

| Defect Type | How Detected | Risk Implication |
|-------------|--------------|------------------|
| **Cracks** | GPT-4o Vision on photos | >2mm or step cracking = foundation movement |
| **Water Stains** | GPT-4o Vision on ceiling photos | Roof leak risk |
| **Mould** | GPT-4o Vision | Health hazard + underlying moisture issue |
| **Salt Damp** | GPT-4o Vision (efflorescence) | Rising damp - expensive to fix |
| **Termite Damage** | Cross-reference pest report + missing termite barrier in S32 | HIGH RISK if both present |

### Illegal Works Detection

```
CV detects modern structure (deck, pool, pergola)
                    +
Section 32 shows NO building permit for that structure
                    =
        HIGH RISK: Potential Illegal Works
```

This cross-reference is a key differentiator - human analysts often miss this connection.

---

## Financial Analysis

### Yield Calculations

```python
# Gross Yield
gross_yield = (annual_rent / purchase_price) * 100

# Net Yield  
annual_outgoings = council_rates + water_rates + strata_levies + insurance + land_tax
net_yield = ((annual_rent - annual_outgoings) / purchase_price) * 100

# Monthly Cashflow (80% LVR @ 6.5% interest)
loan_amount = purchase_price * 0.8
monthly_interest = loan_amount * 0.065 / 12
monthly_rent = weekly_rent * 52 / 12
monthly_outgoings = annual_outgoings / 12
cashflow = monthly_rent - monthly_interest - monthly_outgoings
```

### Data Sources

| Data Point | Source |
|------------|--------|
| AVM (Automated Valuation Model) | CoreLogic Trestle API |
| Rental Estimate | CoreLogic RentalAVM |
| Council Rates | Extracted from Section 32 tables (Azure OCR) |
| Water Rates | Extracted from Section 32 tables |
| Strata Levies | Extracted from Strata Report |

---

## Sweat Equity Analysis (Value-Add Detection)

### What is "Sweat Equity"?

Identifying renovation opportunities that can increase property value or rental income disproportionately to cost.

### Opportunities Detected

| Opportunity | Detection Method | Typical Cost | Value Add |
|-------------|------------------|--------------|-----------|
| **Bedroom Conversion** | GPT-4o Vision on floorplan - laundry >5sqm, enclosed sunroom | $15-25k | +$40-80/wk rent |
| **Bathroom Addition** | Space analysis - minimum 2.5m x 2m available | $20-35k | +$40/wk rent |
| **Granny Flat** | Land size check + zoning (Complying Development possible?) | $100-150k | +$300-400/wk rent |
| **Subdivision** | Land size + zoning + covenant check | Variable | Significant |

### ROI Calculation

```python
roi_months = estimated_cost / (rent_increase_weekly * 4.33)  # 4.33 weeks/month
```

---

## Strata/Body Corporate Analysis

For apartments and townhouses, the Owners Corporation health is critical.

### Financial Health Checks

| Check | Threshold | Risk |
|-------|-----------|------|
| **Sinking Fund Ratio** | Balance / Insured Value | Low ratio = special levy coming |
| **Admin Fund Arrears** | High arrears in scheme | Other owners not paying |

### Meeting Minutes Analysis

The system scans AGM minutes for keywords:
- **Cladding** - Combustible cladding liability
- **Water ingress** - Chronic waterproofing issues
- **Legal action / VCAT / NCAT** - Disputes in progress
- **Pump failures / Lift breakdowns** - Chronic maintenance issues
- **Defects** - Building defects being addressed

---

## Report Generation

### Executive Report Contents

1. **Overall Risk Rating** (LOW / MEDIUM / HIGH)
2. **Recommendation** (STRONG_BUY / BUY / PROCEED_WITH_CAUTION / AVOID)
3. **Top Risks** with mitigation strategies
4. **Top Opportunities** with estimated values
5. **Executive Summary** (2-3 sentence investment committee brief)

### PDF Generation

Uses WeasyPrint to generate professional PDF reports suitable for client presentation or investment committee review.

---

## API Endpoints Summary

### Property Flow
```
POST /api/property/analyze     - Analyze property from Domain/REA URL
POST /api/property/manual      - Manually add property details
GET  /api/property/{id}        - Get property details
GET  /api/property/{id}/street-level - Get gatekeeper analysis only
GET  /api/properties           - List all analyzed properties
```

### Document Flow
```
POST /api/documents/upload     - Upload document for OCR processing
GET  /api/documents/{id}       - Get document status
GET  /api/documents/property/{id} - List all documents for property
POST /api/documents/{id}/query - RAG query against document
```

### Analysis Flow
```
POST /api/analysis/run         - Run full analysis on all documents
GET  /api/analysis/{id}        - Get cached analysis
POST /api/analysis/{id}/report - Generate PDF report
```

---

## Database Schema

### Properties Table
```sql
id              UUID PRIMARY KEY
url             VARCHAR(500)     -- Original listing URL
address         VARCHAR(500)
state           VARCHAR(10)      -- VIC, NSW, etc.
listing_data    JSON             -- Raw scraper output
corelogic_data  JSON             -- CoreLogic enrichment
street_level_analysis JSON       -- Gatekeeper results
verdict         VARCHAR(20)      -- PROCEED, REVIEW, REJECT
kill_reasons    JSON             -- Array of kill reason strings
```

### Documents Table
```sql
id              UUID PRIMARY KEY
property_id     UUID FOREIGN KEY
document_type   VARCHAR(50)      -- Section 32, Pest Report, etc.
file_path       VARCHAR(500)     -- Path to uploaded file
status          VARCHAR(20)      -- pending, processing, ready, error
page_count      INTEGER
ocr_result      JSON             -- Structured OCR output
```

### Analyses Table
```sql
id              UUID PRIMARY KEY
property_id     UUID FOREIGN KEY (UNIQUE)
legal_analysis  JSON
physical_analysis JSON
financial_analysis JSON
sweat_equity    JSON
specialized     JSON             -- Rooming house, SMSF checks
summary         JSON             -- Risk rating, recommendation
overall_risk    VARCHAR(20)
recommendation  VARCHAR(30)
```

---

## Cost Structure (Production Estimates)

| Service | Monthly Est. | Notes |
|---------|--------------|-------|
| CoreLogic Trestle | $1,700 | ~$20k/yr enterprise |
| Domain API | $600 | ~$7k/yr |
| Geoscape | $1,000 | ~$12k/yr |
| Azure Document Intelligence | $100 | ~100 docs/mo @ $0.01/page |
| OpenAI (GPT-4o + Embeddings) | $500 | ~50 analyses/mo |
| Isaacus Legal AI | TBD | Per-query pricing |
| **TOTAL** | **~$4,000/mo** | |

### ROI Calculation
- Time saved: 4 hours/property × $100/hr × 500 properties/yr = **$200,000/yr**
- System cost: ~$48,000/yr
- **Net benefit: $152,000/yr + strategic speed advantage**

---

## Configuration

### Required Environment Variables

```bash
# === CORE AI ===
OPENAI_API_KEY=               # Required for LLM reasoning + embeddings

# === OPTIONAL - Enhanced Features ===
CORELOGIC_CLIENT_ID=          # Property valuations + comparable sales
CORELOGIC_CLIENT_SECRET=
GEOSCAPE_CONSUMER_KEY=        # Flood/bushfire risk at building level
GEOSCAPE_CONSUMER_SECRET=
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=  # Premium OCR with table extraction
AZURE_DOCUMENT_INTELLIGENCE_KEY=
ISAACUS_API_KEY=              # Semantic legal clause classification
MAPBOX_TOKEN=                 # Map visualization

# === LOCAL STORAGE ===
DATABASE_URL=sqlite:///./pathway.db
UPLOAD_DIR=./uploads
CACHE_DIR=./cache
VECTOR_DB=chroma
```

---

## User Workflow

```
1. USER enters Domain.com.au or RealEstate.com.au URL
                    │
                    ▼
2. SYSTEM scrapes listing, enriches with CoreLogic
                    │
                    ▼
3. GATEKEEPER runs street-level checks (10 seconds)
   ├── REJECT → Shows kill reasons, offers override
   ├── REVIEW → Shows warnings, user decides
   └── PROCEED → Green light
                    │
                    ▼
4. USER uploads documents (Section 32, pest report, etc.)
                    │
                    ▼
5. SYSTEM processes documents:
   ├── OCR extracts text + tables
   ├── Chunking preserves legal structure
   ├── Embedding stores in vector DB
   └── Isaacus classifies high-risk clauses
                    │
                    ▼
6. USER clicks "Run Full Analysis"
                    │
                    ▼
7. SYSTEM runs:
   ├── Legal extraction (caveats, covenants, special conditions)
   ├── Physical analysis (defects, illegal works)
   ├── Financial analysis (yield, cashflow)
   ├── Sweat equity detection (renovation opportunities)
   └── Summary generation (risk rating, recommendation)
                    │
                    ▼
8. DASHBOARD displays results with tabs:
   ├── Summary (executive overview)
   ├── Legal (title, encumbrances, conditions)
   ├── Physical (defects, termite risk)
   ├── Financial (yields, cashflow)
   └── Sweat Equity (renovation ROI)
                    │
                    ▼
9. USER downloads PDF executive report
```

---

## Key Differentiators

### vs. Generic "Chat with PDF" Tools

1. **Structure-aware chunking** - Doesn't break legal clauses mid-sentence
2. **Legal-specific prompts** - "You are a senior Australian Conveyancer..."
3. **Cross-document reasoning** - Connects building photos with missing permits
4. **State-specific logic** - VIC Section 32 vs NSW Contract for Sale

### vs. Manual Due Diligence

1. **Speed** - Minutes not hours
2. **Consistency** - Every property checked against same criteria
3. **Scalability** - Analyze 5x more properties in same time
4. **Kill criteria enforcement** - System literally won't let you miss flood zones

### vs. Other PropTech Tools

1. **Australian-specific** - Built for VIC/NSW legal documents
2. **Investment-focused** - Yield, cashflow, sweat equity (not just "nice property")
3. **Gatekeeper model** - Fail fast before expensive analysis
4. **Legal AI integration** - Isaacus for semantic clause classification

---

## Technical Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TanStack Query, Tailwind CSS, shadcn/ui |
| **Backend** | Python FastAPI, SQLAlchemy, Pydantic |
| **Database** | SQLite (dev) → PostgreSQL (prod) |
| **Vector Store** | Chroma (dev) → Pinecone (prod) |
| **OCR** | Azure Document Intelligence (premium) / pypdf (fallback) |
| **LLM** | OpenAI GPT-4o |
| **Legal AI** | Isaacus Universal Classifier with IQL |
| **Property Data** | CoreLogic Trestle, Geoscape |
| **Mapping** | Mapbox GL JS |

---

## Disclaimer

> This tool provides preliminary analysis only. It does not constitute legal, financial, or professional advice. Always seek independent professional advice before purchasing property.

The system enforces a **Human-in-the-Loop (HIL)** protocol - AI never issues final recommendations to clients without human expert review.

---

*Last Updated: January 2026*

