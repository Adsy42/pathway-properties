"""
Property enrichment service.
Combines data from scraper, CoreLogic, and other sources.
"""

from typing import Dict, Any

from services.property.scraper import scrape_property, detect_state_from_address
from services.property.corelogic import enrich_with_corelogic
from models import PropertyDetails, CoreLogicData


async def enrich_property(url: str) -> Dict[str, Any]:
    """
    Fully enrich a property from URL.
    
    1. Scrape listing details
    2. Enrich with CoreLogic data
    3. Normalize to standard format
    """
    
    # Step 1: Scrape listing
    listing_data = await scrape_property(url)
    
    # Extract key fields
    address = listing_data.get("address", "")
    state = listing_data.get("state") or detect_state_from_address(address)
    bedrooms = listing_data.get("bedrooms")
    property_type = listing_data.get("property_type", "house")
    
    # Step 2: Enrich with CoreLogic
    corelogic_data = await enrich_with_corelogic(
        address=address,
        bedrooms=bedrooms,
        property_type=property_type
    )
    
    # Step 3: Build standardized response
    property_details = PropertyDetails(
        address=address,
        listing_price=listing_data.get("price_display"),
        bedrooms=bedrooms,
        bathrooms=listing_data.get("bathrooms"),
        parking=listing_data.get("parking"),
        land_size=listing_data.get("land_size"),
        property_type=property_type,
        images=listing_data.get("images", []),
        floorplan_url=listing_data.get("floorplan_url"),
        description=listing_data.get("description"),
        agent=listing_data.get("agent"),
        corelogic=CoreLogicData(
            avm=corelogic_data.get("avm"),
            avm_confidence=corelogic_data.get("avm_confidence"),
            last_sold_price=corelogic_data.get("last_sold_price"),
            last_sold_date=corelogic_data.get("last_sold_date"),
            rental_estimate=corelogic_data.get("rental_estimate"),
            gross_yield_estimate=corelogic_data.get("gross_yield_estimate"),
            comparable_sales=corelogic_data.get("comparable_sales")
        ) if corelogic_data else None
    )
    
    return {
        "address": address,
        "state": state,
        "latitude": listing_data.get("latitude"),
        "longitude": listing_data.get("longitude"),
        "listing": listing_data,
        "corelogic": corelogic_data,
        "property_details": property_details
    }







