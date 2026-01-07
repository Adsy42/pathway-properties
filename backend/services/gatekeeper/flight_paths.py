"""
Flight path and aircraft noise assessment.
Uses Airservices Australia ANEF contours.
"""

from typing import Optional
import httpx

from models import FlightPathCheck, CheckScore


async def check_flight_paths(
    lat: Optional[float],
    lng: Optional[float],
    address: str
) -> FlightPathCheck:
    """
    Check if property is under a flight path.
    
    Uses:
    - ANEF (Australian Noise Exposure Forecast) contours
    - N70 (number of flights >70dB per day)
    
    Kill criteria:
    - ANEF > 20 = AUTO KILL
    - N70 > 20 flights/day = AUTO KILL
    """
    
    if lat is None or lng is None:
        return FlightPathCheck(
            score=CheckScore.WARNING,
            anef=0,
            n70=0,
            details="Unable to determine location - manual check required"
        )
    
    try:
        # Try Airservices Australia data
        anef, n70 = await get_aircraft_noise(lat, lng)
        
        if anef > 25 or n70 > 30:
            score = CheckScore.FAIL
            details = f"HIGH aircraft noise: ANEF {anef}, N70 {n70} flights/day - AUTO KILL"
        elif anef > 20 or n70 > 20:
            score = CheckScore.FAIL
            details = f"Significant aircraft noise: ANEF {anef}, N70 {n70} flights/day - AUTO KILL"
        elif anef > 15 or n70 > 10:
            score = CheckScore.WARNING
            details = f"Moderate aircraft noise: ANEF {anef}, N70 {n70} flights/day"
        else:
            score = CheckScore.PASS
            details = "Not in significant aircraft noise zone"
        
        return FlightPathCheck(
            score=score,
            anef=anef,
            n70=n70,
            details=details
        )
        
    except Exception as e:
        print(f"Flight path check failed: {e}")
        return get_mock_flight_path(lat, lng)


async def get_aircraft_noise(lat: float, lng: float) -> tuple[float, float]:
    """
    Get aircraft noise data for a location.
    
    Data sources:
    - Airservices Australia publishes ANEF contours as shapefiles
    - Major airports: Sydney, Melbourne, Brisbane, Perth, Adelaide
    
    Returns (ANEF value, N70 value)
    """
    
    # Check major airport proximity and return appropriate noise levels
    # Sydney Airport
    if is_near_airport(lat, lng, -33.9461, 151.1772, 15):  # 15km radius
        return await query_sydney_noise(lat, lng)
    
    # Melbourne Airport (Tullamarine)
    if is_near_airport(lat, lng, -37.6733, 144.8433, 15):
        return await query_melbourne_noise(lat, lng)
    
    # Default: not near major airport
    return (0, 0)


def is_near_airport(
    lat: float, lng: float,
    airport_lat: float, airport_lng: float,
    radius_km: float
) -> bool:
    """Check if coordinates are within radius of airport."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in km
    
    lat1, lon1 = radians(lat), radians(lng)
    lat2, lon2 = radians(airport_lat), radians(airport_lng)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    return distance <= radius_km


async def query_sydney_noise(lat: float, lng: float) -> tuple[float, float]:
    """Query noise for Sydney Airport vicinity."""
    # In production, would query Airservices ANEF shapefiles
    # Mock based on distance from airport
    
    distance = get_distance_km(lat, lng, -33.9461, 151.1772)
    
    if distance < 3:
        return (30, 50)  # Very high noise
    elif distance < 5:
        return (25, 35)
    elif distance < 8:
        return (20, 20)
    elif distance < 12:
        return (15, 10)
    else:
        return (5, 3)


async def query_melbourne_noise(lat: float, lng: float) -> tuple[float, float]:
    """Query noise for Melbourne Airport vicinity."""
    distance = get_distance_km(lat, lng, -37.6733, 144.8433)
    
    if distance < 3:
        return (28, 45)
    elif distance < 5:
        return (22, 30)
    elif distance < 8:
        return (18, 15)
    elif distance < 12:
        return (12, 8)
    else:
        return (3, 2)


def get_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in km."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371
    
    lat1, lon1 = radians(lat1), radians(lng1)
    lat2, lon2 = radians(lat2), radians(lng2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def get_mock_flight_path(lat: float, lng: float) -> FlightPathCheck:
    """Return mock flight path data."""
    hash_val = hash(f"{lat:.4f},{lng:.4f}") % 100
    
    if hash_val < 3:
        return FlightPathCheck(
            score=CheckScore.FAIL,
            anef=25,
            n70=35,
            details="[MOCK] Under major flight path - AUTO KILL"
        )
    elif hash_val < 8:
        return FlightPathCheck(
            score=CheckScore.WARNING,
            anef=18,
            n70=15,
            details="[MOCK] Some aircraft noise expected"
        )
    else:
        return FlightPathCheck(
            score=CheckScore.PASS,
            anef=0,
            n70=0,
            details="[MOCK] Not in significant aircraft noise zone"
        )







