"""
Domain API client for property listings and data.

Uses the official Domain API (developer.domain.com.au) instead of web scraping.
Free tier: 500 calls/day - sufficient for MVP.

API Documentation: https://developer.domain.com.au/docs/
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from pydantic import BaseModel

from config import get_settings

settings = get_settings()


class DomainProperty(BaseModel):
    """Domain property listing data."""
    listing_id: str
    address: str
    suburb: str
    state: str
    postcode: str
    property_type: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    parking: Optional[int] = None
    land_size: Optional[int] = None
    building_size: Optional[int] = None
    price_display: Optional[str] = None
    price_from: Optional[int] = None
    price_to: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    features: List[str] = []
    images: List[str] = []
    floorplan_url: Optional[str] = None
    agent_name: Optional[str] = None
    agency_name: Optional[str] = None
    listing_date: Optional[str] = None


class DomainAPIClient:
    """
    Client for Domain API.

    Authentication: OAuth 2.0 Client Credentials flow
    Base URL: https://api.domain.com.au

    Requires DOMAIN_CLIENT_ID and DOMAIN_CLIENT_SECRET in environment.
    """

    BASE_URL = "https://api.domain.com.au"
    AUTH_URL = "https://auth.domain.com.au/v1/connect/token"

    def __init__(self):
        self.client_id = getattr(settings, 'domain_client_id', None)
        self.client_secret = getattr(settings, 'domain_client_secret', None)
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    @property
    def is_configured(self) -> bool:
        """Check if Domain API credentials are configured."""
        return bool(self.client_id and self.client_secret)

    async def _get_access_token(self) -> str:
        """Get OAuth access token, refreshing if necessary."""
        # Check if we have a valid cached token
        if self._access_token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._access_token

        if not self.is_configured:
            raise ValueError("Domain API credentials not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "scope": "api_listings_read api_properties_read api_suburbperformance_read"
                },
                auth=(self.client_id, self.client_secret),
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access_token"]
            # Token typically expires in 3600 seconds, refresh 5 min early
            expires_in = data.get("expires_in", 3600) - 300
            self._token_expires = datetime.utcnow() + __import__('datetime').timedelta(seconds=expires_in)

            return self._access_token

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Domain API."""
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}{endpoint}",
                params=params,
                json=json_data,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_listing_by_id(self, listing_id: str) -> Optional[DomainProperty]:
        """
        Get listing details by Domain listing ID.

        Endpoint: GET /v1/listings/{id}
        """
        try:
            data = await self._request("GET", f"/v1/listings/{listing_id}")
            return self._parse_listing(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def search_listings(
        self,
        suburb: str,
        state: str,
        property_types: Optional[List[str]] = None,
        min_bedrooms: Optional[int] = None,
        max_bedrooms: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        listing_type: str = "Sale",
        page_size: int = 20
    ) -> List[DomainProperty]:
        """
        Search for residential listings.

        Endpoint: POST /v1/listings/residential/_search
        """
        # Build search request
        search_params = {
            "listingType": listing_type,
            "locations": [
                {
                    "state": state,
                    "suburb": suburb
                }
            ],
            "pageSize": page_size
        }

        if property_types:
            search_params["propertyTypes"] = property_types
        if min_bedrooms:
            search_params["minBedrooms"] = min_bedrooms
        if max_bedrooms:
            search_params["maxBedrooms"] = max_bedrooms
        if min_price:
            search_params["minPrice"] = min_price
        if max_price:
            search_params["maxPrice"] = max_price

        data = await self._request(
            "POST",
            "/v1/listings/residential/_search",
            json_data=search_params
        )

        return [self._parse_listing(item.get("listing", {})) for item in data if item.get("listing")]

    async def get_property_by_address(
        self,
        street_number: str,
        street_name: str,
        street_type: str,
        suburb: str,
        state: str,
        postcode: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get property details by address.

        Endpoint: GET /v2/properties/_suggest
        """
        address_query = f"{street_number} {street_name} {street_type}, {suburb} {state} {postcode}"

        try:
            suggestions = await self._request(
                "GET",
                "/v2/properties/_suggest",
                params={"terms": address_query, "pageSize": 1}
            )

            if suggestions and len(suggestions) > 0:
                property_id = suggestions[0].get("id")
                if property_id:
                    return await self.get_property_details(property_id)
        except Exception as e:
            print(f"Domain property lookup failed: {e}")

        return None

    async def get_property_details(self, property_id: str) -> Dict[str, Any]:
        """
        Get detailed property information.

        Endpoint: GET /v1/properties/{id}
        """
        return await self._request("GET", f"/v1/properties/{property_id}")

    async def get_suburb_performance(
        self,
        suburb: str,
        state: str,
        property_category: str = "house"
    ) -> Dict[str, Any]:
        """
        Get suburb performance statistics.

        Endpoint: GET /v2/suburbPerformanceStatistics/{state}/{suburb}/{propertyCategory}
        """
        return await self._request(
            "GET",
            f"/v2/suburbPerformanceStatistics/{state}/{suburb}/{property_category}"
        )

    async def get_sales_results(
        self,
        suburb: str,
        state: str
    ) -> List[Dict[str, Any]]:
        """
        Get recent sales results for a suburb.

        Endpoint: GET /v1/salesResults/{city}
        """
        # Note: This endpoint returns city-wide results
        # Filter by suburb in application code
        city_map = {
            "VIC": "melbourne",
            "NSW": "sydney",
            "QLD": "brisbane",
            "WA": "perth",
            "SA": "adelaide"
        }
        city = city_map.get(state, "melbourne")

        return await self._request("GET", f"/v1/salesResults/{city}")

    def _parse_listing(self, data: Dict[str, Any]) -> DomainProperty:
        """Parse Domain API listing response into DomainProperty model."""
        address_parts = data.get("addressParts", {})
        price_details = data.get("priceDetails", {})
        geo_location = data.get("geoLocation", {})

        # Extract images
        images = []
        media = data.get("media", [])
        for m in media:
            if m.get("category") == "Image" and m.get("url"):
                images.append(m["url"])

        # Extract floorplan
        floorplan_url = None
        for m in media:
            if m.get("category") == "FloorPlan" and m.get("url"):
                floorplan_url = m["url"]
                break

        # Extract features
        features = data.get("features", [])
        if isinstance(features, dict):
            features = features.get("general", []) + features.get("outdoor", []) + features.get("indoor", [])

        return DomainProperty(
            listing_id=str(data.get("id", "")),
            address=data.get("displayableAddress", ""),
            suburb=address_parts.get("suburb", ""),
            state=address_parts.get("stateAbbreviation", ""),
            postcode=address_parts.get("postcode", ""),
            property_type=data.get("propertyTypes", [""])[0] if data.get("propertyTypes") else "",
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            parking=data.get("carspaces"),
            land_size=data.get("landAreaSqm"),
            building_size=data.get("buildingAreaSqm"),
            price_display=price_details.get("displayPrice"),
            price_from=price_details.get("priceFrom"),
            price_to=price_details.get("priceTo"),
            latitude=geo_location.get("latitude"),
            longitude=geo_location.get("longitude"),
            description=data.get("description"),
            features=features,
            images=images,
            floorplan_url=floorplan_url,
            agent_name=data.get("advertiserIdentifiers", {}).get("contactName"),
            agency_name=data.get("advertiserIdentifiers", {}).get("advertiserName"),
            listing_date=data.get("dateListed")
        )


# Singleton instance
_domain_client: Optional[DomainAPIClient] = None


def get_domain_client() -> DomainAPIClient:
    """Get or create Domain API client instance."""
    global _domain_client
    if _domain_client is None:
        _domain_client = DomainAPIClient()
    return _domain_client


async def get_listing_from_url(url: str) -> Optional[DomainProperty]:
    """
    Extract listing data from a Domain URL.

    URL formats:
    - https://www.domain.com.au/123-smith-street-suburb-vic-3000-12345678
    - https://www.domain.com.au/listing/12345678
    """
    import re

    # Extract listing ID from URL
    patterns = [
        r'domain\.com\.au/.*?-(\d{7,})$',  # Address format with ID at end
        r'domain\.com\.au/listing/(\d+)',   # Direct listing URL
        r'(\d{7,})'                          # Just the ID
    ]

    listing_id = None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            listing_id = match.group(1)
            break

    if not listing_id:
        return None

    client = get_domain_client()

    if not client.is_configured:
        print("Domain API not configured, falling back to scraper")
        return None

    return await client.get_listing_by_id(listing_id)


async def enrich_with_domain_api(address: str, suburb: str, state: str) -> Optional[Dict[str, Any]]:
    """
    Enrich property data using Domain API suburb performance.

    Returns suburb statistics and recent sales data.
    """
    client = get_domain_client()

    if not client.is_configured:
        return None

    try:
        # Get suburb performance
        performance = await client.get_suburb_performance(suburb, state, "house")

        return {
            "source": "domain_api",
            "suburb_performance": {
                "median_sold_price": performance.get("medianSoldPrice"),
                "annual_growth": performance.get("annualGrowth"),
                "number_sold": performance.get("numberSold"),
                "days_on_market": performance.get("daysOnMarket"),
                "highest_sold_price": performance.get("highestSoldPrice"),
                "lowest_sold_price": performance.get("lowestSoldPrice"),
                "median_rent_listing_price": performance.get("medianRentListingPrice"),
                "average_days_on_market": performance.get("averageDaysOnMarket"),
                "entry_level_price": performance.get("entryLevelPrice")
            }
        }
    except Exception as e:
        print(f"Domain API enrichment failed: {e}")
        return None
