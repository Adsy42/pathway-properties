# Pathway Property - Revised Implementation Plan

## Executive Summary

After detailed code review, the existing system is **more complete than initially assessed** (~55-60% of compass blueprint). Key corrections to the original plan:

1. **VicPlan WFS integration already works** - flood/bushfire/zoning queries functional
2. **Due diligence modules are comprehensive** - 15+ analyzers already implemented
3. **Isaacus Legal AI integration exists** - semantic clause classification working
4. **PostGIS migration is optional** - SQLite works for MVP, optimize later

This revised plan focuses on **high-value gaps** while avoiding unnecessary rebuilds.

---

## Critical Corrections to Original Plan

### What Was Overcounted as "Missing"

| Original Claim | Reality |
|----------------|---------|
| "VicPlan zones/overlays not implemented" | ✅ Working via WFS at `opendata.maps.vic.gov.au` |
| "Flood/bushfire from Geoscape only" | ✅ VicPlan WFS fallback already implemented |
| "No contamination assessment" | ✅ `ContaminationAssessor` exists in due_diligence |
| "No compliance tracking" | ✅ `DueDiligenceComplianceTracker` exists |
| "No risk scoring framework" | ✅ `PropertyRiskScorer` with 25 factors exists |
| "No cashflow modeling" | ✅ `InvestorCashFlowModel` exists |

### What Is Actually Missing (Priority Gaps)

| Gap | Impact | Effort |
|-----|--------|--------|
| **LANDATA DDP** - official title searches | High (authoritative data) | High (requires broker account) |
| **EPA Victoria** - contamination spatial data | High (risk mitigation) | Medium |
| **Heritage Victoria API** - VHR lookup | Medium (compliance) | Low |
| **Mining/GeoVic tenements** | Medium (regional properties) | Medium |
| **School catchments spatial data** | Medium (location scoring) | Low |
| **Crime statistics** | Medium (location scoring) | Low |
| **PTV transport accessibility** | Medium (location scoring) | Medium |
| **Domain API** (replace scraping) | Medium (reliability) | Low |
| **Rooming house module** | High (Pathway business) | Medium |
| **Commercial property module** | High (Pathway business) | High |
| **Development feasibility** | High (Pathway business) | High |
| **Client portal** | Medium (user experience) | High |

---

## Revised Phase Structure

### Phase 0: Quick Wins (Week 1)
**Low effort, immediate value - no infrastructure changes**

#### 0.1 Domain API Integration
Replace brittle scraping with official API (free tier: 500 calls/day).

**Files to Create:**
```
backend/services/property/domain_api.py
```

**Tasks:**
- [ ] Register at developer.domain.com.au
- [ ] Implement OAuth 2.0 client
- [ ] Implement listings search endpoint
- [ ] Implement property details endpoint
- [ ] Update `enrichment.py` to prefer Domain API
- [ ] Keep scraper as fallback

**Why First:** Zero infrastructure, free tier, immediate reliability improvement.

#### 0.2 Heritage Victoria API
Simple REST API, no auth required.

**Files to Create:**
```
backend/services/heritage/
├── __init__.py
├── client.py
└── models.py
```

**Tasks:**
- [ ] Implement client for `api.heritagecouncil.vic.gov.au/v1/`
- [ ] Parse HAL-formatted JSON responses
- [ ] Integrate with gatekeeper zoning check
- [ ] Add heritage status to property analysis

**Why Now:** Free API, no auth, easy integration.

#### 0.3 Crime Statistics Integration
Static data download, simple lookup.

**Files to Create:**
```
backend/services/crime/
├── __init__.py
├── csa_vic.py
└── models.py
```

**Tasks:**
- [ ] Download quarterly data from crimestatistics.vic.gov.au
- [ ] Parse Excel into SQLite lookup table
- [ ] Implement suburb/postcode lookup
- [ ] Add to location analysis section

**Why Now:** Free data, no API required, enhances reports.

#### 0.4 NBN Availability Check
Simple library integration.

**Files to Create:**
```
backend/services/utilities/
├── __init__.py
└── nbn.py
```

