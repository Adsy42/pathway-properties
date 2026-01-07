# Pathway Property - Full Implementation Plan

## Executive Summary

This document maps the compass blueprint to the current codebase and defines the work required to achieve full implementation. The existing system covers approximately **40-50%** of the blueprint. The remaining work is organized into 6 phases.

---

## Current State Analysis

### What's Already Built (✅ Complete)

| Feature | Location | Status |
|---------|----------|--------|
| Property scraping (Domain/RealEstate) | `services/property/scraper.py` | ✅ Working |
| CoreLogic integration (AVM, sales) | `services/property/corelogic.py` | ✅ Working |
| Document OCR (Azure) | `services/documents/ocr.py` | ✅ Working |
| RAG document querying | `services/documents/rag.py` | ✅ Working |
| Section 32 analysis | `services/due_diligence/section32.py` | ✅ Working |
| Title analysis (caveats, covenants, easements) | `services/due_diligence/title_analysis.py` | ✅ Working |
| Flood/bushfire risk (Geoscape) | `services/gatekeeper/flood_fire.py` | ✅ Working |
| Zoning/overlays (VicPlan) | `services/gatekeeper/zoning.py` | ✅ Working |
| Strata/OC analysis | `services/due_diligence/strata.py` | ✅ Working |
| 25-factor risk scoring | `services/due_diligence/risk_scoring.py` | ✅ Working |
| Stamp duty calculator (VIC) | `services/due_diligence/stamp_duty.py` | ✅ Working |
| Cashflow modeling | `services/due_diligence/financial.py` | ✅ Working |
| Flight path noise check | `services/gatekeeper/flight_paths.py` | ✅ Working |
| Social housing density | `services/gatekeeper/social_housing.py` | ✅ Working |
| Specialist referrals | `services/due_diligence/specialist_referrals.py` | ✅ Working |
| PDF report generation | `services/reports/executive.py` | ✅ Working |
| Frontend UI (4 stages) | `frontend/` | ✅ Working |
| SQLite database | `database.py` | ✅ Working |

### What's Missing (❌ Not Implemented)

| Blueprint Feature | Priority | Complexity |
|-------------------|----------|------------|
| LANDATA DDP API (official title searches) | Critical | High |
| PostGIS spatial database | Critical | High |
| EPA Victoria contamination data | High | Medium |
| Heritage Victoria API | High | Low |
| Mining/GeoVic tenements | High | Medium |
| Melbourne Water flood data | High | Medium |
| School catchment zones | Medium | Medium |
| Crime statistics integration | Medium | Low |
| PTV transport API | Medium | Medium |
| NBN availability check | Medium | Low |
| ABS Census full demographics | Medium | Medium |
| Domain API (replace scraping) | Medium | Low |
| PropTrack API integration | Low | Medium |
| VCAT decision scraping | Low | High |
| Council permit searches | Low | High |
| Rooming house module | High | Medium |
| Commercial property module | High | High |
| Development feasibility module | High | High |
| SMSF compliance module | Medium | Medium |
| Islamic finance compatibility | Medium | Low |
| Portfolio alignment scoring | Medium | Medium |
| Consumer Victoria checklist | Medium | Low |
| Nearmap historical imagery | Low | Medium |
| Cultural heritage sensitivity | Medium | Medium |
| Growth area contributions | Medium | Medium |
| Client portal & white-labeling | Medium | High |

---

## Phase 1: Foundation & Database Infrastructure

**Duration: Weeks 1-3**

### 1.1 PostgreSQL + PostGIS Migration

**Objective:** Replace SQLite with PostgreSQL + PostGIS for production-grade spatial queries.

**Files to Create/Modify:**

```
backend/
├── database.py                    # MODIFY: Add PostGIS support
├── migrations/
│   ├── __init__.py
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_spatial_tables.py
│   │   └── 003_add_cached_datasets.py
│   └── env.py
├── models/
│   ├── __init__.py
│   ├── property.py               # SQLAlchemy models
│   ├── document.py
│   ├── analysis.py
│   └── spatial.py                # NEW: Spatial dataset models
```

**New Tables Required:**

