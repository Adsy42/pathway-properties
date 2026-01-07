"""
Database setup and models for Pathway Property MVP.
Uses SQLite for local development, easily swappable to PostgreSQL.
"""

from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

from config import get_settings

settings = get_settings()

# Create engine - SQLite for local, PostgreSQL for production
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_uuid() -> str:
    """Generate a unique ID for records."""
    return str(uuid.uuid4())


class Property(Base):
    """Property record with listing data and analysis results."""
    __tablename__ = "properties"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    url = Column(String(500), nullable=False)
    address = Column(String(500), nullable=True)
    state = Column(String(10), nullable=True)  # VIC, NSW, QLD, etc.
    
    # Raw data from APIs
    listing_data = Column(JSON, nullable=True)  # Domain/scraper data
    corelogic_data = Column(JSON, nullable=True)  # CoreLogic enrichment
    
    # Street level analysis
    street_level_analysis = Column(JSON, nullable=True)
    verdict = Column(String(20), nullable=True)  # PROCEED, REVIEW, REJECT
    kill_reasons = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="property", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="property", uselist=False, cascade="all, delete-orphan")


class Document(Base):
    """Uploaded document with OCR results."""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    property_id = Column(String(36), ForeignKey("properties.id"), nullable=False)
    
    document_type = Column(String(50), nullable=False)  # SECTION_32, PEST_REPORT, etc.
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    
    # Processing status
    status = Column(String(20), default="pending")  # pending, processing, ready, error
    page_count = Column(Integer, nullable=True)
    
    # OCR results
    ocr_result = Column(JSON, nullable=True)  # Structured text from Azure
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    property = relationship("Property", back_populates="documents")


class Analysis(Base):
    """Full asset-level analysis results."""
    __tablename__ = "analyses"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    property_id = Column(String(36), ForeignKey("properties.id"), nullable=False, unique=True)
    
    # Analysis sections (stored as JSON)
    legal_analysis = Column(JSON, nullable=True)
    physical_analysis = Column(JSON, nullable=True)
    financial_analysis = Column(JSON, nullable=True)
    sweat_equity = Column(JSON, nullable=True)
    specialized = Column(JSON, nullable=True)
    
    # Summary
    summary = Column(JSON, nullable=True)
    overall_risk = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    recommendation = Column(String(30), nullable=True)  # STRONG_BUY, BUY, PROCEED_WITH_CAUTION, AVOID
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property = relationship("Property", back_populates="analysis")


class APICache(Base):
    """Cache for external API responses to reduce costs."""
    __tablename__ = "api_cache"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    cache_key = Column(String(255), unique=True, nullable=False)  # e.g., "corelogic:123-smith-st"
    provider = Column(String(50), nullable=False)  # corelogic, geoscape, domain, etc.
    response_data = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()







