"""
Zoning and planning overlay checks.
Uses VicPlan and NSW ePlanning APIs.
"""

from typing import Optional, List, Dict, Any
import httpx
import re

from config import get_settings
from models import ZoningCheck, CheckScore

settings = get_settings()


async def check_zoning(
    lat: Optional[float],
    lng: Optional[float],
    address: str,
    state: str = "VIC"
) -> ZoningCheck:
    """
    Check zoning and planning overlays for a property.
    
    Checks:
    - Zone code (GRZ1, R2, etc.)
    - Heritage Overlay (HO)
    - Design and Development Overlay (DDO)
    - Other overlays
    """
    
    if lat is None or lng is None:
        return ZoningCheck(
            score=CheckScore.WARNING,
            code="UNKNOWN",
            overlays=[],
            heritage_overlay=False,
            details="Unable to determine location - manual check required"
        )
    
    try:
        if state == "VIC":
            return await check_zoning_vicplan(lat, lng)
        elif state == "NSW":
            return await check_zoning_nsw(lat, lng)
        else:
            return get_mock_zoning(lat, lng, state)
    except Exception as e:
        print(f"Zoning check failed: {e}")
        return get_mock_zoning(lat, lng, state)


async def check_zoning_vicplan(lat: float, lng: float) -> ZoningCheck:
    """Check zoning via VicPlan API."""
    try:
        zone_code = None
        overlays = []
        heritage_overlay = False
        ddo_limits = None
        
        async with httpx.AsyncClient() as client:
            # Query zones via VicMap Open Data
            # BBOX format: minX,minY,maxX,maxY (small buffer around point)
            buffer = 0.0001  # ~10m buffer
            zone_response = await client.get(
                "https://opendata.maps.vic.gov.au/geoserver/ows",
                params={
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetFeature",
                    "typeName": "open-data-platform:plan_zone",
                    "outputFormat": "application/json",
                    "count": "1",
                    "bbox": f"{lng-buffer},{lat-buffer},{lng+buffer},{lat+buffer},EPSG:4326"
                },
                timeout=10.0
            )
            
            if zone_response.status_code == 200:
                data = zone_response.json()
                features = data.get("features", [])
                if features:
                    zone_code = features[0].get("properties", {}).get("zone_code", "UNKNOWN")
            
            # Query overlays via VicMap Open Data
            overlay_response = await client.get(
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
            
            if overlay_response.status_code == 200:
                data = overlay_response.json()
                features = data.get("features", [])
                for feature in features:
                    overlay_code = feature.get("properties", {}).get("zone_code", "")
                    if overlay_code:
                        overlays.append(overlay_code)
                        if overlay_code.startswith("HO"):
                            heritage_overlay = True
                        if overlay_code.startswith("DDO"):
                            ddo_limits = parse_ddo_limits(overlay_code)
        
        if not zone_code:
            return get_mock_zoning(lat, lng, "VIC")
        
        # Determine score
        score = CheckScore.PASS
        details_parts = [f"Zone: {zone_code}"]
        
        if heritage_overlay:
            score = CheckScore.WARNING
            details_parts.append("Heritage Overlay - restrictions on external alterations")
        
        if overlays:
            details_parts.append(f"Overlays: {', '.join(overlays)}")
        
        return ZoningCheck(
            score=score,
            code=zone_code,
            overlays=overlays,
            heritage_overlay=heritage_overlay,
            ddo_limits=ddo_limits,
            details=". ".join(details_parts)
        )
        
    except Exception as e:
        print(f"VicPlan zoning check failed: {e}")
        return get_mock_zoning(lat, lng, "VIC")


async def check_zoning_nsw(lat: float, lng: float) -> ZoningCheck:
    """Check zoning via NSW ePlanning."""
    try:
        async with httpx.AsyncClient() as client:
            # NSW ePlanning Spatial Services
            response = await client.get(
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Land_Zoning/MapServer/0/query",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "*",
                    "f": "json"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                
                if features:
                    attrs = features[0].get("attributes", {})
                    zone_code = attrs.get("SYM_CODE", "UNKNOWN")
                    zone_name = attrs.get("LAY_NAME", "")
                    
                    return ZoningCheck(
                        score=CheckScore.PASS,
                        code=zone_code,
                        overlays=[],
                        heritage_overlay=False,
                        details=f"Zone: {zone_code} ({zone_name})"
                    )
                    
    except Exception as e:
        print(f"NSW ePlanning zoning check failed: {e}")
    
    return get_mock_zoning(lat, lng, "NSW")


def parse_ddo_limits(ddo_code: str) -> Optional[Dict[str, Any]]:
    """
    Parse DDO (Design and Development Overlay) for height/setback limits.
    
    DDO schedules vary by council and require parsing the schedule document.
    For MVP, return generic limits.
    """
    # Extract DDO number
    match = re.search(r'DDO(\d+)', ddo_code)
    if match:
        ddo_num = int(match.group(1))
        # Mock limits based on DDO number
        return {
            "max_height": 9 + (ddo_num % 3) * 2,  # 9-13m typical
            "max_storeys": 2 + (ddo_num % 2),
            "setback_front": 4 + (ddo_num % 3)
        }
    return None


def get_mock_zoning(lat: float, lng: float, state: str) -> ZoningCheck:
    """Return mock zoning for demo."""
    hash_val = hash(f"{lat:.4f},{lng:.4f}") % 100
    
    if state == "VIC":
        zones = ["GRZ1", "GRZ2", "NRZ1", "RGZ1", "C1Z", "MUZ"]
    else:
        zones = ["R2", "R3", "R4", "B1", "B2", "E1"]
    
    zone_code = zones[hash_val % len(zones)]
    
    overlays = []
    heritage = False
    
    if hash_val < 20:
        overlays.append(f"HO{100 + hash_val}")
        heritage = True
    
    if hash_val < 30:
        overlays.append(f"DDO{1 + (hash_val % 10)}")
    
    score = CheckScore.WARNING if heritage else CheckScore.PASS
    
    return ZoningCheck(
        score=score,
        code=zone_code,
        overlays=overlays,
        heritage_overlay=heritage,
        ddo_limits={"max_height": 11, "max_storeys": 3} if "DDO" in str(overlays) else None,
        details=f"[MOCK] Zone: {zone_code}" + (f", Overlays: {', '.join(overlays)}" if overlays else "")
    )




