"""
EPA Victoria Priority Sites Register client.

The Priority Sites Register (PSR) lists sites where EPA has issued:
- Clean Up Notices
- Pollution Abatement Notices
- Environmental Audit Conditions

Data source: https://www.epa.vic.gov.au/for-community/environmental-information/priority-sites-register
GeoJSON available from: https://data.vic.gov.au
"""

from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json
import os
import math

from .models import (
    ContaminatedSite,
    ContaminationRiskAssessment,
    ContaminationType,
    SiteStatus
)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula."""
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


class EPAClient:
    """
    Client for EPA Victoria contamination data.

    Uses cached Priority Sites Register data for fast spatial queries.
    The cache should be refreshed monthly.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cache",
            "epa"
        )
        self._sites: Optional[List[Dict[str, Any]]] = None

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self) -> str:
        """Get path to PSR cache file."""
        return os.path.join(self.cache_dir, "priority_sites.json")

    def _load_sites(self) -> List[Dict[str, Any]]:
        """Load priority sites data from cache."""
        if self._sites is not None:
            return self._sites

        cache_path = self._get_cache_path()

        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    self._sites = json.load(f)
                    return self._sites
            except Exception as e:
                print(f"Error loading EPA cache: {e}")

        # Return mock data if no cache exists
        self._sites = self._get_mock_sites()
        return self._sites

    def _get_mock_sites(self) -> List[Dict[str, Any]]:
        """Return mock priority sites data for testing."""
        return [
            {
                "id": "PSR001",
                "name": "Former Gas Works Site",
                "address": "123 Industrial Road, Footscray VIC 3011",
                "suburb": "FOOTSCRAY",
                "lat": -37.7997,
                "lon": 144.8994,
                "types": ["petroleum", "chemical"],
                "status": "monitoring",
                "description": "Former gas manufacturing facility with petroleum hydrocarbon contamination"
            },
            {
                "id": "PSR002",
                "name": "Historic Landfill",
                "address": "45 Tip Road, Laverton VIC 3028",
                "suburb": "LAVERTON",
                "lat": -37.8633,
                "lon": 144.7628,
                "types": ["landfill"],
                "status": "monitoring",
                "description": "Former municipal landfill site"
            },
            {
                "id": "PSR003",
                "name": "Industrial Chemical Site",
                "address": "78 Factory Street, Dandenong VIC 3175",
                "suburb": "DANDENONG",
                "lat": -37.9876,
                "lon": 145.2156,
                "types": ["chemical", "heavy_metals"],
                "status": "active",
                "description": "Former chemical manufacturing with heavy metal contamination"
            },
            {
                "id": "PSR004",
                "name": "PFAS Affected Area",
                "address": "Airport Road, Tullamarine VIC 3043",
                "suburb": "TULLAMARINE",
                "lat": -37.6733,
                "lon": 144.8519,
                "types": ["pfas"],
                "status": "under_assessment",
                "description": "PFAS contamination from fire fighting foam use"
            },
            {
                "id": "PSR005",
                "name": "Former Service Station",
                "address": "234 Main Street, Box Hill VIC 3128",
                "suburb": "BOX HILL",
                "lat": -37.8190,
                "lon": 145.1215,
                "types": ["petroleum"],
                "status": "remediated",
                "description": "Former petroleum service station - remediation complete"
            }
        ]

    def find_sites_near_point(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 500
    ) -> List[ContaminatedSite]:
        """
        Find contaminated sites within radius of a point.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            radius_meters: Search radius in meters (default 500m)

        Returns:
            List of ContaminatedSite within radius, sorted by distance
        """
        sites = self._load_sites()
        nearby = []

        for site in sites:
            site_lat = site.get("lat")
            site_lon = site.get("lon")

            if site_lat is None or site_lon is None:
                continue

            distance = haversine_distance(latitude, longitude, site_lat, site_lon)

            if distance <= radius_meters:
                # Parse contamination types
                types = []
                for t in site.get("types", []):
                    try:
                        types.append(ContaminationType(t))
                    except ValueError:
                        types.append(ContaminationType.UNKNOWN)

                # Parse status
                try:
                    status = SiteStatus(site.get("status", "unknown"))
                except ValueError:
                    status = SiteStatus.UNKNOWN

                nearby.append(ContaminatedSite(
                    site_id=site.get("id", ""),
                    site_name=site.get("name", "Unknown Site"),
                    address=site.get("address"),
                    suburb=site.get("suburb"),
                    latitude=site_lat,
                    longitude=site_lon,
                    distance_meters=round(distance, 1),
                    contamination_types=types,
                    status=status,
                    description=site.get("description"),
                    epa_reference=site.get("epa_reference")
                ))

        # Sort by distance
        nearby.sort(key=lambda s: s.distance_meters or 999999)
        return nearby

    def check_property_on_psr(
        self,
        address: str,
        suburb: str
    ) -> Optional[ContaminatedSite]:
        """
        Check if a property is directly on the Priority Sites Register.

        Args:
            address: Property address
            suburb: Suburb name

        Returns:
            ContaminatedSite if property is on PSR, None otherwise
        """
        sites = self._load_sites()
        suburb_upper = suburb.upper().strip()
        address_lower = address.lower().strip()

        for site in sites:
            site_suburb = (site.get("suburb") or "").upper()
            site_address = (site.get("address") or "").lower()

            # Check if suburb matches and address is similar
            if site_suburb == suburb_upper:
                # Simple address matching - check if key parts match
                if any(part in site_address for part in address_lower.split()[:3]):
                    # Parse contamination types
                    types = []
                    for t in site.get("types", []):
                        try:
                            types.append(ContaminationType(t))
                        except ValueError:
                            types.append(ContaminationType.UNKNOWN)

                    try:
                        status = SiteStatus(site.get("status", "unknown"))
                    except ValueError:
                        status = SiteStatus.UNKNOWN

                    return ContaminatedSite(
                        site_id=site.get("id", ""),
                        site_name=site.get("name", "Unknown Site"),
                        address=site.get("address"),
                        suburb=site.get("suburb"),
                        latitude=site.get("lat"),
                        longitude=site.get("lon"),
                        distance_meters=0,
                        contamination_types=types,
                        status=status,
                        description=site.get("description"),
                        epa_reference=site.get("epa_reference")
                    )

        return None

    def assess_contamination_risk(
        self,
        address: str,
        suburb: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        historic_zoning: Optional[str] = None,
        overlays: Optional[List[str]] = None
    ) -> ContaminationRiskAssessment:
        """
        Assess contamination risk for a property.

        Args:
            address: Property address
            suburb: Suburb name
            latitude: Property latitude (for proximity search)
            longitude: Property longitude (for proximity search)
            historic_zoning: Historic zoning if known (industrial zones are higher risk)
            overlays: Planning overlays (e.g., EAO - Environmental Audit Overlay)

        Returns:
            ContaminationRiskAssessment
        """
        overlays = overlays or []
        concerns = []
        recommendations = []
        risk_score = 0.0

        # Check if property is on PSR
        psr_site = self.check_property_on_psr(address, suburb)
        is_on_psr = psr_site is not None

        if is_on_psr:
            risk_score += 80
            concerns.append("Property is on EPA Priority Sites Register")
            recommendations.append("Engage environmental consultant before purchase")
            recommendations.append("Review all EPA notices and audit requirements")

        # Check nearby sites
        nearby_sites = []
        if latitude and longitude:
            nearby_sites = self.find_sites_near_point(latitude, longitude, radius_meters=500)
            # Exclude the property itself if it was found
            if psr_site:
                nearby_sites = [s for s in nearby_sites if s.site_id != psr_site.site_id]

            if nearby_sites:
                closest = nearby_sites[0]
                if closest.distance_meters and closest.distance_meters < 100:
                    risk_score += 30
                    concerns.append(f"Adjacent to contaminated site: {closest.site_name} ({closest.distance_meters:.0f}m)")
                elif closest.distance_meters and closest.distance_meters < 250:
                    risk_score += 15
                    concerns.append(f"Near contaminated site: {closest.site_name} ({closest.distance_meters:.0f}m)")
                elif nearby_sites:
                    risk_score += 5
                    concerns.append(f"{len(nearby_sites)} contaminated site(s) within 500m")

        # Check for Environmental Audit Overlay
        has_eao = any("EAO" in str(o).upper() for o in overlays)
        if has_eao:
            risk_score += 40
            concerns.append("Property has Environmental Audit Overlay (EAO)")
            recommendations.append("Environmental audit required before development")

        # Check historic industrial zoning
        historic_industrial = False
        if historic_zoning:
            industrial_zones = ["IN1", "IN2", "IN3", "SUZ", "INDUSTRIAL"]
            if any(z in historic_zoning.upper() for z in industrial_zones):
                historic_industrial = True
                risk_score += 20
                concerns.append("Property has historic industrial zoning")
                recommendations.append("Consider Phase 1 environmental site assessment")

        # Check for groundwater restrictions (would come from VicPlan)
        groundwater_restricted = any("GWR" in str(o).upper() for o in overlays)
        if groundwater_restricted:
            risk_score += 15
            concerns.append("Property in groundwater quality restricted use zone")

        # Determine risk level
        if risk_score >= 80:
            risk_level = "CRITICAL"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "ELEVATED"
        elif risk_score >= 20:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Add default recommendations
        if not recommendations and risk_level in ["MODERATE", "ELEVATED"]:
            recommendations.append("Consider Phase 1 environmental site assessment")

        if not concerns:
            concerns.append("No contamination concerns identified")

        return ContaminationRiskAssessment(
            property_address=address,
            is_on_psr=is_on_psr,
            psr_site=psr_site,
            nearby_sites=nearby_sites[:5],  # Limit to 5 closest
            historic_industrial_use=historic_industrial,
            groundwater_restricted=groundwater_restricted,
            risk_level=risk_level,
            risk_score=min(100, risk_score),
            concerns=concerns,
            recommendations=recommendations,
            environmental_audit_required=has_eao or is_on_psr
        )

    async def refresh_data(self):
        """
        Refresh PSR data from EPA/data.vic.gov.au.

        In production, this would:
        1. Download GeoJSON from data.vic.gov.au
        2. Parse and transform data
        3. Update local cache
        """
        # TODO: Implement actual data download
        # Data available at: https://discover.data.vic.gov.au/dataset/epa-priority-sites
        print("EPA data refresh not yet implemented - using cached/mock data")


# Singleton instance
_epa_client: Optional[EPAClient] = None


def get_epa_client() -> EPAClient:
    """Get or create EPA client instance."""
    global _epa_client
    if _epa_client is None:
        _epa_client = EPAClient()
    return _epa_client


async def check_contamination_risk(
    address: str,
    suburb: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    overlays: Optional[List[str]] = None
) -> ContaminationRiskAssessment:
    """
    Convenience function to check contamination risk for a property.

    Args:
        address: Property address
        suburb: Suburb name
        latitude: Property latitude
        longitude: Property longitude
        overlays: Planning overlays

    Returns:
        ContaminationRiskAssessment
    """
    client = get_epa_client()
    return client.assess_contamination_risk(
        address=address,
        suburb=suburb,
        latitude=latitude,
        longitude=longitude,
        overlays=overlays
    )
