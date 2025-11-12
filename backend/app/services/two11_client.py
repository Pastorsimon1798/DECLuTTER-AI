"""211 Open Referral API Client"""
import httpx
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from app.config import settings
from app.schemas.resource import OpenReferralOrganization, OpenReferralLocation


class Two11Client:
    """Client for 211 Open Referral API"""

    def __init__(self):
        self.base_url = settings.TWO11_API_URL
        self.api_key = settings.TWO11_API_KEY
        self.timeout = 30.0

    async def search_organizations(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[int] = None,  # in meters
        category: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search for organizations via 211 API

        Note: This is a placeholder implementation. The actual 211 API
        endpoints and parameters may vary by region. You'll need to adapt
        this to your specific 211 API provider.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "limit": limit
                }

                # Add API key if configured
                if self.api_key:
                    params["api_key"] = self.api_key

                # Location-based search
                if lat and lon:
                    params["lat"] = lat
                    params["lon"] = lon
                    if radius:
                        params["radius"] = radius / 1609.34  # Convert meters to miles

                # Category filter
                if category:
                    params["category"] = category

                # Text search
                if query:
                    params["query"] = query

                # Make API request
                response = await client.get(
                    f"{self.base_url}/organizations",
                    params=params
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"211 API error: {response.status_code} - {response.text}")
                    return []

        except httpx.TimeoutException:
            print("211 API request timed out")
            return []
        except Exception as e:
            print(f"211 API error: {e}")
            return []

    async def get_organization(self, org_id: str) -> Optional[Dict]:
        """Get details for a specific organization"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if self.api_key:
                    params["api_key"] = self.api_key

                response = await client.get(
                    f"{self.base_url}/organizations/{org_id}",
                    params=params
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"211 API error: {response.status_code}")
                    return None

        except Exception as e:
            print(f"211 API error: {e}")
            return None

    def parse_organization_to_resource(self, org_data: Dict) -> Dict:
        """
        Parse 211 API organization data into our resource format

        This is a helper method to transform 211 API responses into
        our internal resource listing format.
        """
        # Extract location information
        location = None
        location_address = None
        if org_data.get("locations") and len(org_data["locations"]) > 0:
            loc = org_data["locations"][0]
            if loc.get("latitude") and loc.get("longitude"):
                location = {
                    "lat": float(loc["latitude"]),
                    "lon": float(loc["longitude"])
                }

            # Build address string
            address_parts = []
            if loc.get("address_1"):
                address_parts.append(loc["address_1"])
            if loc.get("city"):
                address_parts.append(loc["city"])
            if loc.get("state_province"):
                address_parts.append(loc["state_province"])
            if loc.get("postal_code"):
                address_parts.append(loc["postal_code"])
            location_address = ", ".join(address_parts) if address_parts else None

        # Extract services
        services = []
        languages = set()
        if org_data.get("services"):
            for service in org_data["services"]:
                if service.get("name"):
                    services.append(service["name"])
                if service.get("languages"):
                    languages.update(service["languages"])

        # Determine category (simplified - you may want more sophisticated logic)
        category = "general"
        org_name_lower = org_data.get("name", "").lower()
        if "food" in org_name_lower or "pantry" in org_name_lower:
            category = "food_pantry"
        elif "shelter" in org_name_lower or "housing" in org_name_lower:
            category = "shelter"
        elif "medical" in org_name_lower or "health" in org_name_lower or "clinic" in org_name_lower:
            category = "medical"

        return {
            "external_id": org_data.get("id"),
            "name": org_data.get("name", "Unknown"),
            "category": category,
            "description": org_data.get("description"),
            "location": location,
            "location_address": location_address,
            "phone": org_data.get("phone"),
            "email": org_data.get("email"),
            "website": org_data.get("url"),
            "services": services if services else None,
            "languages": list(languages) if languages else None,
            "last_verified_at": datetime.utcnow(),
        }


# Singleton instance
two11_client = Two11Client()
