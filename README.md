# Pathway Property - AI Due Diligence Platform

AI-powered property due diligence for Australian real estate. Automates risk assessment, legal document analysis, and investment insights.

## 🏗️ Architecture

```
pathway-properties/
├── backend/              # Python FastAPI
│   ├── main.py           # API endpoints
│   ├── database.py       # SQLite + SQLAlchemy
│   ├── models.py         # Pydantic schemas
│   ├── config.py         # Environment config
│   └── services/
│       ├── property/     # Scraping + CoreLogic
│       ├── gatekeeper/   # Street level analysis
│       ├── documents/    # OCR + RAG
│       ├── analysis/     # Legal/Physical/Financial
│       └── reports/      # PDF generation
│
├── frontend/             # Next.js 14
│   ├── app/              # App router pages
│   ├── components/       # React components
│   └── lib/              # API client + utils
│
└── env.example           # Environment template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### 1. Clone and Setup

```bash
cd pathway-properties

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment

Create `.env.local` files in both `backend/` and `frontend/` directories:

**Backend** (`backend/.env.local`):
```bash
# Required
OPENAI_API_KEY=           # Get from platform.openai.com

# Optional - for enhanced features
CORELOGIC_CLIENT_ID=      # Contact sales@corelogic.com.au
CORELOGIC_CLIENT_SECRET=
GEOSCAPE_CONSUMER_KEY=    # Contact geoscape.com.au
GEOSCAPE_CONSUMER_SECRET=
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=
MAPBOX_TOKEN=             # Get from mapbox.com
```

**Frontend** (`frontend/.env.local`):
```bash
NEXT_PUBLIC_MAPBOX_TOKEN= # Get from mapbox.com (optional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run the Application

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📋 Features

### Street Level Analysis (Gatekeeper)

Instant "kill criteria" checks:

- ✅ Social housing density (>15% in SA1 = flag)
- ✅ Flight path noise (ANEF >20 = kill)
- ✅ Flood risk (1% AEP building intersection = kill)
- ✅ Bushfire risk (BAL-40/FZ = warning)
- ✅ Zoning & overlays (Heritage = warning)

### Document Analysis

AI-powered extraction from:

- Section 32 Vendor Statements (VIC)
- Contracts for Sale (NSW)
- Strata Reports & AGM Minutes
- Building & Pest Inspection Reports
- Title Searches

Extracts:
- Caveats, covenants, easements
- Owner-builder defect reports
- Special conditions
- Termite damage risk
- Structural concerns

### Financial Analysis

- Gross & net yield calculations
- Cashflow projections (80% LVR)
- Outgoings extraction (rates, levies)
- GST applicability check
- CoreLogic AVM integration

### Sweat Equity Detection

Identifies value-add opportunities:

- Bedroom conversion potential
- Bathroom addition feasibility
- Granny flat opportunities
- ROI calculations

### Reports

- Executive PDF report
- Risk summary with mitigations
- Investment recommendation

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/property/analyze` | POST | Analyze property from URL |
| `/api/property/{id}` | GET | Get property details |
| `/api/documents/upload` | POST | Upload document for OCR |
| `/api/documents/{id}/query` | POST | RAG query on document |
| `/api/analysis/run` | POST | Run full analysis |
| `/api/analysis/{property_id}` | GET | Get analysis results |
| `/api/analysis/{property_id}/report` | POST | Generate PDF report |

## 🧪 Demo Mode

The system includes mock data for all external APIs, allowing full demo functionality without API keys:

- CoreLogic: Returns mock AVM and rental estimates
- Geoscape: Returns mock flood/bushfire data
- VicPlan: Returns mock zoning data
- Azure OCR: Falls back to pypdf text extraction

## 📊 Data Sources

### Free / Included
- ABS Census data (SA1 social housing)
- VicPlan WFS (zoning, overlays)
- NSW ePlanning (NSW zoning)

### Paid APIs (for production accuracy)
- **CoreLogic Trestle** (~$26,400/yr) - AVM, sales history
- **Geoscape Buildings** (~$15,000/yr) - Flood, bushfire risk
- **Azure Document Intelligence** (~$0.01/page) - OCR
- **OpenAI GPT-4o** (~$2.50/$10 per 1M tokens) - LLM reasoning
- **OpenAI Embeddings** (~$0.13 per 1M tokens) - Vector search

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Python async web framework
- **SQLAlchemy** - ORM with SQLite
- **Chroma** - Local vector database
- **OpenAI GPT-4o** - LLM reasoning
- **Azure Document Intelligence** - OCR

### Frontend
- **Next.js 14** - React framework
- **TanStack Query** - Data fetching
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Mapbox GL JS** - Maps

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI app + routes
├── database.py             # SQLite models
├── models.py               # Pydantic schemas
├── config.py               # Settings
└── services/
    ├── property/
    │   ├── scraper.py      # Domain/REA scraping
    │   ├── corelogic.py    # CoreLogic API
    │   └── enrichment.py   # Data combination
    ├── gatekeeper/
    │   ├── social_housing.py
    │   ├── flood_fire.py
    │   ├── zoning.py
    │   ├── flight_paths.py
    │   └── kill_criteria.py
    ├── documents/
    │   ├── ocr.py          # Azure OCR
    │   ├── chunking.py     # Structure-aware
    │   ├── embeddings.py   # OpenAI embeddings
    │   ├── vector_store.py # Chroma
    │   └── rag.py          # Query + answer
    ├── analysis/
    │   ├── orchestrator.py # Run all modules
    │   └── prompts.py      # LLM prompts
    └── reports/
        └── executive.py    # PDF generation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## ⚖️ License

MIT License - see LICENSE file.

## ⚠️ Disclaimer

This tool provides preliminary analysis only. It does not constitute legal, financial, or professional advice. Always seek independent professional advice before purchasing property.
