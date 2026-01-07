"""
Configuration management for Pathway Property Backend.
Loads environment variables and provides typed settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # === DATABASE ===
    database_url: str = Field(default="sqlite:///./pathway.db")
    
    # === FILE STORAGE ===
    upload_dir: str = Field(default="./uploads")
    cache_dir: str = Field(default="./cache")
    
    # === PROPERTY DATA APIs ===
    corelogic_client_id: Optional[str] = Field(default=None)
    corelogic_client_secret: Optional[str] = Field(default=None)
    corelogic_base_url: Optional[str] = Field(default=None)  # Override auto-detection if set
    corelogic_use_sandbox: bool = Field(default=True)  # Use sandbox by default for safety
    
    geoscape_consumer_key: Optional[str] = Field(default=None)
    geoscape_consumer_secret: Optional[str] = Field(default=None)
    geoscape_base_url: str = Field(default="https://api.psma.com.au/v1")
    
    # === AI SERVICES ===
    azure_document_intelligence_endpoint: Optional[str] = Field(default=None)
    azure_document_intelligence_key: Optional[str] = Field(default=None)
    
    # OpenAI for LLM reasoning and embeddings
    openai_api_key: Optional[str] = Field(default=None)
    
    # Isaacus Legal AI - for legal document classification with IQL
    isaacus_api_key: Optional[str] = Field(default=None)
    isaacus_base_url: str = Field(default="https://api.isaacus.com")
    
    # === VECTOR DB ===
    vector_db: str = Field(default="chroma")
    chroma_persist_dir: str = Field(default="./chroma_data")
    pinecone_api_key: Optional[str] = Field(default=None)
    pinecone_index_name: str = Field(default="pathway-properties")
    
    # === MAPS ===
    mapbox_token: Optional[str] = Field(default=None)

    # === DOMAIN API (Property Listings) ===
    domain_client_id: Optional[str] = Field(default=None)
    domain_client_secret: Optional[str] = Field(default=None)
    domain_base_url: str = Field(default="https://api.domain.com.au")

    # === HERITAGE VICTORIA ===
    # VHD (Victorian Heritage Database) - no key required for public API
    heritage_vic_base_url: str = Field(default="https://vhd.heritagecouncil.vic.gov.au")

    # === CRIME STATISTICS AGENCY VIC ===
    # Public data - no key required
    csa_vic_base_url: str = Field(default="https://www.crimestatistics.vic.gov.au")

    # === NBN CO ===
    # Public rollout check - no key required
    nbn_base_url: str = Field(default="https://places.nbnco.net.au")

    # === EPA VICTORIA ===
    # Priority Sites Register - no key required
    epa_vic_base_url: str = Field(default="https://portal.epa.vic.gov.au")

    # === GEOVIC (Mining Tenements) ===
    # Public WFS - no key required
    geovic_wfs_url: str = Field(default="https://geology.data.vic.gov.au/geoserver/wfs")

    # === PTV (Public Transport Victoria) ===
    ptv_developer_id: Optional[str] = Field(default=None)
    ptv_api_key: Optional[str] = Field(default=None)
    ptv_base_url: str = Field(default="https://timetableapi.ptv.vic.gov.au")

    # === VICPLAN (Planning Scheme) ===
    # Public WFS - no key required
    vicplan_wfs_url: str = Field(default="https://opendata.maps.vic.gov.au/geoserver/wfs")

    # === ANALYSIS BEHAVIOR ===
    # If True, continue full analysis even when kill criteria are triggered
    ignore_kill_criteria: bool = Field(default=False)

    # === SERVICE TOGGLES ===
    # Enable/disable individual services for testing
    use_mock_domain: bool = Field(default=True)
    use_mock_heritage: bool = Field(default=True)
    use_mock_crime: bool = Field(default=True)
    use_mock_nbn: bool = Field(default=True)
    use_mock_epa: bool = Field(default=True)
    use_mock_mining: bool = Field(default=True)
    use_mock_schools: bool = Field(default=True)
    use_mock_transport: bool = Field(default=True)
    use_mock_demographics: bool = Field(default=True)

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

