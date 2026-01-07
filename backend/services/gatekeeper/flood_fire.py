"""
Flood and bushfire risk assessment.
Uses Geoscape API for building-level risk data.
"""

from typing import Optional, Tuple, Dict, Any
import httpx

from config import get_settings
from models import FloodRiskCheck, BushfireRiskCheck, CheckScore

settings = get_settings()


async def check_flood_risk(
    lat: Optional[float],
    lng: Optional[float],
    address: str,
    state: str = "VIC"
) -> FloodRiskCheck:
    """
    Check flood risk at building level.
    
    Uses Geoscape Buildings API for 1% AEP (Annual Exceedance Probability) flood extent.
    This is the "1 in 100 year" flood level.
    
    Kill criteria:
    - Building intersects 1% AEP = AUTO KILL
    - In flood overlay but building on high ground = WARNING
    """
    
    if lat is None or lng is None:
        return FloodRiskCheck(
            score=CheckScore.WARNING,
            aep_1_percent=False,
            building_at_risk=False,
            source="unknown",
            details="Unable to determine location - manual check required"
        )
    
    # TODO: Geoscape API key is for old API version - disabled for now
    # Use VicPlan WFS for flood overlays (SBO, LSIO)
    # if settings.geoscape_consumer_key and settings.geoscape_consumer_secret:
    #     return await check_flood_geoscape(lat, lng, address)
    
    # Use state planning portal (VicPlan WFS)
    return await check_flood_state_wfs(lat, lng, state)