**Tasks:**
- [ ] Add `nbnpy` to requirements.txt
- [ ] Implement address lookup wrapper
- [ ] Add to property enrichment

**Why Now:** One library, immediate value.

---

### Phase 1: Enhanced Spatial Data (Weeks 2-4)
**Improve existing VicPlan integration + add EPA/Mining**

#### 1.1 EPA Victoria Contamination Data
Supplement existing `ContaminationAssessor` with spatial data.

**Files to Create:**
```
backend/services/epa/
├── __init__.py
├── priority_sites.py
└── unearthed.py
```

**Data Ingestion:**
- Download Priority Sites Register GeoJSON from data.vic.gov.au
- Store in SQLite with spatial index (using Shapely)
- Query by proximity (500m radius)

**Tasks:**
- [ ] Download and parse Priority Sites Register
- [ ] Implement proximity search using Shapely
- [ ] Query Victoria Unearthed for additional data
- [ ] Update `ContaminationAssessor` to use real data

**Note:** No PostGIS required - use geopandas/shapely for spatial queries.

#### 1.2 Mining Tenements (GeoVic)
Add mining tenement check to risk assessment.

**Files to Create:**
```
backend/services/mining/
├── __init__.py
├── geovic.py
└── models.py
```

**Tasks:**
- [ ] Implement GeoVic REST API client
- [ ] Query exploration licenses by coordinates
- [ ] Add to gatekeeper checks
- [ ] Update risk scoring

#### 1.3 School Catchments
Download and query school zone boundaries.

**Files to Create:**
```
backend/services/schools/
├── __init__.py
├── catchments.py
└── models.py
```

**Tasks:**
- [ ] Download Victorian school zones from data.vic.gov.au
- [ ] Store boundaries in SQLite
- [ ] Implement catchment lookup
- [ ] Calculate distances to nearest schools
- [ ] Add to location analysis

#### 1.4 Enhanced Melbourne Water Flood Data
Supplement existing VicPlan flood checks.

**Tasks:**
- [ ] Query Melbourne Water Open Data Hub
- [ ] Get detailed flood extent (1%, 0.5%, PMF)
- [ ] Enhance existing `check_flood_vicplan()` function

---

### Phase 2: LANDATA Integration (Weeks 5-7)
**Critical dependency: Requires broker account approval**

#### 2.1 LANDATA DDP API Setup

**Blocking Prerequisite:** Apply for broker account NOW (can take 2-4 weeks)
- Email: `data.services@servictoria.com.au`
- Request: API access to Digital Distribution Platform

**Files to Create:**
```
backend/services/landata/
├── __init__.py
├── client.py
├── title_search.py
├── parcel_discovery.py
├── serv_alert.py
└── models.py
```

**Tasks:**
- [ ] **IMMEDIATE:** Apply for LANDATA broker account
- [ ] Implement OAuth client (once approved)
- [ ] Implement Property Discovery (address → SPI)
- [ ] Implement Title Discovery (SPI → Volume/Folio)
- [ ] Implement Register Search Statement retrieval
- [ ] Create mock data for development
- [ ] Integrate with title_analysis.py

**Fallback:** Continue using CoreLogic + document extraction until approved.

---

### Phase 3: Property-Type Modules (Weeks 8-12)
**High-value Pathway Property-specific features**

#### 3.1 Rooming House Module

**Files to Create:**
```
backend/services/property_types/rooming_house/
├── __init__.py
├── compliance.py      # Building Regs Part 13
├── yield_model.py     # Per-room calculations
├── fire_safety.py     # Fire safety requirements
└── models.py
```

**Compliance Checks:**
- Planning permit for rooming house use
- Building classification (Class 1b/3)
- Fire safety (Part 13 Building Regulations)
- Minimum room sizes (15sqm living, 7.5sqm bedroom)
- Amenity ratios
- Registration status

**Tasks:**
- [ ] Create compliance checklist from VBA regulations
- [ ] Implement fire safety checker
- [ ] Create per-room yield calculator
- [ ] Add council attitude database (some councils hostile)
- [ ] Generate rooming house-specific report section

