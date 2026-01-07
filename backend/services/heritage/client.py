"""
Heritage Victoria API client.

API Documentation: https://api.heritagecouncil.vic.gov.au/
Base URL: https://api.heritagecouncil.vic.gov.au/v1

The API returns HAL-formatted JSON responses.
No authentication required - public access.
"""

from typing import Optional, List, Dict, Any
import httpx
from datetime import date

from .models import HeritagePlace, HeritageSearchResult, HeritageRiskAssessment


class HeritageVictoriaClient:
    """
    Client for Heritage Victoria REST API.

    Provides access to the Victorian Heritage Register (VHR).
    All VHR-listed properties must be notified to Heritage Victoria
    within 28 days of acquisition.
    """

    BASE_URL = "https://api.heritagecouncil.vic.gov.au/v1"

    def __init__(self):
        self._session: Optional[httpx.AsyncClient] = None

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=30.0)
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.aclose()
            self._session = None

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make request to Heritage API."""
        session = await self._get_session()

        response = await session.get(
            f"{self.BASE_URL}{endpoint}",
            params=params,
            headers={"Accept": "application/hal+json"}
        )
        response.raise_for_status()
        return response.json()

    async def search_places(
        self,
        query: Optional[str] = None,
        municipality: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> HeritageSearchResult:
        """
        Search for heritage places.

        Args:
            query: Free text search (address, name, etc.)
            municipality: Filter by municipality/LGA name
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            HeritageSearchResult with list of matching places
        """
        params = {
            "page": page,
            "pageSize": page_size
        }

        if query:
            params["q"] = query
        if municipality:
            params["municipality"] = municipality

        try:
            data = await self._request("/places", params)

            places = []
            for item in data.get("_embedded", {}).get("places", []):
                place = self._parse_place(item)
                if place:
                    places.append(place)

            # Parse pagination from HAL links
            page_info = data.get("page", {})
            total_count = page_info.get("totalElements", len(places))
            total_pages = page_info.get("totalPages", 1)

            return HeritageSearchResult(
                places=places,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_more=page < total_pages
            )

        except httpx.HTTPStatusError as e:
            print(f"Heritage API error: {e}")
            return HeritageSearchResult(
                places=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False
            )
        except Exception as e:
            print(f"Heritage API request failed: {e}")
            return HeritageSearchResult(
                places=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False
            )

    async def get_place_by_vhr(self, vhr_number: str) -> Optional[HeritagePlace]:
        """
        Get heritage place by VHR number.

        Args:
            vhr_number: Victorian Heritage Register number (e.g., "H0001")

        Returns:
            HeritagePlace if found, None otherwise
        """
        try:
            data = await self._request(f"/places/{vhr_number}")
            return self._parse_place(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def search_by_address(
        self,
        address: str,
        municipality: Optional[str] = None
    ) -> HeritageSearchResult:
        """
        Search for heritage places by address.

        Args:
            address: Street address to search
            municipality: Optional municipality to narrow search

        Returns:
            HeritageSearchResult with matching places
        """
        return await self.search_places(
            query=address,
            municipality=municipality,
            page_size=10
        )

    async def search_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 100
    ) -> HeritageSearchResult:
        """
        Search for heritage places near coordinates.

        Note: The Heritage API may not support radius search directly.
        This implementation searches by address derived from coordinates.
        """
        # The Heritage API doesn't have native coordinate search
        # We'd need to use reverse geocoding first
        # For now, return empty result
        return HeritageSearchResult(
            places=[],
            total_count=0,
            page=1,
            page_size=20,
            has_more=False
        )

    async def get_municipalities(self) -> List[Dict[str, str]]:
        """
        Get list of municipalities/LGAs.

        Returns:
            List of municipality records with name and code
        """
        try:
            data = await self._request("/municipalities")
            municipalities = []
            for item in data.get("_embedded", {}).get("municipalities", []):
                municipalities.append({
                    "name": item.get("name", ""),
                    "code": item.get("code", "")
                })
            return municipalities
        except Exception as e:
            print(f"Failed to get municipalities: {e}")
            return []

    async def assess_heritage_risk(
        self,
        address: str,
        municipality: Optional[str] = None,
        local_heritage_overlay: bool = False
    ) -> HeritageRiskAssessment:
        """
        Assess heritage risk for a property.

        Args:
            address: Property address
            municipality: LGA name
            local_heritage_overlay: Whether property has HO overlay (from VicPlan)

        Returns:
            HeritageRiskAssessment with risk level and implications
        """
        # Search Victorian Heritage Register
        search_result = await self.search_by_address(address, municipality)

        is_vhr_listed = search_result.is_heritage_listed
        vhr_place = search_result.get_primary_place()

        # Determine risk level
        implications = []

        if is_vhr_listed:
            risk_level = "HIGH"
            implications.extend([
                "Property is on the Victorian Heritage Register",
                "Must notify Heritage Victoria within 28 days of settlement",
                "Heritage permit required for most external/internal works",
                "May restrict development potential",
                "Insurance implications - specialist heritage cover may be required"
            ])
        elif local_heritage_overlay:
            risk_level = "MEDIUM"
            implications.extend([
                "Property has local Heritage Overlay (HO)",
                "Council planning permit required for external works",
                "May restrict demolition and alterations",
                "Check specific HO schedule for requirements"
            ])
        else:
            risk_level = "NONE"
            implications.append("No heritage restrictions identified")

        return HeritageRiskAssessment(
            is_vhr_listed=is_vhr_listed,
            is_local_heritage=local_heritage_overlay,
            vhr_place=vhr_place,
            risk_level=risk_level,
            implications=implications,
            notification_required=is_vhr_listed,
            permit_required_for_works=is_vhr_listed or local_heritage_overlay
        )

    def _parse_place(self, data: Dict[str, Any]) -> Optional[HeritagePlace]:
        """Parse API response into HeritagePlace model."""
        if not data:
            return None

        # Parse registration date
        reg_date = None
        if data.get("registrationDate"):
            try:
                reg_date = date.fromisoformat(data["registrationDate"][:10])
            except (ValueError, TypeError):
                pass

        # Parse coordinates
        location = data.get("location", {})
        lat = location.get("latitude")
        lng = location.get("longitude")

        # Parse categories
        categories = data.get("categories", [])
        if isinstance(categories, list):
            categories = [c.get("name", c) if isinstance(c, dict) else str(c) for c in categories]

        # Parse images from HAL links
        images = []
        links = data.get("_links", {})
        if "images" in links:
            img_links = links["images"]
            if isinstance(img_links, list):
                images = [i.get("href") for i in img_links if i.get("href")]
            elif isinstance(img_links, dict) and img_links.get("href"):
                images = [img_links["href"]]

        return HeritagePlace(
            vhr_number=data.get("vhrNumber", data.get("id", "")),
            name=data.get("name", "Unknown"),
            address=data.get("address"),
            municipality=data.get("municipality", {}).get("name") if isinstance(data.get("municipality"), dict) else data.get("municipality"),
            latitude=lat,
            longitude=lng,
            significance=data.get("statementOfSignificance"),
            history=data.get("history"),
            description=data.get("description"),
            heritage_status=data.get("status", "Registered"),
            registration_date=reg_date,
            categories=categories,
            images=images
        )


# Singleton instance
_heritage_client: Optional[HeritageVictoriaClient] = None


def get_heritage_client() -> HeritageVictoriaClient:
    """Get or create Heritage Victoria client instance."""
    global _heritage_client
    if _heritage_client is None:
        _heritage_client = HeritageVictoriaClient()
    return _heritage_client


async def check_heritage_status(
    address: str,
    municipality: Optional[str] = None,
    has_heritage_overlay: bool = False
) -> HeritageRiskAssessment:
    """
    Convenience function to check heritage status for a property.

    Args:
        address: Property address
        municipality: LGA name
        has_heritage_overlay: Whether HO overlay detected from VicPlan

    Returns:
        HeritageRiskAssessment
    """
    client = get_heritage_client()
    return await client.assess_heritage_risk(
        address=address,
        municipality=municipality,
        local_heritage_overlay=has_heritage_overlay
    )
