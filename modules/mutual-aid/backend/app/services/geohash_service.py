"""
Geohash service for privacy-preserving location handling

Uses geohash encoding to protect exact user locations while enabling
proximity-based search for needs and offers.
"""
import geohash2 as geohash
from typing import Tuple, List, Optional
from math import radians, sin, cos, sqrt, atan2


class GeohashService:
    """Service for handling geohash-based location operations"""

    # Geohash precision levels and their approximate accuracy
    # Precision 7 = ~150m area (good privacy/utility balance)
    # Precision 6 = ~1.2km area
    # Precision 5 = ~5km area
    DEFAULT_PRECISION = 7

    @staticmethod
    def encode_location(lat: float, lon: float, precision: int = DEFAULT_PRECISION) -> str:
        """
        Convert latitude/longitude to geohash string

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            precision: Geohash precision level (default: 7 for ~150m)

        Returns:
            Geohash string
        """
        return geohash.encode(lat, lon, precision=precision)

    @staticmethod
    def decode_location(geohash_str: str) -> Tuple[float, float]:
        """
        Convert geohash to latitude/longitude (center point)

        Args:
            geohash_str: Geohash string

        Returns:
            Tuple of (latitude, longitude)
        """
        return geohash.decode(geohash_str)

    @staticmethod
    def get_neighbors(geohash_str: str) -> List[str]:
        """
        Get all 8 neighboring geohash cells

        Args:
            geohash_str: Geohash string

        Returns:
            List of neighboring geohash strings
        """
        neighbors = []
        # Get all 8 directions
        directions = [
            'top', 'bottom', 'left', 'right',
            'topleft', 'topright', 'bottomleft', 'bottomright'
        ]

        for direction in directions:
            try:
                neighbor = geohash.neighbor(geohash_str, direction)
                neighbors.append(neighbor)
            except:
                # Some edge cases might not have all neighbors
                pass

        return neighbors

    @staticmethod
    def get_search_cells(center_hash: str, radius_meters: int) -> List[str]:
        """
        Get all geohash cells within a given radius

        Args:
            center_hash: Center geohash string
            radius_meters: Search radius in meters

        Returns:
            List of geohash strings to search (including center)
        """
        # Determine precision based on radius
        if radius_meters <= 200:
            precision = 7  # ~150m cells
        elif radius_meters <= 1000:
            precision = 6  # ~1.2km cells
        elif radius_meters <= 5000:
            precision = 5  # ~5km cells
        else:
            precision = 4  # ~20km cells

        # Truncate center hash to appropriate precision
        center = center_hash[:precision]

        # Start with center cell
        cells = [center]

        # Add immediate neighbors for all radii
        neighbors = GeohashService.get_neighbors(center)
        cells.extend(neighbors)

        # For larger radii, add second ring of neighbors
        if radius_meters > 1000:
            for neighbor in neighbors:
                second_ring = GeohashService.get_neighbors(neighbor)
                cells.extend(second_ring)

        # Remove duplicates and return
        return list(set(cells))

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in meters
        """
        # Earth's radius in meters
        R = 6371000

        # Convert to radians
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        # Haversine formula
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return distance

    @staticmethod
    def is_within_radius(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        radius_meters: int
    ) -> bool:
        """
        Check if two points are within a given radius

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            radius_meters: Maximum distance in meters

        Returns:
            True if within radius, False otherwise
        """
        distance = GeohashService.calculate_distance(lat1, lon1, lat2, lon2)
        return distance <= radius_meters

    @staticmethod
    def get_geohash_bounds(geohash_str: str) -> dict:
        """
        Get the bounding box for a geohash cell

        Args:
            geohash_str: Geohash string

        Returns:
            Dictionary with 'min_lat', 'max_lat', 'min_lon', 'max_lon'
        """
        lat, lon = geohash.decode(geohash_str)
        lat_err, lon_err = geohash.decode_exactly(geohash_str)[2:]

        return {
            'min_lat': lat - lat_err,
            'max_lat': lat + lat_err,
            'min_lon': lon - lon_err,
            'max_lon': lon + lon_err,
        }

    @staticmethod
    def obscure_location(lat: float, lon: float) -> Tuple[float, float]:
        """
        Obscure exact location by returning center of geohash cell

        Args:
            lat: Exact latitude
            lon: Exact longitude

        Returns:
            Tuple of (obscured_lat, obscured_lon) representing cell center
        """
        geohash_str = GeohashService.encode_location(lat, lon)
        return GeohashService.decode_location(geohash_str)