#### 3.2 Commercial Property Module

**Files to Create:**
```
backend/services/property_types/commercial/
├── __init__.py
├── lease_analysis.py
├── tenant_credit.py
├── yield_metrics.py
└── models.py
```

**Features:**
- Lease document parser (extract key terms)
- Cap rate calculation
- WALE (Weighted Average Lease Expiry)
- Net yield calculation
- Zoning compliance check

**Tasks:**
- [ ] Create commercial lease document type in OCR
- [ ] Build lease term extractor
- [ ] Implement cap rate calculator
- [ ] Implement WALE calculator
- [ ] Create commercial property report section

#### 3.3 Development Feasibility Module

**Files to Create:**
```
backend/services/property_types/development/
├── __init__.py
├── site_analysis.py
├── planning.py
├── feasibility.py
└── models.py
```

**Features:**
- Site analysis (area, frontage, slope)
- Zone density controls parser
- Maximum dwelling yield calculator
- Construction cost estimator
- Development margin calculator (target: 20%)

**Tasks:**
- [ ] Parse planning scheme density controls
- [ ] Implement dwelling yield calculator
- [ ] Build construction cost database (per sqm rates)
- [ ] Create feasibility model
- [ ] Generate development feasibility report

---

### Phase 4: Investment Analytics (Weeks 13-15)
**Build on existing financial modules**

#### 4.1 Enhanced Investment Scoring

The current `PropertyRiskScorer` has 25 factors. Add investment-specific scoring.

**Files to Modify:**
```
backend/services/due_diligence/investment_scoring.py  # NEW
backend/services/due_diligence/risk_scoring.py       # MODIFY
```

**Investment Score Components:**
| Factor | Weight |
|--------|--------|
| Yield potential | 25% |
| Capital growth indicators | 25% |
| Holding cost efficiency | 15% |
| Development upside | 10% |
| Risk factors | 25% |

**Tasks:**
- [ ] Create investment scoring module
- [ ] Add suburb yield benchmarks
- [ ] Add capital growth indicators (infrastructure pipeline, demographics)
- [ ] Create composite investment score
- [ ] Add to reports

#### 4.2 Portfolio Alignment Scoring

**Files to Create:**
```
backend/services/portfolio/
├── __init__.py
├── client_brief.py
├── alignment.py
└── models.py
```

**Features:**
- Client brief storage (target yield, budget, locations, risk tolerance)
- Property-brief matching algorithm
- Alignment score calculation

**Tasks:**
- [ ] Create client brief data model
- [ ] Implement storage/retrieval API
- [ ] Create alignment scoring algorithm
- [ ] Rank properties against criteria

#### 4.3 Consumer Victoria Checklist Mapping

The existing `DueDiligenceComplianceTracker` is close but needs explicit Section 33B mapping.

**Tasks:**
- [ ] Map all 15 Section 33B items explicitly
- [ ] Add status tracking (verified/pending/manual)
- [ ] Generate client-facing checklist report
- [ ] Mark items requiring professional inspection

---

### Phase 5: Transport & Demographics (Week 16)
**Optional enrichment data**

#### 5.1 PTV Transport Accessibility

**Files to Create:**
```
backend/services/transport/
├── __init__.py
├── ptv_api.py
└── models.py
```

**Tasks:**
- [ ] Register for PTV API (developer.vic.gov.au)
- [ ] Implement GTFS stop locations query
- [ ] Calculate distances to nearest train/tram/bus
- [ ] Create transport accessibility score

#### 5.2 ABS Census Demographics

Expand existing `social_housing.py` to full demographics.

**Tasks:**
- [ ] Implement ABS Data API client (SDMX 2.1)
- [ ] Extract median income, age distribution, growth
- [ ] Add to location analysis

---

### Phase 6: Client Experience (Weeks 17-20)
**Frontend and reporting improvements**

#### 6.1 Enhanced PDF Reports