```sql
-- Cached spatial datasets
CREATE TABLE vic_planning_zones (
    id SERIAL PRIMARY KEY,
    zone_code VARCHAR(20),
    zone_name VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 4326),
    planning_scheme VARCHAR(100),
    updated_at TIMESTAMP
);

CREATE TABLE vic_overlays (
    id SERIAL PRIMARY KEY,
    overlay_code VARCHAR(20),
    overlay_name VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 4326),
    planning_scheme VARCHAR(100),
    updated_at TIMESTAMP
);

CREATE TABLE vic_bushfire_prone (
    id SERIAL PRIMARY KEY,
    bpa_category VARCHAR(50),
    geometry GEOMETRY(MultiPolygon, 4326),
    updated_at TIMESTAMP
);

CREATE TABLE vic_flood_zones (
    id SERIAL PRIMARY KEY,
    flood_type VARCHAR(50),  -- LSIO, SBO, floodway
    ari VARCHAR(20),         -- 1%, 0.5%, PMF
    geometry GEOMETRY(MultiPolygon, 4326),
    source VARCHAR(100),
    updated_at TIMESTAMP
);

CREATE TABLE vic_heritage_places (
    id SERIAL PRIMARY KEY,
    vhr_number VARCHAR(20),
    place_name VARCHAR(500),
    address TEXT,
    municipality VARCHAR(100),
    geometry GEOMETRY(Point, 4326),
    significance TEXT,
    updated_at TIMESTAMP
);

CREATE TABLE epa_priority_sites (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(50),
    site_name VARCHAR(500),
    site_type VARCHAR(100),
    status VARCHAR(50),
    geometry GEOMETRY(Polygon, 4326),
    updated_at TIMESTAMP
);

CREATE TABLE mining_tenements (
    id SERIAL PRIMARY KEY,
    tenement_id VARCHAR(50),
    tenement_type VARCHAR(100),
    holder_name VARCHAR(500),
    geometry GEOMETRY(MultiPolygon, 4326),
    status VARCHAR(50),
    updated_at TIMESTAMP
);

CREATE TABLE school_catchments (
    id SERIAL PRIMARY KEY,
    school_name VARCHAR(255),
    school_type VARCHAR(50),  -- primary, secondary
    school_id VARCHAR(50),
    geometry GEOMETRY(MultiPolygon, 4326),
    updated_at TIMESTAMP
);

-- Spatial index on all geometry columns
CREATE INDEX idx_zones_geom ON vic_planning_zones USING GIST(geometry);
CREATE INDEX idx_overlays_geom ON vic_overlays USING GIST(geometry);
-- ... etc for all spatial tables
```

**Tasks:**

- [ ] 1.1.1 Install PostgreSQL 15+ with PostGIS extension
- [ ] 1.1.2 Create Alembic migration setup
- [ ] 1.1.3 Write migration scripts for existing tables
- [ ] 1.1.4 Create spatial table schemas
- [ ] 1.1.5 Update `database.py` for PostGIS connection
- [ ] 1.1.6 Create spatial query helpers (`services/spatial/queries.py`)
- [ ] 1.1.7 Test migration from SQLite to PostgreSQL
- [ ] 1.1.8 Update docker-compose for local PostgreSQL

### 1.2 Spatial Data Ingestion Pipeline

**Objective:** Download and cache Victorian government spatial datasets.

**Files to Create:**

```
backend/
├── services/
│   └── spatial/
│       ├── __init__.py
│       ├── ingestion.py          # Dataset download & import
│       ├── queries.py            # PostGIS query wrappers
│       ├── refresh.py            # Scheduled refresh jobs
│       └── sources.py            # Data source URLs/configs
├── scripts/
│   ├── ingest_vicplan.py         # VicPlan zones/overlays
│   ├── ingest_bushfire.py        # BPA/BMO boundaries
│   ├── ingest_flood.py           # Melbourne Water flood extents
│   ├── ingest_heritage.py        # Heritage Victoria places
│   ├── ingest_epa.py             # EPA Priority Sites
│   ├── ingest_mining.py          # GeoVic tenements
│   ├── ingest_schools.py         # School catchments
│   └── refresh_all.py            # Master refresh script
```

**Data Sources:**

| Dataset | URL | Format | Refresh |
|---------|-----|--------|---------|
| VicPlan Zones | `plan-gis.mapshare.vic.gov.au/arcgis/rest/services/Planning/` | ArcGIS REST | Weekly |
| VicPlan Overlays | Same as above | ArcGIS REST | Weekly |
| Bushfire Prone Areas | `data.vic.gov.au` | GeoJSON | Biannual |
| Melbourne Water Flood | `data-melbournewater.opendata.arcgis.com` | ArcGIS REST | As updated |
| Heritage Victoria | `api.heritagecouncil.vic.gov.au/v1/` | JSON | Monthly |
| EPA Priority Sites | `data.vic.gov.au/data/dataset/epa-priority-sites` | GeoJSON | Monthly |
| Mining Tenements | GeoVic | ArcGIS REST | Monthly |
| School Catchments | `data.vic.gov.au` | GeoJSON | Annual |

**Tasks:**

