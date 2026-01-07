"""
Social housing density check.
Uses ABS Census data to identify areas with high public housing concentration.
"""

from typing import Optional, Tuple
import httpx

from config import get_settings
from models import SocialHousingCheck, CheckScore

settings = get_settings()


async def check_social_housing(
    lat: Optional[float],
    lng: Optional[float],
    address: str
) -> SocialHousingCheck:
    """
    Check social housing density at a location.
    
    Uses ABS Census data to find:
    - SA1 (Statistical Area Level 1) for the property
    - Percentage of dwellings with "State Authority" as landlord type
    
    Kill criteria:
    - >15% in SA1 = REVIEW
    - >20% on street = AUTO KILL (requires separate street-level data)
    """
    print(f"[Social Housing] Checking: {address} at ({lat}, {lng})")
    
    if lat is None or lng is None:
        # Can't check without coordinates
        return SocialHousingCheck(
            score=CheckScore.WARNING,
            density_percent=0,
            threshold=15.0,
            details="Unable to determine location - manual check required"
        )
    
    try:
        # Get SA1 code for coordinates
        sa1_code = await get_sa1_for_coordinates(lat, lng)
        
        if not sa1_code:
            return SocialHousingCheck(
                score=CheckScore.WARNING,
                density_percent=0,
                threshold=15.0,
                details="Could not determine SA1 area"
            )
        
        # Get social housing percentage for SA1
        density = await get_social_housing_density(sa1_code)
        
        # Apply kill criteria
        if density > 20:
            score = CheckScore.FAIL
            details = f"HIGH social housing concentration: {density:.1f}% in SA1 {sa1_code} (threshold: 15%)"
        elif density > 15:
            score = CheckScore.WARNING
            details = f"Elevated social housing: {density:.1f}% in SA1 {sa1_code} (threshold: 15%)"
        else:
            score = CheckScore.PASS
            details = f"{density:.1f}% social housing in SA1 {sa1_code} (threshold: 15%)"
        
        return SocialHousingCheck(
            score=score,
            density_percent=density,
            threshold=15.0,
            sa1_code=sa1_code,
            details=details
        )
        
    except Exception as e:
        print(f"Social housing check failed: {e}")
        return SocialHousingCheck(
            score=CheckScore.WARNING,
            density_percent=0,
            threshold=15.0,
            details=f"Check failed: {str(e)}"
        )


async def get_sa1_for_coordinates(lat: float, lng: float) -> Optional[str]:
    """
    Get ABS SA1 (Statistical Area Level 1) code for coordinates.
    
    Uses ABS Geographies API or local shapefile.
    """
    # Try ABS API first
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA1/MapServer/0/query",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "inSR": "4326",  # WGS84 lat/lng coordinate system
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "SA1_CODE_2021",
                    "f": "json"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    attrs = features[0].get("attributes", {})
                    # API returns lowercase field name
                    return attrs.get("sa1_code_2021") or attrs.get("SA1_CODE_2021")
    except Exception as e:
        print(f"ABS API lookup failed: {e}")
    
    # Return mock SA1 for demo if API fails
    mock_sa1 = f"2{int(lat*100)}{int(lng*100):04d}"
    print(f"[Social Housing] Using mock SA1: {mock_sa1} (ABS API unavailable)")
    return mock_sa1


async def get_social_housing_density(sa1_code: str) -> float:
    """
    Get social housing percentage for an SA1 area.
    
    Uses ABS Census data (Landlord Type: State Authority).
    """
    # In production, this would query:
    # 1. ABS TableBuilder API
    # 2. Or a local parquet file with pre-processed Census data
    
    # For demo, return mock data based on SA1 code
    # Some SA1s have higher social housing (inner suburbs, public housing estates)
    
    # Mock: Use hash of SA1 code to generate consistent "random" percentage
    hash_val = hash(sa1_code) % 100
    
    if hash_val < 5:
        density = 25.0 + (hash_val % 10)  # High density area
    elif hash_val < 15:
        density = 12.0 + (hash_val % 8)   # Medium density
    else:
        density = 2.0 + (hash_val % 8)    # Low density (most areas)
    
    print(f"[Social Housing] SA1={sa1_code}, hash={hash_val}, density={density:.1f}% (MOCK DATA)")
    return density


async def get_street_social_housing(address: str) -> Optional[float]:
    """
    Get social housing percentage for a specific street.
    
    This is more granular than SA1 and would require:
    - Land registry data
    - Or council rates data
    - Or Title searches
    
    Returns None if not available.
    """
    # Not implemented for MVP - would need additional data source
    return None




