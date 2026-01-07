"""
Pathway Property MVP - FastAPI Backend

Main application entry point with all API routes.
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime

from config import get_settings
from database import init_db, get_db, Property, Document, Analysis
from models import (
    HealthResponse,
    PropertyAnalyzeRequest,
    PropertyAnalyzeResponse,
    PropertyManualRequest,
    DocumentType,
    DocumentResponse,
    DocumentQueryRequest,
    DocumentQueryResponse,
    RunAnalysisRequest,
    FullAnalysisResponse,
    PropertyListResponse,
    PropertyListItem,
    Verdict,
)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Pathway Property API",
    description="AI-powered property due diligence for Australian real estate",
    version="0.1.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === STARTUP ===

@app.on_event("startup")
async def startup_event():
    """Initialize database and create required directories."""
    # Create database tables
    init_db()
    
    # Create upload and cache directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.cache_dir, exist_ok=True)
    
    print("✓ Database initialized")
    print(f"✓ Upload directory: {settings.upload_dir}")
    print(f"✓ Cache directory: {settings.cache_dir}")


# === HEALTH CHECK ===

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


# === PROPERTY ENDPOINTS ===

@app.post("/api/property/analyze", response_model=PropertyAnalyzeResponse)
async def analyze_property(
    request: PropertyAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze a property from Domain/RealEstate.com.au URL.
    
    1. Scrapes listing details
    2. Enriches with CoreLogic data
    3. Runs Street Level (Gatekeeper) analysis
    4. Returns verdict: PROCEED / REVIEW / REJECT
    """
    from services.property.enrichment import enrich_property
    from services.gatekeeper.kill_criteria import run_gatekeeper
    
    try:
        # Step 1: Scrape and enrich property data
        property_data = await enrich_property(request.url)
        
        # Step 2: Run gatekeeper analysis
        street_level, verdict, kill_reasons = await run_gatekeeper(
            address=property_data.get("address", ""),
            lat=property_data.get("latitude"),
            lng=property_data.get("longitude"),
            state=property_data.get("state", "VIC")
        )
        
        # Step 3: Save to database
        db_property = Property(
            url=request.url,
            address=property_data.get("address"),
            state=property_data.get("state"),
            listing_data=property_data.get("listing"),
            corelogic_data=property_data.get("corelogic"),
            street_level_analysis=street_level.dict() if street_level else None,
            verdict=verdict.value if verdict else None,
            kill_reasons=kill_reasons
        )
        db.add(db_property)
        db.commit()
        db.refresh(db_property)
        
        # Step 4: Build response
        return PropertyAnalyzeResponse(
            id=db_property.id,
            property=property_data.get("property_details"),
            street_level_analysis=street_level,
            verdict=verdict,
            kill_reasons=kill_reasons,
            created_at=db_property.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/property/manual", response_model=PropertyAnalyzeResponse)
async def add_property_manual(
    request: PropertyManualRequest,
    db: Session = Depends(get_db)
):
    """
    Manually add a property with details (no scraping).
    
    Use this when scraping fails or for testing.
    """
    from services.gatekeeper.kill_criteria import run_gatekeeper
    from services.property.corelogic import enrich_with_corelogic
    
    try:
        # Build listing data from request
        listing_data = {
            "source": "manual",
            "address": request.address,
            "suburb": request.suburb,
            "state": request.state,
            "postcode": request.postcode,
            "bedrooms": request.bedrooms,
            "bathrooms": request.bathrooms,
            "parking": request.parking,
            "land_size": request.land_size,
            "building_size": request.building_size,
            "property_type": request.property_type,
            "price_display": request.price_display,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "description": request.description,
        }
        
        # Enrich with CoreLogic if available
        corelogic_data = await enrich_with_corelogic(
            address=request.address,
            bedrooms=request.bedrooms,
            property_type=request.property_type
        )
        
        # Run gatekeeper analysis
        street_level, verdict, kill_reasons = await run_gatekeeper(
            address=request.address,
            lat=request.latitude,
            lng=request.longitude,
            state=request.state
        )
        
        # Save to database
        db_property = Property(
            url=request.url or f"manual://{request.address}",
            address=request.address,
            state=request.state,
            listing_data=listing_data,
            corelogic_data=corelogic_data,
            street_level_analysis=street_level.dict() if street_level else None,
            verdict=verdict.value if verdict else None,
            kill_reasons=kill_reasons
        )
        db.add(db_property)
        db.commit()
        db.refresh(db_property)
        
        # Build property details for response
        property_details = {
            "address": request.address,
            "suburb": request.suburb,
            "state": request.state,
            "postcode": request.postcode,
            "bedrooms": request.bedrooms,
            "bathrooms": request.bathrooms,
            "parking": request.parking,
            "land_size": request.land_size,
            "property_type": request.property_type,
            "price_display": request.price_display,
            "latitude": request.latitude,
            "longitude": request.longitude,
        }
        
        return PropertyAnalyzeResponse(
            id=db_property.id,
            property=property_details,
            street_level_analysis=street_level,
            verdict=verdict,
            kill_reasons=kill_reasons,
            created_at=db_property.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/property/{property_id}")
async def get_property(property_id: str, db: Session = Depends(get_db)):
    """Get a property by ID."""
    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return {
        "id": property_record.id,
        "url": property_record.url,
        "address": property_record.address,
        "state": property_record.state,
        "listing_data": property_record.listing_data,
        "corelogic_data": property_record.corelogic_data,
        "street_level_analysis": property_record.street_level_analysis,
        "verdict": property_record.verdict,
        "kill_reasons": property_record.kill_reasons,
        "created_at": property_record.created_at,
    }


@app.get("/api/property/{property_id}/street-level")
async def get_street_level(property_id: str, db: Session = Depends(get_db)):
    """Get only street level analysis for a property."""
    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return {
        "street_level_analysis": property_record.street_level_analysis,
        "verdict": property_record.verdict,
        "kill_reasons": property_record.kill_reasons,
    }


@app.get("/api/properties", response_model=PropertyListResponse)
async def list_properties(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List all analyzed properties."""
    properties = db.query(Property).order_by(Property.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(Property).count()
    
    return PropertyListResponse(
        properties=[
            PropertyListItem(
                id=p.id,
                address=p.address or "Unknown",
                verdict=p.verdict,
                created_at=p.created_at
            )
            for p in properties
        ],
        total=total
    )


# === DOCUMENT ENDPOINTS ===

@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    property_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for analysis.
    
    Saves file, triggers OCR processing in background.
    """
    # Verify property exists
    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Create property upload directory
    property_upload_dir = os.path.join(settings.upload_dir, property_id)
    os.makedirs(property_upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(property_upload_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create document record
    doc = Document(
        property_id=property_id,
        document_type=document_type,
        file_path=file_path,
        original_filename=file.filename,
        status="pending"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Trigger background processing
    background_tasks.add_task(process_document, doc.id)
    
    return DocumentResponse(
        id=doc.id,
        property_id=doc.property_id,
        document_type=doc.document_type,
        status=doc.status,
        page_count=doc.page_count,
        created_at=doc.created_at
    )


async def process_document(document_id: str):
    """Background task to OCR and embed a document."""
    from services.documents.ocr import process_document_ocr
    from services.documents.vector_store import embed_document
    
    db = next(get_db())
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return
        
        # Update status
        doc.status = "processing"
        db.commit()
        
        # Run OCR
        ocr_result = await process_document_ocr(doc.file_path)
        doc.ocr_result = ocr_result
        doc.page_count = ocr_result.get("page_count", 0)
        
        # Embed in vector store
        await embed_document(
            document_id=doc.id,
            property_id=doc.property_id,
            document_type=doc.document_type,
            ocr_result=ocr_result
        )
        
        # Update status
        doc.status = "ready"
        doc.processed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        doc.status = "error"
        db.commit()
        print(f"Error processing document {document_id}: {e}")
    finally:
        db.close()


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document status and metadata."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=doc.id,
        property_id=doc.property_id,
        document_type=doc.document_type,
        status=doc.status,
        page_count=doc.page_count,
        created_at=doc.created_at
    )


@app.get("/api/documents/property/{property_id}")
async def list_property_documents(property_id: str, db: Session = Depends(get_db)):
    """List all documents for a property."""
    docs = db.query(Document).filter(Document.property_id == property_id).all()
    return [
        DocumentResponse(
            id=doc.id,
            property_id=doc.property_id,
            document_type=doc.document_type,
            status=doc.status,
            page_count=doc.page_count,
            created_at=doc.created_at
        )
        for doc in docs
    ]


@app.post("/api/documents/{document_id}/query", response_model=DocumentQueryResponse)
async def query_document(
    document_id: str,
    request: DocumentQueryRequest,
    db: Session = Depends(get_db)
):
    """Query a document using RAG."""
    from services.documents.rag import query_document_rag
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail="Document not ready for querying")
    
    result = await query_document_rag(
        document_id=doc.id,
        property_id=doc.property_id,
        question=request.question
    )
    
    return DocumentQueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"]
    )


# === ANALYSIS ENDPOINTS ===

@app.post("/api/analysis/run", response_model=FullAnalysisResponse)
async def run_analysis(
    request: RunAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Run full asset-level analysis on all documents for a property.
    """
    from services.analysis.orchestrator import run_full_analysis
    
    property_record = db.query(Property).filter(Property.id == request.property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get all ready documents
    docs = db.query(Document).filter(
        Document.property_id == request.property_id,
        Document.status == "ready"
    ).all()
    
    if not docs:
        raise HTTPException(status_code=400, detail="No documents ready for analysis")
    
    # Run analysis
    analysis_result = await run_full_analysis(
        property_id=request.property_id,
        property_data=property_record,
        documents=docs
    )
    
    # Save to database
    existing_analysis = db.query(Analysis).filter(Analysis.property_id == request.property_id).first()
    if existing_analysis:
        # Update existing
        existing_analysis.legal_analysis = analysis_result.get("legal")
        existing_analysis.physical_analysis = analysis_result.get("physical")
        existing_analysis.financial_analysis = analysis_result.get("financial")
        existing_analysis.sweat_equity = analysis_result.get("sweat_equity")
        existing_analysis.specialized = analysis_result.get("specialized")
        existing_analysis.summary = analysis_result.get("summary")
        existing_analysis.overall_risk = analysis_result.get("overall_risk")
        existing_analysis.recommendation = analysis_result.get("recommendation")
        existing_analysis.updated_at = datetime.utcnow()
    else:
        # Create new
        new_analysis = Analysis(
            property_id=request.property_id,
            legal_analysis=analysis_result.get("legal"),
            physical_analysis=analysis_result.get("physical"),
            financial_analysis=analysis_result.get("financial"),
            sweat_equity=analysis_result.get("sweat_equity"),
            specialized=analysis_result.get("specialized"),
            summary=analysis_result.get("summary"),
            overall_risk=analysis_result.get("overall_risk"),
            recommendation=analysis_result.get("recommendation")
        )
        db.add(new_analysis)
    
    db.commit()
    
    return FullAnalysisResponse(
        property_id=request.property_id,
        timestamp=datetime.utcnow(),
        street_level=property_record.street_level_analysis,
        legal=analysis_result.get("legal"),
        physical=analysis_result.get("physical"),
        financial=analysis_result.get("financial"),
        sweat_equity=analysis_result.get("sweat_equity"),
        specialized=analysis_result.get("specialized"),
        summary=analysis_result.get("summary")
    )


@app.get("/api/analysis/{property_id}", response_model=FullAnalysisResponse)
async def get_analysis(property_id: str, db: Session = Depends(get_db)):
    """Get cached analysis for a property."""
    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")
    
    analysis = db.query(Analysis).filter(Analysis.property_id == property_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found. Run analysis first.")
    
    return FullAnalysisResponse(
        property_id=property_id,
        timestamp=analysis.updated_at or analysis.created_at,
        street_level=property_record.street_level_analysis,
        legal=analysis.legal_analysis,
        physical=analysis.physical_analysis,
        financial=analysis.financial_analysis,
        sweat_equity=analysis.sweat_equity,
        specialized=analysis.specialized,
        summary=analysis.summary
    )


@app.post("/api/analysis/{property_id}/report")
async def generate_report(property_id: str, db: Session = Depends(get_db)):
    """Generate PDF executive report."""
    from services.reports.executive import generate_executive_report
    
    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")
    
    analysis = db.query(Analysis).filter(Analysis.property_id == property_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Generate PDF
    pdf_path = await generate_executive_report(
        property_data=property_record,
        analysis=analysis
    )
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"pathway-report-{property_id[:8]}.pdf"
    )


# === MAP ENDPOINTS ===

@app.get("/api/property/{property_id}/map-layers")
async def get_map_layers(property_id: str, db: Session = Depends(get_db)):
    """Get GeoJSON layers for map visualization."""
    from services.gatekeeper.map_layers import generate_map_layers

    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")

    layers = await generate_map_layers(
        address=property_record.address,
        street_level=property_record.street_level_analysis
    )

    return layers


# === DUE DILIGENCE ENDPOINTS ===

@app.post("/api/due-diligence/stamp-duty")
async def calculate_stamp_duty(
    purchase_price: float,
    property_type: str = "house",
    is_first_home_buyer: bool = False,
    is_foreign_purchaser: bool = False,
    is_pensioner: bool = False,
    is_off_the_plan: bool = False
):
    """
    Calculate Victorian stamp duty for a property purchase.

    Returns duty amount, applicable concessions, and total acquisition costs.
    """
    from services.due_diligence import VictorianStampDutyCalculator
    from services.due_diligence.stamp_duty import PurchaserStatus

    calculator = VictorianStampDutyCalculator()

    # Map foreign purchaser flag to purchaser status
    purchaser_status = PurchaserStatus.FOREIGN if is_foreign_purchaser else PurchaserStatus.CITIZEN

    result = calculator.calculate(
        purchase_price=purchase_price,
        first_home_buyer=is_first_home_buyer,
        purchaser_status=purchaser_status,
        principal_residence=is_first_home_buyer or is_pensioner,  # Assume PPR for concessions
        pensioner=is_pensioner,
        off_the_plan=is_off_the_plan
    )

    # Also calculate total acquisition costs
    total_costs = calculator.estimate_total_acquisition_costs(
        purchase_price=purchase_price,
        purchaser_status=purchaser_status,
        first_home_buyer=is_first_home_buyer,
        is_investment=False
    )

    return {
        "stamp_duty": result.to_dict(),
        "acquisition_costs": total_costs
    }


@app.post("/api/due-diligence/cooling-off")
async def calculate_cooling_off(
    contract_signed_date: str,
    purchase_price: float,
    purchase_method: str = "private_sale",
    purchaser_type: str = "individual",
    is_auction: bool = False
):
    """
    Calculate cooling-off period deadline and penalty.

    Args:
        contract_signed_date: Date in YYYY-MM-DD format
        purchase_price: Purchase price in dollars
        purchase_method: private_sale, auction, pre_auction, post_auction
        purchaser_type: individual, corporation, trust, smsf
        is_auction: Shorthand for purchase_method=auction
    """
    from datetime import date as date_type
    from services.due_diligence import CoolingOffCalculator
    from services.due_diligence.cooling_off import PurchaseMethod, PurchaserType

    try:
        signed_date = date_type.fromisoformat(contract_signed_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Map string to enum
    method_map = {
        "private_sale": PurchaseMethod.PRIVATE_SALE,
        "auction": PurchaseMethod.AUCTION,
        "pre_auction": PurchaseMethod.PRE_AUCTION,
        "post_auction": PurchaseMethod.POST_AUCTION
    }
    purchaser_map = {
        "individual": PurchaserType.INDIVIDUAL,
        "corporation": PurchaserType.CORPORATION,
        "trust": PurchaserType.TRUST,
        "smsf": PurchaserType.SMSF
    }

    method = PurchaseMethod.AUCTION if is_auction else method_map.get(purchase_method, PurchaseMethod.PRIVATE_SALE)
    purchaser = purchaser_map.get(purchaser_type, PurchaserType.INDIVIDUAL)

    calculator = CoolingOffCalculator()
    result = calculator.calculate_cooling_off(
        contract_signed_date=signed_date,
        purchase_price=purchase_price,
        purchase_method=method,
        purchaser_type=purchaser
    )

    # Get key dates
    key_dates = calculator.get_key_dates(
        contract_signed_date=signed_date,
        settlement_days=30
    )

    return {
        "cooling_off": result.to_dict(),
        "key_dates": key_dates
    }


@app.post("/api/due-diligence/timeline")
async def create_timeline(
    contract_signed_date: str,
    settlement_date: str,
    cooling_off_expires: Optional[str] = None,
    property_type: str = "house",
    is_investment: bool = False,
    special_conditions: Optional[List[dict]] = None
):
    """
    Create a due diligence timeline with all key dates and tasks.

    Returns critical deadlines, recommended actions, and delegated tasks.
    """
    from datetime import date as date_type
    from services.due_diligence import DueDiligenceTimeline

    try:
        signed = date_type.fromisoformat(contract_signed_date)
        settlement = date_type.fromisoformat(settlement_date)
        cooling_off = date_type.fromisoformat(cooling_off_expires) if cooling_off_expires else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    timeline = DueDiligenceTimeline()
    result = timeline.create_timeline(
        contract_signed_date=signed,
        cooling_off_expires=cooling_off,
        settlement_date=settlement,
        special_conditions=special_conditions or [],
        property_type=property_type,
        is_investment=is_investment
    )

    return result.to_dict()


@app.post("/api/due-diligence/specialist-referrals")
async def get_specialist_referrals(
    building_year: int,
    property_type: str = "house",
    overlays: Optional[List[str]] = None,
    building_inspection_findings: Optional[List[str]] = None,
    planned_works: Optional[List[str]] = None,
    has_pool: bool = False,
    is_investment: bool = False
):
    """
    Determine which specialist reports are recommended based on property characteristics.

    Returns categorized referrals with urgency levels and cost estimates.
    """
    from services.due_diligence import SpecialistReferralEngine

    engine = SpecialistReferralEngine()
    result = engine.analyze(
        property_data={
            "building_year": building_year,
            "property_type": property_type,
            "overlays": overlays or [],
            "has_pool": has_pool
        },
        building_inspection={"findings": building_inspection_findings or []},
        planned_works=planned_works,
        is_investment=is_investment
    )

    return result.to_dict()


@app.post("/api/due-diligence/risk-score")
async def calculate_risk_score(
    property_id: str,
    db: Session = Depends(get_db)
):
    """
    Calculate weighted risk score for a property based on all analysis results.

    Requires analysis to have been run first.
    """
    from services.due_diligence import PropertyRiskScorer

    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")

    analysis = db.query(Analysis).filter(Analysis.property_id == property_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found. Run analysis first.")

    scorer = PropertyRiskScorer()
    result = scorer.calculate_risk_score(
        legal_analysis=analysis.legal_analysis or {},
        title_analysis={},
        planning_analysis={},
        strata_analysis={},
        environmental_analysis={},
        financial_analysis=analysis.financial_analysis or {},
        physical_analysis=analysis.physical_analysis or {}
    )

    return result.to_dict()


@app.post("/api/due-diligence/cash-flow")
async def calculate_cash_flow(
    purchase_price: float,
    weekly_rent: float,
    deposit_percent: float = 20.0,
    interest_rate: float = 6.5,
    council_rates: float = 2400,
    water_rates: float = 800,
    strata_levies: float = 0,
    insurance: float = 1800,
    property_management_percent: float = 7.5,
    vacancy_rate: float = 3.0,
    maintenance_percent: float = 1.0,
    building_year: int = 2000
):
    """
    Calculate investor cash flow model for a rental property.

    Returns detailed breakdown of income, expenses, tax benefits, and net position.
    """
    from services.due_diligence import InvestorCashFlowModel

    model = InvestorCashFlowModel()
    result = model.calculate(
        purchase_price=purchase_price,
        weekly_rent=weekly_rent,
        outgoings={
            "council_rates": council_rates,
            "water_rates": water_rates,
            "strata_levies": strata_levies,
            "insurance": insurance,
            "building_year": building_year
        },
        finance_params={
            "deposit_percent": deposit_percent,
            "interest_rate": interest_rate / 100,  # Convert to decimal
            "loan_term_years": 30
        },
        investor_params={
            "property_management_percent": property_management_percent,
            "vacancy_rate_percent": vacancy_rate,
            "maintenance_percent": maintenance_percent,
            "marginal_tax_rate": 0.37  # Default to 37% bracket
        }
    )

    return result.to_dict()


@app.get("/api/due-diligence/{property_id}/compliance")
async def get_compliance_status(
    property_id: str,
    db: Session = Depends(get_db)
):
    """
    Get due diligence compliance status against CAV checklist.

    Shows which checklist items are complete, pending, or not applicable.
    """
    from services.due_diligence import DueDiligenceComplianceTracker

    property_record = db.query(Property).filter(Property.id == property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")

    # Get documents for this property
    docs = db.query(Document).filter(Document.property_id == property_id).all()
    doc_types = [d.document_type for d in docs if d.status == "ready"]

    # Get analysis if available
    analysis = db.query(Analysis).filter(Analysis.property_id == property_id).first()

    # Determine property type
    listing = property_record.listing_data or {}
    property_type = listing.get("property_type", "house").lower()

    tracker = DueDiligenceComplianceTracker()
    result = tracker.get_completion_status({
        "title_searched": "Section 32 Vendor Statement (VIC)" in doc_types,
        "section32_reviewed": analysis is not None,
        "building_inspection": "Building Inspection Report" in doc_types,
        "pest_inspection": "Pest & Termite Inspection Report" in doc_types,
        "strata_searched": "Strata Report / OC Certificate" in doc_types,
        "finance_approved": False,
        "property_type": property_type
    })

    return result


# === RUN SERVER ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

