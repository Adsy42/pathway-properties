# How to Run Pathway Property MVP

## Quick Start (Easiest)

### Option 1: Use Helper Scripts

**Terminal 1 - Backend:**
```bash
cd /home/adsy42/Coding/pathway-properties
./start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
cd /home/adsy42/Coding/pathway-properties
./start-frontend.sh
```

### Option 2: Manual Commands

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Verify It's Working

1. **Backend Health Check:**
   - Open http://localhost:8000/api/health
   - Should return: `{"status":"ok","version":"0.1.0"}`

2. **Backend API Docs:**
   - Open http://localhost:8000/docs
   - Interactive Swagger UI

3. **Frontend:**
   - Open http://localhost:3000
   - You should see the Pathway Property homepage

## Test the Application

1. Go to http://localhost:3000
2. Paste a Domain.com.au or RealEstate.com.au URL
3. Click "Analyze"
4. View street-level analysis results
5. Upload documents (Section 32, Building Report, etc.)
6. Run full analysis
7. View comprehensive dashboard

## Troubleshooting

### Backend won't start
- Make sure virtual environment is activated: `source venv/bin/activate`
- Check if port 8000 is already in use: `lsof -i :8000`
- Try a different port: `uvicorn main:app --reload --port 8001`

### Frontend won't start
- Make sure you're in the `frontend` directory
- Check if port 3000 is already in use: `lsof -i :3000`
- Try a different port: `npm run dev -- -p 3001`

### Database errors
- The database (`pathway.db`) will be created automatically on first run
- If you see errors, delete `backend/pathway.db` and restart

### API connection errors
- Make sure backend is running on port 8000
- Check `frontend/next.config.js` - it proxies `/api/*` to `http://localhost:8000`

## Environment Variables (Optional)

For full functionality, create `.env.local` in the project root:

```bash
cp env.example .env.local
# Then edit .env.local with your API keys
```

**Required for production:**
- `ANTHROPIC_API_KEY` - For Claude LLM
- `OPENAI_API_KEY` - For embeddings
- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` - For OCR
- `AZURE_DOCUMENT_INTELLIGENCE_KEY` - For OCR

**Optional but recommended:**
- `CORELOGIC_CLIENT_ID` / `CORELOGIC_CLIENT_SECRET` - Property valuations
- `GEOSCAPE_API_KEY` - Flood/bushfire data
- `DOMAIN_API_KEY` - Listing details
- `NEXT_PUBLIC_MAPBOX_TOKEN` - Map visualization

**Note:** The app works in demo mode without API keys using mock data.