- [ ] 1.2.1 Create `services/spatial/sources.py` with all data source configs
- [ ] 1.2.2 Implement VicPlan zone/overlay ingestion script
- [ ] 1.2.3 Implement bushfire prone area ingestion
- [ ] 1.2.4 Implement Melbourne Water flood extent ingestion
- [ ] 1.2.5 Implement Heritage Victoria API ingestion
- [ ] 1.2.6 Implement EPA Priority Sites ingestion
- [ ] 1.2.7 Implement GeoVic mining tenement ingestion
- [ ] 1.2.8 Implement school catchment ingestion
- [ ] 1.2.9 Create master refresh script with logging
- [ ] 1.2.10 Set up cron job / scheduled task for refreshes

### 1.3 LANDATA DDP API Integration

**Objective:** Replace manual title searches with official LANDATA APIs.

**Files to Create:**

```
backend/
├── services/
│   └── landata/
│       ├── __init__.py
│       ├── client.py             # LANDATA API client
│       ├── title_search.py       # Title discovery & retrieval
│       ├── parcel_discovery.py   # SPI lookup by address
│       ├── serv_alert.py         # Title change monitoring
│       └── models.py             # Response models
```

**API Endpoints to Implement:**

| Endpoint | Purpose | Cost |
|----------|---------|------|
| Property Discovery | Address → SPI mapping | Included |
| Title Discovery | SPI → Volume/Folio | Included |
| Register Search Statement | Full title details | $7.80-$16.81 |
| SERV Alert | Title change notifications | Subscription |

**Tasks:**

- [ ] 1.3.1 Apply for LANDATA broker account (`data.services@servictoria.com.au`)
- [ ] 1.3.2 Implement LANDATA API client with auth
- [ ] 1.3.3 Implement Property Discovery endpoint
- [ ] 1.3.4 Implement Title Discovery endpoint
- [ ] 1.3.5 Implement Register Search Statement retrieval
- [ ] 1.3.6 Implement SERV Alert subscription management
- [ ] 1.3.7 Create mock data for development
- [ ] 1.3.8 Integrate with existing title analysis module
- [ ] 1.3.9 Update `services/due_diligence/title_analysis.py` to use LANDATA

---

## Phase 2: Government Data APIs

**Duration: Weeks 4-6**

### 2.1 Heritage Victoria API

**Objective:** Query Victorian Heritage Register for heritage status.

**Files to Create:**

```
backend/
├── services/
│   └── heritage/
│       ├── __init__.py
│       ├── client.py             # Heritage API client
│       ├── models.py             # HAL-formatted response models
│       └── search.py             # Place search by address/coords
```

**API Details:**
- Base URL: `https://api.heritagecouncil.vic.gov.au/v1/`
- Format: HAL-formatted JSON
- Auth: None (public)
- Endpoints: `/places`, `/municipalities`, `/tours`

**Tasks:**

- [ ] 2.1.1 Implement Heritage Victoria API client
- [ ] 2.1.2 Create place search by municipality/address
- [ ] 2.1.3 Create place search by coordinates (spatial proximity)
- [ ] 2.1.4 Parse HAL-formatted responses into Pydantic models
- [ ] 2.1.5 Cache responses in database
- [ ] 2.1.6 Integrate with gatekeeper zoning module

### 2.2 EPA Victoria Contamination Data

**Objective:** Check properties against contaminated sites registry.

**Files to Create:**

```
backend/
├── services/
│   └── epa/
│       ├── __init__.py
│       ├── priority_sites.py     # PSR lookup
│       ├── unearthed.py          # Victoria Unearthed queries
│       └── models.py
```

**Data Sources:**
- Priority Sites Register (GeoJSON download)
- Victoria Unearthed portal (historic landfills, licensed facilities)
- Environmental audits database

**Tasks:**

- [ ] 2.2.1 Download and ingest Priority Sites Register
- [ ] 2.2.2 Implement spatial proximity query (500m radius)
- [ ] 2.2.3 Query Victoria Unearthed for additional contamination data
- [ ] 2.2.4 Create contamination risk scoring
- [ ] 2.2.5 Integrate with `services/due_diligence/environmental.py`

### 2.3 Mining Tenements (GeoVic)

**Objective:** Check for mining/exploration licenses affecting property.

**Files to Create:**

```
backend/
├── services/
│   └── mining/
│       ├── __init__.py
│       ├── geovic.py             # GeoVic API client
│       └── models.py
```

**Tasks:**

- [ ] 2.3.1 Implement GeoVic spatial API client
- [ ] 2.3.2 Query exploration licenses by coordinates
- [ ] 2.3.3 Query mining permits and quarry authorizations
- [ ] 2.3.4 Create tenement risk assessment
- [ ] 2.3.5 Add to risk scoring framework

### 2.4 Melbourne Water Flood Data

**Objective:** Enhanced flood risk assessment beyond Geoscape.

**Files to Create:**

