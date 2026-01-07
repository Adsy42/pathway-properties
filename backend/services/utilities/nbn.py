"""
NBN (National Broadband Network) availability checker.

Uses the nbnpy library or direct API calls to check NBN availability.
Note: This uses an unofficial API - may require maintenance if NBN changes their systems.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum
import httpx


class NBNTechnology(str, Enum):
    """NBN technology types."""
    FTTP = "FTTP"  # Fibre to the Premises (best)
    FTTC = "FTTC"  # Fibre to the Curb (very good)
    HFC = "HFC"    # Hybrid Fibre-Coaxial (good)
    FTTN = "FTTN"  # Fibre to the Node (variable)
    FTTB = "FTTB"  # Fibre to the Building
    FIXED_WIRELESS = "Fixed Wireless"
    SATELLITE = "Satellite"
    UNKNOWN = "Unknown"


class NBNStatus(BaseModel):
    """NBN availability status for an address."""
    available: bool = False
    technology: NBNTechnology = NBNTechnology.UNKNOWN
    address_match: Optional[str] = None
    location_id: Optional[str] = None
    service_status: str = "unknown"  # available, in_progress, not_available
    max_download_speed: Optional[int] = None  # Mbps
    max_upload_speed: Optional[int] = None  # Mbps
    estimated_ready_date: Optional[str] = None
    quality_rating: str = "unknown"  # excellent, good, fair, poor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "technology": self.technology.value,
            "address_match": self.address_match,
            "location_id": self.location_id,
            "service_status": self.service_status,
            "max_download_speed": self.max_download_speed,
            "max_upload_speed": self.max_upload_speed,
            "estimated_ready_date": self.estimated_ready_date,
            "quality_rating": self.quality_rating
        }


# Technology speed and quality ratings
TECHNOLOGY_RATINGS = {
    NBNTechnology.FTTP: {
        "quality": "excellent",
        "max_download": 1000,
        "max_upload": 400,
        "description": "Fibre to the Premises - fastest and most reliable"
    },
    NBNTechnology.FTTC: {
        "quality": "excellent",
        "max_download": 250,
        "max_upload": 25,
        "description": "Fibre to the Curb - very fast, short copper run"
    },
    NBNTechnology.HFC: {
        "quality": "good",
        "max_download": 250,
        "max_upload": 25,
        "description": "Hybrid Fibre-Coaxial - good speeds, shared bandwidth"
    },
    NBNTechnology.FTTB: {
        "quality": "good",
        "max_download": 100,
        "max_upload": 40,
        "description": "Fibre to the Building - good for apartments"
    },
    NBNTechnology.FTTN: {
        "quality": "fair",
        "max_download": 100,
        "max_upload": 40,
        "description": "Fibre to the Node - speed depends on distance"
    },
    NBNTechnology.FIXED_WIRELESS: {
        "quality": "fair",
        "max_download": 75,
        "max_upload": 10,
        "description": "Fixed Wireless - good for regional areas"
    },
    NBNTechnology.SATELLITE: {
        "quality": "poor",
        "max_download": 25,
        "max_upload": 5,
        "description": "Satellite - high latency, remote areas only"
    }
}


async def check_nbn_availability(address: str) -> NBNStatus:
    """
    Check NBN availability for an address.

    Uses NBN Co's unofficial address lookup API.

    Args:
        address: Full street address

    Returns:
        NBNStatus with technology type and availability details
    """
    # NBN address lookup endpoint (unofficial)
    # This endpoint may change - monitor for updates
    LOOKUP_URL = "https://places.nbnco.net.au/places/v2/details/"
    SEARCH_URL = "https://places.nbnco.net.au/places/v1/autocomplete"

    try:
        async with httpx.AsyncClient() as client:
            # First, search for the address to get location ID
            search_response = await client.get(
                SEARCH_URL,
                params={"query": address},
                headers={
                    "Referer": "https://www.nbnco.com.au/",
                    "User-Agent": "Mozilla/5.0"
                },
                timeout=10.0
            )

            if search_response.status_code != 200:
                return _get_mock_nbn_status(address)

            search_data = search_response.json()
            suggestions = search_data.get("suggestions", [])

            if not suggestions:
                return NBNStatus(
                    available=False,
                    service_status="not_found",
                    quality_rating="unknown"
                )

            # Get the first matching address
            location_id = suggestions[0].get("id")
            matched_address = suggestions[0].get("formattedAddress")

            if not location_id:
                return _get_mock_nbn_status(address)

            # Get detailed information for this location
            details_response = await client.get(
                f"{LOOKUP_URL}{location_id}",
                headers={
                    "Referer": "https://www.nbnco.com.au/",
                    "User-Agent": "Mozilla/5.0"
                },
                timeout=10.0
            )

            if details_response.status_code != 200:
                return _get_mock_nbn_status(address)

            details = details_response.json()
            address_detail = details.get("addressDetail", {})

            # Parse technology type
            tech_type = address_detail.get("techType", "").upper()
            technology = _parse_technology(tech_type)

            # Get service status
            service_status = address_detail.get("serviceStatus", "").lower()
            is_available = service_status in ["available", "serviceable"]

            # Get technology-specific ratings
            tech_info = TECHNOLOGY_RATINGS.get(technology, {})

            return NBNStatus(
                available=is_available,
                technology=technology,
                address_match=matched_address,
                location_id=location_id,
                service_status="available" if is_available else service_status,
                max_download_speed=tech_info.get("max_download"),
                max_upload_speed=tech_info.get("max_upload"),
                estimated_ready_date=address_detail.get("targetEligibilityQuarter"),
                quality_rating=tech_info.get("quality", "unknown")
            )

    except httpx.TimeoutException:
        print("NBN lookup timed out")
        return _get_mock_nbn_status(address)
    except Exception as e:
        print(f"NBN lookup failed: {e}")
        return _get_mock_nbn_status(address)


def _parse_technology(tech_type: str) -> NBNTechnology:
    """Parse NBN technology type string to enum."""
    tech_map = {
        "FTTP": NBNTechnology.FTTP,
        "FIBRE": NBNTechnology.FTTP,
        "FTTC": NBNTechnology.FTTC,
        "HFC": NBNTechnology.HFC,
        "FTTN": NBNTechnology.FTTN,
        "FTTB": NBNTechnology.FTTB,
        "FW": NBNTechnology.FIXED_WIRELESS,
        "FIXED WIRELESS": NBNTechnology.FIXED_WIRELESS,
        "WIRELESS": NBNTechnology.FIXED_WIRELESS,
        "SAT": NBNTechnology.SATELLITE,
        "SATELLITE": NBNTechnology.SATELLITE
    }

    return tech_map.get(tech_type.upper(), NBNTechnology.UNKNOWN)


def _get_mock_nbn_status(address: str) -> NBNStatus:
    """Return mock NBN status based on address characteristics."""
    address_lower = address.lower()

    # Simulate different technologies based on suburb keywords
    if any(s in address_lower for s in ["cbd", "melbourne", "southbank", "docklands"]):
        technology = NBNTechnology.FTTP
    elif any(s in address_lower for s in ["richmond", "fitzroy", "carlton", "brunswick"]):
        technology = NBNTechnology.FTTC
    elif any(s in address_lower for s in ["box hill", "glen waverley", "doncaster"]):
        technology = NBNTechnology.HFC
    elif any(s in address_lower for s in ["werribee", "craigieburn", "tarneit"]):
        technology = NBNTechnology.FTTN
    else:
        # Default to FTTN for unknown suburbs
        technology = NBNTechnology.FTTN

    tech_info = TECHNOLOGY_RATINGS.get(technology, {})

    return NBNStatus(
        available=True,
        technology=technology,
        address_match=f"[Mock] {address}",
        location_id="mock_location",
        service_status="available",
        max_download_speed=tech_info.get("max_download"),
        max_upload_speed=tech_info.get("max_upload"),
        quality_rating=tech_info.get("quality", "fair")
    )


def get_nbn_quality_description(status: NBNStatus) -> str:
    """Get human-readable description of NBN quality."""
    if not status.available:
        return "NBN not yet available at this address"

    tech_info = TECHNOLOGY_RATINGS.get(status.technology, {})
    description = tech_info.get("description", "Unknown technology type")

    if status.quality_rating == "excellent":
        return f"{description}. Excellent for working from home, streaming, and smart home devices."
    elif status.quality_rating == "good":
        return f"{description}. Good for most household needs including streaming and video calls."
    elif status.quality_rating == "fair":
        return f"{description}. Adequate for general use but may struggle with multiple high-bandwidth activities."
    else:
        return f"{description}. Limited capability - consider 4G/5G alternatives."