async def get_geoscape_token() -> str:
    """Get OAuth2 token from Geoscape using consumer key/secret."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.geoscape_base_url}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.geoscape_consumer_key,
                "client_secret": settings.geoscape_consumer_secret,
            },
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def check_flood_geoscape(lat: float, lng: float, address: str) -> FloodRiskCheck:
    """Check flood using Geoscape Buildings API."""
    try:
        token = await get_geoscape_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.geoscape_base_url}/buildings/v2/buildings",
                params={
                    "lat": lat,
                    "lon": lng,
                    "radius": 50  # 50m radius
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                building = data.get("buildings", [{}])[0] if data.get("buildings") else {}
                
                flood_risk = building.get("floodRisk", {})
                aep_1_percent = flood_risk.get("aep1Percent", False)
                at_risk = flood_risk.get("buildingAtRisk", False)
                
                if at_risk:
                    score = CheckScore.FAIL
                    details = "Building footprint intersects 1% AEP flood extent - AUTO KILL"
                elif aep_1_percent:
                    score = CheckScore.WARNING
                    details = "Property in flood zone but building may be on higher ground"
                else:
                    score = CheckScore.PASS
                    details = "Not in designated flood zone"
                
                return FloodRiskCheck(
                    score=score,
                    aep_1_percent=aep_1_percent,
                    building_at_risk=at_risk,
                    source="Geoscape Buildings",
                    details=details
                )
                
    except Exception as e:
        print(f"Geoscape flood check failed: {e}")
    
    # Return mock data
    return get_mock_flood_risk(lat, lng)


async def check_flood_state_wfs(lat: float, lng: float, state: str) -> FloodRiskCheck:
    """Check flood using state planning WFS (less accurate)."""
    
    # VIC: Special Building Overlay (SBO) and Land Subject to Inundation Overlay (LSIO)
    # NSW: Flood Planning Area in LEP
    
    try:
        if state == "VIC":
            return await check_flood_vicplan(lat, lng)
        elif state == "NSW":
            return await check_flood_nsw(lat, lng)
        else:
            return get_mock_flood_risk(lat, lng)
    except Exception as e:
        print(f"State WFS flood check failed: {e}")
        return get_mock_flood_risk(lat, lng)


async def check_flood_vicplan(lat: float, lng: float) -> FloodRiskCheck:
    """Check VIC flood overlays via VicPlan WFS."""
    try:
        async with httpx.AsyncClient() as client:
            # Query all overlays at location, then filter for flood-related ones
            # BBOX format: minX,minY,maxX,maxY (small buffer around point)
            buffer = 0.0001  # ~10m buffer
            response = await client.get(
                "https://opendata.maps.vic.gov.au/geoserver/ows",
                params={
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetFeature",
                    "typeName": "open-data-platform:plan_overlay",
                    "outputFormat": "application/json",
                    "bbox": f"{lng-buffer},{lat-buffer},{lng+buffer},{lat+buffer},EPSG:4326"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                
                # Filter for flood-related overlays: SBO, LSIO, FO (Floodway Overlay)
                all_overlays = [f.get("properties", {}).get("zone_code", "") for f in features]
                flood_overlays = [c for c in all_overlays if c and ("SBO" in c or "LSIO" in c or "FO" in c)]
                
                if flood_overlays:
                    is_sbo = any("SBO" in str(c) for c in flood_overlays)
                    is_lsio = any("LSIO" in str(c) for c in flood_overlays)
                    
                    return FloodRiskCheck(
                        score=CheckScore.FAIL if is_lsio else CheckScore.WARNING,
                        aep_1_percent=is_lsio,
                        building_at_risk=is_lsio,
                        source="VicPlan",
                        details=f"Flood overlays: {', '.join(flood_overlays)}"
                    )
                else:
                    return FloodRiskCheck(
                        score=CheckScore.PASS,
                        aep_1_percent=False,
                        building_at_risk=False,
                        source="VicPlan",
                        details="Not in SBO or LSIO overlay"
                    )
                    
    except Exception as e:
        print(f"VicPlan flood check failed: {e}")
    
    return get_mock_flood_risk(lat, lng)


async def check_flood_nsw(lat: float, lng: float) -> FloodRiskCheck:
    """Check NSW flood via ePlanning."""
    # NSW ePlanning Spatial Services
    # Would query Flood Planning Area layer
    return get_mock_flood_risk(lat, lng)


def get_mock_flood_risk(lat: float, lng: float) -> FloodRiskCheck:
    """Return mock flood risk for demo."""
    # Use coordinates to generate consistent mock data
    hash_val = hash(f"{lat:.4f},{lng:.4f}") % 100
    
    if hash_val < 5:
        return FloodRiskCheck(
            score=CheckScore.FAIL,
            aep_1_percent=True,
            building_at_risk=True,
            source="Mock",
            details="[MOCK] Building in 1% AEP flood extent"
        )
    elif hash_val < 15:
        return FloodRiskCheck(
            score=CheckScore.WARNING,
            aep_1_percent=True,
            building_at_risk=False,
            source="Mock",
            details="[MOCK] In flood overlay but building may be elevated"
        )
    else:
        return FloodRiskCheck(
            score=CheckScore.PASS,
            aep_1_percent=False,
            building_at_risk=False,
            source="Mock",
            details="[MOCK] Not in designated flood zone"
        )


async def check_bushfire_risk(
    lat: Optional[float],
    lng: Optional[float],
    address: str,
    state: str = "VIC"
) -> BushfireRiskCheck:
    """
    Check bushfire risk using BAL (Bushfire Attack Level) rating.
    
    BAL ratings:
    - BAL-LOW: Minimal risk
    - BAL-12.5: Low risk
    - BAL-19: Moderate risk
    - BAL-29: High risk
    - BAL-40: Very high risk
    - BAL-FZ: Flame Zone (extreme risk)
    
    Kill criteria:
    - BAL-40 or BAL-FZ = RED FLAG (significant cost buffer required)
    """
    
    if lat is None or lng is None:
        return BushfireRiskCheck(
            score=CheckScore.WARNING,
            bal_rating=None,
            details="Unable to determine location - manual check required"
        )
    
    # TODO: Geoscape API key is for old API version - disabled for now
    # Use VicPlan WFS for bushfire prone area
    # if settings.geoscape_consumer_key and settings.geoscape_consumer_secret:
    #     return await check_bushfire_geoscape(lat, lng)
    
    # Use state planning portal (VicPlan WFS)
    if state == "VIC":
        return await check_bushfire_vicplan(lat, lng)
    
    # Fallback to mock for other states
    return get_mock_bushfire_risk(lat, lng)


async def check_bushfire_geoscape(lat: float, lng: float) -> BushfireRiskCheck:
    """Check bushfire using Geoscape API."""
    try:
        token = await get_geoscape_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.geoscape_base_url}/buildings/v2/buildings",
                params={
                    "lat": lat,
                    "lon": lng,
                    "radius": 50
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                building = data.get("buildings", [{}])[0] if data.get("buildings") else {}
                
                bal = building.get("bushfireRisk", {}).get("balRating")
                
                if bal in ["BAL-40", "BAL-FZ"]:
                    score = CheckScore.FAIL
                    details = f"HIGH bushfire risk: {bal} - significant cost buffer required"
                elif bal in ["BAL-29"]:
                    score = CheckScore.WARNING
                    details = f"Moderate bushfire risk: {bal}"
                elif bal:
                    score = CheckScore.PASS
                    details = f"Low bushfire risk: {bal}"
                else:
                    score = CheckScore.PASS
                    details = "Not in designated bushfire zone"
                
                return BushfireRiskCheck(
                    score=score,
                    bal_rating=bal,
                    details=details
                )
                
    except Exception as e:
        print(f"Geoscape bushfire check failed: {e}")
    
    return get_mock_bushfire_risk(lat, lng)


async def check_bushfire_vicplan(lat: float, lng: float) -> BushfireRiskCheck:
    """Check VIC bushfire prone area via VicPlan WFS."""
    try:
        async with httpx.AsyncClient() as client:
            # Query for Bushfire Prone Area
            buffer = 0.0001  # ~10m buffer
            response = await client.get(
                "https://opendata.maps.vic.gov.au/geoserver/ows",
                params={
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetFeature",
                    "typeName": "open-data-platform:bushfire_prone_area",
                    "outputFormat": "application/json",
                    "count": "1",
                    "bbox": f"{lng-buffer},{lat-buffer},{lng+buffer},{lat+buffer},EPSG:4326"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                
                if features:
                    # Property is in Bushfire Prone Area
                    return BushfireRiskCheck(
                        score=CheckScore.WARNING,
                        bal_rating="BPA",  # Bushfire Prone Area (BAL assessment required)
                        details="In Bushfire Prone Area - BAL assessment may be required for building works"
                    )
                else:
                    return BushfireRiskCheck(
                        score=CheckScore.PASS,
                        bal_rating=None,
                        details="Not in designated Bushfire Prone Area"
                    )
                    
    except Exception as e:
        print(f"VicPlan bushfire check failed: {e}")
    
    return get_mock_bushfire_risk(lat, lng)


def get_mock_bushfire_risk(lat: float, lng: float) -> BushfireRiskCheck:
    """Return mock bushfire risk for demo."""
    hash_val = hash(f"{lat:.4f},{lng:.4f}") % 100
    
    if hash_val < 3:
        return BushfireRiskCheck(
            score=CheckScore.FAIL,
            bal_rating="BAL-40",
            details="[MOCK] Very high bushfire risk - cost buffer required"
        )
    elif hash_val < 10:
        return BushfireRiskCheck(
            score=CheckScore.WARNING,
            bal_rating="BAL-29",
            details="[MOCK] Moderate bushfire risk"
        )
    elif hash_val < 20:
        return BushfireRiskCheck(
            score=CheckScore.PASS,
            bal_rating="BAL-12.5",
            details="[MOCK] Low bushfire risk"
        )
    else:
        return BushfireRiskCheck(
            score=CheckScore.PASS,
            bal_rating=None,
            details="[MOCK] Not in designated bushfire zone"
        )