```
backend/
├── services/
│   └── flood/
│       ├── __init__.py
│       ├── melbourne_water.py    # Melbourne Water Open Data
│       ├── risk_assessment.py    # Flood risk scoring
│       └── models.py
```

**Data Available:**
- 1-in-100 year flood extent
- 1-in-200 year flood extent
- Probable Maximum Flood (PMF)
- Floodway overlays
- Drainage infrastructure

**Tasks:**

- [ ] 2.4.1 Implement Melbourne Water ArcGIS REST client
- [ ] 2.4.2 Download and cache flood extent polygons
- [ ] 2.4.3 Implement parcel intersection queries
- [ ] 2.4.4 Calculate flood depth at property
- [ ] 2.4.5 Update `services/gatekeeper/flood_fire.py` to use enhanced data

### 2.5 Cultural Heritage Sensitivity

**Objective:** Check for Aboriginal cultural heritage sensitivity.

**Files to Create:**

```
backend/
├── services/
│   └── cultural_heritage/
│       ├── __init__.py
│       ├── sensitivity.py        # Cultural heritage sensitivity check
│       └── models.py
```

**Tasks:**

- [ ] 2.5.1 Integrate with VicPlan cultural heritage sensitivity layers
- [ ] 2.5.2 Check Aboriginal Victoria preliminary assessment requirements
- [ ] 2.5.3 Flag properties requiring Cultural Heritage Management Plan

### 2.6 Growth Area Infrastructure Contributions

**Objective:** Identify properties in growth areas with ICP obligations.

**Files to Create:**

```
backend/
├── services/
│   └── growth_areas/
│       ├── __init__.py
│       ├── infrastructure.py     # ICP zone detection
│       └── models.py
```

**Tasks:**

- [ ] 2.6.1 Download growth area boundary datasets
- [ ] 2.6.2 Implement ICP zone detection
- [ ] 2.6.3 Calculate estimated infrastructure contributions
- [ ] 2.6.4 Flag Melbourne Strategic Assessment biodiversity areas

---

## Phase 3: Enrichment Data Sources

**Duration: Weeks 7-9**

### 3.1 School Catchment Integration

**Objective:** Identify school catchments and calculate distances.

**Files to Create:**

```
backend/
├── services/
│   └── schools/
│       ├── __init__.py
│       ├── catchments.py         # Catchment zone lookup
│       ├── distances.py          # Distance calculations
│       └── models.py
```

**Tasks:**

- [ ] 3.1.1 Download Victorian school zone boundaries
- [ ] 3.1.2 Implement catchment zone lookup by coordinates
- [ ] 3.1.3 Calculate distances to nearest primary/secondary schools
- [ ] 3.1.4 Add school catchment desirability scoring
- [ ] 3.1.5 Display in location analysis section

### 3.2 Crime Statistics Integration

**Objective:** Provide suburb-level crime data for risk assessment.

**Files to Create:**

```
backend/
├── services/
│   └── crime/
│       ├── __init__.py
│       ├── csa_vic.py            # Crime Statistics Agency Victoria
│       └── models.py
```

**Data Source:** `crimestatistics.vic.gov.au/crime-statistics/latest-victorian-crime-data/download-data`

**Tasks:**

- [ ] 3.2.1 Download quarterly crime statistics data
- [ ] 3.2.2 Parse Excel files into database
- [ ] 3.2.3 Implement suburb/LGA/postcode lookup
- [ ] 3.2.4 Calculate per-capita offense rates
- [ ] 3.2.5 Trend analysis (year-over-year)
- [ ] 3.2.6 Integrate into location analysis

### 3.3 ABS Census Full Demographics

**Objective:** Comprehensive demographic analysis beyond social housing.

**Files to Create:**

```
backend/
├── services/
│   └── demographics/
│       ├── __init__.py
│       ├── abs_api.py            # ABS Data API client
│       ├── analysis.py           # Demographic analysis
│       └── models.py
```

**API Details:**
- Base URL: `https://data.api.abs.gov.au`
- Format: SDMX 2.1
- Auth: None required

**Metrics to Extract:**
- Median household income
- Age distribution
- Household composition
- Population growth rate
- Employment statistics
- Education levels

**Tasks:**

- [ ] 3.3.1 Implement ABS Data API client (SDMX 2.1)
- [ ] 3.3.2 Map property coordinates to SA1/SA2/mesh block
- [ ] 3.3.3 Extract key demographic indicators
- [ ] 3.3.4 Calculate growth trends
- [ ] 3.3.5 Update `services/gatekeeper/social_housing.py` to use full census data
- [ ] 3.3.6 Integrate into location analysis

### 3.4 PTV Transport Accessibility

**Objective:** Calculate transport accessibility scores.

**Files to Create:**

