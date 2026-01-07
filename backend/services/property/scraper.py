"""
Property listing scraper for Domain and RealEstate.com.au.
Extracts property details from listing URLs.
"""

import re
import httpx
from typing import Dict, Any
from urllib.parse import urlparse
import json

async def scrape_property(url: str) -> Dict[str, Any]:
    """
    Scrape property details from a listing URL.
    
    Supports:
    - domain.com.au
    - realestate.com.au
    
    Returns standardized property data.
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if "domain.com.au" in domain:
        return await scrape_domain(url)
    elif "realestate.com.au" in domain:
        return await scrape_rea(url)
    else:
        raise ValueError(f"Unsupported property portal: {domain}")


async def scrape_domain(url: str) -> Dict[str, Any]:
    """Scrape property from Domain.com.au via HTML scraping."""
    return await scrape_domain_html(url)


async def scrape_domain_html(url: str) -> Dict[str, Any]:
    """HTML scraper for Domain.com.au."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        html = response.text
        
        # Extract JSON-LD data
        json_ld_match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            html,
            re.DOTALL
        )
        
        if json_ld_match:
            try:
                data = json.loads(json_ld_match.group(1))
                return parse_domain_jsonld(data, url)
            except json.JSONDecodeError:
                pass
        
        # Basic regex extraction as last resort
        return extract_domain_basic(html, url)


def parse_domain_jsonld(data: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Parse JSON-LD structured data from Domain page."""
    address = data.get("address", {})
    geo = data.get("geo", {})
    
    return {
        "source": "domain_scrape",
        "listing_id": None,
        "address": data.get("name", ""),
        "street": address.get("streetAddress", ""),
        "suburb": address.get("addressLocality", ""),
        "state": address.get("addressRegion", ""),
        "postcode": address.get("postalCode", ""),
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "bedrooms": data.get("numberOfRooms"),
        "bathrooms": None,
        "parking": None,
        "land_size": None,
        "property_type": data.get("@type", "").lower(),
        "price_display": None,
        "description": data.get("description", ""),
        "images": [data.get("image")] if data.get("image") else [],
        "floorplan_url": None,
        "agent": {},
        "raw_data": data
    }


def extract_domain_basic(html: str, url: str) -> Dict[str, Any]:
    """Basic regex extraction from Domain HTML."""
    # Extract address from title
    title_match = re.search(r'<title>(.*?)</title>', html)
    address = title_match.group(1).split("|")[0].strip() if title_match else ""
    
    # Extract beds/baths/cars
    beds_match = re.search(r'(\d+)\s*(?:bed|bedroom)', html, re.IGNORECASE)
    baths_match = re.search(r'(\d+)\s*(?:bath|bathroom)', html, re.IGNORECASE)
    cars_match = re.search(r'(\d+)\s*(?:car|parking|garage)', html, re.IGNORECASE)
    
    return {
        "source": "domain_scrape_basic",
        "listing_id": None,
        "address": address,
        "street": "",
        "suburb": "",
        "state": "",
        "postcode": "",
        "latitude": None,
        "longitude": None,
        "bedrooms": int(beds_match.group(1)) if beds_match else None,
        "bathrooms": int(baths_match.group(1)) if baths_match else None,
        "parking": int(cars_match.group(1)) if cars_match else None,
        "land_size": None,
        "property_type": "house",
        "price_display": None,
        "description": "",
        "images": [],
        "floorplan_url": None,
        "agent": {},
        "raw_data": {"url": url}
    }


async def scrape_rea(url: str) -> Dict[str, Any]:
    """Scrape property from RealEstate.com.au."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        html = response.text
        
        # REA embeds property data in a script tag
        data_match = re.search(
            r'window\.ArgonautExchange\s*=\s*({.*?});',
            html,
            re.DOTALL
        )
        
        if data_match:
            try:
                data = json.loads(data_match.group(1))
                return parse_rea_data(data, url)
            except json.JSONDecodeError:
                pass
        
        # Fallback to basic extraction
        return extract_rea_basic(html, url)


def parse_rea_data(data: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Parse REA ArgonautExchange data."""
    listing = data.get("details", {}).get("listing", {})
    address = listing.get("address", {})
    
    return {
        "source": "rea_scrape",
        "listing_id": listing.get("id"),
        "address": address.get("display", {}).get("fullAddress", ""),
        "street": address.get("streetAddress", ""),
        "suburb": address.get("suburb", ""),
        "state": address.get("state", ""),
        "postcode": address.get("postcode", ""),
        "latitude": address.get("location", {}).get("latitude"),
        "longitude": address.get("location", {}).get("longitude"),
        "bedrooms": listing.get("propertyType", {}).get("bedrooms"),
        "bathrooms": listing.get("propertyType", {}).get("bathrooms"),
        "parking": listing.get("propertyType", {}).get("carSpaces"),
        "land_size": listing.get("propertyType", {}).get("landSize"),
        "property_type": listing.get("propertyType", {}).get("propertyType", "").lower(),
        "price_display": listing.get("price", {}).get("display", ""),
        "description": listing.get("description", ""),
        "images": [img.get("uri") for img in listing.get("images", [])],
        "floorplan_url": next(
            (img.get("uri") for img in listing.get("images", []) if "floorplan" in img.get("type", "").lower()),
            None
        ),
        "agent": {
            "name": listing.get("agents", [{}])[0].get("name", "") if listing.get("agents") else "",
            "phone": listing.get("agents", [{}])[0].get("phone", "") if listing.get("agents") else "",
            "agency": listing.get("agency", {}).get("name", "")
        },
        "raw_data": listing
    }


def extract_rea_basic(html: str, url: str) -> Dict[str, Any]:
    """Basic regex extraction from REA HTML."""
    title_match = re.search(r'<title>(.*?)</title>', html)
    address = title_match.group(1).split("|")[0].strip() if title_match else ""
    
    return {
        "source": "rea_scrape_basic",
        "listing_id": None,
        "address": address,
        "street": "",
        "suburb": "",
        "state": "",
        "postcode": "",
        "latitude": None,
        "longitude": None,
        "bedrooms": None,
        "bathrooms": None,
        "parking": None,
        "land_size": None,
        "property_type": "house",
        "price_display": None,
        "description": "",
        "images": [],
        "floorplan_url": None,
        "agent": {},
        "raw_data": {"url": url}
    }


def detect_state_from_address(address: str) -> str:
    """Detect Australian state from address string."""
    address_upper = address.upper()
    
    states = {
        "VIC": ["VIC", "VICTORIA"],
        "NSW": ["NSW", "NEW SOUTH WALES"],
        "QLD": ["QLD", "QUEENSLAND"],
        "SA": ["SA", "SOUTH AUSTRALIA"],
        "WA": ["WA", "WESTERN AUSTRALIA"],
        "TAS": ["TAS", "TASMANIA"],
        "NT": ["NT", "NORTHERN TERRITORY"],
        "ACT": ["ACT", "AUSTRALIAN CAPITAL TERRITORY"]
    }
    
    for state_code, patterns in states.items():
        for pattern in patterns:
            if pattern in address_upper:
                return state_code
    
    return "VIC"  # Default to Victoria

