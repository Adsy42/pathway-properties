"""
Generate GeoJSON layers for map visualization.
"""

from typing import Dict, Any, Optional, List
import json


async def generate_map_layers(
    address: str,
    street_level: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate GeoJSON layers for Mapbox visualization.
    
    Returns layers for:
    - Property marker
    - Flood zones
    - Bushfire zones
    - Social housing heatmap
    - Flight path contours
    """
    
    # For MVP, return structure with mock data
    # In production, would fetch from Geoscape, state planning portals
    
    return {
        "property": {
            "type": "FeatureCollection",
            "features": []  # Property point marker
        },
        "flood_zones": {
            "type": "FeatureCollection",
            "features": [],  # Flood overlay polygons
            "style": {
                "fill-color": "#0066cc",
                "fill-opacity": 0.3,
                "line-color": "#0044aa",
                "line-width": 2
            }
        },
        "bushfire_zones": {
            "type": "FeatureCollection",
            "features": [],  # BAL zone polygons
            "style": {
                "fill-color": "#ff6600",
                "fill-opacity": 0.3,
                "line-color": "#cc4400",
                "line-width": 2
            }
        },
        "social_housing": {
            "type": "FeatureCollection",
            "features": [],  # SA1 polygons with density values
            "style": {
                "fill-color": [
                    "interpolate",
                    ["linear"],
                    ["get", "density"],
                    0, "#00ff00",
                    15, "#ffff00",
                    30, "#ff0000"
                ],
                "fill-opacity": 0.4
            }
        },
        "flight_paths": {
            "type": "FeatureCollection",
            "features": [],  # ANEF contour lines
            "style": {
                "line-color": "#9900cc",
                "line-width": 2,
                "line-dasharray": [2, 2]
            }
        },
        "zoning": {
            "type": "FeatureCollection",
            "features": [],  # Zone boundaries
            "style": {
                "fill-color": "#cccccc",
                "fill-opacity": 0.1,
                "line-color": "#666666",
                "line-width": 1
            }
        }
    }


def create_property_marker(lat: float, lng: float, properties: Dict[str, Any]) -> Dict[str, Any]:
    """Create GeoJSON feature for property marker."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lng, lat]
        },
        "properties": properties
    }


def create_circle_polygon(
    center_lat: float,
    center_lng: float,
    radius_km: float,
    properties: Dict[str, Any],
    num_points: int = 32
) -> Dict[str, Any]:
    """Create a circular polygon (approximation) for buffer zones."""
    from math import radians, degrees, sin, cos, atan2, sqrt
    
    coords = []
    for i in range(num_points + 1):
        angle = (360 / num_points) * i
        angle_rad = radians(angle)
        
        # Calculate point on circle
        lat_rad = radians(center_lat)
        lng_rad = radians(center_lng)
        
        # Angular distance
        d = radius_km / 6371  # Earth radius in km
        
        lat2 = degrees(
            atan2(
                sin(lat_rad) * cos(d) + cos(lat_rad) * sin(d) * cos(angle_rad),
                sqrt(1 - (sin(lat_rad) * cos(d) + cos(lat_rad) * sin(d) * cos(angle_rad))**2)
            )
        )
        
        lng2 = center_lng + degrees(
            atan2(
                sin(angle_rad) * sin(d) * cos(lat_rad),
                cos(d) - sin(lat_rad) * sin(radians(lat2))
            )
        )
        
        coords.append([lng2, lat2])
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        },
        "properties": properties
    }