```
backend/
├── services/
│   └── transport/
│       ├── __init__.py
│       ├── ptv_api.py            # PTV GTFS-R API client
│       ├── accessibility.py      # Accessibility scoring
│       └── models.py
```

**API Details:**
- Portal: `developer.vic.gov.au`
- Format: GTFS-R (realtime timetables)
- License: Creative Commons

**Tasks:**

- [ ] 3.4.1 Register for PTV API access
- [ ] 3.4.2 Implement GTFS-R API client
- [ ] 3.4.3 Calculate distances to nearest train stations
- [ ] 3.4.4 Calculate distances to nearest tram stops
- [ ] 3.4.5 Calculate distances to nearest bus routes
- [ ] 3.4.6 Create transport accessibility score (0-100)
- [ ] 3.4.7 Integrate into location analysis

### 3.5 NBN Availability Check

**Objective:** Verify NBN service availability and technology type.

**Files to Create:**

```
backend/
├── services/
│   └── utilities/
│       ├── __init__.py
│       ├── nbn.py                # NBN availability check
│       └── models.py
```

**Implementation:** Use `nbnpy` library (unofficial API)

**Tasks:**

- [ ] 3.5.1 Install and test `nbnpy` library
- [ ] 3.5.2 Implement address lookup
- [ ] 3.5.3 Extract technology type (FTTP, FTTC, FTTN, HFC, Fixed Wireless)
- [ ] 3.5.4 Extract maximum line speed
- [ ] 3.5.5 Flag properties without NBN or with inferior technology
- [ ] 3.5.6 Add to property enrichment data

---

## Phase 4: Commercial Property Data APIs

**Duration: Weeks 10-12**

### 4.1 Domain API Integration (Replace Scraping)

**Objective:** Use official Domain API instead of HTML scraping.

**Files to Modify:**

```
backend/
├── services/
│   └── property/
│       ├── domain_api.py         # NEW: Official Domain API
│       ├── scraper.py            # MODIFY: Fallback only
│       └── enrichment.py         # MODIFY: Use Domain API
```

**API Details:**
- Portal: `developer.domain.com.au`
- Free tier: 500 calls/day
- Endpoints: listings, property data, suburb stats

**Tasks:**

- [ ] 4.1.1 Register for Domain API Innovation tier
- [ ] 4.1.2 Implement Domain API client with OAuth 2.0
- [ ] 4.1.3 Implement listings search endpoint
- [ ] 4.1.4 Implement property details endpoint
- [ ] 4.1.5 Implement suburb performance endpoint
- [ ] 4.1.6 Update enrichment to prefer Domain API
- [ ] 4.1.7 Keep scraper as fallback

### 4.2 PropTrack API Integration (Optional)

**Objective:** Add PropTrack as alternative/supplementary data source.

**Files to Create:**

```
backend/
├── services/
│   └── proptrack/
│       ├── __init__.py
│       ├── client.py             # PropTrack OAuth 2.0 client
│       ├── transactions.py       # Transaction search
│       ├── valuations.py         # AVM valuations
│       └── models.py
```

**Note:** PropTrack requires enterprise agreement ($10K-$50K+/year)

**Tasks:**

- [ ] 4.2.1 Contact PropTrack for enterprise pricing
- [ ] 4.2.2 Implement OAuth 2.0 client
- [ ] 4.2.3 Implement transaction search
- [ ] 4.2.4 Implement AVM valuations
- [ ] 4.2.5 Implement market supply/demand metrics
- [ ] 4.2.6 Create data source aggregation layer

### 4.3 Enhanced CoreLogic Integration

**Objective:** Expand CoreLogic usage for additional data points.

**Files to Modify:**

```
backend/
├── services/
│   └── property/
│       └── corelogic.py          # MODIFY: Add more endpoints
```

**Additional Endpoints:**
- Comparable sales (detailed)
- Suburb statistics
- Market trends
- Historical median prices

**Tasks:**

- [ ] 4.3.1 Add comparable sales endpoint
- [ ] 4.3.2 Add suburb statistics endpoint
- [ ] 4.3.3 Add market trends endpoint
- [ ] 4.3.4 Implement median price history
- [ ] 4.3.5 Create automated comparable sales analysis

---

## Phase 5: Property-Type Specific Modules

**Duration: Weeks 13-16**

### 5.1 Rooming House Module

**Objective:** Specialized due diligence for rooming house investments.

**Files to Create:**

```
backend/
├── services/
│   └── property_types/
│       ├── __init__.py
│       ├── rooming_house/
│       │   ├── __init__.py
│       │   ├── compliance.py     # Rooming house compliance
│       │   ├── yield_model.py    # Per-room yield modeling
│       │   ├── fire_safety.py    # Part 13 Building Regs
│       │   └── models.py
```

