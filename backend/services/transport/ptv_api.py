"""
PTV (Public Transport Victoria) API client.

Uses PTV's GTFS data and API to calculate transport accessibility.
API registration: https://www.ptv.vic.gov.au/footer/data-and-reporting/datasets/ptv-timetable-api/

For MVP, uses mock data based on known station locations.
"""

from typing import Optional, List, Dict, Any
import math

from .models import TransportStop, TransportAccessibility, TransportMode


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


# Walking speed assumption: 5 km/h = 83 m/min
WALK_SPEED_M_PER_MIN = 83


class TransportClient:
    """
    Client for PTV transport data.

    Uses cached stop location data for fast proximity queries.
    """

    def __init__(self):
        self._stops: Optional[List[Dict[str, Any]]] = None

    def _load_stops(self) -> List[Dict[str, Any]]:
        """Load transport stop data."""
        if self._stops is not None:
            return self._stops

        # Mock data for major Melbourne stations and stops
        self._stops = self._get_mock_stops()
        return self._stops

    def _get_mock_stops(self) -> List[Dict[str, Any]]:
        """Return mock transport stop data."""
        return [
            # Train stations - City Loop
            {"id": "T001", "name": "Flinders Street Station", "mode": "train", "lat": -37.8183, "lon": 144.9671, "routes": ["All Lines"], "zone": 1},
            {"id": "T002", "name": "Melbourne Central Station", "mode": "train", "lat": -37.8102, "lon": 144.9628, "routes": ["All Lines"], "zone": 1},
            {"id": "T003", "name": "Parliament Station", "mode": "train", "lat": -37.8118, "lon": 144.9728, "routes": ["All Lines"], "zone": 1},
            {"id": "T004", "name": "Southern Cross Station", "mode": "train", "lat": -37.8184, "lon": 144.9525, "routes": ["Regional", "Metro"], "zone": 1},

            # Train stations - Inner suburbs
            {"id": "T010", "name": "Richmond Station", "mode": "train", "lat": -37.8239, "lon": 144.9898, "routes": ["Glen Waverley", "Alamein", "Belgrave", "Lilydale"], "zone": 1},
            {"id": "T011", "name": "South Yarra Station", "mode": "train", "lat": -37.8386, "lon": 144.9923, "routes": ["Sandringham", "Frankston"], "zone": 1},
            {"id": "T012", "name": "Footscray Station", "mode": "train", "lat": -37.7997, "lon": 144.8994, "routes": ["Sunbury", "Werribee", "Williamstown"], "zone": 1},
            {"id": "T013", "name": "North Melbourne Station", "mode": "train", "lat": -37.8072, "lon": 144.9422, "routes": ["Craigieburn", "Upfield", "Sunbury"], "zone": 1},

            # Train stations - Eastern suburbs
            {"id": "T020", "name": "Box Hill Station", "mode": "train", "lat": -37.8190, "lon": 145.1215, "routes": ["Belgrave", "Lilydale"], "zone": 1},
            {"id": "T021", "name": "Glen Waverley Station", "mode": "train", "lat": -37.8793, "lon": 145.1621, "routes": ["Glen Waverley"], "zone": 2},
            {"id": "T022", "name": "Camberwell Station", "mode": "train", "lat": -37.8268, "lon": 145.0590, "routes": ["Belgrave", "Lilydale", "Alamein"], "zone": 1},

            # Train stations - Southeast
            {"id": "T030", "name": "Caulfield Station", "mode": "train", "lat": -37.8760, "lon": 145.0422, "routes": ["Frankston", "Cranbourne", "Pakenham"], "zone": 1},
            {"id": "T031", "name": "Brighton Beach Station", "mode": "train", "lat": -37.9216, "lon": 144.9880, "routes": ["Sandringham"], "zone": 2},
            {"id": "T032", "name": "Dandenong Station", "mode": "train", "lat": -37.9876, "lon": 145.2156, "routes": ["Cranbourne", "Pakenham"], "zone": 2},

            # Train stations - North
            {"id": "T040", "name": "Coburg Station", "mode": "train", "lat": -37.7427, "lon": 144.9658, "routes": ["Upfield"], "zone": 1},
            {"id": "T041", "name": "Preston Station", "mode": "train", "lat": -37.7306, "lon": 145.0103, "routes": ["South Morang", "Mernda"], "zone": 1},

            # Tram stops - Key locations
            {"id": "R001", "name": "Stop 1 - Bourke St/Spencer St", "mode": "tram", "lat": -37.8172, "lon": 144.9536, "routes": ["86", "96"], "zone": 1},
            {"id": "R002", "name": "Stop 8 - Bourke St/Swanston St", "mode": "tram", "lat": -37.8133, "lon": 144.9650, "routes": ["86", "96"], "zone": 1},
            {"id": "R003", "name": "Melbourne University", "mode": "tram", "lat": -37.7988, "lon": 144.9600, "routes": ["1", "3", "5", "6", "16", "64", "67", "72"], "zone": 1},
            {"id": "R004", "name": "St Kilda Junction", "mode": "tram", "lat": -37.8586, "lon": 144.9805, "routes": ["3", "16", "67"], "zone": 1},
            {"id": "R005", "name": "Chapel St/Toorak Rd", "mode": "tram", "lat": -37.8410, "lon": 144.9945, "routes": ["6", "72", "78"], "zone": 1},
            {"id": "R006", "name": "Victoria Gardens", "mode": "tram", "lat": -37.8021, "lon": 144.9948, "routes": ["24", "109"], "zone": 1},

            # Bus stops - Selected locations
            {"id": "B001", "name": "Lonsdale St/Spencer St", "mode": "bus", "lat": -37.8150, "lon": 144.9540, "routes": ["200", "207", "302"], "zone": 1},
            {"id": "B002", "name": "Box Hill Bus Interchange", "mode": "bus", "lat": -37.8185, "lon": 145.1220, "routes": ["270", "279", "903", "907"], "zone": 1},
            {"id": "B003", "name": "Chadstone Shopping Centre", "mode": "bus", "lat": -37.8864, "lon": 145.0833, "routes": ["900", "903", "767"], "zone": 2},
        ]

    def find_stops_near_point(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1500,
        mode: Optional[TransportMode] = None
    ) -> List[TransportStop]:
        """
        Find transport stops within radius of a point.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            radius_meters: Search radius
            mode: Filter by transport mode

        Returns:
            List of TransportStop sorted by distance
        """
        stops = self._load_stops()
        nearby = []

        for s in stops:
            # Apply mode filter
            if mode and s.get("mode") != mode.value:
                continue

            s_lat = s.get("lat")
            s_lon = s.get("lon")

            if s_lat and s_lon:
                distance = haversine_distance(latitude, longitude, s_lat, s_lon)
                if distance <= radius_meters:
                    walk_time = int(distance / WALK_SPEED_M_PER_MIN) + 1

                    nearby.append(TransportStop(
                        stop_id=s["id"],
                        name=s["name"],
                        mode=TransportMode(s["mode"]),
                        latitude=s_lat,
                        longitude=s_lon,
                        distance_meters=round(distance, 1),
                        walk_time_minutes=walk_time,
                        routes=s.get("routes", []),
                        zone=s.get("zone")
                    ))

        # Sort by distance
        nearby.sort(key=lambda s: s.distance_meters or 999999)
        return nearby

    def assess_accessibility(
        self,
        address: str,
        latitude: float,
        longitude: float
    ) -> TransportAccessibility:
        """
        Assess transport accessibility for a location.

        Args:
            address: Property address
            latitude: Property latitude
            longitude: Property longitude

        Returns:
            TransportAccessibility assessment
        """
        # Find nearest stops by mode
        all_stops = self.find_stops_near_point(latitude, longitude, radius_meters=2000)

        train_stops = [s for s in all_stops if s.mode == TransportMode.TRAIN]
        tram_stops = [s for s in all_stops if s.mode == TransportMode.TRAM]
        bus_stops = [s for s in all_stops if s.mode == TransportMode.BUS]

        nearest_train = train_stops[0] if train_stops else None
        nearest_tram = tram_stops[0] if tram_stops else None
        nearest_bus = bus_stops[0] if bus_stops else None

        # Calculate accessibility score (0-100)
        score = 0

        # Train proximity (most valuable - up to 40 points)
        if nearest_train:
            train_dist = nearest_train.distance_meters or 9999
            if train_dist < 400:
                score += 40
            elif train_dist < 800:
                score += 35
            elif train_dist < 1200:
                score += 25
            elif train_dist < 1600:
                score += 15
            elif train_dist < 2000:
                score += 5

        # Tram proximity (up to 30 points)
        if nearest_tram:
            tram_dist = nearest_tram.distance_meters or 9999
            if tram_dist < 300:
                score += 30
            elif tram_dist < 500:
                score += 25
            elif tram_dist < 800:
                score += 15
            elif tram_dist < 1200:
                score += 8

        # Bus proximity (up to 20 points)
        if nearest_bus:
            bus_dist = nearest_bus.distance_meters or 9999
            if bus_dist < 300:
                score += 20
            elif bus_dist < 500:
                score += 15
            elif bus_dist < 800:
                score += 10

        # Multi-modal bonus (up to 10 points)
        modes_available = sum([
            1 if nearest_train else 0,
            1 if nearest_tram else 0,
            1 if nearest_bus else 0
        ])
        score += modes_available * 3

        # Determine rating
        if score >= 80:
            rating = "excellent"
        elif score >= 60:
            rating = "good"
        elif score >= 40:
            rating = "moderate"
        elif score >= 20:
            rating = "limited"
        else:
            rating = "poor"

        # Generate summary
        summary_parts = []
        if nearest_train:
            summary_parts.append(f"Train: {nearest_train.name} ({nearest_train.walk_time_minutes} min walk)")
        if nearest_tram:
            summary_parts.append(f"Tram: {nearest_tram.name} ({nearest_tram.walk_time_minutes} min walk)")
        if nearest_bus:
            summary_parts.append(f"Bus: {nearest_bus.name} ({nearest_bus.walk_time_minutes} min walk)")

        summary = ". ".join(summary_parts) if summary_parts else "Limited public transport options"

        # Estimate CBD commute (simplified)
        cbd_lat, cbd_lon = -37.8136, 144.9631  # Melbourne CBD
        cbd_distance = haversine_distance(latitude, longitude, cbd_lat, cbd_lon)

        if nearest_train and nearest_train.distance_meters and nearest_train.distance_meters < 1500:
            # Estimate: walk to station + train time (assume 30km/h avg) + walk from station
            walk_time = (nearest_train.distance_meters / WALK_SPEED_M_PER_MIN)
            train_time = (cbd_distance / 1000) / 30 * 60  # km to hours to minutes
            commute_time = int(walk_time + train_time + 10)  # +10 for exit/wait
        elif nearest_tram:
            # Trams are slower but more frequent
            commute_time = int(cbd_distance / 1000 / 15 * 60 + 10)
        else:
            commute_time = None

        return TransportAccessibility(
            property_address=address,
            nearest_train=nearest_train,
            nearest_tram=nearest_tram,
            nearest_bus=nearest_bus,
            all_nearby_stops=all_stops[:10],
            accessibility_score=min(100, score),
            rating=rating,
            summary=summary,
            commute_to_cbd_minutes=commute_time
        )


# Singleton instance
_transport_client: Optional[TransportClient] = None


def get_transport_client() -> TransportClient:
    """Get or create transport client instance."""
    global _transport_client
    if _transport_client is None:
        _transport_client = TransportClient()
    return _transport_client


async def assess_transport_accessibility(
    address: str,
    latitude: float,
    longitude: float
) -> TransportAccessibility:
    """
    Convenience function to assess transport accessibility.

    Args:
        address: Property address
        latitude: Property latitude
        longitude: Property longitude

    Returns:
        TransportAccessibility assessment
    """
    client = get_transport_client()
    return client.assess_accessibility(address, latitude, longitude)