**Files to Modify:**
```
backend/services/reports/
├── executive.py       # MODIFY
├── templates/
│   ├── base.html
│   ├── summary.html
│   └── ... (section templates)
└── styles/
    └── report.css
```

**Tasks:**
- [ ] Design professional report template
- [ ] Add Pathway Property branding
- [ ] Create section-specific templates
- [ ] Add charts/visualizations
- [ ] Add map screenshots

#### 6.2 Client Portal (Optional)

**Files to Create:**
```
frontend/app/
├── portal/
│   ├── page.tsx
│   └── properties/[id]/page.tsx
└── admin/
    └── page.tsx
```

**Tasks:**
- [ ] Create client portal layout
- [ ] Add authentication (NextAuth.js)
- [ ] Property list view
- [ ] Report viewer with download

---

### Phase 7: Database Optimization (Future)
**Only if SQLite becomes a bottleneck**

#### 7.1 PostgreSQL + PostGIS Migration

**When to Consider:**
- Processing >100 properties/day
- Spatial queries becoming slow
- Need concurrent write access

**Tasks:**
- [ ] Set up PostgreSQL with PostGIS
- [ ] Create Alembic migrations
- [ ] Migrate existing data
- [ ] Update connection strings

**Note:** This is OPTIONAL for MVP. SQLite + Shapely handles most use cases.

---

## Immediate Action Items

### This Week (Priority Order)

1. **Apply for LANDATA broker account** - Email `data.services@servictoria.com.au`
   - This has lead time, start NOW

2. **Register for Domain API** - `developer.domain.com.au`
   - Free tier, instant access

3. **Download static datasets:**
   - EPA Priority Sites Register
   - Crime Statistics quarterly data
   - School catchment boundaries

4. **Implement Domain API client** - Replace brittle scraping

### Next 2 Weeks

5. **Heritage Victoria API** - Easy win, free API
6. **Crime statistics lookup** - Simple data import
7. **NBN availability** - One library
8. **EPA contamination spatial queries** - High-value risk data

---

## Cost Considerations

| Item | Status | Cost |
|------|--------|------|
| CoreLogic | Already configured | ~$26K/year |
| Geoscape | Already configured | ~$15K/year |
| Azure Document Intelligence | Already configured | ~$0.01/page |
| OpenAI | Already configured | Variable |
| Domain API | **RECOMMENDED** | Free tier (500/day) |
| Heritage Victoria API | **RECOMMENDED** | Free |
| PTV API | Optional | Free |
| LANDATA | **RECOMMENDED** | $8-17/search |
| PropTrack | Optional | $10-50K/year |
| Nearmap | Future | Enterprise pricing |

**Recommendation:** Focus on free/low-cost APIs first. Defer PropTrack and Nearmap.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LANDATA approval delayed | Medium | High | Continue with CoreLogic fallback |
| Domain API rate limits | Low | Medium | Implement caching, use scraper fallback |
| Government API changes | Low | Medium | Abstract behind service interfaces |
| Spatial query performance | Low | Low | SQLite + Shapely sufficient for MVP |
| Feature creep | High | Medium | Focus on high-value gaps only |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Due diligence automation | ~55% | 70-80% |
| Processing time | ~30 min | <15 min |
| Data source coverage | 5 APIs | 10+ APIs |
| Property type support | Residential only | +Rooming, Commercial, Development |

---

## What NOT to Do

1. **Don't rebuild VicPlan integration** - It already works
2. **Don't migrate to PostGIS yet** - SQLite is fine for MVP
3. **Don't implement PropTrack** - Expensive, CoreLogic sufficient
4. **Don't build full client portal** - Focus on core analysis first
5. **Don't over-engineer spatial caching** - Use simple file/SQLite storage

---

## Summary

The revised plan reduces scope from ~180 tasks to ~80 high-value tasks by:

1. Recognizing existing implementations
2. Deferring infrastructure changes
3. Prioritizing free/low-cost APIs
4. Focusing on Pathway Property-specific needs
5. Keeping SQLite for MVP

**Estimated completion:** 16-20 weeks for core features vs original 20+ weeks.

---

*Revised based on detailed code review of existing codebase.*