**Compliance Checks:**
- Planning permit for rooming house use
- Building permit classification
- Fire safety requirements (Part 13 Building Regulations)
- Minimum room sizes
- Amenity ratios (bathrooms per occupant)
- Registration status

**Tasks:**

- [ ] 5.1.1 Create rooming house compliance checklist
- [ ] 5.1.2 Implement fire safety requirement checker
- [ ] 5.1.3 Implement room size validator
- [ ] 5.1.4 Implement amenity ratio calculator
- [ ] 5.1.5 Create per-room yield model
- [ ] 5.1.6 Calculate rooming house-specific ROI
- [ ] 5.1.7 Add rooming house risk factors (council attitude, neighbor objections)
- [ ] 5.1.8 Create rooming house report section

### 5.2 Commercial Property Module

**Objective:** Specialized due diligence for commercial investments.

**Files to Create:**

```
backend/
├── services/
│   └── property_types/
│       ├── commercial/
│       │   ├── __init__.py
│       │   ├── lease_analysis.py # Lease term analysis
│       │   ├── tenant_credit.py  # Tenant covenant strength
│       │   ├── yield_metrics.py  # Cap rate, WALE
│       │   ├── zoning.py         # Commercial zoning compliance
│       │   └── models.py
```

**Lease Analysis:**
- Tenant covenant strength assessment
- Lease expiry date and options
- Rental increase mechanisms
- Outgoings responsibility
- Make-good provisions

**Yield Metrics:**
- Net yield calculation
- Cap rate comparison
- Weighted Average Lease Expiry (WALE)

**Tasks:**

- [ ] 5.2.1 Create lease document parser (extract key terms)
- [ ] 5.2.2 Implement tenant covenant strength assessment
- [ ] 5.2.3 Calculate net yield and cap rate
- [ ] 5.2.4 Calculate WALE for multi-tenant properties
- [ ] 5.2.5 Check zoning compliance for permitted uses
- [ ] 5.2.6 Check car parking compliance
- [ ] 5.2.7 Create commercial property report section

### 5.3 Development Feasibility Module

**Objective:** Automated development feasibility assessment.

**Files to Create:**

```
backend/
├── services/
│   └── property_types/
│       ├── development/
│       │   ├── __init__.py
│       │   ├── site_analysis.py  # Physical site assessment
│       │   ├── planning.py       # Planning scheme analysis
│       │   ├── feasibility.py    # Financial feasibility model
│       │   └── models.py
```

**Site Analysis:**
- Land area and frontage
- Slope gradient
- Services availability (sewer, water, power, gas)

**Planning Assessment:**
- Zone density controls
- Height limits
- Setback requirements
- Overlay restrictions
- Neighborhood character study implications

**Financial Model:**
- Gross Realization Value (GRV)
- Construction cost estimates
- Statutory costs (permits, infrastructure contributions, GST)
- Development margin calculation
- Feasibility threshold (20% margin)

**Tasks:**

- [ ] 5.3.1 Create site analysis module (extract from title/planning)
- [ ] 5.3.2 Implement density control parser from planning scheme
- [ ] 5.3.3 Calculate maximum dwelling yield
- [ ] 5.3.4 Implement construction cost estimator (per sqm rates)
- [ ] 5.3.5 Calculate statutory costs
- [ ] 5.3.6 Create development feasibility calculator
- [ ] 5.3.7 Generate development feasibility report section

### 5.4 SMSF Compliance Module

**Objective:** Verify SMSF property purchase compliance.

**Files to Create:**

```
backend/
├── services/
│   └── property_types/
│       ├── smsf/
│       │   ├── __init__.py
│       │   ├── compliance.py     # SMSF rule checking
│       │   ├── lrba.py           # Limited Recourse Borrowing
│       │   └── models.py
```

**Compliance Checks:**
- Single acquirable asset rule
- Arm's length transaction requirements
- Related party restrictions
- In-house asset rules
- LRBA (Limited Recourse Borrowing Arrangement) eligibility

**Tasks:**

- [ ] 5.4.1 Create SMSF compliance checklist
- [ ] 5.4.2 Implement arm's length transaction validator
- [ ] 5.4.3 Implement related party restriction checker
- [ ] 5.4.4 Create LRBA eligibility assessment
- [ ] 5.4.5 Generate SMSF compliance report section

### 5.5 Islamic Finance Compatibility Module

**Objective:** Check property suitability for Islamic/Halal financing.

**Files to Create:**

```
backend/
├── services/
│   └── property_types/
│       ├── islamic_finance/
│       │   ├── __init__.py
│       │   ├── compatibility.py  # Halal loan compatibility
│       │   └── models.py
```

