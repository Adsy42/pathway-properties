# Environment Variables Guide

## Quick Answer: **None Required for Demo!**

The app works **without any API keys** using mock data. Perfect for testing and demos.

---

## For Production-Level Accuracy

### 🔴 **Critical** (Required for Real Analysis)

These are needed for actual document processing and AI analysis:

```bash
# AI Document Analysis
ANTHROPIC_API_KEY=sk-ant-...          # Claude 3.5 Sonnet for legal extraction
OPENAI_API_KEY=sk-...                  # GPT-4o for embeddings & reasoning
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://...  # OCR for PDFs
AZURE_DOCUMENT_INTELLIGENCE_KEY=...
```

**Where to get:**
- **Anthropic**: https://console.anthropic.com → API Keys
- **OpenAI**: https://platform.openai.com → API Keys
- **Azure**: https://portal.azure.com → Create "Document Intelligence" resource

**Cost:** ~$0.01-0.05 per property analysis (depends on document size)

---

### 🟡 **Highly Recommended** (Better Data Quality)

For accurate property valuations and risk data:

```bash
# Property Valuations
CORELOGIC_CLIENT_ID=...
CORELOGIC_CLIENT_SECRET=...
# Contact: sales@corelogic.com.au (2-4 weeks approval, ~$26k/yr)

# Flood/Bushfire Risk
GEOSCAPE_API_KEY=...
# Contact: geoscape.com.au/contact (1-2 weeks, ~$15k/yr)

# Listing Details (Free Dev Tier Available)
DOMAIN_API_KEY=...
DOMAIN_CLIENT_ID=...
DOMAIN_CLIENT_SECRET=...
# Sign up: developer.domain.com.au (immediate access)
```

**Note:** CoreLogic and Geoscape are expensive but provide industry-best data. For MVP demo, mock data is fine.

---

### 🟢 **Optional** (Nice to Have)

```bash
# Map Visualization
NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1...
# Get free token: https://account.mapbox.com/access-tokens/
# Free tier: 50,000 map loads/month

# Vector DB (Production)
# VECTOR_DB=pinecone
# PINECONE_API_KEY=...
# PINECONE_INDEX_NAME=pathway-properties
# Default: Uses local Chroma (no key needed)
```

---

## Setup Instructions

### 1. Create `.env.local` file

```bash
cd /home/adsy42/Coding/pathway-properties
cp env.example .env.local
```

### 2. Edit `.env.local`

Add only the keys you want to use. Leave others empty - the app will use mock data.

**Minimal setup for real AI analysis:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key-here
```

### 3. Restart Backend

After adding keys, restart the backend:
```bash
# Stop backend (Ctrl+C)
# Then restart:
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

---

## What Works Without Keys?

✅ **Street Level Analysis** - Uses mock data for:
- Social housing density
- Flood risk
- Bushfire risk
- Flight paths
- Zoning

✅ **Property Scraping** - Falls back to HTML scraping if Domain API unavailable

✅ **Document Upload** - Files are saved and tracked

⚠️ **Document OCR** - Falls back to basic `pypdf` extraction (less accurate)

⚠️ **RAG Queries** - Returns mock responses

⚠️ **Legal/Physical Analysis** - Uses simplified mock extraction

---

## Cost Estimates

| Service | Cost | Usage |
|---------|------|-------|
| **Anthropic Claude** | $3/$15 per 1M tokens | Legal extraction, RAG |
| **OpenAI Embeddings** | $0.13 per 1M tokens | Vector search |
| **Azure OCR** | $0.01 per page | PDF processing |
| **CoreLogic** | ~$26,400/yr | Property valuations |
| **Geoscape** | ~$15,000/yr | Risk data |
| **Domain API** | Free (dev tier) | Listing details |
| **Mapbox** | Free (50k loads/mo) | Maps |

**Typical cost per property analysis:** $0.10-0.50 (without CoreLogic/Geoscape)

---

## Testing Without Keys

The app is designed to work fully in demo mode:

1. **No `.env.local` file needed** - Uses all defaults
2. **Mock data everywhere** - Realistic but not real
3. **Full UI flow** - All features accessible
4. **Perfect for demos** - Shows complete functionality

---

## Production Checklist

When ready for real use:

- [ ] Add `ANTHROPIC_API_KEY` for legal analysis
- [ ] Add `OPENAI_API_KEY` for embeddings
- [ ] Add `AZURE_DOCUMENT_INTELLIGENCE_*` for OCR
- [ ] (Optional) Add `CORELOGIC_*` for valuations
- [ ] (Optional) Add `GEOSCAPE_API_KEY` for risk data
- [ ] (Optional) Add `NEXT_PUBLIC_MAPBOX_TOKEN` for maps
- [ ] Set up proper database (PostgreSQL instead of SQLite)
- [ ] Configure production vector DB (Pinecone)

---

## Security Notes

⚠️ **Never commit `.env.local` to git** - It's already in `.gitignore`

✅ **Use environment variables** - Don't hardcode keys in code

✅ **Rotate keys regularly** - Especially if exposed

✅ **Use separate keys** - Dev vs Production environments







