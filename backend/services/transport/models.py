"""
Data models for transport accessibility.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class TransportMode(str, Enum):
    """Public transport modes."""
    TRAIN = "train"
    TRAM = "tram"
    BUS = "bus"
    VLINE = "vline"  # Regional train
    FERRY = "ferry"


class TransportStop(BaseModel):
    """Public transport stop/station."""
    stop_id: str
    name: str
    mode: TransportMode
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_meters: Optional[float] = None
    walk_time_minutes: Optional[int] = None
    routes: List[str] = []  # Route names/numbers
    zone: Optional[int] = None  # Myki zone

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stop_id": self.stop_id,
            "name": self.name,
            "mode": self.mode.value,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_meters": self.distance_meters,
            "walk_time_minutes": self.walk_time_minutes,
            "routes": self.routes,
            "zone": self.zone
        }


class TransportAccessibility(BaseModel):
    """Transport accessibility assessment for a location."""
    property_address: str
    nearest_train: Optional[TransportStop] = None
    nearest_tram: Optional[TransportStop] = None
    nearest_bus: Optional[TransportStop] = None
    all_nearby_stops: List[TransportStop] = []
    accessibility_score: float = 0.0  # 0-100
    rating: str = "unknown"  # excellent, good, moderate, limited, poor
    summary: str = ""
    commute_to_cbd_minutes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_address": self.property_address,
            "nearest_train": self.nearest_train.to_dict() if self.nearest_train else None,
            "nearest_tram": self.nearest_tram.to_dict() if self.nearest_tram else None,
            "nearest_bus": self.nearest_bus.to_dict() if self.nearest_bus else None,
            "all_nearby_stops": [s.to_dict() for s in self.all_nearby_stops[:10]],
            "accessibility_score": self.accessibility_score,
            "rating": self.rating,
            "summary": self.summary,
            "commute_to_cbd_minutes": self.commute_to_cbd_minutes
        }
