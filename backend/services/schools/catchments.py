"""
School catchment client for Victorian schools.

Data source: data.vic.gov.au - Victorian government school zones
GeoJSON boundaries available for designated neighbourhood schools.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import os
import math

from .models import School, SchoolCatchment, SchoolsAssessment, SchoolType, SchoolSector


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


class SchoolCatchmentClient:
    """
    Client for Victorian school catchment data.

    Uses cached school location and catchment boundary data.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cache",
            "schools"
        )
        self._schools: Optional[List[Dict[str, Any]]] = None

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _load_schools(self) -> List[Dict[str, Any]]:
        """Load school data from cache."""
        if self._schools is not None:
            return self._schools

        cache_path = os.path.join(self.cache_dir, "schools.json")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    self._schools = json.load(f)
                    return self._schools
            except Exception as e:
                print(f"Error loading schools cache: {e}")

        # Return mock data if no cache
        self._schools = self._get_mock_schools()
        return self._schools

    def _get_mock_schools(self) -> List[Dict[str, Any]]:
        """Return mock school data for common suburbs."""
        return [
            # Inner Melbourne
            {"id": "1001", "name": "Melbourne High School", "type": "secondary", "sector": "government", "suburb": "SOUTH YARRA", "lat": -37.8425, "lon": 144.9847, "icsea": 1150, "enrolments": 1400},
            {"id": "1002", "name": "Mac.Robertson Girls High School", "type": "secondary", "sector": "government", "suburb": "MELBOURNE", "lat": -37.8284, "lon": 144.9584, "icsea": 1180, "enrolments": 1100},
            {"id": "1003", "name": "South Yarra Primary School", "type": "primary", "sector": "government", "suburb": "SOUTH YARRA", "lat": -37.8392, "lon": 144.9890, "icsea": 1120, "enrolments": 450},
            {"id": "1004", "name": "Richmond Primary School", "type": "primary", "sector": "government", "suburb": "RICHMOND", "lat": -37.8195, "lon": 144.9952, "icsea": 1050, "enrolments": 380},
            {"id": "1005", "name": "Richmond High School", "type": "secondary", "sector": "government", "suburb": "RICHMOND", "lat": -37.8239, "lon": 144.9987, "icsea": 1020, "enrolments": 750},

            # Eastern suburbs
            {"id": "2001", "name": "Box Hill High School", "type": "secondary", "sector": "government", "suburb": "BOX HILL", "lat": -37.8188, "lon": 145.1195, "icsea": 1080, "enrolments": 1800},
            {"id": "2002", "name": "Box Hill Primary School", "type": "primary", "sector": "government", "suburb": "BOX HILL", "lat": -37.8201, "lon": 145.1180, "icsea": 1060, "enrolments": 420},
            {"id": "2003", "name": "Glen Waverley Secondary College", "type": "secondary", "sector": "government", "suburb": "GLEN WAVERLEY", "lat": -37.8795, "lon": 145.1640, "icsea": 1140, "enrolments": 2200},
            {"id": "2004", "name": "Glen Waverley Primary School", "type": "primary", "sector": "government", "suburb": "GLEN WAVERLEY", "lat": -37.8778, "lon": 145.1625, "icsea": 1100, "enrolments": 650},
            {"id": "2005", "name": "Camberwell High School", "type": "secondary", "sector": "government", "suburb": "CANTERBURY", "lat": -37.8210, "lon": 145.0767, "icsea": 1090, "enrolments": 1100},
            {"id": "2006", "name": "Balwyn High School", "type": "secondary", "sector": "government", "suburb": "BALWYN NORTH", "lat": -37.7887, "lon": 145.0889, "icsea": 1130, "enrolments": 2000},

            # Bayside
            {"id": "3001", "name": "Brighton Secondary College", "type": "secondary", "sector": "government", "suburb": "BRIGHTON", "lat": -37.9187, "lon": 145.0015, "icsea": 1070, "enrolments": 1200},
            {"id": "3002", "name": "Brighton Primary School", "type": "primary", "sector": "government", "suburb": "BRIGHTON", "lat": -37.9165, "lon": 144.9982, "icsea": 1110, "enrolments": 480},

            # Western suburbs
            {"id": "4001", "name": "Footscray City College", "type": "secondary", "sector": "government", "suburb": "FOOTSCRAY", "lat": -37.7968, "lon": 144.8925, "icsea": 970, "enrolments": 800},
            {"id": "4002", "name": "Footscray Primary School", "type": "primary", "sector": "government", "suburb": "FOOTSCRAY", "lat": -37.7995, "lon": 144.8967, "icsea": 950, "enrolments": 350},
            {"id": "4003", "name": "Werribee Secondary College", "type": "secondary", "sector": "government", "suburb": "WERRIBEE", "lat": -37.9022, "lon": 144.6644, "icsea": 990, "enrolments": 1500},

            # Growth areas
            {"id": "5001", "name": "Tarneit P-9 College", "type": "p12", "sector": "government", "suburb": "TARNEIT", "lat": -37.8332, "lon": 144.6952, "icsea": 1010, "enrolments": 1800},
            {"id": "5002", "name": "Point Cook Senior Secondary College", "type": "secondary", "sector": "government", "suburb": "POINT COOK", "lat": -37.9145, "lon": 144.7412, "icsea": 1030, "enrolments": 1400},

            # Private schools (examples)
            {"id": "6001", "name": "Scotch College", "type": "secondary", "sector": "independent", "suburb": "HAWTHORN", "lat": -37.8324, "lon": 145.0321, "icsea": 1200, "enrolments": 2100},
            {"id": "6002", "name": "Melbourne Grammar School", "type": "secondary", "sector": "independent", "suburb": "SOUTH YARRA", "lat": -37.8398, "lon": 144.9812, "icsea": 1190, "enrolments": 1800},
            {"id": "6003", "name": "Xavier College", "type": "secondary", "sector": "catholic", "suburb": "KEW", "lat": -37.8089, "lon": 145.0296, "icsea": 1170, "enrolments": 2000},
        ]

    def find_schools_near_point(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 3000,
        school_type: Optional[SchoolType] = None,
        sector: Optional[SchoolSector] = None
    ) -> List[School]:
        """
        Find schools within radius of a point.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            radius_meters: Search radius
            school_type: Filter by school type
            sector: Filter by sector

        Returns:
            List of School sorted by distance
        """
        schools = self._load_schools()
        nearby = []

        for s in schools:
            # Apply filters
            if school_type and s.get("type") != school_type.value:
                continue
            if sector and s.get("sector") != sector.value:
                continue

            s_lat = s.get("lat")
            s_lon = s.get("lon")

            if s_lat and s_lon:
                distance = haversine_distance(latitude, longitude, s_lat, s_lon)
                if distance <= radius_meters:
                    nearby.append(School(
                        school_id=s["id"],
                        name=s["name"],
                        school_type=SchoolType(s.get("type", "unknown")),
                        sector=SchoolSector(s.get("sector", "unknown")),
                        suburb=s.get("suburb"),
                        latitude=s_lat,
                        longitude=s_lon,
                        distance_meters=round(distance, 1),
                        icsea=s.get("icsea"),
                        enrolments=s.get("enrolments")
                    ))

        # Sort by distance
        nearby.sort(key=lambda s: s.distance_meters or 999999)
        return nearby

    def find_catchment_school(
        self,
        latitude: float,
        longitude: float,
        school_type: SchoolType
    ) -> Optional[SchoolCatchment]:
        """
        Find designated neighbourhood school for a location.

        Note: This is a simplified implementation. Full implementation
        would use actual catchment boundary polygons.
        """
        # Find nearest government school of the type
        schools = self.find_schools_near_point(
            latitude, longitude,
            radius_meters=5000,
            school_type=school_type,
            sector=SchoolSector.GOVERNMENT
        )

        if not schools:
            return None

        # Assume nearest government school is the catchment school
        # In production, would check actual catchment boundaries
        nearest = schools[0]

        # Simple heuristic: within 2km is likely in catchment
        in_catchment = nearest.distance_meters and nearest.distance_meters < 2000

        return SchoolCatchment(
            school=nearest,
            in_catchment=in_catchment,
            catchment_name=f"{nearest.name} Zone" if in_catchment else None
        )

    def assess_schools(
        self,
        address: str,
        latitude: float,
        longitude: float
    ) -> SchoolsAssessment:
        """
        Assess school options for a property location.

        Args:
            address: Property address
            latitude: Property latitude
            longitude: Property longitude

        Returns:
            SchoolsAssessment with catchments and nearby schools
        """
        # Find catchment schools
        primary_catchment = self.find_catchment_school(
            latitude, longitude, SchoolType.PRIMARY
        )
        secondary_catchment = self.find_catchment_school(
            latitude, longitude, SchoolType.SECONDARY
        )

        # Find nearby schools by type
        nearby_primary = self.find_schools_near_point(
            latitude, longitude,
            radius_meters=3000,
            school_type=SchoolType.PRIMARY,
            sector=SchoolSector.GOVERNMENT
        )[:5]

        nearby_secondary = self.find_schools_near_point(
            latitude, longitude,
            radius_meters=5000,
            school_type=SchoolType.SECONDARY,
            sector=SchoolSector.GOVERNMENT
        )[:5]

        # Find nearby private schools
        nearby_private = [
            s for s in self.find_schools_near_point(latitude, longitude, 5000)
            if s.sector in [SchoolSector.INDEPENDENT, SchoolSector.CATHOLIC]
        ][:5]

        # Calculate desirability score based on:
        # - ICSEA of catchment schools
        # - Distance to schools
        # - Variety of options
        desirability = 50.0

        if primary_catchment and primary_catchment.school.icsea:
            # ICSEA ranges from ~500 to ~1300, average is 1000
            icsea_factor = (primary_catchment.school.icsea - 900) / 300 * 20
            desirability += icsea_factor

        if secondary_catchment and secondary_catchment.school.icsea:
            icsea_factor = (secondary_catchment.school.icsea - 900) / 300 * 20
            desirability += icsea_factor

        # Proximity bonus
        if primary_catchment and primary_catchment.school.distance_meters:
            if primary_catchment.school.distance_meters < 1000:
                desirability += 5

        # Variety bonus
        if len(nearby_private) >= 3:
            desirability += 5

        desirability = max(0, min(100, desirability))

        # Generate summary
        summary_parts = []

        if primary_catchment and primary_catchment.in_catchment:
            summary_parts.append(f"Primary: {primary_catchment.school.name} ({primary_catchment.school.distance_meters:.0f}m)")
        elif primary_catchment:
            summary_parts.append(f"Nearest primary: {primary_catchment.school.name} ({primary_catchment.school.distance_meters:.0f}m)")

        if secondary_catchment and secondary_catchment.in_catchment:
            summary_parts.append(f"Secondary: {secondary_catchment.school.name} ({secondary_catchment.school.distance_meters:.0f}m)")
        elif secondary_catchment:
            summary_parts.append(f"Nearest secondary: {secondary_catchment.school.name} ({secondary_catchment.school.distance_meters:.0f}m)")

        if nearby_private:
            summary_parts.append(f"{len(nearby_private)} private school(s) within 5km")

        summary = ". ".join(summary_parts) if summary_parts else "No school data available"

        return SchoolsAssessment(
            property_address=address,
            primary_catchment=primary_catchment,
            secondary_catchment=secondary_catchment,
            nearby_primary=nearby_primary,
            nearby_secondary=nearby_secondary,
            nearby_private=nearby_private,
            desirability_score=desirability,
            summary=summary
        )


# Singleton instance
_school_client: Optional[SchoolCatchmentClient] = None


def get_school_client() -> SchoolCatchmentClient:
    """Get or create school catchment client instance."""
    global _school_client
    if _school_client is None:
        _school_client = SchoolCatchmentClient()
    return _school_client


async def get_school_catchments(
    address: str,
    latitude: float,
    longitude: float
) -> SchoolsAssessment:
    """
    Convenience function to get school catchment assessment.

    Args:
        address: Property address
        latitude: Property latitude
        longitude: Property longitude

    Returns:
        SchoolsAssessment
    """
    client = get_school_client()
    return client.assess_schools(address, latitude, longitude)