**Compatibility Checks:**
- Property type suitability (no pubs, gambling venues, etc.)
- Musharakah Mutanaqisah (diminishing partnership) compatibility
- Ijara (lease-to-own) structure suitability

**Tasks:**

- [ ] 5.5.1 Create Sharia compliance checklist
- [ ] 5.5.2 Implement property type screening (prohibited uses)
- [ ] 5.5.3 Create Islamic finance compatibility report section

---

## Phase 6: Investment Analytics & Reporting

**Duration: Weeks 17-20**

### 6.1 Enhanced Investment Scoring

**Objective:** Implement full investment scoring framework from blueprint.

**Files to Modify:**

```
backend/
├── services/
│   └── due_diligence/
│       ├── investment_scoring.py # NEW: Investment-specific scoring
│       └── risk_scoring.py       # MODIFY: Add investment factors
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

- [ ] 6.1.1 Create investment scoring module
- [ ] 6.1.2 Implement yield potential scoring (benchmarks by suburb)
- [ ] 6.1.3 Implement capital growth indicator scoring
- [ ] 6.1.4 Implement holding cost efficiency scoring
- [ ] 6.1.5 Implement development upside scoring
- [ ] 6.1.6 Create composite investment score
- [ ] 6.1.7 Add investment score to reports

### 6.2 Consumer Victoria Checklist Tracking

**Objective:** Map all checks to Section 33B requirements.

**Files to Modify:**

```
backend/
├── services/
│   └── due_diligence/
│       └── compliance.py         # MODIFY: Add Section 33B mapping
```

**15 Checklist Items:**
1. Planning controls and zoning
2. Flood and bushfire risk
3. Title and ownership
4. Contamination and environmental risks
5. Mining and earth resources
6. Heritage status
7. Growth area infrastructure contributions
8. Cultural heritage sensitivity
9. Owners corporation assessment
10. Council planning permits
11. Building permits
12. VCAT decisions
13. Building safety inspections
14. Pool/spa compliance
15. Insurance verification

**Tasks:**

- [ ] 6.2.1 Map all existing checks to Section 33B items
- [ ] 6.2.2 Create compliance status tracker (verified/pending/manual required)
- [ ] 6.2.3 Generate client-facing checklist report
- [ ] 6.2.4 Identify items requiring manual verification

### 6.3 Portfolio Alignment Scoring

**Objective:** Match properties against client investment criteria.

**Files to Create:**

```
backend/
├── services/
│   └── portfolio/
│       ├── __init__.py
│       ├── client_brief.py       # Client criteria storage
│       ├── alignment.py          # Property-brief matching
│       └── models.py
```

**Client Brief Parameters:**
- Target yield range
- Budget range
- Preferred locations
- Property type preferences
- Risk tolerance
- Investment horizon
- Value-add requirements

**Tasks:**

- [ ] 6.3.1 Create client brief data model
- [ ] 6.3.2 Implement brief storage/retrieval API
- [ ] 6.3.3 Create property-brief alignment scorer
- [ ] 6.3.4 Rank properties against client criteria
- [ ] 6.3.5 Add portfolio alignment to reports

### 6.4 Enhanced PDF Report Generation

**Objective:** Professional white-labeled reports with Pathway Property branding.

**Files to Modify:**

```
backend/
├── services/
│   └── reports/
│       ├── executive.py          # MODIFY: Enhanced formatting
│       ├── templates/
│       │   ├── base.html         # Base template with branding
│       │   ├── summary.html      # Executive summary
│       │   ├── legal.html        # Legal analysis section
│       │   ├── physical.html     # Physical analysis section
│       │   ├── financial.html    # Financial analysis section
│       │   ├── risk.html         # Risk assessment section
│       │   ├── compliance.html   # Compliance checklist
│       │   └── location.html     # Location analysis section
│       └── styles/
│           └── report.css        # Professional styling
```

**Report Sections:**
1. Executive Summary (snapshot, scores, flags, action items)
2. Title & Ownership
3. Planning Assessment
4. Risk Analysis (flood, bushfire, contamination, mining)
5. Financial Analysis (valuation, yield, cashflow)
6. Location Analysis (schools, crime, transport, demographics)
7. Compliance Checklist (Section 33B status)
8. Appendices (supporting data)

**Tasks:**

- [ ] 6.4.1 Design professional report template
- [ ] 6.4.2 Add Pathway Property branding
- [ ] 6.4.3 Create section-specific templates
- [ ] 6.4.4 Implement chart/graph generation
- [ ] 6.4.5 Add map visualizations to report
- [ ] 6.4.6 Create appendix with source citations
- [ ] 6.4.7 Optimize PDF generation performance

### 6.5 Client Portal & White-Labeling

**Objective:** Professional client-facing portal for report access.

**Files to Create:**

```
frontend/
├── app/
│   ├── portal/
│   │   ├── page.tsx              # Client portal home
│   │   ├── properties/
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Property details
│   │   └── reports/
│   │       └── [id]/
│   │           └── page.tsx      # Report viewer
│   └── admin/
│       ├── page.tsx              # Admin dashboard
│       ├── clients/
│       │   └── page.tsx          # Client management
│       └── branding/
│           └── page.tsx          # White-label settings
```

**Tasks:**

- [ ] 6.5.1 Create client portal layout
- [ ] 6.5.2 Implement property list view for clients
- [ ] 6.5.3 Implement report viewer with download
- [ ] 6.5.4 Create admin dashboard
- [ ] 6.5.5 Implement white-label branding settings
- [ ] 6.5.6 Add authentication (NextAuth.js or similar)

---

## Phase 7: Advanced Features (Ongoing)

**Duration: Weeks 21+**

### 7.1 VCAT Decision Monitoring

**Objective:** Scrape and analyze VCAT decisions for relevant properties.

**Tasks:**

- [ ] 7.1.1 Build AustLII scraper for VCAT decisions
- [ ] 7.1.2 Extract case details (address, outcome, reasons)
- [ ] 7.1.3 Match decisions to property addresses
- [ ] 7.1.4 Flag properties with adverse VCAT history

### 7.2 Council Permit Aggregation

**Objective:** Aggregate permit data from multiple council sources.

**Tasks:**

- [ ] 7.2.1 Integrate PlanningAlerts.org.au feed
- [ ] 7.2.2 Build scrapers for major council ePlanning portals
- [ ] 7.2.3 Detect nearby development applications
- [ ] 7.2.4 Flag potential impact on subject property

### 7.3 Nearmap Historical Imagery

**Objective:** Detect unauthorized building work through aerial imagery.

**Tasks:**

- [ ] 7.3.1 Obtain Nearmap enterprise subscription
- [ ] 7.3.2 Implement imagery API integration
- [ ] 7.3.3 Build change detection algorithm
- [ ] 7.3.4 Flag properties with unexplained structural changes

### 7.4 Machine Learning Enhancements

**Objective:** Improve valuation and risk prediction accuracy.

**Tasks:**

- [ ] 7.4.1 Train valuation model on historical sales data
- [ ] 7.4.2 Build risk prediction model based on historical outcomes
- [ ] 7.4.3 Implement A/B testing for model accuracy
- [ ] 7.4.4 Create model retraining pipeline

---

## API Key Requirements

| Service | Required For | Priority | Cost |
|---------|--------------|----------|------|
| LANDATA DDP | Title searches | Critical | Per-search ($8-17) |
| Domain API | Listings/property data | High | Free tier available |
| PropTrack | Enhanced valuations | Medium | Enterprise ($10-50K/yr) |
| CoreLogic | AVM, sales history | Critical | Already configured |
| Geoscape | Flood/bushfire | Critical | Already configured |
| Azure Document Intelligence | OCR | Critical | Already configured |
| OpenAI | LLM reasoning | Critical | Already configured |
| PTV | Transport data | Medium | Free (registration required) |
| Nearmap | Historical imagery | Low | Enterprise pricing |

---

## Database Schema Additions Summary

```sql
-- New tables for Phase 1-3
vic_planning_zones
vic_overlays
vic_bushfire_prone
vic_flood_zones
vic_heritage_places
epa_priority_sites
mining_tenements
school_catchments
crime_statistics
transport_stops
census_demographics

-- New tables for Phase 5
client_briefs
rooming_house_compliance
commercial_leases
development_feasibilities
smsf_compliance

-- New tables for Phase 6
portfolio_alignments
compliance_checklists
report_templates
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Due diligence automation rate | 70-80% of Section 33B checklist |
| Processing time per property | < 30 minutes (from 4-8 hours) |
| API uptime | 99.5% |
| Report generation time | < 2 minutes |
| Data refresh latency | < 24 hours for critical datasets |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LANDATA API access denial | Fallback to current CoreLogic title data |
| Government API changes | Abstract data sources behind interfaces |
| Rate limiting | Implement aggressive caching |
| Data staleness | Scheduled refresh jobs with monitoring |
| Cost overrun | Monitor API usage, set budget alerts |

---

## Next Steps

1. **Immediate:** Apply for LANDATA DDP broker account
2. **Week 1:** Set up PostgreSQL + PostGIS infrastructure
3. **Week 2:** Begin spatial data ingestion pipeline
4. **Week 3:** Implement LANDATA integration
5. **Week 4+:** Follow phase-by-phase implementation

---

*This plan was generated based on analysis of the compass blueprint document and current codebase state.*
