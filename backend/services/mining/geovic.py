"""
GeoVic (Earth Resources Victoria) client.

Provides access to mining tenement data including:
- Exploration licenses
- Mining licenses
- Extractive industry (quarry) work authorities
- Petroleum permits

API: https://earthresources.vic.gov.au/geology-exploration/maps-reports-data/geovic
"""

from typing import Optional, List, Dict, Any
import httpx
import math

from .models import MiningTenement, MiningRiskAssessment, TenementType, TenementStatus


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class GeoVicClient:
    """
    Client for GeoVic mining tenement data.

    Uses ArcGIS REST services for spatial queries.
    """

    # GeoVic ArcGIS REST endpoints
    BASE_URL = "https://services.land.vic.gov.au/arcgis/rest/services"

    TENEMENT_LAYERS = {
        "exploration": "/Vicmap/Vicmap_Admin/MapServer/0",  # Exploration licenses
        "mining": "/Vicmap/Vicmap_Admin/MapServer/1",       # Mining licenses
        "extractive": "/Vicmap/Vicmap_Admin/MapServer/2",   # Extractive industry
    }

    def __init__(self):
        self._session: Optional[httpx.AsyncClient] = None

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=30.0)
        return self._session

    async def query_tenements(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1000
    ) -> List[MiningTenement]:
        """
        Query mining tenements near a point.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            radius_meters: Search radius in meters

        Returns:
            List of MiningTenement records
        """
        tenements = []

        # For MVP, use mock data
        # In production, would query GeoVic ArcGIS REST API
        mock_tenements = self._get_mock_tenements()

        for t in mock_tenements:
            t_lat = t.get("lat")
            t_lon = t.get("lon")

            if t_lat and t_lon:
                distance = haversine_distance(latitude, longitude, t_lat, t_lon)
                if distance <= radius_meters:
                    tenement = MiningTenement(
                        tenement_id=t["id"],
                        tenement_type=TenementType(t.get("type", "unknown")),
                        holder_name=t.get("holder"),
                        status=TenementStatus(t.get("status", "unknown")),
                        area_hectares=t.get("area_ha"),
                        grant_date=t.get("grant_date"),
                        expiry_date=t.get("expiry_date"),
                        commodities=t.get("commodities", []),
                        distance_meters=round(distance, 1),
                        covers_property=distance < 50,  # Within 50m considered "covering"
                        description=t.get("description")
                    )
                    tenements.append(tenement)

        # Sort by distance
        tenements.sort(key=lambda t: t.distance_meters or 999999)
        return tenements

    async def query_tenements_api(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query GeoVic ArcGIS REST API for tenements.

        This is the production implementation using actual API.
        """
        session = await self._get_session()

        # Convert point + radius to envelope for query
        # Approximate degrees for radius (rough conversion)
        deg_offset = radius_meters / 111000  # ~111km per degree

        geometry = {
            "xmin": longitude - deg_offset,
            "ymin": latitude - deg_offset,
            "xmax": longitude + deg_offset,
            "ymax": latitude + deg_offset,
            "spatialReference": {"wkid": 4326}
        }

        results = []

        for layer_name, layer_path in self.TENEMENT_LAYERS.items():
            try:
                response = await session.get(
                    f"{self.BASE_URL}{layer_path}/query",
                    params={
                        "geometry": str(geometry),
                        "geometryType": "esriGeometryEnvelope",
                        "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "*",
                        "f": "json"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    features = data.get("features", [])
                    for f in features:
                        results.append({
                            "layer": layer_name,
                            "attributes": f.get("attributes", {}),
                            "geometry": f.get("geometry", {})
                        })

            except Exception as e:
                print(f"GeoVic query failed for {layer_name}: {e}")

        return results

    def _get_mock_tenements(self) -> List[Dict[str, Any]]:
        """Return mock tenement data for testing."""
        return [
            {
                "id": "EL007123",
                "type": "exploration_license",
                "holder": "Gold Mining Co Pty Ltd",
                "status": "active",
                "area_ha": 500,
                "grant_date": "2020-01-15",
                "expiry_date": "2025-01-14",
                "commodities": ["Gold", "Silver"],
                "lat": -37.55,
                "lon": 144.25,
                "description": "Exploration for gold and silver deposits"
            },
            {
                "id": "MIN001456",
                "type": "mining_license",
                "holder": "Brown Coal Mining Ltd",
                "status": "active",
                "area_ha": 2000,
                "grant_date": "2015-06-01",
                "expiry_date": "2035-05-31",
                "commodities": ["Brown Coal"],
                "lat": -38.25,
                "lon": 146.35,
                "description": "Open cut brown coal mining"
            },
            {
                "id": "WA002789",
                "type": "extractive_industry",
                "holder": "Sand & Gravel Supplies",
                "status": "active",
                "area_ha": 50,
                "grant_date": "2018-03-20",
                "expiry_date": "2028-03-19",
                "commodities": ["Sand", "Gravel"],
                "lat": -37.78,
                "lon": 145.05,
                "description": "Sand and gravel quarry extraction"
            }
        ]

    async def assess_mining_risk(
        self,
        address: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> MiningRiskAssessment:
        """
        Assess mining tenement risk for a property.

        Args:
            address: Property address
            latitude: Property latitude
            longitude: Property longitude

        Returns:
            MiningRiskAssessment
        """
        implications = []
        recommendations = []
        covering = []
        nearby = []

        if latitude and longitude:
            tenements = await self.query_tenements(latitude, longitude, radius_meters=2000)

            for t in tenements:
                if t.covers_property:
                    covering.append(t)
                else:
                    nearby.append(t)

        property_covered = len(covering) > 0

        # Determine risk level and implications
        if property_covered:
            risk_level = "HIGH"
            for t in covering:
                if t.tenement_type == TenementType.MINING_LICENSE:
                    implications.append(f"Property is within active mining license ({t.tenement_id})")
                    implications.append("Mining operations may affect property use and value")
                    recommendations.append("Obtain legal advice on mining rights implications")
                    recommendations.append("Check for any compensation agreements")
                elif t.tenement_type == TenementType.EXPLORATION_LICENSE:
                    implications.append(f"Property is within exploration license ({t.tenement_id})")
                    implications.append("Exploration activity may occur on or near property")
                    recommendations.append("Review exploration license conditions")
                elif t.tenement_type == TenementType.EXTRACTIVE_INDUSTRY:
                    implications.append(f"Property is within extractive industry work authority ({t.tenement_id})")
                    implications.append("Quarry operations may cause noise, dust, and traffic impacts")
                    recommendations.append("Investigate buffer zones and operating hours")

        elif nearby:
            closest = nearby[0]
            if closest.distance_meters and closest.distance_meters < 500:
                risk_level = "MODERATE"
                implications.append(f"Mining tenement within {closest.distance_meters:.0f}m of property")
                if closest.tenement_type == TenementType.EXTRACTIVE_INDUSTRY:
                    implications.append("Potential noise and dust impacts from quarry operations")
            else:
                risk_level = "LOW"
                implications.append(f"Mining activity {closest.distance_meters:.0f}m from property")
        else:
            risk_level = "NONE"
            implications.append("No mining tenements identified near property")

        return MiningRiskAssessment(
            property_address=address,
            property_covered=property_covered,
            covering_tenements=covering,
            nearby_tenements=nearby[:5],  # Limit to 5 closest
            risk_level=risk_level,
            implications=implications,
            recommendations=recommendations
        )


# Singleton instance
_geovic_client: Optional[GeoVicClient] = None


def get_geovic_client() -> GeoVicClient:
    """Get or create GeoVic client instance."""
    global _geovic_client
    if _geovic_client is None:
        _geovic_client = GeoVicClient()
    return _geovic_client


async def check_mining_tenements(
    address: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> MiningRiskAssessment:
    """
    Convenience function to check mining tenements for a property.

    Args:
        address: Property address
        latitude: Property latitude
        longitude: Property longitude

    Returns:
        MiningRiskAssessment
    """
    client = get_geovic_client()
    return await client.assess_mining_risk(address, latitude, longitude)
